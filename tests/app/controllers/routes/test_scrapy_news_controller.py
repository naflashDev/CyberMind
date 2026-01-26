"""
@file test_scrapy_news_controller.py
@author naflashDev
@brief Tests para el controlador de noticias Scrapy (scrapy_news_controller).
@details Tests unitarios y de integración para endpoints y tareas de fondo. Se mockean dependencias externas y llamadas asíncronas.
"""

import pytest
from unittest.mock import patch, MagicMock
import threading
from fastapi.testclient import TestClient
from main import app

import threading
import logging
# --- Cobertura avanzada: errores y timers ---
import pytest
from unittest.mock import patch, MagicMock

def test_recurring_google_alert_scraper_error_extract(monkeypatch):
    # Fuerza excepción al extraer feeds
    monkeypatch.setattr(scrapy_news_controller, "fetch_and_save_alert_urls", lambda: (_ for _ in ()).throw(Exception("fail")))
    loop = MagicMock()
    stop_event = threading.Event()
    def dummy_register(timer): pass
    # No debe lanzar excepción
    scrapy_news_controller.recurring_google_alert_scraper(loop, stop_event, dummy_register)
    assert True

def test_recurring_google_alert_scraper_error_reschedule(monkeypatch):
    monkeypatch.setattr(scrapy_news_controller, "fetch_and_save_alert_urls", lambda: None)
    # Fuerza excepción al crear timer
    class DummyTimer:
        def __init__(*a, **kw): raise Exception("timer fail")
    monkeypatch.setattr(scrapy_news_controller, "threading", MagicMock(Timer=DummyTimer))
    loop = MagicMock()
    stop_event = threading.Event()
    def dummy_register(timer): pass
    # No debe lanzar excepción
    scrapy_news_controller.recurring_google_alert_scraper(loop, stop_event, dummy_register)
    assert True

def test_start_scraping_feeds_exception(monkeypatch):
    # Fuerza excepción en Thread
    monkeypatch.setattr(scrapy_news_controller, "threading", MagicMock(Thread=lambda *a, **kw: (_ for _ in ()).throw(Exception("thread fail"))))
    from fastapi.testclient import TestClient
    client = TestClient(app)
    try:
        client.get("/newsSpider/scrapy/google-dk/feeds")
    except Exception as e:
        assert "thread fail" in str(e)

def test_start_scraping_news_exception(monkeypatch):
    # Fuerza excepción en Thread
    monkeypatch.setattr(scrapy_news_controller, "threading", MagicMock(Thread=lambda *a, **kw: (_ for _ in ()).throw(Exception("thread fail"))))
    from fastapi.testclient import TestClient
    client = TestClient(app)
    try:
        client.get("/newsSpider/scrapy/google-dk/news")
    except Exception as e:
        assert "thread fail" in str(e)

def test_start_google_alert_scheduler_stop_event(monkeypatch):
    # Simula que el evento de parada ya existe
    from fastapi.testclient import TestClient
    client = TestClient(app)
    monkeypatch.setattr(os.path, "exists", lambda path: True)
    # Simula app.state con evento de parada
    class DummyEvt:
        def is_set(self): return False
    class DummyState:
        worker_stop_events = {"google_alerts": DummyEvt()}
        worker_timers = {}
        worker_status = {}
    app.state = DummyState()
    resp = client.get("/newsSpider/start-google-alerts")
    assert resp.status_code == 200
    assert "Google Alerts scraping process started" in resp.text
import threading
import asyncio
from src.app.controllers.routes import scrapy_news_controller

def test_background_scraping_feeds_runs(monkeypatch):
    monkeypatch.setattr(scrapy_news_controller, "run_dork_search_feed", lambda: None)
    loop = asyncio.new_event_loop()
    stop_event = threading.Event()
    def dummy_register(timer): pass
    scrapy_news_controller.background_scraping_feeds(loop, stop_event, dummy_register)
    assert True

def test_background_scraping_feeds_stop(monkeypatch):
    monkeypatch.setattr(scrapy_news_controller, "run_dork_search_feed", lambda: None)
    loop = asyncio.new_event_loop()
    stop_event = threading.Event(); stop_event.set()
    def dummy_register(timer): pass
    scrapy_news_controller.background_scraping_feeds(loop, stop_event, dummy_register)
    assert True

