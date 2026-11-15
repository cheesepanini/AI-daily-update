from datetime import date
from io import BytesIO

import pytest
from bs4 import BeautifulSoup
from fastapi.testclient import TestClient
from PIL import Image

from ai_daily_update import news_media
from ai_daily_update.collectors.web_page import extract_document_from_html
from ai_daily_update.config import load_settings
from ai_daily_update.processors.candidates import Candidate
from ai_daily_update.processors.card_builder import apply_content_date, apply_source_evidence, build_card_metadata
from ai_daily_update.reports.public_period import source_hash, write_report
from ai_daily_update.storage.markdown import read_card, update_metadata, write_card
from ai_daily_update.utils.dates import public_date_fields
from ai_daily_update.web import create_app, public_cards


def test_original_source_dates_and_images_are_distinguished_from_inference():
    candidate = Candidate("https://example.org/news", "industry", [], "消息")
    document = extract_document_from_html(candidate.url, """
        <meta property="article:published_time" content="2026-07-08T10:05:00+08:00">
        <meta property="og:image" content="/cover.png">
        <header><img src="/logo.png"></header>
        <article><p>事件日期：2026-07-07</p><img src="/cover.png">
        <img data-src="/photo.jpg" alt="现场"><img src="data:image/svg+xml,xxx"></article>
    """)
    metadata = build_card_metadata(candidate, date(2026, 7, 9), "Asia/Shanghai")
    metadata = apply_content_date(metadata, candidate, "事件可能发生于 2026-07-06")
    assert not public_date_fields(metadata)["display_date"]
    apply_source_evidence(metadata, candidate, document)
    dates = public_date_fields(metadata)
    assert dates["display_date"] == "2026-07-07" and dates["reported_date"] == "2026-07-08"
    assert [item["url"] for item in document.images] == ["https://example.org/cover.png", "https://example.org/photo.jpg"]


def test_download_checks_redirect_destination_and_pins_public_ip(monkeypatch):
    calls = []

    class Redirect:
        status = 302
        headers = {"Location": "https://127.0.0.1/image.png"}

        def close(self):
            pass

    class Pool:
        def __init__(self, address, port, **kwargs):
            calls.append((address, kwargs["server_hostname"]))

        def urlopen(self, *args, **kwargs):
            return Redirect()

        def close(self):
            pass

    def resolve(host, *args, **kwargs):
        return [(None, None, None, None, ("8.8.8.8" if host == "example.org" else host, 443))]

    monkeypatch.setattr(news_media.socket, "getaddrinfo", resolve)
    monkeypatch.setattr(news_media.urllib3, "HTTPSConnectionPool", Pool)
    with pytest.raises(ValueError, match="公开网络"):
        news_media.download_public("https://example.org/image.png", 1024, "image/")
    assert calls == [("8.8.8.8", "example.org")]


def test_public_dates_and_reviewed_images_follow_the_card(tmp_path, monkeypatch):
    config = tmp_path / "config"
    config.mkdir()
    (config / "app.yaml").write_text("timezone: Asia/Shanghai\nauth: {enabled: false}\n", encoding="utf-8")
    settings = load_settings(tmp_path)
    page = "https://example.org/news"
    url = "https://example.org/cover.png"
    path = settings.markdown_root / "cards" / "sample.md"
    write_card(path, {
        "id": "sample", "title_zh": "配图验收样例", "date": "2026-07-10",
        "event_date": "2026-07-07", "collected_date": "2026-07-10", "track": "industry",
        "review_status": "accepted", "source_url": page,
        "image_candidates_page": page, "image_candidates_source": page,
        "image_candidates": [{"url": url, "caption": "现场"}],
    }, "## 一句话结论\n正文。\n![未审核外链](https://example.org/unapproved.png)")
    client = TestClient(create_app(tmp_path))
    assert "旧记录日期 · 待核实" in client.get("/public/featured").text
    assert not BeautifulSoup(client.get("/public/cards/sample").text, "html.parser").select('img[src*="unapproved.png"]')
    assert not BeautifulSoup(client.get("/public/featured").text, "html.parser").select(".public-card-thumbnail")
    client.post("/actions/card-event-date", data={"card_id": "sample", "review_both": "true",
                "event_date": "", "reported_date": "2026-07-08"})
    assert "报道日期" in client.get("/public/featured").text
    assert "配图验收样例" in client.get("/public/reports?period=day&day=2026-07-08").text
    assert "配图验收样例" not in client.get("/public/reports?period=day&day=2026-07-07").text
    members = public_cards(settings)
    for period, start in [("week", date(2026, 7, 6)), ("month", date(2026, 7, 1))]:
        write_report(settings.markdown_root, period, start, {
            "source": "editor", "source_hash": source_hash(members), "lead": "有效总结",
            "highlights": [{"text": "重点", "card_ids": ["sample"]}],
            "watch": [{"text": "重复引用", "card_ids": ["sample"]}],
        })

    buffer = BytesIO()
    Image.new("RGB", (850, 600), "teal").save(buffer, format="PNG")
    monkeypatch.setattr(news_media, "download_public", lambda *args: (url, buffer.getvalue()))
    endpoint = "/actions/card-images"
    form = {"card_id": "sample", "url": url}
    client.post(endpoint, data={**form, "action": "preview"})
    image_id = read_card(path).metadata["image_candidates"][0]["preview"]
    asset = f"/public/card-images/sample/{image_id}/thumb"
    publish = {**form, "action": "publish", "image_id": image_id, "credit": "现场摄影"}
    client.post(endpoint, data=publish)
    assert client.get(asset).status_code == 404
    client.post(endpoint, data={**publish, "confirmed": "true"})
    response = client.get(asset)
    assert response.status_code == 200 and response.headers["cache-control"] == "no-store"
    with Image.open(BytesIO(response.content)) as thumb:
        assert max(thumb.size) == 480
    assert asset in client.get("/public/featured").text
    assert "现场摄影" in client.get("/public/cards/sample").text
    assert "现场摄影" in client.get("/public/reports?period=day&day=2026-07-08").text
    for period in ("week", "month"):
        assert client.get(f"/public/reports?period={period}&day=2026-07-08").text.count("现场摄影") == 1
    update_metadata(path, {"review_status": "rejected"})
    assert client.get(asset).status_code == 404
    assert "有效总结" not in client.get("/public/reports?period=week&day=2026-07-08").text
    update_metadata(path, {"review_status": "accepted"})
    client.post(endpoint, data={"card_id": "sample", "action": "withdraw", "image_id": image_id})
    assert client.get(asset).status_code == 404
    client.post("/actions/card-event-date", data={"card_id": "sample", "review_both": "true",
                "event_date": "", "reported_date": ""})
    assert "配图验收样例" not in client.get("/public?to_date=2026-07-10").text
    assert "有效总结" not in client.get("/public/reports?period=month&day=2026-07-08").text
