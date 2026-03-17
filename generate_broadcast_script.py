import json
import os
import argparse

if 'SSLKEYLOGFILE' in os.environ:
    del os.environ['SSLKEYLOGFILE']

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage


API_KEY = os.environ.get("DEEPSEEK_API_KEY", "")
BASE_URL = os.environ.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
MODEL = os.environ.get("DEEPSEEK_MODEL", "deepseek-reasoner")


def get_false_records(jsonl_file):
    false_records = []
    with open(jsonl_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    for line in reversed(lines):
        data = json.loads(line.strip())
        history = data.get('history', {})
        for k, history_list in history.items():
            if history_list and history_list[0].get('Result') == 'FALSE':
                false_records.append(data)
                break
    return false_records


def generate_broadcast_script(news_data):
    llm = ChatOpenAI(
        api_key=API_KEY,
        base_url=BASE_URL,
        model=MODEL,
        temperature=0.3
    )
    
    description = news_data.get('description', '')
    last_output = news_data.get('last_output', {})
    analysis_content = last_output.get('k=5', '')
    
    system_prompt = """你是一个专业的新闻播报撰稿人。你的任务是将新闻鉴别报告转换为适合口播的新闻文稿。

要求：
1. 开头使用"各位观众晚上好。下面播报一则XX快讯。"（XX根据新闻类型选择：科技/财经/社会/政治等）
2. 简洁明了地陈述新闻标题和核心事实
3. 说明新闻的鉴别结果（真/假）及主要原因
4. 语言口语化，适合朗读，避免书面语
5. 结尾使用"新闻播报完毕。"
6. 总字数控制在200-300字
7. 不要添加任何解释或额外文字，只输出播报文稿"""

    human_prompt = f"""请根据以下新闻鉴别报告，生成一段口播新闻文稿：

新闻标题：{description}

鉴别分析报告：
{analysis_content}

请生成口播文稿："""

    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=human_prompt)
    ]
    
    response = llm.invoke(messages)
    return response.content


def main():
    parser = argparse.ArgumentParser(description='生成新闻口播文稿')
    parser.add_argument('-n', type=int, default=1, help='输出倒数第n个FALSE记录的口播文稿（默认为1，即最新一条）')
    args = parser.parse_args()
    
    print("=" * 60)
    print("口播文稿生成测试")
    print("=" * 60)
    
    INPUT_FILE = "data/new_0206.jsonl"
    OUTPUT_FILE = "口播文稿.txt"
    
    print(f"\n从 {INPUT_FILE} 读取 FALSE 记录...")
    false_records = get_false_records(INPUT_FILE)
    
    if not false_records:
        print("没有找到 FALSE 记录")
        return
    
    total = len(false_records)
    if args.n < 1 or args.n > total:
        print(f"错误：n 的取值范围是 1 到 {total}")
        return
    
    news_data = false_records[args.n - 1]
    
    print(f"✓ 找到第 {args.n} 条记录（共 {total} 条 FALSE 记录）")
    print(f"  记录 ID: {news_data['id']}")
    print(f"  新闻标题: {news_data['description']}")
    
    print("\n正在生成口播文稿...")
    script = generate_broadcast_script(news_data)
    
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write(script)
    
    print(f"\n✓ 口播文稿已保存到: {OUTPUT_FILE}")
    print("\n" + "=" * 60)
    print("生成的口播文稿：")
    print("=" * 60)
    print(script)


if __name__ == "__main__":
    main()
