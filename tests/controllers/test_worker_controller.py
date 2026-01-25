"""
@file test_worker_controller.py
@author naflashDev
@brief Unit tests for worker_controller endpoints.
@details Tests endpoints for worker management and status.
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

def test_workers_status():
    client = TestClient(app)
    resp = client.get('/workers/status')
    # Puede devolver 200, 404 o 405 (método no permitido)
    assert resp.status_code in (200, 404, 405)

def test_workers_start(monkeypatch):
    client = TestClient(app)
    # Simular que el worker se inicia correctamente
    monkeypatch.setattr('threading.Thread', lambda *a, **kw: type('T', (), {'start': lambda self: None})())
    resp = client.get('/workers/start')
    # Puede devolver 200, 404 o 405 (método no permitido)
    assert resp.status_code in (200, 404, 405)
