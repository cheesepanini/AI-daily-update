from __future__ import annotations

import os
import subprocess
from datetime import date
from pathlib import Path
from typing import Annotated, Callable

import typer

from ai_daily_update.collectors.arxiv import search_latest_arxiv
from ai_daily_update.collectors.company_blogs import (
    company_blogs_from_settings,
    fetch_all_company_blogs,
)
from ai_daily_update.collectors.manual import ManualCandidate, read_manual_urls
from ai_daily_update.collectors.rss import feeds_from_settings, fetch_all_rss_feeds
from ai_daily_update.collectors.web_page import SourceDocument, fetch_source_document
from ai_daily_update.config import Settings, load_settings
from ai_daily_update.feedback.events import append_feedback_event
from ai_daily_update.llm.client import OpenAIClient
from ai_daily_update.preference.features import extract_preference_features
from ai_daily_update.processors.card_builder import (
    apply_content_date,
    build_card_metadata,
    build_placeholder_content,
    card_path,
)
from ai_daily_update.processors.candidates import (
    Candidate,
    candidate_from_arxiv_document,
    candidate_from_company_item,
    candidate_from_manual,
    candidate_from_rss_item,
)
from ai_daily_update.processors.classify import classify_candidate_topics
from ai_daily_update.processors.dedupe import dedupe_by_url, normalize_url_for_dedupe
from ai_daily_update.processors.digest import expand_digest_candidate, should_split_digest
from ai_daily_update.processors.metadata import infer_title_zh
from ai_daily_update.processors.score import score_candidate, select_top_candidates
from ai_daily_update.processors.score import select_top_media_candidates
from ai_daily_update.ppt.corpus import (
    group_ppt_topic_nodes,
    match_registered_nodes,
    read_ppt_entries,
    read_ppt_node_registry,
)
from ai_daily_update.ppt.decks import selected_ppt_deck
from ai_daily_update.ppt.plan import generate_ppt_plan
from ai_daily_update.reports.brief import generate_brief
from ai_daily_update.reports.candidates import write_candidate_report
from ai_daily_update.reports.review_summary import (
    build_review_summary_prompt,
    deterministic_review_summary,
    needs_review_cards as collect_needs_review_cards,
    write_review_summary,
)
from ai_daily_update.review.auto import auto_review_stale_cards
from ai_daily_update.review.workflow import needs_review_cards, set_review_status
from ai_daily_update.source_proposals import generate_source_proposals
from ai_daily_update.storage.indexer import rebuild_index
from ai_daily_update.storage.markdown import iter_cards, read_card, write_card
from ai_daily_update.utils.dates import today_in_timezone
from ai_daily_update.utils.paths import ensure_directories


app = typer.Typer(help="AI-Daily-Update local knowledge base CLI.")
ProgressCallback = Callable[[str], None]


def emit_progress(progress: ProgressCallback | None, message: str) -> None:
    if progress:
        progress(message)


def _settings() -> Settings:
    settings = load_settings(Path.cwd())
    ensure_directories(settings.root)
    return settings


def _llm_client(settings: Settings) -> OpenAIClient:
    llm_config = settings.app.get("llm", {})
    return OpenAIClient(
        model=llm_config.get("model") or os.getenv("OPENAI_MODEL", ""),
        api_key_env=llm_config.get("api_key_env", "OPENAI_API_KEY"),
        base_url=llm_config.get("base_url") or os.getenv("OPENAI_BASE_URL") or None,
    )


def _prompt_for_candidate(
    candidate: Candidate, source_document: SourceDocument | None
) -> str:
    source_material = "未能抓取正文，请仅基于已知元数据生成，并明确标注待核实。"
    if source_document and source_document.text:
        source_material = f"""
Fetched title: {source_document.title}
Fetched description: {source_document.description}
Fetched text excerpt:
{source_document.text[:12000]}
"""
    return f"""
请根据以下来源材料生成中文知识卡片草稿。

要求：
- 中文正文。
- 不要编造事实；无法从材料确认的部分写“待核实”。
- 保留英文标题、英文关键词和原始来源。
- 输出 Markdown 正文，不要输出 frontmatter。
- 不要把整段结果包裹在 ```markdown 或其他代码块中。
- 第一行必须是一级标题，格式为：# 知识卡片：中文标题。
- 尽量使用如下小节：一句话结论、事件概述或研究问题、方法/产品要点、主要结果或产业意义、为什么重要、局限与不确定性、可用于图书/PPT/简报的角度、原始材料。

URL: {candidate.url}
Track: {candidate.track}
Topics: {", ".join(candidate.topics)}
Manual title: {candidate.title}
Candidate summary: {getattr(candidate, "summary", "")}
Parent digest: {getattr(candidate, "parent_title", "")}
Parent URL: {getattr(candidate, "parent_url", "")}

Source material:
{source_material}
"""


