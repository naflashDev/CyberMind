import os
from pathlib import Path
import io
import app.services.scraping.google_alerts_pages as gaps


def test_clean_google_redirect_url():
    src = "https://www.google.com/url?sa=t&url=https%3A%2F%2Fexample.com%2Fpage&usg=ABC"
    out = gaps.clean_google_redirect_url(src)
    assert out == "https://example.com/page"


def test_fetch_and_save_alert_urls_dedupes(tmp_path, monkeypatch):
    # prepare fake feeds file
    feeds_file = tmp_path / "feeds.txt"
    feeds_file.write_text("http://feed1.example/rss\n")

    # prepare output urls file with an existing URL
    urls_file = tmp_path / "urls.txt"
    urls_file.write_text("https://existing.example/\n")

    # monkeypatch module paths
    monkeypatch.setattr(gaps, "FEEDS_FILE_PATH", str(feeds_file))
    monkeypatch.setattr(gaps, "URLS_FILE_PATH", str(urls_file))

    # fake feedparser.parse to return entries with duplicate links
    class FakeFeed:
        def __init__(self, entries):
            self.entries = entries

    def fake_parse(url):
        return FakeFeed(entries=[{"link": "https://new.example/"}, {"link": "https://new.example/"}, {"link": "https://existing.example/"}])

    monkeypatch.setattr(gaps, "feedparser", type("m", (), {"parse": staticmethod(fake_parse)})())

    # run
    gaps.fetch_and_save_alert_urls()

    # verify urls_file contains only the new unique url appended
    content = urls_file.read_text().splitlines()
    assert "https://existing.example/" in content
    assert "https://new.example/" in content
    # new.example only once
    assert content.count("https://new.example/") == 1
