---
book_potential: 3
collected_date: '2026-07-07'
confidence: 2
created_at: '2026-07-07T09:15:38+08:00'
date: '2026-07-07'
entities:
- artificialanalysis.ai
id: 2026-07-07-industry-benchmark-evaluation-artificial-analysis
importance: 4
industry_dimensions:
- company
keywords_en: &id001
- benchmark-evaluation
novelty: 3
ppt_potential: 4
primary_source: true
public_brief_potential: 3
review_status: rejected
source_type: benchmark-update
source_url: https://artificialanalysis.ai/
title_en: Artificial Analysis
title_zh: 人工智能模型与API提供商分析平台 (Artificial Analysis)
topics: *id001
track: industry
---

# 知识卡片：人工智能模型与API提供商分析平台 (Artificial Analysis)

## 一句话结论
Artificial Analysis 是一个独立分析 AI 模型与 API 托管提供商的平台，通过多项自有基准测试（如 Intelligence Index、AA-Briefcase、AA-Omniscience 等）帮助用户根据智能、速度、成本等维度选择最佳模型和提供商。

## 事件概述或研究问题
该平台旨在解决 AI 模型与 API 提供商缺乏统一、独立、可横向对比的性能指标的问题，提供涵盖质量、价格、输出速度、延迟等关键指标的基准数据，使用户能够针对自身场景做出有依据的选择。

## 方法/产品要点
- **独立评估**：平台自行运行多种基准测试，不依赖于第三方或厂商自报数据。
- **核心基准**：
  - **Artificial Analysis Intelligence Index v4.1**：综合 9 项评估，包括 GDPval-AA v2、τ³-Banking、Terminal-Bench v2.1、SciCode、Humanity's Last Exam、GPQA Diamond、CritPt、AA-Omniscience、AA-LCR。
  - **AA-Briefcase**：针对长期知识工作的前沿智能体评估，测试智能体能否产出电子表格、演示文稿、备忘录等真实业务交付物。
  - **AA-Omniscience**：知识和幻觉基准，奖励正确回答、惩罚幻觉，不惩罚拒绝作答。
  - **Coding Agent Index**：衡量编码智能体在端到端软件工程任务中的性能、成本与执行时间。
  - **Image & Video Leaderboards**：基于用户盲选偏好的 Elo 评分。
  - **Speech Leaderboards**：包含文本转语音、语音转文本、语音转语音等评估。
- **个性化推荐**：用户可根据对智能、速度、成本的优先级获取个性化模型推荐。
- **标签分类**：模型标注为开放权重 / 专有、推理 / 非推理、文本仅 / 多模态输入等，并可按国家筛选。

## 主要结果或产业意义
- 平台收录了 548 个模型（截至当前快照），其中 27 个模型在 Intelligence Index 排行榜中展示。
- 提供 **Intelligence vs. Cost per Task**、**Intelligence vs. Time per Task** 等对比图表，帮助权衡性能与成本。
- 展示前沿语言模型智能随时间变化的趋势，涵盖 Anthropic、OpenAI、Google、DeepSeek 等 14 家模型创建者。
- 开放权重模型（如 GLM-5.2）的表现也被纳入对比，体现了开源社区的进展。

## 为什么重要
- **独立性**：由第三方运营，降低厂商单方面宣称的偏差。
- **多维度**：不只看单项分数，而是组合智能、速度、成本、任务耗时等指标。
- **实用性**：提供个性化推荐和按任务类型（编码、客服、通用工作等）的智能体对比，直接可用于采购或部署决策。

## 局限与不确定性
- 待核实：平台未公布完整的测试集规模、重复性校验方法或样本大小。部分基准如 AA-Briefcase 的 Elo 分数区间可能受限于测试数量。
- 待核实：用户需自行评估基准与自己实际业务场景的匹配度；某些能力（如长上下文、多模态）仅部分覆盖。
- 待核实：平台的定价数据基于公布的 API 价格，实际部署成本和延迟可能因使用模式（缓存命中率、并发等）而异。

## 可用于图书/PPT/简报的角度
- **对比视角**：在介绍 AI 模型选型时引用该平台的 Intelligence Index 图表，展示主流模型的智能-成本帕累托边界。
- **基准更新趋势**：展示 Intelligence Index 从早期版本向 v4.1 的演变（从纯知识问答转向智能体任务），反映行业对 AI 评价重点的迁移。
- **开放 vs 专有模型**：利用平台的开放权重分类，对比开源模型（如 GLM-5.2）与闭源模型（如 Claude、GPT）的表现差距。

## 原始材料
- **英文标题**：AI Model & API Providers Analysis | Artificial Analysis
- **英文关键词**：benchmark, evaluation, AI model, API provider, independent analysis, leaderboard, intelligence index, agentic workload
- **原始来源**：https://artificialanalysis.ai/