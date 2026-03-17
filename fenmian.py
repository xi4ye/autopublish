from PIL import Image, ImageDraw, ImageFont, ImageFilter
import textwrap
import json
def create_soft_shadow_border(
    img_size=(3370, 1436),
    border_width=20,
    margin=40,
    shadow_offset=(3, 3),
    shadow_blur=6,
    shadow_opacity=60,
    color_start=(165, 186, 5),
    font_size=24,
    color_end=(69, 166, 120),
    main_text="这是一段带自动换行的主文本，边框添加了柔和阴影效果。优化后的阴影不会产生深色外围，过渡更自然。",
    special_text="是真的吗",
    main_text_color=(0, 0, 0),
    special_text_color=(255, 0, 0),
    special_font_size=24,
    text_top_margin=30,
    text_left_margin=30,
    platform='jr',
    timestamp=None
):  
    if platform=='jr':
        img_size=(656, 511)
    elif platform=='wx':
        img_size=(3370, 1436)
    # 创建基础图像（带alpha通道用于阴影）
    img_w, img_h = img_size
    img = Image.new('RGBA', (img_w, img_h), (255, 255, 255, 255))  # 白色不透明背景
    draw = ImageDraw.Draw(img)
    
    # 1. 计算核心区域坐标
    # 边框外沿（渐变区域）
    outer_left, outer_top = margin, margin
    outer_right, outer_bottom = img_w - margin, img_h - margin
    # 边框内沿（白色中心区域）
    inner_left = outer_left + border_width
    inner_top = outer_top + border_width
    inner_right = outer_right - border_width
    inner_bottom = outer_bottom - border_width
    
    # 2. 绘制柔和阴影（核心优化）
    # 阴影区域：比边框略大，只覆盖边框外围
    shadow_expand = 5  # 阴影向外扩展的像素（减小值避免外围过宽）
    shadow_left = outer_left - shadow_expand + shadow_offset[0]
    shadow_top = outer_top - shadow_expand + shadow_offset[1]
    shadow_right = outer_right + shadow_expand + shadow_offset[0]
    shadow_bottom = outer_bottom + shadow_expand + shadow_offset[1]
    
    # 创建阴影层（仅包含阴影部分）
    shadow_layer = Image.new('RGBA', (img_w, img_h), (0, 0, 0, 0))
    shadow_draw = ImageDraw.Draw(shadow_layer)
    
    # 绘制阴影外环（边框的阴影）
    shadow_draw.rectangle(
        [shadow_left, shadow_top, shadow_right, shadow_bottom],
        fill=(0, 0, 0, shadow_opacity)  # 使用灰度阴影，避免彩色偏差
    )
    
    # 挖空阴影内环（与白色中心区域对齐，避免中心区域有阴影）
    shadow_inner_left = inner_left + shadow_offset[0]
    shadow_inner_top = inner_top + shadow_offset[1]
    shadow_inner_right = inner_right + shadow_offset[0]
    shadow_inner_bottom = inner_bottom + shadow_offset[1]
    shadow_draw.rectangle(
        [shadow_inner_left, shadow_inner_top, shadow_inner_right, shadow_inner_bottom],
        fill=(0, 0, 0, 0)  # 完全透明，移除中心区域阴影
    )
    
    # 应用柔和模糊（使用较小的模糊半径）
    shadow_layer = shadow_layer.filter(ImageFilter.GaussianBlur(shadow_blur))
    
    # 将阴影层合并到主图像（阴影在最底层）
    img.alpha_composite(shadow_layer)
    
    # 3. 绘制渐变边框（在阴影上方）
    draw = ImageDraw.Draw(img)  # 更新绘制对象
    
    # 填充渐变边框
    for x in range(outer_left, outer_right):
        for y in range(outer_top, outer_bottom):
            # 只绘制边框区域（外沿到内沿之间）
            if not (x >= inner_left and x < inner_right and y >= inner_top and y < inner_bottom):
                norm_x = (x - outer_left) / (outer_right - outer_left)
                norm_y = (y - outer_top) / (outer_bottom - outer_top)
                ratio = (norm_x + norm_y) / 2
                
                r = int(color_start[0]*(1-ratio) + color_end[0]*ratio)
                g = int(color_start[1]*(1-ratio) + color_end[1]*ratio)
                b = int(color_start[2]*(1-ratio) + color_end[2]*ratio)
                draw.point((x, y), (r, g, b))
    
    # 确保中心区域为纯白色（覆盖可能的阴影残留）
    draw.rectangle([inner_left, inner_top, inner_right, inner_bottom], fill=(255, 255, 255))
    
    # 4. 绘制文本内容
    text_area_width = inner_right - (inner_left + text_left_margin)
    text_x = inner_left + text_left_margin
    current_y = inner_top + text_top_margin
    
    # 主文本处理
    try:
        main_font = ImageFont.truetype("fonts/SourceHanSansSC-Bold-2.otf", font_size)
    except:
        main_font = ImageFont.load_default()
    
    main_text_clean = main_text.replace('\n', ' ')
    avg_char_width = font_size
    max_chars_per_line = int(text_area_width / avg_char_width)
    main_wrapped = textwrap.fill(main_text_clean, width=max_chars_per_line)
    main_lines = main_wrapped.split('\n')
    
    main_line_spacing = font_size * 1.2
    for line in main_lines:
        draw.text((text_x, current_y), line, font=main_font, fill=main_text_color)
        current_y += main_line_spacing
    
    # 特殊文本处理
    current_y += main_line_spacing
    try:
        special_font = ImageFont.truetype("fonts/SourceHanSansSC-Bold-2.otf", special_font_size)
    except:
        special_font = ImageFont.load_default()
    
    draw.text((text_x, current_y), special_text, font=special_font, fill=special_text_color)

    # 右下角绘制表情包（根据图片尺寸动态调整）
    face_size = min(img_w, img_h) // 3  # 表情包大小为图片短边的1/3
    face = Image.open('./imgs/think.png').convert("RGBA").resize((face_size, face_size))
    face_x = inner_right - face_size - 20  # 距离右边20像素
    face_y = inner_bottom - face_size - 20  # 距离下边20像素
    img.paste(face, (face_x, face_y), face)    
    # 保存图像
    img = img.convert('RGB')  # 转换为RGB格式
    if timestamp:
        output_path = f'output/image_{platform}_{timestamp}.png'
    else:
        output_path = f'output/image_{platform}.png'
    img.save(output_path)
    print(f"封面图片已保存到: {output_path}")
    return img, output_path
if __name__ == "__main__":
    with open('detailed_news_example_zh.json', 'r', encoding='utf-8') as file:
        data = json.load(file)
        text = data['description']
    create_soft_shadow_border(
        border_width=80,
        margin=80,
        font_size=168,
        main_text=text,
        text_top_margin=100,
        text_left_margin=100,
        special_font_size=168,
        platform='wx'
    )
