---
auto_review_age_days: 1
auto_review_reasons:
- importance:4+8
- novelty:4+8
- confidence:3+6
- ppt_potential:5+5
- public_brief_potential:4+4
- topic_priority:5+10
- source_type:chinese-media-digest-item-2
- primary_source+2
- 'score>=28: 自动接受'
auto_review_score: 41
book_potential: 4
collected_date: '2026-07-14'
confidence: 3
created_at: '2026-07-14T08:04:53+08:00'
date: '2026-07-14'
digest_item_index: 5
entities:
- m.sohu.com
id: 2026-07-14-industry-agent-cpu-4agent
importance: 4
industry_dimensions:
- company
keywords_en: &id001
- agent
novelty: 4
parent_source_title: 腾讯研究院AI速递 20260714
parent_source_url: https://m.sohu.com/a/1049851171_455313?scm=10001.325_13-325_13.0.0-0-0-0-0.5_1334
ppt_potential: 5
primary_source: true
public_brief_potential: 4
review_status: accepted
reviewed_at: '2026-07-15T08:13:06+08:00'
reviewed_by: auto
source_type: chinese-media-digest-item
source_url: https://m.sohu.com/a/1049851171_455313?scm=10001.325_13-325_13.0.0-0-0-0-0.5_1334&digest_item=5
title_en: 浪潮信息发布CPU原生液冷整机柜，单柜承载4万Agent
title_zh: 浪潮信息发布CPU原生液冷整机柜，单柜承载4万智能体
topics: *id001
track: industry
---

# 知识卡片：浪潮信息发布CPU原生液冷整机柜，单柜承载4万智能体

英文标题：Inspur Releases CPU Native Liquid Cooling Rack, Supporting 40,000 Agents per Rack
英文关键词：Inspur, CPU native liquid cooling, rack server, agent, OCM architecture, YuanBrain SD200, Kimi K2

## 一句话结论
浪潮信息推出业界首款CPU原生液冷整机柜服务器及升级版元脑SD200超节点，单柜最高支持384颗CPU、可承载4万+智能体协同，面向智能体时代重构算力体系。

## 事件概述
2026年7月，浪潮信息发布两款面向智能体时代的新型算力设备：一是CPU原生液冷整机柜服务器，基于开放OCM架构（Open Compute Module），实现全域部件液冷并适配800V高压供电；二是升级版元脑SD200超节点，在Kimi K2.6万亿模型上单Token生成低至4.77ms，支持多模融合，在DRACO等基准表现超越单一模型。

## 方法/产品要点
- **整机柜**：业界首款CPU原生液冷设计，全域部件液冷（CPU、内存、存储、网络等），适配800V高压供电，支持开放OCM架构。
- **算力密度**：单柜最高支持384颗CPU，可承载4万以上智能体（Agent）协同工作。
- **元脑SD200超节点**：在Kimi K2（6万亿参数模型）上实现单Token生成延迟4.77ms；支持多模融合（多模型协同推理）；在DRACO等基准测试中表现超越单一模型（待核实具体基准名称与分数）。
- **计算形态**：面向智能体时代，强调高密度、低延迟、液冷散热，支撑大规模Agent协同推理。

## 主要结果或产业意义
- **算力供给升级**：单柜384颗CPU、4万+Agent的承载能力，为智能体集群部署提供高密度、低功耗的硬件底座。
- **液冷技术突破**：CPU原生液冷从部件级实现全液冷，较传统风冷或间接液冷能效更高，适配800V高压供电进一步降低数据中心PUE。
- **推理性能领先**：元脑SD200在Kimi K2超大规模模型上的毫秒级Token生成（4.77ms），表明其推理加速能力达到业界先进水平。

## 为什么重要
智能体（Agent）的规模化部署依赖强大的算力基础设施。此前已有SIMIA 2、Cursor Design Mode等软件层面的Agent技术，但缺乏面向Agent密度的专用硬件。浪潮信息的整机柜首次从物理架构层面为“Agent协同”设计，单柜承载4万智能体，有望解决多Agent并行推理时的通信延迟、散热和供电瓶颈。同时，元脑SD200在多模融合基准上的表现说明其不单纯是硬件堆叠，而是在模型协同推理上有针对性优化，属于算力体系从“模型训练”向“Agent推理”转变的关键一步。

## 局限与不确定性
- 整机柜的实际部署功耗与散热效果尚未公开详细测试数据（待核实）。
- “4万+智能体协同”的具体场景（如智能体定义、实际推理负载类型）未明确（待核实）。
- 元脑SD200在DRACO基准上的具体分数与其他竞品对比数据未完整披露（待核实）。
- 800V高压供电的兼容性与推广进度暂无时间表（待核实）。

## 可用于图书/PPT/简报的角度
- **技术细节图**：可绘制整机柜架构图，标注CPU原生液冷回路、800V供电链路、OCM接口。
- **性能对比表**：对比传统风冷vs液冷整机柜的能耗、算力密度、Agent承载数。
- **行业趋势图**：从单体模型训练到Agent集群推理的算力需求演变，标注浪潮信息整机柜的位置。
- **案例引用**：可用于“智能体时代的基础设施”主题演讲，强调硬件与软件协同演进。

## 与既有脉络的关系
- 相较于SIMA 2（Google DeepMind的多模态Agnet）、Cursor Design Mode（交互式Agent）等软件层面创新，浪潮信息整机柜从硬件算力供给侧切入，填补了“Agent规模化部署所需的高密度低延迟计算平台”这一空白。
- 相较于之前的大规模推理基准（Together Inference Engine的编码Agent推理优化），本条聚焦于CPU原生液冷整机柜的物理设计，是推理加速在硬件层面的延续，增量信息在于首次明确“单柜4万Agent”的硬件指标。

## 原始材料
- 来源：腾讯研究院AI速递 20260714（搜狐转载），URL: https://m.sohu.com/a/1049851171_455313?scm=10001.325_13-325_13.0.0-0-0-0-0.5_1334
- 关键原文：浪潮信息发布业界首款CPU原生液冷整机柜服务器与升级版元脑SD200超节点……单柜最高支持384颗CPU、可承载4万+智能体协同……元脑SD200在Kimi K2.6万亿模型上单Token生成低至4.77ms……