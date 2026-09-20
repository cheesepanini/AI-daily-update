---
auto_review_age_days: 1
auto_review_reasons:
- importance:5+10
- novelty:5+10
- confidence:3+6
- ppt_potential:5+5
- public_brief_potential:4+4
- topic_priority:5+10
- source_type:chinese-media-2
- primary_source+2
- 'score>=28: 自动接受'
auto_review_score: 45
book_potential: 5
collected_date: '2026-07-25'
confidence: 3
created_at: '2026-07-25T08:03:48+08:00'
date: '2026-07-25'
duplicate_suspect:
  date: '2026-07-09'
  source_url: https://openai.com/index/bio-bug-bounty
  title: OpenAI GPT-5.5 生物漏洞赏金计划
entities:
- aiera.com.cn
event_date: '2026-07-25'
id: 2026-07-25-industry-ai-industry-gpt-5-630-56
importance: 5
industry_dimensions:
- company
keywords_en: &id001
- ai-industry
novelty: 5
ppt_potential: 5
primary_source: true
public_brief_potential: 4
review_status: accepted
reviewed_at: '2026-07-26T08:05:51+08:00'
reviewed_by: auto
source_type: chinese-media
source_url: https://aiera.com.cn/2026/07/25/other/admin/105812/gpt-5-6%e8%af%81%e4%bc%aa30%e5%b9%b4%e5%9b%be%e8%ae%ba%e7%8c%9c%e6%83%b3%ef%bc%81%e5%8c%97%e5%a4%a7%e6%a0%a1%e5%8f%8b5%e5%a4%a9%e8%bf%9e%e7%a0%b46%e9%a2%98
title_en: GPT-5.6证伪30年图论猜想！北大校友5天连破6题
title_zh: GPT-5.6证伪30年图论猜想，北大校友5天连破6题
topics: *id001
track: industry
---

# 知识卡片：GPT-5.6证伪30年图论猜想，北大校友5天连破6题

**English Title:** GPT-5.6 Falsifies a 30-Year Graph Theory Conjecture; PKU Alumni Solves 6 Open Problems in 5 Days

**English Keywords:** GPT-5.6, Dinitz-Garg-Goemans conjecture, graph theory, Erdős problems, AI-assisted mathematics, codex workflow

## 一句话结论

GPT-5.6 Pro 通过与人类专家（Dmitry Rybin）的简短对话，构造了一个反例，证伪了图论中悬而未决30年的 Dinitz-Garg-Goemans 成本版猜想。同期，北大校友 Shouqiao Wang 使用 GPT-5.6 Sol 配合 Codex 工作流，5天内解决了6道开放的 Erdős 问题。

## 事件概述

2026年7月25日，新智元报道了两项由 GPT-5.6 驱动的数学突破。一是 Dmitry Rybin（香港中文大学（深圳）机器学习博士，曾获国际数学奥赛金牌）与 GPT-5.6 Pro 仅用三句对话，便构造出一个分数流成本为58、而任何容量违规不超过15的不可分割流成本至少60的反例，从而证伪了 Dinitz-Garg-Goemans 猜想。二是哥伦比亚大学博士生 Shouqiao Wang（北大数院校友，13岁获欧几里得数学竞赛世界第一，两届CMO银牌）使用 GPT-5.6 Sol 配合 Codex 工作流，5天尝试了约13道开放 Erdős 问题，成功解决了其中6道，成功率达46%，其中一道单题连续计算32小时。

## 方法/产品要点

