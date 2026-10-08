import pytest
import sys
import types

from ai_daily_update.llm.client import OpenAIClient, extract_text


def test_extract_text_accepts_plain_string() -> None:
    assert extract_text("OK") == "OK"


def test_extract_text_rejects_event_stream_string() -> None:
    with pytest.raises(RuntimeError, match="event stream"):
        extract_text("event: codex.rate_limits\ndata: {}\n")


def test_learning_reply_uses_system_instructions_and_output_limit(monkeypatch) -> None:
    captured = {}

    class FakeResponses:
        def create(self, **kwargs):
            captured.update(kwargs)
            return types.SimpleNamespace(output_text="有来源的解释")

    monkeypatch.setitem(sys.modules, "openai", types.SimpleNamespace(OpenAI=lambda **kwargs: types.SimpleNamespace(responses=FakeResponses())))
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    result = OpenAIClient("test-model").generate_learning_reply("只用审核来源", "张量是什么")
    assert result == "有来源的解释"
    assert captured["instructions"] == "只用审核来源"
    assert captured["max_output_tokens"] == 900


def test_deepseek_learning_reply_uses_configured_endpoint_and_non_thinking(monkeypatch) -> None:
    captured = {}

    class FakeResponses:
        def create(self, **kwargs):
            captured.update(kwargs)
            return types.SimpleNamespace(output_text="[1] 张量是多维数据表示。")

    def fake_openai(**kwargs):
        captured["client"] = kwargs
        return types.SimpleNamespace(responses=FakeResponses())

    monkeypatch.setitem(sys.modules, "openai", types.SimpleNamespace(OpenAI=fake_openai))
    monkeypatch.setenv("DEEPSEEK_API_KEY", "test-key")
    client = OpenAIClient("deepseek-flash", "DEEPSEEK_API_KEY", "https://api.deepseek.com", "none")
    assert client.generate_learning_reply("只用审核来源", "张量是什么") == "[1] 张量是多维数据表示。"
    assert captured["client"]["api_key"] == "test-key"
    assert captured["client"]["base_url"] == "https://api.deepseek.com"
    assert captured["reasoning"] == {"effort": "none"}
