from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ManualCandidate:
    url: str
    track: str
    topics: list[str]
    title: str


def read_manual_urls(path: Path) -> list[ManualCandidate]:
    if not path.exists():
        return []
    candidates: list[ManualCandidate] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        parts = [part.strip() for part in stripped.split("|")]
        url = parts[0]
        track = parts[1] if len(parts) > 1 and parts[1] else "industry"
        topics = (
            [topic.strip() for topic in parts[2].split(",") if topic.strip()]
            if len(parts) > 2 and parts[2]
            else ["ai-industry" if track == "industry" else "foundation-model"]
        )
        title = parts[3] if len(parts) > 3 and parts[3] else url
        candidates.append(ManualCandidate(url=url, track=track, topics=topics, title=title))
    return candidates
