import json
import os

try:
    from pydantic import Field
    from pydantic.dataclasses import dataclass

    from astrbot.core.agent.run_context import ContextWrapper
    from astrbot.core.agent.tool import FunctionTool, ToolExecResult
    from astrbot.core.astr_agent_context import AstrAgentContext

    _LLM_TOOL_AVAILABLE = True
except Exception:
    # LLM tool API is optional; keep /porntags command working even if it's unavailable.
    _LLM_TOOL_AVAILABLE = False

from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.star import Context, Star, register
from astrbot.api import logger


def _get_tags_file_path() -> str:
    plugin_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(plugin_dir, "data", "tags.json")


def load_tags_data() -> dict:
    tags_file = _get_tags_file_path()
    if not os.path.exists(tags_file):
        return {}
    with open(tags_file, "r", encoding="utf-8") as f:
        return json.load(f)


def search_tags(tags_data: dict, query: str) -> dict | None:
    """搜索术语，支持别名和模糊匹配"""
    query_lower = query.lower().strip()

    # 精确匹配key
    if query_lower in tags_data:
        return {query_lower: tags_data[query_lower]}

    # 搜索别名和术语名
    results = {}
    for key, data in tags_data.items():
        # 检查英文术语名和别名
        en_data = data.get("en", {})
        en_term = en_data.get("term", "").lower()
        en_aliases = [a.lower() for a in en_data.get("aliases", [])]

        # 检查中文术语名和别名
        zh_data = data.get("zh", {})
        zh_term = zh_data.get("term", "")
        zh_aliases = zh_data.get("aliases", [])

        # 精确匹配
        if (
            query_lower == en_term
            or query_lower in en_aliases
            or query == zh_term
            or query in zh_aliases
        ):
            results[key] = data
            continue

        # 模糊匹配（包含查询）
        if (
            query_lower in en_term
            or query_lower in key
            or any(query_lower in alias for alias in en_aliases)
            or query in zh_term
            or any(query in alias for alias in zh_aliases)
        ):
            results[key] = data

    return results if results else None


def format_tag_result(key: str, data: dict) -> str:
    """格式化单个结果"""
    en_data = data.get("en", {})
    zh_data = data.get("zh", {})

    en_term = en_data.get("term", key.upper())
    en_category = en_data.get("category", "Unknown")
    en_aliases = en_data.get("aliases", [])
    en_desc = en_data.get("description", "No description available.")

    zh_term = zh_data.get("term", "")
    zh_category = zh_data.get("category", "")
    zh_aliases = zh_data.get("aliases", [])
    zh_desc = zh_data.get("description", "")

    result = f"📖 【{en_term}】"
    if zh_term:
        result += f" / {zh_term}"
    result += "\n"

    result += f"📂 类型: {en_category}"
    if zh_category:
        result += f" ({zh_category})"
    result += "\n"

    all_aliases = list(set(en_aliases + zh_aliases))
    if all_aliases:
        result += f"🏷️ 别名: {', '.join(all_aliases)}\n"

    result += f"\n🇬🇧 English:\n{en_desc}\n"

    if zh_desc:
        result += f"\n🇨🇳 中文:\n{zh_desc}"

    return result


def format_tag_list(tags_data: dict) -> str:
    tags_list = sorted(tags_data.keys())
    if not tags_list:
        return "❌ 术语库为空"

    # 按类别分组
    categories = {}
    for key in tags_list:
        data = tags_data[key]
        category = data.get("en", {}).get("category", "Other")
        categories.setdefault(category, []).append(key.upper())

    result = "📚 所有可用术语:\n\n"
    for cat, tags in sorted(categories.items()):
        result += f"【{cat}】\n"
        result += ", ".join(tags[:20])
        if len(tags) > 20:
            result += f" ... (+{len(tags)-20})"
        result += "\n\n"

    result += f"共 {len(tags_list)} 个术语"
    return result


