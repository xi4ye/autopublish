import re
import os
import json
import requests
from datetime import datetime, timedelta
from typing import Tuple, Dict, List, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed


class URLRedirectResolver:
    """URL 重定向解析器 - 使用登录 cookies 解析重定向 URL"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self._initialized = True
        self.cookies_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "login_cookies.json")
        self.session = requests.Session()
        self.cookies = {}
        self.cookies_expire_time = None
        
        self._load_cookies()
    
    def _load_cookies(self) -> bool:
        """加载 cookies 文件"""
        if not os.path.exists(self.cookies_file):
            return False
        
        try:
            with open(self.cookies_file, 'r') as f:
                self.cookies = json.load(f)
            
            mtime = os.path.getmtime(self.cookies_file)
            self.cookies_expire_time = datetime.fromtimestamp(mtime) + timedelta(days=7)
            
            for name, value in self.cookies.items():
                self.session.cookies.set(name, value)
            
            return True
        except Exception:
            return False
    
    def is_cookies_valid(self) -> bool:
        """检查 cookies 是否有效"""
        if not self.cookies:
            return False
        if self.cookies_expire_time and datetime.now() > self.cookies_expire_time:
            return False
        return True
    
    def get_final_url(self, url: str, timeout: int = 10) -> Tuple[bool, str]:
        """获取重定向后的最终 URL"""
        if not self.is_cookies_valid():
            return False, url
        
        try:
            response = self.session.head(
                url,
                allow_redirects=True,
                timeout=timeout,
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                }
            )
            return True, response.url
        except Exception:
            return False, url
    
    def batch_resolve(self, urls: List[str], max_workers: int = 5, timeout: int = 10) -> Dict[str, str]:
        """批量解析 URL"""
        if not self.is_cookies_valid():
            return {url: url for url in urls}
        
        results = {}
        
        def resolve(url):
            success, final_url = self.get_final_url(url, timeout)
            return url, final_url
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {executor.submit(resolve, url): url for url in urls}
            for future in as_completed(futures):
                original_url, final_url = future.result()
                results[original_url] = final_url
        
        return results


_resolver = None

def get_url_resolver() -> URLRedirectResolver:
    """获取全局 URL 解析器实例"""
    global _resolver
    if _resolver is None:
        _resolver = URLRedirectResolver()
    return _resolver

def resolve_redirect_url(url: str) -> str:
    """解析单个 URL 的重定向（便捷函数）"""
    resolver = get_url_resolver()
    success, final_url = resolver.get_final_url(url)
    return final_url if success else url


def extract_collection(content):
    """提取 COLLECTION 部分（分析师报告）"""
    collection = []
    
    collection_start = content.find('#### **1. COLLECTION**')
    if collection_start == -1:
        collection_start = content.find('#### **1. 信息收集**')
    
    if collection_start == -1:
        return collection
    
    collection_end = content.find('#### **2.', collection_start)
    if collection_end == -1:
        collection_end = content.find('---', collection_start)
    if collection_end == -1:
        collection_end = len(content)
    
    collection_text = content[collection_start:collection_end]
    
    pattern = r'\*\*Analyst Report\s+(\d+)\s*\([^)]*Importance Score:\s*(\d+)[^)]*\)\*\*[：:]\s*([^\n]+(?:\n(?!\s*-\s*\*\*Analyst Report)[^\n]*)*)'
    matches = re.findall(pattern, collection_text, re.MULTILINE)
    
    for num, score, text in matches:
        collection.append({
            'id': int(num),
            'score': int(score),
            'content': text.strip()
        })
    
    return collection


def extract_evidence(content):
    """提取 ANALYSIS.evidence 部分（证据综合）"""
    evidence = []
    
    evidence_start = content.find('**Evidence Synthesis and Corroboration:**')
    if evidence_start == -1:
        evidence_start = content.find('**证据综合与互证：**')
    if evidence_start == -1:
        evidence_start = content.find('**证据综合与相互印证：**')
    if evidence_start == -1:
        evidence_start = content.find('**证据综合与佐证：**')
    
    if evidence_start == -1:
        return evidence
    
    evidence_end = content.find('---', evidence_start)
    if evidence_end == -1:
        evidence_end = content.find('#### **3.', evidence_start)
    if evidence_end == -1:
        evidence_end = content.find('**NEWS TYPE**', evidence_start)
    if evidence_end == -1:
        evidence_end = content.find('**新闻类型**', evidence_start)
    if evidence_end == -1:
        evidence_end = len(content)
    
    evidence_text = content[evidence_start:evidence_end]
    
    pattern = r'\d+\.\s*\*\*([^*]+)\*\*[：:]\s*([^\n]+(?:\n(?!\d+\.\s*\*\*)[^\n]*)*)'
    matches = re.findall(pattern, evidence_text, re.MULTILINE)
    
    for i, (title, text) in enumerate(matches[:5], 1):
        evidence.append({
            'id': i,
            'title': title.strip(),
            'content': text.strip()
        })
    
    return evidence


def extract_final_judgment(content):
    """提取 CONCLUSION.FinalJudgment"""
    judgment_start = content.find('##### **Final Judgment**')
    if judgment_start == -1:
        judgment_start = content.find('##### **最终判定**')
    if judgment_start == -1:
        judgment_start = content.find('**Final Judgment**')
    if judgment_start == -1:
        judgment_start = content.find('**最终判定**')
    
    if judgment_start == -1:
        return 'FALSE'
    
    judgment_text = content[judgment_start:judgment_start+200]
    
    if '**TRUE**' in judgment_text:
        return 'TRUE'
    elif '**FALSE**' in judgment_text:
        return 'FALSE'
    
    return 'FALSE'


def extract_detailed_reasons(content):
    """提取 CONCLUSION.DetailedReasons（详细原因）"""
    detailed_reasons = []
    
    reason_markers = [
        '**Detailed Reasons for False Classification:**',
        '**Detailed reasons for false classification:**',
        '**归类为错误的详细理由：**',
        '**错误分类的详细原因：**',
        '**判定为虚假的详细理由：**',
        '**虚假分类的详细原因：**',
        '**详细理由：**',
        '**判定理由：**',
    ]
    
    reasons_start = -1
    matched_marker = None
    for marker in reason_markers:
        reasons_start = content.find(marker)
        if reasons_start != -1:
            matched_marker = marker
            break
    
    if reasons_start == -1:
        flexible_pattern = r'\*\*[^*]*(?:详细理由|详细原因|理由)[：:]\*\*'
        match = re.search(flexible_pattern, content)
        if match:
            reasons_start = match.start()
            matched_marker = match.group()
    
    if reasons_start == -1:
        return detailed_reasons
    
    reasons_start = content.find('\n', reasons_start) + 1
    if reasons_start == 0:
        reasons_start = reasons_start + len(matched_marker) if matched_marker else 0
    
    end_markers = [
        '所有证据都指向',
        '所有证据均指向',
        '**NEWS TYPE**',
        '**新闻类型**',
        '---',
    ]
    
    reasons_end = -1
    for end_marker in end_markers:
        reasons_end = content.find(end_marker, reasons_start)
        if reasons_end != -1:
            break
    
    if reasons_end == -1:
        reasons_end = len(content)
    
    detailed_reasons_text = content[reasons_start:reasons_end].strip()
    
    roman_pattern = r'([ⅠⅡⅢⅣⅤⅥⅦⅧⅨⅩ]+)\.\s*\*\*([^*]+)\*\*\s*\n?\s*([^\n]+(?:\n(?![ⅠⅡⅢⅣⅤⅥⅦⅧⅨⅩ]+\.)[^\n]*)*)'
    reasons = re.findall(roman_pattern, detailed_reasons_text, re.MULTILINE)
    
    if not reasons:
        arabic_pattern = r'(\d+)\.\s*\*\*([^*]+)\*\*\s*\n?\s*([^\n]+(?:\n(?!\d+\.\s*\*\*)[^\n]*)*)'
        reasons = re.findall(arabic_pattern, detailed_reasons_text, re.MULTILINE)
    
    if not reasons:
        simple_pattern = r'[-•]\s*\*\*([^*]+)\*\*[：:]\s*([^\n]+)'
        simple_reasons = re.findall(simple_pattern, detailed_reasons_text)
        reasons = [(str(i+1), title, content) for i, (title, content) in enumerate(simple_reasons)]
    
    roman_nums = ['Ⅰ', 'Ⅱ', 'Ⅲ', 'Ⅳ', 'Ⅴ']
    for i, match in enumerate(reasons[:5]):
        if len(match) == 3:
            num, title, reason_content = match
        else:
            continue
        detailed_reasons.append({
            'id': roman_nums[i] if i < len(roman_nums) else str(num),
            'title': title.strip(),
            'content': reason_content.strip()
        })
    
    return detailed_reasons


def extract_news_type(content):
    """提取 NEWS_TYPE"""
    news_type_start = content.find('**NEWS TYPE**')
    if news_type_start == -1:
        news_type_start = content.find('**新闻类型**')
    
    if news_type_start == -1:
        return 'Business'
    
    news_type_text = content[news_type_start:news_type_start+100]
    
    match = re.search(r'\[([^\]]+)\]', news_type_text)
    if match:
        return match.group(1)
    
    return 'Business'


def parse_raw_data(raw_data):
    """
    解析原始数据（不翻译），提取所有字段
    
    Args:
        raw_data: 原始数据字典（包含 last_output.k=5 的英文内容）
        
    Returns:
        formatted_data: 格式化后的数据字典
    """
    date = None
    for k, history_list in raw_data.get('history', {}).items():
        if history_list and history_list[0].get('Date'):
            date = history_list[0].get('Date')
            break

    relevant_news_data = raw_data.get('relevant_news') or raw_data.get('revelent_news', {
        'id': raw_data.get('id', 0),
        'claim': raw_data.get('description', ''),
        'collection': []
    })
    
    result = {
        'description': raw_data.get('description', ''),
        'Date': date,
        'id': raw_data.get('id', 0),
        'CONCLUSION': {
            'FinalJudgment': 'FALSE',
            'DetailedReasons': []
        },
        'ANALYSIS': {
            'summary': '所有经过验证的报道和分析师报告均证实以下事实：',
            'evidence': []
        },
        'COLLECTION': [],
        'NEWS_TYPE': 'Business',
        'relevant_news': relevant_news_data
    }
    
    last_output = raw_data.get('last_output', {})
    analysis_content = last_output.get('k=5', '')
    
    if not analysis_content:
        return result
    
    result['COLLECTION'] = extract_collection(analysis_content)
    result['ANALYSIS']['evidence'] = extract_evidence(analysis_content)
    result['CONCLUSION']['FinalJudgment'] = extract_final_judgment(analysis_content)
    result['CONCLUSION']['DetailedReasons'] = extract_detailed_reasons(analysis_content)
    result['NEWS_TYPE'] = extract_news_type(analysis_content)
    
    return result


def parse_translated_output(translated_data):
    """
    将翻译后的数据转换为结构化的JSON格式（兼容旧代码）
    
    Args:
        translated_data: 翻译后的数据字典
        
    Returns:
        formatted_data: 格式化后的数据字典
    """
    return parse_raw_data(translated_data)


def format_for_template(raw_data, resolve_urls: bool = True):
    """
    格式化数据供 SmartImageGenerator 使用
    
    Args:
        raw_data: 原始数据（可以是翻译前或翻译后的）
        resolve_urls: 是否解析 URL 重定向（默认 True）
    """
    formatted = parse_raw_data(raw_data)

    if resolve_urls and formatted['relevant_news'].get('collection'):
        resolver = get_url_resolver()
        
        if resolver.is_cookies_valid():
            print("\n[URL解析] 正在解析相关新闻 URL 重定向...")
            
            for news in formatted['relevant_news']['collection']:
                if 'url' in news:
                    original_url = news['url']
                    clean_url = original_url.replace('url:', '') if original_url.startswith('url:') else original_url
                    
                    if 'iwencai.com' in clean_url:
                        success, final_url = resolver.get_final_url(clean_url)
                        
                        if success and final_url != clean_url:
                            news['url'] = f"url:{final_url}"
                            print(f"  ✓ {clean_url[:50]}... -> {final_url[:50]}...")
                        else:
                            if not original_url.startswith('url:'):
                                news['url'] = f"url:{clean_url}"
                    else:
                        if not original_url.startswith('url:'):
                            news['url'] = f"url:{clean_url}"
        else:
            print("\n[URL解析] Cookies 无效，跳过 URL 重定向解析")

    if not formatted['relevant_news'].get('collection'):
        formatted['relevant_news']['collection'] = [
            {
                'id': 1,
                'title': '托克与中国 ITG 洽谈设立信贷基金 | 财经新闻',
                'url': 'url:https://example.com/news1'
            },
            {
                'id': 2,
                'title': '东京海上与中国机构合作传闻 | 金融时报',
                'url': 'url:https://example.com/news2'
            },
            {
                'id': 3,
                'title': 'ITG 在中国金融领域的真实性 | 证券日报',
                'url': 'url:https://example.com/news3'
            }
        ]

    return formatted
