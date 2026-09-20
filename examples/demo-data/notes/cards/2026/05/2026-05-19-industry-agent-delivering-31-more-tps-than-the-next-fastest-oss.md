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
book_potential: 3
collected_date: '2026-07-07'
confidence: 4
created_at: '2026-07-07T10:30:32+08:00'
date: '2026-05-19'
entities:
- www.together.ai
id: 2026-05-19-industry-agent-delivering-31-more-tps-than-the-next-fastest-oss
importance: 4
industry_dimensions:
- company
keywords_en: &id001
- agent
novelty: 4
ppt_potential: 4
primary_source: true
public_brief_potential: 3
review_status: accepted
reviewed_at: '2026-07-08T15:27:10+08:00'
reviewed_by: auto
source_type: company-news
source_url: https://www.together.ai/blog/coding-agent-benchmarks
title_en: "\U0001F4CA Delivering 31% more TPS than the next-fastest OSS engine for
  production coding agent workloads →"
title_zh: 大规模推理基准测试：编码智能体
topics: *id001
track: industry
---

# 知识卡片：大规模推理基准测试：编码智能体

## 一句话结论
Together Inference Engine 在编码智能体生产工作负载上，相比 TensorRT-LLM 实现了 31% 更高的 TPS，在饱和状态下 TTFT 提升 2 倍，且相比 Claude Opus 4.6 成本降低 76%（或相比 Claude Opus 4.8 每个请求节省 70%）。

## 事件概述或研究问题
传统推理基准测试通常测量单个用户访问专用端点，无法反映生产环境中多用户并发、共享 KV 缓存和 GPU 资源时的真实表现。本文旨在构建针对编码智能体工作负载的真实推理基准，重点评估高并发、长上下文场景下的性能退化曲线。

## 方法/产品要点
- **硬件**：一起推理引擎和 TensorRT-LLM 使用 4× NVIDIA B200 GPU；SGLang 因内存限制使用 8× B200（TP8）。
- **工作负载**：模拟编码智能体请求，提示长度约 45k–200k tokens，生成长度平均 450 tokens（p50: 293, p99: 2,230），高并发（QPS 递增）。
- **关键指标**：TPM（每分钟输入 tokens）、TPS（每用户每秒 tokens）、p50 TTFT（首 token 时间）。
- **优化手段**：ThunderMLA 将 MLA 架构的两个内核融合为单个 megakernel，效率比 FlashMLA 高 20–35%；全栈优化包括内核重写、内存布局、驱动行为调优。
- **解码方案**：EAGLE 推测解码，3 个 draft tokens，接受率约 70%。

## 主要结果或产业意义
- 在 2.5M TPM 总负载下（625 TPM/GPU）：
  - Together Inference Engine 的 TPS 比 TensorRT-LLM 高 31%，且是唯一 p50 TTFT 低于 1 秒的引擎（0.71s）。
  - TensorRT-LLM 的 TTFT 为 1.1s，SGLang 为 5.1s（尽管使用了 8 块 GPU）。
- 成本对比：
  - Kimi K2.7 Code on Together 每个典型请求（~80k–100k 输入，~450 输出）成本 $0.029，Claude Opus 4.8 为 $0.097，节省约 70%。
  - 一个 150 人的工程团队运行编码智能体（7.5M TPM，每天 5 小时，250 个工作日）可节省约 $421K/年。
- 质量方面：Kimi K2.6 在编码基准上匹配或超越 Claude Opus 4.6（描述中提及 76% 成本降低即指此对比，待核实具体版本）。

## 为什么重要
编码智能体工作负载具有长输入、高并发、对首 token 延迟敏感的特点。传统单用户基准无法捕捉 KV 缓存竞争、预填充压力等生产瓶颈。本文提供的基准方法和优化成果直接帮助工程团队评估和选择推理引擎，降低大规模部署成本。

## 局限与不确定性
- 仅测试了 Kimi K2.5 模型（带 EAGLE 解码），其他模型结果可能不同。
- SGLang 使用了 8 块 GPU（因 TP4 内存不足），且未进行详尽调优，存在边际改进空间。
- TensorRT-LLM 配置为低延迟模式，而非吞吐量优化模式（如使用预填充-解码分离可提高输入 TPM 但降低输出 TPS）。
- 本文为版本一，团队承诺后续更新。

## 可用于图书/PPT/简报的角度
- 展示生产级 AI 推理基准设计思路：为何单用户基准不可靠，需关注并发下的退化曲线。
- 对比开源推理引擎（TensorRT-LLM、SGLang）与商业优化引擎（Together IE）的实际性能差异。
- 以编码智能体为例，量化成本节省（每请求、每年）和延迟改善（TTFT 减少 2 倍）。
- 强调全栈优化（内核融合、内存布局、驱动调优）在推理中的价值。

## 原始材料
**英文标题**：Benchmarking inference at scale: coding agents  
**英文关键词**：coding agent, inference benchmark, TTFT, TPS, Together Inference Engine, TensorRT-LLM, SGLang, ThunderMLA, Kimi K2.5  
**来源 URL**：https://www.together.ai/blog/coding-agent-benchmarks  
**发布日期**：2026年5月19日