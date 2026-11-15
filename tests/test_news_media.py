from concurrent.futures import ThreadPoolExecutor
import json
from datetime import date
from io import BytesIO
from threading import Barrier
from time import sleep

import pytest
from bs4 import BeautifulSoup
from fastapi.testclient import TestClient
from PIL import Image

from ai_daily_update import news_media, web
from ai_daily_update.collectors.web_page import extract_document_from_html
from ai_daily_update.collectors.document import SourceDocument
from ai_daily_update.collectors.rss import RSSItem
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


def test_qbitai_keeps_article_images_and_uses_the_bylines_publication_date():
    document = extract_document_from_html("https://www.qbitai.com/2026/11/510013.html", """
        <main><div class="article">
          <div class="article_info"><span class="date">2026-11-14</span></div>
          <p>这段正文介绍了发布活动。</p><img data-src="/article-photo.png">
        </div></main>
    """)
    assert document.published == "2026-11-14"
    assert "这段正文介绍了发布活动" in document.text
    assert [image["url"] for image in document.images] == ["https://www.qbitai.com/article-photo.png"]


def test_concurrent_searches_serialize_bulk_date_index_refresh(tmp_path, monkeypatch):
    settings = load_settings(tmp_path)
    for number in range(4):
        write_card(settings.markdown_root / "cards" / f"{number}.md", {
            "id": str(number), "title_zh": f"消息{number}", "review_status": "accepted",
            "track": "industry", "news_dates": {"event": "2026-07-07", "reported": "2026-07-08"},
        }, "## 一句话结论\n正文。")
    connect = web.db.connect
    connect(settings.sqlite_path).close()
    barrier = Barrier(3)

    def connect_together(path):
        connection = connect(path)
        connection.execute("PRAGMA busy_timeout = 20")
        barrier.wait(timeout=3)
        return connection

    def slow_read(path):
        sleep(0.04)
        return read_card(path)

    monkeypatch.setattr(web.db, "connect", connect_together)
    monkeypatch.setattr(web, "read_card", slow_read)
    with ThreadPoolExecutor(max_workers=3) as pool:
        assert list(pool.map(lambda _: len(web.search_public_cards(settings, status="accepted")), range(3))) == [4, 4, 4]


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


def test_legacy_source_backfill_preserves_periods_and_manual_dates(tmp_path):
    path = tmp_path / "news.md"
    url = "https://arxiv.org/abs/2607.12345v1"
    original = {"source_url": url, "date": "2026-07-07", "review_status": "accepted"}
    write_card(path, original, "报道正文")
    html = '<meta name="citation_online_date" content="2026/07/08"><meta property="og:image" content="/arxiv-logo-fb.png">'
    document = extract_document_from_html(url, html)
    assert not document.images
    assert news_media.save_news_evidence(path, url, url, document, backfill=True) == (0, "2026-07-08")
    assert "news_dates" not in read_card(path).metadata

    document = extract_document_from_html(url, html.replace("07/08", "07/07"))
    assert news_media.save_news_evidence(path, url, url, document, backfill=True) == (0, "")
    metadata = read_card(path).metadata
    assert metadata["news_dates"]["event"] == metadata["news_dates"]["reported"] == "2026-07-07"

    update_metadata(path, {"news_dates": {"event": "2026-07-06", "event_basis": "人工核对"}})
    news_media.save_news_evidence(path, url, url, document, backfill=True)
    assert read_card(path).metadata["news_dates"] == {
        "event": "2026-07-06", "event_basis": "人工核对",
        "reported": "2026-07-07", "reported_basis": "原文发布时间",
    }


