---
book_potential: 3
collected_date: '2026-07-12'
confidence: 3
created_at: '2026-07-12T09:18:50+08:00'
date: '2026-07-12'
entities:
- www.llamaindex.ai
id: 2026-07-12-academic-foundation-model-parsing-the-unreadable-how-llamaparse-handles-le
importance: 4
keywords_en: &id001
- foundation-model
novelty: 3
ppt_potential: 4
primary_source: true
public_brief_potential: 4
review_status: rejected
source_type: paper
source_url: https://www.llamaindex.ai/blog/parsing-the-unreadable-how-llamaparse-handles-legal-discovery-documents
title_en: 'Parsing the Unreadable: How LlamaParse Handles Legal Discovery Documents'
title_zh: 'Parsing the Unreadable: How LlamaParse Handles Legal Discovery Documents'
topics: *id001
track: academic
---

# 知识卡片：Parsing the Unreadable: How LlamaParse Handles Legal Discovery Documents

**英文标题**：Parsing the Unreadable: How LlamaParse Handles Legal Discovery Documents  
**英文关键词**：llamaparse, legal discovery, document parsing, OCR, multimodal  
**原始来源**：https://www.llamaindex.ai/blog/parsing-the-unreadable-how-llamaparse-handles-legal-discovery-documents

## 一句话结论
LlamaParse 通过多模态模型和自然语言自定义指令，显著提升法律发现（eDiscovery）文档的解析质量，能处理低分辨率扫描、保留视觉内容（照片、图表、表格），并降低传统 OCR 的间距断裂等错误，使下游搜索和分类系统获得更完整的索引。

## 事件概述
在法律诉讼的“发现”（discovery）阶段，诉讼双方需交换大量文件。这些文件常是扫描件（低分辨率、黑白、旋转），且包含照片、PPT、表格、手写注释等非文本内容。传统 OCR 在低质量扫描上表现差，容易产生错误间距（如 “settlement” 变为 “s ettl em ent”），且无法提取视觉信息。LlamaParse 被设计用于处理这类复杂文档，作为 eDiscovery 平台的解析基础层。

## 方法/产品要点
- **底层技术**：使用多模态视觉模型解释页面内容，而非单纯像素级文本识别。可输出 `markdown`（LLM友好）、`text`（纯文本）、`items`（布局树，含表格/图形位置）。
- **关键参数**：
  - `tier="agentic_plus"`：针对复杂布局和视觉内容优化，高分辨率 OCR 对退化扫描有效。
  - `custom_prompt`：支持自然语言写解析指令，例如提取所有可见文本但修正 OCR 假阳性空格，识别照片中是否有人，提取表格数据，单独标注手写注释，保留案件编号/bates编号。
- **工作流**：先上传文件，再启动解析任务，可指定多种输出视图和表格输出格式。

## 主要结果或产业意义
- 低质量扫描仍可输出可用结果（模糊、倾斜、低 DPI 下依然有效）。
- 照片和图表能被描述或提取数据，使得视觉内容不再对搜索系统“不可见”。
- 法律发现流程中，更好的解析减少了相关文档被遗漏的可能性，提升语义搜索和分类的召回率。
- 传统 eDiscovery 平台（如 Relativity、Everlaw、DISCO）的文档索引质量直接受限于底层解析的准确性。

## 为什么重要
法律发现文档解析是整个 eDiscovery 流程的“地基”。传统方法依赖正则和纯 OCR，既脆弱又完全忽略视觉内容。LlamaParse 使得律师团队无需手动标记每张照片、图表，即可通过语义搜索找到包含特定视觉证据的文档，大幅减少人工筛选工作量。本文提供了具体的配置代码，展示了如何针对法律发现场景定制解析行为。

## 局限与不确定性
- 材料中未提供与竞品（如传统 OCR 工具或其他解析服务）的量化性能对比（如召回率、准确率提升数值）。
- 未提及解析大体积文档（数十万页）的成本或耗时。
- 文中强调“没有解析工具能让发现变得简单”，但未给出实际使用中的失败案例或边界（如极端模糊的手写、重叠文字）。

## 可用于图书/PPT/简报的角度
- **法律科技案例**：展示 AI 文档解析如何解决一个典型的高价值行业痛点。
- **多模态模型应用**：从“文本提取”升级为“视觉理解”，打开非结构化数据利用的新窗口。
- **提示工程在文档解析中的作用**：`custom_prompt` 参数体现了用自然语言引导模型关注特定内容的价值。
- **eDiscovery 工作流改进**：具体代码片段可被直接引用为最佳实践。

## 与既有脉络的关系
已有卡片“ParseBench——首个面向AI Agent的文档解析基准测试”中报道了 LlamaParse Agentic 在基准上的总体得分。本文则聚焦于法律发现这一特定垂直场景，详细说明了如何配置解析参数（如 `agentic_plus` tier 和 `custom_prompt`），并解释了为什么视觉内容提取对法律文档检索至关重要——这是基准测试未覆盖的实际业务逻辑。增量信息在于**场景化的配置指南**和**定性效益描述**。

## 原始材料
- 文章标题：Parsing the Unreadable: How LlamaParse Handles Legal Discovery Documents
- 作者：Tuana Çelik
- 发布平台：LlamaIndex 博客
- 发布日期：待核实（文中提及相关文章日期为2026年6月，推断本文同样发布于2026年左右）
- 链接：https://www.llamaindex.ai/blog/parsing-the-unreadable-how-llamaparse-handles-legal-discovery-documents