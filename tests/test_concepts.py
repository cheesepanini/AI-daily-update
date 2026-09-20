from ai_daily_update.processors.concepts import match_foundational_concepts

CONCEPTS_CONFIG = {
    "category_labels": {
        "neural-networks": "神经网络与深度学习",
        "reinforcement-learning": "强化学习基础",
    },
    "concepts": {
        "transformer-attention": {
            "name_zh": "Transformer 与注意力机制",
            "name_en": "Transformer & Attention Mechanism",
            "category": "neural-networks",
            "aliases": ["transformer", "attention mechanism"],
            "applies_to_topics": ["foundation-model"],
        },
        "reinforcement-learning-basics": {
            "name_zh": "强化学习基础",
            "name_en": "Reinforcement Learning Basics",
            "category": "reinforcement-learning",
            "aliases": ["reinforcement learning", "reward function"],
            "applies_to_topics": ["agent", "intelligent-game"],
        },
    },
}


def test_match_foundational_concepts_requires_alias_hit_not_just_topic_overlap():
    metadata = {"topics": ["foundation-model"], "title_zh": "某公司发布新模型", "title_en": ""}

    matches = match_foundational_concepts(metadata, "正文内容", CONCEPTS_CONFIG)

    assert matches == []


def test_match_foundational_concepts_by_alias_with_topic_overlap():
    metadata = {"topics": ["foundation-model"], "title_zh": "某公司发布新的 Transformer 模型", "title_en": ""}

    matches = match_foundational_concepts(metadata, "正文内容", CONCEPTS_CONFIG)

    assert [m["id"] for m in matches] == ["transformer-attention"]


def test_match_foundational_concepts_by_alias_in_title():
    metadata = {"topics": [], "title_zh": "", "title_en": "New reward function design"}

    matches = match_foundational_concepts(metadata, "", CONCEPTS_CONFIG)

    assert [m["id"] for m in matches] == ["reinforcement-learning-basics"]
    assert matches[0]["category_label"] == "强化学习基础"


def test_match_foundational_concepts_returns_empty_when_no_overlap():
    metadata = {"topics": ["ai-industry"], "title_zh": "某公司完成新一轮融资", "title_en": ""}

    matches = match_foundational_concepts(metadata, "", CONCEPTS_CONFIG)

    assert matches == []


def test_match_foundational_concepts_respects_limit():
    metadata = {"topics": ["foundation-model", "agent", "intelligent-game"], "title_zh": "", "title_en": ""}

    matches = match_foundational_concepts(
        metadata, "transformer reward function reinforcement learning", CONCEPTS_CONFIG, limit=1
    )

    assert len(matches) == 1


def test_match_foundational_concepts_ranks_topic_and_alias_hits_above_alias_only():
    metadata = {"topics": ["agent"], "title_zh": "", "title_en": "reinforcement learning update"}

    matches = match_foundational_concepts(metadata, "", CONCEPTS_CONFIG)

    assert matches[0]["id"] == "reinforcement-learning-basics"
