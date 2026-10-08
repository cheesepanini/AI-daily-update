"""Fill empty microtopic teaching fields from the checked PDF and edited drafts."""

from __future__ import annotations

import csv
import json
import re
from pathlib import Path

import frontmatter
import pymupdf

from audit_learning_pdf import ROOT, SOURCE, WIKI, source_lines


def drafts(name: str, key: str) -> dict[str, str]:
    path = ROOT / "docs" / name
    with path.open(encoding="utf-8", newline="") as file:
        return {row["stem"]: row[key] for row in csv.DictReader(file, delimiter="\t")}


def sentences(value: str) -> list[str]:
    value = re.sub(r"【公式见教材原文】|\[\d+\]", "", value)
    return [part.strip(" ·：;；") for part in re.split(r"(?<=[。！？])", value) if len(part.strip()) >= 22]


def main() -> None:
    examples = drafts("learning-microtopic-examples.tsv", "example")
    explanations = drafts("learning-microtopic-explanations.tsv", "explanation")
    misconceptions = drafts("learning-microtopic-misconceptions.tsv", "misconception")
    audit = json.loads((ROOT / "docs" / "learning-source-audit.json").read_text(encoding="utf-8"))
    lines = source_lines(pymupdf.open(SOURCE))
    changes = []
    evidence = []
    for name, (start, end) in sorted(audit["point_line_ranges"].items()):
        path = WIKI / name
        post = frontmatter.load(path)
        stem = path.stem
        excerpt = re.search(r"(?ms)^## 教材原文摘记\s*\n> (.*?)(?=\n\n(?:## |本条目)|\Z)", post.content)
        if not excerpt:
            raise ValueError(f"Missing checked excerpt: {name}")
        source_sentences = [part for part in sentences(excerpt.group(1)) if "【公式见教材原文】" not in part and not re.match(r"^其中，[是为]", part)]
        explanation = explanations.get(stem)
        if not explanation:
            explanation = " ".join(source_sentences[:2])
            if len(explanation) > 300:
                explanation = source_sentences[0]
        source_text = "".join(row["text"] for row in lines[start + 1:end])
        candidates = [part for part in sentences(source_text) if 25 <= len(part) <= 180 and re.search(r"例如|比如|举例|以.{1,25}为例|案例", part) and not re.search(r"[䒿׻Ὅ���]|图\d|式（|（\d\.\d+）", part)]
        candidates.sort(key=lambda part: (0 if "例如" in part else 1 if "比如" in part else 2, len(part)))
        example = examples.get(stem) or (candidates[0] if candidates else "")
        misconception = misconceptions.get(stem, "")
        answer = f"要点：{explanation} 示例：{example}"
        if not all((explanation, example, misconception)):
            raise ValueError(f"Incomplete draft: {name}")
        if any(post.get(key) for key in ("explanation", "example", "misconception", "answer")):
            raise ValueError(f"Refusing to overwrite existing teaching content: {name}")
        content = path.read_text(encoding="utf-8")
        for key, value in (("explanation", explanation), ("example", example), ("misconception", misconception), ("answer", answer)):
            content, count = re.subn(rf"(?m)^{key}: ''$", key + ": " + json.dumps(value, ensure_ascii=False), content)
            if count != 1:
                raise ValueError(f"Expected one empty {key}: {name}")
        content = content.rstrip() + f"\n\n## 学习说明与参考答案\n\n解释：{explanation}\n\n示例：{example}\n\n易错点：{misconception}\n\n参考答案：{answer}\n"
        changes.append((path, content))
        evidence.append({"path": name, "pdf_page": audit["point_pages"][name]["pdf_page"], "example_origin": "illustrative" if stem in examples else "pdf_text", "explanation_origin": "edited" if stem in explanations else "pdf_excerpt"})
    if len(changes) != 189 or set(misconceptions) != {path.stem for path, _ in changes}:
        raise ValueError("Drafts do not cover exactly 189 microtopics")
    for path, content in changes:
        path.write_text(content, encoding="utf-8")
    (ROOT / "docs" / "learning-writing-audit.json").write_text(json.dumps(evidence, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"filled": len(changes), "illustrative_examples": len(examples), "pdf_examples": len(changes) - len(examples), "edited_explanations": len(explanations)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
