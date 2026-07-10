# AI-Daily-Update V0.1 设计说明

## 1. 项目定位

AI-Daily-Update 是一个本地运行、后续可迁移到 Ubuntu 工作站的 AI 学术与产业进展知识库流水线。

系统每天自动抓取配置源，调用 OpenAI API 生成中文知识卡片草稿，用户用约 5 分钟通过 CLI 完成 review，最终将确认后的内容沉淀为 Markdown 知识库，并支持按主题和时间段生成简报。

核心原则：

- 自动抓取，人工确认入库。
- Markdown 作为主知识资产，SQLite 作为索引和查询加速层。
- 中文正文，保留英文标题、英文关键词和原始来源。
- 先跑通 CLI 工作流，再做 dashboard。
- 先生成 Markdown 简报，后续再考虑 PPTX、公众号排版和网站发布。

## 2. V0.1 范围

### 2.1 V0.1 要做

- 自动抓取 arXiv、RSS、公司官方博客等来源。
- 根据 YAML 配置维护主题、数据源和评分规则。
- 每天保留候选池，但最多生成 5 张完整知识卡片。
- 调用 OpenAI API 完成中文摘要、分类、评分和卡片草稿生成。
- 通过 CLI 完成 review：accept / later / reject / edit / open source。
- 通过 frontmatter 的 `review_status` 管理卡片状态，不移动文件。
- 使用 SQLite 索引 Markdown 卡片元数据。
- 支持按时间段、主题和用途生成 Markdown 简报。
- 支持先在 Windows 本机测试，后续迁移到 Ubuntu 工作站。

### 2.2 V0.1 暂不做

- 不做本地 dashboard。
- 不做自动发布公众号或个人网站。
- 不做 PPTX 自动生成。
- 不做社交媒体抓取。
- 不做微信公众号抓取。
- 不做复杂知识图谱。
- 不做完全无人值守入库。
- 不做大规模产业统计数据库，先保守处理。

## 3. 信息通道设计

V0.1 采用双通道：

- Academic Track：学术前沿。
- Industry Track：AI 产业观察。

每日默认额度：

- 学术前沿：最多 3 张卡片。
- 产业观察：最多 2 张卡片。
- 每日总量：最多 5 张完整卡片。

系统可以抓取更多候选内容，但只为评分最高、最值得 review 的条目生成完整卡片。

推荐流水线：

```text
candidates: 50
shortlisted: 10
generated_cards: 5
```

## 4. 推荐目录结构

```text
AI-Daily-Update/
  config/
    topics.yaml
    sources.yaml
    scoring.yaml
    prompts.yaml
    app.yaml

  data/
    kb.sqlite
    manual_urls.txt
    raw/
    cache/
    logs/

  notes/
    inbox/
    cards/
      2026/
        07/
    topics/
    briefs/
      academic/
      industry/
      book/
      public/

  src/
    ai_daily_update/
      __init__.py
      cli.py

      collectors/
        arxiv.py
        rss.py
        company_blogs.py
        manual.py

      processors/
        dedupe.py
        classify.py
        score.py
        summarize.py
        card_builder.py

      storage/
        db.py
        markdown.py
        indexer.py

      review/
        workflow.py

      reports/
        daily.py
        brief.py
        slides_outline.py

      llm/
        client.py
        prompts.py

      utils/
        dates.py
        slug.py
        paths.py

  tests/
    test_dedupe.py
    test_markdown.py
    test_scoring.py
    test_slug.py

  pyproject.toml
  README.md
  .env.example
```

说明：

- `notes/cards/` 是长期知识资产。
- 卡片按照年份和月份存放，不按照 review 状态移动。
- review 状态只通过 frontmatter 字段 `review_status` 管理。
- `data/kb.sqlite` 可以随时通过 Markdown 重建，不应成为唯一事实来源。

## 5. 配置设计

### 5.1 app.yaml

