from datetime import date

from ai_daily_update.processors.candidates import Candidate
from ai_daily_update.reports.candidates import write_candidate_report


def test_write_candidate_report_outputs_summary_and_candidates(tmp_path) -> None:
    selected = Candidate(
        url="https://example.com/a",
        track="industry",
        topics=["agent"],
        title="Agent platform update",
        source_kind="company_blog",
        source_name="Example",
        score=62,
        score_reasons=("source:company_blog+12", "topic_priority:5+50"),
    )
    skipped = Candidate(
        url="https://example.com/b",
        track="academic",
        topics=["foundation-model"],
        title="Foundation model paper",
        source_kind="arxiv",
        source_name="arXiv",
        score=50,
    )

    output_path = write_candidate_report(
        tmp_path / "notes",
        date(2026, 7, 7),
        [selected, skipped],
        [selected],
        ["OpenAI timeout"],
        skipped_existing=3,
        dry_run=True,
    )

    content = output_path.read_text(encoding="utf-8")
    assert "# 每日候选池：2026-07-07" in content
    assert "- 运行模式：预跑候选（未生成卡片）" in content
    assert "- 去重后候选数：2" in content
    assert "- 跳过已有来源：3" in content
    assert "### 拟入选（未生成）：Agent platform update" in content
    assert "### 未入选：Foundation model paper" in content
    assert "source:company_blog+12" in content
