"""
@file test_status_controller.py
@author naflashDev
@brief Unit tests for status_controller endpoints.
@details Tests endpoints for system status and health.
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

def test_status_endpoint():
    client = TestClient(app)
    resp = client.get('/status')
    assert resp.status_code == 200
    data = resp.json()
    assert 'workers' in data
    assert isinstance(data['workers'], dict)
