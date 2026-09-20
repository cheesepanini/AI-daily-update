---
auto_review_age_days: 1
auto_review_reasons:
- importance:4+8
- novelty:4+8
- confidence:3+6
- ppt_potential:4+4
- public_brief_potential:3+3
- topic_priority:5+10
- source_type:company-news+2
- primary_source+2
- 'score>=28: 自动接受'
auto_review_score: 43
book_potential: 4
collected_date: '2026-08-26'
confidence: 3
created_at: '2026-08-26T18:19:47+08:00'
date: '2026-08-26'
duplicate_suspect:
  date: '2026-07-10'
  source_url: https://aiera.com.cn/2026/07/10/other/admin/103416/%e8%a1%8c%e4%b8%9a%e9%a6%96%e4%b8%aa%e5%85%b7%e8%ba%ab%e5%8e%9f%e7%94%9f%e4%b8%96%e7%95%8c%e5%8a%a8%e4%bd%9c%e6%a8%a1%e5%9e%8b%e6%9d%a5%e4%ba%86%ef%bc%81%e8%9a%82%e8%9a%81%e7%81%b5%e6%b3%a2%e5%8f%91
  title: 行业首个具身原生世界动作模型——蚂蚁灵波发布 LingBot-VA 2.0
entities:
- technology.robbyant.com
id: 2026-08-26-industry-ai-industry-lingbot-depth-1-0
importance: 4
industry_dimensions:
- company
keywords_en: &id001
- ai-industry
novelty: 4
ppt_potential: 4
primary_source: true
public_brief_potential: 3
review_status: accepted
reviewed_at: '2026-08-27T08:16:00+08:00'
reviewed_by: auto
source_type: company-news
source_url: https://technology.robbyant.com/lingbot-depth
title_en: LingBot-Depth 1.0
title_zh: LingBot-Depth 1.0——将失效的深度传感器变成精确3D感知
topics: *id001
track: industry
---

# 知识卡片：LingBot-Depth 1.0——将失效的深度传感器变成精确3D感知

## 一句话结论

LingBot-Depth 用“深度传感器自身产生的空洞”作为掩码信号，通过掩码深度建模（Masked Depth Modeling, MDM）学习用 RGB 视觉上下文补全缺失深度，把消费级深度相机在玻璃、镜面、金属等反光透明物体上失效的问题，转化为可训练的感知任务，并在深度补全、单目深度估计、立体匹配和机器人抓取上取得领先结果。

## 事件概述或研究问题

消费级深度相机在无纹理区域、透明玻璃、镜面和金属表面经常无法输出有效深度，因为立体匹配算法在左右视图“看起来一样”或发生畸变时会失效，产生“空洞”。LingBot-Depth 的核心研究问题是：如何把这些传感器失效区域从“噪声”变成“学习信号”，让模型根据 RGB 图像理解视觉上下文，预测缺失区域的度量级深度。

## 方法/产品要点

- **核心方法：掩码深度建模（Masked Depth Modeling, MDM）**  
  不是像标准掩码自编码器那样随机隐藏图像块，而是直接使用深度相机输出中自然出现的“空洞”作为掩码。这些空洞恰好对应几何推理最困难的区域，模型被要求利用 RGB 上下文重建缺失深度。

- **数据规模与构成**  
  构建了真实与仿真结合的数据管线，收集 300 万对 RGB-深度数据（200 万真实 + 100 万合成）。真实数据覆盖家庭、办公室、健身房、大厅和室外场景；合成管线模拟真实传感器失效模式，提供干净的真值深度。原文另一处提到“1000 万张图像”的训练规模，与“300 万对”的关系待核实。

- **显式几何与隐式特征的对齐**  
  模型学到 RGB 外观与深度几何紧密耦合的统一潜在空间：一方面输出准确的度量深度图（显式几何），另一方面产出跨模态对齐的特征表示（隐式特征），支撑下游 3D/4D 跟踪、场景理解和机械臂操作。

- **时间一致性**  
  虽然没有显式时序建模，但宣称在视频输入上能保持稳定的深度序列和时间一致性。

## 主要结果或产业意义

