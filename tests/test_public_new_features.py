import json
from datetime import date
from urllib.parse import urlparse
from xml.etree import ElementTree

from fastapi.testclient import TestClient

from ai_daily_update.ai_links import AI_LINKS
from ai_daily_update.feedback.corrections import read_corrections
from ai_daily_update.feeds import render_feed
from ai_daily_update.reports.public_period import source_hash, write_report
from ai_daily_update.storage.markdown import read_card, update_metadata, write_card
from ai_daily_update.web import create_app, public_cards
from ai_daily_update.config import load_settings


def setup(root):
    config = root / "config"
    config.mkdir()
    (config / "app.yaml").write_text("""timezone: Asia/Shanghai
auth:
  enabled: true
  username: reviewer
  password: secret
  session_secret: test-secret
storage:
  markdown_root: notes
  sqlite_path: data/kb.sqlite
review:
  statuses: [needs-review, accepted, later, rejected]
""", encoding="utf-8")
    (config / "sources.yaml").write_text("sources: {}\n", encoding="utf-8")
    (config / "topics.yaml").write_text("topics:\n  agent:\n    name_zh: 智能体\n", encoding="utf-8")
    return TestClient(create_app(root))


def card(root, card_id, status="accepted", track="academic", title="Agent 研究"):
    path = root / "notes" / "cards" / "2026" / "07" / f"{card_id}.md"
    write_card(path, {"id": card_id, "title_zh": title, "date": "2026-07-08",
                      "event_date": "2026-07-08", "review_status": status,
                      "track": track, "topics": ["agent"],
                      "source_url": f"https://example.org/{card_id}"},
               f"## 一句话结论\n{title}取得进展。")
    return path


def login(client):
    assert client.post("/login", data={"username": "reviewer", "password": "secret"}).status_code == 200


def test_ai_directory_official_hosts_and_no_key_input(tmp_path):
    client = setup(tmp_path)
    page = client.get("/public/ai-links")
    assert page.status_code == 200
    assert len(AI_LINKS) == 18
    assert all(urlparse(url).scheme == "https" for entry in AI_LINKS for url in entry[2:] if url)
    assert "name=\"api_key\"" not in page.text
    assert "https://www.midjourney.com/" in page.text
    assert "https://klingai.kuaishou.com/" in page.text
    assert "https://kling.ai/dev/api-key" in page.text
    assert "https://cursor.com/docs/cloud-agent/api/endpoints" in page.text
    assert client.get("/corrections", follow_redirects=False).status_code == 303


def test_research_links_require_admin_confirmation_and_accepted_card(tmp_path):
    client = setup(tmp_path)
    path = card(tmp_path, "paper")
    assert client.post("/actions/research-links", data={"card_id": "paper", "paper_url": "https://arxiv.org/abs/1234"}, follow_redirects=False).status_code == 303
    login(client)
    assert client.post("/actions/research-links", data={"card_id": "paper", "paper_url": "javascript:alert(1)", "confirmed": "yes"}).status_code == 400
    assert client.post("/actions/research-links", data={"card_id": "paper", "paper_url": "https://arxiv.org/abs/1234"}).status_code == 400
    assert client.post("/actions/research-links", data={"card_id": "paper", "paper_url": "https://arxiv.org/abs/1234", "confirmed": "yes"}).status_code == 200
    assert "https://arxiv.org/abs/1234" in client.get("/public/cards/paper").text
    assert "数据集" not in client.get("/public/cards/paper").text
    update_metadata(path, {"review_status": "needs-review"})
    assert "研究资料" not in client.get("/public/cards/paper").text


def test_card_correction_requires_real_edit_and_hides_visitor_message(tmp_path):
    client = setup(tmp_path)
    card(tmp_path, "wrong")
    submit = client.post("/public/corrections", data={"kind": "card", "target": "wrong",
                                                    "message": "访客秘密文本：这个结论需要更正。"}, follow_redirects=False)
    assert submit.status_code == 303
    item = read_corrections(tmp_path)[0]
    assert "访客秘密文本" not in client.get("/public/cards/wrong").text
    assert client.post("/actions/correction-decision", data={"correction_id": item["id"], "decision": "resolved", "summary": "已修正原文。"}, follow_redirects=False).status_code == 303
    login(client)
    assert client.post("/actions/correction-decision", data={"correction_id": item["id"], "decision": "resolved", "summary": "已修正原文。"}).status_code == 409
    page = client.get("/corrections")
    assert "访客秘密文本" in page.text
    assert client.post("/actions/correction-card-save", data={"correction_id": item["id"],
                        "current_hash": item["original_hash"], "title": "Agent 研究（修正）",
                        "source_url": "https://example.org/wrong", "content": "## 一句话结论\nAgent 研究内容已修正。"}).status_code == 200
    assert client.post("/actions/correction-decision", data={"correction_id": item["id"],
                        "decision": "resolved", "summary": "修正了卡片结论。"}).status_code == 200
    public = client.get("/public/cards/wrong").text
    assert "修正了卡片结论" in public and "访客秘密文本" not in public


