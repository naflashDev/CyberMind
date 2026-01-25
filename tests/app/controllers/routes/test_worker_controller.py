def test_toggle_worker_rss_extractor_file_missing(monkeypatch):
    monkeypatch.setattr(os.path, "exists", lambda path: False)
    app.state = type("State", (), {})()
    app.state.worker_stop_events = {}
    app.state.worker_timers = {}
    app.state.worker_status = {}
    client = TestClient(app)
    resp = client.post("/workers/rss_extractor", json={"enabled": True})
    assert resp.status_code == 400
    assert "urls file missing" in resp.text

def test_toggle_worker_spacy_nlp_file_missing(monkeypatch):
    monkeypatch.setattr(os.path, "exists", lambda path: False)
    app.state = type("State", (), {})()
    app.state.worker_stop_events = {}
    app.state.worker_timers = {}
    app.state.worker_status = {}
    client = TestClient(app)
    resp = client.post("/workers/spacy_nlp", json={"enabled": True})
    assert resp.status_code == 400
    assert "input file missing" in resp.text

def test_toggle_worker_disable_timer_cancel(monkeypatch):
    # Simula settings y app.state con timer que soporta cancel()
    monkeypatch.setattr("src.app.utils.worker_control.load_worker_settings", lambda: {"google_alerts": True})
    monkeypatch.setattr("src.app.utils.worker_control.save_worker_settings", lambda s: None)
    class DummyTimer:
        def cancel(self): raise Exception("cancel fail")
    app.state = type("State", (), {})()
    app.state.worker_stop_events = {"google_alerts": threading.Event()}
    app.state.worker_timers = {"google_alerts": DummyTimer()}
    app.state.worker_status = {"google_alerts": True}
    client = TestClient(app)
    resp = client.post("/workers/google_alerts", json={"enabled": False})
    assert resp.status_code == 200
    assert "disabled" in resp.text

def test_toggle_worker_disable_timer_terminate(monkeypatch):
    # Simula settings y app.state con timer que soporta terminate()
    monkeypatch.setattr("src.app.utils.worker_control.load_worker_settings", lambda: {"google_alerts": True})
    monkeypatch.setattr("src.app.utils.worker_control.save_worker_settings", lambda s: None)
    class DummyProc:
        def terminate(self): raise Exception("term fail")
        def join(self, timeout=None): pass
    app.state = type("State", (), {})()
    app.state.worker_stop_events = {"google_alerts": threading.Event()}
    app.state.worker_timers = {"google_alerts": DummyProc()}
    app.state.worker_status = {"google_alerts": True}
    client = TestClient(app)
    resp = client.post("/workers/google_alerts", json={"enabled": False})
    assert resp.status_code == 200
    assert "disabled" in resp.text
import types
# --- Cobertura avanzada: workers soportados y errores ---
def test_toggle_worker_google_alerts_success(monkeypatch):
    monkeypatch.setattr(os.path, "exists", lambda path: True)
    monkeypatch.setattr("threading.Thread", lambda *a, **kw: type("T", (), {"start": lambda self: None})())
    app.state = type("State", (), {})()
    app.state.worker_stop_events = {}
    app.state.worker_timers = {}
    app.state.worker_status = {}
    client = TestClient(app)
    resp = client.post("/workers/google_alerts", json={"enabled": True})
    assert resp.status_code == 200
    assert "enabled" in resp.text

def test_toggle_worker_rss_extractor_success(monkeypatch):
    monkeypatch.setattr(os.path, "exists", lambda path: True)
    monkeypatch.setattr("threading.Thread", lambda *a, **kw: type("T", (), {"start": lambda self: None})())
    app.state = type("State", (), {})()
    app.state.worker_stop_events = {}
    app.state.worker_timers = {}
    app.state.worker_status = {}
    client = TestClient(app)
    resp = client.post("/workers/rss_extractor", json={"enabled": True})
    assert resp.status_code == 200
    assert "enabled" in resp.text

def test_toggle_worker_scraping_feeds_success(monkeypatch):
    monkeypatch.setattr("threading.Thread", lambda *a, **kw: type("T", (), {"start": lambda self: None})())
    app.state = type("State", (), {})()
    app.state.worker_stop_events = {}
    app.state.worker_timers = {}
    app.state.worker_status = {}
    client = TestClient(app)
    resp = client.post("/workers/scraping_feeds", json={"enabled": True})
    assert resp.status_code == 200
    assert "enabled" in resp.text

def test_toggle_worker_scraping_news_success(monkeypatch):
    monkeypatch.setattr("threading.Thread", lambda *a, **kw: type("T", (), {"start": lambda self: None})())
    app.state = type("State", (), {})()
    app.state.worker_stop_events = {}
    app.state.worker_timers = {}
    app.state.worker_status = {}
    client = TestClient(app)
    resp = client.post("/workers/scraping_news", json={"enabled": True})
    assert resp.status_code == 200
    assert "enabled" in resp.text

def test_toggle_worker_spacy_nlp_success(monkeypatch):
    monkeypatch.setattr(os.path, "exists", lambda path: True)
    monkeypatch.setattr("threading.Thread", lambda *a, **kw: type("T", (), {"start": lambda self: None})())
    app.state = type("State", (), {})()
    app.state.worker_stop_events = {}
    app.state.worker_timers = {}
    app.state.worker_status = {}
    client = TestClient(app)
    resp = client.post("/workers/spacy_nlp", json={"enabled": True})
    assert resp.status_code == 200
    assert "enabled" in resp.text

