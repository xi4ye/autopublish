# 新闻自动发布系统 (AutoPublish)

一个新闻事实核查自动化发布系统，支持自动翻译、生成海报、并发布到微信公众号和今日头条。

## 功能特性

- **API 服务**：提供 RESTful API 接口，支持异步队列处理
- **智能翻译**：使用 DeepSeek API 翻译英文内容为中文
- **海报生成**：自动生成新闻鉴别报告海报，支持 TRUE/FALSE 不同颜色显示
- **多平台发布**：支持微信公众号和今日头条自动发布
- **URL 解析**：自动解析 URL 重定向，获取最终链接

## 快速开始

### 1. 环境准备

```bash
# 安装依赖
pip install -r requirements.txt

# 复制环境变量模板
cp .env.example .env

# 编辑 .env 文件，填入实际的 API 密钥
```

### 2. 配置环境变量

编辑 `.env` 文件：

```bash
# DeepSeek API 配置
DEEPSEEK_API_KEY=your_api_key_here
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-reasoner

# 微信公众号配置
WX_APP_ID=your_wechat_app_id
WX_APP_SECRET=your_wechat_app_secret

# 今日头条/同花顺配置
THS_CREDENTIALS_FILE=username
```

### 3. 启动服务

```bash
python api_server.py
```

服务将在 `http://127.0.0.1:8888` 启动。

### 4. 发送请求

```bash
curl -X POST http://127.0.0.1:8888/api/news \
  -H "Content-Type: application/json" \
  -d '{
    "id": 1,
    "description": "新闻标题",
    "auto_publish": true,
    "history": {...},
    "last_output": {...},
    "relevant_news": {...}
  }'
```

## API 接口

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/news` | POST | 提交新闻处理任务 |
| `/api/task/{task_id}` | GET | 查询任务状态 |
| `/api/queue` | GET | 查询队列状态 |
| `/health` | GET | 健康检查 |

## 项目结构

```
autopublish/
├── api_server.py               # API 服务入口
├── translate_agent.py          # 翻译模块
├── translate_formatted.py      # 格式化数据翻译
├── data_adapter.py             # 数据格式化模块
├── create_detailed_news_template.py  # 海报生成模块
├── fenmian.py                  # 封面生成模块
├── create_template.py          # 文档生成模块
├── autowx.py                   # 微信发布模块
├── autojr_pydoll.py            # 今日头条发布模块
├── fonts/                      # 字体文件
├── imgs/                       # 图片资源
├── data/                       # 数据目录
├── output/                     # 输出目录
└── logs/                       # 日志目录
```

## 核心模块

| 模块 | 功能 |
|------|------|
| `api_server.py` | API 服务入口，异步任务队列 |
| `translate_agent.py` | DeepSeek 翻译代理 |
| `data_adapter.py` | 数据格式化适配器 |
| `create_detailed_news_template.py` | 海报生成器 |
| `autowx.py` | 微信公众号发布 |
| `autojr_pydoll.py` | 今日头条发布 |

## 输出文件

| 文件 | 说明 |
|------|------|
| `output/image2_{timestamp}.png` | 详细鉴别海报 |
| `output/image_wx_{timestamp}.png` | 微信平台封面 |
| `output/image_jr_{timestamp}.png` | 今日头条封面 |
| `output/jrbd_{timestamp}.docx` | Word 文档 |

## 注意事项

1. **API 密钥安全**：请勿将 API 密钥提交到版本控制系统
2. **字体文件**：确保 `fonts/` 目录下有所需的中文字体
3. **微信发布**：草稿自动创建，需手动在公众号后台确认发布
4. **Cookies 有效期**：`login_cookies.json` 有效期为 7 天

## 详细文档

查看 [WORKFLOW.md](./WORKFLOW.md) 了解完整的工作流程和技术细节。

## 许可证

MIT License
