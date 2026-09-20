---
auto_review_age_days: 1
auto_review_reasons:
- importance:4+8
- novelty:4+8
- confidence:3+6
- ppt_potential:5+5
- public_brief_potential:2+2
- topic_priority:5+10
- source_type:company-news+2
- primary_source+2
- 'score>=28: 自动接受'
auto_review_score: 43
book_potential: 4
collected_date: '2026-09-19'
confidence: 3
created_at: '2026-09-19T08:13:32+08:00'
date: '2026-09-19'
duplicate_suspect:
  date: '2026-07-06'
  source_url: https://arxiv.org/abs/2607.04668v1
  title: 弹性组：硬屏障LLM推理组与OS进程协同调度中的逐令牌成员变更
entities:
- developer.nvidia.com
id: 2026-09-19-industry-foundation-model-benchmark-evaluation-benchmarking-llm-inference-at-scale-with-aiperf
importance: 4
industry_dimensions:
- company
keywords_en: &id001
- foundation-model
- benchmark-evaluation
novelty: 4
ppt_potential: 5
primary_source: true
public_brief_potential: 2
review_status: accepted
reviewed_at: '2026-09-20T08:05:52+08:00'
reviewed_by: auto
source_type: company-news
source_url: https://developer.nvidia.com/blog/benchmarking-llm-inference-at-scale-with-aiperf
title_en: Benchmarking LLM Inference at Scale with AIPerf
title_zh: 用 AIPerf 进行大规模 LLM 推理基准测试
topics: *id001
track: industry
---

# 知识卡片：用 AIPerf 进行大规模 LLM 推理基准测试

## 一句话结论
NVIDIA AIPerf 是 GenAI-Perf 的后继与从零重写版本，采用多进程架构和可配置流量模式，目标是在高并发 LLM 推理基准测试中避免压测客户端成为瓶颈，并输出可用于容量与性能分析的指标。

## 事件概述或研究问题
NVIDIA 技术博客于 Sep 18, 2026 发布《Benchmarking LLM Inference at Scale with AIPerf | NVIDIA Technical Blog》。文章从“模型部署后如何判断快不快”切入，指出 curl、手写 asyncio、一次性负载生成器、单进程 GenAI-Perf 等做法可能受单进程性能限制、Python GIL 限制并发、或使用自制参考导致结果不可信。AIPerf 定位为 designated successor to GenAI-Perf，是 ground-up rewrite。

## 方法/产品要点
- **架构变化**：AIPerf 不再像 GenAI-Perf 那样运行在 Perf Analyzer 之上，而是一次干净架构断点。它采用多进程系统：worker processes 生成负载，独立 record-processor services 处理结果，并通过 ZMQ 协调，目的是防止 AIPerf 本身成为客户端侧瓶颈。
- **端点与数据集**：材料称 AIPerf 支持 15+ endpoint types，包括 chat、responses、NIM rankings、image generation 等；支持公开数据集如 ShareGPT，以及来自 Mooncake、Baseten、WEKA（AgentX）等的 trace replay 格式，可用于合成烟测或回放捕获的生产流量。
- **负载形状控制**：支持 constant、Poisson、gamma arrival patterns，并可调 burstiness；支持对并发和请求速率进行 gradual ramping；支持包括 vLLM/SGLang range-ratio 在内的 synthetic distributions，用于生成可变 ISL/OSL。
- **核心指标**：TTFT（Time to First Token）、ITL（Inter-Token Latency）、Request Latency、Output Token Throughput。指标会给出 p25、p50、p75、p90、p95、p99 等百分位，以及 min、max、average、standard deviation。
- **GPU 遥测**：当 DCGM 或 pynvml 可用时，AIPerf 可在同一次运行输出中带入 GPU power draw、utilization、memory consumption，便于把延迟尖峰与资源压力关联起来。
- **安装与示例**：材料给出 `uv tool install aiperf` 或虚拟环境安装方式。示例服务端使用 vLLM 跑 `Qwen/Qwen3-0.6B`。静态基准示例固定 128 input / 128 output tokens，并使用 `min_tokens:128`、`ignore_eos:true` 和 `--streaming`；Poisson 示例使用 `--request-rate 10`、`--arrival-pattern poisson`、input mean 512 / stddev 128、output mean 128 / stddev 32、`--random-seed 42`、`--request-count 200`。
- **平台备注**：在 aarch64 上，`crick` 依赖以 source-only 形式提供，需要 C toolchain，如 Debian/Ubuntu 上的 `build-essential` 或 RHEL 上的 `Development Tools`。

