---
auto_review_age_days: 1
auto_review_reasons:
- importance:3+6
- novelty:3+6
- confidence:2+4
- ppt_potential:3+3
- public_brief_potential:3+3
- topic_priority:5+10
- source_type:benchmark-update+2
- primary_source+2
- 'score>=28: 自动接受'
auto_review_score: 36
book_potential: 4
collected_date: '2026-07-07'
confidence: 2
created_at: '2026-07-07T10:13:31+08:00'
date: '2026-06-25'
entities:
- openrouter.ai
id: 2026-06-25-industry-benchmark-evaluation-agent-the-openrouter-mcp-server-connect-your-coding-ag
importance: 4
industry_dimensions:
- company
keywords_en: &id001
- benchmark-evaluation
- agent
novelty: 4
ppt_potential: 4
primary_source: true
public_brief_potential: 2
review_status: accepted
reviewed_at: '2026-07-08T15:27:10+08:00'
reviewed_by: auto
source_type: benchmark-update
source_url: https://openrouter.ai/blog/announcements/openrouter-mcp-server
title_en: The OpenRouter MCP Server Connect your coding agent to OpenRouter's live
  model catalog, benchmarks, docs, and test inference, all without leaving your editor.
  June 25, 2026
title_zh: OpenRouter MCP 服务器
topics: *id001
track: industry
---

# 知识卡片：OpenRouter MCP 服务器

**一句话结论**：OpenRouter MCP 服务器让编码代理无需离开编辑器即可实时查询模型目录、基准测试、定价、文档并执行测试推理，从而基于最新数据推荐最佳模型。

**事件概述**  
2026 年 6 月 25 日，OpenRouter 发布了一个 MCP（Model Context Protocol）服务器，旨在解决编码代理在模型选择上依赖过时训练数据的问题。该服务器提供一组工具（如模型搜索、基准排名、测试推理），使代理能够根据实时数据（如价格、延迟、AI 智能评分）推荐模型，并将集成过程简化为一键安装。

**方法/产品要点**  
- 产品名称：OpenRouter MCP Server  
- 安装方式：支持 Claude Code、Codex CLI、Cursor、Claude Desktop/Web 等客户端，通过一行命令或配置文件添加远程 MCP 服务器 URL（`https://mcp.openrouter.ai/mcp`）。  
- 关键工具：
  - `models-list`：按价格、上下文长度、模态、提供商等筛选实时模型目录。
  - `model-get`：获取单个模型的完整能力、定价、上下文窗口。
  - `model-endpoints`：按提供商查看价格、延迟、吞吐量、数据策略。
  - `benchmarks`：来自 Artificial Analysis 和 Design Arena 的第三方质量评分。
  - `rankings-daily`：按 token 流量显示最常用和趋势模型。
  - `chat-send`：向任意模型发送测试提示，返回响应和成本（需付费）。
  - `generation-get`：查询特定生成的成本、token 计数和服务提供商。
  - `docs-search`：全文搜索 OpenRouter 文档。
  - `credits-get`：查询账户剩余额度。
  - `providers-list`：列出可用于路由偏好的提供商。
  - `app-rankings`：按类别显示驱动 OpenRouter 流量的应用排名。
- 身份验证：通过 OAuth 流程生成专用 API 密钥，7 天有效，默认消费上限 10 美元，可在仪表板撤销。
- 数据来源：实时模型目录、Artificial Analysis 智能分数、Design Arena ELO 排名、OpenRouter 自身排名。

**主要结果或产业意义**  
- 使编码代理能在几分钟内完成过去需 15 分钟上下文切换的模型选型、测试和集成流程。  
- 示例推荐：针对“结构化 JSON 提取”场景，代理推荐 `google/gemini-3-flash-preview`，价格为 $0.10/M 输入 token，138k 上下文。  
- 侧边对比测试：支持同时向多个模型（如 Claude Opus 4.8、GPT-5.5、DeepSeek V4 Pro）发送相同提示，比较成本、速度和结果质量。  
- 模型 slug 支持后缀：`:online`（网络搜索）、`:nitro`（速度）、`:floor`（最低价）、`:free`（免费端点），使代理可测试变体。  
- 该工具定位为开发辅助，不取代 OpenRouter API；应用程序仍应直接调用 OpenRouter API。

**为什么重要**  
编码代理在编写代码时表现优异，但模型选择依赖于过时的训练数据，无法反映真实成本、性能和最新排名。OpenRouter MCP 服务器将实时数据直接注入代理决策流程，避免了手动切换浏览器、查阅文档和运行测试的步骤，大幅提升开发效率。

**局限与不确定性**  
- 所有工具（除 `chat-send` 外）均为只读查询，`chat-send` 会消耗 MCP 密钥余额产生费用。  
- 源代码不会自动发送至外部，除非用户明确在 `chat-send` 中包含。  
- 某些组织可能不允许添加自定义连接器，导致 Claude Desktop/Web 中选项不可见。  
- 密钥有效期仅 7 天，需在到期前重新授权。  
- 文章中提到的模型（如 GLM-5.2、Claude Opus 4.8、GPT-5.5、DeepSeek V4 Pro、google/gemini-3-flash-preview）其存在性和性能为示例性描述，具体事实性需与 OpenRouter 官方确认。

**可用于图书/PPT/简报的角度**  
- 如何让 AI 编码代理实时“自我检索”最优模型？OpenRouter MCP 的架构与实现。  
- 从“猜测”到“决策”：AI 代理工具链中数据新鲜度的重要性。  
- 开发者体验的进化：一体化 MCP 服务器如何消除上下文切换。  
- 行业趋势：MCP 协议在 AI 代理生态中的角色与扩展案例。

**原始材料**  
- 原文标题：The OpenRouter MCP Server — OpenRouter Blog  
- 原文描述：Connect your coding agent to OpenRouter's live model catalog, benchmarks, docs, and test inference, all without leaving your editor.  
- 来源：https://openrouter.ai/blog/announcements/openrouter-mcp-server  
- 发布日期：June 25, 2026  
- 轨迹：industry | 主题：benchmark-evaluation, agent