---
auto_review_age_days: 1
auto_review_reasons:
- importance:5+10
- novelty:5+10
- confidence:3+6
- ppt_potential:5+5
- public_brief_potential:4+4
- topic_priority:5+10
- source_type:chinese-media-2
- primary_source+2
- 'score>=28: 自动接受'
auto_review_score: 45
book_potential: 5
collected_date: '2026-07-19'
confidence: 3
created_at: '2026-07-19T08:03:52+08:00'
date: '2026-07-15'
entities:
- aiera.com.cn
event_date: '2026-07-15'
id: 2026-07-15-industry-ai-industry-deepmind
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
reviewed_at: '2026-07-20T08:05:13+08:00'
reviewed_by: auto
source_type: chinese-media
source_url: https://aiera.com.cn/2026/07/19/other/admin/104753/deepmind%e7%a7%91%e5%ad%a6%e5%ae%b6%e6%84%a4%e7%84%b6%e7%a6%bb%e8%81%8c%ef%bc%8c%e4%b8%87%e5%ad%97%e9%95%bf%e6%96%87%e6%8f%ad%e9%9c%b2%e8%b0%b7%e6%ad%8c%e7%bd%aa%e6%81%b6%ef%bc%81
title_en: DeepMind科学家愤然离职，万字长文揭露谷歌罪恶！
title_zh: DeepMind科学家愤然离职，揭露谷歌军事AI协议内幕
topics: *id001
track: industry
---

# 知识卡片：DeepMind科学家愤然离职，揭露谷歌军事AI协议内幕

**一句话结论**  
前谷歌DeepMind科学家Alex Turner于2026年7月15日辞职，并发布万字长文，指控谷歌高层在五角大楼压力下秘密签署一份“毫无红线”的军事AI协议，将Gemini模型部署于军方隔离数据中心，使谷歌丧失对模型思维链的监控能力，且多位曾公开反对致命自主武器的AI领袖（Jeff Dean、Demis Hassabis、Yoshua Bengio、Stuart Russell）在此过程中默许或袖手旁观。

**事件概述**  
2026年1月，美国国土安全部特工街头枪杀平民，Turner发现谷歌是DHS的云与AI供应商。随后五角大楼向AI巨头施压，要求签署允许“任何合法政府用途”的军事AI合同。Anthropic拒绝并遭供应链威胁，而谷歌高层准备妥协。Turner于2026年4月27日晚得知合同正式签署，合同中限制自主武器和大规模监控的条款仅使用无法律约束力的“不应该”措辞，且谷歌将Gemini服务器物理部署于军方隔离数据中心，完全放弃对思维链的监控。Turner历时数月撰写25页《军事AI红线与监督框架》、收集约250名员工签名，并试图说服Jeff Dean和Demis Hassabis，均遭“已读不回”或敷衍回应。多位学术泰斗（如Bengio、Russell）也拒绝发声或撤回公开承诺。Turner最终辞职，并称自己选择成为一名失业者。

**方法/产品要点**  
- 谷歌与五角大楼的合同条款：允许“任何合法政府用途”，缺乏对致命自主武器和大规模监控的明确红线。
- 技术部署方式：谷歌将装有Gemini模型的服务器物理部署在军方隔离的数据中心，谷歌失去对模型思维链（CoT）的实时监控能力，军方缺乏AI对齐训练工程师。
- Turner提出的替代方案：25页《军事AI红线与监督框架》，包含审查机制、禁止无人类控制的致命武器和无差别监控等条款，被军事与监控法专家评价“相当出色”，但高层从未阅读。

**主要结果或产业意义**  
- 谷歌（2026年4月27日）正式签署该军事AI协议，标志着DeepMind创始时“AI绝不用于军事和武器”的承诺被彻底放弃（2025年2月Demis参与修改AI原则，删除禁止武器条款）。
- 事件暴露AI行业巨头在商业利益与军事压力下的伦理失守，以及表面上拥护AI安全的学术界领袖在关键时刻的沉默。
- Turners的长文（turntrout.com/why-i-left-google-deepmind）成为行业公开信，引发对前沿AI军事部署安全风险的广泛讨论。

**为什么重要**  
- 该事件是继2018年Google Project Maven争议后最严重的军事AI合作丑闻，且直接涉及DeepMind（曾被视作伦理标杆）。
- 与已有相关卡片（如NIST AI RMF、AlphaEvolve、AlphaEarth）形成对比：此前卡片多关注技术进展或框架制定，本卡片揭示在底层伦理红线和实际商业决策中的系统性失败。
- 新增增量信息：具体揭露了合同签署时间（2026年4月27日）、物理部署方式（失去CoT监控）、关键人物（Jeff Dean、Demis等）的实际行动与承诺之间的断裂，以及Turner的25页框架被高层忽视的细节。

**局限与不确定性**  
- 本卡片的全部事实来源于Alex Turner的公开长文及新智元的报道，无法独立核实其所有指控（如五角大楼施压细节、高层内部沟通记录）。待核实：谷歌官方是否正式承认该合同存在？Demis Hassabis是否真的声称“AI原则没有改变”？Jeff Dean是否确实签署了2018年反自主武器誓言但未采取进一步行动？
- 合同中“不应该”条款的具体法律效力待核实；军方是否真的缺乏AI对齐工程师待核实。
- Turners的个人动机和离职背景已由本人陈述，但谷歌及被点名人士的回应尚未公开发布。

**可用于图书/PPT/简报的角度**  
- 案例研究：AI伦理承诺与商业现实冲突的典型，适合商业伦理、科技政策课程。
- 技术风险警示：模型思维链监控缺失在军事部署中的灾难性后果，适合AI安全专题。
- 组织行为分析：内部 whistleblower（吹哨人）的困境、高层“已读不回”现象，适合领导力培训。
- 时间线梳理：2018年反自主武器誓言 → 2025年谷歌修改AI原则 → 2026年合同签署 → 2026年7月Turner辞职发帖，展现监管与军工复合体的演进。

**英文标题**  
DeepMind scientist quits, reveals Google’s secret military AI deal in a 10,000-word exposé

**英文关键词**  
Google DeepMind, military AI, lethal autonomous weapons, Gemini, CoT monitoring, AI ethics, whistleblower, Alex Turner

**原始材料**  
- Alex Turner 辞职声明与长篇揭露：https://turntrout.com/why-i-left-google-deepmind
- Turner 撰写的《军事AI红线与监督框架》：https://turntrout.com/red-line-framework
- 新智元报道（本文来源）：https://aiera.com.cn/2026/07/19/other/admin/104753/deepmind%e7%a7%91%e5%ad%a6%e5%ae%b6%e6%84%a4%e7%84%b6%e7%a6%bb%e8%81%8c%ef%bc%8c%e4%b8%87%e5%ad%97%e9%95%bf%e6%96%87%e6%8f%ad%e9%9c%b2%e8%b0%b7%e6%ad%8c%e7%bd%aa%e6%81%b6%ef%bc%81