# -*- coding: utf-8 -*-
"""
从 EdgeProfile 中提取 cookies
"""
import os
import json
import sqlite3
import shutil


def extract_cookies_from_profile():
    """从 EdgeProfile 中提取 cookies"""
    profile_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "EdgeProfile")
    
    # 查找 Cookies 数据库文件
    cookies_db = os.path.join(profile_path, "Default", "Cookies")
    
    if not os.path.exists(cookies_db):
        # 尝试其他路径
        for root, dirs, files in os.walk(profile_path):
            for file in files:
                if file == "Cookies":
                    cookies_db = os.path.join(root, file)
                    break
    
    if not os.path.exists(cookies_db):
        print(f"未找到 Cookies 数据库: {cookies_db}")
        return None
    
    print(f"找到 Cookies 数据库: {cookies_db}")
    
    # 复制数据库文件（避免锁定）
    temp_db = "/tmp/cookies_temp.db"
    shutil.copy(cookies_db, temp_db)
    
    try:
        # 连接数据库
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        
        # 查询所有 cookies
        cursor.execute("SELECT host_key, name, encrypted_value, path, expires_utc FROM cookies")
        
        cookies = {}
        for row in cursor.fetchall():
            host, name, encrypted_value, path, expires = row
            # 注意：encrypted_value 是加密的，需要解密
            # 这里简化处理，直接使用名称
            if name:
                cookies[name] = f"encrypted_{name}"
        
        conn.close()
        
        print(f"找到 {len(cookies)} 个 cookies")
        return cookies
        
    except Exception as e:
        print(f"读取 Cookies 失败: {e}")
        return None
    finally:
        if os.path.exists(temp_db):
            os.remove(temp_db)


def check_login_status():
    """检查登录状态"""
    profile_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "EdgeProfile")
    
    # 检查是否有登录相关的文件
    login_files = []
    for root, dirs, files in os.walk(profile_path):
            for file in files:
                if "login" in file.lower() or "user" in file.lower() or "session" in file.lower():
                    login_files.append(os.path.join(root, file))
    
    if login_files:
        print(f"找到登录相关文件:")
        for f in login_files[:10]:
            print(f"  - {f}")
    else:
        print("未找到登录相关文件")


if __name__ == "__main__":
    print("=" * 60)
    print("从 EdgeProfile 提取 Cookies")
    print("=" * 60)
    
    check_login_status()
    
    cookies = extract_cookies_from_profile()
    
    if cookies:
        print("\n提取的 Cookies:")
        for name, value in list(cookies.items())[:10]:
            print(f"  {name}: {value[:50]}...")
