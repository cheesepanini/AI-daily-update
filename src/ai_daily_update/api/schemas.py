from __future__ import annotations

from typing import Annotated, Any, Literal

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


class LearningPlanRequest(BaseModel):
    goal_id: str = Field(default="", max_length=40)
    goal_text: str = Field(default="", max_length=200)
    background: str = Field(default="beginner", max_length=20)
    known_ids: list[Annotated[str, Field(max_length=120)]] = Field(default_factory=list, max_length=100)


class LearningHistoryTurn(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(max_length=500)


class LearningChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=1200)
    depth: str = Field(default="plain", max_length=20)
    card_id: str = Field(default="", max_length=200)
    history: list[LearningHistoryTurn] = Field(default_factory=list, max_length=12)
