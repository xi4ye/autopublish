# -*- coding: utf-8 -*-
"""
通用内容配置文件
包含介绍语、免责声明、结束语等可复用内容
"""

INTRO = """
大家好，欢迎来到今日新闻鉴别报告！

在这个信息爆炸的时代，我们每天都会接触到大量的新闻资讯。然而，并非所有新闻都是真实可靠的。为了帮助大家辨别真伪，我们每天精选热点新闻进行深度分析。

今天我们要鉴别的新闻是：
"""

DISCLAIMER = """
【免责声明】
本文内容仅供参考，不构成任何投资建议或决策依据。新闻鉴别结果基于公开信息和AI分析，可能存在偏差。如有疑问，请以官方发布信息为准。转载请注明出处。
"""

ENDING = """
感谢您的阅读！

如果您觉得这份报告对您有帮助，欢迎点赞、收藏和分享。您的支持是我们持续更新的动力！

我们明天再见！👋
"""

FOOTER = """
━━━━━━━━━━━━━━━━━━
🔍 每日新闻鉴别 | 让真相不再迷雾
━━━━━━━━━━━━━━━━━━
"""


def generate_title(news_title, style='question'):
    """
    生成有吸引力的标题
    
    Args:
        news_title: 新闻标题
        style: 标题风格
            - question: 疑问式 "XXX是真的吗？"
            - reveal: 揭秘式 "真相揭秘：XXX"
            - shock: 震惊式 "震惊！XXX竟然是..."
            - verify: 求证式 "新闻求证：XXX"
            - fact: 事实式 "【事实核查】XXX"
    
    Returns:
        生成的标题
    """
    # 截断过长的标题
    short_title = news_title[:50] + "..." if len(news_title) > 50 else news_title
    
    styles = {
        'question': f"「{short_title}」是真的吗？",
        'reveal': f"真相揭秘：「{short_title}」",
        'shock': f"震惊！「{short_title}」真相竟然是...",
        'verify': f"新闻求证：「{short_title}」",
        'fact': f"【事实核查】{short_title}",
    }
    
    return styles.get(style, styles['question'])


def generate_wx_title(news_title, style='question'):
    """
    生成微信公众号标题（限制64字符）
    """
    title = generate_title(news_title, style)
    if len(title) > 64:
        title = title[:61] + "..."
    return title


def generate_jr_title(news_title, style='question'):
    """
    生成今日头条标题
    """
    return generate_title(news_title, style)


def get_docx_content(title=''):
    """获取 Word 文档的内容"""
    intro = f"""
大家好，欢迎来到今日新闻鉴别报告！

今天我们要鉴别的新闻是：「{title}」
"""
    return intro


# 标题风格说明
TITLE_STYLES = {
    'question': '疑问式 - 引发读者好奇心',
    'reveal': '揭秘式 - 强调真相揭示',
    'shock': '震惊式 - 制造悬念和冲击',
    'verify': '求证式 - 专业严谨风格',
    'fact': '事实式 - 强调客观核查',
}
