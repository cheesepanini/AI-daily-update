from __future__ import annotations

import re


TITLE_PREFIXES = ["知识卡片：", "知识卡片:", "标题：", "标题:"]
SECTION_HEADINGS = {
    "一句话结论",
    "事件概述",
    "事件概述或研究问题",
    "研究问题",
    "方法要点",
    "方法/产品要点",
    "主要结果",
    "主要结果或产业意义",
    "为什么重要",
    "与既有脉络的关系",
    "产业意义",
    "局限与不确定性",
    "可用于图书/PPT/简报的角度",
    "原始材料",
}


def infer_title_zh(content: str | None, fallback: str = "待补充中文标题") -> str:
    if not content:
        return fallback
    for raw_line in content.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        is_heading = line.startswith("#")
        line = re.sub(r"^#{1,3}\s*", "", line).strip()
        line = line.strip("*` ")
        has_title_prefix = False
        for prefix in TITLE_PREFIXES:
            if line.startswith(prefix):
                line = line[len(prefix) :].strip()
                has_title_prefix = True
                break
        if line in SECTION_HEADINGS:
            continue
        if line and (is_heading or has_title_prefix) and not line.startswith("---") and not line.startswith("```"):
            return line
    return fallback
