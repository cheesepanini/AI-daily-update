from __future__ import annotations

from datetime import date, datetime
import re
from zoneinfo import ZoneInfo


def today_in_timezone(timezone: str) -> date:
    return datetime.now(ZoneInfo(timezone)).date()


def now_iso(timezone: str) -> str:
    return datetime.now(ZoneInfo(timezone)).isoformat(timespec="seconds")


def normalize_iso_date(value: str) -> str | None:
    text = value.strip()
    if not text:
        return ""
    try:
        return datetime.strptime(text, "%Y-%m-%d").date().isoformat()
    except ValueError:
        return None


_WRITTEN_DATE = re.compile(
    r"(?<!\d)20\d{2}[-/.]\d{1,2}[-/.]\d{1,2}(?!\d)|20\d{2}\s*年\s*\d{1,2}\s*月\s*\d{1,2}\s*日|"
    r"\b(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|"
    r"Sep(?:t(?:ember)?)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\.?\s+\d{1,2},?\s+20\d{2}\b|"
    r"\b\d{1,2}\s+(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|"
    r"Sep(?:t(?:ember)?)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\.?\s+20\d{2}\b", re.I,
)


def written_dates(text: str) -> set[str]:
    values = set()
    for match in _WRITTEN_DATE.finditer(text):
        value = re.sub(r"\s|日", "", match[0]) if match[0][0:4].isdigit() else match[0].replace(".", "").replace(",", "")
        value = re.sub("[/.年月]", "-", value)
        for fmt in ("%Y-%m-%d", "%B %d %Y", "%b %d %Y", "%d %B %Y", "%d %b %Y"):
            try:
                values.add(datetime.strptime(value.replace("Sept ", "Sep "), fmt).date().isoformat())
                break
            except ValueError:
                continue
    return values


def public_date_fields(metadata: dict) -> dict[str, str]:
    dates = metadata.get("news_dates", {})
    event = normalize_iso_date(str(dates.get("event") or "")) or ""
    reported = normalize_iso_date(str(dates.get("reported") or "")) or ""
    legacy = ""
    if "news_dates" not in metadata:
        legacy = normalize_iso_date(str(metadata.get("event_date") or metadata.get("date") or "")) or ""
    if event:
        label = "事件日期"
    elif reported:
        label = "报道日期"
    elif legacy:
        label = "旧记录日期 · 待核实"
    else:
        label = "日期待核实"
    return {"confirmed_event_date": event, "reported_date": reported, "legacy_date": legacy,
            "display_date": event or reported or legacy, "date_label": label}
