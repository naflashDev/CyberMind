"""
@file test_feeds_gd.py
@author naflashDev
@brief Unit tests for feeds_gd Google Dork search utilities.
@details Covers async search and dork feed logic, including error and edge cases.
"""
import pytest
import asyncio
from app.services.scraping import feeds_gd

@pytest.mark.asyncio
async def test_search_async_happy(monkeypatch):
    """
    Happy Path: search_async returns a list of URLs.
    """
    monkeypatch.setattr(feeds_gd, "search", lambda q, num_results=15: ["http://a.com", "http://b.com"])
    result = await feeds_gd.search_async("test", 2)
    assert isinstance(result, list)
    assert len(result) == 2

@pytest.mark.asyncio
async def test_search_async_executor(monkeypatch):
    """
    Edge Case: search_async with empty result.
    """
    monkeypatch.setattr(feeds_gd, "search", lambda q, num_results=15: [])
    result = await feeds_gd.search_async("test", 1)
    assert result == []

@pytest.mark.asyncio
async def test_run_dork_search_feed(monkeypatch, tmp_path):
    """
    Happy Path: run_dork_search_feed writes results to file.

    This test mocks `search_async` to return a single deterministic URL and
    mocks `asyncio.sleep` to avoid long delays caused by randomized waits
    inside `run_dork_search_feed`.
    """
    async def fake_search_async(q, num_results=15):
        return [f"http://{q.replace('"', '').split()[0]}.com"]

    async def fake_sleep(_):
        return None

    # Use an isolated temporary file for OUTPUT_FILE
    out_file = tmp_path / "test_urls.txt"
    out_file.write_text("")

    monkeypatch.setattr(feeds_gd, "search_async", fake_search_async)
    monkeypatch.setattr(asyncio, "sleep", fake_sleep)
    monkeypatch.setattr(feeds_gd, "OUTPUT_FILE", out_file)

    await feeds_gd.run_dork_search_feed()

    # Ensure the file was written and contains at least one URL
    content = out_file.read_text()
    assert "http://" in content
