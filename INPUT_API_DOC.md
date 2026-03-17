# 输入数据接口文档

## 1. 概述

本文档描述了新闻自动发布系统的输入数据格式。输入数据采用 **JSONL (JSON Lines)** 格式，每行是一个独立的 JSON 对象，代表一条新闻记录。

## 2. 文件格式

- **文件类型**: JSONL (`.jsonl`)
- **编码**: UTF-8
- **每行**: 一个完整的 JSON 对象

## 3. 数据结构

### 3.1 完整数据结构

```json
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
      },
      {
        "id": 2,
        "title": "相关新闻标题2",
        "url": "url:https://example.com/news2"
      },
      {
        "id": 3,
        "title": "相关新闻标题3",
        "url": "url:https://example.com/news3"
      }
    ]
  }
}
```

### 3.2 字段说明

| 字段名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| `id` | integer | 是 | 新闻唯一标识符 |
| `description` | string | 是 | 新闻标题/描述内容 |
| `history` | object | 是 | 鉴别历史记录 |
| `last_output` | object | 是 | 最新鉴别分析报告 |
| `revelent_news` | object | 是 | 相关新闻集合 |

## 4. 字段详细说明

### 4.1 `id` 字段

- **类型**: integer
- **说明**: 新闻记录的唯一标识符
- **示例**: `8`, `1384`, `1383`

### 4.2 `description` 字段

- **类型**: string
- **说明**: 新闻标题或描述内容
- **示例**: `"Gemini准确率从21%飙到97%！谷歌只用了这一招：复制粘贴。"`

### 4.3 `history` 字段

- **类型**: object
- **说明**: 鉴别历史记录，包含不同 k 值的鉴别结果
- **结构**:

```json
{
  "k=5": [
    {
      "Date": "2026-01-22",
      "Result": "FALSE"
    }
  ],
  "k=10": [],
  "k=15": [],
  "k=20": []
}
```

| 子字段 | 类型 | 说明 |
|--------|------|------|
| `k=5` | array | 最近5条相关记录的鉴别结果 |
| `k=10` | array | 最近10条相关记录的鉴别结果 |
| `k=15` | array | 最近15条相关记录的鉴别结果 |
| `k=20` | array | 最近20条相关记录的鉴别结果 |

#### `history` 数组元素结构

| 字段名 | 类型 | 可选值 | 说明 |
|--------|------|--------|------|
| `Date` | string | - | 鉴别日期，格式：`YYYY-MM-DD` |
| `Result` | string \| null | `"TRUE"`, `"FALSE"`, `null` | 鉴别结果 |

**Result 值说明**:
- `"TRUE"`: 新闻内容真实
- `"FALSE"`: 新闻内容虚假
- `null`: 尚未鉴别

### 4.4 `last_output` 字段

- **类型**: object
- **说明**: 最新鉴别分析报告，包含详细的英文分析内容
- **结构**:

```json
{
  "k=5": "#### **1. COLLECTION**\n**Record ALL Analyst Reports...**",
  "k=10": "",
  "k=15": "",
  "k=20": ""
}
```

| 子字段 | 类型 | 说明 |
|--------|------|------|
| `k=5` | string | 对应 k=5 的详细分析报告（Markdown格式） |
| `k=10` | string | 对应 k=10 的详细分析报告 |
| `k=15` | string | 对应 k=15 的详细分析报告 |
| `k=20` | string | 对应 k=20 的详细分析报告 |

### 4.5 `revelent_news` 字段

- **类型**: object
- **说明**: 相关新闻集合，包含与当前新闻相关的其他新闻报道
- **结构**:

```json
{
  "id": 8,
  "claim": "新闻标题内容",
  "collection": [
    {
      "id": 1,
      "title": "相关新闻标题1",
      "url": "url:https://example.com/news1"
    },
    {
      "id": 2,
      "title": "相关新闻标题2",
      "url": "url:https://example.com/news2"
    },
    {
      "id": 3,
      "title": "相关新闻标题3",
      "url": "url:https://example.com/news3"
    }
  ]
}
```

| 子字段 | 类型 | 说明 |
|--------|------|------|
| `id` | integer | 新闻ID（与顶层 `id` 一致） |
| `claim` | string | 新闻声明/标题（与 `description` 一致） |
| `collection` | array | 相关新闻集合（最多3条） |

#### `collection` 数组元素结构

| 字段名 | 类型 | 说明 |
|--------|------|------|
| `id` | integer | 相关新闻序号（1-3） |
| `title` | string | 相关新闻标题 |
| `url` | string | 新闻链接（以 `url:` 为前缀） |

**URL 格式说明**:
- 格式：`url:https://实际链接地址`
- 示例：`url:https://www.example.com/news/article123`

## 5. `last_output` 内容格式

`last_output.k=5` 字段包含 Markdown 格式的详细分析报告，结构如下：

### 5.1 报告结构

