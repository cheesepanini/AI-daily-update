from __future__ import annotations

import hashlib
import hmac
import csv
import json
import os
import re
import threading
import time
import traceback
import uuid
from datetime import datetime, timedelta
from pathlib import Path
import shutil
from typing import Any
from urllib.parse import urlencode, urlparse
from zoneinfo import ZoneInfo

from fastapi import FastAPI, File, Form, Request, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse, PlainTextResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from markdown_it import MarkdownIt
import yaml

from ai_daily_update.api.public import public_card_summary
from ai_daily_update.api.schemas import (
    ApiError,
    Pagination,
    PublicCardDetail,
    PublicCardListResponse,
    PublicMetaResponse,
)
from ai_daily_update.config import Settings, load_settings
from ai_daily_update.processors.concepts import match_foundational_concepts
from ai_daily_update.feedback.events import append_feedback_event, feedback_log_path, read_feedback_events
from ai_daily_update.preference.features import (
    SURFACES,
    extract_preference_features,
    feature_output_path,
    read_feature_records,
)
from ai_daily_update.ppt.decks import PPTDeck, deck_options, selected_ppt_deck
from ai_daily_update.ppt.plan import generate_ppt_plan, load_ppt_node_matches
from ai_daily_update.reports.brief import extract_sections, generate_brief
from ai_daily_update.source_proposals import read_source_proposals
from ai_daily_update.storage import db
from ai_daily_update.storage.indexer import rebuild_index
from ai_daily_update.storage.markdown import iter_cards, read_card, update_metadata
from ai_daily_update.trends import (
    trend_count,
    trend_group_count,
    trend_matches,
    trend_term_groups as build_trend_term_groups,
)
from ai_daily_update.utils.config import list_section, section
from ai_daily_update.utils.dates import now_iso, today_in_timezone


PACKAGE_ROOT = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=str(PACKAGE_ROOT / "templates"))
markdown_renderer = MarkdownIt("commonmark", {"html": False}).enable("table")

STATUS_LABELS = {
    "needs-review": "待审核",
    "accepted": "已接受",
    "later": "稍后处理",
    "rejected": "已拒绝",
}

TRACK_LABELS = {
    "academic": "学术前沿",
    "industry": "产业观察",
}

SOURCE_THEME_LABELS = {
    "general-ai": "泛 AI",
    "foundation-model": "基础模型",
    "agent": "智能体",
    "spatial-intelligence": "空间智能",
    "self-supervised-learning": "自监督学习",
    "generative-model": "生成模型",
    "ai4science": "AI4S",
    "benchmark-evaluation": "公开测评与榜单",
    "academic-research": "学术论文",
    "chinese-media": "中文媒体",
    "ai-industry": "AI 产业",
    "ai-compute": "AI 算力",
    "ai-policy": "AI 政策",
}

DEFAULT_SOURCE_TOPIC_OPTIONS = [
    {"id": theme_id, "label": label}
    for theme_id, label in SOURCE_THEME_LABELS.items()
]

JOBS: dict[str, dict[str, Any]] = {}
JOBS_LOCK = threading.Lock()
SCHEDULER_LOCK = threading.Lock()
SCHEDULER_THREADS: dict[str, threading.Thread] = {}

LOGIN_MAX_ATTEMPTS = 5
LOGIN_WINDOW_SECONDS = 300.0


def login_rate_limited(app: FastAPI, client_ip: str) -> bool:
    state = _login_attempts_state(app)
    with state["lock"]:
        attempts = state["attempts"].get(client_ip, [])
        cutoff = time.time() - LOGIN_WINDOW_SECONDS
        attempts = [attempt for attempt in attempts if attempt >= cutoff]
        state["attempts"][client_ip] = attempts
        return len(attempts) >= LOGIN_MAX_ATTEMPTS


def record_login_failure(app: FastAPI, client_ip: str) -> None:
    state = _login_attempts_state(app)
    with state["lock"]:
        state["attempts"].setdefault(client_ip, []).append(time.time())


def clear_login_failures(app: FastAPI, client_ip: str) -> None:
    state = _login_attempts_state(app)
    with state["lock"]:
        state["attempts"].pop(client_ip, None)


def _login_attempts_state(app: FastAPI) -> dict[str, Any]:
    if not hasattr(app.state, "login_attempts"):
        app.state.login_attempts = {"lock": threading.Lock(), "attempts": {}}
    return app.state.login_attempts


def install_auth(app: FastAPI, settings: Settings) -> None:
    if not auth_settings(settings)["enabled"]:
        return

    @app.middleware("http")
    async def require_login(request: Request, call_next):
        path = request.url.path
        if path == "/login" or path.startswith("/static/"):
            return await call_next(request)
        if request.method == "GET" and (path == "/" or path == "/public" or path.startswith("/public/")):
            return await call_next(request)
        if request.method == "GET" and path.startswith("/api/v1/"):
            return await call_next(request)
        if auth_session_valid(request, settings):
            return await call_next(request)
        if request.headers.get("x-requested-with") == "fetch":
            return JSONResponse(
                {"error": "登录状态已失效，请重新登录后再试。"},
                status_code=401,
            )
        return RedirectResponse("/login", status_code=303)


def auth_settings(settings: Settings) -> dict[str, Any]:
    config = settings.app.get("auth", {})
    enabled = bool(config.get("enabled", False))
    username = str(config.get("username") or "") or os.getenv(
        str(config.get("username_env") or "AI_DAILY_ADMIN_USERNAME"), ""
    )
    password = str(config.get("password") or "") or os.getenv(
        str(config.get("password_env") or "AI_DAILY_ADMIN_PASSWORD"), ""
    )
    secret = str(config.get("session_secret") or "") or os.getenv(
        str(config.get("session_secret_env") or "AI_DAILY_SESSION_SECRET"), ""
    )
    if enabled and (not username or not password or not secret):
        raise RuntimeError(
            "auth.enabled is true but username/password/session_secret are not configured. "
            "Set AI_DAILY_ADMIN_USERNAME, AI_DAILY_ADMIN_PASSWORD and AI_DAILY_SESSION_SECRET "
            "(or the matching auth.* keys in config/app.yaml)."
        )
    return {
        "enabled": enabled,
        "username": username,
        "password": password,
        "secret": secret,
        "session_hours": float(config.get("session_hours", 24) or 24),
    }


def credentials_match(username: str, password: str, auth: dict[str, Any]) -> bool:
    return hmac.compare_digest(username, str(auth["username"])) and hmac.compare_digest(
        password,
        str(auth["password"]),
    )


def session_epoch_path(settings: Settings) -> Path:
    return settings.root / "data" / ".session_epoch"


def read_session_epoch(settings: Settings) -> int:
    path = session_epoch_path(settings)
    try:
        return int(path.read_text(encoding="utf-8").strip())
    except (OSError, ValueError):
        return 0


def bump_session_epoch(settings: Settings) -> int:
    path = session_epoch_path(settings)
    path.parent.mkdir(parents=True, exist_ok=True)
    epoch = read_session_epoch(settings) + 1
    path.write_text(str(epoch), encoding="utf-8")
    return epoch


def build_auth_token(username: str, auth: dict[str, Any], epoch: int) -> str:
    expires_at = int(time.time() + float(auth["session_hours"]) * 3600)
    payload = f"{username}|{expires_at}|{epoch}"
    signature = sign_auth_payload(payload, auth)
    return f"{payload}|{signature}"


def auth_session_valid(request: Request, settings: Settings) -> bool:
    auth = auth_settings(settings)
    if not auth["enabled"]:
        return True
    token = request.cookies.get("ai_daily_session", "")
    parts = token.split("|")
    if len(parts) != 4:
        return False
    username, expires_text, epoch_text, signature = parts
    try:
        expires_at = int(expires_text)
        epoch = int(epoch_text)
    except ValueError:
        return False
    if expires_at < int(time.time()):
        return False
    if epoch != read_session_epoch(settings):
        return False
    payload = f"{username}|{expires_at}|{epoch}"
    expected = sign_auth_payload(payload, auth)
    return hmac.compare_digest(username, str(auth["username"])) and hmac.compare_digest(
        signature,
        expected,
    )


def sign_auth_payload(payload: str, auth: dict[str, Any]) -> str:
    return hmac.new(str(auth["secret"]).encode("utf-8"), payload.encode("utf-8"), "sha256").hexdigest()


