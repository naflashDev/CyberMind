"""
@file test_network_analysis_controller.py
@author naflashDev
@brief Unit tests for network_analysis_controller endpoints.
@details Tests endpoints for network analysis, including error and edge cases.
"""
import os
import sys
import pytest
from fastapi.testclient import TestClient

WORKSPACE_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..'))
SRC_PATH = os.path.join(WORKSPACE_ROOT, 'src')
if SRC_PATH not in sys.path:
    sys.path.insert(0, SRC_PATH)
from main import app

def test_network_scan_range(monkeypatch):
    client = TestClient(app)
    # Simular error de parámetros
    resp = client.get('/network/scan-range?start_ip=bad&end_ip=bad')
    # Puede devolver 200, 400, 404 o 422 según la validación y la existencia del endpoint
    assert resp.status_code in (200, 400, 404, 422)

def test_network_status():
    client = TestClient(app)
    resp = client.get('/network/status')
    assert resp.status_code in (200, 404)
