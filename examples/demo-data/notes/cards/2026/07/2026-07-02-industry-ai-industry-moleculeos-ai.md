---
auto_review_age_days: 1
auto_review_reasons:
- topic_priority:5+10
- source_type:chinese-media-2
- primary_source+2
- 'score<=22: 自动拒绝'
auto_review_score: 10
book_potential: 0
collected_date: '2026-07-11'
confidence: 0
created_at: '2026-07-11T18:03:08+08:00'
date: '2026-07-02'
entities:
- aiera.com.cn
event_date: '2026-07-02'
id: 2026-07-02-industry-ai-industry-moleculeos-ai
importance: 0
industry_dimensions:
- company
keywords_en: &id001
- ai-industry
novelty: 0
ppt_potential: 0
primary_source: true
public_brief_potential: 0
review_status: rejected
reviewed_at: '2026-07-12T08:08:29+08:00'
reviewed_by: auto
source_type: chinese-media
source_url: https://aiera.com.cn/2026/07/10/other/admin/103421/%e5%88%86%e5%ad%90%e4%b9%8b%e5%bf%83moleculeos%e5%bc%80%e6%94%be%e6%b5%8b%e8%af%95%ef%bc%8c%e6%8e%a8%e5%8a%a8ai%e7%94%9f%e7%89%a9%e7%bb%8f%e6%b5%8e%e5%9f%ba%e7%a1%80%e8%ae%be%e6%96%bd%e8%90%bd
title_en: 分子之心MoleculeOS开放测试，推动AI生物经济基础设施落地
title_zh: 分子之心MoleculeOS开放测试，推动AI生物经济基础设施落地
topics: *id001
track: industry
---

# 知识卡片：分子之心MoleculeOS开放测试，推动AI生物经济基础设施落地

**一句话结论**  
MoleculeOS 是一个面向生物研发的 AI 原生操作系统，通过将研发意图作为入口，自动拆解任务、调度模型并沉淀可追踪的研发链路，旨在把 AI 生物研发从“工具时代”推向“操作系统时代”。

**事件概述**  
- 2026 年 7 月 2 日，在 2026 上海国投前沿论坛上，分子之心创始人许锦波教授正式面向产业界开放自研的 AI 原生生物经济操作系统 MoleculeOS（MOS）。  
- MoleculeOS 的开放意味着生物领域的研发基础设施被重新定义：AI 角色从生物规律的“预测者”变为研发流程的“组织者”。  
- 试用入口：https://mos.moleculemind.com/login

**方法/产品要点**  
- 核心变化：以“研发意图”作为系统入口。研究人员只需提出目标（如提升抗体亲和力、针对特定靶点生成候选分子），系统自动拆解任务、调度模型（序列建模、结构预测、结合界面判断、突变设计、亲和力评估、稳定性评估、可开发性分析等），并给出决策建议。  
- 每一次研发链路会被自动沉淀为结构化研发资产（可追踪、可复盘、可复用），支持后续项目调用历史参数和逻辑。  
- 底层模型体系：围绕“序列—结构—功能—进化—相互作用—生成设计”构建，包括：  
  - 多模态蛋白质基础大模型 NewOrigin（达尔文）  
  - 全原子大分子复合物结构预测模型 MMFold  
  - 面向纳米抗体、酶和功能蛋白的生成式设计模型 MMDesign  
- 技术指标（来自材料中提供的测试数据）：  
  - MMFold 在 FoldBench 基准测试中针对 172 个抗体–抗原界面实现 68.6% 预测成功率，相较 AlphaFold3 等国际主流模型显著领先。  
  - 抗体从头设计平台在 12 个靶点中，每个靶点仅测试不超过 50 个候选分子，靶点成功率超过 90%。

**主要结果或产业意义**  
- 在一个免疫检查点抗体优化项目中，传统需多名研究人员跨工具协作、耗时数周的工作，在 MoleculeOS 中可压缩至数小时。  
- 完成计算后，项目结果可一键分享至湿实验团队，包含完整计算链路与可视化分析，减少二次转述。  
- 该系统的开放有望推动创新药、生物制造、合成生物学等领域的团队低门槛获得系统能力，推动 AI 生物经济基础设施规模化落地。

**为什么重要**  
- AI 生物研发正从“工具智能”转向“系统智能”：过去模型突破不等于研发效率跃迁，主要瓶颈在于“工具栈+人工调度”模式。MoleculeOS 将研发体系标准化、协同化、可扩展化，使 AI 从“单步计算工具”升级为“完整研发流程的组织者”。  
- 研发不再是从零开始的重复劳动，而是在持续积累的体系中加速，这对整个生物产业的研发范式具有标志性意义。

**局限与不确定性**  
- 材料中未提及 MoleculeOS 在真实产业场景中大规模部署后的具体时间节约量化数据（如平均缩短天数）及成本降低比例。  
- 抗体从头设计平台的高成功率（90%）是在极低通量（≤50 个候选分子）条件下取得，实际更大规模或更复杂靶点下的表现待进一步验证。  
- 与现有主流商业或开源生物信息学工具（如 Schrödinger、Rosetta 等）的具体对比数据未在材料中提供。  
- 材料未说明系统对不同类型生物分子（如小分子、核酸等）的支持情况。  
- 开放测试后的实际用户反馈和系统稳定性信息尚待披露。

**可用于图书/PPT/简报的角度**  
1. **范式转变**：从“筛选试错”到“分子创造”——AI 操作系统如何重塑生物研发流程。  
2. **技术突破**：自研模型 MMFold 在抗体–抗原结构预测上的显著领先（68.6% vs 国际主流）。  
3. **产业落地**：低门槛操作系统如何降低创新药和生物制造的门槛，加速候选分子发现。  
4. **人物故事**：许锦波教授（2016 年提出 RaptorX-Contact 方法，深度学习提升蛋白质结构预测的开创者）创立分子之心，推动系统级 AI 基础设施。  
5. **关键词联想**：AI 生物经济、蛋白质基础大模型、抗体设计、合成生物学、研发资产沉淀。

**原始材料**  
- 来源：新智元（AIERA）报道《分子之心MoleculeOS开放测试，推动AI生物经济基础设施落地》  
- URL：https://aiera.com.cn/2026/07/10/other/admin/103421/%e5%88%86%e5%ad%90%e4%b9%8b%e5%bf%83moleculeos%e5%bc%80%e6%94%be%e6%b5%8b%e8%af%95%ef%bc%8c%e6%8e%a8%e5%8a%a8ai%e7%94%9f%e7%89%a9%e7%bb%8f%e6%b5%8e%e5%9f%ba%e7%a1%80%e8%ae%be%e6%96%bd%e8%90%bd  
- 英文标题：分子之心MoleculeOS开放测试，推动AI生物经济基础设施落地（原文无独立英文标题，此处保留中文原标题）  
- 英文关键词：AI Industry, MoleculeOS, AI Biotech, Protein Design, Operating System