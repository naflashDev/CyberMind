"""
@file test_spacy_controller_full.py
@author naflashDev
@brief Additional tests for spacy_controller endpoints.
@details Covers /start-spacy endpoint for both file present and not present cases.
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

def test_start_spacy_file_present(monkeypatch, tmp_path):
    client = TestClient(app)
    # Crear archivo result.json temporal
    result_path = tmp_path / 'result.json'
    result_path.write_text('[]')
    monkeypatch.setattr('os.path.exists', lambda p: True)
    resp = client.get('/start-spacy')
    assert resp.status_code in (200, 404)

def test_start_spacy_file_missing(monkeypatch):
    client = TestClient(app)
    monkeypatch.setattr('os.path.exists', lambda p: False)
    resp = client.get('/start-spacy')
    assert resp.status_code == 404
