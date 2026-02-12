"""
@file test_tiny_postgres_controller_unit.py
@author naflashDev
@brief Unit tests for tiny_postgres_controller endpoints.
@details Covers happy path, edge cases, and error handling for /postgre-ttrss endpoints.
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock, AsyncMock
from src.app.controllers.routes.tiny_postgres_controller import router
from fastapi import FastAPI

app = FastAPI()
app.include_router(router)

@pytest.mark.asyncio
async def test_list_feeds_happy(monkeypatch):
    """
    Caso: Happy Path - Devuelve lista de feeds correctamente
    """
    class AsyncContextManager:
        async def __aenter__(self):
            return MagicMock()
        async def __aexit__(self, exc_type, exc, tb):
            pass
    mock_pool = MagicMock()
    mock_pool.acquire = MagicMock(return_value=AsyncContextManager())
    mock_feeds = [
        {"id": 1, "title": "Feed1", "feed_url": "http://feed1", "site_url": "http://site1", "owner_uid": 1, "cat_id": 1},
        {"id": 2, "title": "Feed2", "feed_url": "http://feed2", "site_url": "http://site2", "owner_uid": 2, "cat_id": 2}
    ]
    monkeypatch.setattr("src.app.controllers.routes.tiny_postgres_controller.asyncpg.create_pool", AsyncMock(return_value=mock_pool))
    monkeypatch.setattr("src.app.controllers.routes.tiny_postgres_controller.get_feeds_from_db", AsyncMock(return_value=mock_feeds))
    with patch("src.app.controllers.routes.tiny_postgres_controller.logger"):
        client = TestClient(app)
        app.state.pool = mock_pool
        response = client.get("/postgre-ttrss/feeds?limit=2")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
    assert len(response.json()) == 2

@pytest.mark.asyncio
async def test_list_feeds_not_found(monkeypatch):
    """
    Caso: Edge Case - No hay feeds en la base de datos
    """
    class AsyncContextManager:
        async def __aenter__(self):
            return MagicMock()
        async def __aexit__(self, exc_type, exc, tb):
            pass
    mock_pool = MagicMock()
    mock_pool.acquire = MagicMock(return_value=AsyncContextManager())
    monkeypatch.setattr("src.app.controllers.routes.tiny_postgres_controller.asyncpg.create_pool", AsyncMock(return_value=mock_pool))
    monkeypatch.setattr("src.app.controllers.routes.tiny_postgres_controller.get_feeds_from_db", AsyncMock(return_value=[]))
    with patch("src.app.controllers.routes.tiny_postgres_controller.logger"):
        client = TestClient(app)
        app.state.pool = mock_pool
        response = client.get("/postgre-ttrss/feeds?limit=2")
    assert response.status_code == 404
    assert "No feeds found" in response.text

@pytest.mark.asyncio
async def test_list_feeds_db_error(monkeypatch):
    """
    Caso: Error Handling - Error inesperado en la base de datos
    """
    class AsyncContextManager:
        async def __aenter__(self):
            return MagicMock()
        async def __aexit__(self, exc_type, exc, tb):
            pass
    mock_pool = MagicMock()
    mock_pool.acquire = MagicMock(return_value=AsyncContextManager())
    monkeypatch.setattr("src.app.controllers.routes.tiny_postgres_controller.asyncpg.create_pool", AsyncMock(return_value=mock_pool))
    monkeypatch.setattr("src.app.controllers.routes.tiny_postgres_controller.get_feeds_from_db", AsyncMock(side_effect=Exception("fail")))
    with patch("src.app.controllers.routes.tiny_postgres_controller.logger"):
        client = TestClient(app)
        app.state.pool = mock_pool
        response = client.get("/postgre-ttrss/feeds?limit=2")
    assert response.status_code == 500
    assert "Ha ocurrido un error interno" in response.text
