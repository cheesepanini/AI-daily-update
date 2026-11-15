from __future__ import annotations

import hashlib
import ipaddress
import re
import socket
import tempfile
import time
from io import BytesIO
from pathlib import Path
from urllib.parse import quote, urljoin, urlsplit

import urllib3
from PIL import Image, ImageOps

from ai_daily_update.collectors.web_page import extract_document_from_html
from ai_daily_update.collectors.document import SourceDocument
from ai_daily_update.processors.card_builder import source_news_dates
from ai_daily_update.storage.markdown import read_card, write_card
from ai_daily_update.utils.dates import public_date_fields
from ai_daily_update.utils.lock import exclusive_file_lock


MAX_IMAGE_BYTES = 8 * 1024 * 1024


def download_public(url: str, limit: int, expected_type: str) -> tuple[str, bytes]:
    """Fetch a bounded public resource, pinning the checked IP on each hop."""
    deadline = time.monotonic() + 15
    for _ in range(4):
        if len(url) > 2048 or "\\" in url or any(char.isspace() for char in url):
            raise ValueError("来源地址无效")
        parts = urlsplit(url)
        if parts.scheme not in {"http", "https"} or not parts.hostname or parts.username is not None:
            raise ValueError("只支持公开的 HTTP(S) 地址")
        hostname = parts.hostname.encode("idna").decode("ascii")
        port = 443 if parts.scheme == "https" else 80
        if parts.port not in {None, port}:
            raise ValueError("来源端口无效")
        addresses = {entry[4][0] for entry in socket.getaddrinfo(hostname, port, type=socket.SOCK_STREAM)}
        if not addresses or any(not ipaddress.ip_address(ip).is_global or ipaddress.ip_address(ip).is_multicast for ip in addresses):
            raise ValueError("来源不是公开网络地址")
        address = sorted(addresses, key=lambda ip: (":" in ip, ip))[0]
        if parts.scheme == "https":
            pool = urllib3.HTTPSConnectionPool(address, port, server_hostname=hostname, assert_hostname=hostname, cert_reqs="CERT_REQUIRED")
        else:
            pool = urllib3.HTTPConnectionPool(address, port)
        target = parts.path or "/"
        if parts.query:
            target += "?" + parts.query
        response = None
        try:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise ValueError("来源请求超时")
            response = pool.urlopen("GET", target, headers={"Host": f"[{hostname}]" if ":" in hostname else hostname,
                                                           "Accept-Encoding": "identity", "User-Agent": "AI-Daily-Update/0.2"},
                                    timeout=urllib3.Timeout(connect=min(4, remaining), read=min(4, remaining)),
                                    redirect=False, retries=False, preload_content=False)
            if response.status in {301, 302, 303, 307, 308} and response.headers.get("Location"):
                url = urljoin(url, response.headers["Location"])
                response.close()
                continue
            content_type = response.headers.get("Content-Type", "").split(";", 1)[0].lower()
            if response.status != 200 or not content_type.startswith(expected_type):
                raise ValueError("来源响应或格式不支持")
            if int(response.headers.get("Content-Length") or 0) > limit:
                raise ValueError("来源文件超过大小限制")
            chunks = bytearray()
            for chunk in response.stream(64 * 1024, decode_content=False):
                chunks.extend(chunk)
                if len(chunks) > limit or time.monotonic() > deadline:
                    raise ValueError("来源文件过大或请求超时")
            return url, bytes(chunks)
        finally:
            if response is not None:
                response.close()
            pool.close()
    raise ValueError("来源跳转次数过多")


def fetch_news_evidence(page_url: str) -> SourceDocument:
    url, html = download_public(page_url, 3 * 1024 * 1024, "text/html")
    original, final = urlsplit(page_url), urlsplit(url)
    if original.hostname != final.hostname or original.path.rstrip("/") != final.path.rstrip("/"):
        raise ValueError("原报道已重定向到其他页面，请人工核对")
    return extract_document_from_html(url, html)


def card_source_page(metadata: dict) -> str:
    return str(metadata.get("parent_source_url") or metadata.get("source_url") or "")


