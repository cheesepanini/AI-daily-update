from ai_daily_update.processors.metadata import infer_title_zh


def test_infer_title_zh_from_markdown_heading() -> None:
    content = "# 知识卡片：DeepSeek 模型与定价\n\n## 一句话结论\n"

    assert infer_title_zh(content) == "DeepSeek 模型与定价"


def test_infer_title_zh_uses_fallback_for_empty_content() -> None:
    assert infer_title_zh("", fallback="默认标题") == "默认标题"


def test_infer_title_zh_skips_section_headings() -> None:
    content = "### 一句话结论\n内容"

    assert infer_title_zh(content, fallback="默认标题") == "默认标题"
