from ai_daily_update.collectors.document import SourceDocument
from ai_daily_update.cli import expand_digest_candidates
from ai_daily_update.processors.candidates import Candidate
from ai_daily_update.processors.digest import (
    digest_item_url,
    expand_digest_candidate,
    published_date_from_digest_title,
    should_split_digest,
    split_digest_document,
)


TENCENT_DIGEST_TEXT = """
生成式AI
一、Gemini 3.5 Pro泄露，前端能力超越Fable 5
1.传闻Gemini 3.5 Pro将于7月17日发布，泄露显示其前端与视觉代码生成能力明显跃升；
2.但在硬核推理、仓库级工程和长程Agent任务上仍不及Fable 5与GPT-5.6。
二、腾讯混元Hy3发布，Agent与产品体验升级
1.腾讯正式发布Hy3大模型，扩大后训练与RL算力规模；
2.模型以Apache 2.0协议开源，并降低API价格。
报告观点
三、Karpathy称做Agent应先夯实底层大模型
1.Karpathy指出当前AI最大错误是急于逼Agent干活，却未先搞懂底层大模型；
2.他忠告Demo容易、产品难，做成Agent需十年积累。
"""


def test_split_digest_document_uses_chinese_numbered_headings() -> None:
    document = SourceDocument(
        url="https://m.sohu.com/a/1_455313",
        title="腾讯研究院AI速递 20260707",
        description="",
        text=TENCENT_DIGEST_TEXT,
    )

    items = split_digest_document(document)

    assert [item.title for item in items] == [
        "Gemini 3.5 Pro泄露，前端能力超越Fable 5",
        "腾讯混元Hy3发布，Agent与产品体验升级",
        "Karpathy称做Agent应先夯实底层大模型",
    ]
    assert items[0].index == 1
    assert "视觉代码生成能力明显跃升" in items[0].summary
    assert "报告观点" not in items[2].summary


def test_expand_digest_candidate_preserves_parent_source() -> None:
    candidate = Candidate(
        url="https://m.sohu.com/a/1_455313",
        track="industry",
        topics=[],
        title="腾讯研究院AI速递 20260707",
        source_kind="chinese_media",
        source_name="腾讯研究院",
    )
    document = SourceDocument(
        url=candidate.url,
        title=candidate.title,
        description="",
        text=TENCENT_DIGEST_TEXT,
    )

    expanded = expand_digest_candidate(candidate, document)

    assert len(expanded) == 3
    assert expanded[1].url == "https://m.sohu.com/a/1_455313?digest_item=2"
    assert expanded[1].parent_url == candidate.url
    assert expanded[1].parent_title == candidate.title
    assert expanded[1].digest_item_index == 2
    assert expanded[1].published == "2026-07-07"
    assert "Apache 2.0" in expanded[1].summary


def test_should_split_digest_only_targets_tencent_ai_digest() -> None:
    assert should_split_digest(
        Candidate(
            url="https://m.sohu.com/a/1_455313",
            track="industry",
            topics=[],
            title="腾讯研究院AI速递 20260707",
            source_kind="chinese_media",
            source_name="腾讯研究院",
        )
    )
    assert not should_split_digest(
        Candidate(
            url="https://m.sohu.com/a/2_455313",
            track="industry",
            topics=[],
            title="腾讯研究院观点",
            source_kind="chinese_media",
            source_name="腾讯研究院",
        )
    )


def test_published_date_from_digest_title_parses_compact_date() -> None:
    assert published_date_from_digest_title("腾讯研究院AI速递 20260707") == "2026-07-07"


def test_digest_item_url_preserves_existing_query() -> None:
    assert (
        digest_item_url("https://m.sohu.com/a/1_455313?scm=abc", 3)
        == "https://m.sohu.com/a/1_455313?scm=abc&digest_item=3"
    )


def test_expand_digest_candidates_drops_unsplittable_digest(monkeypatch) -> None:
    candidate = Candidate(
        url="https://m.sohu.com/a/1_455313",
        track="industry",
        topics=[],
        title="腾讯研究院AI速递 20260707",
        source_kind="chinese_media",
        source_name="腾讯研究院",
    )

    def fake_fetch_source_document(url: str, timeout: int = 12) -> SourceDocument:
        return SourceDocument(url=url, title="腾讯研究院AI速递 20260707", description="", text="无可拆条目")

    monkeypatch.setattr("ai_daily_update.cli.fetch_source_document", fake_fetch_source_document)
    warnings: list[str] = []

    expanded = expand_digest_candidates([candidate], warnings)

    assert expanded == []
    assert "no digest items found" in warnings[0]
