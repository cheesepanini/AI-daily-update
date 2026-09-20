---
auto_review_age_days: 1
auto_review_reasons:
- importance:4+8
- novelty:4+8
- confidence:3+6
- ppt_potential:4+4
- public_brief_potential:3+3
- topic_priority:5+10
- source_type:paper+2
- primary_source+2
- 'score>=28: 自动接受'
auto_review_score: 43
book_potential: 3
collected_date: '2026-08-21'
confidence: 3
created_at: '2026-08-21T18:12:47+08:00'
date: '2026-08-20'
duplicate_suspect:
  date: '2026-07-17'
  source_url: https://arxiv.org/abs/2607.16165v1
  title: 主动观察者测试：多模态大语言模型缺乏主动视觉感知能力
entities:
- arxiv.org
id: 2026-08-20-academic-foundation-model-an-agentic-approach-for-active-data-collection-t
importance: 4
keywords_en: &id001
- foundation-model
novelty: 4
ppt_potential: 4
primary_source: true
public_brief_potential: 3
review_status: accepted
reviewed_at: '2026-08-22T08:19:18+08:00'
reviewed_by: auto
source_type: paper
source_url: https://arxiv.org/abs/2608.20320v1
title_en: An Agentic Approach for Active Data Collection, Travel Behavior Modeling,
  and Weather-Sensitive Demand Prediction
title_zh: 智能体驱动的主动数据收集、出行行为建模与天气敏感需求预测
topics: *id001
track: academic
---

# 知识卡片：智能体驱动的主动数据收集、出行行为建模与天气敏感需求预测

**英文标题**：An Agentic Approach for Active Data Collection, Travel Behavior Modeling, and Weather-Sensitive Demand Prediction

**英文关键词**：Agentic Approach; Active Data Collection; Travel Behavior Modeling; Weather-Sensitive Demand Prediction; Large Language Models

## 一句话结论

本研究提出并展示了一个可审计的三智能体工作流，将对话式出行调查、结构化数据处理和天气敏感的出行行为预测串在一起。在五分类出行方式预测上，最佳纯文本零样本 LLM 达到 69.9%，使用与受访者相同的天气图像后，最佳视觉配置达到 71.5%，高于随机森林基准的 69.6%。

## 事件概述或研究问题

出行行为研究越来越常把数字数据收集与预测建模结合起来，但这些环节通常被分开开发和评估。本文针对这一割裂，提出一个整合对话式数据收集、结构化数据处理和行为预测的多智能体工作流。摘要中的预测任务聚焦于学生通勤者在不同天气场景下的出行方式选择。

## 方法/产品要点

- 提出三智能体工作流：对话式数据收集（conversational data collection）、结构化数据处理（structured data processing）、行为预测（behavioral prediction），并强调流程可审计。
- 数据收集使用聊天机器人实施的、加入天气图像的陈述偏好调查（image-augmented stated-preference survey），覆盖五个预定义天气场景，得到 454 条“受访者-场景”观测。
- 天气关联分析使用多项 Logit 模型（multinomial logit model）；预测基准包括逻辑回归和随机森林。
- 本地部署 9 个大语言模型，参数规模从 20 亿到 350 亿，在四种零样本提示与上下文条件下评估，并扩展到角色设定（persona）、少样本提示（few-shot）和基于视觉的配置。
- 视觉配置使用与受访者相同的天气图像，测试多模态 LLM 的预测表现。

## 主要结果或产业意义

- 随机森林达到 69.6% 的五分类准确率；最佳纯文本零样本 LLM 达到 69.9%，无需任务特定拟合。
- 最佳基于天气图像的视觉配置达到 71.5% 的五分类准确率，提示视觉上下文可能为部分模型提供额外预测信息。
- 习惯性出行信息带来的性能提升最一致；专家式提示框架总体优于角色扮演式提示；当缺少习惯性出行信息时，角色设定信息最有帮助。
- 少样本提示能改进多个模型的预测，且收益在少量示例后趋于稳定。
- 从摘要看，其主要贡献是流程与方法层面的；具体产业落地效果、运营成本和可扩展性尚待核实。

## 为什么重要

这项研究的意义不只是比较模型准确率，而是把“数据收集”和“预测建模”纳入同一个可审计的智能体流程。它展示了对话式调查、传统行为模型、机器学习和多模态 LLM 预测能够在多大程度上被协调和比较，而不是彼此割裂。

### 与既有脉络的关系

本条与已有相关卡片同属基础模型（foundation-model）应用脉络，但将场景转向交通出行行为。增量信息在于：LLM 不仅被用于预测，还被用于“主动数据收集/对话式调查”环节，并与传统行为模型、机器学习基准放在同一个可审计流程中比较。

## 局限与不确定性

- 样本为学生通勤者，且天气场景为预定义的五类；对其他人群、真实天气变化和更大区域的可推广性待核实。
- 摘要未说明逻辑回归的具体表现，也未说明各模型之间的差异是否具有统计显著性，待核实。
- 未列出具体 LLM 名称、提示词措辞、智能体分工细节、少样本示例数量等，待核实。
- “五分类”对应的具体出行方式类别未在摘要中列出，待核实。
- 标题中的“天气敏感需求预测”与摘要中的“出行方式选择预测”之间的具体对应关系未在摘要中展开，待核实。
- 视觉配置的 71.5% 是最佳结果，并不意味着所有模型在使用图像后都一致提升，逐模型结果待核实。

## 可用于图书/PPT/简报的角度

- 用“天气如何改变出行方式选择？”作为引入，引出 LLM 智能体辅助出行调查的新方式。
- 画一张流程示意图：聊天机器人调查 → 结构化数据 → 传统行为模型/机器学习/LLM 预测 → 多模态视觉输入。
- 用准确率对比条形图呈现 69.6%、69.9%、71.5% 三个数字，说明零样本 LLM 和多模态 LLM 与机器学习基准相当或略优。
- 讨论“本地小模型（2B–35B）+ 零样本/少样本提示”在行为预测中的可行性。
- 强调可审计的多智能体工作流，而不是只把 LLM 当作黑箱打分器。

## 原始材料

- 英文标题：An Agentic Approach for Active Data Collection, Travel Behavior Modeling, and Weather-Sensitive Demand Prediction
- arXiv ID：2608.20320v1
- 作者：Narges Ahmadi, Yubo Jiao, Jônatas Augusto Manzolli, Jiangbo Yu, Luis Miranda-Moreno
- 发表/更新时间：2026-08-20T17:57:42Z
- 分类：cs.AI；cs.CL
- URL：https://arxiv.org/abs/2608.20320v1
- PDF：https://arxiv.org/pdf/2608.20320v1