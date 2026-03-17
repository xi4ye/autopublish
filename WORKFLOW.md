# 新闻自动发布系统 WORKFLOW

## 1. 项目概述

本项目是一个新闻事实核查自动化发布系统，主要功能包括：
- 通过 API 服务接收外部请求
- 使用 DeepSeek API 翻译英文内容为中文
- 格式化数据为结构化 JSON
- 生成新闻鉴别海报图片
- 生成封面图片（支持 TRUE/FALSE 不同颜色）
- 解析 URL 重定向（需要登录 cookies）
- 自动发布到多个平台（微信公众号、今日头条）

## 2. 整体工作流程

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           新闻自动发布系统工作流程                              │
└─────────────────────────────────────────────────────────────────────────────┘

┌──────────────┐    ┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│   API 请求    │───▶│   任务队列    │───▶│   翻译内容    │───▶│   格式化数据  │
│  (POST 8888) │    │ (TaskQueue)  │    │  (DeepSeek)  │    │ (data_adapter)│
└──────────────┘    └──────────────┘    └──────────────┘    └──────────────┘
                                                                   │
                                                                   ▼
┌──────────────┐    ┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│   平台发布    │◀───│   创建文档    │◀───│   生成封面    │◀───│   生成海报    │
│  (wx/jr)    │    │   (docx)     │    │  (fenmian)   │    │  (image2)    │
└──────────────┘    └──────────────┘    └──────────────┘    └──────────────┘
        │
        ▼
┌──────────────┐
│   URL 重定向  │
│   解析       │
└──────────────┘
```

## 3. 详细步骤说明

### 步骤 1：API 请求接收

**服务端口**：`http://127.0.0.1:8888`

**接口**：
- `POST /api/news` - 提交新闻处理任务
- `GET /api/task/{task_id}` - 查询任务状态

**请求格式**：
```json
{
  "id": 6414,
  "description": "新闻标题",
  "auto_publish": true,
  "history": {
    "k=5": [{"Date": "2026-02-22", "Result": "TRUE"}],
    "k=10": [],
    "k=15": [],
    "k=20": []
  },
  "last_output": {
    "k=5": "#### **1. COLLECTION**\n**Record ALL Analyst Reports...**",
    "k=10": "",
    "k=15": "",
    "k=20": ""
  },
  "revelent_news": {
    "id": 6414,
    "claim": "新闻声明",
    "collection": [
      {"id": 1, "title": "相关新闻标题", "url": "https://www.iwencai.com/goto?..."}
    ]
  }
}
```

**响应格式**：
```json
{
  "status": "accepted",
  "task_id": "task_20260307_184756_340016",
  "message": "任务已加入队列",
  "queue_size": 1,
  "auto_publish": true
}
```

**关键代码**：
```python
# api_server.py
async def handle_post(request):
    data = await request.json()
    task_id = f"task_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
    task = await task_queue.add_task(task_id, data, auto_publish=auto_publish)
    return web.json_response({"status": "accepted", "task_id": task_id})
```

### 步骤 2：翻译内容

**工具**：`translate_agent.py` - DeepSeekTranslator 类

**操作**：
- 使用 DeepSeek API 翻译 `last_output` 中的英文内容
- 保持 Markdown 格式不变
- 固定翻译关键标题（如 "COLLECTION" → "信息收集"）

**关键代码**：
```python
from translate_agent import DeepSeekTranslator

translator = DeepSeekTranslator(API_KEY, BASE_URL, MODEL)
translated_content = translator.translate_markdown(english_content)
```

**API 配置**：
- API_KEY: DeepSeek API 密钥
- BASE_URL: https://api.deepseek.com
- MODEL: deepseek-reasoner

### 步骤 3：格式化数据

**工具**：`data_adapter.py` - format_for_template 函数

**操作**：
- 解析翻译后的 Markdown 内容
- 提取 `ANALYSIS`、`CONCLUSION`、`COLLECTION` 等字段
- 转换为结构化 JSON 格式
- **解析 URL 重定向**（使用 login_cookies.json）

