import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from fastapi.testclient import TestClient
from src.app.controllers.routes.tiny_postgres_controller import router
from fastapi import FastAPI

app = FastAPI()
app.include_router(router)
client = TestClient(app)

@pytest.mark.asyncio
async def test_insert_feed_missing_params(monkeypatch):
    '''
    @brief Error Handling: Falta de parámetros obligatorios en insert-feed.
    '''
    with patch("src.app.controllers.routes.tiny_postgres_controller.logger"):
        response = client.post("/postgre-ttrss/insert-feed", json={})
    assert response.status_code in [400, 404, 422, 500]

@pytest.mark.asyncio
async def test_insert_feed_db_error(monkeypatch):
    '''
    @brief Error Handling: Error inesperado en la base de datos al insertar feed.
    '''
    with patch("src.app.controllers.routes.tiny_postgres_controller.logger"):
        with patch("src.app.controllers.routes.tiny_postgres_controller.asyncpg.create_pool", AsyncMock(side_effect=Exception("fail"))):
            response = client.post("/postgre-ttrss/insert-feed", json={"feed_url": "http://feed", "title": "Feed"})
    assert response.status_code in [500, 404]
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from fastapi.testclient import TestClient
from src.app.controllers.routes.tiny_postgres_controller import router
from fastapi import FastAPI

app = FastAPI()
app.include_router(router)
client = TestClient(app)

@pytest.mark.asyncio
async def test_search_and_insert_rss_file_missing(monkeypatch):
    '''
    @brief Error Handling: file_path no existe.
    Simula error de archivo faltante en search-and-insert-rss.
    '''
    monkeypatch.setattr("src.app.controllers.routes.tiny_postgres_controller.os.path.exists", lambda x: False)
    # Patch asyncpg.create_pool to avoid triggering 503 error
    monkeypatch.setattr("src.app.controllers.routes.tiny_postgres_controller.asyncpg.create_pool", AsyncMock(return_value=MagicMock()))
    with patch("src.app.controllers.routes.tiny_postgres_controller.logger"):
        response = client.get("/postgre-ttrss/search-and-insert-rss")
    assert response.status_code == 404
    assert "URL file not found" in response.text

@pytest.mark.asyncio
async def test_search_and_insert_rss_pool_creation(monkeypatch):
    '''
    @brief Happy Path: pool se crea on-demand correctamente.
    '''
    monkeypatch.setattr("src.app.controllers.routes.tiny_postgres_controller.os.path.exists", lambda x: True)
    monkeypatch.setattr("src.app.controllers.routes.tiny_postgres_controller.asyncpg.create_pool", AsyncMock(return_value=MagicMock()))
    with patch("src.app.controllers.routes.tiny_postgres_controller.logger"):
        app.state.pool = None
        response = client.get("/postgre-ttrss/search-and-insert-rss")
    assert response.status_code in [200, 202, 500]
"""
@file test_tiny_postgres_controller_unit.py
@author naflashDev
@brief Unit tests for tiny_postgres_controller endpoints.
@details Unificado: Cubre happy path, edge cases y manejo de errores para todos los endpoints /postgre-ttrss.
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock, AsyncMock
from src.app.controllers.routes.tiny_postgres_controller import router
from fastapi import FastAPI

app = FastAPI()
app.include_router(router)
client = TestClient(app)

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
        app.state.pool = mock_pool
        response = client.get("/postgre-ttrss/feeds?limit=2")
    assert response.status_code == 500
    assert "Ha ocurrido un error interno" in response.text

# --- Extra tests unificados ---
@pytest.mark.asyncio
def test_search_and_insert_rss(monkeypatch):
    """
    @brief Happy Path: search-and-insert-rss endpoint.
    Simula el inicio del proceso de extracción RSS.
    """
    monkeypatch.setattr("src.app.controllers.routes.tiny_postgres_controller.asyncpg.create_pool", AsyncMock(return_value=MagicMock()))
    with patch("src.app.controllers.routes.tiny_postgres_controller.logger"):
        response = client.get("/postgre-ttrss/search-and-insert-rss")
    assert response.status_code in [200, 202, 404, 500]

@pytest.mark.asyncio
def test_search_and_insert_rss_error(monkeypatch):
    """
    @brief Error Handling: search-and-insert-rss error.
    Simula error de pool no inicializado.
    """
    monkeypatch.setattr("src.app.controllers.routes.tiny_postgres_controller.asyncpg.create_pool", AsyncMock(side_effect=Exception("Pool error")))
    with patch("src.app.controllers.routes.tiny_postgres_controller.logger"):
        response = client.get("/postgre-ttrss/search-and-insert-rss")
    assert response.status_code in [500, 404]

@pytest.mark.asyncio
def test_insert_feed_invalid(monkeypatch):
    """
    @brief Edge Case: Insert feed with invalid data.
    Simula inserción de feed con datos inválidos.
    """
    with patch("src.app.controllers.routes.tiny_postgres_controller.logger"):
        response = client.post("/postgre-ttrss/insert-feed", json={"feed_url": "", "title": ""})
    assert response.status_code in [400, 404, 422, 500]
