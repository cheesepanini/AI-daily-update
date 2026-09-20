---
auto_review_age_days: 1
auto_review_reasons:
- importance:4+8
- novelty:3+6
- confidence:2+4
- ppt_potential:4+4
- public_brief_potential:2+2
- topic_priority:5+10
- source_type:company-news+2
- primary_source+2
- 'score>=28: 自动接受'
auto_review_score: 38
book_potential: 4
collected_date: '2026-09-12'
confidence: 2
created_at: '2026-09-12T08:09:00+08:00'
date: '2026-09-12'
duplicate_suspect:
  date: '2026-08-18'
  source_url: https://www.qbitai.com/2026/08/474611.html
  title: AI Infra进入自进化时代！清华团队AI优化AI造就国产万亿Token工厂
entities:
- www.together.ai
id: 2026-09-12-industry-ai-industry-the-open-source-ai-stack-models-inference-router
importance: 4
industry_dimensions:
- company
keywords_en: &id001
- ai-industry
novelty: 3
ppt_potential: 4
primary_source: true
public_brief_potential: 2
review_status: accepted
reviewed_at: '2026-09-13T18:06:01+08:00'
reviewed_by: auto
source_type: company-news
source_url: https://www.together.ai/blog/the-open-source-ai-stack
title_en: 'The Open Source AI Stack: models, inference, routers, harnesses & tools
  →'
title_zh: 开源AI栈：模型、推理、网关与路由器、Harness与工具
topics: *id001
track: industry
---

# 知识卡片：开源AI栈：模型、推理、网关与路由器、Harness与工具

## 一句话结论
开源模型质量逐步接近闭源模型后，应用开发者可通过分层独立的开源AI栈——**Model、Inference、Gateways and routers、Harness、Tools（Skills和MCP）**——在新模型发布时快速替换，而不必重建整个工作流。

## 事件概述或研究问题
Together AI博客文章 **The Open Source AI Stack**（作者 Hassan El Mghari，来源标注发布日期 9/9/2026，待核实）讨论：当开发者与组织因所有权、控制权和经济性转向开源模型时，需要理解哪些栈层。文章的核心问题是：使用开源模型进行 agentic software development，是否必须训练模型、购买GPU或成为机器学习专家？文章认为不需要，并称从应用开发者视角看，这套栈与使用闭源模型相当类似：有模型回答提示，也有 harness 管理交互。若已熟悉 Claude Code，可能比想象中更接近使用开源模型。

## 方法/产品要点
文章将开源模型AI栈拆为五层，并称之为 **The MIGHT Stack**：

1. **Model**：解释请求并决定做什么的智能层，负责推理、决策与代码库变更判断。
2. **Inference**：模型实际运行的基础设施与推理提供商。
3. **Gateways and routers**：决定哪个模型或提供商处理每个请求，平衡成本、速度与能力。
4. **Harness**：管理对话、给模型工具、连接代码库的应用。
5. **Tools (Skills and MCP)**：告诉模型如何完成特定任务的知识，并为模型与 harness 提供相关上下文。

各层彼此独立，允许在每一层做更适合工作流的技术决策，并便于在新模型发布后快速实验。

**模型层**
- 大模型通常参数更多、训练计算更多，擅长多步推理与模糊/欠指定任务。文章举例 **Kimi K3**：1.8T总参数、104B激活参数；适用于重构认证系统、升级框架、审查PR、诊断SQL数据库突然变慢等。
- 小模型与大模型的差异更多在于能舒适处理多少模糊性，而非单纯质量。任务定义清晰、范围紧时，小模型可媲美大模型。文章举例 **GLM 5.3 Flash**：320B总参数、18B激活参数，比Kimi K3约6倍小、约20倍便宜；适合更新函数、写测试、解释错误、审查50行函数、重命名API等。
- 多数领先开源模型是 **Mixture-of-Expert (MoE)**，包含许多专家，但每个token只激活一小部分。
- 模型选择应像选工具：按任务在大小模型间分配。发现渠道包括 **The Open Frontier**、**Artificial Analysis** 等排行榜。文章提及当时流行开源模型：**GLM 5.3 Flash、DeepSeek V4 Flash、Kimi K3、MiniMax M3**，但变化很快。

**推理提供商**
- 云推理提供商/云网关：发送API请求，由提供商在GPU上运行模型，按输入与输出token付费。
- 适合实验：创建API key、指定模型名、发送请求。文中提到 **Together AI** 等提供大目录，单一账户可访问多种大小模型。
- 同一模型版本与采样设置下，不同提供商结果一般相似，但性能、价格、延迟、API功能可能不同。

