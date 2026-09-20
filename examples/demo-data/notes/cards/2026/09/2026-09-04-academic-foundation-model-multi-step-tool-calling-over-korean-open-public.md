---
auto_review_age_days: 1
auto_review_reasons:
- importance:2+4
- novelty:1+2
- confidence:1+2
- ppt_potential:1+1
- public_brief_potential:1+1
- topic_priority:5+10
- source_type:paper+2
- primary_source+2
- '22<score<28: 信号不够强，按配置设为 rejected'
auto_review_score: 24
book_potential: 1
collected_date: '2026-09-07'
confidence: 1
created_at: '2026-09-07T18:19:43+08:00'
date: '2026-09-04'
entities:
- arxiv.org
event_date: '2026-09-04'
id: 2026-09-04-academic-foundation-model-multi-step-tool-calling-over-korean-open-public
importance: 2
keywords_en: &id001
- foundation-model
novelty: 1
ppt_potential: 1
primary_source: true
public_brief_potential: 1
review_status: rejected
reviewed_at: '2026-09-08T08:35:23+08:00'
reviewed_by: auto
source_type: paper
source_url: https://arxiv.org/abs/2609.05395v1
title_en: 'Multi-Step Tool-Calling over Korean Open Public APIs: A Benchmark and a
  Data-Synthesis Recipe'
title_zh: 面向韩国开放公共 API 的多步工具调用：一个新基准与数据合成配方
topics: *id001
track: academic
---

# 知识卡片：面向韩国开放公共 API 的多步工具调用：一个新基准与数据合成配方

**英文标题**：Multi-Step Tool-Calling over Korean Open Public APIs: A Benchmark and a Data-Synthesis Recipe

**英文关键词**：KOPA-Bench; EDGE; multi-step tool-calling; Korean open public APIs; benchmark; data synthesis; GRPO; data-sovereignty

## 一句话结论

该论文提出 KOPA-Bench（Korean Open Public API Benchmark），用 145 个真实世界任务衡量开源大语言模型在韩国开放公共 API 上进行多步工具调用的能力；同时提出 EDGE（Execution-grounded Dynamic Graph for tool-calling data synthesis），一种以真实 API 执行结果为依据的数据合成方法。用 EDGE 生成数据并通过 GRPO 微调后，9B 模型几乎追平同系列未调优的 27B 模型，并在 KOPA-Bench 和 BFCL 基准上都有显著提升。

## 事件概述/研究问题

研究背景是：数据主权法规越来越多地要求公共机构部署开源、本地的 LLM 智能体，并让这些智能体在真实政府 API 上连续调用多个工具。然而，开源模型在“多步工具调用”场景下表现持续落后，且此前没有现成基准能衡量这一差距。

为此，论文做了两件事：

- 构建 KOPA-Bench，包含 145 个真实世界任务，覆盖韩国开放公共 API 上的多步工具调用。
- 提出 EDGE，一种由真实执行结果驱动数据合成的“执行锚定动态图”方法，用于生成可执行的多步工具调用轨迹。

## 方法/产品要点

- **KOPA-Bench**：一个新的评测基准，任务是真实世界场景下的多步工具调用，而不是单次 API 调用。
- **EDGE 的核心思路**：先构建工具调用关系图，表示“一个工具的输出可以作为另一个工具的输入”；随后只保留在真实 API 调用中验证成功的边；最后沿着这些经过执行验证的边，遍历生成可执行的多步轨迹。
- **训练策略**：使用 EDGE 生成的数据，以 GRPO 方式对模型进行微调，目标是提升开源模型的多步工具调用表现。

## 主要结果或产业意义

- 在未提供该评测之前，开源模型在多步工具调用上的差距无法被系统衡量。
- 使用 EDGE 生成数据并经过 GRPO 微调后，论文中的 9B 模型几乎接近同系列未调优的 27B 模型。
- 该模型不仅在 KOPA-Bench 上有显著提升，在 BFCL 基准上也表现出明显改善。
- 产业意义在于：在数据主权合规框架下，公共机构可能无法默认依赖外部云 API 或商业闭源模型，因此“本地开源模型 + 高质量多步工具调用训练数据”是一条值得关注的技术路线。

## 为什么重要

这篇论文同时提供了“问题度量工具”和“数据生成配方”：KOPA-Bench 让多步工具调用差距变得可见，EDGE 则试图降低构建高质量工具调用训练数据的成本。与单纯依赖人工标注或静态构造数据不同，EDGE 强调“真实执行验证”，这更贴近政府 API 环境中的实际可用性。

### 与既有脉络的关系

本条与已有卡片 VAKRA 的增量关系在于：VAKRA 面向企业级代理，强调跨 API 与文档检索的组合，并引入自然语言工具使用策略约束；本条则聚焦韩国开放公共 API，且明确提出“评测基准 + 执行锚定数据合成配方”的组合，重点不是策略约束，而是用真实 API 执行结果筛选可用工具链路并生成训练数据。

## 局限与不确定性

以下内容在 arXiv 摘要中未详细说明，需阅读论文原文后确认：

- KOPA-Bench 的具体任务类型、难度分布、评估指标和人工评测方法；待核实。
- 论文中提到的 9B 和 27B 模型具体属于哪个模型家族、基座模型是什么；待核实。
- “untuned 27B model”具体指“未经过该论文数据微调”还是“完全未做任何工具调用调优”；待核实。
- 9B 模型“nearly matches”27B 模型的量化差距是多少；待核实。
- EDGE 在图构建过程中访问真实 API 的成本、失败率和安全边界；待核实。
- BFCL 上的具体提升幅度和测试集范围；待核实。
- 数据主权法规与本地部署之间的具体政策约束并未在摘要中展开；待核实。

## 可用于图书/PPT/简报的角度

- 从“云端大模型调用”到“本地化开源智能体”：“数据主权”正在改变 AI 部署方式。
- 多步工具调用是公共 API 智能体的关键能力，但开源模型仍有明显短板。
- “先验证，再合成”：EDGE 用真实 API 执行结果过滤工具关系边，是一种可借鉴的数据合成思路。
- “小模型追赶大模型”：9B 模型经过针对性数据合成和训练后，几乎追平同系列 27B 模型，这对资源受限场景有意义。

## 原始材料

- 英文标题：Multi-Step Tool-Calling over Korean Open Public APIs: A Benchmark and a Data-Synthesis Recipe
- arXiv ID：2609.05395v1
- 作者：Dain Kim, Eungi Cho, Kyumin Kim, Shinyeong Noh, Kyuseong Lim
- 提交/更新日期：2026-09-04
- 原始来源：https://arxiv.org/abs/2609.05395v1
- PDF URL：https://arxiv.org/pdf/2609.05395v1

来源摘要：

> Data-sovereignty regulations increasingly require public institutions to deploy open-source, on-premise LLM agents that chain multiple tool-calls across live government APIs. However, open-source models consistently underperform in this multi-step setting, and no existing benchmark measures the gap. We introduce the Korean Open Public API Benchmark (KOPA-Bench), comprising 145 real-world tasks. To close this gap, we present EDGE, an Execution-grounded Dynamic Graph for tool-calling data synthEsis driven by live execution. EDGE builds a graph of how each tool's output can feed another's input, keeps only the links that succeed when actually called against the live APIs, and traverses these verified links to synthesize executable multi-step trajectories. Fine-tuned via GRPO on the resulting dataset, our 9B model nearly matches the untuned 27B model from the same family, improving substantially not only on KOPA-Bench but also on the BFCL benchmark.