```yaml
project_name: AI-Daily-Update
language: zh
timezone: Asia/Shanghai

daily:
  max_cards: 5
  academic_quota: 3
  industry_quota: 2
  candidate_limit: 50
  shortlist_limit: 10

storage:
  markdown_root: notes
  sqlite_path: data/kb.sqlite

llm:
  provider: openai
  model: ${OPENAI_MODEL}
  api_key_env: OPENAI_API_KEY

review:
  statuses:
    - needs-review
    - accepted
    - later
    - rejected
```

### 5.2 .env.example

```bash
OPENAI_API_KEY=your_api_key_here
OPENAI_MODEL=your_preferred_model
```

模型名不应写死在代码里，便于后续替换。

## 6. 主题配置

`config/topics.yaml`：

```yaml
tracks:
  academic:
    name_zh: 学术前沿
    daily_quota: 3

  industry:
    name_zh: AI 产业观察
    daily_quota: 2

topics:
  foundation-model:
    name_zh: 预训练大模型
    name_en: Foundation Models
    track: [academic, industry]
    priority: 5
    aliases:
      - large language model
      - LLM
      - foundation model
      - pretrained model
      - multimodal foundation model

  self-supervised-learning:
    name_zh: 自监督学习
    name_en: Self-Supervised Learning
    track: [academic]
    priority: 4
    aliases:
      - self-supervised learning
      - contrastive learning
      - masked modeling
      - representation learning

  generative-model:
    name_zh: 生成模型
    name_en: Generative Models
    track: [academic, industry]
    priority: 5
    aliases:
      - diffusion model
      - flow matching
      - autoregressive model
      - video generation
      - image generation
      - world model

  intelligent-game:
    name_zh: 智能博弈
    name_en: Intelligent Game
    track: [academic]
    priority: 3
    aliases:
      - game AI
      - multi-agent game
      - strategic reasoning
      - reinforcement learning game

  spatial-intelligence:
    name_zh: 空间智能
    name_en: Spatial Intelligence
    track: [academic, industry]
    priority: 5
    aliases:
      - spatial reasoning
      - 3D understanding
      - embodied spatial intelligence
      - world model
      - scene understanding

  agent:
    name_zh: 智能体
    name_en: AI Agents
    track: [academic, industry]
    priority: 5
    aliases:
      - AI agent
      - autonomous agent
      - tool use
      - agent workflow
      - multi-agent system
      - computer use agent

  ai4science:
    name_zh: AI4S
    name_en: AI for Science
    track: [academic, industry]
    priority: 4
    aliases:
      - AI for Science
      - scientific foundation model
      - protein model
      - materials discovery
      - drug discovery

  ai-industry:
    name_zh: AI 产业
    name_en: AI Industry
    track: [industry]
    priority: 5
    aliases:
      - AI market
      - AI company
      - AI startup
      - AI platform
      - AI application

  ai-compute:
    name_zh: AI 算力
    name_en: AI Compute
    track: [industry]
    priority: 4
    aliases:
      - AI chip
      - GPU cluster
      - training compute
      - inference infrastructure
      - datacenter

  ai-policy:
    name_zh: AI 政策
    name_en: AI Policy
    track: [industry]
    priority: 4
    aliases:
      - AI regulation
      - AI governance
      - AI policy
      - model safety regulation

future_topics:
  autonomous-driving:
    name_zh: 自动驾驶
    enabled: false

  humanoid-robot:
    name_zh: 人形机器人
    enabled: false

  uav:
    name_zh: 智能无人机
    enabled: false
```

## 7. 数据源配置

`config/sources.yaml`：

