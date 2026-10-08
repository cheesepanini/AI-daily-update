"""Add an explicit, still-unreviewed teaching checklist to local Wiki pages."""

from __future__ import annotations

import re
from copy import deepcopy
from pathlib import Path

import frontmatter


WIKI = Path(__file__).resolve().parents[1] / "AI-introduction" / "AI-introduction" / "wiki"
REQUIRED_SEEDS = {
    "训练验证推理闭环": ["人工智能学习三要素"],
    "回归任务": ["人工智能学习三要素"],
    "分类任务": ["人工智能学习三要素"],
    "梯度下降": ["人工智能学习三要素"],
    "泛化与过拟合": ["训练验证推理闭环"],
    "数据集切分与泄漏": ["训练验证推理闭环"],
    "多层感知机": ["梯度下降"],
    "自监督学习": ["训练验证推理闭环"],
    "预训练指令微调与对齐": ["自监督学习"],
    "大语言模型实践": ["提示工程与思维链"],
    "统计学习实践": ["训练验证推理闭环", "分类任务"],
    "模型部署与运行监测": ["训练验证推理闭环", "AI开发环境"],
    "智能体系统": ["智能体定义与类型"],
}


def section(body: str, heading: str) -> str:
    match = re.search(rf"(?ms)^## {re.escape(heading)}\s*\n(.*?)(?=^## |\Z)", body)
    return match.group(1).strip() if match else ""


def prepare() -> int:
    changed = 0
    for folder in ("concepts", "microtopics", "synthesis"):
        for path in (WIKI / folder).glob("*.md"):
            post = frontmatter.load(path)
            if post.metadata.get("review_status") == "reviewed":
                continue
            body = post.content
            data = deepcopy(dict(post.metadata))
            title = str(data.get("title") or path.stem)
            data.setdefault("aliases", [title])
            data.setdefault("reviewed_by", "")
            data.setdefault("reviewed_at", "")
            data.setdefault("formula_checked", False)
            data.setdefault("figures_checked", False)
            if folder == "synthesis":
                data.setdefault("overview", section(body, "学完后应能"))
            else:
                explanation = section(body, "核心理解") or section(body, "学习补充")
                data.setdefault("explanation", explanation.split("\n\n", 1)[0].strip())
                data.setdefault("example", "")
                misconception = section(body, "容易混淆")
                if not misconception:
                    match = re.search(r"\*\*容易混淆：\*\*(.+)", body)
                    misconception = match.group(1).strip() if match else ""
                data.setdefault("misconception", misconception)
                question = section(body, "自测") or section(body, "自我检查")
                if not question:
                    match = re.search(r"\*\*自测：\*\*(.+)", body)
                    question = match.group(1).strip() if match else ""
                data.setdefault("question", question)
                data.setdefault("answer", "")
                match = re.search(r"先修[：:]([^\n]+)", body)
                helpful = re.findall(r"\[\[([^\]]+)\]\]", match.group(1)) if match else []
                data.setdefault("prerequisites", {"required": [], "helpful": [f"concept:{name}" for name in helpful], "advanced": []})
                if folder == "concepts" and not data["prerequisites"]["required"] and path.stem in REQUIRED_SEEDS:
                    required = [f"concept:{name}" for name in REQUIRED_SEEDS[path.stem]]
                    data["prerequisites"]["required"] = required
                    data["prerequisites"]["helpful"] = [name for name in data["prerequisites"]["helpful"] if name not in required]
            if data != dict(post.metadata):
                post.metadata.clear()
                post.metadata.update(data)
                path.write_text(frontmatter.dumps(post) + "\n", encoding="utf-8")
                changed += 1
    return changed


if __name__ == "__main__":
    print(f"prepared={prepare()}")
