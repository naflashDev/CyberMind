import os
import threading
import asyncio
from fastapi import Request
from unittest.mock import AsyncMock, MagicMock

def test_search_and_insert_rss_success(monkeypatch):
    class DummyPool: pass
    monkeypatch.setattr(os.path, "exists", lambda path: True)
    monkeypatch.setattr("src.app.controllers.routes.tiny_postgres_controller.asyncpg.create_pool", AsyncMock(return_value=DummyPool()))
    app.state = type("State", (), {})()
    app.state.pool = DummyPool()
    client = TestClient(app)
    resp = client.get("/postgre-ttrss/search-and-insert-rss")
    assert resp.status_code == 200
    assert "Background process started" in resp.text

def test_search_and_insert_rss_file_not_found(monkeypatch):
    monkeypatch.setattr(os.path, "exists", lambda path: False)
    app.state = type("State", (), {})()
    app.state.pool = object()
    client = TestClient(app)
    resp = client.get("/postgre-ttrss/search-and-insert-rss")
    assert resp.status_code == 404
    assert "URL file not found" in resp.text

def test_search_and_insert_rss_pool_error(monkeypatch):
    monkeypatch.setattr(os.path, "exists", lambda path: True)
    monkeypatch.setattr("src.app.controllers.routes.tiny_postgres_controller.asyncpg.create_pool", AsyncMock(side_effect=Exception("fail")))
    app.state = type("State", (), {})()
    delattr(app.state, "pool") if hasattr(app.state, "pool") else None
    client = TestClient(app)
    resp = client.get("/postgre-ttrss/search-and-insert-rss")
    assert resp.status_code == 503
    assert "on-demand creation failed" in resp.text

def test_list_feeds_success(monkeypatch):
    class DummyConn: pass
    class DummyContext:
        async def __aenter__(self): return DummyConn()
        async def __aexit__(self, exc_type, exc, tb): pass
    class DummyPool:
        def acquire(self):
            return DummyContext()
    async def dummy_get_feeds(conn, limit):
        return [{
            "id": 1,
            "owner_uid": 123,
            "cat_id": 456,
            "title": "Test Feed",
            "feed_url": "http://test.com/rss",
            "site_url": "http://test.com"
        }]
    monkeypatch.setattr("src.app.controllers.routes.tiny_postgres_controller.get_feeds_from_db", dummy_get_feeds)
    monkeypatch.setattr("src.app.controllers.routes.tiny_postgres_controller.asyncpg.create_pool", AsyncMock(return_value=DummyPool()))
    app.state = type("State", (), {})()
    app.state.pool = DummyPool()
    client = TestClient(app)
    resp = client.get("/postgre-ttrss/feeds?limit=1")
    assert resp.status_code == 200

def test_list_feeds_not_found(monkeypatch):
    class DummyConn: pass
    class DummyContext:
        async def __aenter__(self): return DummyConn()
        async def __aexit__(self, exc_type, exc, tb): pass
    class DummyPool:
        def acquire(self):
            return DummyContext()
    async def dummy_get_feeds(conn, limit): return []
    monkeypatch.setattr("src.app.controllers.routes.tiny_postgres_controller.get_feeds_from_db", dummy_get_feeds)
    monkeypatch.setattr("src.app.controllers.routes.tiny_postgres_controller.asyncpg.create_pool", AsyncMock(return_value=DummyPool()))
    app.state = type("State", (), {})()
    app.state.pool = DummyPool()
    client = TestClient(app)
    resp = client.get("/postgre-ttrss/feeds?limit=1")
    assert resp.status_code == 404
    assert "No feeds found" in resp.text

def test_list_feeds_db_error(monkeypatch):
    class DummyConn: pass
    class DummyContext:
        async def __aenter__(self): return DummyConn()
        async def __aexit__(self, exc_type, exc, tb): pass
    class DummyPool:
        def acquire(self):
            return DummyContext()
    async def dummy_get_feeds(conn, limit): raise Exception("fail")
    monkeypatch.setattr("src.app.controllers.routes.tiny_postgres_controller.get_feeds_from_db", dummy_get_feeds)
    monkeypatch.setattr("src.app.controllers.routes.tiny_postgres_controller.asyncpg.create_pool", AsyncMock(return_value=DummyPool()))
    app.state = type("State", (), {})()
    app.state.pool = DummyPool()
    client = TestClient(app)
    resp = client.get("/postgre-ttrss/feeds?limit=1")
    assert resp.status_code == 500
    assert "Error retrieving feeds" in resp.text
"""
@file test_tiny_postgres_controller.py
@author GitHub Copilot
@brief Tests for tiny_postgres_controller.py
@details Unit and integration tests for endpoints and error cases. External dependencies are mocked.
"""
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from src.app.controllers.routes.tiny_postgres_controller import router as tiny_router

app = FastAPI()
app.include_router(tiny_router)


# Más tests se añadirán tras analizar el controlador y los endpoints
