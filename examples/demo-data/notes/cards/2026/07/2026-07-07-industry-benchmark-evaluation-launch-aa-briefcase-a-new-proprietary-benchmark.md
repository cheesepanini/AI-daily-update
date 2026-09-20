---
book_potential: 4
collected_date: '2026-07-07'
confidence: 4
created_at: '2026-07-07T09:16:14+08:00'
date: '2026-07-07'
entities:
- artificialanalysis.ai
id: 2026-07-07-industry-benchmark-evaluation-launch-aa-briefcase-a-new-proprietary-benchmark
importance: 5
industry_dimensions:
- company
keywords_en: &id001
- benchmark-evaluation
novelty: 5
ppt_potential: 5
primary_source: true
public_brief_potential: 4
review_status: accepted
source_type: benchmark-update
source_url: https://artificialanalysis.ai/articles/aa-briefcase
title_en: Launch AA-Briefcase A new proprietary benchmark for long-horizon knowledge
  work
title_zh: AA-Briefcase：前沿知识工作评估基准
topics: *id001
track: industry
---

# 知识卡片：AA-Briefcase：前沿知识工作评估基准

## 一句话结论
AA-Briefcase 是由 Artificial Analysis 发布的前沿知识工作基准测试，通过在模拟多周真实项目场景中评估 AI 模型的代理能力，揭示了当前顶级模型在长周期、碎片化上下文知识任务中的表现、成本与缺陷。

## 事件概述
2026 年 6 月 18 日，Artificial Analysis 宣布推出 AA-Briefcase，这是一个用于测试 AI 模型在复杂、长期知识工作项目中表现的新基准。该基准由来自 Google、麦肯锡、波士顿咨询集团等机构的行业专家耗时数月构建，包含 4 个多周项目场景、91 个私有任务，以及近 2000 个源文件（包括超过 3500 封邮件和 2.5 万条 Slack 消息）。模型需要在碎片化、自相矛盾的上下文中完成诸如财务模型、董事会报告、设计原型等实际交付物。

## 方法/产品要点
- **评估框架**：AA-Briefcase 结合三种评分方式：
  - **二元规则检查（Rubric）**：逐项检查任务是否正确完成（事实正确性）。
  - **分析质量成对评分**：比较两个模型输出，评出更全面、严谨、有证据支撑的答案。
  - **呈现质量成对评分**：比较输出在专业呈现上的优劣。
- **任务结构**：每个任务对应一个多周项目中的某周，模型独立运行（不延续之前提交），但共享项目背景文件和上下文。
- **成本差异**：不同模型完成一个任务的平均成本差异超过 800 倍（Claude Fable 5 约 $31，DeepSeek V4 Flash 约 $0.04）。
- **数据私密性**：除一个公开演示场景外，所有任务指令、输入文件和评分细则均为私有。

## 主要结果
- **整体冠军**：Claude Fable 5 取得最高 AA-Briefcase Elo（综合规则通过率、分析质量和呈现质量）。Claude Opus 4.8 (max) 和 GLM-5.2 (max) 紧随其后，GLM-5.2 在开放权重模型中领先，且成本仅为 Claude Opus 4.8 的 25%。
- **规则通过率极低**：Claude Fable 5 仅在 3% 的任务中完全通过所有规则检查；在 91 个任务中，有 31 个任务没有任何模型得分超过 50%。
- **故障模式差异**：低能力模型主要失败于任务执行（遗漏文件、无交付物）；高能力模型主要失败于未能满足所有任务要求（遗漏隐藏需求、分析错误、格式问题）。
- **文件数量与难度**：所需外部文件越多，模型通过率越低；顶级模型降幅较小，但仍有明显衰退。
- **视觉检查与呈现质量**：在呈现质量上领先的模型（Claude Fable 5、Claude Opus 4.8）平均每个任务进行 21 次和 12 次视觉检查，而低分模型几乎不检查。

## 为什么重要
AA-Briefcase 填补了现有基准测试的空白：它不再使用孤立、简单的提示，而是模拟现实中长达数周、涉及大量碎片化上下文和矛盾信息的知识工作。通过同时评估事实正确性、分析深度和呈现专业性，它暴露了模型“表面好看但实质错误”的常见问题，为评估 AI 代理的实际工作能力提供了更完整的视角。

## 局限与不确定性
- **任务私有性**：91 个任务均未公开，仅有一个演示场景，外部研究者无法完全复现或验证结果。
- **独立运行限制**：模型在每个任务中独立运行，不携带之前的输出，这与真实工作中持续迭代的流程不同。
- **成本高昂**：前沿模型单任务成本超过 $31，可能限制大规模测试的普及性。
- **模型时效性**：数据截至 2026 年 6 月 18 日，后续模型版本可能改变排名。
- **无法确认细节**：关于任务场景的具体行业领域、评分细则权重以及“GLM-5.2”等模型的具体架构信息，本文材料未详细说明，需待核实。

## 可用于图书/PPT/简报的角度
- 主题演讲：“AI 代理在知识工作中的真实能力——AA-Briefcase 的启示”
- 行业分析报告：长周期 AI 代理评估基准的设计原则与现有瓶颈
- 产品对比：从“死记硬背”到“真正干活”——AA-Briefcase 如何区分模型的实际工作能力
- 成本与性能权衡图：展示不同模型的 Elo 分数与单任务成本，突出 GLM-5.2 等性价比之选

## 原始材料
- **英文标题**：Announcing AA-Briefcase: a frontier knowledge work evaluation
- **英文关键词**：benchmark-evaluation, AI agent evaluation, knowledge work
- **来源 URL**：https://artificialanalysis.ai/articles/aa-briefcase