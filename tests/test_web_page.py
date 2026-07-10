from ai_daily_update.collectors.web_page import extract_document_from_html


def test_extract_document_from_html_prefers_metadata_and_main_text() -> None:
    html = """
    <html>
      <head>
        <title>Fallback Title</title>
        <meta property="og:title" content="OG Title">
        <meta name="description" content="Short description">
      </head>
      <body>
        <nav>Navigation</nav>
        <main>
          <h1>Main Heading</h1>
          <p>First paragraph.</p>
          <script>ignore()</script>
          <p>Second paragraph.</p>
        </main>
      </body>
    </html>
    """

    document = extract_document_from_html("https://example.com", html)

    assert document.title == "OG Title"
    assert document.description == "Short description"
    assert "First paragraph." in document.text
    assert "Second paragraph." in document.text
    assert "ignore" not in document.text
    assert "Navigation" not in document.text
