from ai_daily_update.web import extract_event_overview, extract_one_sentence_conclusion


def test_extract_event_overview_with_slash_heading() -> None:
    content = """# 知识卡片

## 一句话结论
一句话。

## 事件概述 / 研究问题
这是事件概述第一段。

## 方法 / 产品要点
- 要点
"""

    assert extract_event_overview(content) == "这是事件概述第一段。"


def test_extract_event_overview_with_or_heading_and_truncation() -> None:
    content = """# 知识卡片

## 事件概述或研究问题
这是一段比较长的事件概述，用于测试首页审核队列里不会显示过长内容。
"""

    overview = extract_event_overview(content, max_chars=18)

    assert overview.endswith("…")
    assert len(overview) == 18


def test_extract_event_overview_with_bold_heading() -> None:
    content = """# 知识卡片

**一句话结论**
一句话。

**事件概述**
这是粗体标题下的事件概述。

**方法/产品要点**
- 要点
"""

    assert extract_event_overview(content) == "这是粗体标题下的事件概述。"


def test_extract_one_sentence_conclusion() -> None:
    content = """# 知识卡片

**一句话结论**
这是列表页应显示的一句话结论。

## 事件概述
这是事件概述。
"""

    assert extract_one_sentence_conclusion(content) == "这是列表页应显示的一句话结论。"