def candidates_for_generation(candidates: list[Candidate]) -> list[Candidate]:
    """Generate media cards first so their separate quota is visible quickly."""
    media = [candidate for candidate in candidates if candidate.source_kind == "chinese_media"]
    non_media = [candidate for candidate in candidates if candidate.source_kind != "chinese_media"]
    return media + non_media


@app.command()
def doctor() -> None:
    """Check config, directories, env vars, and database path."""
    settings = _settings()
    checks = [
        ("config/app.yaml", (settings.root / "config/app.yaml").exists()),
        ("config/topics.yaml", (settings.root / "config/topics.yaml").exists()),
        ("config/sources.yaml", (settings.root / "config/sources.yaml").exists()),
        ("data/manual_urls.txt", settings.manual_urls_path.exists()),
        ("notes/cards", (settings.markdown_root / "cards").exists()),
    ]
    for name, ok in checks:
        typer.echo(f"{'OK' if ok else 'MISSING'}  {name}")
    llm = _llm_client(settings)
    typer.echo(f"{'OK' if llm.available else 'SKIP'}  OpenAI API configuration")
    typer.echo(f"INFO  SQLite path: {settings.sqlite_path}")


@app.command()
def serve(
    host: Annotated[str, typer.Option("--host", help="Dashboard host.")] = "127.0.0.1",
    port: Annotated[int, typer.Option("--port", help="Dashboard port.")] = 8000,
    reload: Annotated[bool, typer.Option("--reload", help="Reload on code changes.")] = False,
) -> None:
    """Start the local dashboard."""
    import uvicorn

    uvicorn.run(
        "ai_daily_update.web:create_app",
        factory=True,
        host=host,
        port=port,
        reload=reload,
    )


@app.command("review-summary")
def review_summary(
    day: Annotated[
        str | None,
        typer.Option("--date", help="Write summary for this date."),
    ] = None,
    limit: Annotated[int, typer.Option("--limit", help="Maximum cards to summarize.")] = 12,
) -> None:
    """Generate a concise LLM summary for needs-review cards."""
    settings = _settings()
    run_day = date.fromisoformat(day) if day else today_in_timezone(settings.timezone)
    cards = collect_needs_review_cards(settings.markdown_root, limit=limit)
    if not cards:
        typer.echo("No needs-review cards.")
        return
    llm = _llm_client(settings)
    if llm.available:
        content = llm.generate_card_content(build_review_summary_prompt(cards))
    else:
        content = deterministic_review_summary(cards)
    output_path = write_review_summary(settings.markdown_root, run_day, content or "")
    typer.echo(f"Review summary written: {output_path}")


@app.command("ppt-nodes")
def ppt_nodes(
    deck_id: Annotated[
        str,
        typer.Option("--deck-id", help="PPT deck id from ppt/decks.yaml."),
    ] = "",
    ppt_csv: Annotated[
        Path | None,
        typer.Option("--ppt-csv", help="Structured PPT CSV path."),
    ] = None,
    node_registry: Annotated[
        Path | None,
        typer.Option("--node-registry", help="Stable PPT node registry YAML."),
    ] = None,
) -> None:
    """Check stable PPT nodes against the current structured PPT text."""
    settings = _settings()
    deck = selected_ppt_deck(settings.root, deck_id)
    ppt_csv = ppt_csv or deck.csv_path
    node_registry = node_registry or deck.node_registry_path
    entries = read_ppt_entries(ppt_csv)
    current_nodes = group_ppt_topic_nodes(entries)
    registered_nodes = read_ppt_node_registry(node_registry)
    matches = match_registered_nodes(
        [node for node in registered_nodes if node.status == "active"],
        current_nodes,
    )
    matched = [match for match in matches if match.current]
    typer.echo(f"PPT current topic nodes: {len(current_nodes)}")
    typer.echo(f"Registered active nodes: {len(matches)}")
    typer.echo(f"Matched registered nodes: {len(matched)}")
    for match in matches:
        if match.current:
            pages = ",".join(str(page) for page in match.current.pages)
            typer.echo(
                f"- {match.registered.node_id}: score={match.score} pages={pages} "
                f"location={match.current.title_path}"
            )
        else:
            typer.echo(f"- {match.registered.node_id}: unmatched")


