---
auto_review_age_days: 1
auto_review_reasons:
- importance:4+8
- novelty:4+8
- confidence:3+6
- ppt_potential:4+4
- public_brief_potential:4+4
- topic_priority:5+10
- source_type:benchmark-update+2
- primary_source+2
- 'score>=28: 自动接受'
auto_review_score: 44
book_potential: 4
collected_date: '2026-08-19'
confidence: 3
created_at: '2026-08-19T08:16:43+08:00'
date: '2026-08-18'
entities:
- artificialanalysis.ai
event_date: '2026-08-18'
id: 2026-08-18-industry-benchmark-evaluation-agent-launch-artificial-analysis-search-index-compare
importance: 4
industry_dimensions:
- company
keywords_en: &id001
- benchmark-evaluation
- agent
novelty: 4
ppt_potential: 4
primary_source: true
public_brief_potential: 4
review_status: accepted
reviewed_at: '2026-08-20T08:12:18+08:00'
reviewed_by: auto
source_type: benchmark-update
source_url: https://artificialanalysis.ai/articles/search-api
title_en: Launch Artificial Analysis Search Index Compare search API providers on
  quality, cost, and speed using the same agent
title_zh: Artificial Analysis Search Index：同一智能体、不同搜索 API 的质量/成本/速度基准
topics: *id001
track: industry
---

# 知识卡片：Artificial Analysis Search Index：同一智能体、不同搜索 API 的质量/成本/速度基准

## 一句话结论
Artificial Analysis 发布 Search Index，用同一个候选模型和同一个开源智能体 harness 横向对比多家搜索 API 提供商，量化搜索工具在质量、成本、速度上对智能体的增益。

## 事件概述或研究问题
2026 年 8 月 18 日，Artificial Analysis 发布文章“Announcing the Artificial Analysis Search Index: Same Agent, Different Search”，推出一个新基准：在完全相同的智能体设置下，仅替换搜索 API 提供商，对比其搜索质量、成本和速度。研究问题是：当智能体使用不同的搜索 API 时，最终任务表现、总成本和总耗时会有多大差异？

## 方法/产品要点
- 固定候选模型：GPT-5.6 Luna (medium)。
- 固定智能体 harness：Stirrup（开源），提供 `web_search` 和 `web_fetch` 两个工具，模型最多有 25 轮搜索；若用完 25 轮未调用 `finish`，该任务得 0 分。
- 唯一变量：搜索 API 提供商。
- 基准任务：
  - DeepSearchQA：需要多次搜索的宽泛研究问题，答案以列表计分，LLM 评分员计算 F1，全量评估集 900 个任务。
  - BrowseComp：需要多跳浏览的难找事实，使用 200 个样本的困难子集，按精确答案正确率计分。
  - AA-Omniscience：600 道私有事实问题，覆盖 6 个领域，按准确率计分。
- Search Index：上述三个基准得分的等权平均，0–100 分。
- 基线：同一模型在不使用搜索工具的情况下单次生成完成同样任务（模型 only）。
- 成本：搜索 API 调用费用 + 候选模型全部 token 费用。
- 时间：搜索调用实测时间 + 模型时间（由 token 数与模型输出速度推导）。

## 主要结果或产业意义
启动时榜单覆盖 7 个搜索提供商、11 个结果。部分得分（Artificial Analysis Search Index）：

| 提供商 | Search Index |
|---|---|
| Parallel Search (advanced) | 75 |
| Exa Search (auto) | 74 |
| Firecrawl Search | 73 |
| Parallel Search (basic) | 73 |
| Exa Search (fast) | 68 |
| You.com Search | 68 |
| Parallel Search (turbo) | 67 |

- 模型无搜索工具基线在 Search Index 上约为 33，显示搜索工具带来的显著提升。
- 成本并非只看搜索单价：Parallel Search (advanced) 搜索成本高于 basic，但总成本反而更低（每任务 $0.084 vs $0.11），因为高质量搜索结果让模型少用约一半 token。
- 速度也不是只看单次搜索延迟：Keenable Search (realtime) 平均单次搜索最快（0.34s），总耗时也最低（15.1s），得分 67；Exa Search (fast) 单次搜索比 auto 快，但每任务总成本更高（$0.16 vs $0.13）。
- 产业意义：选择搜索 API 需要同时权衡质量、成本和端到端延迟；搜索结果的“聚焦程度”会直接影响模型 token 消耗和推理开销，进而影响总成本。

## 为什么重要
这是首个用“同一智能体、同一模型、唯一改变搜索提供商”的方式横向评估搜索 API 的公开基准。它把搜索 API 从“单次查询延迟/价格”的评估维度，扩展为“对智能体任务成功率、总成本、总耗时”的系统级评估。相比已有相关卡片（OpenRouter MCP、通用智能体性能评估、ParseBench 文档解析基准），本条记录的是对搜索工具层的专门基准评测，属于对 AI agent 评估体系的增量贡献。

## 局限与不确定性
- 候选模型仅使用 GPT-5.6 Luna (medium)，其他模型下结论可能不同。
- 基准只覆盖三类搜索相关任务，不能代表所有真实 agent 搜索场景。
- AA-Omniscience 为私有子集，外部无法完全复现。
- 时间中的模型时间由 token 速度推导，并非实测模型执行时间。
- 榜单结果截至发布时；提供商和模型会持续更新，最新结果需查阅 Search API leaderboard。
- 完整 harness 设置、评分细节和 contamination 过滤方式在 methodology 页面，本文未展开，具体实现细节待核实。

## 可用于图书/PPT/简报的角度
- 如何系统评估 AI Agent 的搜索工具：固定模型与 harness，只换搜索 API。
- 搜索质量如何影响 token 成本：高质量结果可显著降低模型推理消耗。
- 搜索 API 的“性价比”不只看单次查询价格，还要看端到端任务成本。
- 延迟陷阱：单次搜索快不等于整体任务快，因为模型可能因结果差而搜索更多轮。
- Search Index 作为“质量-成本-速度”三维评估框架的示例。

## 与既有脉络的关系
延续了 Artificial Analysis 对模型和智能体性能的评估体系；与 ParseBench 不同，本基准不考察文档解析，而是考察搜索工具对智能体任务表现的增益；与 OpenRouter MCP 服务器条目相比，本条提供了可复现的搜索 API 对比方法和发布时的具体榜单数据。

## 原始材料
- 英文标题：Announcing the Artificial Analysis Search Index: Same Agent, Different Search
- 英文关键词：Search API benchmark, AI agent, DeepSearchQA, BrowseComp, AA-Omniscience, Stirrup, Artificial Analysis Search Index
- 来源：https://artificialanalysis.ai/articles/search-api