- **GPT-5.6 Pro 证伪猜想：** 人类专家仅给出三条逐步深入的指令（构造反例、寻找结构化反例、给出完整无条件反例）。模型输出一个三终端图：需求15/10/15，每个终端有一条零成本路径和一条成本30的路径，三条零成本路径两两冲突，致使整数解最低成本60，而分数解（1/3、2/5、1/3）成本仅58。本质上利用了稳定集不等式的分数/整数间隙。
- **Shouqiao Wang 的工作流：**
  1. **选题策略：** 只挑数学家已在讨论的题，排除与重大猜想捆绑的题目。
  2. **定义解决标准：** 精确重述问题、写明完整证明所需确立的要点、列出较弱的不算数的结论、点明特有陷阱。
  3. **对抗审计：** 要求独立的对抗Agent挑战每个候选结论，模型反复推翻自我论证，直到挑不出实质问题。
  4. **流程：** 尝试 → 失败 → 诊断 → 换路线 → 写证明草稿 → 对抗审计 → 修补，死循环直至通过。

## 主要结果或产业意义

- 成功证伪了图论领域一个30年未解的猜想（该猜想在2023年 arXiv 论文和2026年1月文献中仍列为 open）。
- 用 AI 辅助方法在短时间内解开了6道此前标记为开放的 Erdős 问题，其中一道是陶哲轩研究过但未解决的。
- 展示了多 Agent 对抗审计、迭代式自纠正工作流在数学研究中的有效性，无需极深的数学背景即可操作（Shouqiao Wang 声称“这套工作流不需要很深的数学知识”）。

## 为什么重要

- 此事件是 AI 从“辅助计算”到“主动发现反例/证明”的显著跃升。与已有卡片（GPT-5.6 发布、性能分档）不同，本卡片聚焦于 GPT-5.6 在数学前沿问题上的实际产出，提供了具体结果（破题数、成功率、反例细节）和工作流方法论，为“AI是否能获得菲尔兹奖”的讨论提供了实证。
- 与“人类最后一届菲尔兹奖”的圈内说法相呼应，引发了关于人类智力在数学研究中地位的广泛讨论。

## 局限与不确定性

- 材料中提到的“人类最后一届菲尔兹奖”为圈内观点或网络热梗，并非正式结论，待核实。
- GPT-5.6 在此过程中的具体角色是“生成反例/辅助推理”还是“完全自主”尚需澄清；人类专家（Rybin 和 Wang）仍然提供了关键的方向性指引和验证。
- Shouqiao Wang 承认自己有数学背景，其工作流的可推广性（对无背景用户）未经验证。
- 文中提及的“5天连破6题”具体包括哪些 Erdős 问题编号、是否经过同行评审或正式验证，材料未提供，待核实。

## 可用于图书/PPT/简报的角度

- **AI 数学能力的里程碑：** 对比 AlphaGo 下棋、AlphaFold 预测蛋白质，GPT-5.6 直接攻击纯数学开放问题并成功。
- **人机协作新模式：** 从“人类提问、机器执行”到“人类给策略、机器生成反例、人类/Agent共同审计”。
- **反例的力量：** 用一个简单图（三个节点、两条路径）推翻30年猜想，强调反例在数学中的决定性作用。
- **教育启示：** 奥赛金牌、北大数院校友转向机器学习与博弈论，AI 工具让非纯数学背景的人也能触及前沿。

## 与既有脉络的关系

本卡片是对已有 GPT-5.6 相关卡片（发布、分档、额度重置）的延伸，新增了具体数学成果和应用案例，展示了 GPT-5.6 在科研协作中的实际价值，而非仅性能参数或产品功能。

## 原始材料

- 新智元报道：GPT-5.6证伪30年图论猜想！北大校友5天连破6题（2026-07-25）  
  URL: https://aiera.com.cn/2026/07/25/other/admin/105812/gpt-5-6%e8%af%81%e4%bc%aa30%e5%b9%b4%e5%9b%be%e8%ae%ba%e7%8c%9c%e6%83%b3%ef%bc%81%e5%8c%97%e5%a4%a7%e6%a0%a1%e5%8f%8b5%e5%a4%a9%e8%bf%9e%e7%a0%b46%e9%a2%98
- 引用推特来源：Dmitry Rybin (@DmitryRybin1) 和 Shouqiao Wang (@Qiaoqiao2001) 的原帖（具体ID见原文）