- **深度补全**  
  在 iBims、NYUv2、DIODE、ETH3D 等标准基准上，相比现有方法实现 40–50% 的误差降低；在稀疏 SfM 输入上，室内 RMSE 提升 47%，室外提升 38%。

- **超越工业级深度相机**  
  宣称在挑战性场景下比 ZED 立体相机生成更完整、更准确的深度；能填补结构光和立体相机都失效的深度空洞，包括玻璃墙、镜面、水族馆隧道等。

- **机器人抓取**  
  透明储物箱抓取成功率从 0% 提升到 50%；钢杯从 65% 到 85%，玻璃杯从 60% 到 80%，玩具车从 45% 到 80%；反光和透明物体整体抓取成功率提升 30–78%。

- **基础模型能力**  
  作为单目深度估计的预训练骨干，在 10 个基准上超过 DINOv2；用其初始化可加速 FoundationStereo 的立体匹配训练；对齐的 RGB-深度特征可支持下游 3D/4D 跟踪而无需任务特定微调。

- **产业意义**  
  为机器人在透明/反光物体场景中的可靠操作提供了一条不依赖更贵硬件的技术路径，也为机器人学习中的 4D 点跟踪、室内建图和相机轨迹估计提供更干净的度量深度输入。

## 为什么重要

LingBot-Depth 的增量价值在于：它把传感器“失效模式”重新定义为可学习的掩码信号，而不是简单地当作噪声过滤。这一思路直接解决了机器人从感知到操作中最容易出问题的真实场景——玻璃、镜面、金属容器等。相比既有 LingBot-VA 2.0 的世界动作模型和 LingBot-Vision 的边界中心视觉模型，本卡片聚焦的是 LingBot 系列中深度补全这一具体环节。

## 与既有脉络的关系

已有相关卡片提到 LingBot-Vision 作为 LingBot-Depth 2.0 的编码器初始化。本卡片按手动标题记为 LingBot-Depth 1.0，但原文页面未出现版本号；它应是理解后续 LingBot-Depth 2.0 的能力基线。本卡片的增量信息包括：MDM 不以随机掩码而是以传感器天然空洞为掩码、300 万对真实+仿真数据、透明/反光物体抓取成功率等具体数字。版本对应关系待核实。

## 局限与不确定性

- 原文页面没有明确写“LingBot-Depth 1.0”，版本号来自手动标题，待核实。
- 原文同时出现“1000 万张图像”和“300 万 RGB-深度对”两种数据规模表述，两者关系待核实。
- 未披露模型架构、参数量、推理速度、训练算力、发布时间和开源许可，待核实。
- 所有评测结果均为页面自述，缺乏第三方独立评估细节；所谓“超越工业级深度相机”需要更多验证。
- 原文中名为“Scaling Law”的小节实际内容更接近方法动机与数据规模介绍，未给出 scaling law 曲线或计算量-性能关系。
- “在 10 个基准上超过 DINOv2”等表述缺少具体 benchmark 列表和实验设置，待核实。

## 可用于图书/PPT/简报的角度

- **一句话金句**：机器人不需要在透明杯子面前换更贵的传感器，而是可以学会用视觉上下文猜出缺失的深度。
- **案例图表**：透明储物箱抓取成功率 0% → 50%，钢杯 65% → 85%，玻璃杯 60% → 80%，玩具车 45% → 80%。
- **技术叙事角度**：从“传感器失效是噪声”到“传感器失效是数据”，用掩码深度建模把失败变成学习信号。
- **产业应用角度**：作为机器人基础模型家族中的空间感知模块，LingBot-Depth 可服务于机械臂抓取、室内建图、4D 点跟踪和场景理解。

## 原始材料

- **英文标题**：LingBot-Depth Spatial Perception Model - Robbyant
- **英文关键词**：Masked Depth Modeling, Depth Completion, Monocular Depth Estimation, Stereo Matching, Metric Depth, Temporal Consistency, Robotic Grasping, Spatial Perception, 3D/4D Point Tracking
- **原始来源**：https://technology.robbyant.com/lingbot-depth
- **页面简介**：Transforming flawed depth sensors into precision 3D perception through masked depth modeling.