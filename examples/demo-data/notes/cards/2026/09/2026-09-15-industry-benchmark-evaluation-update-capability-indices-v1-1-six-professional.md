---
auto_review_age_days: 1
auto_review_reasons:
- importance:3+6
- novelty:2+4
- confidence:3+6
- ppt_potential:3+3
- public_brief_potential:2+2
- topic_priority:5+10
- source_type:benchmark-update+2
- primary_source+2
- 'score>=28: 自动接受'
auto_review_score: 35
book_potential: 3
collected_date: '2026-09-15'
confidence: 3
created_at: '2026-09-15T18:05:21+08:00'
date: '2026-09-15'
entities:
- artificialanalysis.ai
id: 2026-09-15-industry-benchmark-evaluation-update-capability-indices-v1-1-six-professional
importance: 3
industry_dimensions:
- company
keywords_en: &id001
- benchmark-evaluation
novelty: 2
ppt_potential: 3
primary_source: true
public_brief_potential: 2
review_status: accepted
reviewed_at: '2026-09-16T08:20:52+08:00'
reviewed_by: auto
source_type: benchmark-update
source_url: https://artificialanalysis.ai/models/capabilities
title_en: Update Capability Indices v1.1 Six professional-domain indices, updated
  with stronger domain tuning and specialized evaluations
title_zh: Artificial Analysis 专业领域能力指数（AI Capability Indices）
topics: *id001
track: industry
---

# 知识卡片：Artificial Analysis 专业领域能力指数（AI Capability Indices）

## 一句话结论
Artificial Analysis 的 Capability Indices 页面展示了一套按“技能”和“专业领域”组织的 AI 模型能力指数；其中六个专业领域指数覆盖金融会计、战略运营、法律、医疗健康、工程和经济，并把 agentic knowledge work、推理、长上下文、工具使用、非幻觉等纳入测量维度。抓取摘录未包含具体模型排名、分数或 v1.1 更新细节。

## 事件概述或研究问题
该页面为 Artificial Analysis 的 AI Capability Indices 汇总页。页面描述称其提供独立能力指数，对 AI 模型在 agentic work 以及行业垂直领域（包括 legal、healthcare、finance、engineering、economics）进行排名。

页面按两类组织：
- By Skill：Reasoning、Coding、Tool Use、Long Context、Faithfulness、Agentic、Knowledge Work。
- By Domain：Business、Finance、Legal、Medical、Science。

页面列出六个标记为 Updated 的专业领域指数：Finance & Accounting Index、Strategy & Ops Index、Legal Index、Healthcare & Medical Index、Engineering Index、Economics Index。

任务提供的 Manual title 称这是 “Update Capability Indices v1.1 Six professional-domain indices, updated with stronger domain tuning and specialized evaluations”；但抓取正文未展示 v1.1、stronger domain tuning 或 specialized evaluations 的具体说明，待核实。

## 方法/产品要点
- **Finance & Accounting Index**：衡量金融与会计领域表现，包括 business knowledge、agentic knowledge work、reasoning、agentic tool use、long-context analysis、non-hallucination。标签：Finance、Business、Agentic、Knowledge Work、Reasoning、Tool Use、Long Context、Faithfulness、Updated。
- **Strategy & Ops Index**：衡量战略与运营领域表现，包括 business knowledge、agentic knowledge work、跨 business apps 的 agentic tool use、long-context analysis。标签：Business、Agentic、Knowledge Work、Tool Use、Long Context、Updated。
- **Legal Index**：衡量法律领域表现，包括 legal knowledge、agentic knowledge work、reasoning、long-context document analysis、non-hallucination、agentic tool use。标签：Legal、Agentic、Knowledge Work、Reasoning、Long Context、Faithfulness、Tool Use、Updated。
- **Healthcare & Medical Index**：衡量医疗与健康领域表现，包括 clinical knowledge、agentic knowledge work、对患者记录的长上下文推理、non-hallucination、clinical reasoning、agentic tool use。标签：Medical、Agentic、Knowledge Work、Long Context、Faithfulness、Reasoning、Tool Use、Updated。
- **Engineering Index**：衡量工程领域表现，包括 engineering knowledge、quantitative reasoning、agentic execution、terminal use。标签：Science、Reasoning、Agentic、Knowledge Work、Coding、Updated。
- **Economics Index**：衡量经济领域表现，包括 economics knowledge、quantitative reasoning、agentic execution、long-context analysis。标签：Business、Reasoning、Agentic、Knowledge Work、Long Context、Updated。

