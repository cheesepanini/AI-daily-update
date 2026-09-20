from ai_daily_update.processors.candidates import Candidate
from ai_daily_update.processors.retrieval import find_duplicate_suspect, find_related_cards
from ai_daily_update.storage.markdown import write_card


def write_existing_card(root, card_id, title_zh, topics, conclusion, status="accepted", url="https://example.com/existing"):
    write_card(
        root / "cards" / "2026" / "07" / f"{card_id}.md",
        {
            "id": card_id,
            "track": "industry",
            "title_zh": title_zh,
            "title_en": title_zh,
            "date": "2026-07-01",
            "source_url": url,
            "topics": topics,
            "entities": [],
            "review_status": status,
        },
        f"## 一句话结论\n{conclusion}\n",
    )


def test_find_related_cards_ranks_by_topic_and_title_overlap(tmp_path):
    write_existing_card(
        tmp_path,
        "card-fm",
        "多模态大模型发布",
        ["foundation-model"],
        "某公司发布新的多模态大模型。",
    )
    write_existing_card(
        tmp_path,
        "card-agent",
        "智能体框架发布",
        ["agent"],
        "某团队发布新的智能体框架。",
    )
    candidate = Candidate(
        url="https://example.com/new",
        track="industry",
        topics=["foundation-model"],
        title="多模态大模型更新",
    )

    related = find_related_cards(candidate, tmp_path, limit=3)

    assert len(related) == 1
    assert related[0]["title"] == "多模态大模型发布"
    assert related[0]["conclusion"] == "某公司发布新的多模态大模型。"


def test_find_related_cards_returns_empty_when_nothing_matches(tmp_path):
    write_existing_card(
        tmp_path,
        "card-agent",
        "智能体框架发布",
        ["agent"],
        "某团队发布新的智能体框架。",
    )
    candidate = Candidate(
        url="https://example.com/new",
        track="academic",
        topics=["robotics"],
        title="机器人控制新方法",
    )

    related = find_related_cards(candidate, tmp_path)

    assert related == []


def test_find_related_cards_skips_rejected_and_self(tmp_path):
    write_existing_card(
        tmp_path,
        "card-fm",
        "多模态大模型发布",
        ["foundation-model"],
        "某公司发布新的多模态大模型。",
        status="rejected",
    )
    write_existing_card(
        tmp_path,
        "card-self",
        "候选自身",
        ["foundation-model"],
        "这是候选自身对应的已有卡片。",
        url="https://example.com/new",
    )
    candidate = Candidate(
        url="https://example.com/new",
        track="industry",
        topics=["foundation-model"],
        title="多模态大模型更新",
    )

    related = find_related_cards(candidate, tmp_path)

    assert related == []


def test_find_related_cards_respects_limit(tmp_path):
    for index in range(5):
        write_existing_card(
            tmp_path,
            f"card-{index}",
            f"多模态大模型进展 {index}",
            ["foundation-model"],
            f"进展 {index}。",
        )
    candidate = Candidate(
        url="https://example.com/new",
        track="industry",
        topics=["foundation-model"],
        title="多模态大模型更新",
    )

    related = find_related_cards(candidate, tmp_path, limit=2)

    assert len(related) == 2


def test_find_duplicate_suspect_flags_high_overlap_title(tmp_path):
    write_existing_card(
        tmp_path,
        "card-launch-a",
        "行业首个具身原生世界动作模型——蚂蚁灵波发布 LingBot-VA 2.0",
        ["ai-industry"],
        "蚂蚁灵波发布了具身原生世界动作模型 LingBot-VA 2.0。",
    )
    candidate = Candidate(
        url="https://example.com/new",
        track="industry",
        topics=["ai-industry"],
        title="全球首个「具身原生」预训练模型 LingBot-VA 2.0 发布",
    )

    suspect = find_duplicate_suspect(candidate, tmp_path)

    assert suspect is not None
    assert suspect["title"] == "行业首个具身原生世界动作模型——蚂蚁灵波发布 LingBot-VA 2.0"


def test_find_duplicate_suspect_does_not_flag_topically_adjacent_but_distinct_items(tmp_path):
    write_existing_card(
        tmp_path,
        "card-kv-a",
        "DepthWeave-KV：面向长上下文KV缓存压缩的令牌自适应跨层残差分解",
        ["foundation-model"],
        "提出了一种跨层残差分解的KV缓存压缩方法。",
    )
    candidate = Candidate(
        url="https://example.com/new",
        track="academic",
        topics=["foundation-model"],
        title="Mixture-of-Experts 路由稳定性研究",
    )

    suspect = find_duplicate_suspect(candidate, tmp_path)

    assert suspect is None


def test_find_duplicate_suspect_returns_none_when_no_topic_overlap(tmp_path):
    write_existing_card(
        tmp_path,
        "card-agent",
        "智能体框架发布",
        ["agent"],
        "某团队发布新的智能体框架。",
    )
    candidate = Candidate(
        url="https://example.com/new",
        track="industry",
        topics=["foundation-model"],
        title="智能体框架发布",
    )

    suspect = find_duplicate_suspect(candidate, tmp_path)

    assert suspect is None


def test_find_duplicate_suspect_flags_same_event_with_unrelated_phrasing(tmp_path):
    # Real case: same qbitai article covered by two differently-phrased
    # Chinese headlines. The old punctuation-only title_terms split these
    # into two unsplittable clauses with zero overlap (false negative).
    write_existing_card(
        tmp_path,
        "card-wam-ttt",
        "银河通用发布全球首个具身智能测试时后训练框架 WAM-TTT",
        ["ai-industry"],
        "银河通用发布 WAM-TTT 框架。",
    )
    candidate = Candidate(
        url="https://example.com/new",
        track="industry",
        topics=["ai-industry"],
        title="全球首个！银河通用新框架仅需人类视频即可部署",
    )

    suspect = find_duplicate_suspect(candidate, tmp_path)

    assert suspect is not None
    assert suspect["title"] == "银河通用发布全球首个具身智能测试时后训练框架 WAM-TTT"


def test_find_duplicate_suspect_does_not_flag_unrelated_titles_sharing_a_company_name(
    tmp_path,
):
    # Real case: two distinct AGIBOT news items sharing only the "AGIBOT"
    # token. The old whole-clause splitting shrank the comparable term count
    # so much that one shared token alone crossed the overlap threshold
    # (false positive).
    write_existing_card(
        tmp_path,
        "card-agibot-uk",
        "AGIBOT在伦敦举办英国APC2026会议，推动人形机器人欧洲商业部署",
        ["ai-industry"],
        "AGIBOT 在伦敦举办活动。",
    )
    candidate = Candidate(
        url="https://example.com/new",
        track="industry",
        topics=["ai-industry"],
        title="AGIBOT 将 APC 2026 引入澳大利亚和新西兰",
    )

    suspect = find_duplicate_suspect(candidate, tmp_path)

    assert suspect is None