def test_feeds_and_report_correction_hide_invalid_report(tmp_path):
    client = setup(tmp_path)
    accepted = card(tmp_path, "accepted")
    card(tmp_path, "pending", "needs-review")
    card(tmp_path, "rejected", "rejected")
    settings = load_settings(tmp_path)
    members = [item for item in public_cards(settings) if item["status"] == "accepted"]
    write_report(settings.markdown_root, "week", date(2026, 7, 6), {
        "period": "week", "start": "2026-07-06", "end": "2026-07-12", "source": "editor",
        "source_hash": source_hash(members), "generated_at": "2026-07-09T08:00+08:00",
        "lead": "本周研究有进展。", "highlights": [{"text": "Agent 取得进展。", "card_ids": ["accepted"]}], "watch": [],
    })
    for collection in ("featured", "reports"):
        rss = client.get(f"/feeds/{collection}.rss")
        feed = client.get(f"/feeds/{collection}.json")
        assert rss.status_code == feed.status_code == 200
        assert rss.headers["cache-control"] == feed.headers["cache-control"] == "no-store"
        ElementTree.fromstring(rss.content)
        assert json.loads(feed.text)["version"] == "https://jsonfeed.org/version/1.1"
        assert "pending" not in rss.text and "rejected" not in rss.text
    assert "accepted" in client.get("/feeds/featured.json").text
    assert "2026-07-06" in client.get("/feeds/reports.json").text
    submit = client.post("/public/corrections", data={"kind": "report", "target": "week:2026-07-06",
                                                    "message": "访客秘密文本：报告总述需要核对。"}, follow_redirects=False)
    assert submit.status_code == 303
    correction = read_corrections(tmp_path)[0]
    login(client)
    assert client.post("/actions/correction-decision", data={"correction_id": correction["id"],
                        "decision": "resolved", "summary": "修正了报告总述。"}).status_code == 409
    report_page = client.get("/reports?period=week&day=2026-07-06")
    from bs4 import BeautifulSoup
    token = BeautifulSoup(report_page.text, "html.parser").select_one('input[name="source_hash"]')["value"]
    assert client.post("/actions/report-save", data={"period": "week", "day": "2026-07-06", "source_hash": token,
                      "lead": "修正后的本周研究进展。", "highlight_text_0": "Agent 取得进展。",
                      "highlight_ids_0": "accepted"}).status_code == 200
    assert client.post("/actions/correction-decision", data={"correction_id": correction["id"],
                        "decision": "resolved", "summary": "修正了报告总述。"}).status_code == 200
    assert "修正了报告总述" in client.get("/public/reports?period=week&day=2026-07-06").text
    update_metadata(accepted, {"review_status": "rejected"})
    assert "2026-07-06" not in client.get("/feeds/reports.json").text
    assert "修正了报告总述" not in client.get("/public/reports?period=week&day=2026-07-06").text


def test_follow_items_are_accepted_only_and_filter_union(tmp_path):
    client = setup(tmp_path)
    card(tmp_path, "agent", title="Agent 研究")
    card(tmp_path, "other", title="别的研究")
    card(tmp_path, "pending", "needs-review", title="Agent 待审核")
    response = client.get("/public/follow-items?keyword=Agent%20研究")
    assert response.status_code == 200
    assert [item["id"] for item in response.json()["items"]] == ["agent"]
    assert client.get("/public/follow-items?topic=agent").json()["items"]
    assert [item["id"] for item in client.get("/public/follow-items?source=example.org%2Fagent").json()["items"]] == ["agent"]
    assert not client.get("/public/follow-items?topic=agent&page=1001").json()["items"]
    assert not client.get("/public/follow-items").json()["items"]
    assert client.get("/public/follows").status_code == 200


def test_feed_escapes_markup_and_invalid_xml_characters():
    body, _ = render_feed([{"title": "<Agent & AI>\x00", "summary": "<结论 & 依据>",
                           "url": "https://example.org/a?x=1&y=2", "date": "2026-07-08"}],
                          "标题", "https://example.org/", "https://example.org/feed", "rss", "Asia/Shanghai")
    root = ElementTree.fromstring(body)
    assert root.findtext("./channel/item/title") == "<Agent & AI>"
    assert root.findtext("./channel/item/description") == "<结论 & 依据>"
