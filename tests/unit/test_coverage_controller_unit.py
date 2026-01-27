"""
@file test_coverage_controller.py
@author naflashDev
@brief Tests for the coverage_controller FastAPI endpoint.
@details Unit tests for the /coverage/html endpoint, including happy path and error handling.
"""
import os
import pytest
from fastapi.testclient import TestClient
from app.controllers.routes.coverage_controller import router

@pytest.fixture
def client():
    from fastapi import FastAPI
    app = FastAPI()
    app.include_router(router)
    return TestClient(app)

def test_coverage_html_happy_path(monkeypatch, client):
    """
    Happy Path: Should return HTML if coverage file exists and BeautifulSoup is installed.
    """
    # Mock os.path.exists to True
    monkeypatch.setattr(os.path, "exists", lambda x: True)
    # Mock open to return simple HTML with .read()
    class DummyFile:
        def read(self):
            return "<html><head></head><body></body></html>"
        def __enter__(self): return self
        def __exit__(self, exc_type, exc_val, exc_tb): pass
    monkeypatch.setattr("builtins.open", lambda f, encoding=None: DummyFile())
    # Mock BeautifulSoup
    class DummySoup:
        def __init__(self, html, parser): pass
        def find_all(self, *a, **k): return []
        @property
        def head(self): return self
        def append(self, tag): pass
        def new_tag(self, *a, **k): return "<link>"
        def __str__(self): return "<html><head><link></head><body></body></html>"
    monkeypatch.setattr("app.controllers.routes.coverage_controller.BeautifulSoup", DummySoup)
    response = client.get("/coverage/html")
    assert response.status_code == 200
    assert 'href="/ui/styles.css"' in response.text

def test_coverage_html_not_found(monkeypatch, client):
    """
    Error Handling: Should return 404 if file does not exist.
    """
    monkeypatch.setattr(os.path, "exists", lambda x: False)
    response = client.get("/coverage/html")
    assert response.status_code == 404
    assert "not found" in response.text.lower()

def test_coverage_html_bs4_missing(monkeypatch, client):
    """
    Error Handling: Should return 500 if BeautifulSoup is not installed.
    """
    monkeypatch.setattr(os.path, "exists", lambda x: True)
    class DummyFile:
        def read(self):
            return "<html></html>"
        def __enter__(self): return self
        def __exit__(self, exc_type, exc_val, exc_tb): pass
    monkeypatch.setattr("builtins.open", lambda f, encoding=None: DummyFile())
    # Simula ImportError al importar bs4
    import sys
    sys.modules["bs4"] = None
    response = client.get("/coverage/html")
    assert response.status_code == 500
    assert "beautifulsoup4" in response.text.lower()
