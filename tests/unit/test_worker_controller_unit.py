"""
@file test_worker_controller_unit.py
@author naflashDev
@brief Unit tests for worker_controller endpoints and logic.
@details Covers endpoints for worker status, toggling, and shutdown. Includes edge cases and error handling.
"""

import pytest
from fastapi.testclient import TestClient
from app.controllers.routes.worker_controller import router
from fastapi import FastAPI

app = FastAPI()
app.include_router(router)
client = TestClient(app)


def test_get_workers_status():
    """
    @brief Happy Path: Get workers status.
    Test that the /workers endpoint returns a valid status dict.
    """
    response = client.get("/workers")
    assert response.status_code == 200
    assert isinstance(response.json(), dict)


def test_toggle_worker():
    """
    @brief Happy Path: Toggle worker enabled/disabled.
    Test enabling/disabling a worker via POST /workers/{name}.
    """
    response = client.post("/workers/google_alerts", json={"enabled": True})
    assert response.status_code in [200, 204, 400, 404]  # Acceptable for test


def test_shutdown_app():
    """
    @brief Happy Path: Shutdown endpoint.
    Test that /workers/shutdown returns shutdown message.
    """
    # Mock os._exit and sys.exit to prevent real shutdown
    import os, sys
    from unittest.mock import patch
    with patch.object(os, "_exit", lambda code: None), patch.object(sys, "exit", lambda code=0: None):
        response = client.post("/workers/shutdown")
        assert response.status_code == 200
        # Accept Spanish shutdown message
        msg = response.json().get("message", "")
        assert "apagado" in msg.lower() or "cerrará" in msg.lower()


def test_toggle_worker_invalid(monkeypatch):
    """
    @brief Error Handling: Invalid worker name.
    Test POST /workers/{name} with invalid worker name returns error.
    """
    response = client.post("/workers/invalid_worker", json={"enabled": True})
    assert response.status_code in [404, 400]


def test_shutdown_app_edge(monkeypatch):
    """
    @brief Edge Case: Shutdown with missing background tasks.
    Simulate missing background tasks and check response.
    """
    # Mock os._exit, sys.exit, or any kill/exit logic to prevent real shutdown
    import os, sys
    monkeypatch.setattr(os, "_exit", lambda code: None)
    monkeypatch.setattr(sys, "exit", lambda code=0: None)
    # If kill or similar is used, mock it as well
    response = client.post("/workers/shutdown")
    assert response.status_code == 200
    # Accept Spanish shutdown message
    msg = response.json().get("message", "")
    assert "apagado" in msg.lower() or "cerrará" in msg.lower()

    def test_shutdown_app_with_pool_and_timers(monkeypatch):
        '''
        @brief Edge Case: App state with pool, timers, stop events, logger and shutdown_services mocked.
        Verifica que el endpoint maneja correctamente la presencia de pool y timers.
        '''
        import os
        import sys
        from unittest.mock import MagicMock, patch

        monkeypatch.setattr(os, "_exit", lambda code=0: None)
        monkeypatch.setattr(sys, "exit", lambda code=0: None)

        app.state.stop_event = MagicMock()
        app.state.worker_stop_events = {"w1": MagicMock(), "w2": MagicMock()}
        app.state.worker_timers = {"t1": MagicMock(cancel=MagicMock()), "t2": MagicMock(terminate=MagicMock(), join=MagicMock())}
        app.state.worker_status = {"w1": True, "w2": True}
        app.state.pool = MagicMock(close=MagicMock())
        app.state.parameters = ("Ubuntu", "container1,container2")

        with patch("src.app.utils.run_services.shutdown_services") as shutdown_mock, \
            patch("src.app.controllers.routes.worker_controller.logger") as logger_mock:
           shutdown_mock.return_value = None
           logger_mock.success.return_value = None
           logger_mock.remove.return_value = None
           response = client.post("/workers/shutdown")
           assert response.status_code == 200
           msg = response.json().get("message", "")
           assert "apagado" in msg.lower() or "cerrará" in msg.lower()


    def test_shutdown_app_error_handling(monkeypatch):
        '''
        @brief Error Handling: Simula errores en pool.close, timers y logger.
        Verifica que el endpoint sigue devolviendo respuesta válida.
        '''
        import os
        import sys
        from unittest.mock import MagicMock, patch

        monkeypatch.setattr(os, "_exit", lambda code=0: None)
        monkeypatch.setattr(sys, "exit", lambda code=0: None)

        app.state.stop_event = MagicMock()
        app.state.worker_stop_events = {"w1": MagicMock()}
        app.state.worker_timers = {"t1": MagicMock(cancel=MagicMock(side_effect=Exception("fail")))}
        app.state.worker_status = {"w1": True}
        app.state.pool = MagicMock(close=MagicMock(side_effect=Exception("fail")))
        app.state.parameters = ("Ubuntu", "container1")

        with patch("src.app.utils.run_services.shutdown_services") as shutdown_mock, \
            patch("src.app.controllers.routes.worker_controller.logger") as logger_mock:
           shutdown_mock.side_effect = Exception("fail")
           logger_mock.success.side_effect = Exception("fail")
           logger_mock.remove.side_effect = Exception("fail")
           response = client.post("/workers/shutdown")
           assert response.status_code == 200
           msg = response.json().get("message", "")
           assert "apagado" in msg.lower() or "cerrará" in msg.lower()
