import json

from ai_daily_update.processors.card_builder import score_card_quality_with_llm


class FakeLLM:
    available = True

    def __init__(self, response):
        self.response = response

    def generate_card_content(self, prompt):
        return self.response


VALID_RESPONSE = json.dumps(
    {
        "scores": {
            "importance": 4,
            "novelty": 3,
            "confidence": 5,
            "book_potential": 2,
            "ppt_potential": 4,
            "public_brief_potential": 3,
        }
    }
)


def test_score_card_quality_with_llm_parses_valid_response():
    llm = FakeLLM(VALID_RESPONSE)
    metadata = {"title_zh": "测试卡片", "track": "industry", "topics": ["agent"]}

    scores = score_card_quality_with_llm(metadata, "正文内容", llm)

    assert scores == {
        "importance": 4,
        "novelty": 3,
        "confidence": 5,
        "book_potential": 2,
        "ppt_potential": 4,
        "public_brief_potential": 3,
    }


def test_score_card_quality_with_llm_clamps_out_of_range_values():
    response = json.dumps(
        {
            "scores": {
                "importance": 9,
                "novelty": 0,
                "confidence": 3,
                "book_potential": 3,
                "ppt_potential": 3,
                "public_brief_potential": 3,
            }
        }
    )
    llm = FakeLLM(response)
    metadata = {"title_zh": "测试卡片"}

    scores = score_card_quality_with_llm(metadata, "正文内容", llm)

    assert scores["importance"] == 5
    assert scores["novelty"] == 1


def test_score_card_quality_with_llm_returns_empty_on_invalid_json():
    llm = FakeLLM("not json at all")
    metadata = {"title_zh": "测试卡片"}

    scores = score_card_quality_with_llm(metadata, "正文内容", llm)

    assert scores == {}


def test_score_card_quality_with_llm_returns_empty_on_missing_fields():
    response = json.dumps({"scores": {"importance": 4}})
    llm = FakeLLM(response)
    metadata = {"title_zh": "测试卡片"}

    scores = score_card_quality_with_llm(metadata, "正文内容", llm)

    assert scores == {}


def test_score_card_quality_with_llm_returns_empty_when_unavailable():
    class UnavailableLLM:
        available = False

    metadata = {"title_zh": "测试卡片"}

    scores = score_card_quality_with_llm(metadata, "正文内容", UnavailableLLM())

    assert scores == {}


def test_score_card_quality_with_llm_returns_empty_when_client_is_none():
    metadata = {"title_zh": "测试卡片"}

    scores = score_card_quality_with_llm(metadata, "正文内容", None)

    assert scores == {}


def test_score_card_quality_with_llm_handles_fenced_json():
    fenced = f"```json\n{VALID_RESPONSE}\n```"
    llm = FakeLLM(fenced)
    metadata = {"title_zh": "测试卡片"}

    scores = score_card_quality_with_llm(metadata, "正文内容", llm)

    assert scores["importance"] == 4