@app.command("ppt-plan")
def ppt_plan(
    from_date: Annotated[str, typer.Option("--from-date", help="Start date YYYY-MM-DD.")],
    to_date: Annotated[str, typer.Option("--to-date", help="End date YYYY-MM-DD.")],
    deck_id: Annotated[
        str,
        typer.Option("--deck-id", help="PPT deck id from ppt/decks.yaml."),
    ] = "",
    ppt_csv: Annotated[
        Path | None,
        typer.Option("--ppt-csv", help="Structured PPT CSV path."),
    ] = None,
    node_registry: Annotated[
        Path | None,
        typer.Option("--node-registry", help="Stable PPT node registry YAML."),
    ] = None,
    date_basis: Annotated[
        str,
        typer.Option("--date-basis", help="collected or event."),
    ] = "collected",
    status: Annotated[
        str,
        typer.Option("--status", help="Card review status to include."),
    ] = "accepted",
) -> None:
    """Generate a structure-node-based PPT update plan from knowledge cards."""
    settings = _settings()
    deck = selected_ppt_deck(settings.root, deck_id)
    ppt_csv = ppt_csv or deck.csv_path
    node_registry = node_registry or deck.node_registry_path
    llm_client = _llm_client(settings) if settings.app.get("ppt", {}).get("llm_polish", False) else None
    output_path = generate_ppt_plan(
        settings.markdown_root,
        ppt_csv,
        node_registry,
        from_date,
        to_date,
        date_basis=date_basis,
        status=status,
        topics_config=settings.topics,
        deck_id=deck.id,
        deck_title=deck.title,
        deck_version=deck.version,
        llm_client=llm_client,
    )
    typer.echo(f"PPT update plan written: {output_path}")


@app.command()
def daily(
    day: Annotated[
        str | None,
        typer.Option("--date", help="Generate cards for this date."),
    ] = None,
    manual_only: Annotated[
        bool,
        typer.Option("--manual-only", help="Only use data/manual_urls.txt candidates."),
    ] = False,
    dry_run: Annotated[
        bool,
        typer.Option("--dry-run", help="Collect, dedupe, score, and print candidates without generating cards."),
    ] = False,
) -> None:
    """Run the V0.1 daily pipeline."""
    settings = _settings()
    run_day = date.fromisoformat(day) if day else today_in_timezone(settings.timezone)
    run_daily_pipeline(settings, run_day, manual_only=manual_only, dry_run=dry_run)


