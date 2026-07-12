from app.pipeline.ingest import _clean, _html_to_text, extract_url


def test_extract_url_found():
    assert extract_url("see https://example.com/x here") == "https://example.com/x"


def test_extract_url_strips_trailing_punct():
    assert extract_url("(https://example.com/x).") == "https://example.com/x"


def test_extract_url_none():
    assert extract_url("no link at all") is None
    assert extract_url("") is None


def test_clean_collapses_whitespace():
    assert _clean("a\n\n  b\t c ") == "a b c"


def test_html_to_text_extracts_title_and_paragraphs():
    html = """
    <html><head><title>My Title</title></head>
    <body><script>ignore()</script>
    <article><p>First para.</p><p>Second para.</p></article>
    </body></html>
    """
    title, text = _html_to_text(html)
    assert title == "My Title"
    assert "First para." in text
    assert "Second para." in text
    assert "ignore" not in text
