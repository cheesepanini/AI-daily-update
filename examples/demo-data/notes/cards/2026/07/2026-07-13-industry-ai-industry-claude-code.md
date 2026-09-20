---
auto_review_age_days: 1
auto_review_reasons:
- topic_priority:5+10
- source_type:chinese-media-2
- primary_source+2
- 'score<=22: 自动拒绝'
auto_review_score: 10
book_potential: 0
collected_date: '2026-07-13'
confidence: 0
created_at: '2026-07-13T18:03:13+08:00'
date: '2026-07-13'
entities:
- www.qbitai.com
id: 2026-07-13-industry-ai-industry-claude-code
importance: 0
industry_dimensions:
- company
keywords_en: &id001
- ai-industry
novelty: 0
ppt_potential: 0
primary_source: true
public_brief_potential: 0
review_status: rejected
reviewed_at: '2026-07-14T08:05:46+08:00'
reviewed_by: auto
source_type: chinese-media
source_url: https://www.qbitai.com/2026/07/448925.html
title_en: Claude Code砸的坑，蚂蚁安全在尝试填上
title_zh: Claude Code砸的坑，蚂蚁安全在尝试填上
topics: *id001
track: industry
---

# 知识卡片：Claude Code砸的坑，蚂蚁安全在尝试填上

**一句话结论**  
蚂蚁安全开源了面向智能体安全的双模推理护栏框架 SingGuard-NSFA 和面向多模态大模型的安全框架 SingGuard，旨在将安全检测前置到 AI 执行之前，从“打补丁”转向定义可扩展的安全基础设施。

**事件概述**  
2026 年，工信部 NVDB 平台发布风险预警，指出 Claude Code 存在安全后门隐患；同期 OpenClaw 也屡曝高危险漏洞。Agent 产品在快速普及后漏洞频发，行业意识到传统内容安全审核无法应对 AI “行为”风险。蚂蚁安全近期开源两大安全框架，试图从底层解决智能体执行前的安全拦截与多模态感知风险。

**方法/产品要点**  
- **SingGuard-NSFA**：面向智能体安全，提供 0.8B、2B、4B、9B 四个尺寸。核心思想是将安全检查前置到智能体执行之前，并在请求拦截和响应兜底两端设卡。  
  - 基于 NSFA 风险分类体系（以 CIA 三元组 + OWASP 指南为理论底座）和多语种评测基准。  
  - 双模推理：生成式模式输出链式推理分析（用于离线审计）；判别式模式直接输出风险置信度，延迟 45～57ms（用于实时拦截）。  
  - 骨干网络冻结，外挂轻量分类头，新增风险只需补训小头，支持可扩展；可当插件用（如给 Llama Guard 3 加分类头，用户请求安全 F1 提升 17.6 个百分点）。  
- **SingGuard**：面向多模态大模型，提供 0.8B、2B、4B、8B 四个尺寸。  
  - 安全规则作为运行时输入，不同业务域可现场下发红线，模型逐条判定是否违规。  
  - 快慢思考分工：快思考低延迟秒判，慢思考逐规则深度推理，通过 early exit 自动切换。  
  - RI-Mask 机制：共享图文上下文只编码一次，多条规则并行判断，多模态推理最高提速 5 倍以上。

**主要结果或产业意义**  
- SingGuard-NSFA 在用户请求安全、模型响应安全、跨数据集泛化三大评测基准上均取得 SOTA。最小 0.8B 模型可比肩 8B 竞品，9B 模型泛化 F1 达 91.29%，精度与召回均衡。  
- SingGuard 通过 RI-Mask 实现多模态推理效率提升 5 倍以上。  
- 蚂蚁智能体安全产品已通过信通院泰尔实验室最高等级评级，显示工程落地进展。  
- 行业趋势：从漏洞修补转向建设可定义安全边界、应对未知风险和规则变动的底层框架。

**为什么重要**  
AI 风险源头已从内容转向行为（如恶意工具调用、代码生成、提示注入），传统内容安全分类体系无法覆盖。蚂蚁的开源框架强调**过程可解释**（违反哪条规则、依据是什么）和**新增风险可扩展**（轻量扩展不影响已有能力），为未来智能体运行提供安全基础设施，而非零散补丁。

**局限与不确定性**  
- 材料未提及框架在实际大规模生产部署中的性能开销、误报率、跨场景适应性等具体局限，待核实。  
- 框架的行业采纳程度和与其他安全体系的互操作性尚不清楚，待核实。  
- 文中称“骨干网络冻结”可支持新风险扩展，但未知需补训多少数据或对原有能力有无副作用，待核实。

**可用于图书/PPT/简报的角度**  
- **AI 安全新范式**：从“内容审核”到“行为安全”，对比传统与框架式安全方案。  
- **蚂蚁安全的技术路线**：从支付安全、风控到 AI 安全，展示体系化演进。  
- **Agent 治理案例**：以 Claude Code、OpenClaw 漏洞为引，说明开源框架如何填补空白。  
- **多模态风险控制**：利用运行时规则注入和 RI-Mask 解决多模态并行审核瓶颈。

**原始材料**  
URL: https://www.qbitai.com/2026/07/448925.html  
英文标题: Claude Code砸的坑，蚂蚁安全在尝试填上  
英文关键词: AI Security, SingGuard-NSFA, SingGuard, Agent Safety, Multi-modal Security