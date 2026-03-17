#!/usr/bin/env python3
"""
同花顺账号密码登录 - 纯API方式
"""
import asyncio
import platform
import sys
import os
import time
import json
import requests
import re
import random
import hashlib
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_v1_5
import base64
from pydoll.browser import Edge
from pydoll.browser.options import ChromiumOptions

DIR_PATH = os.path.dirname(os.path.abspath(__file__))

if platform.system() == "Linux":
    PROFILE_ROOT = "EdgeProfile"
else:
    PROFILE_ROOT = "ChromeProfile"

RSA_MODULUS = "D90F4DD5BF444916913F7B434F192587C354387FA531F2964725B5188FB9D5B40FDDD2B34F61B5560468D1F5C568796EB15F7799F03E4A3301EAF8B79B655F1B2B7DC6FFE1084E4C14A05DD9C6D0C72C5ED75890DC5D11AB5990A3C7DEBA0D68EFFD8C619B2A21AEFA3E7FF902CDAE0502025901EE2D42B76A0D7AD389F0BF69"
RSA_EXPONENT = "10001"

with open(os.environ.get("THS_CREDENTIALS_FILE", "username"), "r") as f:
    lines = f.read().strip().split("\n")
    USERNAME = lines[0].split(":")[1]
    PASSWORD = lines[1].split(":")[1]

def rsa_encrypt(text: str) -> str:
    n = int(RSA_MODULUS, 16)
    e = int(RSA_EXPONENT, 16)
    key = RSA.construct((n, e))
    cipher = PKCS1_v1_5.new(key)
    encrypted = cipher.encrypt(text.encode('utf-8'))
    return base64.b64encode(encrypted).decode('utf-8')

def generate_crnd():
    chars = "abcdefghijklmnopqrstuvwxyz0123456789"
    return ''.join(random.choice(chars) for _ in range(16))

def get_dsk(username, password, salt):
    s = f"{username}{password}{salt}"
    return hashlib.sha256(s.encode()).hexdigest()

