---
auto_review_age_days: 1
auto_review_reasons:
- importance:4+8
- novelty:4+8
- confidence:2+4
- ppt_potential:4+4
- public_brief_potential:2+2
- topic_priority:5+10
- source_type:chinese-media-2
- primary_source+2
- 'score>=28: 自动接受'
auto_review_score: 36
book_potential: 3
collected_date: '2026-08-23'
confidence: 2
created_at: '2026-08-23T18:05:18+08:00'
date: '2026-08-23'
entities:
- aiera.com.cn
event_date: '2026-08-23'
id: 2026-08-23-industry-ai-industry-gpt-5-6-sol-openai
importance: 4
industry_dimensions:
- company
keywords_en: &id001
- ai-industry
novelty: 4
ppt_potential: 4
primary_source: true
public_brief_potential: 2
review_status: accepted
reviewed_at: '2026-08-24T08:07:26+08:00'
reviewed_by: auto
source_type: chinese-media
source_url: https://aiera.com.cn/2026/08/23/other/admin/110248/%e7%aa%81%e5%8f%91%ef%bc%8cgpt-5-6-sol%e5%a4%a7%e9%99%8d%e4%bb%b7%ef%bc%81openai%e6%8a%8a%e4%bb%b7%e6%a0%bc%e6%88%98%e7%83%a7%e5%88%b0%e6%97%97%e8%88%b0
title_en: 突发，GPT-5.6 Sol大降价！OpenAI把价格战烧到旗舰
title_zh: GPT-5.6 Sol 大降价，OpenAI 将价格战烧至旗舰
topics: *id001
track: industry
---

# 知识卡片：GPT-5.6 Sol 大降价，OpenAI 将价格战烧至旗舰

## 一句话结论
OpenAI 宣布对 GPT-5.6 Sol 的 API 价格和按需 credit 价格进行大幅下调，未来三个月内降幅超过 20%，其中输出 token 价格从每百万 token 30 美元降至 20 美元，降幅约 33%；订阅套餐价格不变。

## 事件概述
2026 年 8 月 23 日，OpenAI 通过其开发者账号宣布 GPT-5.6 Sol 开启大幅降价，覆盖 API 价格和超出套餐额度后的按需付费用量（credit）。API 端即时生效，符合条件的 ChatGPT Work 和 Codex credits 正在陆续推送。这是继此前 Luna、Terra 降价后，旗舰模型 Sol 首次跟进降价，被解读为针对 Anthropic 与中国低价模型的攻防战。

## 方法/产品要点
- 降价范围：API 按 token 计费部分 + credit 价格，未来三个月降幅超过 20%；Pro、Plus、Business 订阅价格不变，套餐内包含用量不变。
- GPT-5.6 Sol 此前 API 定价：每百万 token 输入 5 美元、输出 30 美元，为 GPT-5.6 家族最贵。
- 降价后 API 定价：每百万 token 输入 4 美元（降 20%），输出 20 美元（降 33%）。
- 缓存价格调整：缓存输入从 0.5 美元降至 0.4 美元；缓存写入从 6.25 美元降至 5 美元。
- 长上下文档位也下调：输入从 10 美元降至 8 美元；输出从 45 美元降至 30 美元。
- 官方解释：OpenAI Developers 称价格下降是因为 Sol 运行更有效率；Sol 参与优化了自己的生产推理内核，端到端服务成本下降 20%，token 生成效率提升超过 15%。
- 同日，Codex 负责人 Tibo 宣布 Codex 周活跃用户突破 2000 万，并向所有 Codex 和 ChatGPT Work 用户发放一次 BANKED 重置额度。

## 主要结果或产业意义
- 按文中示例：一个大型 Agent 每月消耗 1 亿输入 token、2000 万输出 token，成本从 1100 美元降至 800 美元，综合降幅约 27.3%；重输入场景约省两成多，重输出场景（如 Codex 写代码）可省三成以上。
- 这次降价发生在 Anthropic 被曝已递交 S-1 启动 IPO、路演窗口为 8 月至 9 月的节点，科技博主 Chubby 与记者 tae kim 均认为这是 OpenAI 对 Anthropic 的针对性施压。
- 背景还包括 DeepSeek V4 Flash 于 7 月 31 日发布，以及一个代号为“Ox Alpha”的神秘模型（1M 上下文，支持文本、图片、视频输入，免费一周）出现，形成中国低价模型的竞争压力。
- OpenAI 近期披露的基础设施扩张（俄亥俄州 PORTS-Pike 园区约 8 IT-GW 算力、与 Oracle 的 3000 亿美元合作、与 AMD 的 6GW GPU 部署协议等）被视为降价空间来源。

## 为什么重要
- 这是 OpenAI 首次对旗舰模型 Sol 进行实质性降价，标志着 AI 大模型竞争从能力竞争扩展到价格战，且火力集中到最高端产品线。
- 相比已有相关卡片（GPT-5.6 发布、分档信息、Claude 额度重置），本卡片的增量信息在于：Sol 降价的具体幅度与生效方式、原因、Anthropic IPO 背景、DeepSeek/神秘模型竞争压力，以及 Codex 活跃用户里程碑和风控表态。
- 降价如果持续，可能影响企业级 AI 采购决策，也会对 Anthropic、Google、中国模型厂商的定价策略形成压力。

## 局限与不确定性
- 关于 Anthropic 于 2026 年 6 月 1 日向 SEC 递交 S-1、估值约 2 万亿美元、最快 10 月在纳斯达克上市等细节，均来自“多家媒体报道”，尚未获得 Anthropic 官方确认，待核实。
- 神秘模型“Ox Alpha”的来源、发布方和真实能力无法从本文确认，待核实。
- “8 IT-GW”按原文保留，具体含义（是否为“GW”笔误或特定计量单位）待核实。
- Codex 负责人 Tibo 称“目前没有发现异常”但“正式调查已启动”，因此额度消耗问题尚无最终结论。
- 降价是否覆盖所有地区、所有客户类型，以及“未来三个月”之后的价格走势，文中未说明，待核实。

## 可用于图书/PPT/简报的角度
- AI 价格战：旗舰模型主动降价，标志头部厂商进入以价格换市场的阶段。
- 成本飞轮：模型效率提升 → 推理成本下降 → 价格空间释放 → 用户涌入 → 收入增长 → 再投基建。
- 竞争格局：OpenAI 对 Anthropic 的 IPO 窗口施压，同时防守中国低价模型。
- API 定价策略：从按量付费到 credit 调整，企业用户如何计算真实成本。
- Codex 用户规模与风控：订阅转售、sub2api 等灰色玩法被明确禁止。

## 英文标题
原文为中文标题，暂无官方英文标题；对应英文可译为：**GPT-5.6 Sol Big Price Cut! OpenAI Brings Price War to Flagship**

## 英文关键词
GPT-5.6 Sol, OpenAI, price cut, API pricing, Anthropic, DeepSeek, Codex

## 原始材料
- 来源：新智元（作者：AIERA）
- 发布于：2026 年 8 月 23 日
- URL: https://aiera.com.cn/2026/08/23/other/admin/110248/%e7%aa%81%e5%8f%91%ef%bc%9agpt-5-6-sol%e5%a4%a7%e9%99%8d%e4%bb%b7%ef%bc%81openai%e6%8a%8a%e4%bb%b7%e6%a0%bc%e6%88%98%e7%83%a7%e5%88%b0%e6%97%97%e8%88%b0