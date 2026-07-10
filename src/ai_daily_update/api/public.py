from __future__ import annotations

from ai_daily_update.api.schemas import PublicCardSummary


def public_card_summary(card: dict) -> PublicCardSummary:
    return PublicCardSummary(
        id=str(card.get("id", "")),
        title=str(card.get("title", "")),
        title_en=str(card.get("title_en", "")),
        event_date=str(card.get("event_date", "")),
        info_date=str(card.get("info_date", "")),
        collected_date=str(card.get("collected_date", "")),
        status=str(card.get("status", "")),
        status_label=str(card.get("status_label", "")),
        track=str(card.get("track", "")),
        track_label=str(card.get("track_label", "")),
        source_label=str(card.get("source_label", "")),
        source_url=str(card.get("source_url", "")),
        topics=list(card.get("topics", []) or []),
        conclusion=str(card.get("conclusion", "")),
        event_overview=str(card.get("event_overview", "")),
        detail_url=f"/api/v1/cards/{card.get('id', '')}",
    )