def run_daily_pipeline(
    settings: Settings,
    run_day: date,
    manual_only: bool = False,
    dry_run: bool = False,
    progress: ProgressCallback | None = None,
) -> None:
    emit_progress(progress, "正在采集消息源")
    candidates, collection_warnings = collect_daily_candidates(
        settings,
        manual_only=manual_only,
        progress=progress,
    )
    emit_progress(progress, f"形成候选 {len(candidates)} 条")
    for warning in collection_warnings:
        typer.echo(f"warning: {warning}", err=True)
    if not candidates:
        emit_progress(progress, "没有采集到候选内容")
        typer.echo("No candidates found.")
        return
    emit_progress(progress, "正在与已有卡片去重")
    existing_source_urls = existing_card_source_urls(settings.markdown_root)
    duplicate_existing = [
        candidate
        for candidate in candidates
        if normalize_url_for_dedupe(candidate.url) in existing_source_urls
    ]
    candidates = [
        candidate
        for candidate in candidates
        if normalize_url_for_dedupe(candidate.url) not in existing_source_urls
    ]
    emit_progress(
        progress,
        f"去重完成：新增候选 {len(candidates)} 条，跳过已有 {len(duplicate_existing)} 条",
    )
    if not candidates:
        emit_progress(progress, "没有新的候选内容")
        typer.echo("No new candidates found.")
        typer.echo(f"Skipped existing sources: {len(duplicate_existing)}")
        return
    emit_progress(progress, f"正在评分 {len(candidates)} 条候选")
    scored_candidates = [
        score_candidate(
            classify_candidate_topics(candidate, settings.topics),
            settings.topics,
            settings.scoring,
        )
        for candidate in candidates
    ]
    daily_config = settings.app.get("daily", {})
    primary_candidates = [
        candidate for candidate in scored_candidates if candidate.source_kind != "chinese_media"
    ]
    media_candidates = select_top_media_candidates(
        [
            candidate
            for candidate in scored_candidates
            if candidate.source_kind == "chinese_media"
        ],
        media_quota=int(daily_config.get("media_quota", 5)),
    )
    candidates = select_top_candidates(
        primary_candidates,
        max_cards=settings.max_cards,
        academic_quota=int(daily_config.get("academic_quota", 3)),
        industry_quota=int(daily_config.get("industry_quota", 2)),
    )
    candidates.extend(media_candidates)
    emit_progress(
        progress,
        f"已入选 {len(candidates)} 条（主候选 {len(candidates) - len(media_candidates)} 条，来自媒体 {len(media_candidates)} 条）",
    )
    report_path = write_candidate_report(
        settings.markdown_root,
        run_day,
        scored_candidates,
        candidates,
        collection_warnings,
        skipped_existing=len(duplicate_existing),
        dry_run=dry_run,
    )
    typer.echo(f"Candidate report: {report_path}")
    typer.echo("Selected candidates:")
    for candidate in candidates:
        typer.echo(
            f"- [{candidate.track}] {candidate.title} "
            f"(score={candidate.score:.1f}, source={candidate.source_kind}, topics={','.join(candidate.topics)})"
        )
        if dry_run:
            typer.echo(f"  {candidate.url}")
    if dry_run:
        emit_progress(progress, f"预跑完成：入选 {len(candidates)} 条，跳过已有 {len(duplicate_existing)} 条")
        typer.echo(f"Dry run complete: selected={len(candidates)}, skipped_existing={len(duplicate_existing)}")
        return

    llm = _llm_client(settings)
    created = 0
    skipped = len(duplicate_existing)
    generation_candidates = candidates_for_generation(candidates)
    media_total = sum(
        1 for candidate in generation_candidates if candidate.source_kind == "chinese_media"
    )
    if media_total:
        typer.echo(f"Generating media cards first: media={media_total}, total={len(generation_candidates)}")
    total_to_generate = len(generation_candidates)
    for index, candidate in enumerate(generation_candidates, start=1):
        card_kind = "媒体" if candidate.source_kind == "chinese_media" else "主候选"
        emit_progress(
            progress,
            f"正在生成第 {index}/{total_to_generate} 张{card_kind}卡片：{candidate.title[:48]}",
        )
        try:
            metadata = build_card_metadata(candidate, run_day, settings.timezone)
            source_document = None
            try:
                source_document = fetch_source_document(candidate.parent_url or candidate.url)
                if source_document.title and candidate.title == candidate.url:
                    metadata["title_en"] = source_document.title
            except Exception as exc:
                typer.echo(f"warning: failed to fetch {candidate.url}: {exc}", err=True)
            content = None
            if llm.available:
                try:
                    content = llm.generate_card_content(_prompt_for_candidate(candidate, source_document))
                except Exception as exc:
                    typer.echo(f"warning: failed to generate content for {candidate.url}: {exc}", err=True)
            content = clean_llm_markdown(content) or build_placeholder_content(candidate)
            metadata = apply_content_date(metadata, candidate, content)
            metadata["title_zh"] = infer_title_zh(content, metadata.get("title_zh", ""))
            card_day = date.fromisoformat(str(metadata["date"]))
            path = card_path(settings.markdown_root, card_day, metadata["id"])
            if path.exists():
                skipped += 1
                emit_progress(progress, f"已跳过第 {index}/{total_to_generate} 张：卡片已存在")
                continue
            write_card(path, metadata, content)
            created += 1
            emit_progress(progress, f"已完成 {created}/{total_to_generate} 张：{metadata.get('title_zh') or candidate.title}")
            typer.echo(f"created {path}")
        except Exception as exc:
            typer.echo(f"warning: failed to write card for {candidate.url}: {exc}", err=True)
            skipped += 1
            emit_progress(progress, f"第 {index}/{total_to_generate} 张生成失败，继续处理下一条")
            continue
    emit_progress(progress, "正在重建索引")
    indexed, warnings = rebuild_index(settings.markdown_root, settings.sqlite_path)
    emit_progress(progress, "正在自动审核超过 1 天未处理的卡片")
    auto_decisions = run_auto_review_if_enabled(settings, run_day, dry_run=False)
    if auto_decisions:
        emit_progress(progress, f"自动审核 {len(auto_decisions)} 张卡片，正在刷新索引")
        indexed, warnings = rebuild_index(settings.markdown_root, settings.sqlite_path)
    emit_progress(progress, f"整理完成：新建 {created} 张，跳过 {skipped} 条，索引 {indexed} 张")
    typer.echo(f"Daily complete: created={created}, skipped={skipped}, indexed={indexed}")
    if auto_decisions:
        typer.echo(f"Auto-reviewed stale cards: {len(auto_decisions)}")
        for decision in auto_decisions:
            typer.echo(
                f"- {decision.status}: {decision.title} "
                f"(score={decision.score}, age={decision.age_days}d)"
            )
    for warning in warnings:
        typer.echo(f"warning: {warning}", err=True)


