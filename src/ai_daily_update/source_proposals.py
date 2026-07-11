from __future__ import annotations

from collections import Counter, defaultdict
import json
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from ai_daily_update.config import Settings
from ai_daily_update.storage.markdown import iter_cards, read_card
from ai_daily_update.utils.config import list_section, section
from ai_daily_update.utils.dates import now_iso


def source_proposals_path(root: Path) -> Path:
    return root / "data" / "source_proposals.json"


def generate_source_proposals(settings: Settings) -> Path:
    proposals = accepted_card_domain_proposals(settings)
    proposals.extend(inaccessible_link_proposals(settings.root))
    proposals = dedupe_proposals(proposals)
    payload = {
        "generated_at": now_iso(settings.timezone),
        "proposal_version": "v1",
        "proposals": proposals,
    }
    path = source_proposals_path(settings.root)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def read_source_proposals(root: Path) -> list[dict[str, Any]]:
    path = source_proposals_path(root)
    if not path.exists():
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    proposals = data.get("proposals", [])
    return [item for item in proposals if isinstance(item, dict)]


def accepted_card_domain_proposals(settings: Settings) -> list[dict[str, Any]]:
    configured_domains = source_configured_domains(settings.sources)
    domain_counts: Counter[str] = Counter()
    domain_topics: dict[str, Counter[str]] = defaultdict(Counter)
    domain_titles: dict[str, list[str]] = defaultdict(list)
    for path in iter_cards(settings.markdown_root):
        card = read_card(path)
        metadata = card.metadata
        if metadata.get("review_status") != "accepted":
            continue
        url = str(metadata.get("source_url") or "")
        root_url = source_root_url(url)
        if not root_url:
            continue
        domain = urlparse(root_url).netloc.removeprefix("www.")
        if domain in configured_domains:
            continue
        domain_counts[root_url] += 1
        for topic in metadata.get("topics", []) or []:
            if topic:
                domain_topics[root_url][str(topic)] += 1
        title = str(metadata.get("title_zh") or metadata.get("title_en") or "")
        if title and len(domain_titles[root_url]) < 3:
            domain_titles[root_url].append(title)
    proposals = []
    for root_url, count in domain_counts.most_common(20):
        if count < 2:
            continue
        topics = [topic for topic, _ in domain_topics[root_url].most_common(2)]
        primary_topic = topics[0] if topics else "general-ai"
        secondary_topic = topics[1] if len(topics) > 1 else ""
        domain = urlparse(root_url).netloc.removeprefix("www.")
        examples = "；".join(domain_titles[root_url])
        proposals.append(
            {
                "name": domain,
                "url": root_url,
                "coverage": f"已接受卡片来源域名，近库内命中 {count} 次",
                "topic_text": " / ".join(part for part in [primary_topic, secondary_topic] if part),
                "primary_topic": primary_topic,
                "secondary_topic": secondary_topic,
                "reason": f"该域名多次出现在已接受卡片中，可考虑配置为正式消息源。示例：{examples}",
                "priority": "高频已接受来源" if count >= 3 else "候选来源",
                "proposal_origin": "accepted-card-domain",
                "score": min(100, 50 + count * 10),
            }
        )
    return proposals


def inaccessible_link_proposals(root: Path) -> list[dict[str, Any]]:
    path = root / "data" / "inaccessible_links.md"
    if not path.exists():
        return []
    proposals = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.startswith("|"):
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if len(cells) < 4 or cells[0] in {"Source", "---"}:
            continue
        name, url, status, note = cells[:4]
        if not url.startswith("http"):
            continue
        proposals.append(
            {
                "name": name,
                "url": url,
                "coverage": f"待修复消息源：{status}",
                "topic_text": "general-ai",
                "primary_topic": "general-ai",
                "secondary_topic": "",
                "reason": note,
                "priority": "待修复/待接入",
                "proposal_origin": "inaccessible-links",
                "score": 45,
            }
        )
    return proposals


def dedupe_proposals(proposals: list[dict[str, Any]]) -> list[dict[str, Any]]:
    deduped: dict[str, dict[str, Any]] = {}
    for proposal in proposals:
        url = str(proposal.get("url") or "").rstrip("/")
        if not url:
            continue
        existing = deduped.get(url)
        if not existing or int(proposal.get("score", 0)) > int(existing.get("score", 0)):
            proposal = dict(proposal)
            proposal["url"] = url
            deduped[url] = proposal
    return sorted(
        deduped.values(),
        key=lambda item: (int(item.get("score", 0)), str(item.get("name", ""))),
        reverse=True,
    )


def source_configured_domains(sources_config: dict[str, Any]) -> set[str]:
    domains: set[str] = set()
    sources = section(sources_config, "sources")
    if section(sources, "arxiv").get("enabled", False):
        domains.add("arxiv.org")
    for feed in list_section(section(sources, "rss"), "feeds"):
        add_domain(domains, str(feed.get("url", "")))
    for source in list_section(section(sources, "company_blogs"), "sources"):
        add_domain(domains, str(source.get("url", "")))
    return domains


def add_domain(domains: set[str], url: str) -> None:
    parsed = urlparse(url)
    domain = parsed.netloc.removeprefix("www.")
    if domain:
        domains.add(domain)


def source_root_url(url: str) -> str:
    parsed = urlparse(url)
    if not parsed.scheme or not parsed.netloc:
        return ""
    return f"{parsed.scheme}://{parsed.netloc.removeprefix('www.')}"