class ThsnxPasswordLogin:
    def __init__(self, hexin_v, cookies):
        self.hexin_v = hexin_v
        self.session = requests.Session()
        
        for name, value in cookies.items():
            self.session.cookies.set(name, value)
        
        self.session.headers.update({
            "Accept": "*/*",
            "Accept-Language": "zh-CN,zh;q=0.9",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36",
        })
        
        self.captcha_info = {}
        self.ticket = None
        self.signature = None
        self.crnd = generate_crnd()
        self.salt = None
        self.dsk = None
    
    def get_gs(self):
        """获取加密参数"""
        print("\n[1] 获取加密参数 (getGS)...")
        
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "hexin-v": self.hexin_v,
        }
        
        data = {
            "uname": rsa_encrypt(USERNAME),
            "rsa_version": "default_5",
            "crnd": self.crnd,
        }
        
        resp = self.session.post(
            "https://upass.ths123.com/user/getGS",
            data=data,
            headers=headers
        )
        
        result = resp.json()
        print(f"  响应: {json.dumps(result, ensure_ascii=False)}")
        
        if result.get("errorcode") == 0:
            self.salt = result.get("salt", "")
            self.dsk = result.get("dsk", "")
            print(f"  ✓ salt: {self.salt}")
            print(f"  ✓ dsk: {self.dsk}")
            return True
        return False
    
    def do_login(self):
        """登录请求"""
        print("\n[2] 登录请求 (dologinreturnjson2)...")
        
        headers = {
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "hexin-v": self.hexin_v,
            "X-Requested-With": "XMLHttpRequest",
        }
        
        data = {
            "uname": rsa_encrypt(USERNAME),
            "passwd": rsa_encrypt(PASSWORD),
            "saltLoginTimes": "1",
            "longLogin": "on",
            "rsa_version": "default_5",
            "source": "pc_web",
            "request_type": "login",
            "captcha_type": "4",
            "upwd_score": "45",
            "ignore_upwd_score": "",
            "passwdSalt": rsa_encrypt(self.salt) if self.salt else "",
            "dsk": self.dsk or "",
            "crnd": self.crnd,
            "ttype": "WEB",
            "sdtis": "C22",
            "timestamp": str(int(time.time())),
        }
        
        resp = self.session.post(
            "https://upass.ths123.com/login/dologinreturnjson2",
            data=data,
            headers=headers
        )
        
        result = resp.json()
        print(f"  响应: {json.dumps(result, ensure_ascii=False)}")
        
        return result
    
    def solve_slider(self, max_attempts=5):
        """滑块验证 - 多次尝试"""
        print("\n[滑块验证]")
        
        # 固定的距离列表（验证码只有五六个固定的距离值）
        fixed_distances = [160, 150, 170, 140, 180, 165, 155, 175, 145, 185, 130, 190, 135, 195, 125, 200]
        
        for attempt in range(1, max_attempts + 1):
            print(f"\n=== 第 {attempt} 次尝试 ===")
            
            print("  [1] 获取预处理句柄...")
            resp = self.session.get(
                "https://captcha.10jqka.com.cn/getPreHandle",
                params={
                    "captcha_type": 4,
                    "appid": "registernew",
                    "random": str(random.random() * 1e12),
                    "callback": "PreHandle",
                    "hexin-v": self.hexin_v
                }
            )
            
            match = re.search(r'PreHandle\((.*)\)', resp.text)
            if not match:
                print("  ✗ 获取失败")
                continue
            
            self.captcha_info = json.loads(match.group(1)).get('data', {})
            print(f"  ✓ initx: {self.captcha_info.get('initx')}")
            print(f"  ✓ inity: {self.captcha_info.get('inity')}")
            
            print("  [2] 获取验证码图片...")
            url_params = self.captcha_info.get('urlParams', '')
            imgs = self.captcha_info.get('imgs', [])
            
            if len(imgs) < 2:
                print("  ✗ 图片列表为空")
                continue
            
            bg_url = f"https://captcha.10jqka.com.cn/getImg?{url_params}&iuk={imgs[0]}"
            slider_url = f"https://captcha.10jqka.com.cn/getImg?{url_params}&iuk={imgs[1]}"
            
            bg_resp = self.session.get(bg_url)
            slider_resp = self.session.get(slider_url)
            
            print(f"  ✓ 背景图: {len(bg_resp.content)} bytes")
            print(f"  ✓ 滑块图: {len(slider_resp.content)} bytes")
            
            print("  [3] 使用固定距离列表尝试验证...")
            initx = int(self.captcha_info.get('initx', 60))
            inity = int(self.captcha_info.get('inity', 60))
            
            init_y = inity / 340 * 309
            
            for dist in fixed_distances:
                phrase = f"{dist};{init_y};309;177.22058823529412"
                self.captcha_info['phrase'] = phrase
                
                print(f"  [4] 提交验证... (距离: {dist}px)")
                ticket_url = f"https://captcha.10jqka.com.cn/getTicket?{url_params}&phrase={phrase}&callback=verify&hexin-v={self.hexin_v}"
                ticket_resp = self.session.get(ticket_url)
                
                match = re.search(r'verify\((.*)\)', ticket_resp.text)
                if not match:
                    continue
                
                result = json.loads(match.group(1))
                
                if result.get('code') == 0:
                    self.ticket = result.get('ticket')
                    self.signature = self.captcha_info.get('sign', '')
                    print(f"  ✓ 验证成功!")
                    print(f"  ✓ ticket: {self.ticket}")
                    return True
                else:
                    print(f"  ✗ 验证失败: code={result.get('code')}")
            
            print("✗ 滑块验证失败")
        
        return False
    
    def do_login_with_ticket(self):
        """带ticket的登录请求"""
        print("\n[3] 带ticket登录...")
        
        headers = {
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "hexin-v": self.hexin_v,
            "X-Requested-With": "XMLHttpRequest",
        }
        
        data = {
            "uname": rsa_encrypt(USERNAME),
            "passwd": rsa_encrypt(PASSWORD),
            "saltLoginTimes": "1",
            "longLogin": "on",
            "rsa_version": "default_5",
            "source": "pc_web",
            "request_type": "login",
            "captcha_type": "4",
            "captcha_ticket": self.ticket,
            "captcha_phrase": self.captcha_info.get('phrase', ''),
            "captcha_signature": self.signature,
            "upwd_score": "45",
            "ignore_upwd_score": "",
            "passwdSalt": rsa_encrypt(self.salt) if self.salt else "",
            "dsk": self.dsk or "",
            "crnd": self.crnd,
            "ttype": "WEB",
            "sdtis": "C22",
            "timestamp": str(int(time.time())),
        }
        
        resp = self.session.post(
            "https://upass.ths123.com/login/dologinreturnjson2",
            data=data,
            headers=headers
        )
        
        result = resp.json()
        print(f"  响应: {json.dumps(result, ensure_ascii=False)}")
        
        return result
    
    def login(self):
        """完整登录流程"""
        if not self.get_gs():
            print("✗ 获取加密参数失败")
            return False
        
        result = self.do_login()
        
        if result.get("errorcode") == 0:
            print("\n✓ 登录成功！无需滑块验证")
            return True
        
        if result.get("errorcode") == -11400:
            print("\n需要滑块验证...")
            
            if not self.solve_slider():
                print("✗ 滑块验证失败")
                return False
            
            result = self.do_login_with_ticket()
            
            if result.get("errorcode") == 0:
                print("\n✓ 登录成功！")
                return True
        
        print(f"\n✗ 登录失败: {result.get('errormsg', '未知错误')}")
        return False


