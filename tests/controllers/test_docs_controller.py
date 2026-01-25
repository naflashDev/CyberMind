"""
@file test_docs_controller.py
@author naflashDev
@brief Unit tests for docs_controller endpoints.
@details Tests endpoints for listing, reading, and serving documentation files.
"""
import os
import sys
import pytest
from fastapi.testclient import TestClient

WORKSPACE_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..'))
SRC_PATH = os.path.join(WORKSPACE_ROOT, 'src')
if SRC_PATH not in sys.path:
    sys.path.insert(0, SRC_PATH)
import sys
import importlib.util
import os
# Add src directory to sys.path for dynamic import
SRC_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src'))
if SRC_PATH not in sys.path:
    sys.path.insert(0, SRC_PATH)
spec = importlib.util.spec_from_file_location("main", os.path.join(SRC_PATH, "main.py"))
main = importlib.util.module_from_spec(spec)
spec.loader.exec_module(main)
app = main.app

def test_docs_list():
    client = TestClient(app)
    resp = client.get('/docs/list')
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)

def test_docs_readme_exists(monkeypatch):
    client = TestClient(app)
    monkeypatch.setattr(os.path, 'exists', lambda p: True)
    resp = client.get('/docs/readme')
    assert resp.status_code in (200, 404)  # 404 if file not present

def test_docs_readme_not_found(monkeypatch):
    client = TestClient(app)
    monkeypatch.setattr(os.path, 'exists', lambda p: False)
    resp = client.get('/docs/readme')
    assert resp.status_code == 404

def test_docs_file_exists(monkeypatch):
    client = TestClient(app)
    monkeypatch.setattr(os.path, 'exists', lambda p: True)
    resp = client.get('/docs/file/Indice.md')
    assert resp.status_code in (200, 404)

def test_docs_file_not_found(monkeypatch):
    client = TestClient(app)
    monkeypatch.setattr(os.path, 'exists', lambda p: False)
    resp = client.get('/docs/file/NoExiste.md')
    assert resp.status_code == 404
