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
book_potential: 5
collected_date: '2026-07-08'
confidence: 4
created_at: '2026-07-08T15:26:48+08:00'
date: '2026-06-22'
entities:
- developer.nvidia.com
id: 2026-06-22-industry-ai-industry-inside-nvidia-halos-for-robotics-a-full-stack-fu
importance: 5
industry_dimensions:
- company
keywords_en: &id001
- ai-industry
novelty: 5
ppt_potential: 5
primary_source: true
public_brief_potential: 4
review_status: accepted
reviewed_at: '2026-07-09T08:09:03+08:00'
reviewed_by: auto
source_type: company-news
source_url: https://developer.nvidia.com/blog/inside-nvidia-halos-for-robotics-a-full-stack-functional-safety-system-for-physical-ai
title_en: 'Inside NVIDIA Halos for Robotics: A Full-Stack Functional Safety System
  for Physical AI'
title_zh: NVIDIA Halos for Robotics：面向物理AI的全栈功能安全系统
topics: *id001
track: industry
---

# 知识卡片：NVIDIA Halos for Robotics：面向物理AI的全栈功能安全系统

## 一句话结论
NVIDIA推出Halos for Robotics平台，将汽车级功能安全技术（累计超过18,000工程年、210亿安全晶体管）扩展至工业机器人、人形机器人和自主移动机器人领域，通过IGX Thor计算平台和Halos OS安全软件栈提供符合IEC 61508等标准的安全解决方案。

## 事件概述或研究问题
物理AI（在工厂、仓库、医院和家庭中自主与人类协作的机器人）发展迅速，传统结构化环境的安全方案已无法适应非结构化场景。NVIDIA于2026年6月22日发布NVIDIA Halos for Robotics，将自动驾驶领域积累的功能安全技术（超过18,000工程年、210亿安全晶体管、700万行安全评估代码、22,000个平台安全监视器）系统性地迁移至机器人领域，解决机器人安全合规与AI驱动的安全融合问题。

## 方法/产品要点
- **硬件平台**：NVIDIA IGX Thor（工业级AI计算模块），提供高达2,070 FP4 TFLOPs AI性能、14个Neoverse ARM CPU核心、128 GB内存（273 GB/s带宽），内置硬件安全特性：
  - IEC 61508 SIL 3能力的安全岛（FSI，12K DMIPs，物理隔离）
  - 超过22,000个安全机制，覆盖整个SoC的诊断覆盖
  - 多样性/冗余（GPU/CPU、GPU/PVA等）、系统内测试（Logic/Memory BIST）、免于干扰（FFI）支持
- **安全软件栈**：NVIDIA Halos OS，包含Halos Core（安全操作系统，提供Linux版或Linux+QNX版，后者通过NV Hypervisor隔离安全与非安全虚拟机）和Halos应用蓝图（如Outside-In Safety蓝图）。
- **传感器安全扩展**：NVIDIA Holoscan Sensor Bridge（HSB），通过以太网连接传感器和执行器，支持低延迟、可扩展、多模态，提供MACsec加密和IEC 61508 SIL 2安全协议。
- **认证与生态**：Halos AI Systems Inspection Lab（ANAB认可，ISO/IEC 17020检查机构），为合作伙伴提供预评估的安全和AI认证路径；NVIDIA担任IEC 61508、ISO/IEC TS 22440等标准制定领导者。

## 主要结果或产业意义
- Agility Robotics（Digit人形机器人）已采用IGX Thor和Halos OS，并加入Halos AI Systems Inspection Lab，加速工业环境安全人形机器人的开发。
- 生态合作伙伴包括IGX ODM（Advantech、Nexcobot、Inventec、Connect Tech）、安全MCU/传感器（Infineon、NXP、TI）、HSB芯片（TI、ST、NXP、Lattice）以及软件（Blackberry QNX、Acontis EtherCAT、FreeRTOS安全认证包）。
- 标志着机器人安全从临时实现转向共享的、标准对齐的基础设施。

## 为什么重要
- 将自动驾驶领域最严格的功能安全经验（TÜV SÜD/TÜV Rheinland第三方评估）直接复用至机器人，避免从头开发，大幅缩短认证周期和降低成本。
- 提供全栈（硬件+软件+生态）安全方案，解决物理AI时代机器人与人类共存的根本安全挑战。
- 推动国际功能安全标准（IEC 61508、ISO 13849、ISO/IEC TS 22440）在机器人领域的统一化。

## 局限与不确定性
- 部分安全文档（如IGX和Halos OS在安全上下文中的应用笔记）仅在NDA下提供，具体配置细节待核实。
- Halos OS中的“机器人中间件和Halos Infra工具”当前尚未用于安全应用，未来完整安全方案的时间线待核实。
- 认证路径（如ISO/IEC TS 22440）仍为“即将发布”的草案标准，实际推广效果待验证。
- 材料中未提及具体成本、功耗、以及针对不同机器人类型（如人形机器人vs. AMR）的适配差异。

## 可用于图书/PPT/简报的角度
- **对比视角**：对比传统机器人安全（物理围栏/笼）与AI驱动安全（Halos全栈方案）的演进，强调功能安全从AV到机器人的技术迁移。
- **产业里程碑**：以Agility Robotics采用为例，展示人形机器人安全合规的商业化路径。
- **标准制定视角**：NVIDIA作为IEC 61508召集人的角色如何塑造机器人安全标准。
- **技术架构图**：将分层的Halos架构（硬件平台安全→Halos OS→生态安全）可视化，突出安全岛、HSB、Outside-In蓝图等关键组件。

## 原始材料
- **英文标题**：Inside NVIDIA Halos for Robotics: A Full-Stack Functional Safety System for Physical AI
- **英文关键词**：Robotics, Functional Safety, Physical AI, NVIDIA Halos, IGX Thor, Halos OS, Safety Island, Autonomous Mobile Robots, Humanoids
- **来源**：https://developer.nvidia.com/blog/inside-nvidia-halos-for-robotics-a-full-stack-functional-safety-system-for-physical-ai