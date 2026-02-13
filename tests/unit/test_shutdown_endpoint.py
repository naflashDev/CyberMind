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
    @brief Test the /workers/shutdown endpoint (Happy Path)

    Simulates a call to the shutdown endpoint and checks the response.
    Uses monkeypatch to avoid actually killing the test process.
    @return None
    '''
    # Patch os.kill to prevent real shutdown
    import os
    monkeypatch.setattr(os, "kill", lambda pid, sig: None)
    response = client.post("/workers/shutdown")
    assert response.status_code == 200
    assert "Apagado iniciado" in response.json().get("message", "")
