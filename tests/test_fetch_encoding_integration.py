import http.server
import socketserver
import threading
from contextlib import contextmanager

from ai_daily_update.collectors.company_blogs import CompanyBlogConfig, fetch_company_blog
from ai_daily_update.collectors.web_page import fetch_source_document


@contextmanager
def _server(body_bytes: bytes, content_type: str):
    class Handler(http.server.BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            self.send_response(200)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body_bytes)))
            self.end_headers()
            self.wfile.write(body_bytes)

        def log_message(self, *args) -> None:
            pass

    server = socketserver.TCPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_address[1]}/"
    finally:
        server.shutdown()
        thread.join()


def test_fetch_source_document_decodes_utf8_html_without_charset_header() -> None:
    html = (
        "<html><head><meta charset=\"utf-8\"><title>中文标题</title></head>"
        "<body><main><p>正文内容，测试编码修复。</p></main></body></html>"
    ).encode("utf-8")

    with _server(html, "text/html") as url:
        document = fetch_source_document(url)

    assert document.title == "中文标题"
    assert "正文内容，测试编码修复。" in document.text


def test_fetch_company_blog_decodes_utf8_listing_without_charset_header() -> None:
    html = (
        "<html><body><article>"
        "<a href=\"/blog/post\">中文文章标题，测试博客抓取编码修复</a>"
        "</article></body></html>"
    ).encode("utf-8")

    with _server(html, "text/html") as url:
        source = CompanyBlogConfig(name="Example", url=url)
        items = fetch_company_blog(source)

    assert items[0].title == "中文文章标题，测试博客抓取编码修复"


def test_fetch_rss_feed_decodes_gbk_feed_without_charset_header() -> None:
    from ai_daily_update.collectors.rss import RSSFeedConfig, fetch_rss_feed

    xml = (
        '<?xml version="1.0" encoding="gbk"?>'
        "<rss version=\"2.0\"><channel><item>"
        "<title>中文资讯标题</title>"
        "<link>https://example.com/article</link>"
        "</item></channel></rss>"
    ).encode("gbk")

    with _server(xml, "text/xml") as url:
        feed = RSSFeedConfig(name="Example", track="industry", url=url)
        items = fetch_rss_feed(feed)

    assert items[0].title == "中文资讯标题"
