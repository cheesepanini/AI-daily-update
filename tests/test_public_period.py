import json
from datetime import date

import pytest

from ai_daily_update.reports.public_period import failed_report, generate_report, read_report
from ai_daily_update.reports.public_period import source_hash, write_report
from ai_daily_update.storage.markdown import update_metadata, write_card


class FakeLLM:
    available = True

    def __init__(self, bad_ids=False):
        self.calls = 0
        self.bad_ids = bad_ids

    def generate_card_content(self, prompt):
        self.calls += 1
        payload = json.loads(prompt.splitlines()[-1])
        if isinstance(payload, list) and payload and "title" in payload[0]:
            return json.dumps({"notes": [
                {"text": f"本批卡片记录了进展 {index}。", "card_ids": [item["id"]]}
                for index, item in enumerate(payload[:3])
            ]})
        ids = [note["card_ids"][0] for note in payload]
        if self.bad_ids:
            ids = ["not-accepted"]
        return json.dumps({
            "lead": "本期多个进展集中在模型应用。",
            "highlights": [
                {"text": f"阶段性进展 {index + 1}。", "card_ids": [card_id]}
                for index, card_id in enumerate(ids[:3])
            ],
            "watch": [{"text": "继续关注后续公开验证。", "card_ids": [ids[0]]}],
        })


def cards(count=26):
    return [{
        "id": f"card-{index:02d}", "event_date": "2026-07-08", "title": f"进展 {index}",
        "conclusion": f"结论 {index}", "event_overview": f"概况 {index}",
        "topics": ["agent"], "source_url": f"https://example.com/{index}",
        "search_fields": {"body": f"正文 {index}"},
    } for index in range(count)]


def test_period_generation_batches_and_reuses_day_notes(tmp_path):
    items = cards()
    llm = FakeLLM()
    start = date(2026, 7, 6)
    generate_report(tmp_path, "week", start, date(2026, 7, 12), items, llm, "Asia/Shanghai")
    assert llm.calls == 3  # two bounded day batches plus one report synthesis
    report = read_report(tmp_path, "week", start, items)
    assert report and len(report["highlights"]) == 3
    assert report["highlights"][0]["sources"][0]["id"] == "card-00"

    generate_report(tmp_path, "month", date(2026, 7, 1), date(2026, 7, 31), items, llm, "Asia/Shanghai")
    assert llm.calls == 4  # monthly report reuses the day notes
    items[0]["search_fields"]["body"] = "修正后的正文"
    assert read_report(tmp_path, "week", start, items) is None


def test_invalid_citation_never_publishes(tmp_path):
    items = cards(3)
    with pytest.raises(ValueError, match="证据引用"):
        generate_report(
            tmp_path, "week", date(2026, 7, 6), date(2026, 7, 12),
            items, FakeLLM(bad_ids=True), "Asia/Shanghai",
        )
    assert read_report(tmp_path, "week", date(2026, 7, 6), items) is None


def test_scheduled_refresh_only_regenerates_changed_periods(tmp_path, monkeypatch):
    from ai_daily_update import cli, web
    from ai_daily_update.config import load_settings

    config = tmp_path / "config"
    config.mkdir()
    (config / "app.yaml").write_text("timezone: Asia/Shanghai\nstorage:\n  markdown_root: notes\n", encoding="utf-8")
    (config / "sources.yaml").write_text("sources: {}\n", encoding="utf-8")
    (config / "topics.yaml").write_text("topics: {}\n", encoding="utf-8")
    paths = []
    for card_id in ("alpha", "beta"):
        path = tmp_path / "notes" / "cards" / "2026" / "07" / f"{card_id}.md"
        write_card(path, {
            "id": card_id, "title_zh": card_id, "date": "2026-07-08",
            "event_date": "2026-07-08", "review_status": "accepted",
            "source_url": f"https://example.com/{card_id}",
        }, f"## 一句话结论\n{card_id} 有一项进展。")
        paths.append(path)
    calls = []

    def fake_generate(root, period, start, end, members, llm, timezone):
        calls.append((period, start))
        return write_report(root, period, start, {
            "lead": "本期有实际进展。",
            "highlights": [
                {"text": f"{card['title']} 的进展。", "card_ids": [card["id"]]}
                for card in members[:3]
            ], "watch": [], "source_hash": source_hash(members), "generated_at": "2026-07-09T08:00",
        })

    monkeypatch.setattr(cli, "_llm_client", lambda settings: object())
    monkeypatch.setattr(web, "generate_report", fake_generate)
    settings = load_settings(tmp_path)
    assert len(web.refresh_public_reports(settings)) == 2
    assert web.refresh_public_reports(settings) == []
    update_metadata(paths[0], {"review_status": "rejected"})
    assert len(web.refresh_public_reports(settings)) == 2
    assert len(calls) == 4

    def fail_generation(*args):
        raise ValueError("model unavailable")

    monkeypatch.setattr(web, "generate_report", fail_generation)
    update_metadata(paths[1], {"title_zh": "beta revised"})
    assert web.refresh_public_reports(settings) == []
    members = [card for card in web.public_cards(settings) if card["status"] == "accepted"]
    assert failed_report(settings.markdown_root, "week", date(2026, 7, 6), members)
    assert read_report(settings.markdown_root, "week", date(2026, 7, 6), members) is None
