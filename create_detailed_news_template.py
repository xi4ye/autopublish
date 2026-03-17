from PIL import Image, ImageDraw, ImageFont
from enum import Enum
import os
import re
import json

class TemplateStyle(Enum):
    TECH = 1
    LIGHT = 2
    DARK = 3

class SmartImageGenerator:
    def __init__(self, external_data=None):
        # 统一颜色风格
        self.path = os.path.dirname(os.path.abspath(__file__))
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
                'third_color':(12,64,38),
                'news_font_color':self.news_font_color,
                'news_title_font_color':(0,90,99),
                'small_banner_color': (0, 2, 148),
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
                'news_date_font': ImageFont.truetype(os.path.join(self.path,"fonts/simhei.ttf"), 28),
                'news_id_font': ImageFont.truetype(os.path.join(self.path,"fonts/simhei.ttf"), 32),
                'title_font' : ImageFont.truetype(os.path.join(self.path,"fonts/simfang.ttf"), 36),
                'main_title_font' : ImageFont.truetype(os.path.join(self.path,"fonts/simhei.ttf"), 48),
                'subtitle_font' : ImageFont.truetype(os.path.join(self.path,"fonts/SourceHanSansSC-Bold-2.otf"), 34),
                'smalltitle_font' : ImageFont.truetype(os.path.join(self.path,"fonts/SourceHanSansSC-Bold-2.otf"), 30),
                'content_font' : ImageFont.truetype(os.path.join(self.path,"fonts/simhei.ttf"), 28),
                'footer_font' : ImageFont.truetype(os.path.join(self.path,"fonts/simhei.ttf"), 20),
                'emoji_font': ImageFont.truetype(os.path.join(self.path,"fonts/seguiemj.ttf"), 28)  # 确保字体路径正确
            }
        }
        self.news = None  # 用于存储新闻数据
        self.content = ""
        
        # 如果提供了外部数据，使用外部数据；否则从文件读取
        if external_data:
            self.data = external_data
        else:
            with open(os.path.join(self.path,'data/formated_translated1.json'), 'r', encoding='utf-8') as file:
                self.data = json.load(file)
        
        self._format_json()  # 格式化JSON数据给 -> self.content
        if self.news['language'] == 'en-US':
            self.templates[TemplateStyle.TECH]['content_font'] = ImageFont.truetype(os.path.join(self.path,"fonts/SourceHanSansSC-Regular-2.otf"), 28)
            # self.templates[TemplateStyle.TECH]['subtitle_font'] = ImageFont.truetype("arial.ttf", 32)
            self.templates[TemplateStyle.TECH]['main_title_font'] = ImageFont.truetype(os.path.join(self.path,"fonts/SourceHanSansSC-Regular-2.otf"), 32)

    def _get_text_dimensions(self, text, font):
        """获取文本的宽度和高度"""
        dummy_img = Image.new('RGB', (1, 1))
        draw = ImageDraw.Draw(dummy_img)
        bbox = draw.textbbox((0, 0), text, font=font)
        return bbox[2] - bbox[0], bbox[3] - bbox[1]  # width, height
    
    def _smart_wrap_text(self, text, font,max_width=550,line_spacing=20):
        """智能换行处理，确保每行长度相同"""
        lines = []
        total_height = 0
        
        if text:
            for paragraph in text.split('\n'):
                if not paragraph.strip():
                    lines.append("")  # 保留空行
                    continue
                    
                # 按段落分割（中文句号、问号等）

                current_sentence = ""
                line_width = 0
               
                img = Image.new('RGB', (1, 1), (255, 255, 255))
                draw = ImageDraw.Draw(img)
                line_height = font.getbbox('A')[3] - font.getbbox('A')[1]
                for char in paragraph:

                    current_sentence += char
                    if char in { '？', '！','。',}:
                        lines.append(current_sentence.strip())
                        current_sentence = ""
                        line_width = 0
                        continue
                    bbox = draw.textbbox((0, 0), char, font=font)
                    char_width = bbox[2] - bbox[0]  # 计算字符宽度
                    line_width += char_width  # 加上间距
                    if line_width > max_width:
                        lines.append(current_sentence.strip())
                        current_sentence = ""
                        line_width = 0

                # 处理最后一个句子
                if current_sentence:
                    lines.append(current_sentence.strip())        

                total_height = len(lines) * (line_height + line_spacing + 2)
                if lines and lines[-1]:  # 减去最后一行多余的行间距
                    total_height -= line_spacing
        pattern_roman = re.compile(r'^[ⅠⅡⅢⅣⅤⅥⅦⅧⅨⅩ]+\.\s*.+')  # 罗马数字标题
        pattern_summary = re.compile(r'^[^\d\W]+(?:分类|分析|问题|佐证|支持)：?$')  # 总结性标题

        for line in lines:
            if pattern_roman.match(line) or pattern_summary.match(line) :  
                total_height += 20
        return lines,total_height
    
    def _calculate_content_dimensions(self, text, font, config):
        """计算内容的总高度和最大宽度"""
        import re
        pattern_roman = re.compile(r'^[ⅠⅡⅢⅣⅤⅥⅦⅧⅨⅩ]+\.\s*.+')  # 罗马数字标题
        pattern_summary = re.compile(r'^[^\d\W]+(?:分类|分析|问题|佐证|支持)：?$')  # 总结性标题
        
        # 不再使用传入的 text，而是使用 self.news 中的实际内容
        # 计算各个部分的实际高度
        
        # 1. 新闻标题部分的高度
        title_lines, title_height = self._smart_wrap_text(self.news.get('news_title', ''), config['subtitle_font'])
        
        # 2. 新闻摘要部分的高度（如果有）
        summary_height = 0
        if 'news_summary' in self.news and self.news['news_summary']:
            _, summary_height = self._smart_wrap_text(self.news['news_summary'], config['content_font'])
        
        # 3. 虚假类型部分的高度
        fake_title_lines, fake_title_height = self._smart_wrap_text(self.news.get('news_title', ''), config['smalltitle_font'])
        fake_result_lines, fake_result_height = self._smart_wrap_text(self.news.get('result', ''), config['smalltitle_font'])
        fake_detail_lines, fake_detail_height = self._smart_wrap_text(self.news.get('typeof_fake', ''), config['content_font'])
        
        # 计算虚假类型部分中罗马数字标题的额外高度
        fake_roman_extra_height = 0
        for line in fake_detail_lines:
            if pattern_roman.match(line) or pattern_summary.match(line):
                fake_roman_extra_height += 20  # 每个特殊标题额外20像素
        
        # 虚假类型部分的总高度 = 标题 + 结果 + 详细内容 + 额外间距 + 罗马数字标题额外高度
        fake_section_height = (
            fake_title_height + 
            fake_result_height + 
            fake_detail_height + 
            2 * config['line_height'] + 20 +  # 额外的行间距
            fake_roman_extra_height  # 罗马数字标题额外高度
        )
        
        # 4. 证据链部分的高度
        evidence_lines, evidence_height = self._smart_wrap_text(self.news.get('ident_evid', ''), config['content_font'])
        
        # 计算证据链部分中罗马数字标题的额外高度
        evidence_roman_extra_height = 0
        for line in evidence_lines:
            if pattern_roman.match(line) or pattern_summary.match(line):
                evidence_roman_extra_height += 20  # 每个特殊标题额外20像素
        
        evidence_height += evidence_roman_extra_height
        
        # 5. 相关新闻部分的高度
        related_lines, related_height = self._smart_wrap_text(self.news.get('reve_news', ''), config['content_font'])
        
        # 计算相关新闻部分中罗马数字标题的额外高度
        related_roman_extra_height = 0
        for line in related_lines:
            if pattern_roman.match(line) or pattern_summary.match(line):
                related_roman_extra_height += 20  # 每个特殊标题额外20像素
        
        related_height += related_roman_extra_height
        
        # 计算总高度（包括各部分之间的间距）
        section_spacing = config['line_height_to_each_content']
        total_height = (
            title_height + summary_height +  # 标题和摘要
            fake_section_height +  # 虚假类型部分
            evidence_height +  # 证据链部分
            related_height +  # 相关新闻部分
            3 * section_spacing  # 三个部分之间的间距
        )
        
        # 添加安全边距，确保内容不会被截断
        total_height += 300
        
        max_line_width = 500  # 与 example 版本一致
        return max_line_width, total_height
    
    def generate_image(self,style=TemplateStyle.TECH, output_path="output.png"):
        config = self.templates.get(style, self.templates[TemplateStyle.TECH])
        title = '详细鉴别报告'
        product_info = "正本清源，言归真章"
        # 计算标题尺寸
        title_width, title_height = self._get_text_dimensions(title, config['title_font'])
        
        # 计算主内容尺寸（使用智能换行）
        content_width, content_height = self._calculate_content_dimensions(self.content, config['content_font'], config)
        
        # # 计算产品信息尺寸（如果有）
        product_width, product_height = 0, 0
        # if product_info:
        #     subtitle_width, _ = self._get_text_dimensions("产品介绍", config['subtitle_font'])
        #     p_width, p_height = self._calculate_content_dimensions(product_info, config['content_font'], config)
        #     product_width = max(subtitle_width, p_width)
        #     product_height = 80 + p_height
            
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
        banner_img = Image.open(os.path.join(self.path,'output/banner.png')).convert("RGBA")
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
        # self._smart_wrap_text(self.content, config['content_font'])
        y_position = self._draw_wrapped_text(img, draw, y_position, total_width, config)


        # 5. 页眉（footer）
        footer_img = Image.open(os.path.join(self.path,'output/footer.png')).convert("RGBA")
        img.paste(footer_img,(0, total_height - config['footer_height']),footer_img)
        # self._draw_footer(img, draw, total_width, total_height, config['footer_height'],config)

        img.save(os.path.join(self.path,output_path))
        print(f"图片已成功生成，尺寸: {total_width}x{total_height}，保存到: {output_path}")
        return img
    
    def _draw_wrapped_text(self, img, draw, y_position, total_width, config):
        """绘制经过智能换行处理的文本"""
        x = config['margins']  # 预留一些空间给
        true_img = Image.open(os.path.join(self.path,"imgs/tick.png")).convert("RGBA").resize((50, 50))
        false_img = Image.open(os.path.join(self.path,"imgs/alert.png")).convert("RGBA").resize((50, 50))
    

        news_date_text = f"{self.news['news_date']}"
        news_id_text = f"ID：{self.news['news_id']}"
        date_width, date_height = self._get_text_dimensions(news_date_text, config['news_date_font'])
        # id_width, id_height = self._get_text_dimensions(news_id_text, config['news_id_font'])
        # 绘制日期
        r = 4
        draw.ellipse((x - 14, y_position + date_height // 2, x - 6, y_position + date_height // 2 + 8), fill="black", outline="black", width=3)
        draw.text((x + 10, y_position), news_date_text, font=config['news_date_font'], fill=config['third_color'])
        draw.text((x + date_width + 210, y_position), news_id_text, font=config['news_id_font'], fill=config['secondary_color'])

        y_position += config['line_height_to_title']  # 每条新闻的标题高度

        if self.news['result'] == '正确':
            img.paste(true_img, (x + 10, y_position - 5), true_img)
        else:  
            img.paste(false_img, (x + 10, y_position - 5), false_img)

        line_length = 0

        wrapped_lines ,_= self._smart_wrap_text(f"{self.news['news_title']}", config['subtitle_font'])

        # 绘制标题
        for line in wrapped_lines:
            if not line:  # 空行（段落分隔）
                y_position += config['paragraph_spacing']
                continue
                
            draw.text((x + 60, y_position), line, font=config['subtitle_font'], fill=config['third_color'])
            y_position += config['line_height']
            line_length += config['line_height']

        try:
            wrapped_lines ,_= self._smart_wrap_text(f"{self.news['news_summary']}", config['content_font'])

            # 绘制摘要
            for line in wrapped_lines:
                if not line:  # 空行（段落分隔）
                    y_position += config['paragraph_spacing']
                    continue
                    
                draw.text((x + 60, y_position), line, font=config['content_font'], fill=config['news_font_color'])
                y_position += config['line_height']
                line_length += config['line_height'] 

            # 绘制竖线
            draw.line((x - 10, y_position - line_length + 10, x - 10, y_position - 10),fill=config['news_font_color'],width=2)
        except KeyError:
            pass
        y_position += config['line_height_to_each_content']  # 每条新闻的内容高度       
        pattern_roman = re.compile(r'^[ⅠⅡⅢⅣⅤⅥⅦⅧⅨⅩ]+\.\s*.+')  # 罗马数字标题
        pattern_summary = re.compile(r'^[^\d\W]+(?:分类|分析|问题|佐证|支持)：?$')  # 总结性标题
        # 绘制虚假类型
        line_length = 0
        draw.ellipse((x - 14, y_position + date_height // 2, x - 6, y_position + date_height // 2 + 8), fill="black", outline="black", width=3)

        # 根据判定结果显示不同的标题和颜色
        if self.news.get('is_true', False):
            type_label = '【真实类型】'
            result_color = "green"
        else:
            type_label = '【虚假类型】'
            result_color = "red"
        
        draw.text((x + 10,y_position - 10), type_label, font=config['subtitle_font'], fill=config['small_banner_color'])
        y_position += config['line_height'] + 20
        
        wrapped_lines1 ,height1 = self._smart_wrap_text(self.news['news_title'], config['smalltitle_font'])
        warpped_lines2 ,height2 = self._smart_wrap_text(self.news['result'], config['smalltitle_font'])
        wrapped_lines3 ,height3 = self._smart_wrap_text(self.news['typeof_fake'], config['content_font'])

        # 绘制背景 - 固定宽度 650px
        actual_fake_height = height1 + height2 + height3 + 3 * config['line_height']
        rect_right = x + 650  # 固定宽度
        draw.rounded_rectangle((x + 30,y_position - 10,rect_right,y_position + actual_fake_height), radius=20, fill='white', outline='white', width=2)
        for line in wrapped_lines1:
            draw.text((x + 60, y_position), line, font=config['smalltitle_font'], fill=config['news_title_font_color'])
            y_position += config['line_height'] + 20
        draw.text((x + 60, y_position), '→  ' + self.news['result'], font=config['smalltitle_font'], fill=result_color) 
        y_position += config['line_height'] + 20
        for line in wrapped_lines3:
            if not line:  # 空行（段落分隔）
                y_position += config['paragraph_spacing']
                continue
            if pattern_roman.match(line) or pattern_summary.match(line):
                draw.text((x + 60, y_position), line, font=config['smalltitle_font'], fill=config['news_title_font_color'])
                y_position += config['line_height'] + 20
                continue 
 
            draw.text((x + 60, y_position), line, font=config['content_font'], fill=config['news_font_color'])
            y_position += config['line_height']
            line_length += config['line_height'] 

        # 绘制竖线 - 使用实际计算的高度
        draw.line((x - 10, y_position - actual_fake_height, x - 10, y_position),fill=config['news_font_color'],width=2)
        y_position += config['line_height_to_each_content']

        # 绘制证据链
        line_length = 0
        draw.ellipse((x - 14, y_position + date_height // 2, x - 6, y_position + date_height // 2 + 8), fill="black", outline="black", width=3)

        draw.text((x + 10,y_position - 10),'【证据链】',font=config['subtitle_font'], fill=config['small_banner_color'])
        y_position += config['line_height'] + 20
        wrapped_lines ,height= self._smart_wrap_text(f"{self.news['ident_evid']}", config['content_font'])
        emojis = ['😌','😬','🤨','🤔','😉','🤗']
        idx = 0
        idxs = ['一', '二', '三', '四','五','六']
        
        # 绘制圆角矩形 - 固定宽度 650px
        rect_right = x + 650
        draw.rounded_rectangle((x + 30,y_position - 10,rect_right,y_position + height), radius=20, fill='white', outline='white', width=2)
        for line in wrapped_lines:
            if not line:  # 空行（段落分隔）
                y_position += config['paragraph_spacing']
                continue

            if pattern_roman.match(line) or pattern_summary.match(line):
                draw.text((x + 60, y_position), line, font=config['smalltitle_font'], fill=config['news_title_font_color'])
                y_position += config['line_height'] + 20
                continue 
       
            draw.text((x + 60, y_position), line, font=config['content_font'], fill=config['news_font_color'])
            y_position += config['line_height']
        # 绘制竖线 - 使用实际计算的高度
        draw.line((x - 10, y_position - height, x - 10, y_position - 10),fill=config['news_font_color'],width=2)
 
        y_position += config['line_height_to_each_content']  # 每条新闻的内容高度       

        # 绘制相关新闻
        line_length = 0
        draw.ellipse((x - 14, y_position + date_height // 2, x - 6, y_position + date_height // 2 + 8), fill="black", outline="black", width=3)

        draw.text((x + 10,y_position - 10),'【相关新闻】',font=config['subtitle_font'], fill=config['small_banner_color'])
        y_position += config['line_height'] + 20
        wrapped_lines ,height= self._smart_wrap_text(f"{self.news['reve_news']}", config['content_font'])
        
        # 绘制圆角矩形 - 固定宽度 650px
        rect_right = x + 650
        draw.rounded_rectangle((x + 30,y_position - 10,rect_right,y_position + height), radius=20, fill='white', outline='white', width=2)
        idx = 0
        for line in wrapped_lines:
            if not line:  # 空行（段落分隔）
                y_position += config['paragraph_spacing']
                continue

            if pattern_roman.match(line) or pattern_summary.match(line):
                draw.text((x + 60, y_position), line, font=config['smalltitle_font'], fill=config['news_title_font_color'])
                y_position += config['line_height'] + 20
                line_length += config['line_height']
                continue                 
            draw.text((x + 60, y_position), line, font=config['content_font'], fill=config['news_font_color'])
            y_position += config['line_height']


        # 绘制竖线 - 使用实际计算的高度
        draw.line((x - 10, y_position - height, x - 10, y_position - 10),fill=config['news_font_color'],width=2)
         
        return y_position
    

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
        jb = Image.open(os.path.join(self.path,'jb.png')).convert("RGBA").resize((width, height))
        img.paste(jb,(0,0))
        logo_img = Image.open(os.path.join(self.path,"logo1_1.png")).convert("RGBA").resize((160, 160))
        text = "正本清源 言归真章"
        logo_img_y = height // 2 - logo_img.height // 2

        # 绘制logo
        img.paste(logo_img, (20, logo_img_y), logo_img)

        # 绘制文字
        text_width, text_height = self._get_text_dimensions(text, config['main_title_font'])
        text_x = width - text_width - 20
        text_y = height // 2 - text_height // 2
        draw.text((text_x, text_y), text, font=config['main_title_font'], fill='white')
    
    def _format_json(self):
        """格式化JSON数据为内容"""
        self.news = {}

        self.news['news_title'] = self.data['description']
        self.news['news_date'] = self.data['Date']
        self.news['news_id'] = self.data['id']
        # self.news['ident_evid'] = self.data.get('ident_evid', '无')
        ident = self.data['CONCLUSION']['FinalJudgment'] == 'TRUE'
        if ident:
            ident = '正确'
        else:
            ident = '虚假'
        
        # 构建分析证据文本，包含 COLLECTION 和 ANALYSIS
        analysis_text = ""
        
        # 添加 COLLECTION（分析师报告）
        if self.data.get('COLLECTION'):
            if isinstance(self.data['COLLECTION'], list):
                # 新格式：数组
                collection_text = "分析师报告\n\n记录所有分析师报告一个接一个:\n"
                for report in self.data['COLLECTION']:
                    collection_text += f"-分析师报告{report['id']} (重要性评分:{report['score']}){report['content']}\n"
                analysis_text += collection_text + "\n\n"
            else:
                # 旧格式：字符串（兼容）
                collection_text = self.data['COLLECTION']
                collection_text = re.sub(r'####\s*\*\*', '', collection_text)
                collection_text = re.sub(r'\*\*', '', collection_text)
                collection_text = re.sub(r'---', '', collection_text)
                collection_text = re.sub(r'^-\s*', '', collection_text, flags=re.MULTILINE)
                analysis_text += "分析师报告\n\n" + collection_text + "\n\n"
        
        # 添加 ANALYSIS（支持证据）
        if isinstance(self.data['ANALYSIS'], dict):
            # 检查是新格式（有 summary 和 evidence）还是旧格式
            if 'summary' in self.data['ANALYSIS'] and 'evidence' in self.data['ANALYSIS']:
                # 新格式：数组
                analysis_text += self.data['ANALYSIS']['summary'] + "\n\n支持证据:\n"
                for evidence in self.data['ANALYSIS']['evidence']:
                    analysis_text += f"{evidence['id']}. {evidence['title']}:{evidence['content']}\n"
            else:
                # 旧格式：拼接各个分析部分
                if self.data['ANALYSIS'].get('信息收集'):
                    analysis_text += "一、信息收集\n\n" + self.data['ANALYSIS']['信息收集'] + "\n\n"
                if self.data['ANALYSIS'].get('分析评估'):
                    analysis_text += "二、分析评估\n\n" + self.data['ANALYSIS']['分析评估'] + "\n\n"
                if self.data['ANALYSIS'].get('结论判定'):
                    analysis_text += "三、结论判定\n\n" + self.data['ANALYSIS']['结论判定'] + "\n\n"
        else:
            # 如果是字符串，清理 markdown 符号后使用
            if self.data.get('ANALYSIS'):
                analysis_str = self.data['ANALYSIS']
                analysis_str = re.sub(r'####\s*\*\*', '', analysis_str)
                analysis_str = re.sub(r'\*\*', '', analysis_str)
                analysis_str = re.sub(r'---', '', analysis_str)
                analysis_text += analysis_str
        
        self.news['ident_evid'] = analysis_text
        
        # 处理 DetailedReasons
        detailed_reasons_data = self.data['CONCLUSION']['DetailedReasons']
        if isinstance(detailed_reasons_data, list):
            # 新格式：数组
            detailed_reasons = ""
            for reason in detailed_reasons_data:
                detailed_reasons += f"{reason['id']}. {reason['title']}\n{reason['content']}\n\n"
        else:
            # 旧格式：字符串（兼容）
            detailed_reasons = detailed_reasons_data
            detailed_reasons = re.sub(r'####\s*\*\*', '', detailed_reasons)
            detailed_reasons = re.sub(r'\*\*', '', detailed_reasons)
            detailed_reasons = re.sub(r'---', '', detailed_reasons)
        self.news['typeof_fake'] = '\n错误分类分析\n' + detailed_reasons.strip()
        # 从相关新闻集合中选取最多三条新闻，转换为换行符分隔的字符串（包含标题和URL）
        # 兼容两种拼写：relevant_news（正确）和 revelent_news（错误）
        relevant_news_data = self.data.get('relevant_news') or self.data.get('revelent_news', {})
        relevant_news_collection = relevant_news_data.get('collection', [])
        selected_news = relevant_news_collection[:3]  # 只选取前三条新闻
        news_items = []
        idx = ['①','②','③']
        
        for index,news in enumerate(selected_news):
            if 'title' in news:
                if 'url' in news:
                    # 提取URL中的实际链接（去掉"url:"前缀）
                    url = news['url'].replace('url:', '') if news['url'].startswith('url:') else news['url']
                    news_items.append(f"{idx[index]}{news['title']}\n{url}")
                else:
                    news_items.append(news['title'])
        self.news['reve_news'] = '\n\n'.join(news_items)
        for key in self.news:
            try:
                self.content += f"{self.news[key]}。\n"
            except KeyError:
                continue

        self.news['result'] = '正确' if self.data['CONCLUSION']['FinalJudgment'] == 'TRUE' else '虚假'
        self.news['is_true'] = self.data['CONCLUSION']['FinalJudgment'] == 'TRUE'
        self.news['language'] = 'zh-CN'

    
       


# 使用示例
if __name__ == "__main__":
    generator = SmartImageGenerator()

    # 测试长文本（包含超过30个字符的行）
    # with open('detailed_news.json', 'r', encoding='utf-8') as file:
    #     data = json.load(file)

    # 生成图片
    generator.generate_image(
        style=TemplateStyle.TECH,
        output_path="image2.png"
    )

    # 打开主图和要叠加的小图

    # 这里的风格是可以选择的。有TECH和BUSINESS两种风格。