**网关和路由器**
- 由于模型并非所有推理提供商都托管，网关/路由器聚合多个提供商，提供单一API，可路由请求、比较价格与延迟、切换模型而不改代码。
- 云网关示例：**OpenRouter**、**Vercel AI Gateway**。
- 本地/自有服务器路由器示例：**LiteLLM**，提供单一API端点，在已设置的多个提供商账户间路由。

**Harness**
- 用户交互的部分，通常本地运行，位于用户、代码库与模型之间；维护对话，并给模型工具。
- 示例流程：问“认证在代码库哪里处理？”→ harness 发给模型 → 模型要求搜索 `auth`、`session`、`login` → harness 在本机运行搜索并返回结果 → 模型要求读取文件 → harness 把文件内容加入对话 → 数轮后模型回答。
- 关键：模型不直接搜索文件系统或执行shell命令；模型决定，harness执行。因此编码agent质量不只取决于模型，也取决于 harness 能否暴露工具、收集上下文、管理长对话、应用补丁等。来源摘录在此处截断，后续内容待核实。

**工具（Skills和MCP）**
- 知识层，告诉模型如何做特定任务，包括给模型和 harness 访问相关上下文。

## 主要结果或产业意义
- 开源模型质量缩小与闭源模型差距，使更多开发者与组织关注所有权、控制权和经济性。
- 分层独立是核心设计：新模型出现时，如果替换只需几分钟而非重建工作流，就能真正实验新模型。
- 模型选择从“找最好模型”转为“按任务选工具”；大模型处理复杂/模糊任务，小模型处理明确/狭窄任务，以换取速度和成本。
- 网关/路由器减少对单一推理提供商的依赖，支持在闭源与开源模型之间路由。
- Harness 成为 agent 质量的关键变量，而不仅是模型本身。

## 为什么重要
- 对应用开发者：无需训练模型、购买GPU或成为ML专家，也可采用开源模型进行 agentic software development。
- 对组织：分层可替换性降低切换成本，增加议价能力与技术控制，支持持续实验。
- 对产业：开源模型栈的成熟可能改变模型、推理、工具链之间的价值分配；推理提供商与网关/路由层的重要性上升。
- 与既有脉络的关系：已有卡片“AI本身不会改变你的业务，运行AI的系统才会”强调集成、可治理、持续改进的系统平台；本卡片是该论点的开源技术栈展开，增量在于给出 **Model → Inference → Gateways/Routers → Harness → Tools** 的五层视图，以及“新模型发布后快速替换而非重建工作流”的操作目标。与“CFO与AI新经济学”卡片相比，本卡片补充技术架构层面的成本/控制选择，但不涉及ROI度量框架。与NVIDIA Halos卡片无直接关系。

## 局限与不确定性
- 来源是 Together AI 博客文章，且抓取内容为摘录而非全文；harness 部分在“apply patches, d”处截断，后续内容待核实。
- 文章称五层栈为 **The MIGHT Stack**，但摘录未完整解释缩写与五层的对应关系，待核实。
- 来源标注发布日期为 9/9/2026，具体年份/日期待核实。
- 模型名称、参数、相对大小/成本数据（Kimi K3、GLM 5.3 Flash等）来自文章，未在材料中独立验证；模型版本与流行度可能快速变化。
- 文章提到 Together AI、OpenRouter、Vercel AI Gateway、LiteLLM 等产品，可能存在来源方推广倾向；具体定价、性能、许可证、安全与治理能力待核实。
- 文章未提供完整基准对比、部署成本、合规/数据治理细节；企业采用前需自行评估。

## 可用于图书/PPT/简报的角度
- 开源AI栈分层架构图：Model / Inference / Gateways & Routers / Harness / Tools。
- “从闭源到开源：迁移检查清单”：模型选型、推理提供商、网关/路由器、harness、工具与MCP。
- “模型不是赢家通吃，而是工具箱”：大模型 vs 小模型的成本、延迟、模糊性权衡。
- “为什么 harness 决定 agent 质量”：模型决定，harness 执行；工具暴露、上下文收集、长对话管理、补丁应用。
- “避免供应商锁定”：网关/路由器如何聚合多提供商、用单一API切换模型。
- “开源模型的 ownership/control/economics”：与已有系统平台、AI ROI卡片串联。
- 企业AI系统平台案例：将开源栈视为“运行AI的系统”的具体实现之一。

## 原始材料
- 英文标题：**The Open Source AI Stack**
- 来源：Together AI Blog
- 作者：Hassan El Mghari
- 来源标注发布日期：9/9/2026（待核实）
- URL：https://www.together.ai/blog/the-open-source-ai-stack
- 英文关键词：open source AI stack, models, inference, gateways, routers, harness, tools, Skills, MCP, agentic software development
- 材料类型：博客文章（抓取摘录，非全文；harness部分结尾不完整）