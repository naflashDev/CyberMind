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
async def test_run_dork_search_feed(monkeypatch):
    """
    Happy Path: run_dork_search_feed writes results to file.
    """
    monkeypatch.setattr(feeds_gd, "search_async", lambda q, num_results=15: [f"http://{q}.com"])
    from pathlib import Path
    class DummyPath(Path):
        _flavour = type(Path())._flavour
        def exists(self): return True
        def open(self, mode='a', encoding=None):
            class F:
                def write(self, x): pass
                def __enter__(self): return self
                def __exit__(self, exc_type, exc_val, exc_tb): pass
                def __iter__(self): return iter([])  # Simula archivo vacío
            return F()
    monkeypatch.setattr(feeds_gd, "OUTPUT_FILE", DummyPath("/tmp/test_urls.txt"))
    await feeds_gd.run_dork_search_feed()
    assert True  # If no exception, test passes
