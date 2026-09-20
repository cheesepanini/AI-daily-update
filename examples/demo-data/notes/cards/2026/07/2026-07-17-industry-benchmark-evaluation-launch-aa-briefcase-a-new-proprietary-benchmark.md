---
book_potential: 4
collected_date: '2026-07-17'
confidence: 4
created_at: '2026-07-17T08:12:19+08:00'
date: '2026-07-17'
duplicate_suspect:
  date: '2026-07-07'
  source_url: https://artificialanalysis.ai/articles/aa-briefcase
  title: AA-Briefcase：前沿知识工作评估基准
entities:
- artificialanalysis.ai
id: 2026-07-17-industry-benchmark-evaluation-launch-aa-briefcase-a-new-proprietary-benchmark
importance: 4
industry_dimensions:
- company
keywords_en: &id001
- benchmark-evaluation
novelty: 4
ppt_potential: 4
primary_source: true
public_brief_potential: 4
review_status: rejected
source_type: benchmark-update
source_url: https://artificialanalysis.ai/evaluations/aa-briefcase
title_en: Launch AA-Briefcase A new proprietary benchmark for long-horizon knowledge
  work
title_zh: AA-Briefcase：代理知识工作基准测试详解
topics: *id001
track: industry
---

# 知识卡片：AA-Briefcase：代理知识工作基准测试详解

**一句话结论**：AA-Briefcase 是 Artificial Analysis 开发的私有基准测试，通过模拟多周真实商业项目（共 4 个场景、91 个任务）评估 AI 模型的代理能力，涵盖数据分析、产品管理、企业战略等长周期知识工作，并采用三元评分体系（Rubric 二元检查、Analytical Quality 成对比较、Presentation 成对比较），最终以 Elo 综合排名。当前（2026年7月）榜首为 Anthropic Claude Fable 5（Elo 1583）。

**事件概述/研究问题**：本基准旨在填补现有评估对代理（agent）在长周期、多步骤知识工作场景中表现测量的空白。不同于短问答或单任务基准，AA-Briefcase 要求模型在跨周的项目中完成可交付物（电子表格、PPT、备忘录等），并处理数千个输入文件中的跨源冲突信息。

**方法/产品要点**：
- **结构**：4 个多周项目场景（数据科学、产品管理、企业战略等）+ 1 个公开示范场景（Hugging Face 发布，不计入正式成绩）。共 91 个任务，每个任务是一个可交付物。
- **评分**：每个任务由三类检查构成：
  1. **Rubric（二元通过/失败）**：是否遵循指令、发现隐藏要求、使用正确证据、得出正确结论。
  2. **Analytical Quality（成对比较）**：与其他模型提交对比，评估全面性、分析严谨性、证据支持度。
  3. **Presentation（成对比较）**：与其他模型对比专业呈现质量。
- **综合指标**：AA-Briefcase Elo，通过将 Rubric 通过率经合成头对头比赛转换为 Elo 分数，再与 Analytical Quality Elo 和 Presentation Elo 聚合得到（置信区间钳制于 0）。
- **运行方式**：虽然同一场景内任务共享文件和上下文，但当前每个任务独立运行，不继承模型之前的提交。

**主要结果或产业意义**：
- **排行榜（前 6 名）**：
  | 排名 | 模型 | Elo | 置信区间 | 发布日期 |
  |---|---|---|---|---|
  | 1 | Anthropic Claude Fable 5 (Adaptive Reasoning, Max Effort, Opus 4.8 Fallback) | 1583 | -15/+16 | Jun 2026 |
  | 2 | Kimi K3 | 1547 | -13/+14 | Jul 2026 |
  | 3 | OpenAI GPT-5.6 Sol (max) | 1495 | -12/+13 | Jul 2026 |
  | 4 | Anthropic Claude Sonnet 5 (Adaptive Reasoning, Max Effort) | 1388 | -12/+11 | Jun 2026 |
  | 5 | Anthropic Claude Opus 4.8 (Adaptive Reasoning, Max Effort) | 1354 | -11/+10 | May 2026 |
  | 6 | SpaceXAI Grok 4.5 (high) | 1323 | -12/+13 | Jul 2026 |
- 共测试 49 个模型，覆盖 OpenAI、Meta、Google、Anthropic、Mistral、DeepSeek 等主流厂商。
- 该基准将成本（每任务平均美元）、速度（每任务壁钟分钟）、Token 消耗、工具调用次数等作为附加维度，支持性能 vs 成本的权衡分析。
- 图表（如 Elo vs 智能指数、Elo vs 发布时间、按文件类型分解的 Rubric 通过率）提供了多维洞察。

**为什么重要**：
- 这是首个专门针对**长周期代理知识工作**的私有基准，模拟实际商业场景中的多周项目，比现有短问答或单任务基准更贴近真实应用。
- 三元评分体系（Rubric + 成对分析 + 呈现）使得评估更全面，既考察客观准确性，也衡量主观分析质量和专业汇报能力。
- **与既有脉络的关系**：相比之前的卡片（AA-Briefcase：前沿知识工作评估基准），本卡片提供了具体的评分机制细节、排行榜排名以及新发布的公开示范场景信息，并展示了最高分模型的 Elo 数据和置信区间。

**局限与不确定性**：
- 当前每个任务独立运行，模型无法利用自身之前的提交结果，与真实工作中连续迭代的流程存在差距。
- 评分中的成对比较（Analytical Quality 和 Presentation）依赖于人工或自动评判，其一致性待核实。
- 公开示范场景仅有一个周，且不计入官方成绩，外部研究者难以完全复现评估。
- 测试集和任务细节未完全公开（仅以私有方式运行），可能影响外部验证和对比。

**可用于图书/PPT/简报的角度**：
- **标题建议**：“AI 代理能完成多周项目管理吗？——AA-Briefcase 揭示的性能、成本与局限”
- **精简要点**：
  - 4 个场景、91 个任务，模拟真实商业项目。
  - Claude Fable 5、Kimi K3、GPT-5.6 Sol 位列前三。
  - 评分不仅看正确性，也看分析深度和呈现质量。
  - 每任务成本、时间、Token 消耗可辅助选型决策。
- **可视化建议**：展示排行榜前 10 名的 Elo 条形图、Elo vs 成本散点图。

**原始材料**：
- URL: https://artificialanalysis.ai/evaluations/aa-briefcase
- 英文标题：AA-Briefcase: Agentic Knowledge Work Benchmark | Artificial Analysis
- 英文关键词：benchmark, evaluation, agentic knowledge work, AI agents, long-horizon, rubric, pairwise comparison, Elo
- 描述：A private evaluation developed by Artificial Analysis for frontier agentic capability in long-horizon knowledge work, testing agents on realistic business workflows that require deliverables such as spreadsheets, presentations, and memos.