```yaml
sources:
  arxiv:
    enabled: true
    track: academic
    categories:
      - cs.AI
      - cs.CL
      - cs.LG
      - cs.CV
      - stat.ML
    max_results_per_day: 50

  rss:
    enabled: true
    feeds:
      - name: OpenAI News
        track: industry
        url: https://openai.com/news/rss.xml

      - name: Anthropic News
        track: industry
        url: https://www.anthropic.com/news/rss.xml

      - name: Google DeepMind Blog
        track: industry
        url: https://deepmind.google/discover/blog/rss.xml

      - name: Hugging Face Blog
        track: academic
        url: https://huggingface.co/blog/feed.xml

  company_blogs:
    enabled: true
    track: industry
    sources:
      - OpenAI
      - Anthropic
      - Google DeepMind
      - Meta AI
      - Microsoft AI
      - NVIDIA
      - Hugging Face

  manual:
    enabled: true
    input_file: data/manual_urls.txt
```

注意：RSS 和公司网页结构可能变化，因此 V0.1 必须保留 `manual_urls.txt`。自动抓取失败时，可以手动添加 URL，让系统继续完成卡片化。

## 8. 卡片模板

### 8.1 学术卡片

```markdown
---
id: 2026-07-06-academic-foundation-model-example
track: academic
title_zh: "中文标题"
title_en: "Original English Title"
date: 2026-07-06
source_type: paper
source_url: "https://..."
primary_source: true

topics:
  - foundation-model
  - agent

keywords_en:
  - foundation model
  - AI agent

entities:
  - Example Lab

importance: 4
novelty: 4
confidence: 3
book_potential: 4
ppt_potential: 4
public_brief_potential: 2

review_status: needs-review
created_at: 2026-07-06T09:00:00+08:00
---

## 一句话结论

## 研究问题

## 方法要点

## 主要结果

## 为什么重要

## 与既有脉络的关系

## 局限与不确定性

## 可用于图书更新的角度

## 可用于 PPT 的表达

## 原始材料
```

### 8.2 产业卡片

```markdown
---
id: 2026-07-06-industry-ai-compute-example
track: industry
title_zh: "中文标题"
title_en: "Original English Title"
date: 2026-07-06
source_type: company-news
source_url: "https://..."
primary_source: true

topics:
  - ai-industry
  - ai-compute

industry_dimensions:
  - company
  - compute
  - platform

entities:
  - Example Company

importance: 4
novelty: 3
confidence: 3
book_potential: 3
ppt_potential: 4
public_brief_potential: 5

review_status: needs-review
created_at: 2026-07-06T09:00:00+08:00
---

## 一句话结论

## 事件概述

## 涉及主体

## 产业意义

## 与技术脉络的关系

## 可验证信息

## 潜在夸大或不确定性

## 可用于简报/公众号的角度

## 可用于 PPT 的表达

## 原始材料
```

## 9. OpenAI API 使用边界

OpenAI API 在 V0.1 中只负责：

- 中文摘要。
- 主题分类。
- 重要性、新颖性、置信度评分。
- 生成知识卡片正文草稿。
- 基于已入库卡片生成简报草稿。

OpenAI API 不负责：

- 自主决定无限扩展哪些网站。
- 自主修改主题体系。
- 无来源地生成事实。
- 自动将卡片从 `needs-review` 改为 `accepted`。

LLM 是加工器，不是事实源。事实必须来自 `source_url` 和原始材料。

## 10. CLI 命令设计

```bash
ai-daily doctor
```

检查配置、OpenAI API key、目录权限、数据库状态和数据源可访问性。

```bash
ai-daily daily
```

执行每日流水线：抓取候选、去重、分类、评分、生成 inbox 和最多 5 张卡片。

```bash
ai-daily review
```

逐条 review `needs-review` 卡片。支持：

- accept
- later
- reject
- edit metadata
- open source

```bash
ai-daily index
```

重新扫描 Markdown 卡片，重建 SQLite 索引。

```bash
ai-daily brief --from 2026-07-01 --to 2026-07-31 --topics foundation-model,agent --audience academic
```

按时间段、主题和用途生成 Markdown 简报。

可选 audience：

- `academic`
- `industry`
- `book`
- `public`

