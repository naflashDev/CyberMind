"""
@file test_shutdown_endpoint.py
@author naflashDev
@brief Unit test for the /workers/shutdown endpoint.
@details Tests the shutdown endpoint returns the expected response and status code.
"""

import pytest
from fastapi.testclient import TestClient
from src.main import app

client = TestClient(app)


def test_shutdown_endpoint(monkeypatch):
    '''
    @brief Happy Path: Test the /workers/shutdown endpoint.
    Simulates a call to the shutdown endpoint and checks the response.
    Uses monkeypatch to avoid actually killing the test process.
    @return None
    '''
    import os
    import sys
    monkeypatch.setattr(os, "kill", lambda pid, sig: None)
    monkeypatch.setattr(os, "_exit", lambda code=0: None)
    monkeypatch.setattr(sys, "exit", lambda code=0: None)
    response = client.post("/workers/shutdown")
    assert response.status_code == 200
    assert "Apagado iniciado" in response.json().get("message", "")


def test_shutdown_endpoint_with_pool(monkeypatch):
    '''
    @brief Edge Case: App state with pool, timers, stop events, logger and shutdown_services mocked.
    Verifica que el endpoint maneja correctamente la presencia de pool y timers.
    '''
    import os
    import sys
    from unittest.mock import MagicMock, patch

    monkeypatch.setattr(os, "kill", lambda pid, sig: None)
    monkeypatch.setattr(os, "_exit", lambda code=0: None)
    monkeypatch.setattr(sys, "exit", lambda code=0: None)

    # Mock app state
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
        assert "Apagado iniciado" in response.json().get("message", "")

def test_shutdown_endpoint_error_handling(monkeypatch):
    '''
    @brief Error Handling: Simula errores en pool.close, timers y logger.
    Verifica que el endpoint sigue devolviendo respuesta válida.
    '''
    import os
    import sys
    from unittest.mock import MagicMock, patch

    monkeypatch.setattr(os, "kill", lambda pid, sig: None)
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
        assert "Apagado iniciado" in response.json().get("message", "")