## 主要结果或产业意义
可确认的主要“结果”是指数结构和测量维度，而不是模型排名：页面没有在抓取摘录中给出具体模型、分数或名次。

产业意义在于，该页面把 AI 能力评测从通用技能扩展到专业领域，并把 agentic knowledge work、工具使用、长上下文、非幻觉等能力放进金融、法律、医疗、战略运营、工程、经济等场景中。这类指数可用于企业选型、供应商对比和行业部署前的维度拆解，尤其适合高风险专业场景的评测框架设计。

## 为什么重要
在 benchmark-evaluation 主题下，专业领域能力指数反映评测正在从单一通用榜单走向“技能 × 行业”的矩阵化。与已有卡片的关系是：既有卡片分别关注模型融合、MCP 工具连接、SWE-Bench Pro 编码基准可靠性；本条卡片的增量信息是 Artificial Analysis 提供的跨专业领域能力指数体系，可作为垂直行业 AI 能力看板和评测框架素材，而不是重复讨论单一编码基准的可靠性问题。

## 与既有脉络的关系
本条不是对既有卡片事实的重复，而是补足“专业领域评测”这一层：从通用/编码/工具调用扩展到 legal、medical、finance、economics、engineering、strategy & ops 等业务域。其增量价值在于展示评测维度如何组合，以及哪些能力被行业内视为关键；具体榜单结果和方法权重仍需回到原页面核实。

## 局限与不确定性
- 抓取摘录仅包含页面导航、指数描述和标签，未包含具体模型、分数、排名或发布时间。
- Manual title 提到 v1.1、stronger domain tuning、specialized evaluations；抓取正文未展示这些信息，待核实。
- “Updated”标签未给出更新日期、版本号或更新范围，待核实。
- 方法、数据、权重、任务数量、审计方式、模型覆盖范围等未在摘录中出现，待核实。
- By Domain 导航列出 Business、Finance、Legal、Medical、Science；六个指数中 Engineering Index 的标签为 Science，Economics Index 的标签为 Business，具体分类映射需以原页面为准。
- 是否存在模型覆盖偏差、排行榜排序变化或分数可复现性问题，待核实。

## 可用于图书/PPT/简报的角度
- “技能 × 行业”：一页看懂 AI 能力评测的矩阵化趋势。
- 专业领域 AI 选型：从通用跑分转向 agentic knowledge work、非幻觉、长上下文和工具使用。
- 高风险行业评测设计：法律、医疗、金融会计如何组合知识、推理与执行维度。
- 金融会计与战略运营：企业后台与决策场景的 AI 能力指标示例。
- 与 SWE-Bench Pro 可靠性争议对照：榜单需要方法透明、更新记录和可复现性。
- 标题示例：从通用榜单到行业能力指数——AI 评测的垂直化。

## 原始材料
- 英文标题：AI Capability Indices | Artificial Analysis
- 抓取描述：Independent capability indices from Artificial Analysis ranking AI models on agentic work and on industry verticals including legal, healthcare, finance, engineering and economics.
- 原始来源：Artificial Analysis, “AI Capability Indices | Artificial Analysis”, https://artificialanalysis.ai/models/capabilities
- 英文关键词：Capability Indices；By Skill；By Domain；Reasoning；Coding；Tool Use；Long Context；Faithfulness；Agentic；Knowledge Work；Business；Finance；Legal；Medical；Science；Finance & Accounting Index；Strategy & Ops Index；Legal Index；Healthcare & Medical Index；Engineering Index；Economics Index；Agentic Knowledge Work；Non-hallucination；Terminal Use；Quantitative Reasoning；Clinical Knowledge；Legal Knowledge；Business Knowledge；Economics Knowledge；Engineering Knowledge。
- 任务标注 Manual title：Update Capability Indices v1.1 Six professional-domain indices, updated with stronger domain tuning and specialized evaluations（页面抓取摘录未显示 v1.1 和 domain tuning 细节，待核实）。