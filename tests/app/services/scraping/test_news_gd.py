"""
@file test_news_gd.py
@author GitHub Copilot
@brief Unit tests for news_gd.py
@details Tests for news extraction, relevance, and file operations (mocks, no real HTTP or Google search).
"""
import pytest
import json
from unittest.mock import patch, MagicMock
from src.app.services.scraping import news_gd


def test_is_relevant_true():
    '''
    @brief Should return True if keyword present.
    '''
    assert news_gd.is_relevant("hay una vulnerabilidad crítica")

def test_is_relevant_false():
    '''
    @brief Should return False if no keyword present.
    '''
    assert not news_gd.is_relevant("texto sin relación")

@pytest.mark.asyncio
async def test_extract_news_structure_relevant(monkeypatch):
    '''
    @brief Should return news dict if relevant.
    '''
    html = """
    <html><head><title>Test</title></head><body><p>vulnerabilidad</p></body></html>
    """
    class FakeResponse:
        text = html
        status_code = 200
        def raise_for_status(self): pass
    class FakeClient:
        async def get(self, url): return FakeResponse()
        async def __aenter__(self): return self
        async def __aexit__(self, exc_type, exc, tb): pass
    monkeypatch.setattr(news_gd.httpx, "AsyncClient", lambda **kwargs: FakeClient())
    result = await news_gd.extract_news_structure("http://test.com")
    assert result and result["url"] == "http://test.com"

@pytest.mark.asyncio
async def test_extract_news_structure_irrelevant(monkeypatch):
    '''
    @brief Should return None if not relevant.
    '''
    html = "<html><head><title>Test</title></head><body><p>sin clave</p></body></html>"
    class FakeResponse:
        text = html
        status_code = 200
        def raise_for_status(self): pass
    class FakeClient:
        async def get(self, url): return FakeResponse()
        async def __aenter__(self): return self
        async def __aexit__(self, exc_type, exc, tb): pass
    monkeypatch.setattr(news_gd.httpx, "AsyncClient", lambda **kwargs: FakeClient())
    result = await news_gd.extract_news_structure("http://irrelevante.com")
    assert result is None

def test_load_existing_urls(tmp_path, monkeypatch):
    '''
    @brief Should load URLs from file.
    '''
    file = tmp_path / "result.json"
    file.write_text(json.dumps([{"url": "a"}, {"url": "b"}]), encoding="utf-8")
    monkeypatch.setattr(news_gd, "OUTPUT_FILE", file)
    urls = news_gd.load_existing_urls()
    assert "a" in urls and "b" in urls

def test_append_news_item(tmp_path, monkeypatch):
    '''
    @brief Should append news item to file.
    '''
    file = tmp_path / "result.json"
    monkeypatch.setattr(news_gd, "OUTPUT_FILE", file)
    news_gd.append_news_item({"url": "c", "title": "t"})
    data = json.loads(file.read_text(encoding="utf-8"))
    assert any(item["url"] == "c" for item in data)
