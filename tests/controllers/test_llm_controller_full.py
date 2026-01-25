"""
@file test_llm_controller_full.py
@author naflashDev
@brief Additional tests for llm_controller endpoints.
@details Covers updater and stop-updater endpoints, including worker state changes.
"""
import os
import sys
import pytest
from fastapi.testclient import TestClient
import threading

WORKSPACE_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..'))
SRC_PATH = os.path.join(WORKSPACE_ROOT, 'src')
if SRC_PATH not in sys.path:
    sys.path.insert(0, SRC_PATH)
from main import app

def test_llm_updater_start_and_stop():
    client = TestClient(app)
    # Start updater
    resp = client.get('/llm/updater')
    assert resp.status_code == 200
    assert 'started' in resp.json().get('message','') or 'already running' in resp.json().get('message','')
    # Stop updater
    resp2 = client.get('/llm/stop-updater')
    assert resp2.status_code == 200
    assert 'stopped' in resp2.json().get('message','')
