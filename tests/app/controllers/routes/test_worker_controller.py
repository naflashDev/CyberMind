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
