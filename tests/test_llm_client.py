import pytest

from ai_daily_update.llm.client import extract_text


def test_extract_text_accepts_plain_string() -> None:
    assert extract_text("OK") == "OK"


def test_extract_text_rejects_event_stream_string() -> None:
    with pytest.raises(RuntimeError, match="event stream"):
        extract_text("event: codex.rate_limits\ndata: {}\n")
