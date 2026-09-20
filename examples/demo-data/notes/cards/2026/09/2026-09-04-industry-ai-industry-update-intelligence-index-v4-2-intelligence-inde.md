---
auto_review_age_days: 1
auto_review_reasons:
- importance:4+8
- novelty:4+8
- confidence:4+8
- ppt_potential:4+4
- public_brief_potential:3+3
- topic_priority:5+10
- source_type:benchmark-update+2
- primary_source+2
- 'score>=28: 自动接受'
auto_review_score: 45
book_potential: 4
collected_date: '2026-09-05'
confidence: 4
created_at: '2026-09-05T08:19:34+08:00'
date: '2026-09-04'
duplicate_suspect:
  date: '2026-08-06'
  source_url: https://artificialanalysis.ai/articles/artificial-analysis-intelligence-index-v4-1-1
  title: Artificial Analysis 发布智能指数 v4.1.1
entities:
- artificialanalysis.ai
event_date: '2026-09-04'
id: 2026-09-04-industry-ai-industry-update-intelligence-index-v4-2-intelligence-inde
importance: 4
industry_dimensions:
- company
keywords_en: &id001
- ai-industry
novelty: 4
ppt_potential: 4
primary_source: true
public_brief_potential: 3
review_status: accepted
reviewed_at: '2026-09-06T08:23:49+08:00'
reviewed_by: auto
source_type: benchmark-update
source_url: https://artificialanalysis.ai/articles/artificial-analysis-intelligence-index-v4-2
title_en: Update Intelligence Index v4.2 Intelligence Index v4.2 adds AA-Briefcase
  and GDP.pdf, upgrades AA-LCR to v1.1, removes GPQA Diamond, updates SciCode grading,
  and rebalances weights
title_zh: Artificial Analysis 发布智能指数 v4.2
topics: *id001
track: industry
---

# 知识卡片：Artificial Analysis 发布智能指数 v4.2

## 一句话结论
Artificial Analysis 于 2026 年 9 月 4 日发布 Intelligence Index v4.2，新增 AA-Briefcase 和 GDP.pdf 两类更接近真实工作场景的评测，移除已饱和的 GPQA Diamond，并将私有 held-out 测试集权重提升至 40%，以降低“刷榜”空间。

## 事件概述
Intelligence Index v4 于 2026 年 1 月发布，距今已 8 个月。团队原本为保持榜单稳定而暂缓更新，但近几周前沿模型迭代很快，因此决定先推出 v4.2 作为过渡版本。v4.2 同时也是 v5 的部分能力提前落地，后续还会有更多增量发布。

v4.2 主要变更：
- 新增 AA-Briefcase：内部自研的私有测试集，评估智能体在真实知识工作项目中的表现。
- 新增 GDP.pdf：由 Surge AI 创建，评估长文档专业推理能力。
- 移除 GPQA Diamond：该科学推理评测已被模型表现饱和。
- 将私有 held-out 测试集权重从 v4.1 的约 20% 提升至 40%。
- 升级评分基础设施，提升评分准确性和稳定性。

## 方法/产品要点
- **AA-Briefcase**：由行业专家构建复杂项目，模拟多周知识工作，每个项目包含多个相互关联的任务和数千个输入源文件。结合 rubric 和 pairwise grading，综合评估可验证的任务成功度、分析质量和展示质量，以衡量模型的整体智能体知识工作能力。
- **GDP.pdf**：覆盖 100 份 PDF、10 个领域，共 4,592 页。模型需要综合文本、表格、图表、脚注和排除项中的证据，进行单轮专业文档推理。回答由 1,275 条专家撰写的原子标准进行评分；只有满足全部标准，任务才计为“All-pass”。
- **防 gaming 加权**：Index 中 40% 权重来自私有 held-out 测试集，是 v4.1 的两倍。Held-out 数据包括 AA-Briefcase、AA-Omniscience 以及 CritPt 的答案数据。
- **基础设置升级**：AA-LCR v1.1 新增评分系统 prompt，修正答案键中的错误和歧义；GDPval-AA v2 与 AA-Briefcase 改进采样方式并重新锚定 Elo 尺度；SciCode 改进评分沙箱，确保运行慢但正确的代码不会被误判为失败。

## 主要结果
- Anthropic 和 OpenAI 领先指数榜单。Anthropic 的 Claude Fable 5.1 位居第一，OpenAI 的 GPT-6 Astra 紧随其后，比 GPT-5.6 Sol 高 4 分。
- Meta 位列第三，其后依次为 SpaceXAI、Moonshot/Kimi、Z.AI 和 Google。
- Cost per Task 帕累托前沿由 Anthropic、OpenAI、Meta 和 Z.AI 四家实验室占据。
- GPT-6 Astra 在输出 token 效率方面领先：在接近智能前沿的模型中，它比几乎所有其他模型更具 token 效率；Claude Fable 5.1、Grok 4.5 和 Gemini 3.5 Flash-Lite 分布在曲线的不同端。
- AA-Briefcase 中，Claude Fable 5.1 和 Opus 5 领先，随后是 GPT-6 Astra 和 Muse Spark 1.3；GPT-6 Astra 较 GPT-5.6 Sol 提升约 85 Elo 点。
- GDP.pdf 中 OpenAI 领先：GPT-6 Astra 的 All-pass Rate 为 33.2%，GPT-5.6 Sol 为 28.2%，Claude Fable 5.1 为 26.2%。

## 为什么重要
本条是对 Artificial Analysis 智能指数 v4.1.1 相关卡片的更新。v4.1.1 时 Claude Opus 5 以 63 分位居第一；v4.2 引入新评测和权重调整后，领先模型变为 Claude Fable 5.1。增量信息主要体现在：评测内容从传统问答转向更复杂的“多周知识工作项目”和“4,592 页 PDF 长文档推理”；私有测试集权重翻倍，说明 Artificial Analysis 正通过不可见测试题降低大模型实验室定向优化的风险；同时，GPT-6 Astra 在 token 效率和长文档任务上的表现，提供了模型竞争的新维度。

## 局限与不确定性
- 材料未给出 v4.2 的完整分模型得分表，也未说明每项评测在总指数中的具体权重。
- AA-Briefcase 是私有测试集，公众无法查看具体题目和完整评分细项；GDP.pdf 只覆盖英文 PDF 文档推理，不能代表所有真实工作场景。
- Elo 尺度重新锚定对历史得分比较的影响、以及移除 GPQA Diamond 后与 v4.1.1 的可比性调整幅度，材料未详细说明，待核实。
- 文中提到的模型名称和具体分数来自官方发布页面，独立复现结果待进一步测试。

## 可用于图书/PPT/简报的角度
- “刷榜”攻防战：评测机构如何通过提高私有测试集权重来防止模型针对性训练。
- 从“考试型基准”到“工作型基准”：AA-Briefcase 模拟数周知识工作，GDP.pdf 测试真实专业文档理解。
- 前沿模型格局：Anthropic、OpenAI 领跑，Meta 进入第三；成本与 token 效率成为与智能分数并列的关键指标。
- 长上下文能力的新测量方式：以跨 4,592 页 PDF 的证据综合能力取代简单“上下文长度”数字。

## 原始材料
- 英文标题：Announcing Artificial Analysis Intelligence Index v4.2
- 来源 URL：https://artificialanalysis.ai/articles/artificial-analysis-intelligence-index-v4-2
- 关键词：AI industry; Artificial Analysis; Intelligence Index v4.2; AA-Briefcase; GDP.pdf; GPQA Diamond; benchmark; private test set; Claude Fable 5.1; GPT-6 Astra