---
auto_review_age_days: 1
auto_review_reasons:
- importance:3+6
- novelty:3+6
- confidence:2+4
- ppt_potential:3+3
- public_brief_potential:3+3
- topic_priority:5+10
- source_type:paper+2
- primary_source+2
- 'score>=28: 自动接受'
auto_review_score: 36
book_potential: 4
collected_date: '2026-07-11'
confidence: 4
created_at: '2026-07-11T18:08:50+08:00'
date: '2026-07-09'
entities:
- arxiv.org
event_date: '2026-07-09'
id: 2026-07-09-academic-foundation-model-webswarm-recursive-multi-agent-orchestration-for
importance: 4
keywords_en: &id001
- foundation-model
novelty: 5
ppt_potential: 4
primary_source: true
public_brief_potential: 3
review_status: accepted
reviewed_at: '2026-07-12T08:08:29+08:00'
reviewed_by: auto
source_type: paper
source_url: https://arxiv.org/abs/2607.08662v1
title_en: 'WebSwarm: Recursive Multi-Agent Orchestration for Deep-and-Wide Web Search'
title_zh: WebSwarm：基于递归多智能体编排的深度与广度网络搜索
topics: *id001
track: academic
---

# 知识卡片：WebSwarm：基于递归多智能体编排的深度与广度网络搜索

**一句话结论**  
WebSwarm 是一种渐进式递归委派框架，通过动态任务分解、递归扩展和智能体协作，在深度搜索、广度搜索及两者交织的复杂任务上，显著优于单智能体与现有并行多智能体基线。

**事件概述 / 研究问题**  
基于大语言模型（LLM）的网络搜索代理正从简单事实问答转向“深度与广度”并重的研究型任务。单 ReAct 风格智能体受限于单一长轨迹与有限上下文，难以兼顾深度与覆盖；现有并行多智能体系统虽提升搜索覆盖，但在递归深度、协作适应性、以及基于证据的扩展上仍存在明确局限。WebSwarm 旨在突破这些限制，实现可递归、自适应的多智能体搜索协调。

**方法 / 产品要点**  
- **核心机制**：渐进递归委派框架，在推理过程中联合构造任务分解、递归扩展与智能体协作。  
- **动态节点**：实例化搜索节点，每个节点耦合一个局部目标与一种搜索模式（指定如何组织搜索与协作）。  
- **委派与归并**：节点可自行解决目标或进一步委派子节点；解决后向上返回证据与结果，父节点据此扩展、修正或聚合搜索过程。  
- **引导策略**：先探测任务相关信息在网页上的组织方式，以指导后续节点扩展；在同质兄弟节点间重用过程级经验。  
- **模型通用性**：实验验证了不同基础模型下的泛化能力（材料未列出具体模型，待核实）。

**主要结果或产业意义**  
- **基准测试**：在 BrowseComp-Plus、WideSearch、DeepWideSearch 和 GISA 四个数据集上，WebSwarm 在深度、广度、以及二者交织的任务中一致优于单智能体和多智能体基线。  
- **分析验证**：消融研究、任务难度分析、网络工具效率分析和模型泛化实验进一步解释了 WebSwarm 的有效性，并为多智能体搜索系统提供了设计洞见。

**为什么重要**  
WebSwarm 针对现有并行多智能体系统的三大短板——递归深度不足、协作适应性差、缺乏基于证据的扩展——提供了统一的解决方案。它展示了如何让 LLM 代理在复杂、多层次的信息搜索中自主构建搜索树，并动态调整策略，从而推动智能信息检索从简单问答走向真正的“研究型搜索”。

**局限与不确定性**  
材料中未提及 WebSwarm 的具体局限性。可能涉及计算开销、节点数量上限、对低质量网页的鲁棒性等问题，需查阅完整论文或待后续验证。

**可用于图书/PPT/简报的角度**  
- 对比“单智能体 vs 多智能体 vs 递归多智能体”在搜索任务中的表现差异。  
- 展示 LLM 代理如何通过递归委派模拟人类研究者的“扩充-聚合”思维过程。  
- 作为“AI 驱动的下一代搜索引擎”或“自主研究助手”的典型案例。

**原始材料**

- **英文标题**：WebSwarm: Recursive Multi-Agent Orchestration for Deep-and-Wide Web Search  
- **英文关键词**：Recursive Multi-Agent Orchestration, Deep-and-Wide Web Search, Large Language Model, Foundation Model  
- **来源**：arXiv preprint arXiv:2607.08662v1, 2026-07-09  
- **作者**：Xiaoshuai Song, Liancheng Zhang, Kangzhi Zhao, Yutao Zhu, Zhongyuan Wang, Guanting Dong, Jinghan Yang, Han Li, Kun Gai, Ji-Rong Wen, Zhicheng Dou  
- **分类**：cs.CL, cs.AI, cs.MA  
- **摘要**（原文）：“Large language model (LLM)-based web search agents are transforming information seeking from simple factoid question answering into complex, deep-and-wide search and research-oriented tasks. ... Experiments on BrowseComp-Plus, WideSearch, DeepWideSearch, and GISA show that WebSwarm consistently outperforms single-agent and multi-agent baselines on deep, wide, and interleaved deep-and-wide tasks.”  
- **URL**：https://arxiv.org/abs/2607.08662v1  
- **PDF**：https://arxiv.org/pdf/2607.08662v1