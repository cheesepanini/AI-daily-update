"""Locate PDF formula and figure evidence, then clear only visual-free draft pages."""

from __future__ import annotations

import json
import re
from collections import defaultdict
from pathlib import Path
from urllib.parse import quote

import frontmatter
import pymupdf

from audit_learning_pdf import ROOT, SOURCE, WIKI, source_lines


MATH = re.compile(r"[=<>≤≥∑∂√×÷λθπ∞≈±→∫∪∩]|（[1-8][.][0-9]+）")
FIGURE = re.compile(r"图\s*[1-8][.][0-9]+")
TABLE = re.compile(r"表\s*[1-8][.][0-9]+")


def main() -> None:
    audit = json.loads((ROOT / "docs" / "learning-source-audit.json").read_text(encoding="utf-8"))
    pdf = pymupdf.open(SOURCE)
    lines = source_lines(pdf)
    images = {number: [item["bbox"] for item in pdf[number - 1].get_image_info()] for number in range(16, len(pdf) + 1)}
    height = {}

    def y(index: int) -> float:
        if index not in height:
            row = lines[index]
            rects = pdf[row["page"] - 1].search_for(row["text"])
            if not rects:
                raise ValueError(f"PDF heading not found: {row}")
            height[index] = min(rect.y0 for rect in rects)
        return height[index]

    def span_images(start: int, end: int) -> list[tuple[int, tuple]]:
        first = lines[start]["page"]
        last = lines[end]["page"] if end < len(lines) else len(pdf)
        start_y = y(start)
        end_y = y(end) if end < len(lines) else 740
        if first == last and start_y >= end_y:
            raise ValueError(f"Reversed PDF bounds: {start}..{end}")
        found = []
        for number in range(first, last + 1):
            low = max(95, start_y if number == first else 95)
            high = min(740, end_y if number == last else 740)
            found.extend((number, box) for box in images[number] if box[3] > low and box[1] < high and box[2] > 60 and box[0] < 610)
        return found

    def evidence(start: int, end: int) -> dict:
        text = "".join(row["text"] for row in lines[start + 1:end])
        embedded = span_images(start, end)
        content_pages = [lines[start]["page"]] + [row["page"] for row in lines[start + 1:end]] + [number for number, _ in embedded]
        return {
            "pdf_physical_pages": [lines[start]["page"], max(content_pages)],
            "image_objects": len(embedded),
            "math_text_or_equation_number": bool(MATH.search(text)),
            "figure_mentions": sorted(set(FIGURE.findall(text))),
            "table_mentions": sorted(set(TABLE.findall(text))),
        }

    def has_visual(row: dict) -> bool:
        return bool(row["image_objects"] or row["math_text_or_equation_number"] or row["figure_mentions"] or row["table_mentions"])

    points = {}
    points_by_ref = defaultdict(list)
    for name, (start, end) in audit["point_line_ranges"].items():
        row = evidence(start, end)
        row["source_section"] = re.match(r"[1-8]\.[1-9]\d?\.[1-9]\d?", Path(name).name).group()
        row["path"] = name
        row["formula_placeholder"] = "【公式见教材原文】" in (WIKI / name).read_text(encoding="utf-8")
        points[name] = row
        points_by_ref[row["source_section"]].append((start, end))

    sections = {}
    for section in audit["pdf_sections"]:
        ref = section["ref"]
        start, end = section["start"], section["end"]
        row = evidence(start, end)
        uncovered_text = any(
            MATH.search(lines[index]["text"]) or FIGURE.search(lines[index]["text"]) or TABLE.search(lines[index]["text"])
            for index in range(start + 1, end)
            if not any(a <= index < b for a, b in points_by_ref.get(ref, []))
        )
        covered_images = {(number, tuple(box)) for a, b in points_by_ref.get(ref, []) for number, box in span_images(a, b)}
        uncovered_images = any((number, tuple(box)) not in covered_images for number, box in span_images(start, end))
        row.update({"ref": ref, "uncovered_visual_outside_points": bool(uncovered_text or uncovered_images)})
        sections[ref] = row

    cleared = []
    newly_marked = 0
    unprepared = []
    concept_extra = defaultdict(list)
    for check in audit["page_checks"]:
        path = WIKI / check["path"]
        content = path.read_text(encoding="utf-8")
        if check["type"] == "microtopics":
            safe = not has_visual(points[check["path"]])
        elif check["type"] == "concepts":
            refs = re.findall(r"[1-8]\.[1-9]\d?(?:\.[1-9]\d?)?", check["source_section"])
            safe = all(not has_visual(sections[ref]) for ref in refs)
            for ref in refs:
                if sections[ref]["uncovered_visual_outside_points"]:
                    concept_extra[ref].append(check["path"])
        else:
            safe = True
        body = re.sub(r"\]\([^)]*\)", "]", frontmatter.loads(content).content)
        body = re.sub(r"(?m)^> ?", "", body)
        safe = safe and not bool(re.search(r"!\[|<img|<svg|\$|[=<>≤≥∑∂√×÷λθπ∞≈±]", body))
        if safe:
            if check["review_status"] == "draft":
                false_pair = content.count("formula_checked: false") == 1 and content.count("figures_checked: false") == 1
                true_pair = content.count("formula_checked: true") == 1 and content.count("figures_checked: true") == 1
                if not (false_pair or true_pair):
                    unprepared.append(check["path"])
                    continue
                if false_pair:
                    path.write_text(content.replace("formula_checked: false", "formula_checked: true").replace("figures_checked: false", "figures_checked: true"), encoding="utf-8")
                    newly_marked += 1
            cleared.append(check["path"])

    result = {
        "source": audit["source"],
        "source_sha256": audit["source_sha256"],
        "physical_pdf_pages": len(pdf),
        "points": points,
        "sections": sections,
        "machine_no_visual_pages": cleared,
        "unprepared_pages": unprepared,
        "concept_extra_sections": dict(concept_extra),
    }
    (ROOT / "docs" / "learning-visual-audit.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    pdf_link = quote("../AI-introduction/AI-introduction/raw/sources/" + SOURCE.name, safe="/.-_")
    report = [
        "# PDF 公式与图表定向复核清单",
        "",
        "基准：最新版 292 页《人工智能导论》PDF。以下页码均为**PDF 物理页码**，不是书内印刷页码。",
        "PDF 中文正文可提取，但公式符号有部分作为图片对象嵌入；清单以点位版面范围、图片对象、数学符号、公式编号和图表提及保守筛选。",
        "",
        f"189 个细知识点中，{sum(has_visual(row) for row in points.values())} 个来源范围有视觉证据。另有 {len(concept_extra)} 个章节位置含未被细卡片范围覆盖的视觉证据。",
        f"{len(cleared)} 页对应来源范围未发现需要转录的公式、图片、图表或数学符号；人工视觉复核范围与结果见[最小人工待办](learning-human-handoff.md)。",
        "",
        "## 细知识点来源位置",
        "",
        "| 原文位置 | 知识库卡片 | PDF 物理页 | 图片对象 | 数学/公式 | 图/表号 |",
        "| --- | --- | ---: | ---: | --- | --- |",
    ]
    for name, row in sorted(points.items(), key=lambda item: tuple(map(int, item[1]["source_section"].split("."))) + (int(re.search(r"内部第(\d+)点", next(check["source_section"] for check in audit["page_checks"] if check["path"] == item[0])).group(1)),)):
        if not has_visual(row):
            continue
        start, end = row["pdf_physical_pages"]
        pages = str(start) if start == end else f"{start}–{end}"
        link = f"{pdf_link}#page={start}"
        card = quote("../AI-introduction/AI-introduction/wiki/" + name, safe="/.-_")
        refs = "/".join(row["figure_mentions"] + row["table_mentions"]) or "—"
        report.append(f"| {row['source_section']} | [{Path(name).stem}]({card}) | [{pages}]({link}) | {row['image_objects']} | {'是' if row['math_text_or_equation_number'] else '—'} | {refs} |")
    report.extend(["", "## 细卡片范围之外的章节位置", "", "| 原文小节 | PDF 物理页 | 相关概念页 |", "| --- | ---: | --- |"])
    for ref, names in sorted(concept_extra.items(), key=lambda item: tuple(map(int, item[0].split(".")))):
        row = sections[ref]
        start, end = row["pdf_physical_pages"]
        pages = str(start) if start == end else f"{start}–{end}"
        cards = "、".join(f"[{Path(name).stem}]({quote('../AI-introduction/AI-introduction/wiki/' + name, safe='/.-_')})" for name in sorted(set(names)))
        report.append(f"| {ref} | [{pages}]({pdf_link}#page={start}) | {cards} |")
    (ROOT / "docs" / "learning-visual-review.md").write_text("\n".join(report) + "\n", encoding="utf-8")
    print(json.dumps({"point_visual": sum(has_visual(row) for row in points.values()), "concept_extra_sections": len(concept_extra), "machine_clear": len(cleared), "newly_marked": newly_marked}, ensure_ascii=False))


if __name__ == "__main__":
    main()
