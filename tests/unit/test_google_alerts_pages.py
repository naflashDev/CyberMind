
import app.services.scraping.google_alerts_pages as gaps

def test_clean_google_redirect_url_happy_path():
    '''
    @brief Happy Path: Extract real URL from Google redirect.
    Verifies that a standard Google redirect URL is correctly cleaned.
    '''
    # Arrange
    src = "https://www.google.com/url?sa=t&url=https%3A%2F%2Fexample.com%2Fpage&usg=ABC"
    # Act
    out = gaps.clean_google_redirect_url(src)
    # Assert
    assert out == "https://example.com/page"

def test_clean_google_redirect_url_no_url_param():
    '''
    @brief Edge Case: No 'url' param in query string.
    Verifies that the original URL is returned if no 'url' param exists.
    '''
    # Arrange
    src = "https://www.google.com/url?sa=t&usg=ABC"
    # Act
    out = gaps.clean_google_redirect_url(src)
    # Assert
    assert out == src

def test_clean_google_redirect_url_empty():
    '''
    @brief Error Handling: Empty string input.
    Verifies that an empty string returns an empty string.
    '''
    # Arrange
    src = ""
    # Act
    out = gaps.clean_google_redirect_url(src)
    # Assert
    assert out == ""



def test_fetch_and_save_alert_urls_dedupes(tmp_path, monkeypatch):
    '''
    @brief Happy Path + Dedupe: Only new unique URLs are appended.
    Simulates feeds and output files, mocks feedparser, and checks deduplication logic.
    '''
    # Arrange
    feeds_file = tmp_path / "feeds.txt"
    feeds_file.write_text("http://feed1.example/rss\n")
    urls_file = tmp_path / "urls.txt"
    urls_file.write_text("https://existing.example/\n")
    monkeypatch.setattr(gaps, "FEEDS_FILE_PATH", str(feeds_file))
    monkeypatch.setattr(gaps, "URLS_FILE_PATH", str(urls_file))

    class FakeFeed:
        def __init__(self, entries):
            self.entries = entries

    def fake_parse(url):
        return FakeFeed(entries=[{"link": "https://new.example/"}, {"link": "https://new.example/"}, {"link": "https://existing.example/"}])

    monkeypatch.setattr(gaps, "feedparser", type("m", (), {"parse": staticmethod(fake_parse)})())

    # Act
    gaps.fetch_and_save_alert_urls()

    # Assert
    content = urls_file.read_text().splitlines()
    assert "https://existing.example/" in content  # Existing URL remains
    assert "https://new.example/" in content       # New URL added
    assert content.count("https://new.example/") == 1  # No duplicates
