#!/usr/bin/env python3
"""
网站术语爬虫脚本
从三个网站抓取成人内容术语及其解释
"""

import requests
from bs4 import BeautifulSoup
import json
import re
import time

# 设置请求头，模拟浏览器
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
}

def scrape_askmen():
    """从AskMen网站抓取术语"""
    url = "https://www.askmen.com/sex/sex-tips/porn-slang-terms-explained.html"
    print(f"正在抓取: {url}")
    
    try:
        response = requests.get(url, headers=HEADERS, timeout=30)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        terms = {}
        
        # 找到所有h2标签作为术语标题
        for h2 in soup.find_all('h2'):
            term_name = h2.get_text(strip=True)
            if not term_name or term_name in ['RELATED:', 'You Might Also Dig:']:
                continue
                
            # 获取描述 - 通常在h2后面的p标签或特定结构中
            description = ""
            category = ""
            alias = ""
            
            # 查找下一个兄弟元素
            sibling = h2.find_next_sibling()
            while sibling:
                if sibling.name == 'h2':
                    break
                if sibling.name == 'p':
                    text = sibling.get_text(strip=True)
                    # 检查是否是类别标识
                    if text.startswith('Porn /'):
                        category = text.replace('Porn /', '').strip()
                    elif text.startswith('aka '):
                        alias = text.replace('aka ', '').strip()
                    elif text and not text.startswith('RELATED:'):
                        if description:
                            description += " " + text
                        else:
                            description = text
                sibling = sibling.find_next_sibling()
            
            if term_name and description:
                key = term_name.lower().replace(' ', '_').replace('/', '_').replace('&', 'and')
                terms[key] = {
                    'term': term_name,
                    'category': category if category else 'General',
                    'alias': alias,
                    'description': description
                }
                print(f"  找到术语: {term_name}")
        
        return terms
        
    except Exception as e:
        print(f"抓取AskMen失败: {e}")
        return {}

def scrape_erohut():
    """从EroHut网站抓取术语"""
    url = "https://erohut.com/sexual-slang-terms-porn-acryonyms/"
    print(f"正在抓取: {url}")
    
    try:
        response = requests.get(url, headers=HEADERS, timeout=30)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        terms = {}
        
        # 找到文章内容区域
        content = soup.find('div', class_='entry-content') or soup.find('article')
        if not content:
            content = soup
        
        # 找到所有粗体标签或h2/h3/h4作为术语标题
        for heading in content.find_all(['h2', 'h3', 'h4', 'strong', 'b']):
            term_name = heading.get_text(strip=True)
            if not term_name or len(term_name) > 50:  # 过滤过长的文本
                continue
            if term_name.lower() in ['quick access', 'common sexual terms', 'escort terms', 'bdsm terms']:
                continue
                
            # 获取描述
            description = ""
            parent = heading.parent
            
            if heading.name in ['strong', 'b']:
                # 如果是粗体，描述可能在同一个p标签中
                if parent and parent.name == 'p':
                    full_text = parent.get_text(strip=True)
                    if term_name in full_text:
                        description = full_text.replace(term_name, '', 1).strip()
            else:
                # 对于h2/h3/h4，描述在下一个p标签
                next_p = heading.find_next('p')
                if next_p:
                    description = next_p.get_text(strip=True)
            
            if term_name and description and len(description) > 20:
                key = term_name.lower().replace(' ', '_').replace('/', '_').replace('&', 'and')
                terms[key] = {
                    'term': term_name,
                    'category': 'General',
                    'alias': '',
                    'description': description
                }
                print(f"  找到术语: {term_name}")
        
        return terms
        
    except Exception as e:
        print(f"抓取EroHut失败: {e}")
        return {}

