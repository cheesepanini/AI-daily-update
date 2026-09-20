---
book_potential: 3
collected_date: '2026-09-20'
confidence: 2
created_at: '2026-09-20T08:04:50+08:00'
date: '2026-09-20'
digest_item_index: 4
entities:
- m.sohu.com
id: 2026-09-20-industry-benchmark-evaluation-minimaxcode-cli-76-7
importance: 3
industry_dimensions:
- company
keywords_en: &id001
- benchmark-evaluation
novelty: 4
parent_source_title: 腾讯研究院AI速递 20260920
parent_source_url: https://m.sohu.com/a/1078322629_455313?scm=10001.325_13-325_13.0.0-0-0-0-0.5_1334
ppt_potential: 4
primary_source: true
public_brief_potential: 3
review_status: needs-review
source_type: chinese-media-digest-item
source_url: https://m.sohu.com/a/1078322629_455313?scm=10001.325_13-325_13.0.0-0-0-0-0.5_1334&digest_item=4
title_en: MiniMax正式开源Code CLI，评测通过率达76.7%
title_zh: MiniMax 开源 Code CLI，FrontierHarness Eval 通过率 76.7%
topics: *id001
track: industry
---

# 知识卡片：MiniMax 开源 Code CLI，FrontierHarness Eval 通过率 76.7%

**一句话结论**  
MiniMax 发布并以 MIT 协议开源 Code CLI v0.4.12；材料称其在第三方 FrontierHarness Eval 的 30 道任务中通过 23 道，通过率 76.7%，成功任务耗时中位数 4 分 33 秒，两项指标优于报告所列公开基线，但基线和方法细节待核实。

**事件概述或研究问题**  
- 材料来自《腾讯研究院AI速递 20260920》第四条。  
- MiniMax 发布 Code CLI v0.4.12，并以 MIT 协议开源。  
- 该组件是 MiniMax Code 客户端核心部分，可通过一行安装脚本快速体验。  
- 在第三方 FrontierHarness Eval 的 30 道任务评测中，通过 23 道，通过率 76.7%；成功任务耗时中位数 4 分 33 秒。  
- 材料称两项指标均优于报告所列公开基线。  
- 官方称开源意在让开发者审视工具调用与权限处理、构建可靠的企业级应用，并由社区参与发现问题与完善安全机制。

**方法/产品要点**  
- 产品/组件：MiniMax Code CLI v0.4.12。  
- 开源许可：MIT。  
- 定位：MiniMax Code 客户端核心部分。  
- 体验方式：一行安装脚本快速体验；具体命令、平台与依赖待核实。  
- 评测框架：第三方 FrontierHarness Eval，30 道任务。  
- 核心指标：通过任务数/通过率、成功任务耗时中位数。  
- 官方期望：工具调用、权限处理、企业级可靠性、社区安全审计。

**主要结果或产业意义**  
- 报告数字：23/30 通过，通过率 76.7%；成功任务中位耗时 4 分 33 秒。  
- 若评测口径可靠，这说明 Code CLI 在代码/代理任务上具备一定完成率与速度，可作为 coding agent 工具链的竞争力信号。  
- MIT 开源降低审查、集成与二次开发门槛，有利于把 CLI 作为企业 Agent 基础设施的一部分。  
- 在 benchmark-evaluation 脉络中，本条补充了“代码 CLI + 第三方 harness”的评测数据点；与已有关于长周期知识工作评估、模型融合的卡片不同，本条核心增量是 CLI 组件开源及其通过率/耗时指标。

**为什么重要**  
- CLI 是 coding agent 接触文件系统、命令、工具和权限的入口，其工具调用与权限处理直接关系企业落地。  
- 开源使安全机制、权限边界和工具调用流程可被开发者与社区审视，符合企业级 Agent 对可审计性与可控性的需求。  
- “通过率 + 耗时中位数”同时呈现效果与效率，比单纯宣称能力更有部署参考价值，但需要方法论与基线支撑。  
- 与既有 benchmark-evaluation 卡片相比，本条增量是具体 CLI 工具的开源动作和第三方评测数字，而非长周期项目评估或模型融合方法。

**局限与不确定性**  
- FrontierHarness Eval 的任务类型、评分规则、运行环境、重复次数、基线名单与具体数值未在材料中给出，待核实。  
- “优于报告所列公开基线”是材料/报告中的说法，缺少基线数据和方法细节，待核实。  
- 4 分 33 秒仅描述成功任务耗时中位数；失败任务耗时、是否含安装/网络/模型延迟、成本与 token 消耗未说明，待核实。  
- 一行安装脚本的具体命令、支持平台、依赖、权限范围与安全风险未给出，待核实。  
- MIT 开源的具体仓库、组件边界、是否包含模型权重或完整客户端、托管地址未给出，待核实。  
- 官方称用于企业级应用与社区安全完善，但审计流程、漏洞响应机制与实际企业案例未说明，待核实。  
- Code CLI 所调用的模型版本、后端 API、价格与限制未在材料中说明，待核实。

**可用于图书/PPT/简报的角度**  
- “CLI 成为 coding agent 的权限边界与基础设施入口”。  
- “开源作为企业信任策略：让工具调用与权限处理可被审计”。  
- “如何读 Agent 评测：通过率、成功任务耗时中位数、公开基线与可复现性”。  
- “从代码助手到可执行代理：第三方 harness 评测的价值与局限”。  
- 可结合同一速递中 Claude Code 兼容 AGENTS.md 的条目，讨论项目指令文件与 Agent 工具链的基础设施化趋势；但 MiniMax Code CLI 是否支持同类机制，材料未说明，待核实。

**与既有脉络的关系**  
- 已有相关卡片涉及 OpenRouter MCP、AA-Briefcase、模型融合等。本条不重复这些事实，增量在于：一个具体代码 CLI 组件以 MIT 开源，并披露第三方 harness 的通过率与成功任务耗时中位数。它属于 benchmark-evaluation 脉络，但评测对象和任务范围与 AA-Briefcase 的长周期知识工作不同，不能直接横向等同。

**原始材料**  
- 来源标题：腾讯研究院AI速递 20260920  
- 原始条目：MiniMax正式开源Code CLI，评测通过率达76.7%  
- 英文产品/关键词：MiniMax Code CLI、Code CLI v0.4.12、MIT、FrontierHarness Eval、benchmark-evaluation  
- 英文标题：材料未提供独立英文标题。  
- URL：https://m.sohu.com/a/1078322629_455313?scm=10001.325_13-325_13.0.0-0-0-0-0.5_1334&digest_item=4  
- Parent URL：https://m.sohu.com/a/1078322629_455313?scm=10001.325_13-325_13.0.0-0-0-0-0.5_1334