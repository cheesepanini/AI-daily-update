---
auto_review_age_days: 1
auto_review_reasons:
- importance:3+6
- novelty:4+8
- confidence:3+6
- ppt_potential:4+4
- public_brief_potential:3+3
- topic_priority:5+10
- source_type:benchmark-update+2
- primary_source+2
- 'score>=28: 自动接受'
auto_review_score: 41
book_potential: 3
collected_date: '2026-08-21'
confidence: 3
created_at: '2026-08-21T08:16:22+08:00'
date: '2026-08-03'
entities:
- openrouter.ai
event_date: '2026-08-03'
id: 2026-08-03-industry-benchmark-evaluation-ori-eval-find-the-best-model-for-what-you-re-bui
importance: 3
industry_dimensions:
- company
keywords_en: &id001
- benchmark-evaluation
novelty: 4
ppt_potential: 4
primary_source: true
public_brief_potential: 3
review_status: accepted
reviewed_at: '2026-08-22T08:19:18+08:00'
reviewed_by: auto
source_type: benchmark-update
source_url: https://openrouter.ai/blog/announcements/ori-eval
title_en: 'Ori Eval: Find the Best Model for What You''re Building August 3, 2026'
title_zh: Ori Eval：为你的应用找到最合适的模型
topics: *id001
track: industry
---

# 知识卡片：Ori Eval：为你的应用找到最合适的模型

**英文标题**：Ori Eval: Find the Best Model for What You're Building  
**英文关键词**：Ori Eval; model evaluation; LLM judge; OpenRouter; agent evals  
**原始来源**：URL: https://openrouter.ai/blog/announcements/ori-eval

## 一句话结论
Ori Eval 是 OpenRouter 推出的评估工具：它用你自己的提示词运行你的 agent，断言 agent 调用了哪些工具，并用 LLM 评判开放式答案，从而帮你找到“最适合你正在构建的东西”的单一模型，并给出可验证的证据。

## 事件概述
OpenRouter 于 2026 年 8 月 3 日发布 Ori Eval。官方背景是：当前有超过 500 个模型可选，但实际选型常依赖社交媒体推荐、基准排行榜或“某个模型目前最强”的直觉。这些方式有一个共同限制：基准测量的是固定任务集，推荐反映的是别人的应用，都无法说明模型在你的应用、你的 harness、你的数据、你的提示词下表现如何。Ori Eval 的目标是让模型选择变成一种可重复、可证明的流程。

## 方法/产品要点
- 启动方式：告诉你的 coding agent 运行 `curl -fsSL https://openrouter.ai/skills/spawn-ori-eval` 并按输出指引操作；如果使用 OpenRouter MCP 服务器，可运行 `/spawn-ori-eval`。
- 工作流程：Ori Eval 扫描你的代码库，找出所有调用模型的位置，并询问你关心什么（成本、性能、延迟、速度、工具调用准确性等），然后选出 5 个符合要求的最新模型并与你确认，最后编写 `review.eval.ts` 文件并并行运行你的 agent 与候选模型，返回一个包含 model、catch、p50、$/PR、result 等列的对比表。
- eval 文件是代码：一个 `*.eval.ts` 文件用 `bun test` 运行，检查三件事：agent 调用了哪些工具、避免了哪些工具，以及答案质量。开放式答案用 LLM-as-a-judge 评分，并可设置评分标准与最低分。
- 一致性：Ori 在运行期间会固定 harness、模型和 effort，环境不变，因此如果 eval 结果发生变化，可以归因于模型变化。
- 覆盖范围：Ori Eval 通过 OpenRouter 路由，因此模型比较可覆盖所有模型和实验室；用户无需会写 eval，Ori Eval 会代写 eval 文件。
- CI 集成：可将 `ori eval` 加入 GitHub Actions workflow，失败即阻止构建；也可定期运行，当新模型表现更好时自动开 PR。

## 主要结果或产业意义
Ori Eval 把“哪个模型最适合我正在构建的东西”这一主观问题变成“有证明的答案”。它能将自然语言描述的 bug 转化为可测试的断言：例如“支持 agent 不检查订单就发退款”，Ori Eval 会写出一个断言要求 `lookup_order` 被调用；eval 先失败证明 bug 存在，修复后 eval 通过，断言留存在测试套件中防止回归。据博客介绍，一位早期 beta 测试者已开始每月运行模型比较，新模型优于现有模型时自动生成 PR。

## 为什么重要
Ori Eval 不是又一个静态排行榜，而是把评估嵌入到开发流程中：它扫描真实代码库、基于真实调用场景生成测试，并让回归检查成为 CI 的一部分。它延续了 OpenRouter 从模型聚合平台向智能时代基础设施演进的方向。与既有脉络相比，增量信息在于：相比 Artificial Analysis Optima 提供的自定义基准构建工具，Ori Eval 更聚焦 agent 的代码级行为（工具调用断言 + LLM 评判），并直接与 GitHub Actions、OpenRouter MCP 服务器集成。

## 局限与不确定性
- 博客未说明 Ori Eval 的公开定价、是否所有模型均可评估、是否支持所有编程语言/框架。
- 示例表格中的具体数值（如 catch 率、p50、$/PR）来自演示用例，不代表对所有模型的实测结果。
- 安装方式目前是通过 curl 脚本安装 Ori，运行需要 Bun；具体安全审计、维护状态和长期支持情况待核实。
- LLM-as-a-judge 的评分准确性、在不同任务上的偏差、以及 Orient 固定 harness 的具体实现细节，均待核实。

## 可用于图书/PPT/简报的角度
- 从“没有最好的模型，只有最适合你构建场景的模型”切入，说明如何把模型选型从“猜”变成“可验证的测试”。
- 展示 eval 示例：断言 agent 调用了 `search`、未调用 `delete_file`、最终 `toComplete()`，说明工具级断言如何检查 agent 行为。
- 演示“bug 变成测试”的工作流：先用失败断言锁定 bug，修复后断言通过并留在测试套件中。
- 用多模型对比表来讨论成本、延迟、成功率之间的权衡，以及如何基于自己的数据做决策。

## 与既有脉络的关系
- 相比 Artificial Analysis Optima（2026-08-14）的自定义基准，Ori Eval 更强调代码库扫描、工具调用断言和 CI 回归阻止。
- 与 OpenRouter MCP 服务器（2026-06-25）集成：MCP 用户可通过 `/spawn-ori-eval` 命令直接启动。
- 延续 OpenRouter 品牌焕新（2026-07-13）所暗示的战略方向：从聚合模型到为开发者提供可证明的选型基础设施。