async def get_hexin_v_from_browser():
    """从浏览器获取hexin-v"""
    profile_path = os.path.join(DIR_PATH, PROFILE_ROOT)
    
    options = ChromiumOptions()
    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument(f"--user-data-dir={profile_path}")
    options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0')
    options.add_argument('--disable-blink-features=AutomationControlled')
    
    if platform.system() == "Linux":
        options.add_argument('--headless=new')
        options.add_argument('--disable-gpu-sandbox')
        options.start_timeout = 120
    
    login_url = "https://upass.ths123.com/login?redir=//mall.ths123.com/center/index/index/channel/myservice/"
    
    print(f"启动浏览器...")
    print(f"Profile路径: {profile_path}")
    
    async with Edge(options=options) as browser:
        page = await browser.start()
        
        await page.execute_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
        """)
        
        print(f"访问登录页面...")
        try:
            await page.go_to(login_url, timeout=120)
        except Exception as e:
            print(f"页面加载警告: {e}")
        
        await asyncio.sleep(5)
        
        hexin_v = None
        cookies = {}
        
        try:
            browser_cookies = await page.get_cookies()
            for cookie in browser_cookies:
                cookies[cookie.get('name', '')] = cookie.get('value', '')
                if cookie.get('name') == 'v':
                    hexin_v = cookie.get('value')
        except Exception as e:
            print(f"获取cookies失败: {e}")
        
        if hexin_v:
            print(f"✓ hexin-v: {hexin_v}")
        else:
            print("✗ 未获取到hexin-v")
            return None, None
        
        return hexin_v, cookies


async def load_cookies_to_profile(cookies_dict):
    """将cookies加载到ChromeProfile"""
    profile_path = os.path.join(DIR_PATH, PROFILE_ROOT)
    
    options = ChromiumOptions()
    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')
    options.add_argument(f"--user-data-dir={profile_path}")
    options.add_argument('--headless=new')
    
    if platform.system() == "Linux":
        options.add_argument('--disable-gpu-sandbox')
        options.start_timeout = 120
    
    async with Edge(options=options) as browser:
        page = await browser.start()
        
        await page.go_to("https://www.10jqka.com.cn/", timeout=30)
        await asyncio.sleep(1)
        
        domains = [
            {"domain": ".10jqka.com.cn", "path": "/"},
            {"domain": ".ths123.com", "path": "/"},
        ]
        
        for name, value in cookies_dict.items():
            if not value:
                continue
            for domain_info in domains:
                try:
                    await page.set_cookies([{
                        "name": name,
                        "value": value,
                        "domain": domain_info["domain"],
                        "path": domain_info["path"],
                    }])
                except:
                    pass
        
        await asyncio.sleep(1)
        print(f"  ✓ Cookies已加载到Profile: {profile_path}")


async def main():
    print("=" * 60)
    print("同花顺账号密码登录")
    print("=" * 60)
    print(f"用户名: {USERNAME}")
    print(f"密码: {'*' * len(PASSWORD)}")
    
    hexin_v, cookies = await get_hexin_v_from_browser()
    
    if not hexin_v:
        print("\n✗ 获取 hexin-v 失败")
        return
    
    login = ThsnxPasswordLogin(hexin_v, cookies)
    
    if login.login():
        print("\n" + "=" * 60)
        print("✓ 登录成功！")
        print("=" * 60)
        
        print("\n保存Cookies...")
        cookies_file = os.path.join(DIR_PATH, "login_cookies.json")
        cookies_dict = {}
        for cookie in login.session.cookies:
            cookies_dict[cookie.name] = cookie.value
        with open(cookies_file, "w") as f:
            json.dump(cookies_dict, f, indent=2)
        print(f"  ✓ Cookies已保存到: {cookies_file}")
        
        print("\n加载Cookies到ChromeProfile...")
        await load_cookies_to_profile(cookies_dict)


if __name__ == "__main__":
    asyncio.run(main())
