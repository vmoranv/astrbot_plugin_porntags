# PornTags - AstrBot 成人内容术语查询插件

一个用于查询成人内容标签术语含义的 AstrBot 插件，支持中英文双语解释。

## 功能特点

- 📚 收录 70+ 常见成人内容术语
- 🌐 中英文双语解释
- 🔍 支持精确匹配和模糊搜索
- 🏷️ 支持别名匹配
- 📂 按类型分类（Genre、Move、Performer等）

## 安装

将本插件目录放置到 AstrBot 的 `data/plugins/` 或 `addons/plugins/` 目录下即可。

## 使用方法

### 基本查询
```
/porntags <tag>
```

### 示例
```
/porntags milf
/porntags 熟女
/porntags bbc
/porntags 内射
/porntags creampie
```

### 列出所有术语
```
/porntags list
```

### 帮助信息
```
/porntags
```

## 术语分类

| 类型 | 说明 | 示例 |
|------|------|------|
| Genre | 内容类型/题材 | amateur, bdsm, cosplay |
| Move | 动作/行为 | creampie, deepthroat, facial |
| Performer | 表演者类型 | milf, bbw, teen |
| Expression | 表情/表现 | ahegao |

## 数据来源

术语数据整理自以下来源：
- AskMen - Porn Slang Terms Explained
- EroHut - Sexual Slang Terms & Porn Acronyms
- GodsOfAdult - Interpretation of Porn Genres

## 文件结构

```
astrbot_plugin_porntags/
├── main.py          # 插件主文件
├── metadata.yaml    # 插件元数据
├── README.md        # 说明文档
├── LICENSE          # 许可证
└── data/
    └── tags.json    # 术语数据库（中英文）
```

## 添加新术语

编辑 `data/tags.json` 文件，按以下格式添加：

```json
"term_key": {
  "en": {
    "term": "Term Name",
    "category": "Genre/Move/Performer",
    "aliases": ["alias1", "alias2"],
    "description": "English description..."
  },
  "zh": {
    "term": "中文名称",
    "category": "类型/动作/表演者",
    "aliases": ["别名1", "别名2"],
    "description": "中文描述..."
  }
}
```

## 许可证

MIT License

## 作者

vmoranv

## 免责声明

本插件仅用于教育目的，帮助用户理解成人内容中的专业术语。请确保在合法、适当的环境中使用。
