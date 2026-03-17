import json
import os
import argparse

if 'SSLKEYLOGFILE' in os.environ:
    del os.environ['SSLKEYLOGFILE']

from create_detailed_news_template import SmartImageGenerator, TemplateStyle
from translate_agent import DeepSeekTranslator
from data_adapter import format_for_template


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


def translate_record(record, translator):
    translated_record = {
        'id': record['id'],
        'description': record['description'],
        'history': record['history'],
        'last_output': {}
    }
    
    for k, content in record.get('last_output', {}).items():
        if content and content.strip():
            try:
                translated_content = translator.translate_markdown(content)
                translated_record['last_output'][k] = translated_content
            except Exception as e:
                print(f"    翻译失败: {e}")
                translated_record['last_output'][k] = content
        else:
            translated_record['last_output'][k] = content
    
    return translated_record


def main():
    parser = argparse.ArgumentParser(description='批量生成新闻海报')
    parser.add_argument('-n', type=int, default=100, help='生成倒数前n条FALSE记录的海报（默认100）')
    parser.add_argument('--skip-translate', action='store_true', help='跳过翻译步骤（使用已翻译数据）')
    args = parser.parse_args()
    
    print("=" * 60)
    print("批量生成新闻海报")
    print("=" * 60)
    
    INPUT_FILE = "data/new_0206.jsonl"
    OUTPUT_DIR = "result"
    
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
        print(f"\n创建输出目录: {OUTPUT_DIR}")
    
    print(f"\n从 {INPUT_FILE} 读取 FALSE 记录...")
    false_records = get_false_records(INPUT_FILE)
    
    if not false_records:
        print("没有找到 FALSE 记录")
        return
    
    total = len(false_records)
    n = min(args.n, total)
    print(f"✓ 共找到 {total} 条 FALSE 记录，将处理前 {n} 条")
    
    translator = None
    if not args.skip_translate:
        print("\n初始化翻译器...")
        translator = DeepSeekTranslator(API_KEY, BASE_URL, MODEL)
    
    success_count = 0
    fail_count = 0
    
    for i in range(n):
        record = false_records[i]
        record_id = record['id']
        output_path = os.path.join(OUTPUT_DIR, f"poster_{record_id}.png")
        
        print(f"\n[{i+1}/{n}] 处理记录 ID: {record_id}")
        print(f"  标题: {record['description'][:50]}...")
        
        try:
            if args.skip_translate:
                translated_record = record
            else:
                print("  正在翻译...")
                translated_record = translate_record(record, translator)
            
            print("  正在格式化数据...")
            formatted_data = format_for_template(translated_record)
            
            print("  正在生成海报...")
            generator = SmartImageGenerator(external_data=formatted_data)
            generator.generate_image(
                style=TemplateStyle.TECH,
                output_path=output_path
            )
            
            print(f"  ✓ 海报已保存: {output_path}")
            success_count += 1
            
        except Exception as e:
            print(f"  ✗ 生成失败: {e}")
            fail_count += 1
    
    print("\n" + "=" * 60)
    print("批量生成完成！")
    print(f"成功: {success_count} 条")
    print(f"失败: {fail_count} 条")
    print(f"输出目录: {OUTPUT_DIR}")
    print("=" * 60)


if __name__ == "__main__":
    main()
