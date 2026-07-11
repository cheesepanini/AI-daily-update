from ai_daily_update.config import load_settings
from ai_daily_update.source_proposals import source_configured_domains
from ai_daily_update.utils.config import list_section, section
from ai_daily_update.web import configured_source_urls, configured_topic_terms


def write_config_with_empty_sections(root) -> None:
    config_dir = root / "config"
    config_dir.mkdir()
    # Every sub-key commented out: YAML parses `sources:` / `storage:` as
    # None rather than an empty dict, which used to crash any code chaining
    # a second .get(...) off the result.
    (config_dir / "app.yaml").write_text(
        "timezone: Asia/Shanghai\nstorage:\ndaily:\nreview:\nppt:\n",
        encoding="utf-8",
    )
    (config_dir / "sources.yaml").write_text("sources:\n", encoding="utf-8")
    (config_dir / "topics.yaml").write_text("topics:\n  foundation-model:\n", encoding="utf-8")
    (config_dir / "scoring.yaml").write_text("candidate_scoring:\n", encoding="utf-8")
    (config_dir / "prompts.yaml").write_text("{}\n", encoding="utf-8")


def test_section_and_list_section_coerce_none_to_empty() -> None:
    assert section({"sources": None}, "sources") == {}
    assert section({}, "sources") == {}
    assert section(None, "sources") == {}
    assert list_section({"feeds": None}, "feeds") == []
    assert list_section({}, "feeds") == []


def test_load_settings_with_empty_sections_does_not_crash(tmp_path) -> None:
    write_config_with_empty_sections(tmp_path)

    settings = load_settings(tmp_path)

    assert settings.markdown_root == tmp_path / "notes"
    assert settings.sqlite_path == tmp_path / "data" / "kb.sqlite"
    assert settings.manual_urls_path == tmp_path / "data" / "manual_urls.txt"
    assert settings.review_statuses == ["needs-review", "accepted", "later", "rejected"]
    assert settings.max_cards == 5


def test_source_configured_domains_handles_empty_sources_section(tmp_path) -> None:
    write_config_with_empty_sections(tmp_path)
    settings = load_settings(tmp_path)

    assert source_configured_domains(settings.sources) == set()


def test_web_helpers_handle_empty_sources_and_topics_sections(tmp_path) -> None:
    write_config_with_empty_sections(tmp_path)
    settings = load_settings(tmp_path)

    assert configured_source_urls(settings.sources) == set()
    assert configured_topic_terms(settings) == {"foundation-model"}
