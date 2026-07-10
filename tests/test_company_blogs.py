from ai_daily_update.collectors.company_blogs import (
    CompanyBlogConfig,
    clean_company_title,
    company_blogs_from_settings,
    parse_company_blog_listing,
)


HTML = """
<html>
  <body>
    <nav><a href="/careers">Careers</a></nav>
    <article>
      <a href="/blog/frontier-model-safety">Frontier model safety and deployment update</a>
    </article>
    <article>
      <a href="https://example.com/blog/new-agent-platform">New agent platform for enterprise teams</a>
    </article>
    <footer><a href="/privacy">Privacy Policy</a></footer>
  </body>
</html>
"""


def test_parse_company_blog_listing_extracts_article_links() -> None:
    source = CompanyBlogConfig(name="Example AI", url="https://example.com/blog")

    items = parse_company_blog_listing(HTML, source)

    assert [item.title for item in items] == [
        "Frontier model safety and deployment update",
        "New agent platform for enterprise teams",
    ]
    assert items[0].url == "https://example.com/blog/frontier-model-safety"
    assert items[0].source_name == "Example AI"


def test_company_blogs_from_settings_reads_structured_sources() -> None:
    settings = {
        "sources": {
            "company_blogs": {
                "track": "industry",
                "sources": [
                    {
                        "name": "Anthropic",
                        "url": "https://www.anthropic.com/news",
                        "include_paths": ["/news/"],
                    }
                ],
            }
        }
    }

    sources = company_blogs_from_settings(settings)

    assert sources == [
        CompanyBlogConfig(
            name="Anthropic",
            url="https://www.anthropic.com/news",
            track="industry",
            include_paths=("/news/",),
        )
    ]


def test_company_blogs_from_settings_skips_disabled_sources() -> None:
    settings = {
        "sources": {
            "company_blogs": {
                "sources": [
                    {
                        "name": "Disabled",
                        "url": "https://example.com/blog",
                        "enabled": False,
                    }
                ]
            }
        }
    }

    assert company_blogs_from_settings(settings) == []


def test_parse_company_blog_listing_respects_include_paths() -> None:
    source = CompanyBlogConfig(
        name="Example AI",
        url="https://example.com/blog",
        include_paths=("/blog/",),
    )

    items = parse_company_blog_listing(HTML, source)

    assert [item.url for item in items] == [
        "https://example.com/blog/frontier-model-safety",
        "https://example.com/blog/new-agent-platform",
    ]


def test_clean_company_title_removes_category_and_date_prefix() -> None:
    assert (
        clean_company_title(
            "Product Jun 30, 2026 Introducing Claude Sonnet 5 Sonnet 5 delivers frontier performance"
        )
        == "Introducing Claude Sonnet 5 Sonnet 5 delivers frontier performance"
    )
