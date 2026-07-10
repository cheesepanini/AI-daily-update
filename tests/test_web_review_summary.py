from ai_daily_update.web import extract_review_overview


def test_extract_review_overview_stops_before_detail_table() -> None:
    text = """好的，这是快速审核结果。

# 待审核内容速览

## 总体判断

整体质量较高，大部分建议接受。

## 优先处理

| 序号 | 标题 | 建议 |
| --- | --- | --- |
| [1] | 示例 | 建议接受 |
"""

    overview = extract_review_overview(text)

    assert "总体判断" in overview
    assert "整体质量较高" in overview
    assert "优先处理" not in overview
    assert "| 序号" not in overview