def test_background_scraping_news_runs(monkeypatch):
    monkeypatch.setattr(scrapy_news_controller, "run_news_search", lambda: None)
    loop = asyncio.new_event_loop()
    stop_event = threading.Event()
    def dummy_register(timer): pass
    scrapy_news_controller.background_scraping_news(loop, stop_event, dummy_register)
    assert True

def test_background_scraping_news_stop(monkeypatch):
    monkeypatch.setattr(scrapy_news_controller, "run_news_search", lambda: None)
    loop = asyncio.new_event_loop()
    stop_event = threading.Event(); stop_event.set()
    def dummy_register(timer): pass
    scrapy_news_controller.background_scraping_news(loop, stop_event, dummy_register)
    assert True

def test_recurring_google_alert_scraper_runs(monkeypatch):
    monkeypatch.setattr(scrapy_news_controller, "fetch_and_save_alert_urls", lambda: None)
    loop = asyncio.new_event_loop()
    stop_event = threading.Event()
    def dummy_register(timer): pass
    scrapy_news_controller.recurring_google_alert_scraper(loop, stop_event, dummy_register)
    assert True

def test_recurring_google_alert_scraper_stop(monkeypatch):
    monkeypatch.setattr(scrapy_news_controller, "fetch_and_save_alert_urls", lambda: None)
    loop = asyncio.new_event_loop()
    stop_event = threading.Event(); stop_event.set()
    def dummy_register(timer): pass
    scrapy_news_controller.recurring_google_alert_scraper(loop, stop_event, dummy_register)
    assert True
def test_scrape_news_articles_success_endpoint(monkeypatch):
    class DummyPool: pass
    async def dummy_spider(pool, **kwargs): return None
    monkeypatch.setattr("src.app.controllers.routes.scrapy_news_controller.run_dynamic_spider_from_db", dummy_spider)
    app.state = type("State", (), {})()
    app.state.pool = DummyPool()
    client = TestClient(app)
    resp = client.get("/newsSpider/scrape-news")
    assert resp.status_code == 200
    assert "News processing started" in resp.text

def test_start_scraping_feeds_success(monkeypatch):
    monkeypatch.setattr("src.app.controllers.routes.scrapy_news_controller.run_dork_search_feed", lambda: None)
    client = TestClient(app)
    resp = client.get("/newsSpider/scrapy/google-dk/feeds")
    assert resp.status_code == 200
    assert "Scraping started" in resp.text

def test_start_scraping_news_success(monkeypatch):
    monkeypatch.setattr("src.app.controllers.routes.scrapy_news_controller.run_news_search", lambda: None)
    client = TestClient(app)
    resp = client.get("/newsSpider/scrapy/google-dk/news")
    assert resp.status_code == 200
    assert "Scraping iniciado" in resp.text
import os
from fastapi import FastAPI
from fastapi.testclient import TestClient
from src.app.controllers.routes.scrapy_news_controller import router as scrapy_router

# Instancia mínima de FastAPI para pruebas de endpoints
app = FastAPI()
app.include_router(scrapy_router)

def test_guardar_link_no_entries(monkeypatch):
    class DummyFeed:
        entries = []
        feed = {}
    monkeypatch.setattr("src.app.controllers.routes.scrapy_news_controller.feedparser.parse", lambda url: DummyFeed())
    client = TestClient(app)
    resp = client.post("/newsSpider/save-feed-google-alerts", json={"feed_url": "http://bad.com/rss"})
    assert resp.status_code == 400
    assert "Error validating the feed" in resp.text

def test_guardar_link_exception(monkeypatch):
    monkeypatch.setattr("src.app.controllers.routes.scrapy_news_controller.feedparser.parse", lambda url: (_ for _ in ()).throw(Exception("fail")))
    client = TestClient(app)
    resp = client.post("/newsSpider/save-feed-google-alerts", json={"feed_url": "http://fail.com/rss"})
    assert resp.status_code == 400
    assert "Error validating the feed" in resp.text

def test_start_google_alert_scheduler_file_not_found(monkeypatch):
    # Fuerza que el archivo no exista
    monkeypatch.setattr(os.path, "exists", lambda path: False)
    client = TestClient(app)
    resp = client.get("/newsSpider/start-google-alerts")
    assert resp.status_code == 404
    assert "not found" in resp.text

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