def create_app(root: Path | None = None) -> FastAPI:
    settings = load_settings(root or Path.cwd())
    app = FastAPI(title="AI-Daily-Update Dashboard")
    app.mount(
        "/static",
        StaticFiles(directory=str(PACKAGE_ROOT / "static")),
        name="static",
    )
    install_auth(app, settings)
    configure_daily_scheduler(settings)

    @app.get("/login", response_class=HTMLResponse)
    def login_page(request: Request):
        if auth_session_valid(request, settings):
            return RedirectResponse("/", status_code=303)
        return templates.TemplateResponse(
            request,
            "login.html",
            {"request": request, "error": ""},
        )

    @app.post("/login")
    def login_action(
        request: Request,
        username: str = Form(default=""),
        password: str = Form(default=""),
    ):
        client_ip = request.client.host if request.client else "unknown"
        if login_rate_limited(app, client_ip):
            return templates.TemplateResponse(
                request,
                "login.html",
                {"request": request, "error": "登录尝试过多，请稍后再试。"},
                status_code=429,
            )
        auth = auth_settings(settings)
        if not credentials_match(username, password, auth):
            record_login_failure(app, client_ip)
            return templates.TemplateResponse(
                request,
                "login.html",
                {"request": request, "error": "用户名或密码不正确。"},
                status_code=401,
            )
        clear_login_failures(app, client_ip)
        response = RedirectResponse("/", status_code=303)
        response.set_cookie(
            "ai_daily_session",
            build_auth_token(auth["username"], auth, read_session_epoch(settings)),
            httponly=True,
            secure=request.url.scheme == "https",
            samesite="lax",
            max_age=int(auth["session_hours"] * 3600),
        )
        return response

    @app.post("/logout")
    def logout_action() -> RedirectResponse:
        bump_session_epoch(settings)
        response = RedirectResponse("/login", status_code=303)
        response.delete_cookie("ai_daily_session")
        return response

    @app.get("/", response_class=HTMLResponse)
    def dashboard(request: Request, page: int = 1) -> HTMLResponse:
        if not auth_session_valid(request, settings):
            return public_cards_response(request, settings, page=page)
        indexed, warnings = ensure_index(settings)
        cards = dashboard_review_cards(settings, limit=12)
        media_cards = dashboard_media_cards(settings, limit=12)
        stats = card_stats(settings)
        candidate_report = latest_candidate_report(settings.markdown_root)
        latest_job = latest_job_snapshot("daily")
        return templates.TemplateResponse(
            request,
            "dashboard.html",
            {
                "request": request,
                "stats": stats,
                "cards": cards,
                "media_cards": media_cards,
                "candidate_report": candidate_report,
                "latest_job": latest_job,
                "indexed": indexed,
                "warnings": warnings,
            },
        )

    @app.get("/public", response_class=HTMLResponse)
    def public_cards_view(request: Request, page: int = 1, topic: str = "", q: str = "") -> HTMLResponse:
        return public_cards_response(request, settings, page=page, topic=topic, q=q)

    @app.get("/public/cards/{card_id}", response_class=HTMLResponse)
    def public_card_detail(request: Request, card_id: str) -> HTMLResponse:
        path = find_card_path_by_id(settings, card_id)
        if not path:
            return templates.TemplateResponse(
                request,
                "public_card_detail.html",
                {"request": request, "card": None, "content_html": "", "is_admin": auth_session_valid(request, settings)},
                status_code=404,
            )
        card = read_card(path)
        item = card_list_item(path, card.metadata, card.content)
        if item["status"] == "rejected":
            return templates.TemplateResponse(
                request,
                "public_card_detail.html",
                {"request": request, "card": None, "content_html": "", "is_admin": auth_session_valid(request, settings)},
                status_code=404,
            )
        return templates.TemplateResponse(
            request,
            "public_card_detail.html",
            {
                "request": request,
                "card": item,
                "content_html": markdown_renderer.render(card.content),
                "is_admin": auth_session_valid(request, settings),
                "foundational_concepts": match_foundational_concepts(
                    card.metadata, card.content, settings.concepts
                ),
            },
        )

    @app.get("/api/v1/meta", response_model=PublicMetaResponse)
    def api_public_meta() -> PublicMetaResponse:
        return PublicMetaResponse(
            project_name=str(settings.app.get("project_name", "AI消息速览")),
            server_time=now_iso(settings.timezone),
            available_tracks=[
                {"id": track_id, "label": label} for track_id, label in TRACK_LABELS.items()
            ],
            available_statuses=[
                {"id": status_id, "label": STATUS_LABELS[status_id]}
                for status_id in ["accepted", "needs-review", "later"]
            ],
        )

    @app.get("/api/v1/cards", response_model=PublicCardListResponse)
    def api_public_cards(
        page: int = 1,
        page_size: int = 20,
        status: str = "",
        track: str = "",
        topic: str = "",
        from_date: str = "",
        to_date: str = "",
    ) -> PublicCardListResponse:
        items = filter_public_cards(
            public_cards(settings),
            status=status,
            track=track,
            topic=topic,
            from_date=from_date,
            to_date=to_date,
        )
        safe_page_size = min(max(page_size, 1), 50)
        paginated = paginate_items(items, page=page, page_size=safe_page_size)
        return PublicCardListResponse(
            items=[public_card_summary(card) for card in paginated["items"]],
            pagination=Pagination(
                page=paginated["page"],
                page_size=paginated["page_size"],
                total=paginated["total"],
                total_pages=paginated["total_pages"],
                has_previous=paginated["has_previous"],
                has_next=paginated["has_next"],
            ),
        )

    @app.get("/api/v1/cards/{card_id}", response_model=PublicCardDetail | ApiError)
    def api_public_card_detail(card_id: str, markdown: bool = False):
        path = find_card_path_by_id(settings, card_id)
        if not path:
            return JSONResponse(
                {"error": {"code": "not_found", "message": "卡片不存在。"}},
                status_code=404,
            )
        card = read_card(path)
        item = card_list_item(path, card.metadata, card.content)
        if item["status"] == "rejected":
            return JSONResponse(
                {"error": {"code": "not_found", "message": "卡片不存在。"}},
                status_code=404,
            )
        sections = [
            {"title": title, "content": content}
            for title, content in extract_sections(card.content).items()
        ]
        summary = public_card_summary(item)
        return PublicCardDetail(
            **summary.model_dump(),
            content_html=markdown_renderer.render(card.content),
            content_markdown=card.content if markdown else "",
            sections=sections,
        )

    @app.get("/cards", response_class=HTMLResponse)
    def cards(
        request: Request,
        status: str = "",
        track: str = "",
        topic: str = "",
        q: str = "",
        page: int = 1,
    ) -> HTMLResponse:
        items = all_cards(settings, status=status, track=track, topic=topic, q=q)
        paginated = paginate_items(items, page=page, page_size=20)
        current_url = cards_page_url(status, track, topic, q, paginated["page"])
        return templates.TemplateResponse(
            request,
            "cards.html",
            {
                "request": request,
                "cards": paginated["items"],
                "status": status,
                "track": track,
                "topic": topic,
                "q": q,
                "topic_options": topic_options(settings.topics),
                "pagination": paginated,
                "current_url": current_url,
                "page_url": lambda target_page: cards_page_url(status, track, topic, q, target_page),
                "clear_url": cards_page_url("", "", "", "", 1),
            },
        )

    @app.get("/sources", response_class=HTMLResponse)
    def sources(request: Request, q: str = "", theme: str = "") -> HTMLResponse:
        entries = source_entries(settings)
        filtered = filter_source_entries(entries, q, theme)
        topic_options = source_topic_options(settings.sources)
        current_url = sources_page_url(q, theme)
        return templates.TemplateResponse(
            request,
            "sources.html",
            {
                "request": request,
                "q": q,
                "theme": theme,
                "theme_options": topic_options,
                "editable_theme_options": topic_options,
                "sources": filtered,
                "total": len(entries),
                "current_url": current_url,
                "source_suggestions": ppt_source_suggestion_preview(settings.root),
                "source_suggestion_items": source_suggestion_items(settings),
            },
        )

    @app.get("/trends", response_class=HTMLResponse)
    def trends(request: Request) -> HTMLResponse:
        return templates.TemplateResponse(
            request,
            "trends.html",
            {
                "request": request,
                "trends": trend_suggestions(settings),
            },
        )

    @app.get("/preferences", response_class=HTMLResponse)
    def preferences(request: Request) -> HTMLResponse:
        return templates.TemplateResponse(
            request,
            "preferences.html",
            {
                "request": request,
                "status": preference_status(settings),
            },
        )

    @app.post("/actions/extract-features")
    def action_extract_features(surface: str = Form(default="all")) -> RedirectResponse:
        extract_preference_features(settings, surface=surface)
        return RedirectResponse("/preferences", status_code=303)

    @app.get("/ppt", response_class=HTMLResponse)
    def ppt(request: Request, deck_id: str = "") -> HTMLResponse:
        today = today_in_timezone(settings.timezone)
        week_start = today - timedelta(days=today.weekday())
        deck = selected_ppt_deck(settings.root, deck_id)
        review_items = ppt_review_items(settings, deck, limit=24)
        return templates.TemplateResponse(
            request,
            "ppt.html",
            {
                "request": request,
                "deck": deck,
                "deck_options": deck_options(settings.root),
                "today": today.isoformat(),
                "week_start": week_start.isoformat(),
                "week_end": today.isoformat(),
                "node_overview": ppt_node_overview(settings, deck),
                "ppt_review_items": review_items,
                "ppt_review_stats": review_stats(ppt_review_items(settings, deck, limit=80)),
                "manuscript": ppt_manuscript_info(settings, deck),
                "plans": latest_ppt_plans(settings.markdown_root, deck, limit=6),
            },
        )

    @app.get("/ppt/template")
    def ppt_template() -> PlainTextResponse:
        response = PlainTextResponse(PPT_MANUSCRIPT_TEMPLATE)
        response.headers["Content-Disposition"] = 'attachment; filename="ppt_manuscript_template.md"'
        return response

    @app.get("/trash", response_class=HTMLResponse)
    def trash(request: Request) -> HTMLResponse:
        return templates.TemplateResponse(
            request,
            "trash.html",
            {
                "request": request,
                "cards": trashed_cards(settings),
            },
        )

    @app.get("/cards/{card_id}", response_class=HTMLResponse)
    def card_detail(request: Request, card_id: str) -> HTMLResponse:
        path = find_card_path_by_id(settings, card_id)
        if not path:
            return templates.TemplateResponse(
                request,
                "card_detail.html",
                {"card": None, "content_html": "", "review_note": None},
                status_code=404,
            )
        card = read_card(path)
        metadata = card.metadata
        status = metadata.get("review_status", "")
        track = metadata.get("track", "")
        return templates.TemplateResponse(
            request,
            "card_detail.html",
            {
                "card": {
                    "id": metadata.get("id", path.stem),
                    "title": metadata.get("title_zh") or metadata.get("title_en") or path.stem,
                    "title_en": metadata.get("title_en", ""),
                    "date": display_event_date(metadata),
                    "event_date": display_event_date(metadata),
                    "info_date": str(metadata.get("date", "")),
                    "collected_date": str(metadata.get("collected_date", metadata.get("date", ""))),
                    "track": track,
                    "track_label": TRACK_LABELS.get(track, track),
                    "status": status,
                    "status_label": STATUS_LABELS.get(status, status),
                    "topics": metadata.get("topics", []),
                    "source_url": metadata.get("source_url", ""),
                    "duplicate_suspect": metadata.get("duplicate_suspect"),
                    "path": path,
                },
                "content_html": markdown_renderer.render(card.content),
                "review_note": latest_card_review_note(
                    settings.markdown_root, str(metadata.get("id", path.stem))
                ),
                "navigation": adjacent_card_navigation(settings, str(metadata.get("id", path.stem))),
                "ppt_usage": card_ppt_usage(settings, str(metadata.get("id", path.stem))),
                "foundational_concepts": match_foundational_concepts(
                    metadata, card.content, settings.concepts
                ),
            },
        )

    @app.get("/briefs", response_class=HTMLResponse)
    def briefs(request: Request) -> HTMLResponse:
        today = today_in_timezone(settings.timezone)
        week_start = today - timedelta(days=today.weekday())
        return templates.TemplateResponse(
            request,
            "briefs.html",
            {
                "request": request,
                "briefs": latest_briefs(settings.markdown_root, limit=12, with_preview=True),
                "today": today.isoformat(),
                "week_start": week_start.isoformat(),
                "week_end": today.isoformat(),
            },
        )

    @app.post("/actions/index")
    def action_index() -> RedirectResponse:
        rebuild_index(settings.markdown_root, settings.sqlite_path)
        return RedirectResponse("/", status_code=303)

    @app.post("/actions/review")
    def action_review(
        request: Request,
        card_id: str = Form(...),
        status: str = Form(...),
        return_to: str = Form(default="/cards"),
        status_actions_vertical: bool = Form(default=False),
    ) -> Any:
        wants_json = request.headers.get("x-requested-with") == "fetch"
        if status not in settings.review_statuses:
            if wants_json:
                return JSONResponse(
                    {"ok": False, "error": "invalid_status"},
                    status_code=400,
                )
            return RedirectResponse(return_to, status_code=303)
        path = find_card_path_by_id(settings, card_id)
        if path:
            card = read_card(path)
            previous_status = str(card.metadata.get("review_status", ""))
            update_metadata(path, {"review_status": status})
            append_feedback_event(
                settings.root,
                settings.timezone,
                "card_review",
                "card",
                card_id,
                status,
                previous_status=previous_status,
                new_status=status,
                metadata={
                    "title": card.metadata.get("title_zh") or card.metadata.get("title_en"),
                    "source_url": card.metadata.get("source_url"),
                    "source_type": card.metadata.get("source_type"),
                    "topics": card.metadata.get("topics", []),
                },
            )
            rebuild_index(settings.markdown_root, settings.sqlite_path)
            if wants_json:
                updated = read_card(path)
                item = card_list_item(path, updated.metadata, updated.content)
                actions_html = templates.get_template("_card_status_actions.html").render(
                    card=item,
                    status_return_to=return_to,
                    status_actions_vertical=status_actions_vertical,
                )
                return JSONResponse(
                    {
                        "ok": True,
                        "card_id": card_id,
                        "status": status,
                        "status_label": STATUS_LABELS.get(status, status),
                        "actions_html": actions_html,
                    }
                )
        elif wants_json:
            return JSONResponse(
                {"ok": False, "error": "card_not_found"},
                status_code=404,
            )
        return RedirectResponse(return_to, status_code=303)

    @app.post("/actions/card-event-date")
    def action_card_event_date(
        card_id: str = Form(...),
        event_date: str = Form(default=""),
        return_to: str = Form(default="/cards"),
    ) -> RedirectResponse:
        normalized = normalize_iso_date(event_date)
        if normalized is None:
            return RedirectResponse(return_to, status_code=303)
        path = find_card_path_by_id(settings, card_id)
        if path:
            card = read_card(path)
            previous_event_date = str(card.metadata.get("event_date", ""))
            update_metadata(path, {"event_date": normalized})
            append_feedback_event(
                settings.root,
                settings.timezone,
                "card_metadata",
                "card",
                card_id,
                "event_date_updated",
                previous_status=previous_event_date,
                new_status=normalized,
                metadata={
                    "title": card.metadata.get("title_zh") or card.metadata.get("title_en"),
                    "source_url": card.metadata.get("source_url"),
                    "info_date": card.metadata.get("date"),
                    "collected_date": card.metadata.get("collected_date"),
                },
            )
            rebuild_index(settings.markdown_root, settings.sqlite_path)
        return RedirectResponse(return_to, status_code=303)

    @app.post("/actions/delete-card")
    def action_delete_card(
        card_id: str = Form(...),
        return_to: str = Form(default="/cards"),
    ) -> RedirectResponse:
        path = find_card_path_by_id(settings, card_id)
        if path:
            card = read_card(path)
            move_card_to_trash(settings, path)
            append_feedback_event(
                settings.root,
                settings.timezone,
                "card_review",
                "card",
                card_id,
                "deleted",
                previous_status=str(card.metadata.get("review_status", "")),
                new_status="deleted",
                metadata={
                    "title": card.metadata.get("title_zh") or card.metadata.get("title_en"),
                    "source_url": card.metadata.get("source_url"),
                    "source_type": card.metadata.get("source_type"),
                    "topics": card.metadata.get("topics", []),
                },
            )
            rebuild_index(settings.markdown_root, settings.sqlite_path)
        return RedirectResponse(return_to, status_code=303)

    @app.post("/actions/source-themes")
    def action_source_themes(
        source_key: str = Form(...),
        primary_topic: str = Form(default="general-ai"),
        secondary_topic: str = Form(default=""),
        return_to: str = Form(default="/sources"),
    ) -> RedirectResponse:
        update_source_topics(settings, source_key, primary_topic, secondary_topic)
        return RedirectResponse(return_to, status_code=303)

    @app.post("/actions/source-enabled")
    def action_source_enabled(
        source_key: str = Form(...),
        enabled: bool = Form(default=True),
        return_to: str = Form(default="/sources"),
    ) -> RedirectResponse:
        source = next(
            (source for source in source_entries(settings) if source["source_key"] == source_key),
            None,
        )
        updated = update_source_enabled(settings, source_key, enabled)
        if updated and source:
            append_feedback_event(
                settings.root,
                settings.timezone,
                "source_subscription",
                "source",
                source_key,
                "enabled" if enabled else "disabled",
                previous_status="enabled" if source.get("enabled") else "disabled",
                new_status="enabled" if enabled else "disabled",
                metadata={
                    "name": source.get("name"),
                    "url": source.get("url"),
                    "kind": source.get("kind"),
                    "primary_topic": source.get("primary_topic"),
                    "secondary_topic": source.get("secondary_topic"),
                },
            )
        return RedirectResponse(return_to, status_code=303)

    @app.post("/actions/source-topic-options")
    def action_source_topic_options(
        topic_id: str = Form(default=""),
        label: str = Form(...),
        return_to: str = Form(default="/sources"),
    ) -> RedirectResponse:
        add_source_topic_option(settings, topic_id, label)
        return RedirectResponse(return_to, status_code=303)

    @app.post("/actions/card-review-note")
    def action_card_review_note(card_id: str = Form(...)) -> RedirectResponse:
        from ai_daily_update.cli import _llm_client

        path = find_card_path_by_id(settings, card_id)
        if path:
            card = read_card(path)
            llm = _llm_client(settings)
            if llm.available:
                content = llm.generate_card_content(
                    build_card_review_note_prompt(card.metadata, card.content)
                )
            else:
                content = deterministic_card_review_note(card.metadata, card.content)
            write_card_review_note(settings.markdown_root, card_id, content or "")
        return RedirectResponse(f"/cards/{card_id}", status_code=303)


    @app.post("/actions/daily")
    def action_daily(
        request: Request,
        dry_run: bool = Form(default=True),
        manual_only: bool = Form(default=False),
    ):
        if has_running_daily_job():
            error = "已有一次生成/预跑任务在进行中，请等待其完成后再试。"
            if request.headers.get("x-requested-with") == "fetch":
                return JSONResponse({"error": error}, status_code=409)
            return RedirectResponse(f"/?{urlencode({'error': error})}", status_code=303)
        job_id = start_daily_job(dry_run=dry_run, manual_only=manual_only, root=settings.root)
        if request.headers.get("x-requested-with") == "fetch":
            return JSONResponse({"job_id": job_id, "job": job_snapshot(job_id)})
        return RedirectResponse(f"/?job={job_id}", status_code=303)

    @app.get("/jobs/latest")
    def job_latest(job_type: str = "") -> JSONResponse:
        return JSONResponse(latest_job_snapshot(job_type or None) or {})

    @app.get("/jobs/{job_id}")
    def job_detail(job_id: str) -> JSONResponse:
        return JSONResponse(job_snapshot(job_id) or {})

    @app.post("/actions/review-summary")
    def action_review_summary() -> RedirectResponse:
        from ai_daily_update.cli import _llm_client
        from ai_daily_update.reports.review_summary import (
            build_review_summary_prompt,
            deterministic_review_summary,
            needs_review_cards,
            write_review_summary,
        )

        cards = needs_review_cards(settings.markdown_root, limit=12)
        if cards:
            llm = _llm_client(settings)
            if llm.available:
                content = llm.generate_card_content(build_review_summary_prompt(cards))
            else:
                content = deterministic_review_summary(cards)
            day = today_in_timezone(settings.timezone)
            write_review_summary(settings.markdown_root, day, content or "")
        return RedirectResponse("/", status_code=303)

    @app.post("/actions/brief")
    def action_brief(
        request: Request,
        preset: str = Form(default="today"),
        from_date: str = Form(default=""),
        to_date: str = Form(default=""),
        topics: str = Form(default=""),
        audience: str = Form(default="academic"),
        date_basis: str = Form(default="collected"),
    ):
        today = today_in_timezone(settings.timezone)
        if preset == "today":
            start = today
            end = today
        elif preset == "this_week":
            start = today - timedelta(days=today.weekday())
            end = today
        else:
            start = fromiso_date_or_default(from_date, today)
            end = fromiso_date_or_default(to_date, start)
        if end < start:
            start, end = end, start
        topic_list = [topic.strip() for topic in topics.split(",") if topic.strip()]
        if request.headers.get("x-requested-with") == "fetch":
            job_id = start_brief_job(
                root=settings.root,
                from_date=start.isoformat(),
                to_date=end.isoformat(),
                topics=topic_list,
                audience=audience,
                date_basis=date_basis,
            )
            return JSONResponse({"job_id": job_id, "job": job_snapshot(job_id)})

        from ai_daily_update.cli import _llm_client
        generate_brief(
            settings.sqlite_path, settings.markdown_root, start.isoformat(), end.isoformat(),
            topic_list or None, audience, date_basis=date_basis, llm_client=_llm_client(settings),
        )
        return RedirectResponse("/briefs", status_code=303)

    @app.post("/actions/delete-brief")
    def action_delete_brief(brief_id: str = Form(default="")) -> RedirectResponse:
        path = brief_path_for_id(settings.markdown_root, brief_id)
        if path is not None:
            path.unlink(missing_ok=True)
        return RedirectResponse("/briefs", status_code=303)

    @app.post("/actions/ppt-plan")
    def action_ppt_plan(
        request: Request,
        deck_id: str = Form(default=""),
        preset: str = Form(default="today"),
        from_date: str = Form(default=""),
        to_date: str = Form(default=""),
        date_basis: str = Form(default="collected"),
        status: str = Form(default="accepted"),
    ):
        deck = selected_ppt_deck(settings.root, deck_id)
        start, end = ppt_plan_date_range(settings, preset, from_date, to_date)
        if request.headers.get("x-requested-with") == "fetch":
            job_id = start_ppt_plan_job(
                root=settings.root,
                deck_id=deck.id,
                from_date=start.isoformat(),
                to_date=end.isoformat(),
                date_basis=date_basis,
                status=status,
            )
            return JSONResponse({"job_id": job_id, "job": job_snapshot(job_id)})
        from ai_daily_update.cli import _llm_client

        llm_client = _llm_client(settings) if section(settings.app, "ppt").get("llm_polish", False) else None

        generate_ppt_plan(
            settings.markdown_root,
            deck.csv_path,
            deck.node_registry_path,
            start.isoformat(),
            end.isoformat(),
            date_basis=date_basis,
            status=status,
            topics_config=settings.topics,
            deck_id=deck.id,
            deck_title=deck.title,
            deck_version=deck.version,
            llm_client=llm_client,
        )
        return RedirectResponse(f"/ppt?deck_id={deck.id}", status_code=303)

    @app.post("/actions/ppt-suggestion-review")
    def action_ppt_suggestion_review(
        deck_id: str = Form(default=""),
        item_id: str = Form(...),
        status: str = Form(...),
        return_to: str = Form(default="/ppt"),
    ) -> RedirectResponse:
        deck = selected_ppt_deck(settings.root, deck_id)
        item = next(
            (item for item in ppt_review_items(settings, deck, limit=200) if item["id"] == item_id),
            None,
        )
        set_ppt_suggestion_status(settings, deck, item_id, status)
        if item:
            append_feedback_event(
                settings.root,
                settings.timezone,
                "ppt_suggestion_review",
                "ppt_suggestion",
                item_id,
                status,
                previous_status=str(item.get("status", "")),
                new_status=status,
                metadata={
                    "title": item.get("title"),
                    "kind": item.get("kind"),
                    "kind_label": item.get("kind_label"),
                    "deck_id": deck.id,
                    "deck_title": deck.title,
                    "deck_version": deck.version,
                    "location": item.get("location"),
                    "report_name": item.get("report_name"),
                    "card_ids": item.get("card_ids", []),
                },
            )
        return RedirectResponse(return_to, status_code=303)

    @app.post("/actions/ppt-manuscript-import")
    def action_ppt_manuscript_import(deck_id: str = Form(default="")) -> RedirectResponse:
        deck = selected_ppt_deck(settings.root, deck_id)
        import_ppt_suggestions_to_manuscript(settings, deck)
        return RedirectResponse(f"/ppt?deck_id={deck.id}#ppt-manuscript", status_code=303)

    @app.post("/actions/ppt-manuscript-save")
    def action_ppt_manuscript_save(
        deck_id: str = Form(default=""),
        content: str = Form(...),
    ) -> RedirectResponse:
        deck = selected_ppt_deck(settings.root, deck_id)
        save_ppt_manuscript(settings, deck, content)
        return RedirectResponse(f"/ppt?deck_id={deck.id}#ppt-manuscript", status_code=303)

    @app.post("/actions/ppt-manuscript-sections-save")
    def action_ppt_manuscript_sections_save(
        deck_id: str = Form(default=""),
        chunk_content: list[str] = Form(...),
    ) -> RedirectResponse:
        deck = selected_ppt_deck(settings.root, deck_id)
        save_ppt_manuscript(settings, deck, "\n".join(chunk_content))
        return RedirectResponse(f"/ppt?deck_id={deck.id}#ppt-manuscript", status_code=303)

    @app.post("/actions/ppt-deck-upload")
    async def action_ppt_deck_upload(
        deck_id: str = Form(...),
        title: str = Form(...),
        version: str = Form(default=""),
        duration: str = Form(default=""),
        manuscript_text: str = Form(default=""),
        manuscript_file: UploadFile | None = File(default=None),
    ) -> RedirectResponse:
        content = manuscript_text
        if manuscript_file and manuscript_file.filename:
            raw = await manuscript_file.read()
            content = raw.decode("utf-8")
        deck = create_ppt_deck(
            settings,
            deck_id=deck_id,
            title=title,
            version=version,
            duration=duration,
            manuscript_text=content,
        )
        return RedirectResponse(f"/ppt?deck_id={deck.id}", status_code=303)

    @app.post("/actions/source-suggestion-review")
    def action_source_suggestion_review(
        request: Request,
        suggestion_id: str = Form(...),
        status: str = Form(...),
        return_to: str = Form(default="/ppt"),
    ) -> Any:
        wants_json = request.headers.get("x-requested-with") == "fetch"
        item = next(
            (item for item in source_suggestion_items(settings) if item["id"] == suggestion_id),
            None,
        )
        set_source_suggestion_status(settings, suggestion_id, status)
        if item:
            append_feedback_event(
                settings.root,
                settings.timezone,
                "source_proposal_review",
                "source_proposal",
                suggestion_id,
                status,
                previous_status=str(item.get("status", "")),
                new_status=status,
                metadata={
                    "name": item.get("name"),
                    "url": item.get("url"),
                    "primary_topic": item.get("primary_topic"),
                    "secondary_topic": item.get("secondary_topic"),
                    "priority": item.get("priority"),
                    "reason": item.get("reason"),
                    "proposal_origin": item.get("proposal_origin", "manual"),
                },
            )
        if wants_json:
            return source_suggestion_json_response(
                templates,
                settings,
                suggestion_id,
                return_to,
            )
        return RedirectResponse(return_to, status_code=303)

    @app.post("/actions/source-suggestion-add")
    def action_source_suggestion_add(
        request: Request,
        suggestion_id: str = Form(...),
        return_to: str = Form(default="/ppt"),
    ) -> Any:
        wants_json = request.headers.get("x-requested-with") == "fetch"
        item = next(
            (item for item in source_suggestion_items(settings) if item["id"] == suggestion_id),
            None,
        )
        add_source_suggestion_to_config(settings, suggestion_id)
        if item:
            append_feedback_event(
                settings.root,
                settings.timezone,
                "source_proposal_review",
                "source_proposal",
                suggestion_id,
                "added",
                previous_status=str(item.get("status", "")),
                new_status="added",
                metadata={
                    "name": item.get("name"),
                    "url": item.get("url"),
                    "primary_topic": item.get("primary_topic"),
                    "secondary_topic": item.get("secondary_topic"),
                    "priority": item.get("priority"),
                    "reason": item.get("reason"),
                    "proposal_origin": item.get("proposal_origin", "manual"),
                },
            )
        if wants_json:
            return source_suggestion_json_response(
                templates,
                settings,
                suggestion_id,
                return_to,
            )
        return RedirectResponse(return_to, status_code=303)

    return app