## 主要结果或产业意义
材料通过静态 128/128 基准与 Poisson 到达模式示例展示差异：Poisson 运行中请求率围绕 10 requests/second 波动，输入序列长度分布以 512 为中心、范围约 154 到 818 tokens；与单并发静态场景相比，Poisson 下 TTFT 分布更宽，因为更多请求同时竞争 GPU、prefill 长度变化且 prefill 与 decode 重叠。具体图表中的完整百分位数值在提供的摘录中未完整给出，待核实。

产业意义在于：大规模 LLM 推理服务的性能验证越来越依赖可信的负载生成、真实流量形状、尾延迟指标和硬件遥测。AIPerf 试图把“压测客户端不要成为瓶颈”“负载形状可控制”“指标可复现”这些工程需求整合到一个工具中，可用于容量规划、部署验证和推理服务调优。

## 为什么重要
- 基准测试结果是否可信，取决于客户端是否成为瓶颈、流量是否接近生产、指标是否覆盖长尾、运行是否可复现。AIPerf 的多进程架构、到达模式、百分位指标和 GPU 遥测，正是围绕这些问题设计的。
- 与已有卡片的关系：已有 TensorRT Edge-LLM 卡片聚焦边缘设备上的 MLPerf Edge Agentic 具体跑分；本条不重复那些具体模型/设备性能数字，而是补上“大规模 LLM 推理基准测试工具与负载方法”的增量视角。已有生物医学基础模型基准测评卡片关注科学评测规范；本条更偏工程性能基准与负载生成方法，二者可互补。
- 对实践者而言，它提示：不要只问“平均吞吐多少”，还要问“客户端能不能压满服务器”“请求到达是否像真实流量”“p99 和 GPU 资源是否同步变化”。

## 局限与不确定性
- 来源是 NVIDIA 技术博客，且抓取文本包含 AI-generated summary，可能概括不完整或有推广倾向；重要信息需回到原文和工具文档核实。
- AIPerf 的具体版本号、开源许可证、代码仓库地址、完整支持矩阵：待核实。
- 除 aarch64 安装说明外，其他操作系统、硬件、容器环境的支持情况：待核实。
- AIPerf 相对 GenAI-Perf 的逐项性能提升幅度：材料未量化，待核实。
- 文中图表的具体完整数值，如各百分位 TTFT、ITL、吞吐、GPU 功耗等：摘录未完整给出，待核实。
- 示例仅使用 vLLM 上的 Qwen3-0.6B，不能直接外推到所有模型、推理引擎、硬件和线上服务。
- Figure 6 相关文本在摘录中被截断，TTFT 对比细节不完整；如需引用具体结论，待核实。

## 可用于图书/PPT/简报的角度
- **“别让压测客户端成为瓶颈”**：从单进程、GIL 限制讲到 AIPerf 的多进程 worker + record-processor + ZMQ 架构。
- **“负载形状比负载大小更重要”**：用 constant、Poisson、gamma、burstiness、ramping 解释为何生产流量不是均匀流。
- **“尾延迟与资源遥测同屏”**：把 TTFT、ITL、Request Latency、Output Token Throughput 与 p99、GPU power/utilization/memory 放在一起讲。
- **“从合成烟测到生产 trace 回放”**：ShareGPT、Mooncake、Baseten、WEKA AgentX 等数据集/格式可作为真实工作负载测试案例。
- **“可复现的基准配方”**：静态 128/128 保基线，Poisson 10 req/s 看动态竞争，random seed 保证重放一致。
- **与边缘 MLPerf 基准对照**：边缘单机跑分关注端侧吞吐与准确率；AIPerf 关注大规模推理服务负载客户端与流量工程方法。

## 原始材料
- 英文标题：Benchmarking LLM Inference at Scale with AIPerf | NVIDIA Technical Blog
- 原始来源：NVIDIA Technical Blog，https://developer.nvidia.com/blog/benchmarking-llm-inference-at-scale-with-aiperf
- 发布日期：Sep 18, 2026
- 作者：Francesco Di Natale, Elias Bermudez, Anthony Casagrande, Matthew Kotila, Harshini Komali, Ganesh Kudleppanavar
- Track：industry
- Topics：foundation-model, benchmark-evaluation
- Manual title：Benchmarking LLM Inference at Scale with AIPerf
- 英文关键词：AIPerf, GenAI-Perf, LLM inference benchmarking, TTFT, ITL, request latency, output token throughput, Poisson arrival, ShareGPT, Mooncake, Baseten, WEKA AgentX, DCGM, pynvml, vLLM, Qwen3-0.6B, ZMQ, ISL/OSL, endpoint types
- 说明：以上草稿基于提供的抓取材料；原文含 AI-generated summary，并提示“AI-generated content may summarize information incompletely. Verify important information.”