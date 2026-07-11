from ai_daily_update.ppt.corpus import safe_int


def test_safe_int_handles_infinity_without_crashing() -> None:
    assert safe_int(float("inf")) == 0
    assert safe_int(float("-inf")) == 0
    assert safe_int(float("nan")) == 0
