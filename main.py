from create_detailed_news_template import TemplateStyle, SmartImageGenerator
from create_template import create_template
from fenmian import create_soft_shadow_border as create_fenmian
import json
from autojr_pydoll import auto_publish_jr
from translate_agent import get_latest_false_record
from data_adapter import format_for_template
from translate_formatted import translate_formatted_json


def app():
    print("=" * 60)
    print("第一步：读取原始数据")
    print("=" * 60)
    
    INPUT_FILE = "data/new_0206.jsonl"
    
    print(f"\n从 {INPUT_FILE} 读取最新的 Result 为 FALSE 的记录...")
    latest_record = get_latest_false_record(INPUT_FILE)
    
    if not latest_record:
        print("没有找到需要处理的记录")
        return
    
    print(f"✓ 找到最新记录: ID={latest_record['id']}")
    
    print("\n" + "=" * 60)
    print("第二步：格式化数据（先提取字段，不翻译）")
    print("=" * 60)
    
    print("\n解析原始英文内容，提取所有字段...")
    formatted_data = format_for_template(latest_record)
    
    print(f"\n格式化结果:")
    print(f"  - COLLECTION: {len(formatted_data['COLLECTION'])} 条")
    print(f"  - ANALYSIS.evidence: {len(formatted_data['ANALYSIS']['evidence'])} 条")
    print(f"  - CONCLUSION.DetailedReasons: {len(formatted_data['CONCLUSION']['DetailedReasons'])} 条")
    print(f"  - FinalJudgment: {formatted_data['CONCLUSION']['FinalJudgment']}")
    
    print("\n" + "=" * 60)
    print("第三步：翻译格式化后的数据")
    print("=" * 60)
    
    print("\n翻译 COLLECTION、ANALYSIS.evidence、DetailedReasons...")
    translated_data = translate_formatted_json(formatted_data)
    
    TRANSLATED_FILE = "data/formated_translated.json"
    with open(TRANSLATED_FILE, 'w', encoding='utf-8') as f:
        json.dump(translated_data, f, ensure_ascii=False, indent=2)
    print(f"\n✓ 翻译完成，保存到: {TRANSLATED_FILE}")
    
    print("\n" + "=" * 60)
    print("第四步：生成海报")
    print("=" * 60)
    
    title = translated_data['description']
    
    generator = SmartImageGenerator(external_data=translated_data)

    generator.generate_image(
        style=TemplateStyle.TECH,
        output_path="output/image2.png"
    )    
    create_fenmian(
        border_width=40,
        margin=40,
        font_size=42,
        main_text=title,
        text_top_margin=30,
        text_left_margin=30,
        special_font_size=42,
        platform='jr'
    )
    
    create_fenmian(
        border_width=80,
        margin=80,
        font_size=168,
        main_text=title,
        text_top_margin=100,
        text_left_margin=100,
        special_font_size=168,
        platform='wx'
    )
    
    create_template(platform='jr')


if __name__ == "__main__":
    app()
