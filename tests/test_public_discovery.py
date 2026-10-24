from datetime import date

from fastapi.testclient import TestClient

from ai_daily_update.config import load_settings
from ai_daily_update.reports.public_period import source_hash, write_report
from ai_daily_update.storage.markdown import read_card, update_metadata, write_card
from ai_daily_update.web import create_app, public_cards, public_period_start


def make_app(tmp_path):
    config = tmp_path / "config"
    config.mkdir()
    (config / "app.yaml").write_text("timezone: Asia/Shanghai\nstorage:\n  markdown_root: notes\n  sqlite_path: data/kb.sqlite\n", encoding="utf-8")
    (config / "sources.yaml").write_text("sources: {}\n", encoding="utf-8")
    (config / "topics.yaml").write_text("topics:\n  agent:\n    name_zh: 智能体\n    priority: 5\n", encoding="utf-8")
    paths = {}
    for card_id, status, date, title, text in [
        ("alpha", "accepted", "2026-10-10", "模型发布", "独特正文词"),
        ("beta", "accepted", "2026-10-10", "模型新进展", "其他正文"),
        ("pending", "needs-review", "2026-10-11", "待审核消息", "不应进精选"),
    ]:
        path = tmp_path / "notes" / "cards" / "2026" / "10" / f"{card_id}.md"
        write_card(path, {
            "id": card_id, "title_zh": title, "date": date, "event_date": date,
            "review_status": status, "track": "industry", "topics": ["agent"],
            "source_url": f"https://example.com/{card_id}",
        }, f"## 一句话结论\n{title}的摘要。\n\n## 为什么重要\n有助于理解该领域。\n\n## 事件概述\n{text}。")
        paths[card_id] = path
    return TestClient(create_app(tmp_path)), paths


def test_featured_daily_topic_and_search_use_reviewed_cards(tmp_path):
    client, _ = make_app(tmp_path)

    assert "待审核消息" not in client.get("/public/featured").text
    assert "待审核消息" in client.get("/public").text
    assert "值得关注：有助于理解该领域" in client.get("/public/featured").text
    assert "模型发布" in client.get("/public/featured?q=独特正文词&search_field=body").text
    assert "模型新进展" not in client.get("/public/featured?q=独特正文词&search_field=body").text
    assert "模型发布" not in client.get("/public/featured?q=独特正文词&search_field=title").text
    assert "模型发布" in client.get("/public/featured?q=模型+发布&search_field=title").text
    assert "模型发布" not in client.get("/public/featured?from_date=2026-10-11").text
    daily = client.get("/public/daily")
    assert daily.status_code == 200 and "2026-10-10" in daily.text
    assert "待审核消息" not in daily.text
    assert "智能体" in client.get("/public/topics").text
    assert "模型发布" in client.get("/public/topics/agent").text


def test_confirmed_event_group_and_first_party_filter(tmp_path):
    client, paths = make_app(tmp_path)
    response = client.post("/actions/card-publication", data={
        "card_id": "alpha", "first_party": "true", "related_card_id": "beta",
    }, follow_redirects=False)
    assert response.status_code == 303
    assert read_card(paths["alpha"]).metadata["first_party"] is True
    assert read_card(paths["alpha"]).metadata["event_group_id"] == "beta"
    assert read_card(paths["beta"]).metadata["event_group_id"] == "beta"
    featured = client.get("/public/featured").text
    assert "另有 1 条已确认的同事件报道" in featured
    assert "一手来源" in client.get("/public/featured?first_party=true").text
    assert "模型新进展" not in client.get("/public/featured?first_party=true").text
    detail = client.get("/public/cards/alpha").text
    assert "同一事件的其他来源" in detail and "模型新进展" in detail

    client.post("/actions/card-publication", data={"card_id": "pending", "related_card_id": "beta"})
    assert not read_card(paths["pending"]).metadata.get("event_group_id")


def test_future_event_uses_information_date_in_list_and_not_default_daily(tmp_path):
    client, _ = make_app(tmp_path)
    path = tmp_path / "notes" / "cards" / "2099" / "01" / "future.md"
    write_card(path, {
        "id": "future", "title_zh": "未来计划", "date": "2026-10-08",
        "event_date": "2099-01-01", "review_status": "accepted",
        "track": "industry", "topics": ["agent"],
    }, "## 一句话结论\n这是一项未来计划。")

    featured = client.get("/public/featured").text
    assert featured.index("模型发布") < featured.index("未来计划")
    daily = client.get("/public/daily").text
    assert "AI 日报 · 2026-10-10" in daily
    assert "未来计划" not in daily
    assert "未来计划" in client.get("/public/daily/2099-01-01").text
    report = client.get("/public/reports").text
    assert "2026-10-05 至 2026-10-11" in report
    assert "未来计划" not in report


def test_public_reports_use_accepted_cards_and_calendar_boundaries(tmp_path):
    client, _ = make_app(tmp_path)
    for card_id, event_day, status in [
        ("july", "2026-07-01", "accepted"),
        ("week-end", "2026-07-05", "accepted"),
        ("next-week", "2026-07-06", "accepted"),
        ("month-end", "2026-07-31", "accepted"),
        ("next-month", "2026-08-01", "accepted"),
        ("pending", "2026-07-02", "needs-review"),
    ]:
        path = tmp_path / "notes" / "cards" / "2026" / f"{card_id}.md"
        write_card(path, {
            "id": card_id, "title_zh": card_id, "date": event_day,
            "event_date": event_day, "review_status": status, "track": "industry",
            "topics": ["agent"], "source_url": f"https://example.com/{card_id}",
        }, f"## 一句话结论\n{card_id} 摘要。")

    settings = load_settings(tmp_path)
    cards = [card for card in public_cards(settings) if card["id"] in {"july", "week-end"}]
    write_report(settings.markdown_root, "week", date(2026, 6, 29), {
        "lead": "这一周两项进展值得关注。", "highlights": [
            {"text": "七月首日有公开进展。", "card_ids": ["july"]},
            {"text": "周末也有新的进展。", "card_ids": ["week-end"]},
        ], "watch": [], "source_hash": source_hash(cards), "generated_at": "2026-07-06 08:00",
    })
    week = client.get("/public/reports?period=week&day=2026-07-01").text
    assert "2026-06-29 至 2026-07-05" in week
    assert "首周仅收录 2026-07-01" in week
    assert "这一周两项进展值得关注" in week
    assert "https://example.com/july" in week and "pending" not in week
    assert "next-week" not in week
    assert "from_date=2026-07-01&amp;to_date=2026-07-05" in week

    month = client.get("/public/reports?period=month&day=2026-07-01").text
    assert "2026-07-01 至 2026-07-31" in month
    assert "总结尚未生成" in month and "month-end" not in month
    assert "这个周期暂无" in client.get("/public/reports?period=week&day=2026-07-15").text
    assert public_period_start(date(2027, 1, 1), "week") == date(2026, 12, 28)
    assert client.get("/public/reports?period=week&day=2027-01-01").status_code == 404
    assert client.get("/public/reports?period=week&day=2026-06-29").status_code == 200
    assert client.get("/public/reports?period=week&day=2026-06-22").status_code == 404
    assert client.get("/public/reports?period=week&day=2026-07-32").status_code == 404

    update_metadata(tmp_path / "notes" / "cards" / "2026" / "july.md", {"review_status": "rejected"})
    stale = client.get("/public/reports?period=week&day=2026-07-01").text
    assert "旧总结失效" in stale and "七月进展获得公开证据" not in stale
