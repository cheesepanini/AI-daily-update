---
book_potential: 5
collected_date: '2026-07-11'
confidence: 4
created_at: '2026-07-11T08:04:17+08:00'
date: '2026-07-10'
entities:
- aiera.com.cn
event_date: '2026-07-10'
id: 2026-07-10-industry-ai-industry-grok-4-5-opus
importance: 4
industry_dimensions:
- company
keywords_en: &id001
- ai-industry
novelty: 5
ppt_potential: 5
primary_source: true
public_brief_potential: 4
review_status: rejected
source_type: chinese-media
source_url: https://aiera.com.cn/2026/07/10/other/admin/103414/%e7%aa%81%e5%8f%91%ef%bc%81%e9%a9%ac%e6%96%af%e5%85%8b%e4%ba%a4%e5%8d%b7%e6%9c%80%e5%bc%bagrok-4-5%ef%bc%8copus%e6%9c%80%e9%ab%98%e7%ba%a7%e6%99%ba%e8%83%bd%e6%89%93%e9%aa%a8%e6%8a%98%e4%bb%b7
title_en: 突发！马斯克交卷最强Grok 4.5，Opus最高级智能打骨折价
title_zh: Grok 4.5发布：性能逼近Opus 4.8，性价比之王？
topics: *id001
track: industry
---

# 知识卡片：Grok 4.5发布：性能逼近Opus 4.8，性价比之王？

英文标题：Grok 4.5 Launch: Musk’s New Model Rivals Opus 4.8 and GPT-5.5 with Dramatically Lower Cost  
英文关键词：Grok 4.5, X.AI, SpaceXAI, Cursor, Opus 4.8, GPT-5.5, SWE Bench Pro, Terminal Bench, DeepSWE, per-token intelligence, GB300  

## 一句话结论

马斯克旗下X.AI（SpaceXAI）发布旗舰模型Grok 4.5，在多项工程基准上逼近甚至超越Opus 4.8和GPT-5.5，同时Token消耗仅为竞品的四分之一，输入/输出价格分别低至$2/$6每百万Token，成为当前“性价比之王”。

## 事件概述

2026年7月10日，马斯克通过X.AI（SpaceXAI）与代码辅助工具Cursor合作，正式发布最强旗舰模型Grok 4.5。模型基于数万块英伟达GB300 GPU训练，专为编码和智能体任务设计。马斯克称其“大致相当于Opus 4.7，但快得多”。同时预告下个月将迎来“阶跃式提升”，并传闻2万亿参数的更大版本已在路上。

## 方法/产品要点

- **训练硬件**：数万块英伟达GB300 GPU，超大规模训练。
- **数据策略**：对海量语料进行严格过滤、去重、质量打分，重点提升“单Token智能度”（per-token intelligence）。训练栈为高度异步设计，支持智能体连续运行数小时，模型在几万块GPU上持续学习。
- **核心协作**：Cursor提供数以万亿计的开发者与代码库、工具互动的真实数据，使模型学会“人和AI如何一起写代码”。
- **模型规格**：基础版本为V9（1.5T参数），快速高级版本定价输入$4/输出$18。
- **速度**：推理速度达80 TPS（每秒Token数），官方宣称比Flash类模型更快。

## 主要结果或产业意义

- **基准测试成绩**：
  - SWE Bench Pro：64.7%，超过Opus 4.7（64.3%）、GPT-5.5（58.6%），逼近Opus 4.8（69.2%）。
  - Terminal Bench 2.1：83.3%，仅差GPT-5.5（83.4%）0.1个百分点。
  - DeepSWE 1.0：62.0%，碾压Opus 4.8（55.75%），紧咬GPT-5.5（64.31%）。
  - AAAI官方测试：排名第四，仅次于Fable 5、GPT-5.5、Opus 4.8。
  - Harvey法律智能体基准测试：位列第一。
- **效率与成本**：在SWE Bench Pro任务中，平均仅输出15,954个Token解决问题，而Opus 4.8需67,020个Token，Token消耗减少4.2倍。输入$2/百万Token，输出$6/百万Token，远低于多数顶级模型（十余美元起步）。
- **产业意义**：Grok 4.5以“单位时间、单位成本能买到更多智能”的思路，将性价比竞争推向新高度，可能倒逼其他厂商调整定价策略。

## 为什么重要

- **性价比碾压**：在性能接近第一梯队的前提下，价格和效率形成显著优势，降低了高级AI模型的应用门槛。
- **编码与智能体赛道**：通过与Cursor深度绑定，Grok 4.5成为专为软件开发和多步骤智能体任务优化的专用模型，可能改变开发者工作流。
- **马斯克生态闭环**：下个版本将整合特斯拉、SpaceX、Neuralink和Boring Company的真实工程问题数据，形成更强的领域能力。

## 局限与不确定性

- **非绝对最强**：当前铁王座仍由Claude Fable占据，Grok 4.5离AI天花板还有差距。马斯克内部评估仅认为其相当于Opus 4.7水平。
- **用户实测反馈不一**：部分开发者反映Grok 4.5在生成熔岩灯等创意任务上效果远不如Opus 4.7，表现不稳定。
- **上下文长度**：当前版本上下文未达百万（官方预告下月升级至100万），长尾任务能力待验证。
- **大规模参数量传闻**：2万亿参数版本尚未官方确认，属于“待核实”信息。
- **训练数据与能耗**：具体训练成本和能耗数据未披露，可持续性影响待观察。

## 可用于图书/PPT/简报的角度

- **AI模型竞争**：从“跑分大战”转向“效率与成本大战”，Grok 4.5为AI economics提供新案例。
- **垂直专用模型**：与Cursor合作体现“模型+工具”协同训练模式，可作为智能体时代模型定制化的范例。
- **马斯克商业版图**：SpaceXAI如何利用特斯拉等内部数据形成闭环，可引申为企业AI战略。
- **技术指标解读**：用“单Token智能度”概念解释模型效率，适合技术普及。

## 原始材料

- 新智元报道：https://aiera.com.cn/2026/07/10/other/admin/103414/%e7%aa%81%e5%8f%91%ef%bc%81%e9%a9%ac%e6%96%af%e5%85%8b%e4%ba%a4%e5%8d%b7%e6%9c%80%e5%bc%bagrok-4-5%ef%bc%8copus%e6%9c%80%e9%ab%98%e7%ba%a7%e6%99%ba%e8%83%bd%e6%89%93%e9%aa%a8%e6%8a%98%e4%bb%b7  
- X.AI官方公告：https://x.ai/news/grok-4-5  
- Cursor官方博客：https://cursor.com/blog/grok-4-5