def scrape_godsofadult():
    """从GodsOfAdult网站抓取术语"""
    url = "https://godsofadult.com/interpretation-porn-genres/"
    print(f"正在抓取: {url}")
    
    try:
        response = requests.get(url, headers=HEADERS, timeout=30)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        terms = {}
        
        # 找到文章内容区域
        content = soup.find('div', class_='entry-content') or soup.find('article') or soup.find('main')
        if not content:
            content = soup
        
        # 找到所有标题标签
        for heading in content.find_all(['h2', 'h3', 'h4']):
            term_name = heading.get_text(strip=True)
            if not term_name or len(term_name) > 100:
                continue
                
            # 获取描述 - 下一个p标签
            description = ""
            next_elem = heading.find_next_sibling()
            while next_elem:
                if next_elem.name in ['h2', 'h3', 'h4']:
                    break
                if next_elem.name == 'p':
                    text = next_elem.get_text(strip=True)
                    if text:
                        if description:
                            description += " " + text
                        else:
                            description = text
                next_elem = next_elem.find_next_sibling()
            
            if term_name and description and len(description) > 20:
                key = term_name.lower().replace(' ', '_').replace('/', '_').replace('&', 'and')
                terms[key] = {
                    'term': term_name,
                    'category': 'Genre',
                    'alias': '',
                    'description': description
                }
                print(f"  找到术语: {term_name}")
        
        return terms
        
    except Exception as e:
        print(f"抓取GodsOfAdult失败: {e}")
        return {}

def merge_terms(askmen_terms, erohut_terms, godsofadult_terms):
    """合并三个来源的术语"""
    merged = {}
    
    # 先添加AskMen的术语
    for key, value in askmen_terms.items():
        merged[key] = {
            'en': value,
            'zh': {
                'term': '',  # 需要翻译
                'category': '',
                'alias': '',
                'description': ''
            },
            'source': ['askmen']
        }
    
    # 添加EroHut的术语
    for key, value in erohut_terms.items():
        if key in merged:
            # 如果已存在，添加来源
            merged[key]['source'].append('erohut')
            # 如果描述更长，更新
            if len(value['description']) > len(merged[key]['en']['description']):
                merged[key]['en']['description'] = value['description']
        else:
            merged[key] = {
                'en': value,
                'zh': {
                    'term': '',
                    'category': '',
                    'alias': '',
                    'description': ''
                },
                'source': ['erohut']
            }
    
    # 添加GodsOfAdult的术语
    for key, value in godsofadult_terms.items():
        if key in merged:
            merged[key]['source'].append('godsofadult')
            if len(value['description']) > len(merged[key]['en']['description']):
                merged[key]['en']['description'] = value['description']
        else:
            merged[key] = {
                'en': value,
                'zh': {
                    'term': '',
                    'category': '',
                    'alias': '',
                    'description': ''
                },
                'source': ['godsofadult']
            }
    
    return merged

def main():
    print("=" * 50)
    print("开始抓取三个网站的术语数据")
    print("=" * 50)
    
    # 抓取三个网站
    askmen_terms = scrape_askmen()
    print(f"\nAskMen: 找到 {len(askmen_terms)} 个术语")
    time.sleep(2)  # 防止请求过快
    
    erohut_terms = scrape_erohut()
    print(f"\nEroHut: 找到 {len(erohut_terms)} 个术语")
    time.sleep(2)
    
    godsofadult_terms = scrape_godsofadult()
    print(f"\nGodsOfAdult: 找到 {len(godsofadult_terms)} 个术语")
    
    # 合并术语
    print("\n正在合并术语...")
    merged = merge_terms(askmen_terms, erohut_terms, godsofadult_terms)
    
    print(f"\n合并后总共: {len(merged)} 个术语")
    
    # 保存到文件
    output_file = 'data/scraped_terms.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(merged, f, ensure_ascii=False, indent=2)
    
    print(f"\n术语已保存到: {output_file}")
    
    # 显示所有术语列表
    print("\n" + "=" * 50)
    print("所有术语列表:")
    print("=" * 50)
    for key in sorted(merged.keys()):
        sources = ', '.join(merged[key]['source'])
        print(f"  - {merged[key]['en']['term']} [{sources}]")

if __name__ == '__main__':
    main()