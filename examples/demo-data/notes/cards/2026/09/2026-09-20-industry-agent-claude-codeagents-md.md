---
book_potential: 4
collected_date: '2026-09-20'
confidence: 3
created_at: '2026-09-20T08:02:50+08:00'
date: '2026-09-20'
digest_item_index: 1
entities:
- m.sohu.com
id: 2026-09-20-industry-agent-claude-codeagents-md
importance: 4
industry_dimensions:
- company
keywords_en: &id001
- agent
novelty: 4
parent_source_title: 腾讯研究院AI速递 20260920
parent_source_url: https://m.sohu.com/a/1078322629_455313?scm=10001.325_13-325_13.0.0-0-0-0-0.5_1334
ppt_potential: 4
primary_source: true
public_brief_potential: 3
review_status: needs-review
source_type: chinese-media-digest-item
source_url: https://m.sohu.com/a/1078322629_455313?scm=10001.325_13-325_13.0.0-0-0-0-0.5_1334&digest_item=1
title_en: Claude Code兼容AGENTS.md，智能体共用项目指令
title_zh: Claude Code 兼容 AGENTS.md，智能体共用项目指令
topics: *id001
track: industry
---

# 知识卡片：Claude Code 兼容 AGENTS.md，智能体共用项目指令

## 一句话结论
材料显示，Claude Code 已兼容 AGENTS.md：当项目目录没有 CLAUDE.md 时会自动读取该文件，并可在 /config 切换；这降低了多工具项目维护两份指令文件的成本，但尚未实现技能目录统一。

## 事件概述或研究问题
- 在编码智能体生态中，项目级指令文件出现 CLAUDE.md 与 AGENTS.md 并存的局面。
- AGENTS.md 最初源自 OpenAI Codex，材料称其被官方称为“面向 Agent 的 README”。
- Shopify CEO 曾因兼容问题考虑内部禁用 Claude Code，并把维护两份文件称为“复杂性税”。
- 本条关注的核心问题是：兼容是否等于统一？材料给出的答案是否定的——兼容只解决指令文件读取，技能目录仍是两套。

## 方法/产品要点
- 触发条件：项目目录中没有 CLAUDE.md 时，Claude Code 自动读取 AGENTS.md。
- 行为切换：该行为可在 /config 中切换。
- 实现方式：材料称该能力基于内置 mod agents-md 实现，并公开源码。
- 边界：兼容不等于统一；.agents/skills 与 .claude/skills 仍是两套独立目录。
- 生态含义：项目指令文件正在从工具偏好变成代码库基础设施。

## 主要结果或产业意义
- 对使用 Claude Code 的团队：若项目已有 AGENTS.md，可能减少额外维护 CLAUDE.md 的需要，缓解“复杂性税”。
- 对多智能体工具生态：兼容性提升了项目指令文件的通用性，但技能/扩展目录未统一，跨工具迁移仍可能碎片化。
- 对代码库治理：项目根目录的 Agent 指令文件越来越像 README、CI 配置一样的基础设施，影响协作、权限与工具接入。
- 对厂商竞争：兼容其他工具来源的 AGENTS.md 可降低采用摩擦，但也意味着项目指令格式的锁定效应被削弱。

## 为什么重要
- 与已有 Claude 模型能力、Agent 产品形态类卡片相比，本条增量不在模型性能或终端入口，而在 Claude Code 的项目级指令文件兼容：竞争焦点进一步落到工作流标准与代码库基础设施。
- 当多个编码智能体并存时，项目指令文件是否兼容，关系到团队是否被迫维护多份文件、是否容易切换工具、以及代码库中的 Agent 上下文能否复用。
- “兼容不等于统一”提示：兼容层能降低摩擦，但标准、技能目录和权限模型若不统一，生态仍可能分裂。

## 局限与不确定性
- 材料未说明该兼容功能上线的具体版本、日期和适用范围，待核实。
- /config 中可切换的具体开关、默认值与影响范围，待核实。
- 内置 mod agents-md 的公开源码仓库、许可证和维护主体，待核实。
- AGENTS.md 的规范维护方、版本演进及“官方”具体所指，待核实。
- Shopify CEO 的姓名、表态时间、考虑禁用的具体原因及是否最终执行，待核实。
- .agents/skills 与 .claude/skills 是否会合并或互通，待核实。
- 其他主流编码智能体是否同步支持 AGENTS.md，材料未说明，待核实。

## 可用于图书/PPT/简报的角度
- “面向 Agent 的 README”：代码库文档的读者从人扩展到智能体。
- 多智能体工具的“复杂性税”：CLAUDE.md、AGENTS.md 并存带来的维护与治理问题。
- 兼容不等于统一：从平台标准竞争看 agent 生态的收敛与分裂。
- 代码库基础设施清单更新：README、CI、Dockerfile 之后，项目指令文件的位置。
- 企业 AI 编码工具选型：兼容性、切换成本与内部禁用风险。
- 智能体协作工作流：项目指令文件如何影响上下文、权限和可复现性。

## 原始材料
- 原始材料标题/栏目：腾讯研究院AI速递 20260920
- 相关条目：一、Claude Code兼容AGENTS.md，智能体共用项目指令
- 原始来源/转载页：https://m.sohu.com/a/1078322629_455313?scm=10001.325_13-325_13.0.0-0-0-0-0.5_1334&digest_item=1
- Parent digest：腾讯研究院AI速递 20260920
- Parent URL：https://m.sohu.com/a/1078322629_455313?scm=10001.325_13-325_13.0.0-0-0-0-0.5_1334
- 英文关键词：Claude Code, AGENTS.md, CLAUDE.md, /config, mod agents-md, OpenAI Codex, Shopify, .agents/skills, .claude/skills