def ensure_index(settings: Settings) -> tuple[int, list[str]]:
    return rebuild_index(settings.markdown_root, settings.sqlite_path)


def card_stats(settings: Settings) -> dict[str, int]:
    stats = {
        "total": 0,
        "accepted": 0,
        "needs-review": 0,
        "later": 0,
        "rejected": 0,
        "academic": 0,
        "industry": 0,
    }
    for path in iter_cards(settings.markdown_root):
        card = read_card(path)
        stats["total"] += 1
        status = card.metadata.get("review_status", "needs-review")
        track = card.metadata.get("track", "")
        if status in stats:
            stats[status] += 1
        if track in stats:
            stats[track] += 1
    return stats


def recent_cards(settings: Settings, limit: int = 12) -> list[dict[str, Any]]:
    cards = all_cards(settings)
    return cards[:limit]


def dashboard_review_cards(settings: Settings, limit: int = 12) -> list[dict[str, Any]]:
    cards = [
        card
        for card in all_cards(settings)
        if card["status"] in {"needs-review", "later"}
        and not is_media_source_card(card)
    ]
    return sort_dashboard_cards(cards)[:limit]


def dashboard_media_cards(settings: Settings, limit: int = 12) -> list[dict[str, Any]]:
    cards = [
        card
        for card in all_cards(settings)
        if card["status"] in {"needs-review", "later"}
        and is_media_source_card(card)
    ]
    return sort_dashboard_cards(cards)[:limit]


