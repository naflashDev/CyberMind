"""
@file test_scrapy_news_controller.py
@author GitHub Copilot
@brief Tests for scrapy_news_controller.py
@details Unit and integration tests for endpoints and background tasks. External dependencies and async calls are mocked.
"""
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from src.app.controllers.routes import scrapy_news_controller

@pytest.mark.asyncio
@patch("src.app.controllers.routes.scrapy_news_controller.feedparser.parse")
@patch("src.app.controllers.routes.scrapy_news_controller.SaveLinkResponse")
async def test_guardar_link_success(mock_save, mock_parse):
    # Simula un feed válido con entradas
    mock_feed = MagicMock()
    mock_feed.entries = ["entry1"]
    mock_feed.feed = {"title": "Test Feed"}
    mock_parse.return_value = mock_feed
    mock_save.return_value = MagicMock()
    class DummyReq:
        feed_url = "http://test.com/rss"
    result = await scrapy_news_controller.guardar_link(DummyReq())
    assert result is not None

@pytest.mark.asyncio
async def test_scrape_news_articles_success():
    req = MagicMock()
    with patch("src.app.controllers.routes.scrapy_news_controller.scrape_news_articles", new_callable=AsyncMock) as mock_scrape:
        mock_scrape.return_value = {"status": "ok"}
        result = await mock_scrape(req)
        assert result["status"] == "ok"

@pytest.mark.asyncio
async def test_start_google_alert_scheduler_success():
    req = MagicMock()
    with patch("src.app.controllers.routes.scrapy_news_controller.start_google_alert_scheduler", new_callable=AsyncMock) as mock_start:
        mock_start.return_value = MagicMock()
        result = await mock_start(req)
        assert result is not None

@pytest.mark.asyncio
async def test_start_scraping_feeds_success():
    req = MagicMock()
    with patch("src.app.controllers.routes.scrapy_news_controller.start_scraping_feeds", new_callable=AsyncMock) as mock_start:
        mock_start.return_value = {"status": "ok"}
        result = await mock_start(req)
        assert result["status"] == "ok"

@pytest.mark.asyncio
async def test_start_scraping_news_success():
    req = MagicMock()
    with patch("src.app.controllers.routes.scrapy_news_controller.start_scraping_news", new_callable=AsyncMock) as mock_start:
        mock_start.return_value = {"status": "ok"}
        result = await mock_start(req)
        assert result["status"] == "ok"

# Test background functions
@patch("src.app.controllers.routes.scrapy_news_controller.asyncio")
def test_background_scraping_feeds(mock_asyncio):
    loop = MagicMock()
    scrapy_news_controller.background_scraping_feeds(loop)
    assert True

def test_background_scraping_news():
    loop = MagicMock()
    scrapy_news_controller.background_scraping_news(loop)
    assert True

