from ai_daily_update.utils.slug import slugify


def test_slugify_keeps_ascii_words() -> None:
    assert slugify("AI Agent Workflow!") == "ai-agent-workflow"


def test_slugify_uses_fallback_for_non_ascii_only() -> None:
    assert slugify("中文标题", fallback="item") == "item"
