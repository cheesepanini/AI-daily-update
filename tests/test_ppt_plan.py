import json

from ai_daily_update.ppt.corpus import (
    group_ppt_topic_nodes,
    match_registered_nodes,
    read_ppt_entries,
    read_ppt_node_registry,
)
from ai_daily_update.ppt.plan import generate_ppt_plan, summarize_level2_trends
from ai_daily_update.ppt.plan import (
    attach_auxiliary_evidence,
    build_ppt_update_groups_by_importance,
    group_core_cards_by_semantics_with_llm,
    score_card_importance_with_llm,
    select_core_cards,
)
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


def make_card_suggestion(card_id: str, node_id: str, topics: list[str], score: int = 0, title: str = "") -> PPTCardSuggestion:
    return PPTCardSuggestion(
        card_id=card_id,
        title=title or card_id,
        source_url="https://example.com",
        date="2026-07-07",
        topics=topics,
        conclusion=f"{card_id} 的一句话结论。",
        overview=f"{card_id} 的事件概述。",
        node_id=node_id,
        node_label=node_id,
        score=score,
        reasons=[],
    )


def test_select_core_cards_splits_by_importance_score() -> None:
    card_ids = [f"card-{i}" for i in range(20)]
    importance = {card_id: (5 if i < 12 else 2) for i, card_id in enumerate(card_ids)}

    core, auxiliary = select_core_cards(card_ids, importance, min_count=10, max_count=15)

    assert len(core) == 12
    assert set(core) == {card_id for card_id in card_ids if importance[card_id] == 5}
    assert set(auxiliary) == {card_id for card_id in card_ids if importance[card_id] == 2}


def test_select_core_cards_keeps_all_when_fewer_than_minimum() -> None:
    card_ids = ["a", "b", "c"]
    importance = {"a": 5, "b": 3, "c": 1}

    core, auxiliary = select_core_cards(card_ids, importance, min_count=10, max_count=15)

    assert core == ["a", "b", "c"]
    assert auxiliary == []


def test_score_card_importance_with_llm_uses_llm_scores() -> None:
    class FakeLLM:
        available = True

        def generate_card_content(self, prompt: str) -> str:
            return json.dumps(
                {"scores": [{"card_id": "card-1", "score": 5}, {"card_id": "card-2", "score": 2}]}
            )

    card_lookup = {
        "card-1": make_card_suggestion("card-1", "node.a", ["foundation-model"], score=10),
        "card-2": make_card_suggestion("card-2", "node.b", ["agent"], score=5),
    }

    scores = score_card_importance_with_llm(["card-1", "card-2"], card_lookup, FakeLLM())

    assert scores == {"card-1": 5, "card-2": 2}


def test_score_card_importance_falls_back_to_match_score_without_llm() -> None:
    card_lookup = {
        "card-1": make_card_suggestion("card-1", "node.a", ["foundation-model"], score=10),
        "card-2": make_card_suggestion("card-2", "node.b", ["agent"], score=5),
    }

    scores = score_card_importance_with_llm(["card-1", "card-2"], card_lookup, None)

    assert scores == {"card-1": 10, "card-2": 5}


def test_group_core_cards_by_semantics_with_llm_uses_llm_groups() -> None:
    class FakeLLM:
        available = True

        def generate_card_content(self, prompt: str) -> str:
            return json.dumps(
                {
                    "groups": [
                        {"card_ids": ["card-1", "card-2"], "label": "多模态大模型"},
                        {"card_ids": ["card-3"], "label": "智能体安全"},
                    ]
                }
            )

    card_lookup = {
        "card-1": make_card_suggestion("card-1", "node.a", ["foundation-model"]),
        "card-2": make_card_suggestion("card-2", "node.a", ["foundation-model"]),
        "card-3": make_card_suggestion("card-3", "node.b", ["agent"]),
    }

    groups = group_core_cards_by_semantics_with_llm(
        ["card-1", "card-2", "card-3"], card_lookup, [], FakeLLM()
    )

    assert len(groups) == 2
    assert {"card-1", "card-2"} == set(groups[0]["card_ids"])
    assert groups[0]["label"] == "多模态大模型"


