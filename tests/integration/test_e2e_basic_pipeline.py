"""
@file test_e2e_basic_pipeline.py
@author naflashDev
@brief Basic end-to-end test for main UI endpoint.
@details Verifies that the main UI endpoint serves index.html and patches startup functions to avoid external side effects.
"""
"""
Test E2E básico: verifica que la UI principal (`/`) sirve `index.html`.

Notas:
- Para evitar efectos secundarios (conexiones a DB, arranque de contenedores),
  se parchean funciones de arranque en el módulo `src.main`.
"""
import pytest
from fastapi.testclient import TestClient

from src import main


@pytest.fixture(autouse=True)
def patch_startup(monkeypatch):
    # Evitar que ensure_infrastructure realice operaciones externas
    monkeypatch.setattr(main, "ensure_infrastructure", lambda params: None)

    # Reemplazar initialize_background_tasks por una versión ligera que marque
    # la inicialización como completada sin intentar conectar a servicios externos.
    async def _dummy_init(app):
        app.state.ui_initialized = True

    monkeypatch.setattr(main, "initialize_background_tasks", _dummy_init)
    yield


def test_ui_index_serves_index_html():
    """Con `TestClient` comprobamos que `/` devuelve HTML (index).

    Este test actúa como un E2E básico: monta la app real y solicita la ruta
    principal, pero evita arrancar dependencias externas mediante mocks.
    """
    with TestClient(main.app) as client:
        resp = client.get("/")
        assert resp.status_code == 200
        content_type = resp.headers.get("content-type", "")
        assert "text/html" in content_type or "html" in resp.text.lower()
