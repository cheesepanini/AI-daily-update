import yaml
from fastapi.testclient import TestClient

from ai_daily_update.config import load_settings
from ai_daily_update.feedback.events import append_feedback_event, feedback_log_path, read_feedback_events
from ai_daily_update.source_proposals import generate_source_proposals, read_source_proposals
from ai_daily_update.storage.markdown import write_card
from ai_daily_update.web import create_app


def write_test_config(root) -> None:
    config_dir = root / "config"
    config_dir.mkdir()
    (config_dir / "app.yaml").write_text(
        """
timezone: Asia/Shanghai
storage:
  markdown_root: notes
  sqlite_path: data/kb.sqlite
review:
  statuses:
    - needs-review
    - accepted
    - later
    - rejected
""".strip()
        + "\n",
        encoding="utf-8",
    )
    (config_dir / "sources.yaml").write_text("sources: {}\n", encoding="utf-8")
    (config_dir / "topics.yaml").write_text("topics: {}\n", encoding="utf-8")


def test_review_action_writes_feedback_event(tmp_path) -> None:
    write_test_config(tmp_path)
    write_card(
        tmp_path / "notes" / "cards" / "2026" / "07" / "card.md",
        {
            "id": "card-1",
            "track": "industry",
            "title_zh": "测试卡片",
            "date": "2026-07-08",
            "source_url": "https://example.com/a",
            "source_type": "company-news",
            "topics": ["agent"],
            "review_status": "needs-review",
        },
        "## 一句话结论\n测试。",
    )
    client = TestClient(create_app(tmp_path))

    response = client.post(
        "/actions/review",
        data={"card_id": "card-1", "status": "accepted", "return_to": "/cards"},
        follow_redirects=False,
    )

    assert response.status_code == 303
    events = read_feedback_events(tmp_path)
    assert len(events) == 1
    assert events[0]["surface"] == "card_review"
    assert events[0]["entity_id"] == "card-1"
    assert events[0]["action"] == "accepted"
    assert events[0]["previous_status"] == "needs-review"
    assert events[0]["new_status"] == "accepted"


def test_read_feedback_events_skips_corrupted_line_instead_of_raising(tmp_path) -> None:
    append_feedback_event(
        tmp_path, "Asia/Shanghai", "card_review", "card", "card-1", "accepted"
    )
    log_path = feedback_log_path(tmp_path)
    with log_path.open("a", encoding="utf-8") as handle:
        handle.write('{"event_id": "feedback-broken", truncated\n')
    append_feedback_event(
        tmp_path, "Asia/Shanghai", "card_review", "card", "card-2", "rejected"
    )

    events = read_feedback_events(tmp_path)

    assert [event["entity_id"] for event in events] == ["card-1", "card-2"]


def test_generate_source_proposals_from_accepted_card_domains(tmp_path) -> None:
    write_test_config(tmp_path)
    for index in range(2):
        write_card(
            tmp_path / "notes" / "cards" / "2026" / "07" / f"card-{index}.md",
            {
                "id": f"card-{index}",
                "track": "industry",
                "title_zh": f"来源卡片 {index}",
                "date": "2026-07-08",
                "source_url": f"https://example-lab.ai/news/{index}",
                "topics": ["embodied-ai"],
                "review_status": "accepted",
            },
            "## 一句话结论\n测试。",
        )
    settings = load_settings(tmp_path)

    output_path = generate_source_proposals(settings)
    proposals = read_source_proposals(tmp_path)

    assert output_path.exists()
    assert any(proposal["url"] == "https://example-lab.ai" for proposal in proposals)
    proposal = next(proposal for proposal in proposals if proposal["url"] == "https://example-lab.ai")
    assert proposal["primary_topic"] == "embodied-ai"
    assert proposal["proposal_origin"] == "accepted-card-domain"


def test_source_suggestion_add_writes_feedback_event_for_auto_proposal(tmp_path) -> None:
    write_test_config(tmp_path)
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    (data_dir / "source_proposals.json").write_text(
        """
{
  "generated_at": "2026-07-08T00:00:00+08:00",
  "proposal_version": "v1",
  "proposals": [
    {
      "name": "Example Lab",
      "url": "https://example-lab.ai",
      "coverage": "测试来源",
      "topic_text": "embodied-ai",
      "primary_topic": "embodied-ai",
      "secondary_topic": "",
      "reason": "测试自动建议",
      "priority": "自动建议",
      "proposal_origin": "accepted-card-domain"
    }
  ]
}
""".strip(),
        encoding="utf-8",
    )
    client = TestClient(create_app(tmp_path))
    response = client.get("/sources")
    marker = 'name="suggestion_id" value="'
    suggestion_id = response.text.split(marker, 1)[1].split('"', 1)[0]

    add_response = client.post(
        "/actions/source-suggestion-add",
        data={"suggestion_id": suggestion_id, "return_to": "/sources"},
        follow_redirects=False,
    )

    assert add_response.status_code == 303
    sources = yaml.safe_load((tmp_path / "config" / "sources.yaml").read_text(encoding="utf-8"))
    assert sources["sources"]["company_blogs"]["sources"][0]["name"] == "Example Lab"
    events = read_feedback_events(tmp_path)
    assert events[0]["surface"] == "source_proposal_review"
    assert events[0]["action"] == "added"
    assert events[0]["metadata"]["proposal_origin"] == "accepted-card-domain"