@app.command("auto-review")
def auto_review(
    day: Annotated[
        str | None,
        typer.Option("--date", help="Run date YYYY-MM-DD. Defaults to today."),
    ] = None,
    dry_run: Annotated[
        bool,
        typer.Option("--dry-run", help="Evaluate stale cards without changing review_status."),
    ] = False,
) -> None:
    """Auto-review needs-review cards that have been waiting longer than the configured threshold."""
    settings = _settings()
    run_day = date.fromisoformat(day) if day else today_in_timezone(settings.timezone)
    decisions = auto_review_stale_cards(
        settings.markdown_root,
        settings.topics,
        settings.app.get("review", {}),
        run_day,
        settings.timezone,
        dry_run=dry_run,
    )
    record_auto_review_feedback(settings, decisions, dry_run=dry_run)
    if not decisions:
        typer.echo("No stale needs-review cards to auto-review.")
        return
    for decision in decisions:
        prefix = "would update" if dry_run else "updated"
        typer.echo(
            f"{prefix}: {decision.status} {decision.path} "
            f"(score={decision.score}, age={decision.age_days}d)"
        )
        typer.echo(f"  reasons: {'; '.join(decision.reasons)}")
    if not dry_run:
        indexed, warnings = rebuild_index(settings.markdown_root, settings.sqlite_path)
        typer.echo(f"Auto-review complete: updated={len(decisions)}, indexed={indexed}")
        for warning in warnings:
            typer.echo(f"warning: {warning}", err=True)


@app.command("propose-sources")
def propose_sources() -> None:
    """Generate source proposals from existing accepted cards and source diagnostics."""
    settings = _settings()
    output_path = generate_source_proposals(settings)
    typer.echo(f"Source proposals written: {output_path}")


@app.command("extract-features")
def extract_features(
    surface: Annotated[
        str,
        typer.Option("--surface", help="cards, ppt_suggestions, source_proposals, or all."),
    ] = "all",
) -> None:
    """Extract deterministic v1 features for future preference models."""
    settings = _settings()
    output_paths = extract_preference_features(settings, surface=surface)
    for output_path in output_paths:
        typer.echo(f"Preference features written: {output_path}")


def run_auto_review_if_enabled(settings: Settings, run_day: date, dry_run: bool = False):
    review_config = settings.app.get("review", {})
    auto_config = review_config.get("auto", {})
    if not bool(auto_config.get("enabled", True)):
        return []
    decisions = auto_review_stale_cards(
        settings.markdown_root,
        settings.topics,
        review_config,
        run_day,
        settings.timezone,
        dry_run=dry_run,
    )
    record_auto_review_feedback(settings, decisions, dry_run=dry_run)
    return decisions


def record_auto_review_feedback(settings: Settings, decisions, dry_run: bool = False) -> None:
    if dry_run:
        return
    for decision in decisions:
        append_feedback_event(
            settings.root,
            settings.timezone,
            "auto_card_review",
            "card",
            decision.card_id,
            decision.status,
            actor="auto",
            previous_status="needs-review",
            new_status=decision.status,
            source="auto-review",
            metadata={
                "title": decision.title,
                "path": str(decision.path),
                "score": decision.score,
                "age_days": decision.age_days,
                "reasons": decision.reasons,
            },
        )


