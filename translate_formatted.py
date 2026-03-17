import json
import os
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage


class FormattedJSONTranslator:
    """翻译格式化后的 JSON 数据"""
    
    def __init__(self, api_key, base_url, model):
        self.llm = ChatOpenAI(
            api_key=api_key,
            base_url=base_url,
            model=model,
            temperature=0.3
        )
    
    def translate_text(self, text):
        """翻译单个文本，删除 Markdown 标记"""
        system_prompt = """你是一个专业的英中翻译专家。你的任务是：

1. 将英文内容翻译成中文
2. 删除所有 Markdown 格式标记（**粗体**、#### 标题、---分隔线、- 列表等）
3. 保持专业术语的准确性
4. 确保翻译流畅自然
5. 只返回翻译后的内容，不要添加任何解释或额外文字

【重要】以下固定标题必须使用指定的中文翻译：
- "COLLECTION" 或 "1. COLLECTION" → "1. 信息收集"
- "Record ALL Analyst Reports one by one" → "逐一记录所有分析师报告"
- "ANALYSIS" 或 "2. ANALYSIS" → "2. 分析"
- "Evaluation of ALL recorded Analyst Reports one by one" → "对所有记录的分析师报告进行逐一评估"
- "Evidence Synthesis and Corroboration" → "证据综合与互证"
- "CONCLUSION" 或 "3. CONCLUSION" → "3. 结论"
- "Final Judgment" → "最终判定"
- "News Type" → "新闻类型"
- "Detailed Reasons for False Classification" → "归类为错误的详细理由"
- "Analyst Report" → "分析师报告"
- "Importance Score" → "重要性评分"
- "TRUE" → "TRUE"（保持不变）
- "FALSE" → "FALSE"（保持不变）

【重要】以下内容保持不变：
- 罗马数字：Ⅰ、Ⅱ、Ⅲ、Ⅳ、Ⅴ、Ⅵ、Ⅶ、Ⅷ、Ⅸ、Ⅹ
- 引用标记：[citation:1]、[citation:2] 等（可翻译为 [引文:1]、[引文:2]）
- 数字和百分比：70%、$31.8 billion 等（转换为中文习惯：70%、318亿美元）
- URL 链接

【重要】删除所有 Markdown 标记：
- 删除 ** 粗体标记
- 删除 #### 标题标记
- 删除 --- 分隔线
- 删除开头的 - 列表标记（保留列表内容）"""

        human_prompt = f"""请将以下英文内容翻译成中文，删除所有 Markdown 标记：

{text}

翻译结果："""
        
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=human_prompt)
        ]
        
        response = self.llm.invoke(messages)
        return response.content
    
    def translate_formatted_data(self, formatted_data):
        """
        翻译格式化后的 JSON 数据
        
        Args:
            formatted_data: 格式化后的数据字典
            
        Returns:
            translated_data: 翻译后的数据字典
        """
        result = {
            'description': formatted_data.get('description', ''),
            'Date': formatted_data.get('Date', ''),
            'id': formatted_data.get('id', 0),
            'CONCLUSION': {
                'FinalJudgment': formatted_data['CONCLUSION'].get('FinalJudgment', 'FALSE'),
                'DetailedReasons': []
            },
            'ANALYSIS': {
                'summary': '所有经过验证的报道和分析师报告均证实以下事实：',
                'evidence': []
            },
            'COLLECTION': [],
            'NEWS_TYPE': formatted_data.get('NEWS_TYPE', 'Business'),
            'relevant_news': formatted_data.get('relevant_news', formatted_data.get('revelent_news', {}))
        }
        
        print("翻译 COLLECTION...")
        for item in formatted_data.get('COLLECTION', []):
            translated_content = self.translate_text(item['content'])
            result['COLLECTION'].append({
                'id': item['id'],
                'score': item['score'],
                'content': translated_content
            })
            print(f"  ✓ [{item['id']}] 翻译完成")
        
        print("\n翻译 ANALYSIS.evidence...")
        for item in formatted_data['ANALYSIS'].get('evidence', []):
            translated_title = self.translate_text(item['title'])
            translated_content = self.translate_text(item['content'])
            result['ANALYSIS']['evidence'].append({
                'id': item['id'],
                'title': translated_title,
                'content': translated_content
            })
            print(f"  ✓ [{item['id']}] {translated_title}")
        
        print("\n翻译 CONCLUSION.DetailedReasons...")
        for item in formatted_data['CONCLUSION'].get('DetailedReasons', []):
            translated_title = self.translate_text(item['title'])
            translated_content = self.translate_text(item['content'])
            result['CONCLUSION']['DetailedReasons'].append({
                'id': item['id'],
                'title': translated_title,
                'content': translated_content
            })
            print(f"  ✓ [{item['id']}] {translated_title}")
        
        if formatted_data.get('NEWS_TYPE'):
            result['NEWS_TYPE'] = self.translate_text(formatted_data['NEWS_TYPE'])
        
        return result


def translate_formatted_json(formatted_data, api_key=None, base_url=None, model=None):
    """
    翻译格式化后的 JSON 数据（便捷函数）
    
    Args:
        formatted_data: 格式化后的数据字典
        api_key: API 密钥（可选，默认使用配置）
        base_url: API 基础 URL（可选）
        model: 模型名称（可选）
        
    Returns:
        translated_data: 翻译后的数据字典
    """
    if api_key is None:
        api_key = os.environ.get("DEEPSEEK_API_KEY", "")
    if base_url is None:
        base_url = os.environ.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
    if model is None:
        model = os.environ.get("DEEPSEEK_MODEL", "deepseek-reasoner")
    
    translator = FormattedJSONTranslator(api_key, base_url, model)
    return translator.translate_formatted_data(formatted_data)


if __name__ == "__main__":
    path = os.path.dirname(os.path.abspath(__file__))
    
    input_file = os.path.join(path, 'data/test_matched_example.json')
    output_file = os.path.join(path, 'data/test_translated_example.json')
    
    print("=" * 60)
    print("翻译格式化后的 JSON 数据")
    print("=" * 60)
    
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    translated_data = translate_formatted_json(data)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(translated_data, f, ensure_ascii=False, indent=2)
    
    print(f"\n✓ 翻译结果已保存到: {output_file}")
