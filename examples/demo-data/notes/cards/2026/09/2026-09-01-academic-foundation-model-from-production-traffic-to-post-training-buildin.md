---
auto_review_age_days: 1
auto_review_reasons:
- importance:2+4
- novelty:1+2
- confidence:1+2
- ppt_potential:1+1
- public_brief_potential:1+1
- topic_priority:5+10
- source_type:paper+2
- primary_source+2
- '22<score<28: 信号不够强，按配置设为 rejected'
auto_review_score: 24
book_potential: 1
collected_date: '2026-09-02'
confidence: 1
created_at: '2026-09-02T18:22:17+08:00'
date: '2026-09-01'
entities:
- arxiv.org
event_date: '2026-09-01'
id: 2026-09-01-academic-foundation-model-from-production-traffic-to-post-training-buildin
importance: 2
keywords_en: &id001
- foundation-model
novelty: 1
ppt_potential: 1
primary_source: true
public_brief_potential: 1
review_status: rejected
reviewed_at: '2026-09-03T08:34:34+08:00'
reviewed_by: auto
source_type: paper
source_url: https://arxiv.org/abs/2609.01572v1
title_en: 'From Production Traffic to Post-Training: Building a Self-Hosted LLM That
  Covers the Corporate Request Mix'
title_zh: 从生产流量到后训练：构建覆盖企业请求混合的自托管大语言模型
topics: *id001
track: academic
---

# 知识卡片：从生产流量到后训练：构建覆盖企业请求混合的自托管大语言模型

**一句话结论**

企业因数据驻留约束必须自托管大语言模型，但“只增加新模型、不淘汰旧模型”会让 GPU 资源池碎片化。本文用来自 200 多个内部应用的生产流量分析质量差距，沿“指令遵循、函数调用、内部任务分布”三个轴分别训练 GRPO 专家，再用两阶段 SLERP 合并；得到的单一模型在非推理模式下超越总参数量约 7 倍的基线，并承担平台 50% 的流量（每月 1.16 亿次请求），服务成本仅为原来的很小一部分。

**事件概述或研究问题**

- 背景：数据驻留约束迫使企业自托管 LLM；持续采用新模型而不淘汰旧模型会使服务集群不断膨胀，有限的 GPU 池被进一步碎片化。
- 问题：能否用一个自托管模型覆盖 200 多个内部应用产生的混合请求，同时不损失质量？
- 路径：从生产流量中找出真实质量差距，而不是只依赖公开通用基准；再用后训练手段系统性关闭这些差距。

**方法/产品要点**

- 整合对象：来自超过 200 个内部应用的生产流量。
- 质量差距分析：沿三个轴进行——指令遵循（instruction following）、函数调用（function-calling）、内部任务分布（internal task distribution）。
- 质量追踪：使用按生产流量分层的离线基准，并由确定性验证器或经过校准的 LLM 评判器打分。
- 训练策略：不将所有目标联合优化，因为这会引入跨领域奖励干扰；而是为每个轴独立训练一个 GRPO 专家。
- 专家合并：通过两阶段 SLERP 合并多个 GRPO 专家。
- 暴露的失败模式：每个专家的奖励信号会暴露不同的失败模式，分别是语义崩溃（semantic collapse）、过度调用（over-calling）和冗长欺骗（verbosity hacking），每种都需要针对性修复。

**主要结果或产业意义**

- 在内部 Arena 评测中，配方得到的模型超越总参数量约 7 倍的基线：69.6 对 65.8。
- 指令遵循得分：0.85 对 0.83。
- 函数调用得分：0.79 对 0.77。
- 同时提升了通用对话基准表现。
- 该模型吸收了平台 50% 的流量，即每月 1.16 亿次请求，服务成本显著降低。
- 产业意义：为“既要数据驻留、又要控制自托管成本”的企业提供了一种用后训练整合模型服务池的可操作路径。

**为什么重要**

- 它把“生产流量”而不是“公开榜单”作为后训练的数据与评估起点，更贴近企业真实部署需求。
- 它示范了如何在多目标任务中避免跨领域奖励干扰：分轴训练专家再合并，而不是端到端联合优化。
- 与已有卡片对比，本条增量在于：既有“缩小实验室到商店差距”卡片关注机器人 VLA 的系统集成，本条关注企业 LLM 服务池整合；既有“从 SRA 到 Self-Flow”卡片讨论数据增强/自监督，本条则讨论“生产错误分析 + 独立奖励专家 + 权重合并”的后训练配方。

**局限与不确定性**

- 摘要未披露具体模型名称、参数量、企业/平台名称以及绝对服务成本数字，以上均待核实。
- 内部 Arena、指令遵循和函数调用的具体评测集、打分方式和置信区间需阅读全文核实。
- “非推理模式”之外是否还支持推理模式，推理模式下的表现如何，材料未说明。
- 模型虽然承担 50% 平台流量，但剩余流量为何未迁移、是否存在仍需专用模型的长尾场景，摘要未说明，待核实。

**可用于图书/PPT/简报的角度**

- 企业自托管 LLM 的成本治理：如何从“模型数量膨胀”转向“用生产流量驱动模型整合”。
- 后训练评估可以按生产流量分层，而不是只追踪通用基准。
- “分轴训练、事后合并”可作为多目标强化学习中避免奖励干扰的案例。
- 案例式素材：覆盖 200+ 个内部应用，将每月 1.16 亿次请求中的 50% 吸收到一个自托管模型上。

**原始材料**

- 英文标题：From Production Traffic to Post-Training: Building a Self-Hosted LLM That Covers the Corporate Request Mix
- 英文关键词：self-hosted LLM; post-training; production traffic; instruction following; function-calling; GRPO; SLERP; enterprise request mix
- 来源：arXiv:2609.01572v1 [cs.CL]
- URL：https://arxiv.org/abs/2609.01572v1
- PDF：https://arxiv.org/pdf/2609.01572v1
- 作者信息：Olga Tsymboi 等
- 发布时间：2026-09-01（v1）