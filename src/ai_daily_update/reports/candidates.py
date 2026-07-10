from __future__ import annotations

from datetime import date
from pathlib import Path

from ai_daily_update.processors.candidates import Candidate


def write_candidate_report(
    markdown_root: Path,
    day: date,
    candidates: list[Candidate],
    selected: list[Candidate],
    warnings: list[str],
    skipped_existing: int,
    dry_run: bool = False,
) -> Path:
    selected_urls = {candidate.url for candidate in selected}
    output_dir = markdown_root / "inbox"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"{day.isoformat()}-candidates.md"
    lines = [
        f"# 每日候选池：{day.isoformat()}",
        "",
        "## 摘要",
        "",
        f"- 运行模式：{'预跑候选（未生成卡片）' if dry_run else '正式生成'}",
        f"- 去重后候选数：{len(candidates)}",
        f"- 入选生成卡片：{len(selected)}",
        f"- 跳过已有来源：{skipped_existing}",
        f"- 警告数量：{len(warnings)}",
        "",
    ]
    if warnings:
        lines.extend(["## 警告", ""])
        for warning in warnings:
            lines.append(f"- {warning}")
        lines.append("")
    lines.extend(["## 入选候选", ""])
    if not selected:
        lines.append("没有入选候选。")
        lines.append("")
    for candidate in selected:
        lines.extend(candidate_lines(candidate, selected=True, dry_run=dry_run))
    lines.extend(["## 全部候选", ""])
    if not candidates:
        lines.append("没有收集到候选。")
        lines.append("")
    for candidate in sorted(candidates, key=lambda item: item.score, reverse=True):
        lines.extend(candidate_lines(candidate, selected=candidate.url in selected_urls, dry_run=dry_run))
    output_path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    return output_path


def candidate_lines(candidate: Candidate, selected: bool, dry_run: bool = False) -> list[str]:
    selected_label = "拟入选（未生成）" if dry_run else "已入选"
    return [
        f"### {selected_label if selected else '未入选'}：{candidate.title}",
        "",
        f"- URL：{candidate.url}",
        f"- 通道：{candidate.track}",
        f"- 主题：{', '.join(candidate.topics)}",
        f"- 来源：{candidate.source_kind} / {candidate.source_name}",
        f"- 发布时间：{candidate.published or 'unknown'}",
        f"- 分数：{candidate.score:.1f}",
        f"- 评分理由：{', '.join(candidate.score_reasons) or 'none'}",
        "",
    ]
