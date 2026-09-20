---
book_potential: 4
collected_date: '2026-07-07'
confidence: 5
created_at: '2026-07-07T09:15:56+08:00'
date: '2026-07-07'
entities:
- artificialanalysis.ai
id: 2026-07-07-industry-ai-industry-update-intelligence-index-v4-1-intelligence-inde
importance: 4
industry_dimensions:
- company
keywords_en: &id001
- ai-industry
novelty: 4
ppt_potential: 5
primary_source: true
public_brief_potential: 4
review_status: rejected
source_type: benchmark-update
source_url: https://artificialanalysis.ai/articles/artificial-analysis-intelligence-index-v4-1
title_en: "Update Intelligence Index v4.1 Intelligence Index v4.1 features updates
  to GDPval-AA V2, \U0001D70F³-Banking, and Terminal-Bench v2.1"
title_zh: AI智能指数v4.1——转向智能体工作负载
topics: *id001
track: industry
---

# 知识卡片：AI智能指数v4.1——转向智能体工作负载

**一句话结论**  
Artificial Analysis 发布 Intelligence Index v4.1，将评估重心转向智能体（Agentic）工作负载，引入每任务成本、时间等新指标，并更新三大基准测试。

**事件概述或研究问题**  
2026年6月15日，Artificial Analysis 宣布 Intelligence Index v4.1 更新。该指数是衡量模型智能和跟踪 AI 进展的综合指标。v4.1 标志着向智能体任务的广泛转变，主要包含三项变化：评估升级与重新加权、添加每任务指标、以及缓存输入 token 报告。

**方法/产品要点**  
- **评估升级**：  
  - Terminal-Bench Hard 升级为 Terminal-Bench 2.1，任务更具挑战性，能更好区分前沿模型。  
  - τ²-Bench Telecom 升级为 τ³-Bench Banking，采用更新、更稳健的任务集。  
  - GDPval-AA 升级至 GDPval-AA v2：Elo 重新标定，以人类表现 1000 为基线；引入旋转前沿模型评审小组；回合限制从 100 提升至 250。  
- **评估移除**：IFBench 因饱和（无法有效区分前沿模型）被移除，但将继续运行并发布新模型结果。  
- **新指标**：每任务成本（Cost per Task）、每任务时间（Time per Task）、每任务 token 数（Tokens per Task），基于指数任务集计算平均值。  
- **缓存输入 token 报告**：报告缓存输入 token 及其对成本的影响，以反映模型运行的真实成本。  
- **权重构成**（满分100%）：  
  - GDPval-AA v2: 20%  
  - Terminal-Bench 2.1: 16%  
  - τ³-Bench Banking: 14%  
  - Humanity's Last Exam: 12%  
  - AA-Omniscience Accuracy: 8%  
  - SciCode: 8%  
  - GPQA: 6%  
  - AA-LCR: 6%  
  - CritPt: 6%  
  - AA-Omniscience Non-Hallucination: 4%

**主要结果或产业意义**  
- **领先模型**：Claude Fable 5（带 Opus 4.8 回退，60 分）领跑指数，但当前不可用；Claude Opus 4.8（max，56 分）为可用模型中最智能的，领先于 GPT-5.5（xhigh，55 分）。  
- **开源领先模型**：DeepSeek V4 Pro（max，44 分）和 MiniMax M3（44 分）并列，其后为 Kimi K2.6（43 分）和 MiMo-V2.5-Pro（42 分）。  
- **每任务成本**：Claude Opus 4.8（max）为最贵的可用模型，$1.78/任务；Claude Fable 5 为最高（$3.25）。GPT-5.5（xhigh）智能指数仅低1分，但每任务成本仅 $0.99。DeepSeek V4 Pro（max）成本极低（$0.04/任务），其他领先专有模型成本是其 20–45 倍。  
- **每任务时间**：Grok 4.3（high）最快（1.5 分钟），Claude Sonnet 4.6（max）最慢（13.5 分钟）。Claude Opus 4.8（max）需 6.4 分钟，GPT-5.5（xhigh）需 3.7 分钟。Gemini 3.1 Pro Preview 在智能指数 46 分下仅需 1.6 分钟，表现出色。  
- **意义**：v4.1 强化了对真实智能体工作负载的评估，并引入成本、时间等实用指标，使用户能更明智地选择模型和 API 提供商。

**为什么重要**  
向智能体工作负载的转变反映了 AI 应用从简单问答向多步骤、长时域自主任务的演进。新指标（成本/任务、时间/任务）直接与部署成本挂钩，帮助开发者平衡性能与预算。缓存 token 的纳入也使成本计算更贴近实际。

**局限与不确定性**  
- Claude Fable 5 目前不可用，其分数可能不代表实际可用性能。  
- 部分基准（如 GDPval-AA v2）仍依赖评审模型，评审模型自身的偏差可能影响评分。  
- IFBench 的移除表明某些旧基准已无法区分前沿模型，未来其他基准也可能饱和。  
- 每任务时间仅计算推理解码时间，不包含其他延迟（如网络传输）。  
- 材料未说明 v4.1 的具体发布时间线和后续更新计划。

**可用于图书/PPT/简报的角度**  
- 在图表中对比 Claude Opus 4.8、GPT-5.5、DeepSeek V4 Pro 的智能指数与每任务成本，展示“性价比”差异。  
- 使用“每任务时间 vs 智能指数”散点图凸显 Gemini 3.1 Pro Preview 的效率。  
- 以 v4.1 的权重构成（特别是 GDPval-AA 占比最高）为例，说明如何设计综合评估体系。  
- 结合“智能体工作负载”趋势，讨论 AI 模型评估标准从语言理解向自主任务执行演变。

**原始材料**  
URL: https://artificialanalysis.ai/articles/artificial-analysis-intelligence-index-v4-1