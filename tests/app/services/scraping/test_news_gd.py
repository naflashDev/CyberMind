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


def test_load_existing_urls_json_error(tmp_path, monkeypatch):
    '''
    @brief Should handle JSON decode error and return empty set.
    '''
    file = tmp_path / "result.json"
    file.write_text("not a json", encoding="utf-8")
    monkeypatch.setattr(news_gd, "OUTPUT_FILE", file)
    urls = news_gd.load_existing_urls()
    assert urls == set()


def test_append_news_item_error(monkeypatch):
    '''
    @brief Should handle exception in append_news_item.
    '''
    import tempfile
    from pathlib import Path
    import builtins
    # Creamos un Path temporal y parcheamos 'open' global
    with tempfile.TemporaryDirectory() as tmpdir:
        fake_file = Path(tmpdir) / "result.json"
        monkeypatch.setattr(news_gd, "OUTPUT_FILE", fake_file)
        def fail_open(*a, **kw):
            raise IOError("fail")
        monkeypatch.setattr(builtins, "open", fail_open)
        # Should not raise
        news_gd.append_news_item({"url": "x", "title": "fail"})


import asyncio

@pytest.mark.asyncio
async def test_extract_news_structure_error(monkeypatch):
    '''
    @brief Should handle exception in extract_news_structure.
    '''
    class FakeClient:
        async def get(self, url): raise Exception("fail")
        async def __aenter__(self): return self
        async def __aexit__(self, exc_type, exc, tb): pass
    monkeypatch.setattr(news_gd.httpx, "AsyncClient", lambda **kwargs: FakeClient())
    result = await news_gd.extract_news_structure("http://fail.com")
    assert result is None


@pytest.mark.asyncio
async def test_async_search(monkeypatch):
    '''
    @brief Should call search and return results.
    '''
    monkeypatch.setattr(news_gd, "search", lambda q, num_results=5: ["url1", "url2"])
    results = await news_gd.async_search("query", num_results=2)
    assert results == ["url1", "url2"]


@pytest.mark.asyncio
async def test_run_news_search(monkeypatch, tmp_path):
    '''
    @brief Should run main routine and cover all branches.
    '''
    # Patch dorks to a single value for speed
    monkeypatch.setattr(news_gd, "DORKS", ["testdork"])
    # Patch OUTPUT_FILE to temp
    file = tmp_path / "result.json"
    monkeypatch.setattr(news_gd, "OUTPUT_FILE", file)
    # Patch async_search to return two urls
    async def fake_async_search(q, num_results=5):
        return ["http://ok.com", "nothttp", "http://dup.com", "http://ok.com"]
    monkeypatch.setattr(news_gd, "async_search", fake_async_search)
    # Patch extract_news_structure to return dict for ok.com, None for dup.com
    async def fake_extract(url):
        if url == "http://ok.com":
            return {"url": url, "title": "t"}
        return None
    monkeypatch.setattr(news_gd, "extract_news_structure", fake_extract)
    # Patch append_news_item to just record calls
    called = []
    def fake_append(item):
        called.append(item["url"])
    monkeypatch.setattr(news_gd, "append_news_item", fake_append)
    # Patch load_existing_urls to simulate duplicate
    monkeypatch.setattr(news_gd, "load_existing_urls", lambda: {"http://dup.com"})
    # Patch logger to avoid output
    monkeypatch.setattr(news_gd.logger, "info", lambda *a, **k: None)
    monkeypatch.setattr(news_gd.logger, "success", lambda *a, **k: None)
    monkeypatch.setattr(news_gd.logger, "error", lambda *a, **k: None)
    # Patch sleep to skip delay
    async def fake_sleep(s):
        return None
    monkeypatch.setattr(news_gd.asyncio, "sleep", fake_sleep)
    await news_gd.run_news_search()
    assert "http://ok.com" in called


@pytest.mark.asyncio
async def test_run_news_search_error(monkeypatch):
    '''
    @brief Should handle error in async_search and continue.
    '''
    monkeypatch.setattr(news_gd, "DORKS", ["errdork"])
    monkeypatch.setattr(news_gd, "load_existing_urls", lambda: set())
    async def fail_async_search(q, num_results=5):
        raise Exception("fail")
    monkeypatch.setattr(news_gd, "async_search", fail_async_search)
    monkeypatch.setattr(news_gd.logger, "info", lambda *a, **k: None)
    monkeypatch.setattr(news_gd.logger, "error", lambda *a, **k: None)
    async def fake_sleep(s):
        return None
    monkeypatch.setattr(news_gd.asyncio, "sleep", fake_sleep)
    await news_gd.run_news_search()
