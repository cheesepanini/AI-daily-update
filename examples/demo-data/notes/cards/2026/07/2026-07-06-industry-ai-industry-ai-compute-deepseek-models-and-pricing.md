---
book_potential: 3
confidence: 4
created_at: '2026-07-06T22:19:07+08:00'
date: '2026-07-06'
entities:
- api-docs.deepseek.com
id: 2026-07-06-industry-ai-industry-ai-compute-deepseek-models-and-pricing
importance: 4
industry_dimensions:
- company
keywords_en: &id001
- ai-industry
- ai-compute
novelty: 3
ppt_potential: 4
primary_source: true
public_brief_potential: 3
review_status: rejected
source_type: company-news
source_url: https://api-docs.deepseek.com/quick_start/pricing
title_en: DeepSeek Models and Pricing
title_zh: DeepSeek 模型与定价
topics: *id001
track: industry
---

# 知识卡片：DeepSeek 模型与定价

## 一句话结论
DeepSeek API 提供 V4-Flash 和 V4-Pro 两种模型，定价策略中**缓存命中可大幅降低成本**（如 Flash 缓存命中仅 $0.0028/1M tokens），显著降低推理成本。

## 事件概述或研究问题
DeepSeek 发布 API 文档，明确了其最新 V4 系列模型的定价、特性及计费规则。模型支持思维模式切换、长上下文（1M tokens）和多种高级功能，适合企业级应用和开发者部署。

## 方法/产品要点
- **模型名称**：`deepseek-v4-flash` 和 `deepseek-v4-pro`
- **上下文长度**：1M tokens；**最大输出**：384K tokens
- **思维模式**：支持非思维（non-thinking）和思维（thinking）模式，默认思维模式
- **基础 URL**：OpenAI 格式 `https://api.deepseek.com`；Anthropic 格式 `https://api.deepseek.com/anthropic`
- **并发限制**：Flash 2500 请求/秒；Pro 500 请求/秒
- **功能支持**：JSON 输出、工具调用、聊天前缀补全（Beta）、FIM 补全（Beta，仅非思维模式）

## 主要结果或产业意义
| 计价项（每1M tokens） | Flash 价格 | Pro 价格 |
|----------------------|------------|----------|
| 输入（缓存命中）      | $0.0028    | $0.003625 |
| 输入（缓存未命中）    | $0.14      | $0.435   |
| 输出                  | $0.28      | $0.87    |

- **缓存命中**成本极低，仅为未命中的 1/50（Flash）至 1/120（Pro），鼓励开发者利用缓存优化。
- 对比主流 API 定价，DeepSeek 在缓存场景下具备明显价格优势，可能推动更多长上下文应用落地。

## 为什么重要
1. **低成本推理**：对于高频、可缓存的请求（如 prompt 前缀相同的对话），成本可降至接近免费。
2. **长上下文能力**：1M 上下文 + 384K 输出，支持文档分析、代码生成等复杂任务。
3. **兼容性**：提供 OpenAI/Anthropic 兼容 API，降低迁移成本。

## 局限与不确定性
- **模型性能**：材料未提供基准测试或能力对比，实际效果待核实。
- **缓存机制**：未说明缓存命中条件（如时间窗口、前缀匹配规则），需自行测试。
- **价格调整**：页面声明价格可能变动，建议定期查看更新。
- **废弃说明**：旧模型名称 `deepseek-chat` 和 `deepseek-reasoner` 将于 2026/07/24 15:59 UTC 废弃，需及时迁移。

## 可用于图书/PPT/简报的角度
- **行业对比**：将 DeepSeek V4 定价与 GPT-4o、Claude 3.5 等对比，突出缓存命中场景的成本优势。
- **降本策略**：展示如何通过 prompt 设计（如固定前缀）提高缓存命中率。
- **技术架构**：长上下文模型对 RAG（检索增强生成）和 Agent 应用的支撑。

## 原始材料
- 标题：Models & Pricing | DeepSeek API Docs
- 描述：The prices listed below are in units of per 1M tokens... We will bill based on the total number of input and output tokens by the model.
- 来源 URL：`https://api-docs.deepseek.com/quick_start/pricing`
- 英文关键词：DeepSeek, API pricing, token, cache hit, V4 Flash, V4 Pro