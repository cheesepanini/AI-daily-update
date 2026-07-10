# AI 消息速览公开 API

公开 API 面向普通网页、微信小程序和未来移动端，均为只读接口。

基础路径：

```text
/api/v1
```

推荐线上域名：

```text
https://ai.cheesepanini.fun/api/v1
```

## 权限

匿名可访问：

```text
GET /api/v1/meta
GET /api/v1/cards
GET /api/v1/cards/{card_id}
```

公开 API 不提供审核、删除、生成卡片、PPT、消息源管理等管理员操作。

公开卡片范围：

```text
包含 accepted / needs-review / later
排除 rejected
排除 notes/trash
```

## GET /api/v1/meta

获取 API 基础信息。

示例：

```bash
curl http://127.0.0.1:8001/api/v1/meta
```

返回：

```json
{
  "api_version": "v1",
  "project_name": "AI-Daily-Update",
  "server_time": "2026-07-09T10:00:00+08:00",
  "available_tracks": [
    {"id": "academic", "label": "学术前沿"},
    {"id": "industry", "label": "产业观察"}
  ],
  "available_statuses": [
    {"id": "accepted", "label": "已接受"},
    {"id": "needs-review", "label": "待审核"},
    {"id": "later", "label": "稍后处理"}
  ],
  "default_page_size": 20,
  "max_page_size": 50
}
```

## GET /api/v1/cards

按事件日期倒序获取公开知识卡片。

参数：

```text
page       页码，默认 1
page_size  每页数量，默认 20，最大 50
status     可选：accepted / needs-review / later
track      可选：academic / industry
topic      可选：主题 ID，例如 agent
from_date  可选：事件日期起始，YYYY-MM-DD
to_date    可选：事件日期结束，YYYY-MM-DD
```

示例：

```bash
curl "http://127.0.0.1:8001/api/v1/cards?page=1&page_size=5"
curl "http://127.0.0.1:8001/api/v1/cards?track=industry&topic=agent"
curl "http://127.0.0.1:8001/api/v1/cards?from_date=2026-07-01&to_date=2026-07-09"
```

返回：

```json
{
  "api_version": "v1",
  "items": [
    {
      "id": "card-id",
      "title": "中文标题",
      "title_en": "English title",
      "event_date": "2026-07-08",
      "info_date": "2026-07-08",
      "collected_date": "2026-07-09",
      "status": "needs-review",
      "status_label": "待审核",
      "track": "industry",
      "track_label": "产业观察",
      "source_label": "OpenAI",
      "source_url": "https://example.com",
      "topics": ["agent"],
      "conclusion": "一句话结论。",
      "event_overview": "事件概述。",
      "detail_url": "/api/v1/cards/card-id"
    }
  ],
  "pagination": {
    "page": 1,
    "page_size": 5,
    "total": 100,
    "total_pages": 20,
    "has_previous": false,
    "has_next": true
  }
}
```

## GET /api/v1/cards/{card_id}

获取公开卡片详情。

示例：

```bash
curl http://127.0.0.1:8001/api/v1/cards/card-id
curl "http://127.0.0.1:8001/api/v1/cards/card-id?markdown=true"
```

返回：

```json
{
  "id": "card-id",
  "title": "中文标题",
  "title_en": "English title",
  "event_date": "2026-07-08",
  "info_date": "2026-07-08",
  "collected_date": "2026-07-09",
  "status": "accepted",
  "status_label": "已接受",
  "track": "industry",
  "track_label": "产业观察",
  "source_label": "OpenAI",
  "source_url": "https://example.com",
  "topics": ["agent"],
  "conclusion": "一句话结论。",
  "event_overview": "事件概述。",
  "detail_url": "/api/v1/cards/card-id",
  "content_html": "<h2>一句话结论</h2>...",
  "content_markdown": "",
  "sections": [
    {"title": "一句话结论", "content": "一句话结论。"},
    {"title": "事件概述", "content": "事件概述。"}
  ]
}
```

默认不返回 Markdown 原文。需要时使用：

```text
?markdown=true
```

## 错误格式

未找到或不在公开范围内：

```json
{
  "error": {
    "code": "not_found",
    "message": "卡片不存在。"
  }
}
```

HTTP 状态码：

```text
404
```

## 小程序接入建议

小程序端建议优先使用：

```text
GET /api/v1/cards
GET /api/v1/cards/{card_id}
```

列表页使用结构化字段：

```text
title
event_date
status_label
track_label
source_label
conclusion
event_overview
```

详情页优先使用：

```text
sections
```

`content_html` 可用于网页端或小程序 rich-text，但小程序 rich-text 对 HTML 支持有限，建议小程序以 `sections` 为主。