@app.command()
def review(
    status: Annotated[
        str | None,
        typer.Option("--status", help="Apply this status to all listed cards."),
    ] = None,
    open_source: Annotated[
        bool,
        typer.Option("--open-source", help="Open each source URL with xdg-open."),
    ] = False,
) -> None:
    """Review needs-review cards from the terminal."""
    settings = _settings()
    paths = needs_review_cards(settings.markdown_root)
    if not paths:
        typer.echo("No needs-review cards.")
        return
    if status and status not in settings.review_statuses:
        raise typer.BadParameter(f"status must be one of: {', '.join(settings.review_statuses)}")
    for path in paths:
        card = read_card(path)
        typer.echo("")
        typer.echo(f"Card: {path}")
        typer.echo(f"Title: {card.metadata.get('title_zh') or card.metadata.get('title_en')}")
        typer.echo(f"Source: {card.metadata.get('source_url')}")
        if open_source and card.metadata.get("source_url"):
            subprocess.run(["xdg-open", card.metadata["source_url"]], check=False)
        next_status = status
        if not next_status:
            next_status = typer.prompt(
                "accept/later/reject/skip",
                default="skip",
            )
            if next_status == "accept":
                next_status = "accepted"
        if next_status == "skip":
            continue
        if next_status not in settings.review_statuses:
            typer.echo(f"Invalid status: {next_status}")
            continue
        previous_status = str(card.metadata.get("review_status", ""))
        set_review_status(path, next_status)
        append_feedback_event(
            settings.root,
            settings.timezone,
            "card_review",
            "card",
            str(card.metadata.get("id", path.stem)),
            next_status,
            previous_status=previous_status,
            new_status=next_status,
            source="cli",
            metadata={
                "title": card.metadata.get("title_zh") or card.metadata.get("title_en"),
                "source_url": card.metadata.get("source_url"),
                "source_type": card.metadata.get("source_type"),
                "topics": card.metadata.get("topics", []),
            },
        )
        typer.echo(f"updated review_status={next_status}")
    indexed, warnings = rebuild_index(settings.markdown_root, settings.sqlite_path)
    typer.echo(f"Review complete: indexed={indexed}")
    for warning in warnings:
        typer.echo(f"warning: {warning}", err=True)


def collect_daily_candidates(
    settings: Settings,
    manual_only: bool = False,
    progress: ProgressCallback | None = None,
) -> tuple[list[Candidate], list[str]]:
    warnings: list[str] = []
    daily_config = settings.app.get("daily", {})
    candidate_limit = int(daily_config.get("candidate_limit", 50))
    arxiv_config = settings.sources.get("sources", {}).get("arxiv", {})
    rss_config = settings.sources.get("sources", {}).get("rss", {})
    company_config = settings.sources.get("sources", {}).get("company_blogs", {})
    source_steps = ["手工链接"]
    if not manual_only:
        if arxiv_config.get("enabled", False):
            source_steps.append("arXiv")
        if rss_config.get("enabled", False):
            source_steps.append("RSS")
        if company_config.get("enabled", False):
            source_steps.append("公司/媒体网页")
    step_total = len(source_steps)
    step_index = 1
    emit_progress(progress, f"正在采集消息源 {step_index}/{step_total}：手工链接")
    candidates: list[Candidate] = [
        candidate_from_manual(candidate)
        for candidate in dedupe_by_url(read_manual_urls(settings.manual_urls_path))
    ]
    emit_progress(progress, f"手工链接候选 {len(candidates)} 条")
    if manual_only:
        return candidates, warnings

    if arxiv_config.get("enabled", False):
        step_index += 1
        emit_progress(progress, f"正在采集消息源 {step_index}/{step_total}：arXiv")
        try:
            arxiv_documents = search_latest_arxiv(
                arxiv_config.get("categories", []),
                max_results=min(int(arxiv_config.get("max_results_per_day", 10)), candidate_limit),
            )
            candidates.extend(candidate_from_arxiv_document(document) for document in arxiv_documents)
            emit_progress(progress, f"arXiv 候选 {len(arxiv_documents)} 条")
        except Exception as exc:
            warnings.append(f"arXiv latest: {exc}")
            emit_progress(progress, f"arXiv 采集失败：{exc}")

    if rss_config.get("enabled", False):
        step_index += 1
        feeds = feeds_from_settings(settings.sources)
        emit_progress(progress, f"正在采集消息源 {step_index}/{step_total}：RSS（{len(feeds)} 个订阅）")
        rss_items, rss_warnings = fetch_all_rss_feeds(
            feeds,
            max_per_feed=3,
            timeout=8,
        )
        warnings.extend(f"RSS {warning}" for warning in rss_warnings)
        candidates.extend(candidate_from_rss_item(item) for item in rss_items)
        emit_progress(progress, f"RSS 候选 {len(rss_items)} 条，警告 {len(rss_warnings)} 条")

    if company_config.get("enabled", False):
        step_index += 1
        sources = company_blogs_from_settings(settings.sources)
        emit_progress(progress, f"正在采集消息源 {step_index}/{step_total}：公司/媒体网页（{len(sources)} 个来源）")
        company_items, company_warnings = fetch_all_company_blogs(
            sources,
            max_per_source=3,
            timeout=8,
        )
        warnings.extend(f"Company {warning}" for warning in company_warnings)
        company_candidates = [candidate_from_company_item(item) for item in company_items]
        emit_progress(progress, f"网页候选 {len(company_candidates)} 条，正在拆解媒体摘要")
        expanded_company_candidates = expand_digest_candidates(
            company_candidates,
            warnings,
            progress=progress,
        )
        candidates.extend(expanded_company_candidates)
        emit_progress(progress, f"网页/媒体候选 {len(expanded_company_candidates)} 条，警告 {len(company_warnings)} 条")

    emit_progress(progress, f"正在去重候选池：原始候选 {len(candidates)} 条")
    unique_candidates = dedupe_by_url_compatible(candidates)
    if len(unique_candidates) > candidate_limit:
        warnings.append(
            f"candidate pool has {len(unique_candidates)} unique items; scoring all before final selection"
        )
    emit_progress(progress, f"候选池去重完成：{len(unique_candidates)} 条")
    return unique_candidates, warnings


