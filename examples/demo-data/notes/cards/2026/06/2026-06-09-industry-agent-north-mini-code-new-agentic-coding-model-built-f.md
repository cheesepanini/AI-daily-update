---
auto_review_age_days: 1
auto_review_reasons:
- importance:3+6
- novelty:3+6
- confidence:2+4
- ppt_potential:3+3
- public_brief_potential:3+3
- topic_priority:5+10
- source_type:company-news+2
- primary_source+2
- 'score>=28: 自动接受'
auto_review_score: 36
book_potential: 4
collected_date: '2026-07-07'
confidence: 3
created_at: '2026-07-07T10:29:35+08:00'
date: '2026-06-09'
entities:
- cohere.com
id: 2026-06-09-industry-agent-north-mini-code-new-agentic-coding-model-built-f
importance: 4
industry_dimensions:
- company
keywords_en: &id001
- agent
novelty: 4
ppt_potential: 4
primary_source: true
public_brief_potential: 4
review_status: accepted
reviewed_at: '2026-07-08T15:27:10+08:00'
reviewed_by: auto
source_type: company-news
source_url: https://cohere.com/blog/north-mini-code
title_en: North Mini Code NEW Agentic coding model, built for practical software engineering
title_zh: Cohere 推出开源智能编码模型 North Mini Code
topics: *id001
track: industry
---

# 知识卡片：Cohere 推出开源智能编码模型 North Mini Code

**一句话结论**  
Cohere 发布了其首个面向开发者的开源智能编码模型 North Mini Code，以 30B 总参数量（3B 活跃参数）在软件工程基准上展现竞争力，并通过高吞吐量和低延迟降低了部署成本。

**事件概述**  
2026 年 6 月 9 日，Cohere 宣布开源 North Mini Code（Apache 2.0 许可）。该模型采用混合专家（MoE）架构，仅需 3B 活跃参数即可完成代码生成、智能软件工程和终端任务，旨在为“主权开发者”提供可本地或私有化部署的编码智能体能力。模型权重已在 Hugging Face、Model Vault 等平台开放，并兼容 OpenCode 等主流工具链。

**方法/产品要点**
- 架构与规模：30B 总参数 / 3B 活跃参数，MoE，支持 FP8 与 FP4 精度。
- 上下文长度：256K 总上下文，64K 最大生成长度。
- 优化方向：代码生成、智能体软件工程（含子智能体编排、系统架构映射、代码审查）、终端任务。
- 最小硬件：1× H100 @ FP8 或 1× H100 @ FP4。
- 许可：Apache 2.0。

**主要结果或产业意义**
- 基准测试：在 SWE-Bench Verified、SWE-Bench Pro 和 Terminal Bench v2 等基准上与同类开源模型（约 30B 规模）处于同一梯队。在 Artificial Analysis Coding Index 上得分为 33.4。
- 速度优势：内部测试中，与 Devstral Small 2 相比，相同并发与硬件下输出吞吐量最高提升 2.8 倍，令牌间延迟降低 30%（时间到首令牌 TTFT 略逊于对手）。
- 产业意义：为无法依赖商业闭源 API 的企业和主权开发者提供了可自由部署的编码智能体模型，推动了开源模型在软件工程领域的实用化。

**为什么重要**
North Mini Code 是 Cohere 首款专为开发者设计的开源模型，填补了“轻量级、可自托管”的智能编码模型空白。其高效设计（3B 活跃参数）使单块 H100 即可运行，大大降低了企业对 AI 编码基础设施建设成本与供应商锁定的担忧。

**局限与不确定性**
- 材料未提供与其他更大规模模型（如 70B/100B+）的直接对比，仅对比了相似参数量级模型。
- 基准测试中部分对比数据为内部复现或第三方报告，未经独立验证（材料脚注说明）。
- “主权 AI”生态的实际落地效果、社区反馈如何影响后续路线图，尚未有具体案例或数据。
- 长上下文（256K）下的实际稳定性与性能表现未在材料中详述。

**可用于图书/PPT/简报的角度**
- “30B 总分 / 3B 活跃：MoE 架构如何用 1/10 参数跑出全栈编码能力”
- “单卡 H100 可运行的智能编码体：从闭源 API 到私有化部署的转折点”
- “基准之外的真正价值：2.8 倍吞吐提升如何缩短开发者迭代周期”
- “主权 AI 实例：Cohere 开源策略对受监管行业（金融、政务）的潜在影响”

**原始材料**
- 标题：North Mini Code: Agentic Coding Model for Developers | Cohere
- 来源 URL：https://cohere.com/blog/north-mini-code
- 英文关键词：North Mini Code, Agentic Coding, Open-source, Cohere, Mixture-of-Experts (MoE), Sovereign AI
- 关键日期：2026-06-09（发布日期）