from ai_daily_update.utils.slug import slugify


def test_slugify_keeps_ascii_words() -> None:
    assert slugify("AI Agent Workflow!") == "ai-agent-workflow"


def test_slugify_hashes_non_ascii_only_titles_instead_of_colliding() -> None:
    slug = slugify("中文标题", fallback="item")
    assert slug.startswith("item-")
    assert slug != "item"


def test_slugify_distinguishes_different_non_ascii_titles() -> None:
    assert slugify("中文标题一", fallback="item") != slugify("中文标题二", fallback="item")


def test_slugify_is_stable_for_the_same_non_ascii_title() -> None:
    assert slugify("中文标题", fallback="item") == slugify("中文标题", fallback="item")


def test_slugify_uses_plain_fallback_for_empty_input() -> None:
    assert slugify("", fallback="item") == "item"
    assert slugify("   ", fallback="item") == "item"
