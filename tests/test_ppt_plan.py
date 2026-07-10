import json

from ai_daily_update.ppt.corpus import (
    group_ppt_topic_nodes,
    match_registered_nodes,
    read_ppt_entries,
    read_ppt_node_registry,
)
from ai_daily_update.ppt.plan import generate_ppt_plan, summarize_level2_trends
from ai_daily_update.ppt.plan import merge_ppt_items_by_evidence
from ai_daily_update.ppt.plan import build_oral_update_text, PPTCardSuggestion
from ai_daily_update.storage.markdown import write_card


def test_group_ppt_entries_by_structure_node(tmp_path) -> None:
    csv_path = tmp_path / "ppt.csv"
    csv_path.write_text(
        "\n".join(
            [
                '"page","level1","level2","level3","content_type","content"',
                '"15","二、人工智能发展理论前沿","（一）预训练大模型","2多模态大模型","content","具身智能技术在快速发展。"',
                '"15","二、人工智能发展理论前沿","（一）预训练大模型","2多模态大模型","figure_note","【配图】Gemini Robotics"',
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    nodes = group_ppt_topic_nodes(read_ppt_entries(csv_path))

    assert len(nodes) == 1
    assert nodes[0].pages == [15]
    assert nodes[0].level3 == "2多模态大模型"
    assert nodes[0].content == ["具身智能技术在快速发展。"]
    assert nodes[0].figure_notes == ["【配图】Gemini Robotics"]


def test_registered_nodes_match_current_ppt_structure(tmp_path) -> None:
    csv_path = tmp_path / "ppt.csv"
    csv_path.write_text(
        "\n".join(
            [
                '"page","level1","level2","level3","content_type","content"',
                '"15","二、人工智能发展理论前沿","（一）预训练大模型","2多模态大模型","content","Gemini Robotics 推动具身智能。"',
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    registry_path = tmp_path / "nodes.yaml"
    registry_path.write_text(
        """
nodes:
  - node_id: theory.foundation_models.multimodal
    status: active
    role: 理论前沿
    intent: 说明多模态大模型成为具身智能基础。
    current_level1: 二、人工智能发展理论前沿
    current_level2: （一）预训练大模型
    current_level3: 2多模态大模型
    keywords: [Gemini Robotics, 具身智能]
""".strip()
        + "\n",
        encoding="utf-8",
    )

    current_nodes = group_ppt_topic_nodes(read_ppt_entries(csv_path))
    registered = read_ppt_node_registry(registry_path)
    matches = match_registered_nodes(registered, current_nodes)

    assert matches[0].registered.node_id == "theory.foundation_models.multimodal"
    assert matches[0].current is not None
    assert matches[0].score >= 30


def test_generate_ppt_plan_matches_accepted_cards_to_nodes(tmp_path) -> None:
    markdown_root = tmp_path / "notes"
    ppt_dir = tmp_path / "ppt"
    ppt_dir.mkdir()
    csv_path = ppt_dir / "ppt.csv"
    registry_path = ppt_dir / "nodes.yaml"
    csv_path.write_text(
        "\n".join(
            [
                '"page","level1","level2","level3","content_type","content"',
                '"15","二、人工智能发展理论前沿","（一）预训练大模型","2多模态大模型","content","多模态大模型和具身智能。"',
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    registry_path.write_text(
        """
nodes:
  - node_id: theory.foundation_models.multimodal
    status: active
    role: 理论前沿
    intent: 说明多模态大模型成为具身智能基础。
    current_level1: 二、人工智能发展理论前沿
    current_level2: （一）预训练大模型
    current_level3: 2多模态大模型
    keywords: [Gemini Robotics, 具身智能, foundation-model]
""".strip()
        + "\n",
        encoding="utf-8",
    )
    write_card(
        markdown_root / "cards" / "2026" / "07" / "gemini-robotics.md",
        {
            "id": "card-1",
            "track": "industry",
            "title_zh": "Google Gemini Robotics",
            "title_en": "Google Gemini Robotics",
            "date": "2026-07-07",
            "collected_date": "2026-07-07",
            "source_url": "https://deepmind.google/models/gemini-robotics/",
            "topics": ["foundation-model"],
            "entities": ["Google DeepMind"],
            "review_status": "accepted",
        },
        "## 一句话结论\nGemini Robotics 将多模态模型扩展到具身智能。\n\n## 事件概述\nGoogle DeepMind 发布 Gemini Robotics。",
    )

    output_path = generate_ppt_plan(
        markdown_root,
        csv_path,
        registry_path,
        "2026-07-07",
        "2026-07-07",
    )

    content = output_path.read_text(encoding="utf-8")
    assert "theory.foundation_models.multimodal" in content
    assert "Google Gemini Robotics" in content
    assert "当前页码参考：15" in content
    assert "建议口头表述" in content
    assert "二级小节趋势建议" in content
    assert "趋势关键词：" in content
    assert "具身智能" in content


def test_generate_ppt_plan_uses_llm_to_polish_json_edits(tmp_path) -> None:
    class FakeLLM:
        available = True

        def generate_card_content(self, prompt: str) -> str:
            assert "中文 PPT 讲稿更新编辑" in prompt
            start = prompt.rindex('{"items"')
            payload = json.loads(prompt[start:])
            suggestion_id = payload["items"][0]["suggestion_id"]
            return json.dumps(
                {
                    "items": [
                        {
                            "suggestion_id": suggestion_id,
                            "instruction": "在第 15 页当前小节末尾补充一句，不改标题。",
                            "suggested_text": "这里可以补充 Gemini Robotics，说明多模态模型正在进入具身智能场景。",
                            "rationale": "依据 Gemini Robotics 卡片改写。",
                        }
                    ]
                },
                ensure_ascii=False,
            )

    markdown_root = tmp_path / "notes"
    ppt_dir = tmp_path / "ppt"
    ppt_dir.mkdir()
    csv_path = ppt_dir / "ppt.csv"
    registry_path = ppt_dir / "nodes.yaml"
    csv_path.write_text(
        "\n".join(
            [
                '"page","level1","level2","level3","content_type","content"',
                '"15","二、人工智能发展理论前沿","（一）预训练大模型","2多模态大模型","content","多模态大模型和具身智能。"',
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    registry_path.write_text(
        """
nodes:
  - node_id: theory.foundation_models.multimodal
    status: active
    role: 理论前沿
    intent: 说明多模态大模型成为具身智能基础。
    current_level1: 二、人工智能发展理论前沿
    current_level2: （一）预训练大模型
    current_level3: 2多模态大模型
    keywords: [Gemini Robotics, 具身智能, foundation-model]
""".strip()
        + "\n",
        encoding="utf-8",
    )
    write_card(
        markdown_root / "cards" / "2026" / "07" / "gemini-robotics.md",
        {
            "id": "card-1",
            "track": "industry",
            "title_zh": "Google Gemini Robotics",
            "title_en": "Google Gemini Robotics",
            "date": "2026-07-07",
            "collected_date": "2026-07-07",
            "source_url": "https://deepmind.google/models/gemini-robotics/",
            "topics": ["foundation-model"],
            "entities": ["Google DeepMind"],
            "review_status": "accepted",
        },
        "## 一句话结论\nGemini Robotics 将多模态模型扩展到具身智能。\n\n## 事件概述\nGoogle DeepMind 发布 Gemini Robotics。",
    )

    output_path = generate_ppt_plan(
        markdown_root,
        csv_path,
        registry_path,
        "2026-07-07",
        "2026-07-07",
        llm_client=FakeLLM(),
    )

    payload = json.loads(output_path.with_suffix(".json").read_text(encoding="utf-8"))
    first_item = payload["items"][0]
    assert first_item["edits"][0]["instruction"] == "在第 15 页当前小节末尾补充一句，不改标题。"
    assert first_item["edits"][0]["suggested_text"] == "这里可以补充 Gemini Robotics，说明多模态模型正在进入具身智能场景。"
    assert first_item["recommendation"] == "这里可以补充 Gemini Robotics，说明多模态模型正在进入具身智能场景。"


def test_merge_ppt_items_by_same_evidence_group() -> None:
    items = [
        {
            "suggestion_id": "section",
            "kind": "section_trend",
            "kind_label": "小节趋势建议",
            "title": "智能体",
            "location": "二、理论前沿 / 智能体",
            "pages": [21],
            "card_ids": ["card-a", "card-b"],
            "recommendation": "建议补充智能体案例。",
            "edits": [{"instruction": "在第 21 页补充。", "suggested_text": "建议文本。"}],
        },
        {
            "suggestion_id": "node",
            "kind": "node_update",
            "kind_label": "结构节点建议",
            "title": "auto.node",
            "location": "二、理论前沿 / 智能体 / 安全评估",
            "pages": [22],
            "card_ids": ["card-b", "card-a"],
            "recommendation": "建议补充智能体案例。",
            "edits": [{"instruction": "在第 22 页补充。", "suggested_text": "建议文本。"}],
        },
    ]

    merged = merge_ppt_items_by_evidence(items, "report.md")

    assert len(merged) == 1
    assert merged[0]["kind"] == "merged_update"
    assert merged[0]["pages"] == [21, 22]
    assert len(merged[0]["target_locations"]) == 2
    assert "同一更新也匹配到" in merged[0]["edits"][0]["instruction"]


def test_merge_ppt_items_by_overlapping_evidence_group() -> None:
    items = [
        {
            "suggestion_id": "section",
            "kind": "section_trend",
            "kind_label": "小节趋势建议",
            "title": "预训练大模型",
            "location": "二、理论前沿 / 预训练大模型",
            "pages": [20],
            "card_ids": ["fusion", "briefcase", "distributed-attack", "safety-monitor"],
            "recommendation": "建议补充 Fusion 工具。",
            "edits": [{"instruction": "在第 20 页补充。", "suggested_text": "建议文本。"}],
        },
        {
            "suggestion_id": "language",
            "kind": "node_update",
            "kind_label": "结构节点建议",
            "title": "语言大模型",
            "location": "二、理论前沿 / 预训练大模型 / 语言大模型",
            "pages": [21],
            "card_ids": ["fusion", "briefcase"],
            "recommendation": "OpenRouter Fusion 可作为语言模型案例。",
            "edits": [{"instruction": "在第 21 页补充。", "suggested_text": "建议文本。"}],
        },
        {
            "suggestion_id": "other",
            "kind": "node_update",
            "title": "空间智能",
            "location": "三、技术前沿 / 空间智能",
            "pages": [40],
            "card_ids": ["spatial-card"],
            "recommendation": "另一个建议。",
            "edits": [],
        },
    ]

    merged = merge_ppt_items_by_evidence(items, "report.md")

    assert len(merged) == 2
    merged_update = next(item for item in merged if item["kind"] == "merged_update")
    assert merged_update["card_ids"] == [
        "briefcase",
        "distributed-attack",
        "fusion",
        "safety-monitor",
    ]
    assert len(merged_update["target_locations"]) == 2


def test_summarize_level2_trends_merges_keywords_by_section(tmp_path) -> None:
    csv_path = tmp_path / "ppt.csv"
    csv_path.write_text(
        "\n".join(
            [
                '"page","level1","level2","level3","content_type","content"',
                '"15","二、人工智能发展理论前沿","（一）预训练大模型","2多模态大模型","content","多模态大模型。"',
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    registry_path = tmp_path / "nodes.yaml"
    registry_path.write_text(
        """
nodes:
  - node_id: theory.foundation_models.multimodal
    status: active
    role: 理论前沿
    intent: 说明多模态大模型成为具身智能基础。
    current_level1: 二、人工智能发展理论前沿
    current_level2: （一）预训练大模型
    current_level3: 2多模态大模型
    keywords: [Gemini Robotics, 具身智能]
""".strip()
        + "\n",
        encoding="utf-8",
    )
    matches = match_registered_nodes(
        read_ppt_node_registry(registry_path),
        group_ppt_topic_nodes(read_ppt_entries(csv_path)),
    )
    suggestions = [
        PPTCardSuggestion(
            card_id="card-1",
            title="Gemini Robotics",
            source_url="https://example.com",
            date="2026-07-07",
            topics=["foundation-model"],
            conclusion="Gemini Robotics 将多模态模型扩展到 embodied AI。",
            overview="具身智能与 robotics 成为新的模型落点。",
            node_id="theory.foundation_models.multimodal",
            node_label="二、人工智能发展理论前沿 / （一）预训练大模型 / 2多模态大模型",
            score=12,
            reasons=[],
        )
    ]

    sections = summarize_level2_trends(
        matches,
        suggestions,
        {
            "topics": {
                "foundation-model": {
                    "name_zh": "基础模型",
                    "aliases": ["foundation model", "embodied AI"],
                }
            }
        },
    )

    assert len(sections) == 1
    assert sections[0].level2 == "（一）预训练大模型"
    assert any(trend["label"] == "基础模型" for trend in sections[0].trends)
    assert "预训练大模型可围绕" in sections[0].recommendation


def test_oral_update_text_limits_recent_dates() -> None:
    items = [
        PPTCardSuggestion(
            card_id=f"card-{index}",
            title=f"事件 {index}",
            source_url="https://example.com",
            date=card_date,
            topics=[],
            conclusion=f"这是第 {index} 条适合口头汇报的更新内容。",
            overview="",
            node_id="node",
            node_label="节点",
            score=10 - index,
            reasons=[],
        )
        for index, card_date in enumerate(["2026-07-07", "2026-06-01", "2025-12-01"], start=1)
    ]

    text = build_oral_update_text(None, items)

    assert "2026-07-07" in text
    assert "2026-06-01" in text
    assert "2025-12-01" not in text
