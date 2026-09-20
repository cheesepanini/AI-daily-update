import json

from ai_daily_update.reports.brief import generate_brief
from ai_daily_update.storage.indexer import rebuild_index
from ai_daily_update.storage.markdown import write_card


class FakeClusteringLLM:
    available = True

    def generate_card_content(self, prompt):
        return json.dumps({"groups": [{"indices": [0, 1]}]})


def test_generate_brief_uses_card_content_sections(tmp_path) -> None:
    markdown_root = tmp_path / "notes"
    card_path = markdown_root / "cards" / "2026" / "07" / "card.md"
    write_card(
        card_path,
        {
            "id": "card-1",
            "track": "industry",
            "title_zh": "Claude Tag 团队协作新方式",
            "title_en": "Introducing Claude Tag",
            "date": "2026-06-23",
            "source_url": "https://www.anthropic.com/news/introducing-claude-tag",
            "topics": ["ai-industry"],
            "entities": ["anthropic.com"],
            "review_status": "accepted",
        },
        """# 知识卡片

**一句话结论**
Claude Tag 让 Claude 以团队成员身份加入 Slack。

**事件概述**
2026 年 6 月 23 日，Anthropic 发布了 Claude Tag。

**产业意义**
它把 AI 从对话助手推进到团队协作者。

**局限与不确定性**
当前仅限 Enterprise 和 Team 客户 beta 使用。
""",
    )
    sqlite_path = tmp_path / "data" / "kb.sqlite"
    rebuild_index(markdown_root, sqlite_path)

    output_path = generate_brief(
        sqlite_path,
        markdown_root,
        "2026-06-01",
        "2026-06-30",
        None,
        "industry",
    )

    text = output_path.read_text(encoding="utf-8")
    assert "待根据以下卡片整理" not in text
    assert "Claude Tag 让 Claude 以团队成员身份加入 Slack" in text
    assert "2026 年 6 月 23 日，Anthropic 发布了 Claude Tag" in text
    assert "它把 AI 从对话助手推进到团队协作者" in text


def test_generate_brief_creates_unique_paths_for_same_range(tmp_path) -> None:
    markdown_root = tmp_path / "notes"
    sqlite_path = tmp_path / "data" / "kb.sqlite"

    first = generate_brief(
        sqlite_path,
        markdown_root,
        "2026-07-06",
        "2026-07-07",
        None,
        "industry",
    )
    second = generate_brief(
        sqlite_path,
        markdown_root,
        "2026-07-06",
        "2026-07-07",
        None,
        "industry",
    )

    assert first.name == "2026-07-06_to_2026-07-07_collected_all.md"
    assert second.name == "2026-07-06_to_2026-07-07_collected_all-2.md"


def test_generate_brief_merges_duplicate_items_via_llm_clustering(tmp_path) -> None:
    markdown_root = tmp_path / "notes"
    write_card(
        markdown_root / "cards" / "2026" / "07" / "card-a.md",
        {
            "id": "card-a",
            "track": "industry",
            "title_zh": "某模型发布（媒体 A 报道）",
            "title_en": "Model launch (outlet A)",
            "date": "2026-07-06",
            "source_url": "https://a.example.com/news",
            "topics": ["ai-industry"],
            "entities": [],
            "review_status": "accepted",
        },
        "## 一句话结论\n某公司发布了新模型。\n",
    )
    write_card(
        markdown_root / "cards" / "2026" / "07" / "card-b.md",
        {
            "id": "card-b",
            "track": "industry",
            "title_zh": "某模型发布（媒体 B 报道）",
            "title_en": "Model launch (outlet B)",
            "date": "2026-07-06",
            "source_url": "https://b.example.com/news",
            "topics": ["ai-industry"],
            "entities": [],
            "review_status": "accepted",
        },
        "## 一句话结论\n某公司发布了新模型。\n",
    )
    sqlite_path = tmp_path / "data" / "kb.sqlite"
    rebuild_index(markdown_root, sqlite_path)

    output_path = generate_brief(
        sqlite_path,
        markdown_root,
        "2026-07-06",
        "2026-07-06",
        None,
        "industry",
        llm_client=FakeClusteringLLM(),
    )

    text = output_path.read_text(encoding="utf-8")
    assert text.count("### ") == 1
    assert "另有 1 家来源报道同一事件" in text


def test_generate_brief_without_llm_client_keeps_items_separate(tmp_path) -> None:
    markdown_root = tmp_path / "notes"
    write_card(
        markdown_root / "cards" / "2026" / "07" / "card-a.md",
        {
            "id": "card-a",
            "track": "industry",
            "title_zh": "某模型发布（媒体 A 报道）",
            "title_en": "Model launch (outlet A)",
            "date": "2026-07-06",
            "source_url": "https://a.example.com/news",
            "topics": ["ai-industry"],
            "entities": [],
            "review_status": "accepted",
        },
        "## 一句话结论\n某公司发布了新模型。\n",
    )
    write_card(
        markdown_root / "cards" / "2026" / "07" / "card-b.md",
        {
            "id": "card-b",
            "track": "industry",
            "title_zh": "某模型发布（媒体 B 报道）",
            "title_en": "Model launch (outlet B)",
            "date": "2026-07-06",
            "source_url": "https://b.example.com/news",
            "topics": ["ai-industry"],
            "entities": [],
            "review_status": "accepted",
        },
        "## 一句话结论\n某公司发布了新模型。\n",
    )
    sqlite_path = tmp_path / "data" / "kb.sqlite"
    rebuild_index(markdown_root, sqlite_path)

    output_path = generate_brief(
        sqlite_path,
        markdown_root,
        "2026-07-06",
        "2026-07-06",
        None,
        "industry",
    )

    text = output_path.read_text(encoding="utf-8")
    assert text.count("### ") == 2
