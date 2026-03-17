from PIL import Image, ImageDraw, ImageFont
from enum import Enum
import json

class TemplateStyle(Enum):
    TECH = 1
    LIGHT = 2
    DARK = 3

class SmartImageGenerator:
    def __init__(self):
        # 统一颜色风格
        self.banner_color = (166, 187, 5)
        self.divider_color = (180, 200, 50)
        self.footer_color = (166, 187, 0)
        self.product_highlight_color = (255, 90, 0)
        self.news_font_color = (30,30,30)
        # 统一模板配置
        self.templates = {
            TemplateStyle.TECH: {
                'bg_color': (245, 245, 245),  # 统一背景色
                'primary_color': self.banner_color,
                'secondary_color': (128, 128, 128), 
                'third_color':(4,97,166),
                'news_font_color':self.news_font_color,
                'header_height': 180,
                'footer_height': 200,
                'margins': 60,
                'line_height': 42,
                'line_height_to_title': 50,
                'line_height_to_each_content': 50,
                'paragraph_spacing': 35,
                'title_spacing': 70,
                'divider_height': 35,
                'min_width': 750,
                'max_width': 1100,
                'max_chars_per_line': 18,
                'news_date_font': ImageFont.truetype("fonts/simhei.ttf", 28),
                'news_id_font': ImageFont.truetype("fonts/simhei.ttf", 32),
                'title_font' : ImageFont.truetype("fonts/simfang.ttf", 36),
                'subtitle_font' : ImageFont.truetype("fonts/simhei.ttf", 32),
                'content_font' : ImageFont.truetype("fonts/simhei.ttf", 28),
                'footer_font' : ImageFont.truetype("fonts/simhei.ttf", 20),
                'emoji_font': ImageFont.truetype("fonts/seguiemj.ttf", 32)  # 确保字体路径正确
            }
        }
        self.news_items = None  # 用于存储新闻数据
        self.content = ""
        with open('data/daily_news_example.json', 'r', encoding='utf-8') as file:
            self.news = json.load(file)
        self._format_json()  # 格式化JSON数据给 -> self.content
        
    
    def _get_text_dimensions(self, text, font):
        """获取文本的宽度和高度"""
        dummy_img = Image.new('RGB', (1, 1))
        draw = ImageDraw.Draw(dummy_img)
        bbox = draw.textbbox((0, 0), text, font=font)
        return bbox[2] - bbox[0], bbox[3] - bbox[1]  # width, height
    
    def _smart_wrap_text(self, text, max_chars):
        """智能换行处理，确保每行不超过max_chars个字符"""
        lines = []
        for paragraph in text.split('\n'):
            if not paragraph.strip():
                lines.append("")  # 保留空行
                continue
                
            # 按句子分割（中文句号、问号等）
            sentences = []
            current_sentence = ""
            for char in paragraph:
                current_sentence += char
                if char in {'。', '？', '！', '、','：'}:
                    sentences.append(current_sentence.strip())
                    current_sentence = ""
            if current_sentence:
                sentences.append(current_sentence.strip())
            
            # 处理每个句子
            for sentence in sentences:
                if len(sentence) <= max_chars:
                    lines.append(sentence)
                    continue
                
                # 需要换行的情况
                words = sentence.split()
                if len(words) == 1:  # 没有空格的情况（纯中文）
                    # 按字符数分割
                    for i in range(0, len(sentence), max_chars):
                        lines.append(sentence[i:i+max_chars])
                else:
                    # 有空格的情况（中英文混合）
                    current_line = ""
                    for word in words:
                        if len(current_line + word) <= max_chars:
                            current_line += word + " "
                        else:
                            if current_line:
                                lines.append(current_line.strip())
                            current_line = word + " "
                    if current_line:
                        lines.append(current_line.strip())
        
        return lines
    
    def _calculate_content_dimensions(self, text, font, config):
        """计算内容的总高度和最大宽度"""
        wrapped_lines = self._smart_wrap_text(text, config['max_chars_per_line'])
        max_line_width = 0
        total_height = 0
        # for news in self.news["news_list"]:


        for line in wrapped_lines:
            if not line:  # 空行（段落分隔）
                total_height += config['paragraph_spacing']
                continue
                
            line_width, _ = self._get_text_dimensions(line, font)
            max_line_width = max(max_line_width, line_width)
            total_height += config['line_height']


        for _ in range(len(self.news["news_list"])):    
            total_height += config['line_height_to_title']  # 每条新闻的标题高度
            total_height += config['line_height_to_each_content']  # 每条新闻的内容高度

    
        return max_line_width, total_height
    
    def generate_image(self,style=TemplateStyle.TECH, output_path="output.png"):
        config = self.templates.get(style, self.templates[TemplateStyle.TECH])
        title = '今日假新闻汇总'
        product_info = "正本清源，言归真章"
        # 计算标题尺寸
        title_width, title_height = self._get_text_dimensions(title, config['title_font'])
        
        # 计算主内容尺寸（使用智能换行）
        content_width, content_height = self._calculate_content_dimensions(self.content, config['content_font'], config)
        
        # # 计算产品信息尺寸（如果有）
        product_width, product_height = 0, 0
            
        # 计算总宽度（考虑边距和最大字符限制）
        total_width = max(
            config['min_width'],
            min(
                config['max_width'],
                max(title_width, content_width, product_width) + 2 * config['margins']
            )
        )
        
        # 计算总高度
        total_height = (
            config['header_height'] + 
            config['title_spacing'] + title_height + 
            config['divider_height'] + 
            content_height + 
            (product_height if product_info else 0) + 
            config['footer_height']
        )
        
        # 创建画布
        img = Image.new('RGB', (total_width, total_height), config['bg_color'])
        draw = ImageDraw.Draw(img)
        y_position = 0

        # 1. 绘制banner
        # self._draw_header(img, draw, total_width, config['header_height'],config)
        banner_img = Image.open('output/banner.png').convert("RGBA")
        img.paste(banner_img,(0,0),banner_img)
        y_position += config['header_height']

        # 绘制生成日期
        # y_position += 100
        # draw.text()

        # 2. 绘制标题
        title_x = (total_width - title_width) // 2
        draw.text((title_x, y_position + 30), title, font=config['title_font'], fill=config['secondary_color'])
        y_position += config['title_spacing'] + title_height

        # 3. 绘制横线（divider）
        line_y = y_position - 15
        line_margin = max(50, (total_width - min(total_width - 100, title_width + 120)) // 2)
        draw.line([(line_margin, line_y), (total_width - line_margin, line_y)],
                  fill=self.divider_color, width=3)
        y_position += config['divider_height']

        # 4. 主内容
        self._smart_wrap_text(self.content, config['max_chars_per_line'])
        y_position = self._draw_wrapped_text(img, draw, y_position, total_width, config)


        # 5. 页眉（footer）
        footer_img = Image.open('output/footer.png').convert("RGBA")
        img.paste(footer_img,(0, total_height - config['footer_height']),footer_img)
        # self._draw_footer(img, draw, total_width, total_height, config['footer_height'],config)

        img.save(output_path)
        print(f"图片已成功生成，尺寸: {total_width}x{total_height}，保存到: {output_path}")
        return img
    
    def _draw_wrapped_text(self, img, draw, y_position, total_width, config):
        """绘制经过智能换行处理的文本"""
        x = config['margins']  # 预留一些空间给
        true_img = Image.open(".\\imgs\\tick.png").convert("RGBA").resize((50, 50))
        false_img = Image.open(".\\imgs\\alert.png").convert("RGBA").resize((50, 50))
        for news in self.news["news_list"]:

            news_date_text = f"{news['news_date']}"
            news_id_text = f"ID：{news['news_id']}"
            date_width, date_height = self._get_text_dimensions(news_date_text, config['news_date_font'])
            # id_width, id_height = self._get_text_dimensions(news_id_text, config['news_id_font'])
            # 绘制日期
            r = 4
            draw.ellipse((x - 14, y_position + date_height // 2 - 4, x - 6, y_position + date_height // 2 + 4), fill="black", outline="black", width=3)
            draw.text((x + 10, y_position), news_date_text, font=config['news_date_font'], fill=config['third_color'])
            draw.text((x + date_width + 210, y_position), news_id_text, font=config['news_id_font'], fill=config['secondary_color'])

            y_position += config['line_height_to_title']  # 每条新闻的标题高度

            if news['result']:
                img.paste(true_img, (x + 10, y_position - 5), true_img)
            else:  
                img.paste(false_img, (x + 10, y_position - 5), false_img)

            line_length = 0

            wrapped_lines = self._smart_wrap_text(f"【{news['news_title']}】", config['max_chars_per_line'])

            # 绘制标题
            for line in wrapped_lines:
                if not line:  # 空行（段落分隔）
                    y_position += config['paragraph_spacing']
                    continue
                    
                draw.text((x + 60, y_position), line, font=config['content_font'], fill=config['news_font_color'])
                y_position += config['line_height']
                line_length += config['line_height']

            wrapped_lines = self._smart_wrap_text(f"{news['news_summary']}", config['max_chars_per_line'])

           # 绘制摘要
            for line in wrapped_lines:
                if not line:  # 空行（段落分隔）
                    y_position += config['paragraph_spacing']
                    continue
                    
                draw.text((x + 60, y_position), line, font=config['content_font'], fill=config['news_font_color'])
                y_position += config['line_height']
                line_length += config['line_height'] 

            # 绘制竖线
            draw.line((x - 10, y_position - line_length, x - 10, y_position),fill=config['news_font_color'],width=2)
 
            y_position += config['line_height_to_each_content']  # 每条新闻的内容高度       


        return y_position
    
    from PIL import Image, ImageDraw, ImageFont

    def _draw_text_with_spacing(self,img, text, letter_spacing, x, y, font_size, font_path='simfang.ttf', text_color='white'):
        draw = ImageDraw.Draw(img)        
        font = ImageFont.truetype(font_path, font_size)
        
        for char in text:
            bbox = font.getbbox(char)
            char_width = bbox[2] - bbox[0]  # 计算字符宽度

            # 绘制字符
            draw.text((x, y), char, font=font, fill=text_color)
            
            # 更新x坐标，给下一个字符增加间距
            x += char_width + letter_spacing


    def _draw_header(self,img, draw, width, height,config):
        """绘制顶部品牌栏"""
        # color = self.banner_color
        # gap = 40
        # draw.rectangle([(0, 0), (width, height)], fill=color)
        jb = Image.open('jb.png').convert("RGBA").resize((width, height))
        img.paste(jb,(0,0))
        logo_img = Image.open("logo1_1.png").convert("RGBA").resize((160, 160))
        text = "正本清源 言归真章"
        logo_img_y = height // 2 - logo_img.height // 2
        logo_img_x = width // 2 - 280
        img.paste(logo_img, (logo_img_x, logo_img_y), logo_img) 
        text_width, text_height = self._get_text_dimensions(text, config['title_font'])
        text_x = logo_img_x + 160  # 留出logo和间距
        text_y = height // 2 - text_height // 2
        # draw.text((text_x, text_y), text, font=config['title_font'], fill=(255, 255, 255))
        self._draw_text_with_spacing(img, text, 5, text_x, text_y ,config['title_font'].size)

    def _draw_footer(self, img, draw, width, total_height, footer_height,config):
        """绘制底部信息栏，并插入logo和二维码"""
        footer_y = total_height - footer_height
        # draw.rectangle([(0, footer_y), (width, total_height)], fill=self.footer_color)
        bg = Image.open('imgs/jb1.png').convert('RGBA').resize((width,total_height))
        # 插入logo和二维码
        img.paste(bg,(0,footer_y))
        try:
            logo_img = Image.open("imgs/logo2_1.png").convert("RGBA")
            qrcode_img = Image.open("output/qrcode.jpg").convert("RGBA").resize((100, 100))  # 确保二维码大小合适
            gap = 40
            # total_icons_width = logo_img.width + gap + qrcode_img.width
            # icons_x = (width - total_icons_width) // 2
            # icons_y = footer_y + footer_height - max(logo_img.height, qrcode_img.height) - 20
            # 用img.paste而不是draw.im.paste
            logo_img_y = (footer_y + total_height) // 2 - logo_img.height // 2
            logo_img_x = (width - logo_img.width - qrcode_img.width - gap) // 2
            qrcode_img_x = logo_img_x + logo_img.width + gap
            qrcode_img_y = (footer_y + total_height) // 2 - qrcode_img.height // 2  
            img.paste(logo_img, (logo_img_x, logo_img_y),logo_img)
            img.paste(qrcode_img, (qrcode_img_x,qrcode_img_y), qrcode_img)
        except Exception as e:
            print("页脚插入logo或二维码失败：", e)

                # 页脚文字
        # line1 = "以上内容由AI生成，不代表开发者立场"
        # line1_width, _ = self._get_text_dimensions(line1, config['footer_font'])
        # draw.text(((width - line1_width) // 2, qrcode_img_y + 20 + 200), line1,
        #           font=config['footer_font'], fill=(255, 255, 255))  

    def _format_json(self):
        
        for news in self.news["news_list"]:
            # self.content += f"新闻：\n"
            # self.content += f"{news['news_date']}    | ID: {news['news_id']}\n"
            self.content += f"【{news['news_title']}。】\n"
            self.content += f"*{news['news_summary']}\n"
            # self.content += f"鉴别结果：{news['result']}\n\n"
    
       

# 使用示例
if __name__ == "__main__":
    generator = SmartImageGenerator()

    # 测试长文本（包含超过30个字符的行）
    with open('daily_news_example.json', 'r', encoding='utf-8') as file:
        data = json.load(file)

    # 生成图片
    generator.generate_image(
        style=TemplateStyle.TECH,
        output_path="image2.png"
    )

    # 打开主图和要叠加的小图

    # 这里的风格是可以选择的。有TECH和BUSINESS两种风格。