def test_group_core_cards_falls_back_to_structure_grouping_without_llm() -> None:
    card_lookup = {
        "card-1": make_card_suggestion("card-1", "node.a", ["foundation-model"]),
        "card-2": make_card_suggestion("card-2", "node.a", ["foundation-model"]),
        "card-3": make_card_suggestion("card-3", "node.b", ["agent"]),
    }
    scoped_items = [
        {"kind": "node_update", "node_id": "node.a", "card_ids": ["card-1", "card-2"]},
        {"kind": "node_update", "node_id": "node.b", "card_ids": ["card-3"]},
    ]

    groups = group_core_cards_by_semantics_with_llm(
        ["card-1", "card-2", "card-3"], card_lookup, scoped_items, None
    )

    grouped_card_ids = sorted(tuple(sorted(group["card_ids"])) for group in groups)
    assert grouped_card_ids == [("card-1", "card-2"), ("card-3",)]


def test_attach_auxiliary_evidence_attaches_by_keyword_overlap() -> None:
    card_lookup = {
        "core-1": make_card_suggestion("core-1", "node.a", ["foundation-model"]),
        "core-2": make_card_suggestion("core-2", "node.b", ["agent"]),
        "aux-1": make_card_suggestion("aux-1", "node.a", ["foundation-model"]),
    }
    groups = [{"card_ids": ["core-1"], "label": ""}, {"card_ids": ["core-2"], "label": ""}]

    updated = attach_auxiliary_evidence(groups, ["aux-1"], card_lookup)

    assert "aux-1" in updated[0]["card_ids"]
    assert "aux-1" not in updated[1]["card_ids"]


def test_build_ppt_update_groups_by_importance_merges_semantically_similar_items() -> None:
    class FakeLLM:
        available = True

        def generate_card_content(self, prompt: str) -> str:
            if "重要性分" in prompt:
                return json.dumps(
                    {
                        "scores": [
                            {"card_id": "card-a", "score": 5},
                            {"card_id": "card-b", "score": 5},
                            {"card_id": "card-c", "score": 4},
                        ]
                    }
                )
            return json.dumps(
                {
                    "groups": [
                        {"card_ids": ["card-a", "card-b"], "label": "预训练大模型"},
                        {"card_ids": ["card-c"], "label": "空间智能"},
                    ]
                }
            )

    suggestions = [
        make_card_suggestion("card-a", "node.language", ["foundation-model"], score=8, title="语言模型进展"),
        make_card_suggestion("card-b", "node.multimodal", ["foundation-model"], score=6, title="多模态模型进展"),
        make_card_suggestion("card-c", "node.spatial", ["spatial-ai"], score=5, title="空间智能进展"),
    ]
    items = [
        {
            "suggestion_id": "node-language",
            "kind": "node_update",
            "kind_label": "结构节点建议",
            "title": "node.language",
            "node_id": "node.language",
            "location": "二、理论前沿 / 预训练大模型 / 语言大模型",
            "pages": [21],
            "card_ids": ["card-a"],
            "cards": [{"card_id": "card-a", "title": "语言模型进展"}],
            "recommendation": "语言模型建议。",
            "edits": [{"instruction": "在第 21 页补充。", "suggested_text": "建议文本。"}],
        },
        {
            "suggestion_id": "node-multimodal",
            "kind": "node_update",
            "kind_label": "结构节点建议",
            "title": "node.multimodal",
            "node_id": "node.multimodal",
            "location": "二、理论前沿 / 预训练大模型 / 多模态大模型",
            "pages": [22],
            "card_ids": ["card-b"],
            "cards": [{"card_id": "card-b", "title": "多模态模型进展"}],
            "recommendation": "多模态建议。",
            "edits": [{"instruction": "在第 22 页补充。", "suggested_text": "建议文本。"}],
        },
        {
            "suggestion_id": "node-spatial",
            "kind": "node_update",
            "kind_label": "结构节点建议",
            "title": "node.spatial",
            "node_id": "node.spatial",
            "location": "三、技术前沿 / 空间智能",
            "pages": [40],
            "card_ids": ["card-c"],
            "cards": [{"card_id": "card-c", "title": "空间智能进展"}],
            "recommendation": "空间智能建议。",
            "edits": [{"instruction": "在第 40 页补充。", "suggested_text": "建议文本。"}],
        },
    ]

    grouped = build_ppt_update_groups_by_importance(items, suggestions, "report.md", FakeLLM())

    assert len(grouped) == 2
    merged_update = next(item for item in grouped if item["kind"] == "merged_update")
    assert set(merged_update["card_ids"]) == {"card-a", "card-b"}
    single_update = next(item for item in grouped if item["card_ids"] == ["card-c"])
    assert single_update["kind"] == "node_update"


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
