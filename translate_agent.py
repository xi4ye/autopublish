import json
import os
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage


class DeepSeekTranslator:
    def __init__(self, api_key, base_url, model):
        self.llm = ChatOpenAI(
            api_key=api_key,
            base_url=base_url,
            model=model,
            temperature=0.3
        )
    
    def translate_markdown(self, text):
        """
        翻译 Markdown 格式的文本，保持格式不变
        """
        system_prompt = """你是一个专业的英中翻译专家。你的任务是：
1. 将英文内容翻译成中文
2. 严格保持 Markdown 格式不变，包括标题、列表、粗体、斜体等所有格式
3. 保持专业术语的准确性
4. 确保翻译流畅自然
5. 只返回翻译后的内容，不要添加任何解释或额外文字

【重要】以下关键标题必须使用固定的中文翻译，保持原有的 Markdown 格式（**粗体**）：
- "#### **1. COLLECTION**" → "#### **1. 信息收集**"
- "**Record ALL Analyst Reports one by one:**" → "**逐一记录所有分析师报告：**"
- "#### **2. ANALYSIS**" → "#### **2. 分析**"
- "**Evaluation of ALL recorded Analyst Reports one by one:**" → "**对所有记录的分析师报告进行逐一评估：**"
- "**Evidence Synthesis and Corroboration:**" → "**证据综合与互证：**"
- "#### **3. CONCLUSION**" → "#### **3. 结论**"
- "**Final Judgment**" → "**最终判定**"
- "**News Type**" → "**新闻类型**"
- "**Detailed Reasons for False Classification:**" → "**归类为错误的详细理由：**"
- "**Analyst Report" → "**分析师报告"
- "Importance Score" → "重要性评分"

注意：以上标题的翻译必须严格匹配，包括标点符号和格式，以确保后续程序能正确解析。"""
        
        human_prompt = f"""请将以下 Markdown 格式的英文内容翻译成中文：

{text}

翻译结果："""
        
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=human_prompt)
        ]
        
        response = self.llm.invoke(messages)
        return response.content


def get_latest_false_record(jsonl_file):
    """
    从 JSONL 文件中获取最新的 history 中 Result 为 FALSE 的记录
    """
    false_records = []
    
    with open(jsonl_file, 'r', encoding='utf-8') as f:
        for line in f:
            data = json.loads(line.strip())
            
            # 检查 history 中是否有 result 为 FALSE 的记录
            for k, history_list in data.get('history', {}).items():
                if history_list and history_list[0].get('Result') == 'FALSE':
                    false_records.append({
                        'data': data,
                        'date': history_list[0].get('Date'),
                        'k': k
                    })
                    break  # 找到一个 FALSE 就可以了
    
    if not false_records:
        return None
    
    # 按日期排序，获取最新的
    false_records.sort(key=lambda x: x['date'], reverse=True)
    return false_records[0]['data']


def translate_record(record, translator):
    """
    翻译单条记录中的 last_output 内容
    """
    print(f"正在翻译记录 ID: {record['id']}")
    print(f"描述: {record['description']}")
    
    # 创建翻译后的记录
    translated_record = {
        'id': record['id'],
        'description': record['description'],
        'history': record['history'],
        'last_output': {}
    }
    
    # 翻译 last_output 中的每个 k 值的内容
    for k, content in record.get('last_output', {}).items():
        if content and content.strip():
            print(f"  - 翻译 k={k} 的内容...")
            try:
                translated_content = translator.translate_markdown(content)
                translated_record['last_output'][k] = translated_content
                print(f"    ✓ 翻译完成")
            except Exception as e:
                print(f"    ✗ 翻译失败: {e}")
                translated_record['last_output'][k] = content  # 保留原文
        else:
            translated_record['last_output'][k] = content
    
    return translated_record


def save_translated_data(translated_record, output_file):
    """
    保存翻译后的数据到 JSON 文件
    """
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(translated_record, f, ensure_ascii=False, indent=2)
    print(f"✓ 翻译结果已保存到: {output_file}")


def main():
    # 配置信息 - 从环境变量读取
    API_KEY = os.environ.get("DEEPSEEK_API_KEY", "")
    BASE_URL = os.environ.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
    MODEL = os.environ.get("DEEPSEEK_MODEL", "deepseek-reasoner")
    
    # 文件路径
    INPUT_FILE = "data/new_0206.jsonl"
    OUTPUT_FILE = "data/formated_translated.json"
    
    print("=" * 60)
    print("DeepSeek 翻译智能体")
    print("=" * 60)
    
    # 1. 初始化翻译器
    print("\n初始化 DeepSeek 翻译器...")
    translator = DeepSeekTranslator(API_KEY, BASE_URL, MODEL)
    print("✓ 翻译器初始化完成")
    
    # 2. 读取最新的 FALSE 记录
    print(f"\n从 {INPUT_FILE} 读取最新的 Result 为 FALSE 的记录...")
    latest_record = get_latest_false_record(INPUT_FILE)
    
    if not latest_record:
        print("没有找到需要翻译的记录")
        return
    
    print(f"✓ 找到最新记录: ID={latest_record['id']}")
    
    # 3. 翻译记录
    print("\n开始翻译...")
    translated_record = translate_record(latest_record, translator)
    
    # 4. 保存结果
    print("\n保存翻译结果...")
    save_translated_data(translated_record, OUTPUT_FILE)
    
    print("\n" + "=" * 60)
    print("翻译完成！")
    print("=" * 60)


if __name__ == "__main__":
    main()