def sort_dashboard_cards(cards: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(
        cards,
        key=lambda item: (
            item.get("collected_date") or item.get("created_at", "")[:10] or item.get("date", ""),
            item.get("date", ""),
            item.get("id", ""),
        ),
        reverse=True,
    )


def all_cards(
    settings: Settings, status: str = "", track: str = "", topic: str = "", q: str = ""
) -> list[dict[str, Any]]:
    cards: list[dict[str, Any]] = []
    normalized_q = q.strip().lower()
    for path in iter_cards(settings.markdown_root):
        card = read_card(path)
        metadata = card.metadata
        if status and metadata.get("review_status") != status:
            continue
        if track and metadata.get("track") != track:
            continue
        item = card_list_item(path, card.metadata, card.content)
        if topic and topic not in set(item.get("topics", []) or []):
            continue
        if normalized_q and normalized_q not in item.get("search_text", ""):
            continue
        cards.append(item)
    return sorted(
        cards,
        key=lambda item: (
            item.get("collected_date") or "",
            item.get("info_date") or "",
            item.get("id") or "",
        ),
        reverse=True,
    )


def paginate_items(items: list[Any], page: int = 1, page_size: int = 20) -> dict[str, Any]:
    total = len(items)
    total_pages = max(1, (total + page_size - 1) // page_size)
    current_page = min(max(page, 1), total_pages)
    start = (current_page - 1) * page_size
    end = min(start + page_size, total)
    return {
        "items": items[start:end],
        "page": current_page,
        "page_size": page_size,
        "total": total,
        "total_pages": total_pages,
        "start": start + 1 if total else 0,
        "end": end,
        "has_previous": current_page > 1,
        "has_next": current_page < total_pages,
        "previous_page": current_page - 1 if current_page > 1 else 1,
        "next_page": current_page + 1 if current_page < total_pages else total_pages,
    }


def cards_page_url(status: str, track: str, topic: str, q: str, page: int) -> str:
    params = {}
    if status:
        params["status"] = status
    if track:
        params["track"] = track
    if topic:
        params["topic"] = topic
    if q:
        params["q"] = q
    if page > 1:
        params["page"] = str(page)
    query = urlencode(params)
    return f"/cards?{query}" if query else "/cards"


def public_page_url(topic: str, q: str, page: int) -> str:
    params = {}
    if topic:
        params["topic"] = topic
    if q:
        params["q"] = q
    if page > 1:
        params["page"] = str(page)
    query = urlencode(params)
    return f"/public?{query}" if query else "/public"


def public_cards_response(
    request: Request, settings: Settings, page: int = 1, topic: str = "", q: str = ""
) -> HTMLResponse:
    items = filter_public_cards(public_cards(settings), topic=topic, q=q)
    paginated = paginate_items(items, page=page, page_size=20)
    return templates.TemplateResponse(
        request,
        "public_cards.html",
        {
            "request": request,
            "cards": paginated["items"],
            "pagination": paginated,
            "page_url": lambda target_page: public_page_url(topic, q, target_page),
            "topic": topic,
            "q": q,
            "topic_options": topic_options(settings.topics),
            "clear_url": public_page_url("", "", 1),
            "is_admin": auth_session_valid(request, settings),
        },
    )


def public_cards(settings: Settings) -> list[dict[str, Any]]:
    visible_statuses = {"accepted", "needs-review", "later"}
    cards = [card for card in all_cards(settings) if card["status"] in visible_statuses]
    return sorted(
        cards,
        key=lambda item: (
            item.get("event_date") or item.get("info_date") or "",
            item.get("info_date") or "",
            item.get("id") or "",
        ),
        reverse=True,
    )


def filter_public_cards(
    cards: list[dict[str, Any]],
    *,
    status: str = "",
    track: str = "",
    topic: str = "",
    q: str = "",
    from_date: str = "",
    to_date: str = "",
) -> list[dict[str, Any]]:
    visible_statuses = {"accepted", "needs-review", "later"}
    if status and status not in visible_statuses:
        return []
    start = normalize_iso_date(from_date) if from_date else ""
    end = normalize_iso_date(to_date) if to_date else ""
    if from_date and start is None:
        start = ""
    if to_date and end is None:
        end = ""
    if start and end and end < start:
        start, end = end, start
    normalized_q = q.strip().lower()
    filtered = cards
    if status:
        filtered = [card for card in filtered if card.get("status") == status]
    if track:
        filtered = [card for card in filtered if card.get("track") == track]
    if topic:
        filtered = [card for card in filtered if topic in set(card.get("topics", []) or [])]
    if normalized_q:
        filtered = [card for card in filtered if normalized_q in card.get("search_text", "")]
    if start:
        filtered = [card for card in filtered if str(card.get("event_date", "")) >= start]
    if end:
        filtered = [card for card in filtered if str(card.get("event_date", "")) <= end]
    return filtered


def topic_options(topics_config: dict[str, Any]) -> list[dict[str, str]]:
    topics = topics_config.get("topics", {})
    ranked = sorted(
        topics.items(),
        key=lambda item: (-int(item[1].get("priority", 0) or 0), item[1].get("name_zh") or item[0]),
    )
    return [
        {"id": topic_id, "label": topic.get("name_zh") or topic.get("name_en") or topic_id}
        for topic_id, topic in ranked
    ]


def display_event_date(metadata: dict[str, Any]) -> str:
    return str(metadata.get("event_date") or metadata.get("date") or "")


def normalize_iso_date(value: str) -> str | None:
    text = value.strip()
    if not text:
        return ""
    try:
        return datetime.strptime(text, "%Y-%m-%d").date().isoformat()
    except ValueError:
        return None


def card_list_item(path: Path, metadata: dict[str, Any], content: str) -> dict[str, Any]:
    info_date = str(metadata.get("date", ""))
    event_date = display_event_date(metadata)
    conclusion = extract_one_sentence_conclusion(content)
    event_overview = extract_event_overview(content) or metadata.get("title_en", "")
    search_text = " ".join(
        filter(
            None,
            [
                metadata.get("title_zh", ""),
                metadata.get("title_en", ""),
                conclusion or "",
                event_overview or "",
                " ".join(metadata.get("topics", []) or []),
            ],
        )
    ).lower()
    return {
        "path": path,
        "id": metadata.get("id", path.stem),
        "title": metadata.get("title_zh") or metadata.get("title_en") or path.stem,
        "title_en": metadata.get("title_en", ""),
        "conclusion": conclusion,
        "event_overview": event_overview,
        "search_text": search_text,
        "track": metadata.get("track", ""),
        "track_label": TRACK_LABELS.get(metadata.get("track", ""), metadata.get("track", "")),
        "source_type": metadata.get("source_type", ""),
        "status": metadata.get("review_status", ""),
        "status_label": STATUS_LABELS.get(
            metadata.get("review_status", ""), metadata.get("review_status", "")
        ),
        "date": event_date,
        "event_date": event_date,
        "info_date": info_date,
        "collected_date": str(metadata.get("collected_date", metadata.get("date", ""))),
        "deleted_at": str(metadata.get("deleted_at", "")),
        "source_url": metadata.get("source_url", ""),
        "source_label": source_label(metadata.get("source_url", "")),
        "detail_url": f"/cards/{metadata.get('id', path.stem)}",
        "public_detail_url": f"/public/cards/{metadata.get('id', path.stem)}",
        "topics": metadata.get("topics", []),
        "score_fields": score_fields(metadata),
        "duplicate_suspect": metadata.get("duplicate_suspect"),
    }


def is_media_source_card(card: dict[str, Any]) -> bool:
    if card.get("source_type") in {"chinese-media", "chinese-media-digest-item"}:
        return True
    label = str(card.get("source_label", ""))
    return label in {"机器之心", "量子位", "新智元", "腾讯研究院（搜狐同步）"}


def trashed_cards(settings: Settings) -> list[dict[str, Any]]:
    trash_root = settings.markdown_root / "trash"
    if not trash_root.exists():
        return []
    cards = []
    for path in trash_root.rglob("*.md"):
        card = read_card(path)
        cards.append(card_list_item(path, card.metadata, card.content))
    return sorted(
        cards,
        key=lambda item: (item["deleted_at"], item["date"], item["id"]),
        reverse=True,
    )


def adjacent_card_navigation(settings: Settings, card_id: str) -> dict[str, Any]:
    cards = all_cards(settings)
    ids = [str(card["id"]) for card in cards]
    if card_id not in ids:
        return {"previous": None, "next": None}
    index = ids.index(card_id)
    previous_card = cards[index - 1] if index > 0 else None
    next_card = cards[index + 1] if index + 1 < len(cards) else None
    return {
        "previous": previous_card,
        "next": next_card,
    }


def find_card_path_by_id(settings: Settings, card_id: str) -> Path | None:
    for path in iter_cards(settings.markdown_root):
        card = read_card(path)
        if card.metadata.get("id") == card_id:
            return path
    return None


def move_card_to_trash(settings: Settings, path: Path) -> Path:
    update_metadata(path, {"deleted_at": now_iso(settings.timezone)})
    cards_root = settings.markdown_root / "cards"
    trash_root = settings.markdown_root / "trash"
    try:
        relative = path.relative_to(cards_root)
    except ValueError:
        relative = Path(path.name)
    target = trash_root / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists():
        target = target.with_name(f"{target.stem}-deleted{target.suffix}")
    shutil.move(str(path), str(target))
    return target


def score_fields(metadata: dict[str, Any]) -> str:
    fields = ["importance", "novelty", "confidence", "book_potential", "ppt_potential"]
    pairs = [f"{field}:{metadata[field]}" for field in fields if field in metadata]
    return " ".join(pairs)


def extract_event_overview(content: str, max_chars: int = 180) -> str:
    return extract_card_section(content, "事件概述", max_chars=max_chars)


def extract_one_sentence_conclusion(content: str, max_chars: int = 180) -> str:
    return extract_card_section(content, "一句话结论", max_chars=max_chars)


def extract_card_section(content: str, section_prefix: str, max_chars: int = 180) -> str:
    lines = content.splitlines()
    in_section = False
    collected: list[str] = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("## "):
            if in_section:
                break
            heading = stripped.lstrip("#").strip()
            if heading.startswith(section_prefix):
                in_section = True
            continue
        if stripped.startswith("**") and stripped.endswith("**"):
            heading = stripped.strip("*").strip()
            if in_section:
                break
            if heading.startswith(section_prefix):
                in_section = True
            continue
        if not in_section:
            continue
        if not stripped:
            if collected:
                break
            continue
        collected.append(stripped.lstrip("- ").strip())
    overview = " ".join(collected).strip()
    if len(overview) <= max_chars:
        return overview
    return overview[: max_chars - 1].rstrip() + "…"


def source_label(source_url: str) -> str:
    parsed = urlparse(source_url)
    host = parsed.netloc.lower().removeprefix("www.")
    path = parsed.path.lower()
    query = parsed.query
    if host == "arxiv.org":
        return "arXiv 论文"
    if host.endswith("openai.com"):
        return "OpenAI 博客" if "/news" in path else "OpenAI"
    if host.endswith("anthropic.com"):
        return "Anthropic 博客" if "/news" in path else "Anthropic"
    if host.endswith("deepseek.com"):
        return "DeepSeek 文档" if "docs" in host or "/docs" in path else "DeepSeek"
    if host.endswith("jiqizhixin.com"):
        return "机器之心"
    if host.endswith("qbitai.com"):
        return "量子位"
    if host.endswith("aiera.com.cn"):
        return "新智元"
    if host.endswith("mp.weixin.qq.com"):
        if "MzI3MTA0MTk1MA" in query:
            return "新智元"
        return "微信公众号"
    if host.endswith("sohu.com") and "455313" in path:
        return "腾讯研究院（搜狐同步）"
    if host.endswith("sohu.com") and "473283" in path:
        return "新智元（搜狐同步）"
    if host.endswith("huggingface.co"):
        return "Hugging Face 博客" if "/blog" in path else "Hugging Face"
    if host.endswith("microsoft.com"):
        return "Microsoft AI 博客"
    if host.endswith("nvidia.com"):
        return "NVIDIA 博客"
    if host.endswith("cohere.com"):
        return "Cohere 博客"
    if host.endswith("together.ai"):
        return "Together AI 博客"
    if host.endswith("langchain.com"):
        return "LangChain 博客"
    if host.endswith("llamaindex.ai"):
        return "LlamaIndex 博客"
    if host.endswith("cursor.com"):
        return "Cursor 博客"
    if host.endswith("windsurf.com"):
        return "Windsurf 博客"
    if not host:
        return "未知来源"
    return host


def latest_candidate_report(markdown_root: Path) -> dict[str, str] | None:
    inbox = markdown_root / "inbox"
    reports = sorted(inbox.glob("*-candidates.md"), reverse=True) if inbox.exists() else []
    if not reports:
        return None
    path = reports[0]
    text = path.read_text(encoding="utf-8")
    preview = "\n".join(text.splitlines()[:80])
    return {
        "path": str(path),
        "name": path.name,
        "preview": preview,
        "preview_html": markdown_renderer.render(preview),
    }


def latest_review_summary(markdown_root: Path) -> dict[str, str] | None:
    inbox = markdown_root / "inbox"
    reports = sorted(inbox.glob("*-review-summary.md"), reverse=True) if inbox.exists() else []
    if not reports:
        return None
    path = reports[0]
    text = path.read_text(encoding="utf-8")
    preview = "\n".join(text.splitlines()[:120])
    overview = extract_review_overview(text)
    return {
        "path": str(path),
        "name": path.name,
        "preview_html": markdown_renderer.render(preview),
        "overview_html": markdown_renderer.render(overview),
    }


def extract_review_overview(text: str) -> str:
    lines = text.splitlines()
    overview: list[str] = []
    started = False
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("## 优先处理") or stripped.startswith("## 逐条") or stripped.startswith("|"):
            break
        if stripped.startswith("# "):
            continue
        if stripped.startswith("## 总体判断"):
            started = True
            overview.append("## 总体判断")
            continue
        if not started and stripped:
            continue
        if started:
            overview.append(line)
    return "\n".join(overview).strip() or "## 总体判断\n\n暂无审核概览。"


def latest_card_review_note(markdown_root: Path, card_id: str) -> dict[str, str] | None:
    path = markdown_root / "inbox" / "review-notes" / f"{card_id}.md"
    if not path.exists():
        return None
    text = path.read_text(encoding="utf-8")
    return {"path": str(path), "preview_html": markdown_renderer.render(text)}


def write_card_review_note(markdown_root: Path, card_id: str, content: str) -> Path:
    output_dir = markdown_root / "inbox" / "review-notes"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"{card_id}.md"
    output_path.write_text(content.strip() + "\n", encoding="utf-8")
    return output_path


def build_card_review_note_prompt(metadata: dict[str, Any], content: str) -> str:
    return f"""
你是 AI-Daily-Update 的中文审核助手。请为单张 needs-review 卡片生成极简审核建议。

要求：
- 输出 Markdown。
- 不要寒暄。
- 用尽量短的文字提供足够信息。
- 给出建议动作：建议接受 / 建议稍后 / 建议拒绝。
- 说明：入库价值、事实风险、是否需要打开来源核对。

输出结构：

# 单卡审核建议

## 建议动作

## 为什么

## 风险

## 审核时看什么

metadata:
{metadata}

content:
{content[:3000]}
"""


def deterministic_card_review_note(metadata: dict[str, Any], content: str) -> str:
    title = metadata.get("title_zh") or metadata.get("title_en") or metadata.get("id")
    if "待补充" in content or "无法直接访问" in content:
        suggestion = "建议稍后"
        reason = "正文仍有占位或来源材料不足。"
    else:
        suggestion = "建议接受"
        reason = "正文已包含结构化摘要和来源，可进入人工核对。"
    return f"""# 单卡审核建议

## 建议动作

{suggestion}

## 为什么

{title}：{reason}

## 风险

需要打开来源核对事实与时间。

## 审核时看什么

- source_url 是否可访问
- 事实是否来自原始材料
- 局限与不确定性是否充分
"""


def fromiso_date_or_default(value: str, fallback: Any) -> Any:
    from datetime import date

    try:
        return date.fromisoformat(value)
    except ValueError:
        return fallback


def latest_briefs(
    markdown_root: Path, limit: int = 8, with_preview: bool = False
) -> list[dict[str, str]]:
    briefs_root = markdown_root / "briefs"
    if not briefs_root.exists():
        return []
    paths = sorted(
        briefs_root.rglob("*.md"),
        key=lambda path: path.stat().st_mtime_ns,
        reverse=True,
    )[:limit]
    briefs = []
    for path in paths:
        relative_path = path.relative_to(briefs_root).as_posix()
        item: dict[str, str] = {"id": brief_id_for_relative_path(relative_path)}
        if with_preview:
            text = path.read_text(encoding="utf-8")
            preview = "\n".join(text.splitlines()[:120])
            item.update(brief_list_summary(text))
            item["preview_html"] = markdown_renderer.render(preview)
        briefs.append(item)
    return briefs


def brief_list_summary(text: str) -> dict[str, str]:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    title = next((line.lstrip("#").strip() for line in lines if line.startswith("#")), "简报内容")
    excerpt = next(
        (
            line.lstrip("- ").strip()
            for line in lines
            if not line.startswith("#") and not line.startswith("-") and len(line) > 8
        ),
        "点击查看本期简报内容。",
    )
    return {"title": title, "excerpt": excerpt[:96]}


def brief_id_for_relative_path(relative_path: str) -> str:
    return hashlib.sha256(relative_path.encode("utf-8")).hexdigest()


def brief_path_for_id(markdown_root: Path, brief_id: str) -> Path | None:
    """Resolve an opaque brief ID without accepting a client-supplied path."""
    briefs_root = markdown_root / "briefs"
    if not brief_id or not briefs_root.exists():
        return None
    for path in briefs_root.rglob("*.md"):
        relative_path = path.relative_to(briefs_root).as_posix()
        if hmac.compare_digest(brief_id, brief_id_for_relative_path(relative_path)):
            return path
    return None


def ppt_node_overview(settings: Settings, deck: PPTDeck) -> dict[str, Any]:
    ppt_csv = deck.csv_path
    node_registry = deck.node_registry_path
    if not ppt_csv.exists() or not node_registry.exists():
        return {
            "available": False,
            "matched": 0,
            "total": 0,
            "items": [],
            "message": "未找到 PPT 结构文件或节点注册表。",
        }
    try:
        matches = load_ppt_node_matches(ppt_csv, node_registry)
    except Exception as exc:
        return {
            "available": False,
            "matched": 0,
            "total": 0,
            "items": [],
            "message": f"PPT 节点读取失败：{exc}",
        }
    items = []
    for match in matches:
        current = match.current
        items.append(
            {
                "node_id": match.registered.node_id,
                "role": match.registered.role,
                "intent": match.registered.intent,
                "location": current.title_path if current else match.registered.title_path,
                "pages": current.pages if current else [],
                "matched": current is not None,
                "score": match.score,
            }
        )
    return {
        "available": True,
        "matched": len([item for item in items if item["matched"]]),
        "total": len(items),
        "items": items,
        "message": "",
    }


def latest_ppt_plans(markdown_root: Path, deck: PPTDeck, limit: int = 6) -> list[dict[str, str]]:
    inbox = markdown_root / "inbox"
    if not inbox.exists():
        return []
    paths = latest_ppt_plan_paths(markdown_root, deck, limit=limit)
    plans = []
    for path in paths:
        text = path.read_text(encoding="utf-8")
        preview = "\n".join(text.splitlines()[:180])
        plans.append(
            {
                "name": path.name,
                "path": str(path),
                "preview_html": markdown_renderer.render(preview),
            }
        )
    return plans


def ppt_review_items(settings: Settings, deck: PPTDeck, limit: int = 24) -> list[dict[str, Any]]:
    link_state = read_ppt_card_links(settings)
    old_states = read_review_state(ppt_review_state_path(settings))
    items = []
    json_paths = latest_ppt_plan_json_paths(settings.markdown_root, deck, limit=1)
    if json_paths:
        for item in parse_ppt_plan_json_items(settings, deck, json_paths[0]):
            state = link_state.get("suggestions", {}).get(item["id"], old_states.get(item["id"], {}))
            item["status"] = state.get("status", "pending")
            item["status_label"] = ppt_review_status_label(item["status"])
            item["updated_at"] = state.get("updated_at", "")
            items.append(item)
        items.sort(key=ppt_review_item_sort_key)
        return items[:limit]
    md_paths = latest_ppt_plan_paths(settings.markdown_root, deck, limit=1)
    if md_paths:
        for item in parse_ppt_plan_review_items(md_paths[0]):
            state = old_states.get(item["id"], {})
            item["status"] = state.get("status", "pending")
            item["status_label"] = ppt_review_status_label(item["status"])
            item["updated_at"] = state.get("updated_at", "")
            items.append(item)
    items.sort(key=ppt_review_item_sort_key)
    return items[:limit]


def ppt_review_item_sort_key(item: dict[str, Any]) -> tuple[int, str]:
    pages = [safe_int_value(page, default=9999) for page in item.get("pages", [])]
    first_page = min(pages) if pages else 9999
    return first_page, str(item.get("display_title") or item.get("title") or "")


def safe_int_value(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError, OverflowError):
        return default


def latest_ppt_plan_paths(markdown_root: Path, deck: PPTDeck, limit: int = 6) -> list[Path]:
    inbox = markdown_root / "inbox"
    if not inbox.exists():
        return []
    deck_paths = sorted(
        inbox.glob(f"*_{deck.id}_ppt-update-plan*.md"),
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )
    fallback_paths = (
        sorted(inbox.glob("*_ppt-update-plan*.md"), key=lambda path: path.stat().st_mtime, reverse=True)
        if deck.id == "ai-frontier-60min"
        else []
    )
    paths = deck_paths or fallback_paths
    return paths[:limit]


def latest_ppt_plan_json_paths(markdown_root: Path, deck: PPTDeck, limit: int = 6) -> list[Path]:
    inbox = markdown_root / "inbox"
    if not inbox.exists():
        return []
    deck_paths = sorted(
        inbox.glob(f"*_{deck.id}_ppt-update-plan*.json"),
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )
    fallback_paths = (
        sorted(inbox.glob("*_ppt-update-plan*.json"), key=lambda path: path.stat().st_mtime, reverse=True)
        if deck.id == "ai-frontier-60min"
        else []
    )
    paths = deck_paths or fallback_paths
    return paths[:limit]


def parse_ppt_plan_json_items(settings: Settings, deck: PPTDeck, path: Path) -> list[dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("deck_id") and payload.get("deck_id") != deck.id:
        return []
    card_lookup = cards_by_id(settings)
    generated_at = format_file_mtime(path, settings.timezone)
    items = []
    for raw in payload.get("items", []):
        cards = [
            enrich_ppt_evidence_card(card_lookup, card)
            for card in raw.get("cards", [])
        ]
        item_id = str(raw.get("suggestion_id", ""))
        recommendation = str(raw.get("recommendation") or raw.get("oral_text") or "")
        title = str(raw.get("title") or raw.get("node_id") or item_id)
        location = str(raw.get("location", ""))
        display_title = ppt_suggestion_display_title(raw, title, location)
        edits = normalize_ppt_edits(raw.get("edits") or fallback_ppt_edits(raw, deck), raw)
        items.append(
            {
                "id": item_id,
                "report_name": payload.get("report_name", path.name),
                "report_path": payload.get("markdown_path", str(path.with_suffix(".md"))),
                "json_path": str(path),
                "generated_at": generated_at,
                "title": title,
                "display_title": display_title,
                "kind": raw.get("kind", ""),
                "kind_label": raw.get("kind_label", raw.get("kind", "")),
                "location": location,
                "subtitle": ppt_suggestion_subtitle(raw, title, location),
                "pages": raw.get("pages", []),
                "recommendation": recommendation,
                "oral_text": raw.get("oral_text", ""),
                "edits": edits,
                "trend_keywords": raw.get("trend_keywords", []),
                "target_locations": raw.get("target_locations", []),
                "card_ids": raw.get("card_ids", []),
                "cards": cards,
                "evidence_summary": evidence_summary(cards),
                "excerpt": recommendation,
                "excerpt_html": markdown_renderer.render(recommendation),
                "status": "pending",
                "status_label": "待处理",
                "updated_at": "",
            }
        )
    return items


def format_file_mtime(path: Path, timezone_name: str) -> str:
    try:
        tz = ZoneInfo(timezone_name)
    except Exception:
        tz = None
    try:
        timestamp = path.stat().st_mtime
    except OSError:
        return ""
    value = datetime.fromtimestamp(timestamp, tz=tz)
    return value.strftime("%Y-%m-%d %H:%M")


def normalize_ppt_edits(edits: list[dict[str, Any]], raw: dict[str, Any]) -> list[dict[str, Any]]:
    normalized = []
    for edit in edits:
        item = dict(edit)
        if not item.get("instruction"):
            item["instruction"] = fallback_ppt_instruction(
                raw,
                item.get("page"),
                str(item.get("current_text") or ""),
            )
        if item.get("type_label") == "补充小节":
            item["type_label"] = "建议新增一段"
        if should_replace_weak_ppt_suggestion(item, raw):
            item["suggested_text"] = fallback_suggested_ppt_text(
                raw,
                str(raw.get("recommendation") or raw.get("oral_text") or item.get("suggested_text") or ""),
            )
        normalized.append(item)
    return normalized


def should_replace_weak_ppt_suggestion(edit: dict[str, Any], raw: dict[str, Any]) -> bool:
    if raw.get("kind") != "section_trend" or edit.get("current_text"):
        return False
    text = str(edit.get("suggested_text") or "")
    weak_patterns = ["可围绕", "近期可以增加", "避免只堆新增材料"]
    return any(pattern in text for pattern in weak_patterns)


def fallback_ppt_edits(raw: dict[str, Any], deck: PPTDeck) -> list[dict[str, Any]]:
    recommendation = str(raw.get("recommendation") or raw.get("oral_text") or "").strip()
    if not recommendation:
        return []
    pages = [page for page in raw.get("pages", []) if page]
    page = pages[0] if pages else None
    current_text = fallback_current_text_for_ppt_item(raw, deck)
    suggested_text = fallback_suggested_ppt_text(raw, recommendation)
    if current_text and raw.get("oral_text"):
        suggested_text = f"{current_text}。{raw['oral_text']}"
    card_count = len(raw.get("card_ids", []))
    rationale = (
        f"根据 {card_count} 张已接受卡片补充近期变化，适合作为该小节的口头更新。"
        if card_count
        else "根据当前建议报告补充近期变化，适合作为该小节的口头更新。"
    )
    return [
        {
            "type": "replace" if current_text else "append",
            "type_label": "建议替换原文" if current_text else "建议新增一段",
            "instruction": fallback_ppt_instruction(raw, page, current_text),
            "page": page,
            "pages": pages,
            "current_text": compact_inline_text(current_text, max_chars=92),
            "suggested_text": compact_inline_text(suggested_text, max_chars=260),
            "rationale": rationale,
            "card_ids": raw.get("card_ids", []),
        }
    ]


def fallback_ppt_instruction(raw: dict[str, Any], page: Any, current_text: str) -> str:
    location = str(raw.get("location") or raw.get("level2") or "")
    section_name = clean_ppt_heading(location.split(" / ")[-1]) if location else "当前小节"
    target = f"第 {page} 页" if page else "对应页面"
    if current_text:
        return f"检查{target}“{section_name}”的现有表述，保留原结构，把下方文字作为替换后的口播稿。"
    return f"在{target}“{section_name}”小节末尾新增一个“近期变化”口播点，不改小节标题。"


def fallback_suggested_ppt_text(raw: dict[str, Any], recommendation: str) -> str:
    if raw.get("kind") != "section_trend":
        return recommendation
    location = str(raw.get("location") or raw.get("level2") or "本小节")
    section_name = clean_ppt_heading(location.split(" / ")[-1])
    trends = raw.get("trend_keywords", [])
    labels = [str(item.get("label", "")) for item in trends[:3] if item.get("label")]
    focus = "、".join(labels)
    card_points = fallback_card_points(raw.get("cards", []))
    landing = fallback_section_landing_text(section_name, focus)
    if len(card_points) >= 2:
        return (
            f"这里建议补充两个近期案例：第一，{card_points[0]}，用作{section_name}从概念走向具体场景的案例；"
            f"第二，{card_points[1]}，用作{section_name}安全性和行为一致性讨论的案例。"
            f"{landing}"
        )
    if card_points:
        return (
            f"这里建议补充一个近期案例：{card_points[0]}，用作{section_name}从概念走向具体场景的案例。"
            f"{landing}"
        )
    if focus:
        return f"这里建议补一个近期案例或图示。{landing}"
    return f"这里建议补一个近期案例或图示，作为{section_name}的口播更新点。"


def fallback_card_points(cards: list[dict[str, Any]], limit: int = 2) -> list[str]:
    points = []
    seen = set()
    for card in cards:
        point = compact_inline_text(
            str(card.get("title") or card.get("conclusion") or card.get("overview") or ""),
            max_chars=34,
        )
        if not point or point in seen:
            continue
        seen.add(point)
        points.append(point)
        if len(points) >= limit:
            break
    return points


def fallback_section_landing_text(section_name: str, focus: str) -> str:
    clean_focus = remove_repeated_focus(section_name, focus)
    if clean_focus:
        return f"讲稿落点可以收束为：{section_name}正在从概念介绍转向{clean_focus}等更具体的案例和评估。"
    return f"讲稿落点可以收束为：{section_name}正在从概念介绍转向更具体的案例和评估。"


def remove_repeated_focus(section_name: str, focus: str) -> str:
    labels = [label for label in focus.split("、") if label and label != section_name]
    return "、".join(labels[:3])


def fallback_current_text_for_ppt_item(raw: dict[str, Any], deck: PPTDeck) -> str:
    if raw.get("kind") != "node_update" or not raw.get("node_id"):
        return ""
    try:
        matches = load_ppt_node_matches(deck.csv_path, deck.node_registry_path)
    except (FileNotFoundError, OSError, yaml.YAMLError):
        return ""
    for match in matches:
        if match.registered.node_id != raw.get("node_id") or not match.current:
            continue
        candidates = [
            *match.current.content,
            *match.current.circled_items,
            *match.current.figure_notes,
        ]
        for candidate in candidates:
            value = compact_inline_text(str(candidate), max_chars=92)
            if value:
                return value
    return ""


def compact_inline_text(text: str, max_chars: int = 120) -> str:
    value = re.sub(r"\s+", " ", text).strip().rstrip("。；;")
    if len(value) <= max_chars:
        return value
    return value[: max_chars - 1].rstrip("，,；;。") + "…"


def ppt_suggestion_display_title(raw: dict[str, Any], title: str, location: str) -> str:
    if raw.get("kind") == "node_update" and location:
        return clean_ppt_heading(location.split(" / ")[-1])
    if raw.get("kind") == "section_trend":
        return clean_ppt_heading(location.split(" / ")[-1] if location else title)
    return clean_ppt_heading(title)


def ppt_suggestion_subtitle(raw: dict[str, Any], title: str, location: str) -> str:
    parts = [str(raw.get("kind_label", raw.get("kind", "")))]
    if raw.get("kind") == "node_update" and title:
        parts.append(title)
    if location:
        parts.append(location)
    return " · ".join(part for part in parts if part)


def clean_ppt_heading(text: str) -> str:
    value = re.sub(r"（[一二三四五六七八九十]+）", "", text).strip()
    value = re.sub(r"^\d+\s*", "", value).strip()
    return value or text


def cards_by_id(settings: Settings) -> dict[str, dict[str, Any]]:
    lookup = {}
    for card in all_cards(settings):
        lookup[str(card["id"])] = card
    return lookup


def enrich_ppt_evidence_card(card_lookup: dict[str, dict[str, Any]], card: dict[str, Any]) -> dict[str, Any]:
    card_id = str(card.get("card_id", ""))
    existing = card_lookup.get(card_id, {})
    status = existing.get("status", "")
    return {
        "id": card_id,
        "title": existing.get("title") or card.get("title") or card_id,
        "date": existing.get("date") or card.get("date", ""),
        "status": status,
        "status_label": existing.get("status_label") or STATUS_LABELS.get(status, status),
        "source_url": existing.get("source_url") or card.get("source_url", ""),
        "source_label": existing.get("source_label") or source_label(card.get("source_url", "")),
        "conclusion": existing.get("conclusion") or card.get("conclusion", ""),
        "overview": existing.get("event_overview") or card.get("overview", ""),
        "detail_url": existing.get("detail_url") or f"/cards/{card_id}",
    }


def evidence_summary(cards: list[dict[str, Any]]) -> str:
    if not cards:
        return "缺少证据卡片"
    accepted = len([card for card in cards if card.get("status") == "accepted"])
    needs_review = len([card for card in cards if card.get("status") == "needs-review"])
    parts = [f"{len(cards)} 张证据卡片"]
    if accepted:
        parts.append(f"{accepted} 张已接受")
    if needs_review:
        parts.append(f"{needs_review} 张待审核")
    return "，".join(parts)


def parse_ppt_plan_review_items(path: Path) -> list[dict[str, Any]]:
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    items: list[dict[str, Any]] = []
    active_section = ""
    current: dict[str, Any] | None = None
    body: list[str] = []
    target_sections = {
        "二级小节趋势建议": "section_trend",
        "结构化更新建议": "node_update",
    }
    for line in lines:
        if line.startswith("## "):
            if current:
                items.append(finalize_ppt_review_item(path, current, body))
            current = None
            body = []
            active_section = line.removeprefix("## ").strip()
            continue
        if active_section not in target_sections:
            continue
        if line.startswith("### "):
            if current:
                items.append(finalize_ppt_review_item(path, current, body))
            title = line.removeprefix("### ").strip()
            current = {
                "title": title,
                "kind": target_sections[active_section],
                "kind_label": "小节趋势建议" if active_section == "二级小节趋势建议" else "结构节点建议",
            }
            body = []
            continue
        if current:
            if line.startswith("#### "):
                continue
            body.append(line)
    if current:
        items.append(finalize_ppt_review_item(path, current, body))
    return items


def finalize_ppt_review_item(path: Path, item: dict[str, Any], body: list[str]) -> dict[str, Any]:
    excerpt = compact_markdown_excerpt(body, max_lines=12)
    raw_key = f"{path.name}|{item['kind']}|{item['title']}"
    item_id = stable_id(raw_key)
    return {
        "id": item_id,
        "report_name": path.name,
        "report_path": str(path),
        "title": item["title"],
        "kind": item["kind"],
        "kind_label": item["kind_label"],
        "excerpt": excerpt,
        "excerpt_html": markdown_renderer.render(excerpt),
        "status": "pending",
        "status_label": "待处理",
        "updated_at": "",
    }


def compact_markdown_excerpt(lines: list[str], max_lines: int = 12) -> str:
    cleaned = [line for line in lines if line.strip()]
    return "\n".join(cleaned[:max_lines]).strip()


def set_ppt_suggestion_status(settings: Settings, deck: PPTDeck, item_id: str, status: str) -> None:
    if status not in {"accepted", "rejected", "adopted", "pending"}:
        return
    lookup = {item["id"]: item for item in ppt_review_items(settings, deck, limit=200)}
    item = lookup.get(item_id)
    if not item:
        return
    links = read_ppt_card_links(settings)
    suggestions = links.setdefault("suggestions", {})
    suggestions[item_id] = {
        "status": status,
        "title": item["title"],
        "kind": item["kind"],
        "kind_label": item.get("kind_label", ""),
        "deck_id": deck.id,
        "deck_title": deck.title,
        "deck_version": deck.version,
        "location": item.get("location", ""),
        "report_name": item["report_name"],
        "report_path": item["report_path"],
        "card_ids": item.get("card_ids", [card["id"] for card in item.get("cards", [])]),
        "updated_at": now_iso(settings.timezone),
    }
    write_ppt_card_links(settings, links)


def ppt_review_state_path(settings: Settings) -> Path:
    return settings.root / "data" / "ppt_update_reviews.yaml"


def ppt_review_status_label(status: str) -> str:
    return {
        "pending": "待处理",
        "accepted": "已采纳，待写入",
        "rejected": "暂不更新",
        "adopted": "已写入 PPT",
    }.get(status, status)


def ppt_card_links_path(settings: Settings) -> Path:
    return settings.root / "data" / "ppt_card_links.yaml"


def read_ppt_card_links(settings: Settings) -> dict[str, Any]:
    path = ppt_card_links_path(settings)
    if not path.exists():
        return {"suggestions": {}}
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(data.get("suggestions"), dict):
        data["suggestions"] = {}
    return data


def write_ppt_card_links(settings: Settings, data: dict[str, Any]) -> None:
    path = ppt_card_links_path(settings)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(data, allow_unicode=True, sort_keys=False), encoding="utf-8")


def card_ppt_usage(settings: Settings, card_id: str) -> list[dict[str, Any]]:
    links = read_ppt_card_links(settings).get("suggestions", {})
    usages = []
    for suggestion_id, item in links.items():
        if card_id not in [str(value) for value in item.get("card_ids", [])]:
            continue
        status = item.get("status", "pending")
        usages.append(
            {
                "suggestion_id": suggestion_id,
                "title": item.get("title", suggestion_id),
                "kind_label": item.get("kind_label", item.get("kind", "")),
                "deck_id": item.get("deck_id", ""),
                "deck_label": deck_usage_label(item),
                "location": item.get("location", ""),
                "report_name": item.get("report_name", ""),
                "status": status,
                "status_label": ppt_review_status_label(status),
            }
        )
    return sorted(usages, key=lambda item: (item["status"], item["title"]))


def deck_usage_label(item: dict[str, Any]) -> str:
    title = item.get("deck_title") or item.get("deck_id") or "未命名 PPT"
    version = item.get("deck_version", "")
    return f"{title}（{version}）" if version else title


PPT_IMPORT_START = "<!-- AI_DAILY_PPT_UPDATE_SUGGESTIONS_START -->"
PPT_IMPORT_END = "<!-- AI_DAILY_PPT_UPDATE_SUGGESTIONS_END -->"


def ppt_manuscript_path(deck: PPTDeck) -> Path:
    return deck.manuscript_path


def ppt_manuscript_info(settings: Settings, deck: PPTDeck) -> dict[str, Any]:
    path = ppt_manuscript_path(deck)
    content = path.read_text(encoding="utf-8") if path.exists() else ""
    chunks = split_manuscript_chunks(content)
    return {
        "path": str(path),
        "deck_id": deck.id,
        "deck_label": deck.label,
        "exists": path.exists(),
        "content": content,
        "chunks": chunks,
        "outline": build_manuscript_outline(chunks),
        "section_count": sum(1 for chunk in chunks if chunk["kind"] == "section"),
        "line_count": len(content.splitlines()),
        "has_import_block": PPT_IMPORT_START in content and PPT_IMPORT_END in content,
    }


def build_manuscript_outline(chunks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    outline: list[dict[str, Any]] = []
    level1_lookup: dict[str, dict[str, Any]] = {}
    for chunk in chunks:
        if chunk.get("kind") != "section":
            continue
        level1_title = str(chunk.get("level1") or "未归入一级标题")
        level2_title = str(chunk.get("level2") or "未归入二级标题")
        level1_item = level1_lookup.get(level1_title)
        if not level1_item:
            level1_item = {"title": level1_title, "children": [], "_level2_lookup": {}}
            level1_lookup[level1_title] = level1_item
            outline.append(level1_item)
        level2_lookup = level1_item["_level2_lookup"]
        level2_item = level2_lookup.get(level2_title)
        if not level2_item:
            level2_item = {"title": level2_title, "sections": []}
            level2_lookup[level2_title] = level2_item
            level1_item["children"].append(level2_item)
        level2_item["sections"].append(
            {
                "title": chunk.get("title", ""),
                "page": chunk.get("page", ""),
                "anchor": chunk.get("anchor", ""),
            }
        )
    for level1_item in outline:
        level1_item.pop("_level2_lookup", None)
    return outline


def split_manuscript_chunks(content: str) -> list[dict[str, Any]]:
    if not content:
        return []
    chunks: list[dict[str, Any]] = []
    current_lines: list[str] = []
    current_meta: dict[str, Any] | None = None
    level1 = ""
    level2 = ""
    page = ""
    in_import_block = False

    def flush() -> None:
        nonlocal current_lines, current_meta
        if not current_lines:
            return
        meta = current_meta or {"kind": "static", "title": ""}
        content_text = "\n".join(current_lines).rstrip()
        if content_text:
            item = dict(meta)
            item["content"] = content_text
            item["line_count"] = len(content_text.splitlines())
            chunks.append(item)
        current_lines = []
        current_meta = None

    lines = content.splitlines()
    for index, raw_line in enumerate(lines):
        line = raw_line.rstrip()
        stripped = line.strip()
        if stripped == PPT_IMPORT_START:
            flush()
            in_import_block = True
            current_meta = {"kind": "static", "title": "自动导入区"}
            current_lines.append(line)
            continue
        if in_import_block:
            current_lines.append(line)
            if stripped == PPT_IMPORT_END:
                flush()
                in_import_block = False
            continue
        slide_match = re.search(r"<!--\s*slide:\s*(\d+)\s*-->", stripped)
        if slide_match:
            page = slide_match.group(1)
            if current_meta and current_meta.get("kind") == "section":
                current_meta["page"] = page
        if stripped.startswith("# ") or stripped.startswith("## "):
            if current_meta and current_meta.get("kind") == "section":
                flush()
        if stripped.startswith("# "):
            level1 = stripped.removeprefix("# ").strip()
            level2 = ""
        elif stripped.startswith("## "):
            level2 = stripped.removeprefix("## ").strip()
            if not level2_has_child_heading(lines, index):
                current_meta = {
                    "kind": "section",
                    "title": "",
                    "level1": level1,
                    "level2": level2,
                    "level3": "",
                    "page": page,
                    "anchor": f"manuscript-section-{len([item for item in chunks if item['kind'] == 'section']) + 1}",
                }
        if stripped.startswith("### "):
            flush()
            title = stripped.removeprefix("### ").strip()
            current_meta = {
                "kind": "section",
                "title": title,
                "level1": level1,
                "level2": level2,
                "level3": title,
                "page": page,
                "anchor": f"manuscript-section-{len([item for item in chunks if item['kind'] == 'section']) + 1}",
            }
        elif current_meta is None:
            current_meta = {"kind": "static", "title": ""}
        current_lines.append(line)
    flush()
    return chunks


def level2_has_child_heading(lines: list[str], start_index: int) -> bool:
    for line in lines[start_index + 1 :]:
        stripped = line.strip()
        if stripped.startswith("# ") or stripped.startswith("## "):
            return False
        if stripped.startswith("### "):
            return True
    return False


def import_ppt_suggestions_to_manuscript(settings: Settings, deck: PPTDeck) -> Path | None:
    path = ppt_manuscript_path(deck)
    if not path.exists():
        return None
    content = path.read_text(encoding="utf-8")
    block = build_ppt_manuscript_import_block(settings, deck)
    backup_ppt_manuscript(settings, path)
    path.write_text(upsert_manuscript_import_block(content, block), encoding="utf-8")
    return path


def build_ppt_manuscript_import_block(settings: Settings, deck: PPTDeck) -> str:
    links = read_ppt_card_links(settings).get("suggestions", {})
    item_lookup = {item["id"]: item for item in ppt_review_items(settings, deck, limit=300)}
    selected = [
        (suggestion_id, state, item_lookup.get(suggestion_id))
        for suggestion_id, state in links.items()
        if state.get("status") in {"accepted", "adopted"}
        and state.get("deck_id", deck.id) == deck.id
    ]
    lines = [
        PPT_IMPORT_START,
        "",
        "## 自动导入的 PPT 更新建议",
        "",
        f"- PPT：{deck.label}",
        f"- 导入时间：{now_iso(settings.timezone)}",
        "- 来源：PPT 建议审核中状态为“已采纳，待写入”或“已写入 PPT”的建议。",
        "- 使用方式：这里是讲稿草案区，可直接编辑、移动到对应小节，或删除不需要的条目。",
        "",
    ]
    if not selected:
        lines.extend(["暂无已采纳或已写入的 PPT 更新建议。", ""])
    for suggestion_id, state, item in selected:
        title = (item or {}).get("display_title") or state.get("title", suggestion_id)
        location = (item or {}).get("location") or state.get("location", "")
        recommendation = (item or {}).get("recommendation") or ""
        edits = (item or {}).get("edits", [])
        status_label = ppt_review_status_label(state.get("status", "pending"))
        cards = (item or {}).get("cards", [])
        lines.extend(
            [
                f"### {title}",
                "",
                f"- 状态：{status_label}",
                f"- 建议位置：{location or '未记录'}",
                f"- 建议写法：{recommendation or '未提取'}",
            ]
        )
        if edits:
            lines.append("- 具体改法：")
            for edit in edits[:3]:
                page = f"第 {edit.get('page')} 页" if edit.get("page") else "对应页面"
                current_text = str(edit.get("current_text") or "").strip()
                suggested_text = str(edit.get("suggested_text") or "").strip()
                if current_text:
                    lines.append(f"  - {page}的“{current_text}”可修改为“{suggested_text}”")
                else:
                    lines.append(f"  - {page}可新增表述：“{suggested_text}”")
        if cards:
            lines.append("- 证据卡片：")
            for card in cards[:6]:
                lines.append(
                    f"  - {card.get('title', card.get('id', '未命名卡片'))}"
                    f"（{card.get('date', '')}，{card.get('source_label', '')}）"
                )
        lines.append("")
    lines.append(PPT_IMPORT_END)
    return "\n".join(lines).rstrip() + "\n"


def upsert_manuscript_import_block(content: str, block: str) -> str:
    if PPT_IMPORT_START in content and PPT_IMPORT_END in content:
        pattern = re.compile(
            rf"{re.escape(PPT_IMPORT_START)}.*?{re.escape(PPT_IMPORT_END)}",
            re.DOTALL,
        )
        return pattern.sub(block.rstrip(), content).rstrip() + "\n"
    return content.rstrip() + "\n\n" + block


def save_ppt_manuscript(settings: Settings, deck: PPTDeck, content: str) -> Path:
    path = ppt_manuscript_path(deck)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        backup_ppt_manuscript(settings, path)
    path.write_text(content.rstrip() + "\n", encoding="utf-8")
    return path


def backup_ppt_manuscript(settings: Settings, path: Path) -> Path:
    backup_dir = settings.root / "ppt" / "backups"
    backup_dir.mkdir(parents=True, exist_ok=True)
    stamp = re.sub(r"[:+]", "-", now_iso(settings.timezone))
    target = backup_dir / f"{path.stem}-{stamp}{path.suffix}"
    shutil.copy2(path, target)
    return target


PPT_MANUSCRIPT_TEMPLATE = """---
title: 人工智能发展前沿
version: 60分钟版
duration: 60
speaker:
source_file:
updated_at:
---

# 人工智能发展前沿 PPT 结构化文字稿

- source_file:
- slide_count:
- extraction_scope: editable_text_only_no_images_no_media
- hierarchy: level1_from_outline; level2_from_parenthesized_chinese_numbers; level3_from_arabic_numbered_titles

## 封面

<!-- slide: 1 -->
- 人工智能发展前沿
- 汇报人：
- 日期：

## 大纲

<!-- slide: 2 -->
- 一、第一部分
- 二、第二部分
- 三、第三部分

# 一、第一部分标题

## （一）二级小节标题

### 1 三级主题标题

<!-- slide: 3 -->
- 这里填写讲稿要点。
- 每条尽量是一句话。
- 可保留适合口头汇报的表达。

### 2 另一个三级主题标题

<!-- slide: 4 -->
- 这里继续填写内容。

## （二）另一个二级小节标题

### 1 三级主题标题

<!-- slide: 5 -->
- 这里填写内容。
"""


def create_ppt_deck(
    settings: Settings,
    deck_id: str,
    title: str,
    version: str,
    duration: str,
    manuscript_text: str,
) -> PPTDeck:
    clean_id = normalize_deck_id(deck_id or f"{title}-{version}")
    deck_dir = settings.root / "ppt" / "decks" / clean_id
    deck_dir.mkdir(parents=True, exist_ok=True)
    manuscript_path = deck_dir / "manuscript.md"
    csv_path = deck_dir / "structured.csv"
    nodes_path = deck_dir / "nodes.yaml"
    metadata_path = deck_dir / "metadata.yaml"
    content = ensure_manuscript_frontmatter(
        manuscript_text or PPT_MANUSCRIPT_TEMPLATE,
        title=title,
        version=version,
        duration=duration,
    )
    manuscript_path.write_text(content.rstrip() + "\n", encoding="utf-8")
    rows = manuscript_to_csv_rows(content)
    write_manuscript_csv(csv_path, rows)
    write_initial_node_registry(nodes_path, rows)
    metadata_path.write_text(
        yaml.safe_dump(
            {
                "id": clean_id,
                "title": title,
                "version": version,
                "duration": duration,
                "created_at": now_iso(settings.timezone),
            },
            allow_unicode=True,
            sort_keys=False,
        ),
        encoding="utf-8",
    )
    register_ppt_deck(
        settings.root,
        {
            "id": clean_id,
            "title": title,
            "version": version,
            "manuscript_path": str(manuscript_path.relative_to(settings.root)),
            "csv_path": str(csv_path.relative_to(settings.root)),
            "node_registry_path": str(nodes_path.relative_to(settings.root)),
        },
    )
    return selected_ppt_deck(settings.root, clean_id)


def normalize_deck_id(value: str) -> str:
    text = re.sub(r"[^A-Za-z0-9\u4e00-\u9fff_-]+", "-", value.strip().lower())
    text = re.sub(r"-+", "-", text).strip("-_")
    return text or "ppt-deck"


def ensure_manuscript_frontmatter(content: str, title: str, version: str, duration: str) -> str:
    stripped = content.strip()
    if stripped.startswith("---"):
        return stripped
    frontmatter = [
        "---",
        f"title: {title}",
        f"version: {version}",
        f"duration: {duration}",
        "speaker:",
        "source_file:",
        "updated_at:",
        "---",
        "",
    ]
    return "\n".join(frontmatter) + stripped


def manuscript_to_csv_rows(content: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    level1 = ""
    level2 = ""
    level3 = ""
    page = 0
    in_frontmatter = False
    for line in content.splitlines():
        stripped = line.strip()
        if stripped == "---":
            in_frontmatter = not in_frontmatter
            continue
        if in_frontmatter or not stripped:
            continue
        slide_match = re.search(r"<!--\s*slide:\s*(\d+)\s*-->", stripped)
        if slide_match:
            page = int(slide_match.group(1))
            continue
        if stripped.startswith("# "):
            heading = stripped.removeprefix("# ").strip()
            if "结构化文字稿" not in heading:
                level1 = heading
                level2 = ""
                level3 = ""
            continue
        if stripped.startswith("## "):
            level2 = stripped.removeprefix("## ").strip()
            level3 = ""
            continue
        if stripped.startswith("### "):
            level3 = stripped.removeprefix("### ").strip()
            continue
        if stripped.startswith("- "):
            rows.append(
                {
                    "page": page,
                    "level1": level1,
                    "level2": level2,
                    "level3": level3,
                    "content_type": "content",
                    "content": stripped.removeprefix("- ").strip(),
                }
            )
    return rows


def write_manuscript_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["page", "level1", "level2", "level3", "content_type", "content"],
        )
        writer.writeheader()
        writer.writerows(rows)


def write_initial_node_registry(path: Path, rows: list[dict[str, Any]]) -> None:
    grouped: dict[tuple[str, str, str], dict[str, str]] = {}
    for row in rows:
        key = (str(row["level1"]), str(row["level2"]), str(row["level3"]))
        if not any(key):
            continue
        grouped.setdefault(
            key,
            {
                "current_level1": key[0],
                "current_level2": key[1],
                "current_level3": key[2],
            },
        )
    nodes = []
    for index, item in enumerate(grouped.values(), start=1):
        title_path = " / ".join(
            part for part in [item["current_level1"], item["current_level2"], item["current_level3"]] if part
        )
        nodes.append(
            {
                "node_id": f"auto.node_{index:03d}",
                "status": "active",
                "role": "自动生成节点",
                "intent": f"跟踪{title_path or '本节'}相关更新，用于补充讲稿。",
                **item,
                "keywords": heading_keywords(title_path),
                "update_policy": "自动上传讲稿生成的初始节点，可后续人工改名、补充关键词和更新策略。",
            }
        )
    path.write_text(yaml.safe_dump({"nodes": nodes}, allow_unicode=True, sort_keys=False), encoding="utf-8")


def heading_keywords(text: str) -> list[str]:
    cleaned = re.sub(r"[（）()：:、/，,。；;【】\[\]\s]+", " ", text)
    terms = []
    seen = set()
    for part in cleaned.split():
        value = re.sub(r"^\d+", "", part).strip()
        if len(value) < 2 or value in seen:
            continue
        seen.add(value)
        terms.append(value)
    return terms[:12]


def register_ppt_deck(root: Path, deck: dict[str, str]) -> None:
    config_path = root / "ppt" / "decks.yaml"
    data = yaml.safe_load(config_path.read_text(encoding="utf-8")) if config_path.exists() else {}
    decks = data.setdefault("decks", [])
    decks[:] = [item for item in decks if item.get("id") != deck["id"]]
    decks.append(deck)
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(yaml.safe_dump(data, allow_unicode=True, sort_keys=False), encoding="utf-8")


def review_stats(items: list[dict[str, Any]]) -> dict[str, int]:
    stats = {"pending": 0, "accepted": 0, "rejected": 0, "adopted": 0}
    for item in items:
        status = item.get("status", "pending")
        if status in stats:
            stats[status] += 1
    return stats


def ppt_source_suggestion_preview(root: Path) -> dict[str, str] | None:
    path = root / "data" / "ppt_source_suggestions.md"
    if not path.exists():
        return None
    text = path.read_text(encoding="utf-8")
    preview = "\n".join(text.splitlines()[:120])
    return {
        "name": path.name,
        "path": str(path),
        "preview_html": markdown_renderer.render(preview),
    }


def source_suggestion_items(settings: Settings) -> list[dict[str, Any]]:
    path = settings.root / "data" / "ppt_source_suggestions.md"
    states = read_review_state(source_suggestion_state_path(settings))
    existing_urls = configured_source_urls(settings.sources)
    items = []
    priority = ""
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.startswith("### "):
                priority = line.removeprefix("### ").split("：", 1)[0].strip()
                continue
            row = parse_source_suggestion_row(line)
            if not row:
                continue
            row["proposal_origin"] = "manual"
            items.append(source_suggestion_with_state(row, states, existing_urls, priority or "未分级"))
    seen_ids = {item["id"] for item in items}
    for proposal in read_source_proposals(settings.root):
        row = source_proposal_row(proposal)
        suggestion_id = stable_id(row["url"])
        if suggestion_id in seen_ids:
            continue
        seen_ids.add(suggestion_id)
        items.append(
            source_suggestion_with_state(
                row,
                states,
                existing_urls,
                str(proposal.get("priority") or "自动建议"),
            )
        )
    return items


def source_suggestion_with_state(
    row: dict[str, Any],
    states: dict[str, Any],
    existing_urls: set[str],
    priority: str,
) -> dict[str, Any]:
    suggestion_id = stable_id(str(row["url"]))
    state = states.get(suggestion_id, {})
    status = state.get("status", "added" if row["url"] in existing_urls else "pending")
    row.update(
        {
            "id": suggestion_id,
            "priority": priority,
            "status": status,
            "status_label": source_suggestion_status_label(status),
            "status_class": source_suggestion_status_class(status),
            "already_configured": row["url"] in existing_urls,
            "updated_at": state.get("updated_at", ""),
        }
    )
    return row


def source_suggestion_json_response(
    templates: Jinja2Templates,
    settings: Settings,
    suggestion_id: str,
    return_to: str,
) -> JSONResponse:
    item = next(
        (item for item in source_suggestion_items(settings) if item["id"] == suggestion_id),
        None,
    )
    if not item:
        return JSONResponse(
            {"ok": False, "error": "source_suggestion_not_found"},
            status_code=404,
        )
    actions_html = templates.get_template("_source_suggestion_actions.html").render(
        source=item,
        source_return_to=return_to,
    )
    return JSONResponse(
        {
            "ok": True,
            "suggestion_id": suggestion_id,
            "status": item["status"],
            "status_label": item["status_label"],
            "status_class": item["status_class"],
            "actions_html": actions_html,
        }
    )


def source_proposal_row(proposal: dict[str, Any]) -> dict[str, Any]:
    primary_topic = str(proposal.get("primary_topic") or "general-ai")
    secondary_topic = str(proposal.get("secondary_topic") or "")
    topic_text = str(
        proposal.get("topic_text")
        or " / ".join(part for part in [primary_topic, secondary_topic] if part)
        or "general-ai"
    )
    return {
        "name": str(proposal.get("name") or proposal.get("url") or "未命名来源"),
        "url": str(proposal.get("url") or ""),
        "coverage": str(proposal.get("coverage") or ""),
        "topic_text": topic_text,
        "primary_topic": primary_topic,
        "secondary_topic": secondary_topic,
        "reason": str(proposal.get("reason") or ""),
        "proposal_origin": str(proposal.get("proposal_origin") or "auto"),
    }


def parse_source_suggestion_row(line: str) -> dict[str, str] | None:
    if not line.startswith("|"):
        return None
    cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
    if len(cells) != 5 or cells[0] in {"建议源", "---"}:
        return None
    if not cells[1].startswith("http"):
        return None
    primary_topic, secondary_topic = split_suggested_topics(cells[3])
    return {
        "name": cells[0],
        "url": cells[1],
        "coverage": cells[2],
        "topic_text": cells[3],
        "primary_topic": primary_topic,
        "secondary_topic": secondary_topic,
        "reason": cells[4],
    }


def split_suggested_topics(text: str) -> tuple[str, str]:
    parts = [part.strip() for part in text.split("/") if part.strip()]
    if not parts:
        return "general-ai", ""
    return parts[0], parts[1] if len(parts) > 1 else ""


def set_source_suggestion_status(settings: Settings, suggestion_id: str, status: str) -> None:
    if status not in {"pending", "accepted", "rejected", "added"}:
        return
    lookup = {item["id"]: item for item in source_suggestion_items(settings)}
    item = lookup.get(suggestion_id)
    if not item:
        return
    path = source_suggestion_state_path(settings)
    states = read_review_state(path)
    states[suggestion_id] = {
        "status": status,
        "name": item["name"],
        "url": item["url"],
        "updated_at": now_iso(settings.timezone),
    }
    write_review_state(path, states)


def add_source_suggestion_to_config(settings: Settings, suggestion_id: str) -> None:
    lookup = {item["id"]: item for item in source_suggestion_items(settings)}
    item = lookup.get(suggestion_id)
    if not item:
        return
    sources_path = settings.root / "config" / "sources.yaml"
    data = yaml.safe_load(sources_path.read_text(encoding="utf-8")) if sources_path.exists() else {}
    sources = data.setdefault("sources", {})
    add_source_topics_if_missing(sources, [item["primary_topic"], item["secondary_topic"]])
    company_blogs = sources.setdefault("company_blogs", {})
    company_blogs.setdefault("enabled", True)
    company_blogs.setdefault("track", "industry")
    entries = company_blogs.setdefault("sources", [])
    if any(str(entry.get("url", "")).rstrip("/") == item["url"].rstrip("/") for entry in entries):
        set_source_suggestion_status(settings, suggestion_id, "added")
        return
    entries.append(
        {
            "name": item["name"],
            "url": item["url"],
            "track": suggested_source_track(item),
            "primary_topic": item["primary_topic"] or "general-ai",
            "secondary_topic": item["secondary_topic"],
            "include_paths": [suggested_include_path(item["url"])],
        }
    )
    sources_path.write_text(
        yaml.safe_dump(data, allow_unicode=True, sort_keys=False),
        encoding="utf-8",
    )
    set_source_suggestion_status(settings, suggestion_id, "added")


def add_source_topics_if_missing(sources: dict[str, Any], topic_ids: list[str]) -> None:
    options = sources.setdefault("source_topics", [])
    existing = {
        str(option.get("id", ""))
        for option in options
        if isinstance(option, dict)
    }
    for topic_id in topic_ids:
        if not topic_id or topic_id in existing:
            continue
        options.append({"id": topic_id, "label": source_theme_label(topic_id)})
        existing.add(topic_id)


def suggested_source_track(item: dict[str, Any]) -> str:
    topics = " ".join([item.get("primary_topic", ""), item.get("secondary_topic", "")])
    if "academic-research" in topics or "ai4science" in topics:
        return "academic"
    return "industry"


def suggested_include_path(url: str) -> str:
    parsed = urlparse(url)
    path = parsed.path.rstrip("/")
    return path + "/" if path else "/"


def source_suggestion_state_path(settings: Settings) -> Path:
    return settings.root / "data" / "source_suggestion_reviews.yaml"


def source_suggestion_status_label(status: str) -> str:
    return {
        "pending": "待筛选",
        "accepted": "待加入",
        "rejected": "不加入",
        "added": "已加入",
    }.get(status, status)


def source_suggestion_status_class(status: str) -> str:
    if status in {"accepted", "added"}:
        return "accepted"
    if status == "rejected":
        return "rejected"
    return "later"


def configured_source_urls(sources_config: dict[str, Any]) -> set[str]:
    urls = set()
    sources = section(sources_config, "sources")
    for feed in list_section(section(sources, "rss"), "feeds"):
        url = str(feed.get("url", "")).rstrip("/")
        if url:
            urls.add(url)
    for source in list_section(section(sources, "company_blogs"), "sources"):
        url = str(source.get("url", "")).rstrip("/")
        if url:
            urls.add(url)
    return urls


def read_review_state(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def write_review_state(path: Path, state: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(state, allow_unicode=True, sort_keys=False), encoding="utf-8")


def stable_id(text: str) -> str:
    return hashlib.sha1(text.encode("utf-8")).hexdigest()[:16]


def source_entries(settings: Settings) -> list[dict[str, Any]]:
    sources = section(settings.sources, "sources")
    entries: list[dict[str, Any]] = []
    arxiv_config = section(sources, "arxiv")
    entries.append(
        source_entry(
            settings.sources,
            name="arXiv latest",
            kind="arxiv",
            track="academic",
            url="https://arxiv.org/",
            enabled=bool(arxiv_config.get("enabled", False)),
            keywords=list(arxiv_config.get("categories", [])),
            raw=arxiv_config,
            fallback_topics=["academic-research", "foundation-model"],
            source_key="arxiv",
        )
    )
    rss_config = section(sources, "rss")
    for index, feed in enumerate(list_section(rss_config, "feeds")):
        entries.append(
            source_entry(
                settings.sources,
                name=feed.get("name", feed.get("url", "RSS")),
                kind="rss",
                track=feed.get("track", "industry"),
                url=feed.get("url", ""),
                enabled=bool(rss_config.get("enabled", False))
                and feed.get("enabled", True) is not False,
                raw=feed,
                source_key=f"rss:{index}",
            )
        )
    company_config = section(sources, "company_blogs")
    for index, item in enumerate(list_section(company_config, "sources")):
        entries.append(
            source_entry(
                settings.sources,
                name=item.get("name", item.get("url", "Web source")),
                kind="web",
                track=item.get("track", company_config.get("track", "industry")),
                url=item.get("url", ""),
                enabled=bool(company_config.get("enabled", False))
                and item.get("enabled", True) is not False,
                keywords=list(item.get("include_paths", [])),
                raw=item,
                source_key=f"web:{index}",
            )
        )
    return sorted(entries, key=lambda item: (item["theme_labels"][0], item["kind"], item["name"]))


def source_entry(
    sources_config: dict[str, Any],
    name: str,
    kind: str,
    track: str,
    url: str,
    enabled: bool,
    keywords: list[str] | None = None,
    raw: dict[str, Any] | None = None,
    fallback_topics: list[str] | None = None,
    source_key: str = "",
) -> dict[str, Any]:
    theme_ids = source_topics(raw or {}, fallback=fallback_topics)
    labels = source_topic_label_map(sources_config)
    theme_labels = [source_topic_label(theme_id, labels) for theme_id in theme_ids]
    tags = source_keywords(name, kind, track, url, keywords or [], theme_ids)
    return {
        "name": name,
        "kind": kind,
        "track": track,
        "track_label": TRACK_LABELS.get(track, track),
        "url": url,
        "enabled": enabled,
        "source_key": source_key,
        "theme_ids": theme_ids,
        "theme_labels": theme_labels,
        "primary_topic": theme_ids[0],
        "primary_topic_label": theme_labels[0],
        "secondary_topic": theme_ids[1] if len(theme_ids) > 1 else "",
        "secondary_topic_label": theme_labels[1] if len(theme_labels) > 1 else "",
        "keywords": tags,
        "search_text": " ".join([name, kind, track, url, *theme_ids, *theme_labels, *tags]).lower(),
    }


def source_topics(raw: dict[str, Any], fallback: list[str] | None = None) -> list[str]:
    if raw.get("primary_topic") or raw.get("secondary_topic"):
        values = [raw.get("primary_topic") or "general-ai", raw.get("secondary_topic") or ""]
    else:
        values = raw.get("themes", raw.get("theme", fallback or ["general-ai"]))
    if isinstance(values, str):
        values = [values]
    if not values:
        values = fallback or ["general-ai"]
    normalized = []
    seen = set()
    for value in values:
        theme_id = str(value).strip()
        if not theme_id or theme_id in seen:
            continue
        seen.add(theme_id)
        normalized.append(theme_id)
    return normalized or (fallback or ["general-ai"])


def source_theme_label(theme_id: str) -> str:
    return SOURCE_THEME_LABELS.get(theme_id, theme_id)


def source_topic_label(theme_id: str, labels: dict[str, str]) -> str:
    return labels.get(theme_id, source_theme_label(theme_id))


def source_topic_label_map(sources_config: dict[str, Any]) -> dict[str, str]:
    labels = dict(SOURCE_THEME_LABELS)
    options = list_section(sources_config, "source_topics")
    options = list(options) + list_section(section(sources_config, "sources"), "source_topics")
    for option in options:
        if not isinstance(option, dict):
            continue
        topic_id = str(option.get("id", "")).strip()
        label = str(option.get("label", "")).strip()
        if topic_id and label:
            labels[topic_id] = label
    return labels


def source_theme_options(entries: list[dict[str, Any]]) -> list[dict[str, str]]:
    options: dict[str, str] = {}
    for entry in entries:
        for theme_id, label in zip(entry["theme_ids"], entry["theme_labels"]):
            options[theme_id] = label
    return [
        {"id": theme_id, "label": label}
        for theme_id, label in sorted(options.items(), key=lambda item: item[1])
    ]


def source_topic_options(sources_config: dict[str, Any]) -> list[dict[str, str]]:
    labels = source_topic_label_map(sources_config)
    return [
        {"id": topic_id, "label": label}
        for topic_id, label in sorted(labels.items(), key=lambda item: item[1])
    ]


def sources_page_url(query: str, theme: str) -> str:
    params = {}
    if query:
        params["q"] = query
    if theme:
        params["theme"] = theme
    encoded = urlencode(params)
    return f"/sources?{encoded}" if encoded else "/sources"


def update_source_topics(
    settings: Settings, source_key: str, primary_topic: str, secondary_topic: str = ""
) -> bool:
    source_config_path = settings.root / "config" / "sources.yaml"
    raw = load_sources_yaml_for_update(source_config_path)
    sources = raw.setdefault("sources", {})
    normalized_topics = source_topics(
        {"primary_topic": primary_topic, "secondary_topic": secondary_topic}
    )
    target = source_config_target(sources, source_key)
    if target is None:
        return False
    target["primary_topic"] = normalized_topics[0]
    if len(normalized_topics) > 1:
        target["secondary_topic"] = normalized_topics[1]
    else:
        target.pop("secondary_topic", None)
    source_config_path.write_text(
        yaml.safe_dump(raw, allow_unicode=True, sort_keys=False),
        encoding="utf-8",
    )
    settings.sources.clear()
    settings.sources.update(raw)
    return True


def update_source_themes(settings: Settings, source_key: str, themes: list[str]) -> bool:
    topics = source_topics({"themes": themes})
    primary = topics[0]
    secondary = topics[1] if len(topics) > 1 else ""
    return update_source_topics(settings, source_key, primary, secondary)


def update_source_enabled(settings: Settings, source_key: str, enabled: bool) -> bool:
    source_config_path = settings.root / "config" / "sources.yaml"
    raw = load_sources_yaml_for_update(source_config_path)
    sources = raw.setdefault("sources", {})
    target = source_config_target(sources, source_key)
    if target is None:
        return False
    target["enabled"] = bool(enabled)
    source_config_path.write_text(
        yaml.safe_dump(raw, allow_unicode=True, sort_keys=False),
        encoding="utf-8",
    )
    settings.sources.clear()
    settings.sources.update(raw)
    return True


def add_source_topic_option(settings: Settings, topic_id: str, label: str) -> bool:
    clean_label = " ".join(label.split())
    clean_id = normalize_source_topic_id(topic_id or clean_label)
    if not clean_id or not clean_label:
        return False
    source_config_path = settings.root / "config" / "sources.yaml"
    raw = load_sources_yaml_for_update(source_config_path)
    options = raw.setdefault("sources", {}).setdefault("source_topics", [])
    for option in options:
        if isinstance(option, dict) and option.get("id") == clean_id:
            option["label"] = clean_label
            break
    else:
        options.append({"id": clean_id, "label": clean_label})
    source_config_path.write_text(
        yaml.safe_dump(raw, allow_unicode=True, sort_keys=False),
        encoding="utf-8",
    )
    settings.sources.clear()
    settings.sources.update(raw)
    return True


def normalize_source_topic_id(value: str) -> str:
    text = value.strip().lower()
    text = re.sub(r"[^a-z0-9\u4e00-\u9fff]+", "-", text).strip("-")
    return text or "custom-topic"


def load_sources_yaml_for_update(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"sources": {}}
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {"sources": {}}


def source_config_target(sources: dict[str, Any], source_key: str) -> dict[str, Any] | None:
    if source_key == "arxiv":
        return sources.setdefault("arxiv", {})
    prefix, _, index_text = source_key.partition(":")
    try:
        index = int(index_text)
    except ValueError:
        return None
    if prefix == "rss":
        feeds = sources.setdefault("rss", {}).setdefault("feeds", [])
        return feeds[index] if 0 <= index < len(feeds) else None
    if prefix == "web":
        web_sources = sources.setdefault("company_blogs", {}).setdefault("sources", [])
        return web_sources[index] if 0 <= index < len(web_sources) else None
    return None


def source_keywords(
    name: str, kind: str, track: str, url: str, keywords: list[str], themes: list[str]
) -> list[str]:
    text = f"{name} {url}".lower()
    tags = set(keywords)
    if track == "academic":
        tags.update(["学术", "论文", "基础模型", "自监督训练"])
    if track == "industry":
        tags.update(["产业", "产品", "基础模型"])
    if any(part in text for part in ["arena", "artificial analysis", "openrouter", "helm"]):
        tags.update(["公开测评", "榜单", "benchmark-evaluation", "基础模型"])
    if any(part in text for part in ["agent", "anthropic", "openai", "cursor", "windsurf"]):
        tags.update(["智能体", "agent"])
    if any(part in text for part in ["nature", "science", "arxiv", "huggingface"]):
        tags.update(["基础模型", "自监督训练", "空间智能"])
    if any(part in text for part in ["机器之心", "量子位", "qbitai", "jiqizhixin"]):
        tags.update(["中文", "媒体", "智能体", "基础模型", "空间智能"])
    return sorted(tag for tag in tags if tag)


def filter_source_entries(
    entries: list[dict[str, Any]], query: str, theme: str = ""
) -> list[dict[str, Any]]:
    normalized = query.strip().lower()
    return [
        entry
        for entry in entries
        if (not normalized or normalized in entry["search_text"])
        and (not theme or theme in entry["theme_ids"])
    ]


def ppt_plan_date_range(
    settings: Settings, preset: str, from_date: str, to_date: str
) -> tuple[Any, Any]:
    today = today_in_timezone(settings.timezone)
    if preset == "today":
        start = today
        end = today
    elif preset == "this_week":
        start = today - timedelta(days=today.weekday())
        end = today
    else:
        start = fromiso_date_or_default(from_date, today)
        end = fromiso_date_or_default(to_date, start)
    if end < start:
        start, end = end, start
    return start, end


def configure_daily_scheduler(settings: Settings) -> None:
    schedule_config = section(section(settings.app, "daily"), "schedule")
    if not schedule_config.get("enabled", False):
        return
    schedule_times = parse_daily_schedule_times(schedule_config.get("times", []))
    if not schedule_times:
        return
    start_daily_scheduler(settings.root, settings.timezone, schedule_times)


def parse_daily_schedule_times(raw_times: list[str] | tuple[str, ...] | Any) -> list[tuple[int, int]]:
    parsed: list[tuple[int, int]] = []
    if not isinstance(raw_times, (list, tuple)):
        raw_times = []
    for raw_time in raw_times:
        if not isinstance(raw_time, str):
            continue
        match = re.fullmatch(r"([01]?\d|2[0-3]):([0-5]\d)", raw_time.strip())
        if not match:
            continue
        parsed.append((int(match.group(1)), int(match.group(2))))
    return sorted(set(parsed))


def start_daily_scheduler(root: Path, timezone: str, schedule_times: list[tuple[int, int]]) -> None:
    root_key = str(root.resolve())
    with SCHEDULER_LOCK:
        existing = SCHEDULER_THREADS.get(root_key)
        if existing and existing.is_alive():
            return
        thread = threading.Thread(
            target=daily_scheduler_loop,
            args=(root, timezone, schedule_times),
            daemon=True,
            name=f"daily-scheduler:{root_key}",
        )
        SCHEDULER_THREADS[root_key] = thread
        thread.start()


def daily_scheduler_loop(root: Path, timezone: str, schedule_times: list[tuple[int, int]]) -> None:
    triggered_keys: set[str] = set()
    while True:
        now = datetime.now(ZoneInfo(timezone))
        today_prefix = now.date().isoformat()
        triggered_keys = {key for key in triggered_keys if key.startswith(today_prefix)}
        for hour, minute in schedule_times:
            if now.hour != hour or now.minute != minute:
                continue
            trigger_key = f"{today_prefix} {hour:02d}:{minute:02d}"
            if trigger_key in triggered_keys:
                continue
            triggered_keys.add(trigger_key)
            if has_running_daily_job():
                continue
            job_id = start_daily_job(
                dry_run=False,
                manual_only=False,
                root=root,
                trigger="schedule",
                schedule_label=f"{hour:02d}:{minute:02d}",
            )
            job_log(job_id, f"由定时任务触发：{hour:02d}:{minute:02d}")
        # Poll often enough to catch minute-level schedules while staying lightweight.
        threading.Event().wait(20)


def has_running_daily_job() -> bool:
    with JOBS_LOCK:
        return any(
            job.get("job_type") == "daily" and job.get("status") in {"queued", "running"}
            for job in JOBS.values()
        )


def start_ppt_plan_job(
    root: Path, deck_id: str, from_date: str, to_date: str, date_basis: str, status: str
) -> str:
    job_id = uuid.uuid4().hex[:12]
    job = {
        "id": job_id,
        "label": "生成 PPT 更新建议",
        "status": "queued",
        "step": "已加入后台任务队列",
        "root": str(root),
        "deck_id": deck_id,
        "from_date": from_date,
        "to_date": to_date,
        "date_basis": date_basis,
        "card_status": status,
        "job_type": "ppt-plan",
        "logs": [],
    }
    with JOBS_LOCK:
        JOBS[job_id] = job
    thread = threading.Thread(target=run_ppt_plan_job, args=(job_id,), daemon=True)
    thread.start()
    return job_id


def start_brief_job(
    root: Path, from_date: str, to_date: str, topics: list[str], audience: str, date_basis: str
) -> str:
    job_id = uuid.uuid4().hex[:12]
    job = {
        "id": job_id,
        "label": "生成简报",
        "status": "queued",
        "step": "已加入后台任务队列",
        "root": str(root),
        "from_date": from_date,
        "to_date": to_date,
        "topics": topics,
        "audience": audience,
        "date_basis": date_basis,
        "job_type": "brief",
        "logs": [],
    }
    with JOBS_LOCK:
        JOBS[job_id] = job
    threading.Thread(target=run_brief_job, args=(job_id,), daemon=True).start()
    return job_id


def run_brief_job(job_id: str) -> None:
    try:
        from ai_daily_update.cli import _llm_client

        snapshot = job_snapshot(job_id)
        settings = load_settings(Path(str(snapshot.get("root") or Path.cwd())))
        job_update(job_id, status="running", step="正在筛选已接受卡片")
        job_log(job_id, f"时间范围：{snapshot.get('from_date')} 至 {snapshot.get('to_date')}")
        topics = snapshot.get("topics") or []
        if topics:
            job_log(job_id, f"Topic 过滤：{', '.join(str(topic) for topic in topics)}")
        job_update(job_id, step="正在生成简报内容")
        output_path = generate_brief(
            settings.sqlite_path,
            settings.markdown_root,
            str(snapshot.get("from_date")),
            str(snapshot.get("to_date")),
            list(topics) or None,
            str(snapshot.get("audience", "academic")),
            date_basis=str(snapshot.get("date_basis", "collected")),
            llm_client=_llm_client(settings),
        )
        job_update(job_id, status="complete", step="已完成")
        job_log(job_id, "简报已生成，可在下方查看内容。")
    except Exception as exc:
        job_update(job_id, status="failed", step=f"失败：{exc}")
        job_log(job_id, traceback.format_exc(limit=4))


def run_ppt_plan_job(job_id: str) -> None:
    from ai_daily_update.cli import _llm_client

    snapshot = job_snapshot(job_id)
    settings = load_settings(Path(str(snapshot.get("root") or Path.cwd())))
    deck = selected_ppt_deck(settings.root, snapshot.get("deck_id", ""))
    job_update(job_id, status="running", step="正在匹配 PPT 结构节点和已接受卡片")
    try:
        job_log(job_id, f"选择 PPT：{deck.label}")
        job_log(job_id, f"时间范围：{snapshot.get('from_date')} 至 {snapshot.get('to_date')}")
        if section(settings.app, "ppt").get("llm_polish", False):
            job_update(job_id, step="正在生成结构化建议，并调用 LLM 改写讲稿")
            job_log(job_id, "LLM 讲稿化改写已启用")
            llm_client = _llm_client(settings)
        else:
            job_update(job_id, step="正在生成结构化建议")
            job_log(job_id, "LLM 讲稿化改写未启用，使用规则建议")
            llm_client = None
        output_path = generate_ppt_plan(
            settings.markdown_root,
            deck.csv_path,
            deck.node_registry_path,
            str(snapshot.get("from_date")),
            str(snapshot.get("to_date")),
            date_basis=str(snapshot.get("date_basis", "collected")),
            status=str(snapshot.get("card_status", "accepted")),
            topics_config=settings.topics,
            deck_id=deck.id,
            deck_title=deck.title,
            deck_version=deck.version,
            llm_client=llm_client,
        )
        job_update(job_id, status="complete", step="已完成")
        job_log(job_id, f"已生成：{output_path.name}")
    except Exception as exc:
        job_update(job_id, status="failed", step=f"失败：{exc}")
        job_log(job_id, traceback.format_exc(limit=4))


def start_daily_job(
    dry_run: bool,
    manual_only: bool,
    root: Path | None = None,
    trigger: str = "manual",
    schedule_label: str = "",
) -> str:
    job_id = uuid.uuid4().hex[:12]
    if trigger == "schedule":
        label = f"定时生成今日卡片 {schedule_label}".strip()
    else:
        label = "预跑候选" if dry_run else "生成今日卡片"
    job = {
        "id": job_id,
        "label": label,
        "status": "queued",
        "step": "已加入后台任务队列",
        "dry_run": dry_run,
        "manual_only": manual_only,
        "root": str(root or Path.cwd()),
        "trigger": trigger,
        "job_type": "daily",
        "schedule_label": schedule_label,
        "logs": [],
    }
    with JOBS_LOCK:
        JOBS[job_id] = job
    thread = threading.Thread(
        target=run_daily_job,
        args=(job_id,),
        daemon=True,
    )
    thread.start()
    return job_id


def run_daily_job(job_id: str) -> None:
    from ai_daily_update.cli import run_daily_pipeline

    job_update(job_id, status="running", step="正在采集消息源、去重并评分")
    try:
        snapshot = job_snapshot(job_id)
        settings = load_settings(Path(str(snapshot.get("root") or Path.cwd())))

        def progress(message: str) -> None:
            job_update(job_id, step=message)
            job_log(job_id, message)

        job_log(job_id, "开始执行 daily pipeline")
        run_daily_pipeline(
            settings,
            today_in_timezone(settings.timezone),
            manual_only=bool(snapshot.get("manual_only")),
            dry_run=bool(snapshot.get("dry_run")),
            progress=progress,
        )
        job_update(job_id, status="complete", step="已完成")
        job_log(job_id, "任务完成，可以刷新卡片、候选报告或简报页面查看结果")
    except Exception as exc:
        job_update(job_id, status="failed", step=f"失败：{exc}")
        job_log(job_id, traceback.format_exc(limit=4))


def job_snapshot(job_id: str) -> dict[str, Any]:
    with JOBS_LOCK:
        return dict(JOBS.get(job_id, {}))


def job_update(job_id: str, **updates: Any) -> None:
    with JOBS_LOCK:
        if job_id not in JOBS:
            return
        JOBS[job_id].update(updates)


def job_log(job_id: str, message: str) -> None:
    with JOBS_LOCK:
        if job_id not in JOBS:
            return
        logs = JOBS[job_id].setdefault("logs", [])
        logs.append(message)
        del logs[:-20]


def latest_job_snapshot(job_type: str | None = None) -> dict[str, Any] | None:
    with JOBS_LOCK:
        if not JOBS:
            return None
        for latest_id in reversed(JOBS):
            job = JOBS[latest_id]
            if job_type and job.get("job_type") != job_type:
                continue
            return dict(job)
        return None


def preference_status(settings: Settings) -> dict[str, Any]:
    feedback_path = feedback_log_path(settings.root)
    feedback_events = read_feedback_events(settings.root)
    surface_labels = {
        "cards": "知识卡片",
        "ppt_suggestions": "PPT 更新建议",
        "source_proposals": "消息源建议",
    }
    surfaces = []
    for surface in sorted(SURFACES):
        path = feature_output_path(settings.root, surface)
        surfaces.append(
            {
                "id": surface,
                "label": surface_labels.get(surface, surface),
                "path": str(path),
                "exists": path.exists(),
                "count": len(read_feature_records(settings.root, surface)),
                "updated_at": format_file_mtime(path, settings.timezone) if path.exists() else "",
            }
        )
    return {
        "feedback_path": str(feedback_path),
        "feedback_exists": feedback_path.exists(),
        "feedback_count": len(feedback_events),
        "feature_version": "v1",
        "model_status": "尚未训练",
        "model_note": "当前仅抽取和缓存特征；SVM/线性模型会在反馈样本积累后再训练。",
        "surfaces": surfaces,
    }


def trend_suggestions(settings: Settings) -> list[dict[str, Any]]:
    text = "\n".join(trend_source_texts(settings))
    suggestions = []
    for group in trend_term_groups(settings):
        count = trend_group_count(text, group["terms"])
        if count == 0:
            continue
        suggestions.append(
            {
                "term": group["label"],
                "aliases": group["aliases"],
                "count": count,
                "status": "已有主题" if group["configured"] else "候选趋势",
                "action": "可继续观察" if group["configured"] else "建议评估是否加入 topics.yaml",
            }
        )
    return sorted(suggestions, key=lambda item: (item["count"], item["term"]), reverse=True)


def trend_source_texts(settings: Settings) -> list[str]:
    texts = []
    for path in list(iter_cards(settings.markdown_root))[:80]:
        card = read_card(path)
        metadata = card.metadata
        texts.append(
            "\n".join(
                [
                    str(metadata.get("title_zh", "")),
                    str(metadata.get("title_en", "")),
                    " ".join(metadata.get("topics", [])),
                    card.content[:1200],
                ]
            )
        )
    report = latest_candidate_report(settings.markdown_root)
    if report:
        texts.append(report.get("preview", ""))
    return texts


def configured_topic_terms(settings: Settings) -> set[str]:
    terms = set()
    for topic_id, topic in section(settings.topics, "topics").items():
        topic = topic if isinstance(topic, dict) else {}
        terms.add(str(topic_id).lower())
        for key in ["name_zh", "name_en"]:
            if topic.get(key):
                terms.add(str(topic[key]).lower())
        for alias in topic.get("aliases", []) or []:
            terms.add(str(alias).lower())
    return terms


def trend_term_groups(settings: Settings) -> list[dict[str, Any]]:
    return build_trend_term_groups(settings.topics)


app = create_app()
