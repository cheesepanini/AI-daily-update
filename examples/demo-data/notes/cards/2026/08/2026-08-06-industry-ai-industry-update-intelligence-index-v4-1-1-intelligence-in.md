---
auto_review_age_days: 1
auto_review_reasons:
- importance:3+6
- novelty:3+6
- confidence:3+6
- ppt_potential:3+3
- public_brief_potential:2+2
- topic_priority:5+10
- source_type:benchmark-update+2
- primary_source+2
- 'score>=28: 自动接受'
auto_review_score: 37
book_potential: 2
collected_date: '2026-08-07'
confidence: 3
created_at: '2026-08-07T08:17:20+08:00'
date: '2026-08-06'
entities:
- artificialanalysis.ai
event_date: '2026-08-06'
id: 2026-08-06-industry-ai-industry-update-intelligence-index-v4-1-1-intelligence-in
importance: 3
industry_dimensions:
- company
keywords_en: &id001
- ai-industry
novelty: 3
ppt_potential: 3
primary_source: true
public_brief_potential: 2
review_status: accepted
reviewed_at: '2026-08-08T08:26:15+08:00'
reviewed_by: auto
source_type: benchmark-update
source_url: https://artificialanalysis.ai/articles/artificial-analysis-intelligence-index-v4-1-1
title_en: "Update Intelligence Index v4.1.1 Intelligence Index v4.1.1 moves \U0001D70F³-Banking
  to v1.0.1 and upgrades the grader for HLE, AA-LCR, and AA-Omniscience to GPT-5.6
  Luna (medium)"
title_zh: Artificial Analysis 发布智能指数 v4.1.1
topics: *id001
track: industry
---

# 知识卡片：Artificial Analysis 发布智能指数 v4.1.1

## 一句话结论
Artificial Analysis 于 2026 年 8 月 6 日发布 Intelligence Index v4.1.1，升级了评测模型并引入 𝜏³-Banking v1.0.1，整体模型排名基本不变，Claude Opus 5 仍以 63 分位居第一。

## 事件概述
Artificial Analysis 宣布将 Artificial Analysis Intelligence Index 更新至 v4.1.1。这是一个小幅补丁版本，目的是在保持现有评测体系连续性的前提下，提高评分可靠性和与人类判断的一致性。所有公开模型结果已切换至 v4.1.1 口径。

## 方法/产品要点
- **𝜏³-Banking 升级**：采用 Sierra 发布的 v1.0.1 版本，更新了上游任务版本，并改进了 grader 流程，修复了从“不愉快路径”恢复的轨迹中存在的正确性错误。
- **Grader 模型统一升级**：HLE、AA-LCR、AA-Omniscience 三项评测的评分模型分别从 GPT-4o、Qwen3 235B A22B 2507、Gemini 3 Flash Preview，统一更换为 GPT-5.6 Luna (medium)。该模型在 grader 验证中与人类判断的一致性更强。
- **评分影响较小**：多数模型在 Intelligence Index 上的分数变动小于 1 分；最大增幅来自 Muse Spark 1.2 (xhigh)，上升 2.7 分。领先榜头部模型保持不变。

## 主要结果或产业意义
- Claude Opus 5 继续位列第一，Intelligence Index 为 63。
- 本次更新更侧重于评测可靠性而非排名洗牌，说明在当前头部模型竞争中，评分方法论的稳健性对开发者选择模型具有实际影响。
- Artificial Analysis 强调其作为独立评测方的角色，持续迭代评测方法以反映最新模型能力。

## 为什么重要
该更新是 Artificial Analysis 对评测基础设施的持续维护，体现了第三方基准在快速变化的 AI 产业中“校准尺子”的价值。与已有相关卡片相比，本条增量在于：随着 GPT-5.6 Luna 在 ChatGPT 中扩大免费访问（见 2026-08-06 卡片），它同时开始被第三方评测机构用作更可靠的评分模型，显示出前沿模型的双重角色——既是产品，也是评测基础设施的一部分。

## 局限与不确定性
- 材料仅提供摘要性说明，未披露 GPT-5.6 Luna 作为 grader 的详细验证数据和具体一致性指标，待核实。
- “𝜏³-Banking v1.0.1”的具体任务变更内容未展开，待核实。
- 分数变动的具体模型列表未完全公开，仅提及 Muse Spark 1.2 的增幅，其他模型的具体变化待核实。
- 关于 Claude Opus 5 的 63 分是否与 v4.1.0 完全可比，材料未给出直接对比，待核实。

## 可用于图书/PPT/简报的角度
- 第三方 AI 评测机构如何保持“尺子”的准确性？以 Intelligence Index v4.1.1 的 grader 升级为例。
- 从 GPT-4o 到 GPT-5.6 Luna：评测模型迭代如何影响排行榜分数，但又不改变头部格局？
- AI 模型的双重身份：既是被测对象，又是评测工具——对产业标准化的启示。

## 原始材料
- 英文标题：Launching v4.1.1 of the Artificial Analysis Intelligence Index
- 英文关键词：Artificial Analysis, Intelligence Index, v4.1.1, GPT-5.6 Luna, 𝜏³-Banking, Claude Opus 5, benchmark
- 来源：Artificial Analysis（2026年8月6日），URL: https://artificialanalysis.ai/articles/artificial-analysis-intelligence-index-v4-1-1