```markdown
#### **1. COLLECTION**  
**Record ALL Analyst Reports one by one:**  
- **Analyst Report 1 (Importance Score: 100)**: 报告内容...
- **Analyst Report 2 (Importance Score: 95)**: 报告内容...
...

**+more**  

---

#### **2. ANALYSIS**  
**Evaluation of ALL recorded Analyst Reports one by one:**  
- **Analyst Report 1 (Importance Score: 100)**: 评估内容...
...

**Evidence Synthesis and Corroboration:**  
- 证据点1...
- 证据点2...
...

---

#### **3. CONCLUSION**  
### **Final Judgment**  
**FALSE**  

**Detailed Reasons for False Classification:**  
Ⅰ. **理由标题**  
理由内容...

Ⅱ. **理由标题**  
理由内容...

**NEWS TYPE**  
[Business]
```

### 5.2 关键标题对照表

| 英文标题 | 中文翻译 |
|----------|----------|
| `#### **1. COLLECTION**` | `#### **1. 信息收集**` |
| `**Record ALL Analyst Reports one by one:**` | `**逐一记录所有分析师报告：**` |
| `#### **2. ANALYSIS**` | `#### **2. 分析**` |
| `**Evaluation of ALL recorded Analyst Reports one by one:**` | `**对所有记录的分析师报告进行逐一评估：**` |
| `**Evidence Synthesis and Corroboration:**` | `**证据综合与互证：**` |
| `#### **3. CONCLUSION**` | `#### **3. 结论**` |
| `**Final Judgment**` | `**最终判定**` |
| `**NEWS TYPE**` | `**新闻类型**` |
| `**Detailed Reasons for False Classification:**` | `**归类为错误的详细理由：**` |

## 6. 完整示例

### 6.1 输入数据示例（Result 为 FALSE）

```json
{
  "id": 8,
  "description": "Gemini准确率从21%飙到97%！谷歌只用了这一招：复制粘贴。",
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
    "k=5": "#### **1. COLLECTION**  \n**Record ALL Analyst Reports one by one:**  \n- **Analyst Report 1 (Importance Score: 100)**: Gemini's accuracy improved from 21% to 97% within a single year, according to internal performance benchmarks released in Q2 2024. This improvement was attributed to a major architectural update, not copying or pasting existing models.  \n- **Analyst Report 2 (Importance Score: 95)**: Google's AI team confirmed in a public blog post on June 15, 2024, that the performance jump in Gemini was due to enhanced training data diversity and fine-tuning techniques, not replication of prior models.  \n\n**+more**  \n\n---\n\n#### **2. ANALYSIS**  \n**Evaluation of ALL recorded Analyst Reports one by one:**  \n- **Analyst Report 1 (Importance Score: 100)** provides the core factual claim: Gemini's accuracy increased from 21% to 97% in Q2 2024, with an official explanation tied to architectural improvements—this is the only report that confirms the numerical accuracy shift.  \n\n**Evidence Synthesis and Corroboration:**  \n- The numerical claim (21% → 97%) is supported by internal benchmarks and public disclosures.  \n- The methodological claim (\"copy-paste\") is directly contradicted by Google's own technical reports, peer-reviewed AI literature, and ethical guidelines.  \n\n---\n\n#### **3. CONCLUSION**  \n### **Final Judgment**  \n**FALSE**  \n\n**Detailed Reasons for False Classification:**  \nⅠ. **Contradictory Evidence**  \nThe claim that Google used \"copy-paste\" to improve Gemini's accuracy directly contradicts Google's own public documentation and technical reports from June 2024, which state the improvement resulted from enhanced training and fine-tuning.  \nⅡ. **Lack of Supporting Data**  \nNo verifiable source, technical paper, or internal document supports the \"copy-paste\" methodology.  \n\n**NEWS TYPE**  \n[Business]",
    "k=10": "",
    "k=15": "",
    "k=20": ""
  },
  "revelent_news": {
    "id": 8,
    "claim": "Gemini准确率从21%飙到97%！谷歌只用了这一招：复制粘贴。",
    "collection": [
      {
        "id": 1,
        "title": "谷歌Gemini模型性能提升背后的技术突破 | 科技日报",
        "url": "url:https://example.com/tech/gemini-breakthrough"
      },
      {
        "id": 2,
        "title": "AI模型准确率提升的真实路径 | 人工智能周刊",
        "url": "url:https://example.com/ai/accuracy-improvement"
      },
      {
        "id": 3,
        "title": "大型语言模型训练方法解析 | 深度学习研究",
        "url": "url:https://example.com/research/llm-training"
      }
    ]
  }
}
```

### 6.2 未鉴别记录示例（Result 为 null）

```json
{
  "id": 1,
  "description": "Gemini准确率从21%飙到97%！谷歌只用了这一招：复制粘贴。",
  "history": {
    "k=5": [
      {
        "Date": "2026-01-22",
        "Result": null
      }
    ],
    "k=10": [],
    "k=15": [],
    "k=20": []
  },
  "last_output": {
    "k=5": "",
    "k=10": "",
    "k=15": "",
    "k=20": ""
  },
  "revelent_news": {
    "id": 1,
    "claim": "Gemini准确率从21%飙到97%！谷歌只用了这一招：复制粘贴。",
    "collection": []
  }
}
```

