---
book_potential: 1
collected_date: '2026-09-20'
confidence: 1
created_at: '2026-09-20T08:04:09+08:00'
date: '2026-09-20'
digest_item_index: 3
entities:
- m.sohu.com
id: 2026-09-20-industry-agent-qwen3-8-omni-flash-agent
importance: 3
industry_dimensions:
- company
keywords_en: &id001
- agent
novelty: 4
parent_source_title: 腾讯研究院AI速递 20260920
parent_source_url: https://m.sohu.com/a/1078322629_455313?scm=10001.325_13-325_13.0.0-0-0-0-0.5_1334
ppt_potential: 2
primary_source: true
public_brief_potential: 1
review_status: needs-review
source_type: chinese-media-digest-item
source_url: https://m.sohu.com/a/1078322629_455313?scm=10001.325_13-325_13.0.0-0-0-0-0.5_1334&digest_item=3
title_en: 千问推出Qwen3.8-Omni-Flash，全模态Agent上阵
title_zh: 千问推出 Qwen3.8-Omni-Flash，全模态 Agent 上阵
topics: *id001
track: industry
---

# 知识卡片：千问推出 Qwen3.8-Omni-Flash，全模态 Agent 上阵

## 一句话结论
腾讯研究院 AI 速递称，千问推出 Qwen3.8-Omni-Flash，支持文本、图像、音频、视频输入与 1M 长上下文，主攻音视频 Agent 工作流，并在 30 项评测中较上代平均提升超 26%。

## 事件概述或研究问题
- 材料来源为“腾讯研究院AI速递 20260920”，第三条标题为“千问推出Qwen3.8-Omni-Flash，全模态Agent上阵”。
- 该模型被描述为面向全模态 Agent 的产品，重点覆盖音视频理解与端到端任务。
- 材料列出的典型工作流包括：视频剪辑、短剧翻译配音、电影解说、会议纪要。
- 其研究/产品问题是：如何用统一模型处理多模态输入，并在音视频场景中完成 Agentic 任务编排与执行。
- 模型参数规模、架构、训练数据、发布时间、开放范围等，材料未说明，待核实。

## 方法/产品要点
- 输入模态：文本、图像、音频、视频。
- 上下文长度：1M 长上下文。
- Agent 能力：材料称 Agentic 理解准确率升至 67.8。
- 音频能力：材料称整体超过 Gemini 3.8 Flash。
- 生态组件：同步扩展并开源 Qwen-MM-Plugins 与 Qwen-Live Harness。
- 价格变化：材料称每小时音频输入价格降幅超 98%，音视频输入降幅超 93%。
- 模型是否开放权重、是否可商用、API 名称与定价绝对值、Qwen-MM-Plugins 与 Qwen-Live Harness 的具体功能与开源协议，均待核实。

## 主要结果或产业意义
- 材料称，Qwen3.8-Omni-Flash 在 30 项评测中较上代平均提升超 26%。
- 音频能力被描述为整体超过 Gemini 3.8 Flash。
- Agentic 理解准确率达到 67.8。
- 若音频与音视频输入价格大幅下降属实，可能降低音视频 Agent 的规模化调用成本。
- 材料列出的视频剪辑、短剧翻译配音、电影解说、会议纪要等工作流，指向模型从“多模态理解”向“内容生产与处理”延伸。
- 评测集细节、基线设置、第三方复现情况，材料未提供，待核实。

## 为什么重要
- 全模态输入、长上下文与 Agent 工作流结合，是模型竞争从文本、代码向音视频生产链延伸的一个信号。
- 开源 Qwen-MM-Plugins 与 Qwen-Live Harness，可能降低开发者接入音视频 Agent 的门槛，但实际生态影响待观察。
- 价格降幅若成立，会影响会议纪要、短剧本地化、视频剪辑等场景的成本结构。
- 本条与既有 Qwen3.8-Flash-Next 卡片形成同系列脉络：后者聚焦 agentic coding 与长上下文高并发，本条转向全模态音视频 Agent；但两者是否同代、是否共享架构或权重，材料未说明，待核实。

## 与既有脉络的关系
- 已有卡片记录 Qwen3.8-Flash-Next 面向 agentic coding 与高并发长上下文场景。
- 本条增量在于：Qwen3.8-Omni-Flash 转向文本、图像、音频、视频全模态输入，并强调音视频 Agent 工作流、Agentic 理解准确率与输入价格下降。
- 两者是否属于同一模型家族的不同分支、是否共享训练或推理技术，无法从当前材料确认，待核实。

## 局限与不确定性
- 材料为二手速递，未附原始技术报告、模型卡或官方博客链接。
- “30 项评测平均提升超 26%”缺少评测集名称、基线设置、统计口径与复现条件。
- “音频能力整体超过 Gemini 3.8 Flash”缺少具体评测任务与对比版本。
- “上代”具体指哪一代模型，待核实。
- 价格降幅的对比基准、计费单位、是否限时优惠，待核实。
- Qwen-MM-Plugins 与 Qwen-Live Harness 的功能边界、维护主体、开源协议，待核实。
- 实际音视频工作流的输出质量、延迟、吞吐、版权与隐私合规，待核实。
- 模型是否开放权重、是否可商用、区域可用性，待核实。

## 可用于图书/PPT/简报的角度
- 从“多模态输入”到“音视频 Agent 工作流”的产品范式迁移。
- 模型价格战向音频、视频输入延伸：降幅超 98% 与超 93% 的成本叙事。
- 开源 Harness 与插件作为 Agent 生态入口：Qwen-MM-Plugins、Qwen-Live Harness。
- 音视频内容生产链的 AI 化：剪辑、翻译配音、电影解说、会议纪要。
- 与 Qwen3.8-Flash-Next 的系列化对比：编码 Agent 与全模态 Agent 的分工。
- 风险提示：评测口径、真实工作流质量、版权与合规不确定性。

## 原始材料
- 原始来源标题：腾讯研究院AI速递 20260920
- 相关条目：三、千问推出Qwen3.8-Omni-Flash，全模态Agent上阵
- Parent URL: https://m.sohu.com/a/1078322629_455313?scm=10001.325_13-325_13.0.0-0-0-0-0.5_1334
- URL: https://m.sohu.com/a/1078322629_455313?scm=10001.325_13-325_13.0.0-0-0-0-0.5_1334&digest_item=3
- 英文标题/模型名：Qwen3.8-Omni-Flash
- 英文关键词：Omni, Agent, Agentic, Qwen-MM-Plugins, Qwen-Live Harness, Gemini 3.8 Flash, 1M context