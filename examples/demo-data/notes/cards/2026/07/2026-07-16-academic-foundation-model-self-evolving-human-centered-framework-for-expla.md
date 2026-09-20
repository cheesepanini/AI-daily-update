---
book_potential: 4
collected_date: '2026-07-18'
confidence: 4
created_at: '2026-07-18T08:11:11+08:00'
date: '2026-07-16'
entities:
- arxiv.org
id: 2026-07-16-academic-foundation-model-self-evolving-human-centered-framework-for-expla
importance: 4
keywords_en: &id001
- foundation-model
novelty: 3
ppt_potential: 4
primary_source: true
public_brief_potential: 3
review_status: accepted
source_type: paper
source_url: https://arxiv.org/abs/2607.15202v1
title_en: Self-Evolving Human-Centered Framework for Explainable Depression Symptom
  Annotation
title_zh: 自进化人本框架用于可解释抑郁症症状标注
topics: *id001
track: academic
---

# 知识卡片：自进化人本框架用于可解释抑郁症症状标注

**一句话结论**  
本研究提出了一种结合大语言模型（LLM）与专家审核的自进化标注框架，旨在为抑郁症相关数据集提供结构化、可追溯、符合DSM-5-TR标准的症状级证据和标签生成，在初步研究中提升了标注一致性与可解释性并减少了人工修改工作量。

**事件概述或研究问题**  
在心理健康可解释人工智能（XAI）研究中，标注质量是主要瓶颈。现有抑郁症数据集的标签常缺乏结构化证据、症状级论证或与DSM-5-TR标准的可追溯对齐，限制了透明度和下游模型的可解释性。该工作试图解决：如何利用LLM辅助并融入专家反馈，构建自进化、可审计的标注流程。

**方法/产品要点**  
- **框架名称**：Self-Evolving Human-Centered Framework for Explainable Depression Symptom Annotation（自进化人本可解释抑郁症症状标注框架）。  
- **目标**：为重度抑郁症（MDD）构建可解释、对齐DSM-5-TR的数据集（非临床诊断工具）。  
- **三阶段流程**：  
  1. 候选证据选择：从文本记录（如临床笔记）中提取相关语句。  
  2. 标准级DSM-5-TR分析：将证据映射到DSM-5-TR的具体诊断标准。  
  3. 案例级综合：生成标签级别的诊断和严重程度注释。  
- **双记忆架构**：由“示例记忆”（Example Memory）和“反思记忆”（Reflection Memory）组成，可在不重新训练模型的情况下内化专家反馈，迭代改进后续标注。  
- **输出内容**：除最终标签外，还导出临床证据、推理轨迹和编辑历史，支持全面审计。

**主要结果或产业意义**  
- 在专家评审样本的初步研究中，该框架提高了标注一致性和可解释性，同时减少了人工修改工作量。  
- 意义在于：为心理健康领域AI模型提供高质量、可追溯的标注数据，推动可解释抑郁症检测系统的落地。  
- 产业层面：可应用于电子健康记录（EHR）标注、临床决策支持系统训练数据构建等场景。

**为什么重要**  
- 填补了抑郁症标注过程中结构化证据缺失的空白，使标注过程可审计、可复现。  
- 自进化设计通过记忆机制实现持续改进，无需频繁重新训练，降低了工程成本。  
- 与已有相关卡片（如HealthClaw自进化智能体）相比，本工作聚焦于**医学标注**这一特定领域，且强调与DSM-5-TR诊断标准的严格对齐，而HealthClaw关注的是通用健康管理智能体的隐私与上下文管理。

**局限与不确定性**  
- 多轮反馈循环的评估被列为未来工作，当前仅报告了单轮初始效果。  
- 框架目前只针对重度抑郁症（MDD），对其他精神障碍的泛化能力待验证。  
- 依赖专家在环，可能引入人力成本和时间开销；专家数量与资质的具体要求未明确。  
- 初步研究的样本规模和详细性能指标（如准确率、F1等）未在摘要中提供，需查阅全文确认。

**可用于图书/PPT/简报的角度**  
- **角度A**：如何利用LLM+专家协作构建高可靠性医学标注数据集——以抑郁症为例。  
- **角度B**：可解释AI在精神健康领域的落地挑战与自进化框架的解决思路。  
- **角度C**：双记忆架构在无需重训练情况下的持续学习优势（对比传统微调方法）。  
- **角度D**：审计追踪（reasoning trace + edit history）对AI临床系统信任度的影响。

**与既有脉络的关系**  
- 本文是对“可解释AI在心理健康标注中的应用”的延续，与已有卡片“可解释性需求工程实践评估”不同，后者聚焦需求工程阶段，本文聚焦具体领域的数据标注方法。  
- 与“HealthClaw”共享“自进化”概念，但HealthClaw面向个人健康管理智能体的隐私与记忆，本文面向专家协助下的医学标注，二者技术细节与评估场景不同。

**原始材料**  
- **英文标题**：Self-Evolving Human-Centered Framework for Explainable Depression Symptom Annotation  
- **arXiv ID**：2607.15202v1  
- **URL**：https://arxiv.org/abs/2607.15202v1  
- **PDF**：https://arxiv.org/pdf/2607.15202v1  
- **关键词**：Explainable AI, Depression Symptom Annotation, DSM-5-TR, Large Language Model, Self-Evolving Framework, Expert-in-the-Loop, Annotation Auditability