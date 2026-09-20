---
book_potential: 3
collected_date: '2026-07-09'
confidence: 3
created_at: '2026-07-09T18:07:33+08:00'
date: '2026-07-08'
entities:
- arxiv.org
id: 2026-07-08-academic-foundation-model-ecglight-compute-light-framework-for-paper-ecg-d
importance: 4
keywords_en: &id001
- foundation-model
novelty: 4
ppt_potential: 4
primary_source: true
public_brief_potential: 4
review_status: rejected
source_type: paper
source_url: https://arxiv.org/abs/2607.07683v1
title_en: 'ECGLight: Compute-Light Framework For Paper ECG Digitization and Myocardial
  Infarction Screening'
title_zh: ECGLight：用于纸质心电图数字化和心肌梗死筛查的轻量计算框架
topics: *id001
track: academic
---

# 知识卡片：ECGLight：用于纸质心电图数字化和心肌梗死筛查的轻量计算框架

## 一句话结论
ECGLight 是一个无需高端计算资源、可在 CPU 上运行的端到端轻量化框架，能将智能手机拍摄的纸质心电图照片直接转换为校准后的 12 导联信号并筛查心肌梗死，在 PTB-XL 数据集上达到 95.51% 的检测准确率（F1=0.9519）。

## 事件概述或研究问题
偏远地区的诊所因缺乏网络连接和高性能计算设备，仍广泛使用纸质心电图打印件进行分析，导致大量纸质心电图无法被当代 AI 决策支持系统利用，容易遗漏急性冠脉闭塞等病情，延误再灌注治疗。现有研究将数字化和诊断分离处理，且依赖高级 AI 模型，缺乏一个在设备端计算轻量、高保真重建纸质心电图并支持多种临床终点的统一框架。

## 方法/产品要点
- 端到端轻量化设备端流水线：输入为智能手机拍摄的纸质心电图照片或扫描件，输出为校准后的 12 导联信号，并直接筛查心肌梗死（MI）病理。
- 使用 SHAP（SHapley Additive exPlanations）提供可解释性支持。
- 训练和评估基于 PTB-XL 数据集的 21,799 份心电图，并在医院获得的 ECG-Matrix 数据集上进行了外部验证。
- 整个系统仅依赖 CPU 资源，每份心电图处理时间小于 30 秒。

## 主要结果或产业意义
- MI 检测（PTB-XL）：准确率 95.51%，F1 分数 0.9519。
- OMI（梗阻性心肌梗死）检测（ECG-Matrix）：准确率 88.89%，F1 分数 0.8862。
- 该工作证明，即使在数字心电图导出、网络连接或高端计算不可用的情况下，老旧纸质记录也可在全球范围内被可靠地“民主化”利用，提供可扩展的决策支持。

## 为什么重要
- 解决了资源受限环境下纸质心电图无法接入 AI 决策支持的痛点，有望减少因漏诊导致的延误治疗。
- 首次提出一个计算轻量（CPU 仅需 <30 秒）、设备端运行的从数字化到诊断的完整流水线，填补了此前只有分离方案或高算力方案的空白。
- 结合可解释性方法（SHAP）增强临床信任度。

## 局限与不确定性
- 外部验证仅在单个医院 ECG-Matrix 数据集上进行，泛化性需进一步评估（待核实更多医院/地区验证情况）。
- 该框架对纸质心电图的图像质量（如拍照角度、光照、纸张褶皱）可能敏感，尚需在更多真实场景测试。
- 仅针对心肌梗死筛查，其他心血管疾病（如心律失常）的检测能力未在摘要中提及。
- 模型训练基于 PTB-XL（德国数据），可能对非欧洲人群的适配性存疑（待核实）。

## 可用于图书/PPT/简报的角度
- 数字健康公平性：如何用低成本、低算力方案弥合医疗资源差距。
- 轻量化 AI 在移动医疗中的应用案例：智能手机拍照→即时诊断。
- 模型可解释性（SHAP）在临床诊断中的价值。
- 从“纸”到“数字”再到“诊断”的端到端技术演进。

## 原始材料
- 英文标题：ECGLight: Compute-Light Framework For Paper ECG Digitization and Myocardial Infarction Screening
- 英文关键词：ECG digitization, compute-light, myocardial infarction, smartphone-based diagnosis, SHAP explainability, PTB-XL
- 来源：arXiv 预印本，ID 2607.07683v1，URL: https://arxiv.org/abs/2607.07683v1