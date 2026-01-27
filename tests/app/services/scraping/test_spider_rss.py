"""
@file test_spider_rss.py
@author naflashDev
@brief Unit tests for spider_rss.py
@details Tests for reading URLs and spider creation (mocks, no real Scrapy or multiprocessing).
"""
import pytest
from unittest.mock import patch, MagicMock
from src.app.services.scraping import spider_rss


def test_read_urls_from_file_reads(tmp_path):
    '''
    @brief Should read URLs from file.
    '''
    file = tmp_path / "urls.txt"
    file.write_text("http://a\nhttp://b\n", encoding="utf-8")
    urls = spider_rss.read_urls_from_file(str(file))
    assert urls == ["http://a", "http://b"]


def test_read_urls_from_file_handles_error():
    '''
    @brief Should return empty list on error.
    '''
    urls = spider_rss.read_urls_from_file("nonexistent.txt")
    assert urls == []


def test_create_rss_spider_yields_rss():
    '''
    @brief Should append RSS URLs found.
    '''
    urls = ["http://test.com"]
    results = []
    SpiderClass = spider_rss.create_rss_spider(urls, results)
    spider = SpiderClass()
    class FakeResponse:
        url = "http://test.com"
        def css(self, sel):
            class Link:
                attrib = {"href": "/rss.xml", "type": "application/rss+xml"}
            return [Link()]
        def urljoin(self, href):
            return "http://test.com/rss.xml"
    list(spider.parse(FakeResponse()))
    assert "http://test.com/rss.xml" in results
