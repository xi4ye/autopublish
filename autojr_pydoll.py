# -*- coding: utf-8 -*-
import asyncio
import os
import platform
import shutil

if 'SSLKEYLOGFILE' in os.environ:
    del os.environ['SSLKEYLOGFILE']

from pydoll.browser.chromium.chrome import Chrome
from pydoll.browser.options import ChromiumOptions
import os
import json


def _clean_chrome_locks(profile_path):
    """清理 Chrome 配置目录中的锁文件"""
    lock_files = ['SingletonLock', 'SingletonSocket', 'SingletonCookie']
    for lock_file in lock_files:
        lock_path = os.path.join(profile_path, lock_file)
        if os.path.exists(lock_path):
            try:
                os.remove(lock_path)
                print(f"已清理锁文件: {lock_path}")
            except Exception as e:
                print(f"清理锁文件失败: {e}")


async def auto_publish_jr(title='', timestamp=None):
    script_dir = os.path.dirname(os.path.abspath(__file__))
    PROFILE_ROOT = os.path.join(script_dir, "ChromeProfile")
    
    _clean_chrome_locks(PROFILE_ROOT)
    
    options = ChromiumOptions()
    options.binary_location = '/usr/bin/google-chrome'
    options.start_timeout = 60
    options.headless = True
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_argument('--disable-gpu')
    options.add_argument('--disable-software-rasterizer')
    options.add_argument(
        '--user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/')
    options.add_argument(f"--user-data-dir={PROFILE_ROOT}")
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--window-size=2560,1600')
    options.add_argument('--disable-extensions')
    options.add_argument('--disable-background-networking')
    options.add_argument('--disable-sync')
    options.add_argument('--disable-infobars')
    options.add_argument('--disable-breakpad')
    options.add_argument('--disable-component-update')
    
    async with Chrome(options=options) as browser:
        await browser.start()
        page = await browser.new_tab()

        await page.go_to("https://mp.toutiao.com/profile_v4/graphic/publish")
        await asyncio.sleep(10)

        try:
            mask = await page.find(class_name='byte-drawer-mask')
            await mask.click()
        except Exception:
            pass
        await asyncio.sleep(1)

        try:
            login_btn = await page.find(
                class_name='web-login-other-login-method__list__item__icon__account_pwd')
            await login_btn.click()
            await asyncio.sleep(2)
            bt1 = await page.find(class_name='web-login-normal-input__input')
            await bt1.click()
            await bt1.type_text("18067237418")
            await asyncio.sleep(2)
            pwd_input = await page.find(class_name='web-login-button-input__input')
            await pwd_input.type_text("XSY4myson")

            await asyncio.sleep(2)
            checkbox = await page.find(class_name='web-login-confirm-info__checkbox')
            await checkbox.click()

            await asyncio.sleep(1)
            login_btn2 = await page.find(class_name='web-login-button')
            await login_btn2.click()
            await asyncio.sleep(3)
            print("已保存登录结果截图: login_result.png")
            
        except Exception as e:
            print(f"登录失败: {e}")
        try:
            banner = await page.query("h1[class='header'] > svg")
            await banner.click()
        except Exception:
            pass
        
        await asyncio.sleep(2)

        header = await page.query("//textarea")

        await header.click()
        await header.type_text(title)
        await asyncio.sleep(1)
        await page.execute_script('window.scrollBy(0, 500);')
        await asyncio.sleep(2)
        try:
            close_btn = await page.find(class_name='close-bin')
            await close_btn.click()
        except Exception:
            pass
        
        await asyncio.sleep(1)
        await page.execute_script('window.scrollBy(0, -1500);')
        await asyncio.sleep(1)
        upload = await page.find(class_name='doc-import')
        await upload.click()
        if timestamp:
            template_path = os.path.abspath(f'output/jrbd_{timestamp}.docx')
        else:
            template_path = os.path.abspath('jrbd.docx')
        
        if not os.path.exists(template_path):
            print(f"文档不存在: {template_path}")
            return {"status": "error", "message": f"文档不存在: {template_path}"}
        
        await asyncio.sleep(1)
        try:
            file_input = await page.query('input[type="file"]')
        except Exception:
            await upload.click()
            await asyncio.sleep(1)
            file_input = await page.query('input[type="file"]')
        await file_input.set_input_files([template_path])
        await asyncio.sleep(5)

        await page.execute_script("window.scrollBy(0,2500);")
        # tns = await page.find(class_name='editor-image-menu-item')
        # await tns.scroll_into_view()
        # await tns.click()
        # await page.take_screenshot('login_result.png')
        # await asyncio.sleep(1)
        # tns = await page.query(
        #     "//div[@class='btns']/button[contains(@class, 'byte-btn-primary')]")
        # await tns.scroll_into_view()
        # await tns.click()
        # await page.take_screenshot('login_result.png')
        # await asyncio.sleep(1)

        # if timestamp:
        #     image_path = os.path.abspath(f'output/image_jr_{timestamp}.png')
        # else:
        #     image_path = os.path.abspath('output/image_jr.png')
        
        # if not os.path.exists(image_path):
        #     print(f"封面图片不存在: {image_path}")
        #     return {"status": "error", "message": f"封面图片不存在: {image_path}"}
        
        # await asyncio.sleep(1)
        # try:
        #     cover_input = await page.query('input[type="file"][accept*="image"]')
        #     if cover_input:
        #         await cover_input.set_input_files([image_path])
        #         print(f"封面图片已上传: {image_path}")
        # except Exception as e:
        #     print(f"上传封面图片失败: {e}")
        # await asyncio.sleep(2)
        # await page.take_screenshot('login_result.png')
        await page.execute_script("window.scrollBy(0, 2000);")
        await asyncio.sleep(1)
        buttons = await page.find(class_name='byte-checkbox-mask', find_all=True)
        await buttons[-4].click()
        await asyncio.sleep(1)
        await page.take_screenshot('login_result.png')
        submit = await page.query(
            "//div[contains(@class, 'publish-footer-content')]/button[contains(@class, 'byte-btn-primary')]")
        await submit.click()
        await page.take_screenshot('login_result.png')
        await asyncio.sleep(2)
        sure = await page.query(
            "//div[contains(@class, 'publish-footer')]/button[contains(@class, 'publish-btn-last')]")
        await sure.click()
        await page.take_screenshot('login_result.png')
        print("今日头条文章发布成功！")
        return {"status": "success", "message": "今日头条文章发布成功"}


if __name__ == "__main__":
    asyncio.run(auto_publish_jr("测试文章"))
