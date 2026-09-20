---
auto_review_age_days: 1
auto_review_reasons:
- importance:4+8
- novelty:4+8
- confidence:3+6
- ppt_potential:4+4
- public_brief_potential:2+2
- topic_priority:5+10
- source_type:paper+2
- primary_source+2
- 'score>=28: 自动接受'
auto_review_score: 42
book_potential: 3
collected_date: '2026-07-30'
confidence: 3
created_at: '2026-07-30T18:09:34+08:00'
date: '2026-07-29'
entities:
- arxiv.org
id: 2026-07-29-academic-foundation-model-denseon-with-the-lateon-fully-open-dense-and-lat
importance: 4
keywords_en: &id001
- foundation-model
novelty: 4
ppt_potential: 4
primary_source: true
public_brief_potential: 2
review_status: accepted
reviewed_at: '2026-07-31T08:10:10+08:00'
reviewed_by: auto
source_type: paper
source_url: https://arxiv.org/abs/2607.27178v1
title_en: 'DenseOn with the LateOn: Fully Open Dense and Late-Interaction Models for
  Multilingual, Long-Context, and Code Search'
title_zh: DenseOn与LateOn：完全开放的多语言、长上下文与代码搜索密集及延迟交互模型
topics: *id001
track: academic
---

# 知识卡片：DenseOn与LateOn：完全开放的多语言、长上下文与代码搜索密集及延迟交互模型

- **一句话结论**：本文提出了一套完全开放的双编码器检索模型训练方案，并发现延迟交互模型在翻译-训练（translate-train）下能泛化到未见语言和文字系统，而密集模型仅限于翻译语言（待核实具体数字与对比实验设置）。
- **事件概述**：为弥合检索模型因依赖封闭训练数据而导致的复现性鸿沟，作者构建了665M英文对比预训练对（来自34个公开源共1.4B对）和1.88M监督微调对（含挖掘的难负例），训练出两个149M参数的模型：DenseOn（单向量密集模型）和LateOn（ColBERT风格延迟交互模型）。它们在BEIR上分别达到56.20和57.22平均nDCG@10，刷新了该参数量级的最优结果。随后将验证过的英文数据翻译为八种语言，生成2.8B对跨语言样本，基于mmBERT-base训练了307M参数的mDenseOn和mLateOn。尽管共享骨干、数据和目标，两者的表示行为差异显著：密集模型在英语和翻译语言上强，但在翻译-训练支持范围外退化；延迟交互模型对未见语言和文字系统泛化更好。这表明token级匹配将翻译-训练从目标语言扩展策略转变为多语言泛化策略。所有模型、数据集和训练代码均已开源。
- **方法/产品要点**：
    - 数据构建：从34个公开源筛选1.4B对→665M对比预训练对；1.88M监督微调对（含挖掘难负例）。
    - 模型规模：DenseOn/LateOn为149M参数（待核实具体架构细节）；mDenseOn/mLateOn为307M参数（基于mmBERT-base）。
    - 训练策略：先英文→后翻译-训练（translate-train）扩展到八种语言。
    - 关键发现：密集模型依赖翻译语言对，延迟交互模型因token级匹配实现跨文字系统泛化。
- **主要结果或产业意义**：在BEIR上达到该参数量级新SOTA（nDCG@10 56.20/57.22）；展示了开放训练配方可复现，并揭示了不同检索架构对多语言泛化的迥异影响。对于构建多语言搜索系统、代码搜索等场景具有指导价值。
- **为什么重要**：该工作提供了完全开放、可复现的检索模型训练流程，有助于推动学术研究对比与工业落地。其发现（延迟交互优于密集模型在翻译-训练外的泛化）为多语言检索架构选择提供了新视角。与既有相关卡片的区别：本文聚焦检索模型而非长程智能体、状态空间模型或扩散模型，属于基础模型社区的重要补充。
- **局限与不确定性**：模型规模局限于149M/307M，更大参数量下的行为待验证；翻译-训练仅覆盖八种语言，对不同语系的表现需进一步评估；具体超参数、训练细节及硬件需求待核实（因无法抓取全文）。
- **可用于图书/PPT/简报的角度**：
    - 开放科学：如何构建完全开放的训练数据与模型以避免闭源垄断。
    - 翻译-训练 vs. 多语言泛化：密集与延迟交互模型的行为对比图解。
    - 小参数模型SOTA：149M模型在BEIR上达到56+ nDCG@10的意义。
- **原始材料**：
    - URL: https://arxiv.org/abs/2607.27178v1
    - 英文标题：DenseOn with the LateOn: Fully Open Dense and Late-Interaction Models for Multilingual, Long-Context, and Code Search
    - 英文关键词：foundation-model, retrieval, multilingual, translate-train, open-source