**关键代码**：
```python
from data_adapter import format_for_template

formatted_data = format_for_template(translated_record, resolve_urls=True)
```

**URL 重定向解析**：
```python
# data_adapter.py 中的 URLRedirectResolver 类
class URLRedirectResolver:
    def get_final_url(self, url: str) -> Tuple[bool, str]:
        """使用 HEAD 请求获取重定向后的最终 URL"""
        response = self.session.head(url, allow_redirects=True, cookies=self.cookies)
        return True, response.url
```

**输出格式**：
```json
{
  "description": "新闻标题",
  "Date": "2026-03-07",
  "id": 6414,
  "CONCLUSION": {
    "FinalJudgment": "TRUE",
    "DetailedReasons": [
      {"id": "Ⅰ", "title": "理由标题", "content": "理由内容"}
    ]
  },
  "ANALYSIS": {
    "summary": "分析摘要",
    "evidence": [
      {"id": 1, "title": "证据标题", "content": "证据内容"}
    ]
  },
  "COLLECTION": [
    {"id": 1, "score": 100, "content": "分析师报告内容"}
  ],
  "revelent_news": {
    "id": 6414,
    "claim": "新闻声明",
    "collection": [
      {"id": 1, "title": "相关新闻标题", "url": "url:https://mp.weixin.qq.com/..."}
    ]
  }
}
```

### 步骤 4：生成海报

**工具**：`create_detailed_news_template.py` - SmartImageGenerator 类

**操作**：
- 使用格式化后的数据生成详细鉴别报告海报
- 应用 TECH 风格模板
- 包含：新闻标题、判定类型、证据链、相关新闻
- **根据 TRUE/FALSE 显示不同颜色**（TRUE=绿色，FALSE=红色）

**关键代码**：
```python
from create_detailed_news_template import SmartImageGenerator, TemplateStyle

generator = SmartImageGenerator(external_data=formatted_data)
generator.generate_image(
    style=TemplateStyle.TECH,
    output_path="output/image2_{timestamp}.png"
)
```

**判定类型显示**：
```python
# create_detailed_news_template.py
if self.news.get('is_true', False):
    type_label = '【真实类型】'
    result_color = "green"
else:
    type_label = '【虚假类型】'
    result_color = "red"
```

**输出文件**：`output/image2_{timestamp}.png`

### 步骤 5：生成封面

**工具**：`fenmian.py` - create_soft_shadow_border 函数

**操作**：
- 生成带渐变边框和阴影效果的封面图片
- 支持两种平台尺寸：jr(656x511)、wx(3370x1436)
- 添加新闻标题和表情包装饰
- **表情包大小根据图片尺寸动态调整**

**关键代码**：
```python
from fenmian import create_soft_shadow_border

create_soft_shadow_border(
    border_width=80,
    margin=80,
    font_size=168,
    main_text=title,
    platform='wx',
    timestamp=timestamp
)
```

**输出文件**：
- `output/image_jr_{timestamp}.png` (今日头条封面)
- `output/image_wx_{timestamp}.png` (微信封面)

### 步骤 6：创建文档

**工具**：`create_template.py` - create_template 函数

**操作**：
- 创建 Word 文档
- 插入封面图片和海报图片
- 添加日期、介绍语、免责声明、结束语

**关键代码**：
```python
from create_template import create_template

create_template(platform='jr', title=title, timestamp=timestamp)
```

**输出文件**：`output/jrbd_{timestamp}.docx`

### 步骤 7：平台发布

#### 7.1 微信公众号发布

**工具**：`autowx.py` - wx_main 函数

**操作**：
- 获取微信 Access Token
- 上传封面图片获取 media_id
- 构造文章内容（使用 HTML 模板）
- **自动创建草稿**（调用草稿箱 API）
- 标题限制 64 字符

**关键代码**：
```python
from autowx import wx_main

result = await wx_main(title, timestamp)
# 返回: {"status": "success", "draft_media_id": "..."}
```

**文章内容**：使用 `data/template.html` 模板，包含：
- 封面图片：`output/image_wx_{timestamp}.png`
- 海报图片：`output/image2_{timestamp}.png`
- 介绍语、免责声明、结束语

