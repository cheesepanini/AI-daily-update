---
auto_review_age_days: 1
auto_review_reasons:
- importance:5+10
- novelty:5+10
- confidence:4+8
- ppt_potential:5+5
- public_brief_potential:4+4
- topic_priority:5+10
- source_type:chinese-media-2
- primary_source+2
- 'score>=28: 自动接受'
auto_review_score: 47
book_potential: 5
collected_date: '2026-07-22'
confidence: 4
created_at: '2026-07-22T08:04:06+08:00'
date: '2026-07-22'
entities:
- aiera.com.cn
event_date: '2026-07-22'
id: 2026-07-22-industry-ai-industry-7-fable-5
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
reviewed_at: '2026-07-23T08:14:07+08:00'
reviewed_by: auto
source_type: chinese-media
source_url: https://aiera.com.cn/2026/07/22/other/admin/105334/%e7%aa%81%e5%8f%91%ef%bc%81%e8%ae%a9%e5%bc%a0%e7%9b%8a%e5%94%90%e8%8b%a6%e7%86%ac7%e5%b9%b4%e7%9a%84%e9%9b%85%e5%8f%af%e6%af%94%e7%8c%9c%e6%83%b3%ef%bc%8cfable-5%e7%ab%9f%e4%b8%80%e5%a4%9c%e6%8e%a8
title_en: 突发！让张益唐苦熬7年的雅可比猜想，Fable 5竟一夜推翻证伪
title_zh: Fable 5推翻证伪雅可比猜想，张益唐七年苦熬成注脚
topics: *id001
track: industry
---

# 知识卡片：Fable 5推翻证伪雅可比猜想，张益唐七年苦熬成注脚

**一句话结论**  
Anthropic 的 Claude Fable 5 给出了一个简洁反例，证明了广义三维雅可比猜想不成立。该结果显示 AI 已具备真正的数学创造力，但二维情形的核心问题仍未解决。

**事件概述**  
2026 年 7 月 22 日，Anthropic 研究人员 Levent Alpoge 在 X 上发布推文，宣布 Claude Fable 5 证伪了自 1939 年提出的雅可比猜想（Jacobian Conjecture）。该猜想由德国数学家 Ott-Heinrich Keller 提出，询问：如果一个多项式映射的雅可比行列式是非零常数，该映射是否一定存在多项式逆映射？这个问题困扰数学界 87 年，二维情形更早在 1884 年出现。Fable 5 在三维空间 \( \mathbb{C}^3 \) 中给出一个反例：一个雅可比行列式恒等于 -2 的多项式映射，却将三个不同点映射到同一个像点，从而证明其非单射，进而否定逆映射的存在。该反例简洁到可手算验证，随后被 Wolfram Alpha 等工具确认。GPT-5.6 和 OpenAI 的 Aaron Lou（使用内部 Codex）也独立推导出本质相同的反例，并提出修正后的新猜想。

**方法/产品要点**  
- **Claude Fable 5**：Anthropic 发布的旗舰大语言模型，此次展现的是数学推理与反例构造能力，而非仅模仿已有知识。  
- **协作过程**：研究人员输入问题后，Fable 5 直接输出反例，未依赖人类逐步提示。  
- **验证工具**：反例可通过大学微积分水平的求偏导和代入法人工验证，也可通过 Wolfram Alpha 等工具快速核验。

**主要结果**  
- 广义三维雅可比猜想被证伪，一个 87 年历史的开放问题得到否定答案。  
- 多位数学家（如 Jared Duker Lichtman、菲尔兹奖得主 Timothy Gowers）公开表达震撼，称“数学可能已经被解决”。  
- GPT-5.6 在分析后提出了修正版本的猜想，展示了 AI 不仅能证伪，还能推动新的理论方向。  
- 该事件也重新引发人们对张益唐早年经历的讨论：张益唐在普渡大学攻读博士期间，因导师莫宗坚提供的错误引理而耗费七年试图证明二维雅可比猜想，最终论文失败并在赛百味打工多年。此次证伪的是三维版本，二维猜想仍未被解决。

**为什么重要**  
- **数学史转折**：这是大型语言模型首次独立攻克一个长期未决的重大数学猜想，标志着 AI 从“解题工具”向“数学创造者”的跨越。  
- **对张益唐的呼应**：张益唐曾因导师坚持相信雅可比猜想而虚耗七年，如今 AI 用简单反例证伪了更广义的版本，引发学界对当年学术责任与路径选择的反思。  
- **连锁反应**：数学家们预计，该反例可能引发一系列相关猜想的证伪浪潮，如多项式自同构猜想等。  
- **与既有脉络的关系**：此前已有卡片报道 Claude Fable 5 永久可用（2026-07-19），但未涉及具体能力。本条卡片展示了该模型在数学前沿的突破性应用，是 AI 能力从“可用”到“能创新”的关键增量。

**局限与不确定性**  
- 证伪的仅是 **三维** 雅可比猜想，二维情形（张益唐当年研究的主题）被认为数学意义更大且难度更高，目前仍然未解决。  
- AI 的“创造力”是否完全自主存在争议：研究人员 Levent Alpoge 提到是好友 akhil 提问后才触发生成，Fable 5 的原始输出是否经过人类在提示中的引导尚未完全公开。  
- 反例的发现过程细节（如是否依赖预训练数据中的类似构造）未披露，需要进一步验证其“偶然性”与“系统性”的平衡。  
- 修正后的新猜想尚未经过严格同行评议，其正确性待核实。

**可用于图书/PPT/简报的角度**  
1. **AI 与数学研究**：作为 AI 推动基础数学突破的典型案例，可对比传统“人肉苦熬”与“AI 一击”的效率差异。  
2. **学术伦理与导师影响**：张益唐的故事提醒我们，学术权威的错误判断可能浪费天才的黄金岁月，而 AI 的客观性或许能减少此类悲剧。  
3. **局部 vs 全局**：雅可比猜想是“局部性质推导全局性质”的经典难题，适合在数学或 AI 通识课中讲解反例的思维价值。  
4. **连锁反应猜想**：可用于解释数学中一个命题的证伪如何引发一系列重新审视（类似多米诺骨牌）。

**英文关键词**  
Jacobian conjecture, Claude Fable 5, mathematical reasoning, counterexample, Zhang Yitang, GPT-5.6

**原始材料**  
- URL: https://aiera.com.cn/2026/07/22/other/admin/105334/  
- 标题：突发！让张益唐苦熬7年的雅可比猜想，Fable 5竟一夜推翻证伪 – 新智元  
- 发布时间：2026年7月22日  
- 部分关键引用：反例公式、Levent Alpoge 的推文、Jason Lee 的评论、Aaron Lou 的完整推导文档（https://aaronlou.com/jacobian_counterexample_derivation.pdf）