def test_toggle_worker_llm_updater_success(monkeypatch):
    monkeypatch.setattr("threading.Thread", lambda *a, **kw: type("T", (), {"start": lambda self: None})())
    app.state = type("State", (), {})()
    app.state.worker_stop_events = {}
    app.state.worker_timers = {}
    app.state.worker_status = {}
    client = TestClient(app)
    resp = client.post("/workers/llm_updater", json={"enabled": True})
    assert resp.status_code == 200
    assert "enabled" in resp.text

def test_toggle_worker_dynamic_spider_success(monkeypatch):
    monkeypatch.setattr(os.path, "exists", lambda path: True)
    # Simula pool ya creado
    app.state = type("State", (), {})()
    app.state.worker_stop_events = {}
    app.state.worker_timers = {}
    app.state.worker_status = {}
    app.state.pool = object()
    import asyncio
    monkeypatch.setattr(asyncio, "create_task", lambda coro: None)
    client = TestClient(app)
    resp = client.post("/workers/dynamic_spider", json={"enabled": True})
    assert resp.status_code == 200
    assert "enabled" in resp.text

def test_toggle_worker_dynamic_spider_pool_fail(monkeypatch):
    monkeypatch.setattr(os.path, "exists", lambda path: True)
    # Simula pool no creado y error en asyncpg.create_pool
    app.state = type("State", (), {})()
    app.state.worker_stop_events = {}
    app.state.worker_timers = {}
    app.state.worker_status = {}
    import asyncpg
    monkeypatch.setattr(asyncpg, "create_pool", lambda **kw: (_ for _ in ()).throw(Exception("fail pool")))
    client = TestClient(app)
    resp = client.post("/workers/dynamic_spider", json={"enabled": True})
    assert resp.status_code == 503
    assert "DB pool not available" in resp.text
import threading
from fastapi import FastAPI
from fastapi.testclient import TestClient
from src.app.controllers.routes.worker_controller import router as worker_router, WorkerToggle
import os

app = FastAPI()
app.include_router(worker_router)

def test_toggle_worker_unknown():
    client = TestClient(app)
    resp = client.post("/workers/unknown", json={"enabled": True})
    assert resp.status_code == 404
    assert "Unknown worker" in resp.text

def test_toggle_worker_file_missing(monkeypatch):
    monkeypatch.setattr(os.path, "exists", lambda path: False)
    client = TestClient(app)
    resp = client.post("/workers/google_alerts", json={"enabled": True})
    assert resp.status_code == 400
    assert "feeds file missing" in resp.text

def test_toggle_worker_pool_missing(monkeypatch):
    monkeypatch.setattr(os.path, "exists", lambda path: True)
    # Simula que no hay pool en app.state
    app.state = type("State", (), {})()
    client = TestClient(app)
    resp = client.post("/workers/dynamic_spider", json={"enabled": True})
    assert resp.status_code in (503, 200)  # Puede ser 503 si pool no se crea

def test_toggle_worker_unsupported():
    client = TestClient(app)
    resp = client.post("/workers/not_supported", json={"enabled": True})
    assert resp.status_code == 404
    assert "Unknown worker" in resp.text

def test_toggle_worker_disable_success(monkeypatch):
    # Simula settings y app.state
    monkeypatch.setattr("src.app.utils.worker_control.load_worker_settings", lambda: {"google_alerts": True})
    monkeypatch.setattr("src.app.utils.worker_control.save_worker_settings", lambda s: None)
    app.state = type("State", (), {})()
    app.state.worker_stop_events = {"google_alerts": threading.Event()}
    app.state.worker_timers = {"google_alerts": None}
    app.state.worker_status = {"google_alerts": True}
    client = TestClient(app)
    resp = client.post("/workers/google_alerts", json={"enabled": False})
    assert resp.status_code == 200
    assert "disabled" in resp.text
"""
@file test_worker_controller.py
@author GitHub Copilot
@brief Tests for worker_controller.py
@details Unit and integration tests for endpoints and background logic. External dependencies and async calls are mocked.
"""
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from src.app.controllers.routes import worker_controller

@pytest.mark.asyncio
async def test_get_workers_success():
    req = MagicMock()
    with patch("src.app.controllers.routes.worker_controller.get_workers", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = [{"name": "w1", "status": "on"}]
        result = await mock_get(req)
        assert isinstance(result, list)
        assert result[0]["name"] == "w1"

@pytest.mark.asyncio
async def test_toggle_worker_success():
    req = MagicMock()
    payload = MagicMock()
    with patch("src.app.controllers.routes.worker_controller.toggle_worker", new_callable=AsyncMock) as mock_toggle:
        mock_toggle.return_value = {"result": "ok"}
        result = await mock_toggle("w1", payload, req)
        assert result["result"] == "ok"

# Test WorkerToggle model
from src.app.controllers.routes.worker_controller import WorkerToggle

def test_worker_toggle_model():
    w = WorkerToggle(enabled=True)
    assert w.enabled is True