def expand_digest_candidates(
    candidates: list[Candidate],
    warnings: list[str],
    progress: ProgressCallback | None = None,
) -> list[Candidate]:
    expanded: list[Candidate] = []
    digest_candidates_to_split = [
        candidate for candidate in candidates if should_split_digest(candidate)
    ]
    digest_total = len(digest_candidates_to_split)
    digest_index = 0
    for candidate in candidates:
        if not should_split_digest(candidate):
            expanded.append(candidate)
            continue
        digest_index += 1
        emit_progress(progress, f"正在拆解媒体摘要 {digest_index}/{digest_total}：{candidate.title[:48]}")
        try:
            document = fetch_source_document(candidate.url, timeout=12)
        except Exception as exc:
            warnings.append(f"Digest {candidate.source_name} {candidate.url}: {exc}")
            emit_progress(progress, f"媒体摘要拆解失败：{candidate.source_name}")
            continue
        digest_candidates = expand_digest_candidate(candidate, document)
        if len(digest_candidates) == 1 and digest_candidates[0] == candidate:
            warnings.append(f"Digest {candidate.source_name} {candidate.url}: no digest items found")
            emit_progress(progress, f"媒体摘要未拆出条目：{candidate.source_name}")
            continue
        expanded.extend(digest_candidates)
        emit_progress(progress, f"媒体摘要拆出 {len(digest_candidates)} 条：{candidate.source_name}")
    return expanded


def dedupe_by_url_compatible(candidates: list[Candidate]) -> list[Candidate]:
    from ai_daily_update.processors.dedupe import dedupe_items

    return dedupe_items(candidates).unique


@app.command("index")
def index_command() -> None:
    """Rebuild the SQLite index from Markdown cards."""
    settings = _settings()
    indexed, warnings = rebuild_index(settings.markdown_root, settings.sqlite_path)
    typer.echo(f"Indexed {indexed} card(s).")
    for warning in warnings:
        typer.echo(f"warning: {warning}", err=True)


@app.command()
def brief(
    from_date: Annotated[str, typer.Option("--from-date", help="Start date YYYY-MM-DD.")],
    to_date: Annotated[str, typer.Option("--to-date", help="End date YYYY-MM-DD.")],
    topics: Annotated[
        str | None,
        typer.Option("--topics", help="Comma-separated topic ids."),
    ] = None,
    audience: Annotated[
        str,
        typer.Option("--audience", help="academic, industry, book, or public."),
    ] = "academic",
    date_basis: Annotated[
        str,
        typer.Option("--date-basis", help="collected or event."),
    ] = "collected",
) -> None:
    """Generate a Markdown brief from accepted cards."""
    settings = _settings()
    topic_list = [topic.strip() for topic in topics.split(",") if topic.strip()] if topics else None
    output_path = generate_brief(
        settings.sqlite_path,
        settings.markdown_root,
        from_date,
        to_date,
        topic_list,
        audience,
        date_basis=date_basis,
    )
    typer.echo(f"Brief written: {output_path}")


