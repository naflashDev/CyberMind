"""
@file test_feeds_gd.py
@author GitHub Copilot
@brief Unit tests for feeds_gd.py
@details Tests for async search and file writing (mocks, no real Google search).
"""
import pytest
import asyncio
from unittest.mock import patch, MagicMock, AsyncMock
from src.app.services.scraping import feeds_gd

@pytest.mark.asyncio
async def test_search_async_returns_results(monkeypatch):
    '''
    @brief Should return list of URLs.
    '''
    monkeypatch.setattr(feeds_gd, "search", lambda q, num_results=15: ["http://a", "http://b"])
    res = await feeds_gd.search_async("test", num_results=2)
    assert res == ["http://a", "http://b"]

@pytest.mark.asyncio
async def test_run_dork_search_feed_writes_file(tmp_path, monkeypatch):
    '''
    @brief Should write found URLs to file.
    '''
    monkeypatch.setattr(feeds_gd, "OUTPUT_FILE", tmp_path / "urls.txt")
    monkeypatch.setattr(feeds_gd, "search_async", lambda q, num_results=15: asyncio.Future())
    # Patch search_async to return different URLs for each dork
    async def fake_search_async(q, num_results=15):
        return [f"http://{q.replace(' ', '')}"]
    monkeypatch.setattr(feeds_gd, "search_async", fake_search_async)
    monkeypatch.setattr(feeds_gd, "DORKS", ["dork1", "dork2"])
    monkeypatch.setattr(feeds_gd, "logger", AsyncMock())
    await feeds_gd.run_dork_search_feed()
    urls = (tmp_path / "urls.txt").read_text(encoding="utf-8").splitlines()
    assert any("dork1" in u or "dork2" in u for u in urls)