#### 7.2 今日头条发布

**工具**：`autojr_pydoll.py` - auto_publish_jr 函数

**操作**：
- 使用 pydoll 自动化浏览器
- 登录今日头条创作者平台
- 上传文档 `output/jrbd_{timestamp}.docx`
- 自动发布文章

**关键代码**：
```python
from autojr_pydoll import auto_publish_jr

result = await auto_publish_jr(timestamp)
```

## 4. 核心模块说明

| 文件 | 功能 | 主要类/函数 |
|------|------|-------------|
| `api_server.py` | API 服务入口 | `handle_post()`, `TaskQueue`, `process_news_data()` |
| `translate_agent.py` | DeepSeek 翻译代理 | `DeepSeekTranslator`, `translate_markdown()` |
| `data_adapter.py` | 数据格式化适配器 | `format_for_template()`, `URLRedirectResolver` |
| `create_detailed_news_template.py` | 海报生成器 | `SmartImageGenerator`, `TemplateStyle` |
| `fenmian.py` | 封面图片生成 | `create_soft_shadow_border()` |
| `create_template.py` | Word 文档生成 | `create_template()` |
| `content_config.py` | 通用内容配置 | `INTRO`, `DISCLAIMER`, `ENDING`, `generate_title()` |
| `autowx.py` | 微信公众号发布 | `wx_main()`, `add_draft()`, `upload_image()` |
| `autojr_pydoll.py` | 今日头条发布 | `auto_publish_jr()` |
| `ths_password_login.py` | 同花顺登录获取 cookies | `THSPasswordLogin` |
| `slider_detector.py` | 滑块验证码检测 | `get_distance_with_retry()` |

## 5. 数据格式说明

### 5.1 请求日志格式

**文件**：`logs/request_{YYYYMMDD}.json`

```json
{
  "timestamp": "2026-03-07T18:47:56.340203",
  "task_id": "task_20260307_184756_340016",
  "data": { ... 原始请求数据 ... }
}
```

### 5.2 中间数据格式

**文件**：`data/formated_translated_{timestamp}.json`

```json
{
  "description": "新闻标题",
  "Date": "2026-03-07",
  "id": 6414,
  "CONCLUSION": {
    "FinalJudgment": "TRUE",
    "DetailedReasons": [...]
  },
  "ANALYSIS": {
    "summary": "...",
    "evidence": [...]
  },
  "COLLECTION": [...],
  "revelent_news": {...}
}
```

### 5.3 输出文件

| 文件 | 说明 |
|------|------|
| `output/image2_{timestamp}.png` | 详细鉴别海报 |
| `output/image_wx_{timestamp}.png` | 微信平台封面 |
| `output/image_jr_{timestamp}.png` | 今日头条封面 |
| `output/jrbd_{timestamp}.docx` | Word 文档 |
| `login_cookies.json` | 同花顺登录 cookies（7天有效） |

## 6. 配置说明

### 6.1 API 服务配置

```python
# api_server.py
HOST = "127.0.0.1"
PORT = 8888
MAX_WORKERS = 3  # 最大并发 Worker 数
```

### 6.2 DeepSeek API 配置

```python
# 从环境变量读取
API_KEY = os.environ.get("DEEPSEEK_API_KEY", "")
BASE_URL = os.environ.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
MODEL = os.environ.get("DEEPSEEK_MODEL", "deepseek-reasoner")
```

### 6.3 微信公众号配置

```python
# 从环境变量读取
APPID = os.environ.get("WX_APP_ID", "")
APPSECRET = os.environ.get("WX_APP_SECRET", "")
```

### 6.4 封面平台尺寸

| 平台 | 代码 | 尺寸 |
|------|------|------|
| 今日头条 | jr | 656 x 511 |
| 微信公众号 | wx | 3370 x 1436 |

### 6.5 Cookies 配置

```python
# login_cookies.json - 同花顺登录 cookies
# 有效期：7 天
# 用途：解析 iwencai.com 的 URL 重定向
```

## 7. 使用指南

### 7.1 环境准备