if _LLM_TOOL_AVAILABLE:

    def _make_tool_result(text: str) -> ToolExecResult:
        try:
            return ToolExecResult(content=text)  # type: ignore[arg-type]
        except Exception:
            pass
        try:
            return ToolExecResult(result=text)  # type: ignore[arg-type]
        except Exception:
            pass
        try:
            return ToolExecResult(text=text)  # type: ignore[arg-type]
        except Exception:
            pass
        try:
            return ToolExecResult(text)  # type: ignore[misc]
        except Exception:
            return text  # type: ignore[return-value]

    @dataclass
    class PornTagsQueryTool(FunctionTool[AstrAgentContext]):
        name: str = "porntags_query"  # 工具名称
        description: str = "Query PornTags term meanings (supports English/Chinese, aliases, and fuzzy search)."
        parameters: dict = Field(
            default_factory=lambda: {
                "type": "object",
                "properties": {
                    "keywords": {
                        "type": "string",
                        "description": "Tag/term keywords to search (use 'list' to list all terms).",
                    },
                },
                "required": ["keywords"],
            }
        )

        async def call(
            self, context: ContextWrapper[AstrAgentContext], **kwargs
        ) -> ToolExecResult:
            keywords = (kwargs.get("keywords") or "").strip()
            if not keywords:
                return _make_tool_result(
                    "❌ 请提供要查询的关键词（例如: milf / 熟女 / bbc），或使用 keywords='list' 列出全部术语。"
                )

            tags_data = load_tags_data()
            if not tags_data:
                return _make_tool_result("❌ 术语库为空或加载失败。")

            if keywords.lower() == "list":
                return _make_tool_result(format_tag_list(tags_data))

            results = search_tags(tags_data, keywords)
            if not results:
                return _make_tool_result(f"❌ 未找到术语: {keywords}")

            if len(results) == 1:
                key, data = list(results.items())[0]
                return _make_tool_result(format_tag_result(key, data))

            # 多个结果，列出匹配项
            if len(results) <= 5:
                response = f"🔍 找到 {len(results)} 个匹配项:\n\n"
                for key, data in list(results.items())[:5]:
                    response += format_tag_result(key, data)
                    response += "\n" + "─" * 30 + "\n\n"
                return _make_tool_result(response.rstrip())

            # 太多结果，只显示列表
            response = f"🔍 找到 {len(results)} 个匹配项:\n\n"
            for key, data in results.items():
                en_term = data.get("en", {}).get("term", key)
                zh_term = data.get("zh", {}).get("term", "")
                response += f"• {en_term}"
                if zh_term:
                    response += f" ({zh_term})"
                response += "\n"
            response += "\n请输入更精确的关键词进行搜索"
            return _make_tool_result(response)

@register("porntags", "vmoranv", "成人内容标签术语查询插件", "1.1.0")
class PornTagsPlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)
        self.tags_data = {}
        self._load_tags()
        if _LLM_TOOL_AVAILABLE and hasattr(self.context, "add_llm_tools"):
            try:
                self.context.add_llm_tools(PornTagsQueryTool())
                logger.info("已注册 LLM Tool: porntags_query")
            except Exception as e:
                logger.warning(f"注册 LLM Tool 失败: {e}")

    def _load_tags(self):
        """加载术语数据"""
        try:
            self.tags_data = load_tags_data()
            if self.tags_data:
                logger.info(f"成功加载 {len(self.tags_data)} 个术语")
            else:
                logger.warning(f"术语文件不存在或为空: {_get_tags_file_path()}")
        except Exception as e:
            logger.error(f"加载术语数据失败: {e}")

    async def initialize(self):
        """插件初始化"""
        logger.info("PornTags 插件已初始化")

    def _search_tag(self, query: str) -> dict | None:
        """搜索术语，支持别名和模糊匹配"""
        return search_tags(self.tags_data, query)

    def _format_result(self, key: str, data: dict) -> str:
        """格式化单个结果"""
        return format_tag_result(key, data)

    @filter.command("porntags")
    async def porntags_handler(self, event: AstrMessageEvent):
        """
        查询成人内容术语标签的含义
        用法: /porntags <tag>
        示例: /porntags milf
        """
        message_str = event.message_str.strip()
        
        # 解析命令参数
        parts = message_str.split(maxsplit=1)
        if len(parts) < 2:
            help_text = """📚 PornTags - 成人内容术语查询

用法: /porntags <tag>

示例:
  /porntags milf
  /porntags 熟女
  /porntags bbc
  /porntags 内射

支持英文和中文搜索，支持别名匹配。

提示: 输入 /porntags list 查看所有可用术语"""
            yield event.plain_result(help_text)
            return
        
        query = parts[1].strip()
        
        # 列出所有术语
        if query.lower() == "list":
            yield event.plain_result(format_tag_list(self.tags_data))
            return
        
        # 搜索术语
        results = self._search_tag(query)
        
        if not results:
            yield event.plain_result(f"❌ 未找到术语: {query}\n\n提示: 尝试使用英文缩写或输入 /porntags list 查看所有可用术语")
            return
        
        # 格式化并返回结果
        if len(results) == 1:
            key, data = list(results.items())[0]
            formatted = self._format_result(key, data)
            yield event.plain_result(formatted)
        else:
            # 多个结果，列出匹配项
            if len(results) <= 5:
                response = f"🔍 找到 {len(results)} 个匹配项:\n\n"
                for key, data in list(results.items())[:5]:
                    response += self._format_result(key, data)
                    response += "\n" + "─" * 30 + "\n\n"
            else:
                # 太多结果，只显示列表
                response = f"🔍 找到 {len(results)} 个匹配项:\n\n"
                for key, data in results.items():
                    en_term = data.get("en", {}).get("term", key)
                    zh_term = data.get("zh", {}).get("term", "")
                    response += f"• {en_term}"
                    if zh_term:
                        response += f" ({zh_term})"
                    response += "\n"
                response += f"\n请输入更精确的关键词进行搜索"
            
            yield event.plain_result(response)

    async def terminate(self):
        """插件卸载时清理"""
        logger.info("PornTags 插件已卸载")
