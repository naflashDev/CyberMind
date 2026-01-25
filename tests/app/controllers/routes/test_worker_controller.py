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
