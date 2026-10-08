"""Audit the authoring Wiki and export only teacher-reviewed learning material.

Run `python scripts/export_learning_content.py --audit` before editing. The
default export refuses an incomplete corpus. No textbook document is copied.
"""

from __future__ import annotations

import argparse
import json
import re
from datetime import date
from pathlib import Path

import frontmatter


ROOT = Path(__file__).resolve().parents[1]
WIKI = ROOT / "AI-introduction" / "AI-introduction" / "wiki"
DESTINATION = ROOT / "content" / "learning" / "catalog.json"
EXPECTED = {"concepts": 90, "microtopics": 189, "synthesis": 8}
TEACHING_FIELDS = ("explanation", "example", "misconception", "question", "answer")


def collect() -> tuple[list[dict], list[str]]:
    items: list[dict] = []
    issues: list[str] = []
    for folder, count in EXPECTED.items():
        pages = [(path, frontmatter.load(path)) for path in sorted((WIKI / folder).glob("*.md"))]
        included = [(path, post) for path, post in pages if post.get("learning_catalog") is not False]
        if len(included) != count:
            issues.append(f"{folder}: expected {count} pages, found {len(included)}")
        for path, post in included:
            data = dict(post.metadata)
            item_type = "concept" if folder == "concepts" else "microtopic" if folder == "microtopics" else "synthesis"
            item_id = f"{item_type}:{path.stem}"
            required = ("title", "source_section", "reviewed_by", "reviewed_at", "aliases", "formula_checked", "figures_checked")
            if item_type != "synthesis":
                required += TEACHING_FIELDS + ("prerequisites",)
            missing = [key for key in required if data.get(key) is None or data.get(key) == ""]
            if data.get("review_status") != "reviewed":
                missing.append("review_status=reviewed")
            if data.get("formula_checked") is not True or data.get("figures_checked") is not True:
                missing.append("formula/figure verification")
            if missing:
                issues.append(f"{path.relative_to(WIKI)}: {', '.join(missing)}")
                continue
            if not isinstance(data["aliases"], list):
                issues.append(f"{path.relative_to(WIKI)}: aliases must be a list")
                continue
            prerequisites = data.get("prerequisites", {})
            if item_type != "synthesis" and (
                not isinstance(prerequisites, dict)
                or any(not isinstance(prerequisites.get(group), list) for group in ("required", "helpful", "advanced"))
            ):
                issues.append(f"{path.relative_to(WIKI)}: prerequisites must have required/helpful/advanced lists")
                continue
            try:
                date.fromisoformat(str(data["reviewed_at"]))
            except ValueError:
                issues.append(f"{path.relative_to(WIKI)}: invalid reviewed_at")
                continue
            item = {
                "id": item_id,
                "type": item_type,
                "title": str(data["title"]),
                "aliases": data["aliases"],
                "source_section": str(data["source_section"]),
                "review_status": "reviewed",
                "reviewed_by": str(data["reviewed_by"]),
                "reviewed_at": str(data["reviewed_at"]),
            }
            if item_type != "synthesis":
                item.update({key: str(data[key]) for key in TEACHING_FIELDS})
                item["prerequisites"] = prerequisites
            else:
                item["overview"] = str(data.get("overview", ""))
            items.append(item)

    ids = {item["id"] for item in items}
    if len(ids) != len(items):
        issues.append("Duplicate stable IDs")
    for item in items:
        for group, targets in item.get("prerequisites", {}).items():
            for target in targets:
                if target not in ids or not target.startswith("concept:"):
                    issues.append(f"{item['id']}: invalid {group} target {target}")
    graph = {item["id"]: item.get("prerequisites", {}).get("required", []) for item in items if item["type"] == "concept"}
    seen: set[str] = set()
    active: set[str] = set()

    def visit(node: str) -> None:
        if node in active:
            issues.append(f"Required prerequisite cycle at {node}")
            return
        if node in seen or node not in graph:
            return
        active.add(node)
        for target in graph[node]:
            visit(target)
        active.remove(node)
        seen.add(node)

    for item_id in graph:
        visit(item_id)
    return items, issues


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--audit", action="store_true", help="Report readiness without writing")
    args = parser.parse_args()
    items, issues = collect()
    print(f"reviewed={len(items)} expected={sum(EXPECTED.values())} issues={len(issues)}")
    for issue in issues[:30]:
        print(issue)
    if len(issues) > 30:
        print(f"... {len(issues) - 30} more issues")
    if args.audit:
        return 0
    if issues:
        print("Export refused: complete the teacher review first.")
        return 1
    DESTINATION.parent.mkdir(parents=True, exist_ok=True)
    DESTINATION.write_text(json.dumps({"complete": True, "items": items}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Exported {DESTINATION}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