## 7. 格式化后的数据结构

系统会将输入数据翻译并格式化为以下结构，供海报生成模块使用：

### 7.1 格式化数据结构

```json
{
  "description": "新闻标题",
  "Date": "2026-02-06",
  "id": 1384,
  "CONCLUSION": {
    "FinalJudgment": "FALSE",
    "DetailedReasons": [
      {
        "id": "Ⅰ",
        "title": "理由标题",
        "content": "理由内容"
      },
      {
        "id": "Ⅱ",
        "title": "理由标题",
        "content": "理由内容"
      }
    ]
  },
  "ANALYSIS": {
    "summary": "所有经过验证的报道和分析师报告均证实以下事实：",
    "evidence": [
      {
        "id": 1,
        "title": "证据标题",
        "content": "证据内容"
      },
      {
        "id": 2,
        "title": "证据标题",
        "content": "证据内容"
      }
    ]
  },
  "COLLECTION": [
    {
      "id": 1,
      "score": 100,
      "content": "分析师报告内容"
    }
  ],
  "NEWS_TYPE": "Business",
  "revelent_news": {
    "id": 1384,
    "claim": "新闻标题",
    "collection": [
      {
        "id": 1,
        "title": "相关新闻标题1",
        "url": "url:https://example.com/news1"
      },
      {
        "id": 2,
        "title": "相关新闻标题2",
        "url": "url:https://example.com/news2"
      },
      {
        "id": 3,
        "title": "相关新闻标题3",
        "url": "url:https://example.com/news3"
      }
    ]
  }
}
```

### 7.2 格式化字段说明

| 字段名 | 类型 | 说明 |
|--------|------|------|
| `description` | string | 新闻标题 |
| `Date` | string | 鉴别日期 |
| `id` | integer | 新闻ID |
| `CONCLUSION` | object | 结论部分 |
| `CONCLUSION.FinalJudgment` | string | 最终判定（"TRUE" 或 "FALSE"） |
| `CONCLUSION.DetailedReasons` | array | 详细理由列表 |
| `ANALYSIS` | object | 分析部分 |
| `ANALYSIS.summary` | string | 分析摘要 |
| `ANALYSIS.evidence` | array | 证据列表 |
| `COLLECTION` | array | 分析师报告列表 |
| `NEWS_TYPE` | string | 新闻类型 |
| `revelent_news` | object | 相关新闻（从输入直接继承） |
| `revelent_news.collection` | array | 相关新闻集合（最多3条） |

## 8. 数据处理流程

```
输入 JSONL 文件
       ↓
筛选 Result = "FALSE" 的记录
       ↓
读取 last_output.k=5 内容
       ↓
DeepSeek API 翻译（英文 → 中文）
       ↓
格式化为结构化 JSON
  - 解析 COLLECTION（分析师报告）
  - 解析 ANALYSIS（证据链）
  - 解析 CONCLUSION（详细理由）
  - 保留 revelent_news（相关新闻）
       ↓
生成海报和封面
       ↓
发布到平台
```

## 9. 筛选条件

系统会自动筛选满足以下条件的记录进行处理：

1. `history.k=5[0].Result` 值为 `"FALSE"`
2. `last_output.k=5` 内容不为空

## 10. 注意事项

1. **编码**: 文件必须使用 UTF-8 编码
2. **格式**: 每行必须是有效的 JSON 对象
3. **必填字段**: `id`, `description`, `history`, `last_output`, `revelent_news` 为必填字段
4. **日期格式**: 日期统一使用 `YYYY-MM-DD` 格式
5. **空数组**: `k=10`, `k=15`, `k=20` 可以为空数组 `[]`
6. **空字符串**: `last_output` 中的未使用字段可以为空字符串 `""`
7. **相关新闻**: `revelent_news.collection` 最多包含3条相关新闻，可以为空数组
8. **URL格式**: 相关新闻的 `url` 字段必须以 `url:` 为前缀

## 11. 错误处理

| 错误类型 | 说明 | 处理方式 |
|----------|------|----------|
| JSON 解析错误 | 某行不是有效的 JSON | 跳过该行，记录错误日志 |
| 缺少必填字段 | 缺少 `id` 或 `description` | 跳过该记录 |
| 编码错误 | 非 UTF-8 编码 | 尝试转换编码或报错 |
| 空文件 | 文件无内容 | 返回空列表 |
| 相关新闻格式错误 | `url` 格式不正确 | 记录警告，继续处理 |

## 12. 版本历史

| 版本 | 日期 | 说明 |
|------|------|------|
| 1.2 | 2026-02-12 | 将 `revelent_news` 添加为输入必填字段 |
| 1.1 | 2026-02-12 | 添加格式化数据结构说明，补充相关新闻字段说明 |
| 1.0 | 2026-02-12 | 初始版本 |