def image_candidates(metadata: dict) -> list[dict]:
    if metadata.get("image_candidates_page") == card_source_page(metadata) and metadata.get("image_candidates_source") == metadata.get("source_url"):
        return metadata.get("image_candidates", [])
    return []


def refresh_image_candidates(path: Path) -> int:
    snapshot = read_card(path).metadata
    page = card_source_page(snapshot)
    count, _ = save_news_evidence(path, page, snapshot.get("source_url"), fetch_news_evidence(page))
    return count


def save_news_evidence(path: Path, page: str, source: str | None, document: SourceDocument,
                       *, backfill: bool = False) -> tuple[int, str]:
    with exclusive_file_lock(path.with_name(f".{path.name}.lock"), blocking=True):
        card = read_card(path)
        metadata = card.metadata
        if card_source_page(metadata) != page or metadata.get("source_url") != source:
            raise ValueError("原报道链接已变化，请刷新卡片")
        if backfill and metadata.get("review_status") != "accepted":
            return 0, ""
        existing = {item["url"]: item for item in image_candidates(metadata)}
        updates = dict(image_candidates_page=page, image_candidates_source=source,
                       image_candidates=[existing.get(item["url"], item) for item in document.images])
        moved_date = ""
        if backfill and "news_dates" not in metadata:
            dates = source_news_dates(document, bool(metadata.get("digest_item_index")))
            verified = dates.get("event") or dates.get("reported")
            legacy = public_date_fields(metadata)["legacy_date"]
            if verified and (not legacy or verified == legacy):
                updates["news_dates"] = dates
            elif verified:
                # An editor can confirm the move and regenerate the affected reports together.
                moved_date = verified
        if any(metadata.get(key) != value for key, value in updates.items()):
            write_card(path, {**metadata, **updates}, card.content)
    return len(document.images), moved_date


def image_path(root: Path, image_id: str, size: str) -> Path:
    if not re.fullmatch(r"[a-f0-9]{64}", image_id) or size not in {"full", "thumb"}:
        raise ValueError("无效图片地址")
    return root / "data" / "news_images" / image_id[:2] / f"{image_id}-{size}.jpg"


def prepare_image(root: Path, url: str) -> str:
    _, data = download_public(url, MAX_IMAGE_BYTES, "image/")
    return store_news_image(root, data)


def store_news_image(root: Path, data: bytes) -> str:
    if len(data) > MAX_IMAGE_BYTES:
        raise ValueError("来源文件超过大小限制")
    with Image.open(BytesIO(data), formats=["JPEG", "PNG", "WEBP", "GIF"]) as image:
        if image.width * image.height > 24_000_000 or min(image.size) < 80:
            raise ValueError("图片尺寸不支持")
        image.thumbnail((1440, 1440))
        oriented = ImageOps.exif_transpose(image).convert("RGBA")
    raster = Image.new("RGB", oriented.size, "white")
    raster.paste(oriented, mask=oriented.getchannel("A"))
    full = BytesIO()
    raster.save(full, format="JPEG", quality=85, optimize=True)
    image_id = hashlib.sha256(full.getvalue()).hexdigest()
    raster.thumbnail((480, 480))
    thumb = BytesIO()
    raster.save(thumb, format="JPEG", quality=82, optimize=True)
    for size, content in (("full", full), ("thumb", thumb)):
        path = image_path(root, image_id, size)
        path.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(dir=path.parent, delete=False) as temp:
            temp.write(content.getvalue())
        Path(temp.name).replace(path)
    return image_id


def approved_images(metadata: dict, card_id: str) -> list[dict]:
    images = []
    for image in metadata.get("approved_images", [])[:4]:
        if image.get("card_source") != metadata.get("source_url") or image.get("page") != card_source_page(metadata):
            continue
        image_id = image.get("id", "")
        if not re.fullmatch(r"[a-f0-9]{64}", image_id):
            continue
        base = f"/public/card-images/{quote(card_id, safe='')}/{image_id}"
        images.append({**image, "full_url": f"{base}/full", "thumb_url": f"{base}/thumb"})
    return images