```bash
pip install pillow langchain-openai requests beautifulsoup4 python-docx aiohttp ddddocr
```

### 7.2 启动 API 服务

```bash
python api_server.py
```

### 7.3 发送请求

```bash
curl -X POST http://127.0.0.1:8888/api/news \
  -H "Content-Type: application/json" \
  -d '{
    "id": 1,
    "description": "新闻标题",
    "auto_publish": true,
    "history": {...},
    "last_output": {...},
    "revelent_news": {...}
  }'
```

### 7.4 查询任务状态

```bash
curl http://127.0.0.1:8888/api/task/task_20260307_184756_340016
```

### 7.5 获取登录 Cookies

```bash
# 编辑 username 文件，填入同花顺账号密码
python ths_password_login.py
```

### 7.6 目录结构

```
publish/
├── api_server.py               # API 服务入口
├── translate_agent.py          # 翻译模块
├── data_adapter.py             # 数据格式化模块（含 URL 重定向解析）
├── create_detailed_news_template.py  # 海报生成模块
├── fenmian.py                  # 封面生成模块
├── create_template.py          # 文档生成模块
├── content_config.py           # 通用内容配置
├── autowx.py                   # 微信发布模块
├── autojr_pydoll.py            # 今日头条发布模块
├── ths_password_login.py       # 同花顺登录模块
├── slider_detector.py          # 滑块验证码检测模块
├── login_cookies.json          # 登录 cookies（7天有效）
├── data/
│   ├── formated_translated_{timestamp}.json  # 格式化数据
│   └── template.html           # 微信文章模板
├── output/
│   ├── image2_{timestamp}.png  # 海报图片
│   ├── image_wx_{timestamp}.png # 微信封面
│   ├── image_jr_{timestamp}.png # 今日头条封面
│   └── jrbd_{timestamp}.docx   # Word 文档
├── logs/
│   └── request_{YYYYMMDD}.json # 请求日志
├── fonts/
│   ├── SourceHanSansSC-Bold-2.otf
│   ├── simhei.ttf
│   └── simfang.ttf
└── imgs/
    ├── think.png               # 思考表情包
    ├── tick.png                # 正确图标
    └── alert.png               # 警告图标
```

## 8. 注意事项

1. **API 密钥安全**：请勿将 API 密钥提交到版本控制系统
2. **字体文件**：确保 `fonts/` 目录下有所需的中文字体
3. **图片资源**：确保 `imgs/` 目录下有所需的装饰图片
4. **微信发布**：草稿自动创建，需手动在公众号后台确认发布
5. **Cookies 有效期**：`login_cookies.json` 有效期为 7 天，过期需重新登录
6. **任务队列**：支持异步处理，立即返回 task_id
7. **TRUE/FALSE 判定**：海报会根据判定结果显示不同颜色

## 9. 常见问题

### Q1: 翻译失败怎么办？
检查 DeepSeek API 密钥是否有效，网络连接是否正常。

### Q2: 图片生成失败？
检查字体文件路径是否正确，PIL 库是否正确安装。

### Q3: 微信发布失败？
检查 APPID 和 APPSECRET 是否正确，Access Token 是否有效，标题是否超过 64 字符。

### Q4: URL 重定向解析失败？
检查 `login_cookies.json` 是否存在且有效（7天内）。

### Q5: 如何处理多条记录？
发送多个 API 请求，系统会自动排队处理。

### Q6: TRUE 和 FALSE 的区别？
TRUE 判定显示绿色"真实类型"，FALSE 判定显示红色"虚假类型"。

## 10. 更新日志

- 2026-03-10: 更新 WORKFLOW 文档，改为 API 服务模式
- 2026-03-07: 添加 URL 重定向解析功能
- 2026-03-07: 添加 TRUE/FALSE 不同颜色显示
- 2026-03-07: 添加请求日志记录
- 2026-02-12: 修复微信和今日头条发布功能
- 2026-02-12: 创建 WORKFLOW 文档
- 2026-02-09: 优化海报生成模块
- 2026-02-06: 添加 DeepSeek 翻译功能
