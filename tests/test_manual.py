from ai_daily_update.collectors.manual import read_manual_urls


def test_read_manual_urls_supports_optional_fields(tmp_path) -> None:
    path = tmp_path / "manual_urls.txt"
    path.write_text(
        """
# comment
https://example.com/a | academic | foundation-model,agent | Example Paper
https://example.com/b
""".strip(),
        encoding="utf-8",
    )

    candidates = read_manual_urls(path)

    assert len(candidates) == 2
    assert candidates[0].track == "academic"
    assert candidates[0].topics == ["foundation-model", "agent"]
    assert candidates[0].title == "Example Paper"
    assert candidates[1].track == "industry"
    assert candidates[1].topics == ["ai-industry"]