@app.command("arxiv-latest")
def arxiv_latest(
    categories: Annotated[
        str | None,
        typer.Option("--categories", help="Comma-separated arXiv categories."),
    ] = None,
    max_results: Annotated[
        int,
        typer.Option("--max-results", help="Maximum papers to fetch."),
    ] = 5,
    from_date: Annotated[
        str | None,
        typer.Option("--from-date", help="Optional start date YYYY-MM-DD."),
    ] = None,
    to_date: Annotated[
        str | None,
        typer.Option("--to-date", help="Optional end date YYYY-MM-DD."),
    ] = None,
) -> None:
    """Fetch latest arXiv papers by submitted date."""
    settings = _settings()
    configured_categories = (
        settings.sources.get("sources", {}).get("arxiv", {}).get("categories", [])
    )
    category_list = (
        [item.strip() for item in categories.split(",") if item.strip()]
        if categories
        else configured_categories
    )
    if not category_list:
        raise typer.BadParameter("No arXiv categories configured or supplied.")
    documents = search_latest_arxiv(
        category_list,
        max_results=max_results,
        from_date=date.fromisoformat(from_date) if from_date else None,
        to_date=date.fromisoformat(to_date) if to_date else None,
    )
    for index, document in enumerate(documents, start=1):
        first_lines = document.text.splitlines()
        published = next((line for line in first_lines if line.startswith("Published:")), "")
        categories_line = next((line for line in first_lines if line.startswith("Categories:")), "")
        typer.echo(f"{index}. {document.title}")
        typer.echo(f"   {document.url}")
        if published:
            typer.echo(f"   {published}")
        if categories_line:
            typer.echo(f"   {categories_line}")


@app.command("rss-latest")
def rss_latest(
    max_per_feed: Annotated[
        int,
        typer.Option("--max-per-feed", help="Maximum entries to show per feed."),
    ] = 5,
    timeout: Annotated[
        int,
        typer.Option("--timeout", help="Timeout per RSS feed in seconds."),
    ] = 8,
) -> None:
    """Fetch latest items from configured RSS feeds."""
    settings = _settings()
    feeds = feeds_from_settings(settings.sources)
    if not feeds:
        typer.echo("No RSS feeds configured.")
        return
    items, warnings = fetch_all_rss_feeds(feeds, max_per_feed=max_per_feed, timeout=timeout)
    for warning in warnings:
        typer.echo(f"warning: {warning}", err=True)
    if not items:
        typer.echo("No RSS items fetched.")
        return
    for index, item in enumerate(items, start=1):
        typer.echo(f"{index}. [{item.feed_name}] {item.title}")
        typer.echo(f"   {item.url}")
        if item.published:
            typer.echo(f"   Published: {item.published}")
        if item.summary:
            typer.echo(f"   {item.summary[:240]}")


@app.command("company-latest")
def company_latest(
    max_per_source: Annotated[
        int,
        typer.Option("--max-per-source", help="Maximum entries to show per company."),
    ] = 5,
    timeout: Annotated[
        int,
        typer.Option("--timeout", help="Timeout per company page in seconds."),
    ] = 8,
) -> None:
    """Fetch latest-looking posts from configured company blog pages."""
    settings = _settings()
    sources = company_blogs_from_settings(settings.sources)
    if not sources:
        typer.echo("No company blog sources configured.")
        return
    items, warnings = fetch_all_company_blogs(
        sources, max_per_source=max_per_source, timeout=timeout
    )
    for warning in warnings:
        typer.echo(f"warning: {warning}", err=True)
    if not items:
        typer.echo("No company blog items fetched.")
        return
    for index, item in enumerate(items, start=1):
        typer.echo(f"{index}. [{item.source_name}] {item.title}")
        typer.echo(f"   {item.url}")


def clean_llm_markdown(content: str | None) -> str | None:
    if not content:
        return content
    stripped = content.strip()
    if stripped.startswith("```"):
        lines = stripped.splitlines()
        if lines and lines[0].startswith("```") and lines[-1].strip() == "```":
            return "\n".join(lines[1:-1]).strip() + "\n"
    return content


def existing_card_source_urls(markdown_root: Path) -> set[str]:
    urls: set[str] = set()
    for path in iter_existing_card_paths(markdown_root):
        card = read_card(path)
        source_url = card.metadata.get("source_url")
        if source_url:
            urls.add(normalize_url_for_dedupe(str(source_url)))
    return urls


def iter_existing_card_paths(markdown_root: Path) -> list[Path]:
    paths = list(iter_cards(markdown_root))
    trash_root = markdown_root / "trash"
    if trash_root.exists():
        paths.extend(sorted(trash_root.rglob("*.md")))
    return paths


if __name__ == "__main__":
    app()
