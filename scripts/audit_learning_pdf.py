"""Compare learning Wiki pages with the latest typeset textbook PDF."""

from __future__ import annotations

import json
import hashlib
import re
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path
from urllib.parse import unquote

import frontmatter
import pymupdf


ROOT = Path(__file__).resolve().parents[1]
WIKI = ROOT / "AI-introduction" / "AI-introduction" / "wiki"
SOURCE = ROOT / "AI-introduction" / "AI-introduction" / "raw" / "sources" / "117145-01  人工智能导论(4)(1).pdf"
SOURCE_REF = f"raw/sources/{SOURCE.name}"
SECTION = re.compile(r"^([1-8]\.[1-9]\d?(?:\.[1-9]\d?)?)[ \u2003]+(.{1,30})$")
POINT = re.compile(r"^([1-9]\d?)．\s*(.{1,90})$")
END_MARKERS = {"本章小结", "本章习题", "习题", "思考题", "参考文献"}


def compact(value: str) -> str:
    return re.sub(r"\s+", "", unicodedata.normalize("NFKC", value))


def source_lines(pdf: pymupdf.Document) -> list[dict]:
    lines = []
    for index in range(15, len(pdf)):
        for line in pdf[index].get_text().splitlines():
            value = line.strip()
            if not value or value.startswith("CBDC_") or re.match(r"^2026/\d+/\d+", value):
                continue
            if value == "人工智能导论" or re.fullmatch(r"\d{1,3}", value):
                continue
            if re.match(r"^第[1-8] 章\s", value) and "\u2003" in value:
                continue
            lines.append({"page": index + 1, "text": value})
    return lines


def index_sections(lines: list[dict]) -> tuple[list[dict], dict]:
    sections = []
    for index, row in enumerate(lines):
        match = SECTION.fullmatch(row["text"])
        if match and not match.group(2).startswith("节"):
            sections.append({"ref": match.group(1), "title": match.group(2), "start": index, "page": row["page"]})
    if len(sections) != 124 or len({row["ref"] for row in sections}) != 124:
        raise ValueError(f"Expected 124 unique PDF section headings; got {len(sections)}")
    for i, section in enumerate(sections):
        end = sections[i + 1]["start"] if i + 1 < len(sections) else len(lines)
        section["end"] = next((j for j in range(section["start"] + 1, end) if lines[j]["text"] in END_MARKERS), end)
    return sections, {row["ref"]: row for row in sections}


def wiki_pages() -> list[dict]:
    pages = []
    for folder in ("concepts", "microtopics", "synthesis"):
        for path in sorted((WIKI / folder).glob("*.md")):
            post = frontmatter.load(path)
            pages.append({"path": str(path.relative_to(WIKI)).replace("\\", "/"), "folder": folder, "post": post})
    if len(pages) < 287:
        raise ValueError(f"Expected at least the original 287 teaching pages; got {len(pages)}")
    return pages


def pdf_links_valid(path: Path, body: str, pdf_pages: int) -> bool:
    links = re.findall(r"\]\(([^)]+\.pdf#page=\d+)\)", body)
    return bool(links) and all(
        path.parent.joinpath(unquote(link).rsplit("#page=", 1)[0]).resolve() == SOURCE.resolve()
        and 1 <= int(link.rsplit("#page=", 1)[1]) <= pdf_pages
        for link in links
    )


