---
auto_review_age_days: 1
auto_review_reasons:
- importance:4+8
- novelty:4+8
- confidence:2+4
- ppt_potential:4+4
- public_brief_potential:3+3
- topic_priority:5+10
- source_type:paper+2
- primary_source+2
- 'score>=28: 自动接受'
auto_review_score: 41
book_potential: 3
collected_date: '2026-07-24'
confidence: 2
created_at: '2026-07-24T18:08:49+08:00'
date: '2026-07-23'
entities:
- arxiv.org
id: 2026-07-23-academic-foundation-model-graphvid-interactive-graph-controllable-video-ge
importance: 4
keywords_en: &id001
- foundation-model
novelty: 4
ppt_potential: 4
primary_source: true
public_brief_potential: 3
review_status: accepted
reviewed_at: '2026-07-25T08:14:09+08:00'
reviewed_by: auto
source_type: paper
source_url: https://arxiv.org/abs/2607.21580v1
title_en: 'GraphVid: Interactive Graph-Controllable Video Generation'
title_zh: GraphVid：基于交互图的可控视频生成
topics: *id001
track: academic
---

# 知识卡片：GraphVid：基于交互图的可控视频生成

## 一句话结论
GraphVid 通过结构化交互图代替轨迹或文本，实现了对多主体交互视频的精准、灵活控制，在视频质量指标上显著优于 Motion-I2V，且所需训练数据和参数更少。

## 事件概述或研究问题
可控视频生成一直面临难题：文本提示难以精确描述多物体的交互细节，轨迹控制需要用户为每个物体绘制准确路径，在遮挡或重叠场景下易产生歧义且难以扩展。GraphVid 提出用交互图（Interaction Graph）作为控制接口，让用户通过图结构指定物体间的关系和运动，以实现灵活且精确的多主体视频生成。

## 方法/产品要点
- **模型架构**：GraphVid 是一个基于图条件的图像到视频生成模型，输入为一张静态图像和一个结构化交互图，输出为对应的视频序列。
- **图控制接口**：交互图中的节点表示物体，边表示物体间的交互关系（如相对运动、碰撞、跟随等），用户可通过编辑图结构或属性来控制视频内容。
- **训练数据集**：创建了 GraphVid-Bench，一个大规模以交互为中心的视频数据集，包含结构化关系标注，用于训练交互感知的视频生成模型。
- **效率**：相比之前的运动控制方法（如 Motion-I2V），GraphVid 使用更少的训练数据和更少的可训练参数。

## 主要结果或产业意义
- 定量指标（与 Motion-I2V 对比）：
  - FID 降低 39.9%，FVD 降低 37.6%。
  - PSNR 从 9.87 提升至 15.98，SSIM 从 0.38 提升至 0.61。
- 展示了结构化语义接口（交互图）作为可控视频生成新范式的潜力。

## 为什么重要
- 现有可控视频生成多依赖轨迹（像素级）或文本（语义级），GraphVid 填补了中间层次——利用图结构描述物体间关系，既保留了语义的灵活性，又提供了明确的几何/运动约束。
- 与已有相关卡片（几何互易定理、MV-Forcing、视频生成模型作为光照估计器）不同，该工作聚焦于交互控制的表达形式，而非立体或多视角生成。**增量信息**：首次将图神经网络与扩散模型结合用于视频生成控制，并建立了配套数据集。

## 局限与不确定性
- 原文正文未获取，以下为基于摘要推测的待核实点：
  - 图结构的构建是否需要人工标注？是否支持自动提取？
  - GraphVid-Bench 的数据规模、来源及标注方式待核实。
  - 在复杂场景（如大量物体、遮挡严重）下的实际表现未在摘要中明确。
  - 与其它基于文本/轨迹的方法在用户易用性上的对比待核实。

## 可用于图书/PPT/简报的角度
- 介绍“可控视频生成”的三种范式：文本、轨迹、图结构，并对比优劣。
- 展示交互图如何简化多物体运动控制（例如汽车追逐、群鸟飞行等场景）。
- 说明优秀的数据集（GraphVid-Bench）对模型训练的重要性。

## 原始材料
- URL: https://arxiv.org/abs/2607.21580v1
- 英文标题: GraphVid: Interactive Graph-Controllable Video Generation
- 英文关键词: foundation-model, controllable video generation, interaction graph, video diffusion
- 来源：arXiv 预印本（正文未抓取，以上信息基于元数据摘要和候选总结，部分细节待核实）