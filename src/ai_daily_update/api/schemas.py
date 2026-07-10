from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class PublicCardSummary(BaseModel):
    id: str
    title: str
    title_en: str = ""
    event_date: str = ""
    info_date: str = ""
    collected_date: str = ""
    status: str = ""
    status_label: str = ""
    track: str = ""
    track_label: str = ""
    source_label: str = ""
    source_url: str = ""
    topics: list[str] = Field(default_factory=list)
    conclusion: str = ""
    event_overview: str = ""
    detail_url: str = ""


class PublicCardDetail(PublicCardSummary):
    content_html: str = ""
    content_markdown: str = ""
    sections: list[dict[str, str]] = Field(default_factory=list)


class Pagination(BaseModel):
    page: int
    page_size: int
    total: int
    total_pages: int
    has_previous: bool
    has_next: bool


class PublicCardListResponse(BaseModel):
    api_version: str = "v1"
    items: list[PublicCardSummary]
    pagination: Pagination


class PublicMetaResponse(BaseModel):
    api_version: str = "v1"
    project_name: str
    server_time: str
    available_tracks: list[dict[str, str]]
    available_statuses: list[dict[str, str]]
    default_page_size: int = 20
    max_page_size: int = 50


class ApiError(BaseModel):
    error: dict[str, Any]
