---
auto_review_age_days: 1
auto_review_reasons:
- importance:5+10
- novelty:5+10
- confidence:2+4
- ppt_potential:4+4
- public_brief_potential:3+3
- topic_priority:5+10
- source_type:chinese-media-digest-item-2
- primary_source+2
- 'score>=28: 自动接受'
auto_review_score: 41
book_potential: 4
collected_date: '2026-08-31'
confidence: 2
created_at: '2026-08-31T08:03:58+08:00'
date: '2026-08-31'
digest_item_index: 2
entities:
- m.sohu.com
id: 2026-08-31-industry-ai-industry-openaicursor-1112
importance: 5
industry_dimensions:
- company
keywords_en: &id001
- ai-industry
novelty: 5
parent_source_title: 腾讯研究院AI速递 20260831
parent_source_url: https://m.sohu.com/a/1069745836_455313?scm=10001.325_13-325_13.0.0-0-0-0-0.5_1334
ppt_potential: 4
primary_source: true
public_brief_potential: 3
review_status: accepted
reviewed_at: '2026-09-01T08:24:00+08:00'
reviewed_by: auto
source_type: chinese-media-digest-item
source_url: https://m.sohu.com/a/1069745836_455313?scm=10001.325_13-325_13.0.0-0-0-0-0.5_1334&digest_item=2
title_en: OpenAI终止向Cursor供应模型，11月12日起生效
title_zh: OpenAI终止向Cursor供应模型，11月12日起生效
topics: *id001
track: industry
---

# 知识卡片：OpenAI终止向Cursor供应模型，11月12日起生效

**英文标题**：OpenAI Terminates Direct Model Supply to Cursor, Effective November 12  
**英文关键词**：OpenAI; Cursor; Anysphere; SpaceX; AI industry; model API neutrality; control-change clause  
**原始来源**：腾讯研究院AI速递 20260831（https://m.sohu.com/a/1069745836_455313?scm=10001.325_13-325_13.0.0-0-0-0-0.5_1334&digest_item=2）

## 一句话结论
据腾讯研究院AI速递，OpenAI 因 SpaceX 以 600 亿美元收购 Cursor 母公司 Anysphere 并完成交割，启动控制权变更条款，宣布自 11 月 12 日起终止直接向 Cursor 供应模型；缓冲期后开发者只能自带 API Key 使用，OpenAI 称无法确认 SpaceX 会遵守服务条款。此事件显示底层模型 API 的中立性正被上下游竞争关系取代。

## 事件概述或研究问题
事件概述：SpaceX 完成对 Anysphere 的收购交割 15 天后，OpenAI 启动控制权变更条款，宣布终止直接向 Cursor 供模；新模型包括 Astra 均不再提供，开发者需在缓冲期后自带 API Key。研究问题：当模型提供商与下游应用厂商之间出现资本/竞争关系时，模型 API 还能否保持中立？

## 方法/产品要点
- 触发机制：控制权变更条款（change-of-control provision），由 OpenAI 在 Anysphere 被收购后启动。
- 涉及产品：Cursor（AI 编程工具）、Anysphere（Cursor 母公司）、OpenAI 模型及新模型 Astra。
- 执行方式：OpenAI 终止直接供模，不再提供新模型（包括 Astra）；过渡期后开发者自带 API Key。
- 相关先例：据同一速递，此前 Anthropic 曾对拟被 OpenAI 收购的 Windsurf 限流。

## 主要结果或产业意义
主要结果：11 月 12 日起 Cursor 不能再从 OpenAI 获取直接模型供应，开发者需自带 API Key；OpenAI 给出的理由是 SpaceX 作为新控制方可能不遵守服务条款（具体条款内容待核实）。产业意义：模型 API 不再天然中立，上下游并购/控股会直接影响模型供给；Anthropic/Windsurf 与 OpenAI/Cursor 构成一组对称案例。

## 与既有脉络的关系
已有 OpenRouter 归档卡片显示，LLM 网关、模型路由、多模态 API 等中间层在 2024–2026 年快速产品化。本条是同一时期的断供案例，为“开发者为何需要自带 Key、多路由和模型抽象层”补充了来自上游模型厂商的供应链风险证据。

## 为什么重要
对开发者而言，Cursor 内置 OpenAI 模型的工作流可能在 11 月 12 日后被打破，需要用自带 API Key 或其他来源替代。对行业而言，模型层与应用层的纵向整合可能优先于 API 中立承诺，渠道控制权正在成为 AI 竞争的新战场；这也将推高开放路由/网关类基础设施的价值。

## 局限与不确定性
- 交易金额、交割日期、15 天计算方式、“控制权变更条款”具体内容均未在材料中提供原始合同或官方公告，待核实。
- “11月12日”的年份未在摘要中写明，按速递标题/URL 推断为 2026 年，待核实。
- “新模型包括 Astra 都不再提供”中的 Astra 在同期速递中仍处于内测/预计发布状态，其对 Cursor 供应的具体安排待核实。
- 缓冲期时长、自带 API Key 是否适用于所有用户/企业客户、历史模型访问是否受影响，材料未说明，待核实。
- Anthropic 对 Windsurf 限流的细节未展开，待核实。

## 可用于图书/PPT/简报的角度
- 模型供应链风险：当模型厂商、AI 应用与资本收购交织，API 中立性如何保证？
- 纵向整合与渠道冲突：OpenAI/Cursor 与 Anthropic/Windsurf 的“对称”案例。
- 自带 Key 模式：从平台默认供模到开发者自带密钥，AI 应用层的防御性架构。
- 中间层机会：模型网关、路由与多模型抽象层可能因断供风险而成为刚需。

## 原始材料
腾讯研究院AI速递 20260831（Sohu）  
URL: https://m.sohu.com/a/1069745836_455313?scm=10001.325_13-325_13.0.0-0-0-0-0.5_1334&digest_item=2