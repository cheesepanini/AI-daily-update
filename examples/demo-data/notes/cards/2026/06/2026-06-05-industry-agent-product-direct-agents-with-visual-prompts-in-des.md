---
auto_review_age_days: 1
auto_review_reasons:
- importance:3+6
- novelty:3+6
- confidence:2+4
- ppt_potential:3+3
- public_brief_potential:3+3
- topic_priority:5+10
- source_type:company-news+2
- primary_source+2
- 'score>=28: 自动接受'
auto_review_score: 36
book_potential: 4
collected_date: '2026-07-07'
confidence: 5
created_at: '2026-07-07T11:15:33+08:00'
date: '2026-06-05'
entities:
- cursor.com
id: 2026-06-05-industry-agent-product-direct-agents-with-visual-prompts-in-des
importance: 4
industry_dimensions:
- company
keywords_en: &id001
- agent
novelty: 4
ppt_potential: 4
primary_source: true
public_brief_potential: 4
review_status: accepted
reviewed_at: '2026-07-08T15:27:10+08:00'
reviewed_by: auto
source_type: company-news
source_url: https://cursor.com/blog/design-mode
title_en: Product Direct agents with visual prompts in Design Mode Point, draw, or
  narrate UI changes in the browser while agents edit the code underneath. Erik, Ian
  & Ryo · 6m 6 min read
title_zh: Direct agents with visual prompts in Design Mode
topics: *id001
track: industry
---

# 知识卡片：Direct agents with visual prompts in Design Mode

## 一句话结论
Cursor 的 Design Mode 更新让用户可以通过点击、绘制或语音直接在浏览器中指示 agent 修改 UI，agent 自动编辑底层代码，从而大幅缩短从观察到修改的反馈循环。

## 事件概述
Cursor 于 2026 年 6 月 5 日发布了 Design Mode 的更新。该功能允许用户在使用 Cursor 浏览器时，直接点击页面元素、在界面上绘制区域或使用语音描述修改，agent 会获取所需的上下文（包括元素标识、代码、布局等）并自动编辑代码。用户可以在前一个编辑尚未完成时发送下一个指令，支持多子 agent 并行管理。

## 方法/产品要点
- **交互方式**：点击元素、多选元素、在界面上绘制（圈选、框选）、语音输入。
- **上下文信号**：被选中元素的 xpath、组件、属性、计算样式、fiber 树中的 props，以及一张用于空间上下文的屏幕截图。
- **底层模型**：Composer 2.5，专为快速且精准的 UI 修改设计，支持热重载。
- **工作流**：用户可以在一个编辑未完成时发送下一个，agent 在后台并行处理，应用实时更新。

## 主要结果或产业意义
Design Mode 使设计迭代变得更加紧密和高效，尤其适合设计师、产品经理和前端开发者。它让“注意→修改”的循环在运行中的应用内直接完成，无需离开产品环境。这种空间化的交互方式比纯文本聊天更直观，有望成为 AI 辅助 UI 开发的主流范式。

## 为什么重要
- 它缩小了用户所见与 agent 理解之间的距离，通过视觉和语音等多模态提示降低沟通成本。
- 支持并行多编辑，提升了迭代速度。
- 体现了“全栈 AI 代理”从纯文本对话走向空间化、多模态交互的趋势。

## 局限与不确定性
- 材料未提及对复杂动画页面、自定义组件或非标准框架的支持程度，有待进一步验证。
- 语音输入的准确性和多语言支持情况待核实。
- 对于大型页面或高频编辑场景下的性能表现未作说明。

## 可用于图书/PPT/简报的角度
- **主题**：AI 辅助开发的交互范式演变——从“聊天”到“空间化提示”。
- **案例**：展示 Design Mode 如何让非开发者也能通过点、画、说直接参与 UI 修改，降低协作门槛。
- **启示**：未来软件构建中，用户将能在抽象层面（自然语言/视觉）和细节层面（代码）之间无缝切换，而 agent 负责中间转换。

## 原始材料
- **URL**: https://cursor.com/blog/design-mode
- **标题**: Direct agents with visual prompts in Design Mode · Cursor
- **描述**: Point, draw, or narrate UI changes in the browser while agents edit the code underneath.
- **作者**: Erik Nilsson, Ian Huang & Ryo Lu
- **发布时间**: 2026 年 6 月 5 日
- **分类**: product (industry track)
- **英文关键词**: Design Mode, visual prompts, agent, UI editing, Cursor