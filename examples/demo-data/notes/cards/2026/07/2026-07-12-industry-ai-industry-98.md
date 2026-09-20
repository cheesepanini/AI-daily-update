---
book_potential: 4
collected_date: '2026-07-12'
confidence: 5
created_at: '2026-07-12T18:03:23+08:00'
date: '2026-07-12'
entities:
- www.qbitai.com
event_date: '2026-07-12'
id: 2026-07-12-industry-ai-industry-98
importance: 5
industry_dimensions:
- company
keywords_en: &id001
- ai-industry
novelty: 4
ppt_potential: 5
primary_source: true
public_brief_potential: 4
review_status: rejected
source_type: chinese-media
source_url: https://www.qbitai.com/2026/07/448034.html
title_en: 98年哈工大教授创业，要做人形灵巧操作世界模型
title_zh: 98年哈工大教授创业，要做人形灵巧操作世界模型
topics: *id001
track: industry
---

# 知识卡片：98年哈工大教授创业，要做人形灵巧操作世界模型

**一句话结论**：破晓智能（PHANES AI）从触觉数据切入，通过EgoTouch、TouchAnything、TouchWorld三阶段技术路线，构建人形机器人全身移动灵巧操作世界模型，让机器人从“看见世界”走向“真正接触并操作世界”。

**事件概述**：1998年出生的哈工大（深圳）长聘教授杨朔，围绕“机器人如何真正学会操作”创办破晓智能。公司核心工作是融合人类视频数据与触觉感知模态，构建人形机器人全身移动灵巧操作世界模型。本周发布的TouchWorld是继EgoTouch（触觉数据采集）、TouchAnything（从视频恢复触觉）后的第三项关键工作，使机器人能预测接触状态并利用触觉反馈修正动作。

**方法/产品要点**：
- **Touch系列技术路线**：
  - **EgoTouch**：采集第一人称视觉-触觉数据（腕部视角、手部姿态、双手压力图），覆盖刚性/柔性物体、抓取、拧动、工具使用等任务。
  - **TouchAnything**：利用EgoTouch对齐数据训练模型，从纯第一人称视频中估计双手接触区域和压力分布，实现低成本触觉数据增广。
  - **TouchWorld**：触觉世界模型，包含两个核心能力：①触觉目标预测（predictive）——预测未来接触状态；②高频触觉反馈修正（reactive）——上层模型给出粗动作后，底层以4倍频率输出delta修正量，实现实时纠偏。
- **HumanWBC（后续步骤）**：基于人类数据训练全身移动灵巧操作控制模型，串联感知、自主移动、双臂协同、灵巧手操作。
- **数据基础设施**：正在搭建低成本、无感便携、全场景的多模态数据采集平台，同步采集第一人称视觉、腕部视角、手部姿态、全掌触觉、全身姿态。

**主要结果或产业意义**：
- TouchWorld在浇花、桌面清理、电源插头插入、杯子插入、擦锅、抽纸巾六项真实机器人任务中测试。
  - clean setting下平均成功率**65.0%**，人为扰动场景下平均成功率**57.2%**。
  - 相比Pi-0.5、FTP-1、GR00T N1.7等最强baseline，分别高出**15.7**和**16.0**个百分点。
- 验证了触觉目标预测和高频反馈修正能提升机器人操作稳定性，触觉可被纳入世界模型而非仅停留在传感器读数。
- 产业意义：推动人形机器人从“能看懂”走向“能走过去、抓起来、做完事”，补齐触觉这一关键感知模态。

**为什么重要**：
- 现有VLA和世界模型主要解决“看懂世界”和“预测世界”，但物理世界中的接触反馈（手是否碰到、滑落、力是否合适）缺乏有效处理。TouchWorld首次系统性地将触觉目标预测与高频反馈修正融入灵巧操作策略。
- 团队以触觉数据为入口，构建“数据采集→触觉恢复→世界模型→全身控制”完整能力链，而非仅发布单个模型，对于人形机器人落地真实场景（家庭、服务、工业）具有基础架构价值。

**局限与不确定性**：
- TouchWorld在clean setting下平均成功率仅65.0%，距离大规模泛化仍有很大距离。
- 灵巧手硬件方案尚不成熟：高自由度、带全掌触觉的灵巧手方案待定；触觉手套易损坏（几天即坏）、灵巧手发热导致标定漂移、数据噪声大、采集效率低。
- 行业统一benchmark尚未建立，不同传感器数据表示不统一。

**可用于图书/PPT/简报的角度**：
- **从触觉切入**：对比视觉+语言模型的局限，说明为什么物理世界操作需要触觉。
- **数据飞轮**：EgoTouch→TouchAnything→TouchWorld三步如何实现触觉数据从稀缺到放大再到模型使用的闭环。
- **产业混沌期的创业选择**：在人形机器人行业基础设施不完善时，从具体问题（触觉数据）入手构建系统性解决方案。
- **年轻教授创业**：1998年出生、26岁已成哈工大长聘教授的创业者，团队的技术积累与商业化结合。

**原始材料**：
- 来源：量子位（2026-07-12）
- 标题：98年哈工大教授创业，要做人形灵巧操作世界模型
- URL: https://www.qbitai.com/2026/07/448034.html
- 英文标题：98年哈工大教授创业，要做人形灵巧操作世界模型（原始来源为中文报道，英文标题保留原文拼音/翻译）
- 英文关键词：TouchWorld, EgoTouch, TouchAnything, HumanWBC, PHANES AI, tactile world model, dexterous manipulation, humanoid robot, loco-manipulation, contact prediction, tactile feedback
- 相关论文：
  - TouchWorld：https://arxiv.org/abs/2607.07287
  - TouchAnything：https://arxiv.org/abs/2605.13083
  - 项目主页：https://phanes-lab.github.io/TouchWorld-website/