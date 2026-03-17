# -*- coding: utf-8 -*-
import requests
import json
import os

from bs4 import BeautifulSoup
import datetime

APPID = os.environ.get("WX_APP_ID", "")
APPSECRET = os.environ.get("WX_APP_SECRET", "")


def get_access_token(appid, appsecret):
    url = "https://api.weixin.qq.com/cgi-bin/token"
    params = {
        "grant_type": "client_credential",
        "appid": appid,
        "secret": appsecret
    }
    response = requests.get(url, params=params).json()
    return response.get("access_token")


def upload_image(access_token, image_path):
    url = f'https://api.weixin.qq.com/cgi-bin/material/add_material?access_token={access_token}&type=image'
    
    with open(image_path, 'rb') as img_file:
        files = {'media': img_file}
        response = requests.post(url, files=files)
    
    if response.status_code == 200:
        result = response.json()
        if 'media_id' in result:
            return result['media_id']
    else:
        print("上传图片失败:", response.text)
        return None


def upload_image_url(access_token, image_path):
    url = f'https://api.weixin.qq.com/cgi-bin/media/uploadimg?access_token={access_token}'
    
    with open(image_path, 'rb') as img_file:
        files = {'media': img_file}
        response = requests.post(url, files=files)
    
    if response.status_code == 200:
        result = response.json()
        if 'url' in result:
            return result['url']
    else:
        print("上传图片失败:", response.text)
        return None


def create_article(title, content, thumb_media_id):
    # 微信公众号标题限制64个字符
    if len(title) > 64:
        title = title[:61] + "..."
    
    return {
        "title": title,
        "thumb_media_id": thumb_media_id,
        "author": "正言",
        "content": content,
        "digest": "文章摘要",
        "show_cover_pic": 0
    }


def add_draft(access_token, article):
    """创建草稿"""
    url = f'https://api.weixin.qq.com/cgi-bin/draft/add?access_token={access_token}'
    
    data = {
        "articles": [article]
    }
    
    # 使用 ensure_ascii=False 避免中文被转义成 Unicode
    headers = {'Content-Type': 'application/json; charset=utf-8'}
    response = requests.post(url, data=json.dumps(data, ensure_ascii=False).encode('utf-8'), headers=headers)
    result = response.json()
    
    if result.get('errcode', 0) == 0:
        return result.get('media_id')
    else:
        print(f"创建草稿失败: {result}")
        return None


def replace_image_urls(html, access_token, timestamp=None):
    soup = BeautifulSoup(html, 'html.parser')
    img_tags = soup.find_all('img')
    for i, img in enumerate(img_tags):
        if timestamp:
            image_path = f'output/image_wx_{timestamp}.png' if i == 0 else f'output/image2_{timestamp}.png'
        else:
            image_path = f'output/image_wx.png' if i == 0 else f'output/image2.png'
        
        if os.path.exists(image_path):
            actual_url = upload_image_url(access_token, image_path)
            if actual_url:
                img['src'] = actual_url
                print(f"图片 {i + 1} 上传成功: {actual_url}")
    return str(soup)


def wx_main(title='', timestamp=None):
    access_token = get_access_token(APPID, APPSECRET)
    if not access_token:
        print("获取 Access Token 失败！")
        return {"status": "error", "message": "获取 Access Token 失败"}
    
    if timestamp:
        thumb_image_path = f"output/image_wx_{timestamp}.png"
    else:
        thumb_image_path = "output/image_wx.png"
    
    if not os.path.exists(thumb_image_path):
        print(f"封面图片不存在: {thumb_image_path}")
        return {"status": "error", "message": f"封面图片不存在: {thumb_image_path}"}
    
    thumb_media_id = upload_image(access_token, thumb_image_path)
    if not thumb_media_id:
        print("上传封面图片失败！")
        return {"status": "error", "message": "上传封面图片失败"}
    
    print("封面图片已上传，media_id:", thumb_media_id)
    
    template_path = "data/template.html"
    if not os.path.exists(template_path):
        print(f"模板文件不存在: {template_path}")
        return {"status": "error", "message": f"模板文件不存在: {template_path}"}
    
    with open(template_path, 'r', encoding='utf-8') as f:
        soup = BeautifulSoup(f, 'html.parser')
    
    date_div = soup.find('div', class_='date')
    if date_div:
        now = datetime.datetime.now()
        weekday = now.weekday()
        weekdays_in_chinese = ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"]
        date_str = f"{now.month}月{now.day}日  {weekdays_in_chinese[weekday]}"
        date_div.string = date_str
    
    # 构造标题（微信限制64字符）
    wx_title = f"\"{title}\"是真的吗？"
    if len(wx_title) > 64:
        wx_title = f"\"{title[:50]}...\"是真的吗？"
    
    article = create_article(
        title=wx_title,
        content=replace_image_urls(str(soup), access_token, timestamp),
        thumb_media_id=thumb_media_id
    )
    
    print("文章构造完成！")
    print("标题:", article['title'])
    print("封面图片已上传，media_id:", thumb_media_id)
    
    # 创建草稿
    print("\n正在创建草稿...")
    draft_media_id = add_draft(access_token, article)
    
    if draft_media_id:
        print(f"草稿创建成功！media_id: {draft_media_id}")
        print("请登录微信公众号后台，在草稿箱中找到文章并发布。")
        return {
            "status": "success",
            "message": "文章已上传到微信公众号草稿箱",
            "title": article['title'],
            "thumb_media_id": thumb_media_id,
            "draft_media_id": draft_media_id
        }
    else:
        print("草稿创建失败！")
        return {
            "status": "error",
            "message": "草稿创建失败"
        }


if __name__ == "__main__":
    result = wx_main("测试标题")
    print(result)