def test_model_date_requires_original_quote_and_merges_with_report_date(tmp_path):
    page = "https://example.org/news"
    quote = "On October 29, the attacker published a malicious extension."
    document = SourceDocument(url=page, title="Incident update", description="", text=quote, published="2026-11-13")

    class Model:
        available = True

        def generate_learning_reply(self, instructions, prompt):
            return json.dumps([{"index": 0, "date": "2026-10-29", "quote": quote},
                               {"index": 1, "date": "2026-10-30", "quote": quote},
                               {"index": 2, "date": "2026-10-29", "quote": "On October 29, invented evidence."}])

    results = news_media.infer_source_events(Model(), [(document.title, document, 0)] * 3)
    assert results[0].event_date_text.endswith(quote)
    assert not results[1].event_date_text and not results[2].event_date_text
    path = tmp_path / "history.md"
    write_card(path, {"source_url": page, "review_status": "accepted",
                      "news_dates": {"reported": "2026-11-13", "reported_basis": "人工核对"}}, "正文")
    assert news_media.save_news_evidence(path, page, page, results[0], backfill=True,
                                         apply_period_changes=True)[1] == "2026-10-29"
    dates = read_card(path).metadata["news_dates"]
    assert dates["event"] == "2026-10-29" and dates["reported_basis"] == "人工核对"


def test_openai_publisher_feed_fills_dates_only_for_exact_article(monkeypatch):
    url = "https://openai.com/index/new-model"
    def unavailable(*args):
        raise ValueError("blocked article")
    monkeypatch.setattr(news_media, "download_public", unavailable)
    monkeypatch.setattr(news_media, "fetch_rss_feed", lambda *a, **kw: [
        RSSItem("OpenAI", "industry", "New model", url + "/", "Fri, 13 Nov 2026 11:00:00 GMT",
                "We’re introducing a new model."),
    ])
    news_media._openai_feed.cache_clear()
    try:
        document = news_media.fetch_news_evidence(url)
        assert document.publication_basis == "OpenAI 官方 RSS"
        with pytest.raises(ValueError, match="blocked article"):
            news_media.fetch_news_evidence(url + "-other")
    finally:
        news_media._openai_feed.cache_clear()


def test_arxiv_figures_crosscheck_exact_paper_and_generate_private_preview(tmp_path, monkeypatch):
    paper = "2611.12345v1"
    abs_page = f"https://arxiv.org/abs/{paper}"
    html_page = f"https://arxiv.org/html/{paper}"
    abs_html = b'<meta name="citation_online_date" content="2026/11/12"><div class="license"><a href="https://creativecommons.org/licenses/by/4.0/">view license</a></div>'
    html = b'''<span class="ltx_personname">Example Author</span>
    <figure><img src="figure1.png"><figcaption>Figure 1: Architecture</figcaption></figure>
    <figure><img src="figure2.png"><figcaption>Figure 2: Reproduced with permission</figcaption></figure>
    <figure><img src="/html/2611.12345v2/other.png"><figcaption>Figure 3: Model</figcaption></figure>'''
    documents = {abs_page: abs_html, html_page: html}
    monkeypatch.setattr(news_media, "download_public", lambda url, *_: (url, documents[url]))
    preview = "a" * 64
    monkeypatch.setattr(news_media, "prepare_image", lambda root, url: preview)
    document = news_media.preview_licensed_figures(tmp_path, news_media.fetch_news_evidence(abs_page))
    assert document.published == "2026-11-12"
    assert [item["url"] for item in document.images] == [f"{html_page}/figure1.png"]
    assert document.images[0]["preview"] == preview
    candidate = Candidate(abs_page, "academic", [], "Test paper")
    metadata = build_card_metadata(candidate, date(2026, 11, 12), "Asia/Shanghai")
    apply_source_evidence(metadata, candidate, document)
    assert not news_media.approved_images(metadata, "sample")


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
    dates = BeautifulSoup(client.get("/public/featured").text, "html.parser").select_one(".public-card-date")
    assert dates.strong.get_text(strip=True) == "事件时间待核实"
    assert dates.small.time["datetime"] == "2026-07-08"
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
    client.post("/actions/card-event-date", data={"card_id": "sample", "review_both": "true",
                "event_date": "2026-07-08", "reported_date": "2026-07-08"})
    for route in ("/public/featured", "/public/cards/sample", "/public/reports?period=day&day=2026-07-08",
                  "/public/reports?period=week&day=2026-07-08", "/public/reports?period=month&day=2026-07-08"):
        date_block = BeautifulSoup(client.get(route).text, "html.parser").select_one(".public-card-date")
        assert date_block.strong.time["datetime"] == date_block.small.time["datetime"] == "2026-07-08"
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
