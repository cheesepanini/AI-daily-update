---
book_potential: 4
collected_date: '2026-07-29'
confidence: 3
created_at: '2026-07-29T08:13:33+08:00'
date: '2026-07-27'
entities:
- arxiv.org
event_date: '2026-07-27'
id: 2026-07-27-academic-foundation-model-evaluating-the-impact-of-explainable-ai-on-trust
importance: 4
keywords_en: &id001
- foundation-model
novelty: 4
ppt_potential: 5
primary_source: true
public_brief_potential: 3
review_status: needs-review
source_type: paper
source_url: https://arxiv.org/abs/2607.24601v1
title_en: Evaluating the Impact of Explainable AI on Trust in AI-Assisted Code Review
title_zh: 评估可解释人工智能对 AI 辅助代码审查中信任的影响
topics: *id001
track: academic
---

# 知识卡片：评估可解释人工智能对 AI 辅助代码审查中信任的影响

**一句话结论**：在 AI 辅助代码审查中，提供详细解释会提升开发者对 AI 的感知信任（满分 5 分中达到 3.99），但并未带来最高的代码评审意见采纳率；反而是仅提供评审反馈（无额外解释）的中等解释条件获得了最高的意见同意率（89.22%），表明详尽解释可能促使开发者更频繁地质疑 AI 推荐。

**事件概述或研究问题**：大语言模型（LLM）越来越多地被用于自动化代码审查，但其决策过程难以理解，开发者难以评估 LLM 生成审查意见的有效性，从而难以确定对 AI 的信任程度。可解释 AI（XAI）在代码审查中的作用及其对信任的影响尚缺乏深入研究。本研究旨在探究 XAI 如何影响开发者对 AI 辅助代码审查的信任。

**方法/产品要点**：
- 采用被试内设计，34 名参与者。
- 比较三种不同 XAI 支持水平的 LLM 代码审查系统：
  - 条件 A：提供详细解释和审查反馈；
  - 条件 B：仅提供审查反馈（无解释）；
  - 条件 C：不提供任何解释或反馈（仅由参与者自行评审）。
- 参与者对真实世界的代码变更请求进行审查，同时呈现 AI 生成的审查意见。
- 测量指标：信任感知、与 AI 推荐的一致性（同意率）、决策理由、所用时间。

**主要结果或产业意义**：
- 解释水平显著影响信任和同意率，但方向不同：
  - 条件 A（完全解释）的感知信任最高（均值 M = 3.99/5）；
  - 条件 B（中等解释）的同意率最高（89.22%）；
  - 条件 C（无解释）在信任和同意率上均为最低。
- 这表明更多的解释可能促使开发者更频繁地质疑 AI 推荐。
- 解释水平未显著影响审查时间。
- 决策时最常引用的理由是代码可读性和正确性。
- 结果可为设计可信的 AI 代码审查系统提供依据，并对 AI 辅助软件开发中的人因研究有参考价值。

**为什么重要**：本研究首次通过受控实验量化了不同 XAI 支持水平对开发者信任与行为的一致影响，揭示了“信任高 ≠ 采纳高”的非直观关系，为平衡模型透明度和用户接受度提供了实证数据。

**局限与不确定性**：
- 样本量较小（34 人），可能不足以推广至所有开发者群体。
- 实验为受控环境，真实工作场景中时间压力、团队协作等因素未纳入。
- 解释内容的具体设计（详细程度、内容质量）未作进一步细分，不同解释类型的影响可能不同。
- 未测量长期信任变化或学习效应。

**可用于图书/PPT/简报的角度**：
- 示例图表：以柱状图对比三种条件下信任评分（3.99 vs. 待核实 vs. 待核实）和同意率（待核实 vs. 89.22% vs. 待核实）。
- 关键论点：AI 解释并非越多越好——设计 XAI 时需权衡解释的详尽程度与用户批判性思维之间的关系。
- 产业启示：代码审查工具可提供“仅反馈”默认模式，并允许用户按需展开详细解释，以兼顾效率与信任。

**与既有脉络的关系**：已有相关卡片均聚焦于其他领域（具身推理、非人类语言评估、概念可解释性审计），本条卡片填补了 XAI 在代码审查人机信任中的实证研究空白，补充了“解释水平如何影响实际采纳行为”的量化证据。

**英文标题**：Evaluating the Impact of Explainable AI on Trust in AI-Assisted Code Review  
**英文关键词**：Explainable AI, code review, trust, large language models, user study  

**原始材料**：
- 标题：Evaluating the Impact of Explainable AI on Trust in AI-Assisted Code Review
- 作者：Zhenhan Gao, Marvin Muñoz Barón, Umm-e Habiba, Daniel Graziotin, Stefan Wagner
- 发布/更新日期：2026-07-27
- arXiv ID：2607.24601v1
- URL：https://arxiv.org/abs/2607.24601v1