def main() -> None:
    digest = hashlib.sha256(SOURCE.read_bytes()).hexdigest()
    if hashlib.sha256((ROOT / SOURCE.name).read_bytes()).hexdigest() != digest:
        raise ValueError("Latest top-level PDF and raw/sources copy differ")
    pdf = pymupdf.open(SOURCE)
    lines = source_lines(pdf)
    sections, by_ref = index_sections(lines)
    chapter_titles = {}
    for index in range(10, 15):
        for line in pdf[index].get_text().splitlines():
            match = re.match(r"^第([1-8]) 章 (.*?)\s*\.{3,}", line)
            if match:
                chapter_titles[int(match.group(1))] = match.group(2).strip()
    if len(chapter_titles) != 8:
        raise ValueError(f"Expected eight PDF chapter titles; got {chapter_titles}")
    pages = wiki_pages()
    issues = []
    checks = []
    numeric_review = []
    map_links = defaultdict(set)
    map_titles = {}
    point_pages = {}
    for page in pages:
        if page["folder"] != "synthesis":
            continue
        text = page["post"].content
        chapter = int(page["post"].get("source_section", 0))
        actual = re.findall(r"(?m)^- \*\*(\d+(?:\.\d+){1,2})\s+([^*]+)\*\*", text)
        expected = [(row["ref"], row["title"]) for row in sections if row["ref"].startswith(f"{chapter}.")]
        matches = [(ref, compact(title)) for ref, title in expected] == [(ref, compact(title)) for ref, title in actual]
        title_matches = compact(str(page["post"].get("title", "")).split("：")[-1]) == compact(chapter_titles[chapter])
        map_titles[chapter] = {"pdf_chapter_title": chapter_titles[chapter], "chapter_title_matches_pdf": title_matches, "expected": expected, "actual": actual, "matches": matches}
        if not title_matches:
            issues.append({"path": page["path"], "kind": "chapter_title", "details": {"pdf": chapter_titles[chapter], "wiki": page["post"].get("title")}})
        if not matches:
            issues.append({"path": page["path"], "kind": "chapter_map", "details": [f"{ref}: PDF={title}, Wiki={dict(actual).get(ref)}" for ref, title in expected if compact(dict(actual).get(ref, "")) != compact(title)]})
        for line in text.splitlines():
            match = re.match(r"- \*\*(\d+(?:\.\d+){1,2})\s+", line)
            if match:
                for link in re.findall(r"\[\[([^]|]+)", line):
                    map_links[link].add(match.group(1))

    expected_points = defaultdict(list)
    for page in pages:
        if page["folder"] == "microtopics":
            section = re.search(r"[1-8]\.[1-9]\d?(?:\.[1-9]\d?)?", str(page["post"].get("source_section", "")))
            number = re.search(r"内部第(\d+)点", str(page["post"].get("source_section", "")))
            if section and number:
                expected_points[section.group()].append((int(number.group(1)), page))

    point_ranges = {}
    for ref, expected in expected_points.items():
        section = by_ref.get(ref)
        if section is None:
            continue
        candidates = []
        for index in range(section["start"] + 1, section["end"]):
            match = POINT.fullmatch(lines[index]["text"])
            if match:
                candidates.append((int(match.group(1)), match.group(2), index))
        found = []
        for number, page in sorted(expected):
            title = str(page["post"].get("title", ""))
            same_number = [row for row in candidates if row[0] == number]
            exact = [row for row in same_number if compact(row[1]) == compact(title)]
            chosen = exact[0] if exact else (same_number[0] if same_number else None)
            if chosen:
                found.append((number, page, chosen))
                point_pages[page["path"]] = {"pdf_title": chosen[1], "pdf_page": lines[chosen[2]]["page"]}
            else:
                issues.append({"path": page["path"], "kind": "point_missing", "details": f"{ref} / {number}"})
        found.sort(key=lambda row: row[2][2])
        for i, (number, page, chosen) in enumerate(found):
            end = found[i + 1][2][2] if i + 1 < len(found) else section["end"]
            point_ranges[page["path"]] = (chosen[2], end)
            if compact(chosen[1]) != compact(str(page["post"].get("title", ""))):
                issues.append({"path": page["path"], "kind": "point_title", "details": {"pdf": chosen[1], "wiki": page["post"].get("title")}})

    for page in pages:
        post = page["post"]
        name = page["path"]
        supplemental = post.get("learning_catalog") is False
        refs = re.findall(r"[1-8]\.[1-9]\d?(?:\.[1-9]\d?)?", str(post.get("source_section", "")))
        check = {
            "path": name,
            "type": page["folder"],
            "source_section": str(post.get("source_section", "")),
            "source_reference_valid": post.get("sources") == [SOURCE_REF],
            "review_status": post.get("review_status"),
            "formula_checked": post.get("formula_checked") is True,
            "figures_checked": post.get("figures_checked") is True,
            "has_reviewer": bool(post.get("reviewed_by") and post.get("reviewed_at")),
            "supplemental_draft": supplemental,
            "missing_teaching_fields": [key for key in ("explanation", "example", "misconception", "question", "answer") if page["folder"] != "synthesis" and not post.get(key)],
        }
        check["pdf_deep_link_valid"] = pdf_links_valid(WIKI / name, post.content, len(pdf))
        checks.append(check)
        required_keys = ("aliases", "formula_checked", "figures_checked", "reviewed_by", "reviewed_at", "explanation", "example", "misconception", "question", "answer") if page["folder"] != "synthesis" else ("aliases", "formula_checked", "figures_checked", "reviewed_by", "reviewed_at", "overview")
        absent_keys = [key for key in required_keys if key not in post.metadata]
        if absent_keys and not supplemental:
            issues.append({"path": name, "kind": "learning_schema_missing", "details": absent_keys})
        if not check["source_reference_valid"]:
            issues.append({"path": name, "kind": "source_reference", "details": post.get("sources")})
        if not check["pdf_deep_link_valid"]:
            issues.append({"path": name, "kind": "pdf_deep_link", "details": "missing or invalid"})
        if page["folder"] == "synthesis":
            check["chapter_map_matches_pdf"] = map_titles[int(post.get("source_section", 0))]["matches"]
            continue
        if not refs or any(ref not in by_ref for ref in refs):
            issues.append({"path": name, "kind": "section_missing", "details": refs})
            continue
        teaching = " ".join(str(post.get(key, "")) for key in ("explanation", "example", "misconception", "question", "answer"))
        numbers = set(re.findall(r"(?<![\w.])\d+(?:\.\d+)?%?(?![\w.])", teaching))
        if numbers:
            source_text = " ".join(lines[index]["text"] for ref in refs for index in range(by_ref[ref]["start"], by_ref[ref]["end"]))
            unmatched = sorted(number for number in numbers if number not in source_text)
            if unmatched:
                numeric_review.append({"path": name, "numbers_not_in_pdf_section": unmatched})
        link = Path(name).stem if page["folder"] == "concepts" else f"microtopics/{Path(name).stem}"
        check["chapter_map_links_match"] = map_links.get(link, set()) == set(refs)
        if not check["chapter_map_links_match"] and not supplemental:
            issues.append({"path": name, "kind": "chapter_map_links", "details": {"pdf_refs": refs, "map_refs": sorted(map_links.get(link, set()))}})
        if page["folder"] != "microtopics":
            continue
        span = point_ranges.get(name)
        if not span:
            continue
        excerpt = re.search(r"(?ms)^## 教材原文摘记\s*\n> (.*?)(?=\n\n(?:## |本条目)|\Z)", post.content)
        if not excerpt:
            issues.append({"path": name, "kind": "excerpt_missing", "details": ""})
            continue
        pdf_text = compact("".join(row["text"] for row in lines[span[0] + 1:span[1]]))
        parts = [compact(part) for part in re.split(r"(?<=[。！？])", excerpt.group(1)) if "【公式见教材原文】" not in part]
        tested = [part for part in parts if len(part) >= 12]
        misses = [part for part in tested if part not in pdf_text]
        check["excerpt_pdf_match"] = not misses
        check["excerpt_tested_parts"] = len(tested)
        check["excerpt_missed_parts"] = len(misses)
        check["pdf_page"] = point_pages[name]["pdf_page"]
        if misses:
            issues.append({"path": name, "kind": "excerpt_mismatch", "details": [part[:100] for part in misses]})

    auxiliary = []
    for folder in ("entities", "queries"):
        for path in sorted((WIKI / folder).glob("*.md")):
            post = frontmatter.load(path)
            name = str(path.relative_to(WIKI)).replace("\\", "/")
            refs = re.findall(r"[1-8]\.[1-9]\d?(?:\.[1-9]\d?)?", str(post.get("source_section", "")))
            valid = {
                "path": name,
                "source_reference_valid": post.get("sources") == [SOURCE_REF],
                "pdf_deep_link_valid": pdf_links_valid(path, post.content, len(pdf)),
                "sections_valid": bool(refs) and all(ref in by_ref for ref in refs),
            }
            if folder == "entities" and valid["sections_valid"]:
                term = {"NVIDIA-Isaac-Sim": "IsaacSim", "Open-X-Embodiment-RT-X": "OpenX-Embodiment", "Stable-Diffusion": "StableDiffusion", "TensorFlow-Serving": "TensorFlowServing"}.get(path.stem, path.stem)
                source_text = compact("".join(lines[index]["text"] for ref in refs for index in range(by_ref[ref]["start"], by_ref[ref]["end"])))
                valid["name_found_in_pdf_sections"] = compact(term).casefold() in source_text.casefold()
            auxiliary.append(valid)
            for key, passed in valid.items():
                if key != "path" and passed is False:
                    issues.append({"path": name, "kind": key, "details": post.get("source_section")})

    result = {
        "source": SOURCE_REF,
        "source_sha256": digest,
        "physical_pdf_pages": len(pdf),
        "counts": dict(Counter(page["folder"] for page in pages)),
        "pdf_sections": sections,
        "chapter_maps": map_titles,
        "page_checks": checks,
        "point_pages": point_pages,
        "point_line_ranges": point_ranges,
        "auxiliary_page_checks": auxiliary,
        "numeric_review": numeric_review,
        "issues": issues,
    }
    output = ROOT / "docs" / "learning-source-audit.json"
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"pages": len(pages), "auxiliary_pages": len(auxiliary), "sections": len(sections), "points_located": len(point_pages), "issues_by_kind": dict(Counter(row["kind"] for row in issues))}, ensure_ascii=False))


if __name__ == "__main__":
    main()