## 11. 简报模板

### 11.1 学术报告版

```markdown
# 2026 年 7 月 AI 学术前沿简报

## 核心判断

## 重要进展

## 技术脉络变化

## 代表性论文与系统

## 对后续研究的启示

## 可用于 PPT 的页面建议

## 参考材料
```

### 11.2 图书更新版

```markdown
# 图书内容更新候选：2026 年 7 月

## 建议更新章节

## 新增概念

## 新增案例

## 需要修订的判断

## 可引用材料

## 参考来源
```

### 11.3 公众号/网站版

```markdown
# 本月 AI 进展观察

## 开头摘要

## 值得关注的 5 个变化

## 学术前沿

## 产业动态

## 一个关键趋势

## 延伸阅读
```

公众号/网站版应优先使用 `public_brief_potential >= 3` 的卡片。

## 12. Windows 到 Ubuntu 的迁移要求

V0.1 必须从一开始支持后续迁移：

- 所有路径使用 Python `pathlib`。
- 配置中不写死 Windows 盘符。
- 默认 UTF-8。
- Markdown 文件名使用英文、数字和短横线。
- `.env` 保存 API key，不进入 Git。
- SQLite 路径通过配置指定。
- 日志写入 `data/logs/`。
- 定时任务先不写死，后续分别提供 Windows Task Scheduler 和 Ubuntu cron/systemd 示例。

推荐文件名：

```text
2026-07-06-academic-foundation-model-agent-evaluation.md
2026-07-06-industry-ai-compute-nvidia-platform.md
```

## 13. 实施顺序

建议按以下顺序实现：

1. 创建项目骨架和配置文件。
2. 实现 Markdown 卡片读写。
3. 实现 SQLite 索引。
4. 实现 `manual_urls.txt` 输入。
5. 实现 OpenAI 卡片生成。
6. 实现去重和评分。
7. 实现 daily inbox。
8. 实现 CLI review。
9. 实现 brief 生成。
10. 实现 arXiv 抓取。
11. 实现 RSS 抓取。
12. 实现公司博客抓取。
13. 增加 Windows/Ubuntu 定时任务说明。

优先跑通最小链路：

```text
manual_urls.txt
-> OpenAI 生成卡片
-> notes/cards/YYYY/MM/*.md
-> ai-daily review
-> SQLite 索引
-> ai-daily brief
```

再逐步接入 arXiv、RSS 和公司博客。

## 14. V0.1 验收标准

V0.1 完成标准：

- `ai-daily doctor` 能检查环境。
- `ai-daily daily` 能自动抓取并生成当天 inbox。
- 每天最多生成 5 张 `needs-review` 卡片。
- 卡片默认中文正文，保留英文标题、英文关键词和来源链接。
- `ai-daily review` 能修改卡片 frontmatter 中的 `review_status`。
- `ai-daily index` 能重建 SQLite 索引。
- `ai-daily brief` 能按时间段、主题和用途生成 Markdown 简报。
- 所有 `accepted` 卡片都有 `source_url`、`date`、`topics`、`review_status`。
- 项目可以在 Windows 本机运行，并能迁移到 Ubuntu 工作站。

## 15. 后续阶段

### V0.2

- 增强 arXiv、RSS、公司博客抓取。
- 增加 Hugging Face、GitHub 等源。
- 增加更好的去重和相似内容合并。
- 增加 topic note 自动更新。

### V0.3

- 增加本地 dashboard。
- 支持 inbox 可视化 review。
- 支持按主题、时间、实体筛选卡片。

### V0.4

- 支持 PPT 大纲生成。
- 支持时间线、技术地图、对比表。
- 支持 Marp / Reveal.js / Quarto 等 slides Markdown 输出。

### V0.5

- 支持公众号/网站发布草稿。
- 支持更多产业数据源。
- 支持 Ubuntu 上的 cron 或 systemd timer 自动运行。
