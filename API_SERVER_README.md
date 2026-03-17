# API 服务器使用说明

## 概述

这是一个 HTTP 服务器，用于接收同事发送的 JSON 格式新闻数据，自动处理并生成海报。

## 启动服务器

### 方式一：使用默认配置（127.0.0.1:8888）

```bash
cd /home/wangwei/publish
python3 api_server.py
```

### 方式二：指定端口

```bash
python3 api_server.py 8080
```

### 方式三：指定主机和端口

```bash
python3 api_server.py 8080 0.0.0.0
```

## 停止服务器

按 `Ctrl + C` 即可停止服务器。

## API 端点

### 1. 健康检查

**请求：**
```http
GET /health
或
GET /
```

**响应示例：**
```json
{
  "status": "ok",
  "service": "news_publisher",
  "timestamp": "2026-03-03T14:00:00"
}
```

### 2. 接收新闻数据

**请求：**
```http
POST /api/news
或
POST /
Content-Type: application/json

{
  "id": 8,
  "description": "新闻标题内容",
  "history": {
    "k=5": [
      {
        "Date": "2026-01-22",
        "Result": "FALSE"
      }
    ],
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
    "id": 8,
    "claim": "新闻标题内容",
    "collection": [
      {
        "id": 1,
        "title": "相关新闻标题1",
        "url": "url:https://example.com/news1"
      }
    ]
  }
}
```

**响应示例（成功）：**
```json
{
  "status": "success",
  "id": 8,
  "timestamp": "20260303_140000",
  "files": {
    "translated": "data/formated_translated_20260303_140000.json",
    "poster": "output/image2_20260303_140000.png"
  }
}
```

**响应示例（失败）：**
```json
{
  "status": "error",
  "message": "错误描述"
}
```

## 数据格式

详细的数据格式说明请参考：[INPUT_API_DOC.md](INPUT_API_DOC.md)

## 使用示例

### Python 示例

```python
import requests
import json

data = {
    "id": 123,
    "description": "新闻标题",
    # ... 其他字段
}

response = requests.post(
    "http://localhost:8888/api/news",
    json=data
)
result = response.json()
print(result)
```

### curl 示例

```bash
curl -X POST http://localhost:8888/api/news \
  -H "Content-Type: application/json" \
  -d @data.json
```

## 测试 API

先在一个终端启动服务器：
```bash
python3 api_server.py
```

然后在另一个终端运行测试：
```bash
python3 test_api.py
```

## 文件说明

| 文件 | 说明 |
|------|------|
| `api_server.py` | API 服务器主程序 |
| `test_api.py` | API 测试脚本 |
| `INPUT_API_DOC.md` | 输入数据格式文档 |
| `API_SERVER_README.md` | 本说明文档 |

## 处理流程

1. 接收 JSON 数据
2. 使用 DeepSeek API 翻译英文内容
3. 格式化为结构化数据
4. 生成详细海报和封面
5. 返回处理结果

## 注意事项

- 服务器默认监听 `127.0.0.1:8888`
- 确保端口未被占用
- 确保有足够的磁盘空间存储生成的文件
- 确保 DeepSeek API 密钥有效
- 同一台服务器上的其他用户可以通过 `127.0.0.1:8888` 或 `localhost:8888` 访问
