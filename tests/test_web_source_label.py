from ai_daily_update.web import is_media_source_card, source_label


def test_source_label_for_known_sources() -> None:
    assert source_label("https://openai.com/news/example") == "OpenAI 博客"
    assert source_label("https://www.anthropic.com/news/example") == "Anthropic 博客"
    assert source_label("https://api-docs.deepseek.com/quick_start/pricing") == "DeepSeek 文档"
    assert source_label("https://arxiv.org/abs/2607.02514v1") == "arXiv 论文"
    assert source_label("https://www.qbitai.com/2026/07/example.html") == "量子位"
    assert (
        source_label("https://mp.weixin.qq.com/s?__biz=MzI3MTA0MTk1MA==&mid=1")
        == "新智元"
    )
    assert source_label("https://aiera.com.cn/2026/07/07/example") == "新智元"
    assert source_label("https://m.sohu.com/a/1046718053_455313") == "腾讯研究院（搜狐同步）"
    assert source_label("https://m.sohu.com/a/1046595190_473283") == "新智元（搜狐同步）"


def test_source_label_falls_back_to_hostname() -> None:
    assert source_label("https://example.com/post") == "example.com"


def test_digest_item_source_type_is_media_card() -> None:
    assert is_media_source_card(
        {
            "source_type": "chinese-media-digest-item",
            "source_label": "腾讯研究院（搜狐同步）",
        }
    )
