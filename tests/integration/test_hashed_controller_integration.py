"""
@file test_hashed_controller_integration.py
@author naflashDev
@brief Integration test for /hashed/unhash-file endpoint (procesamiento secuencial y timeout real).
@details Cubre integración real con FastAPI y fuerza bruta limitada (Happy Path, Timeout, Resource Limit).
"""
import pytest
from fastapi.testclient import TestClient
from src.app.controllers.routes.hashed_controller import router
from fastapi import FastAPI
import hashlib


from unittest.mock import MagicMock
app = FastAPI()
app.include_router(router)

# Mock global de la dependencia get_db para todos los endpoints
def override_get_db():
    yield MagicMock()
from src.app.models import db as db_module
app.dependency_overrides[db_module.get_db] = override_get_db

def test_unhash_file_secuencial_timeout():
    '''
    @brief Happy Path, Edge Case y Error Handling: Procesa varios hashes reales de forma secuencial, comprobando timeout y resultado correcto.
    '''
    from unittest.mock import patch, MagicMock
    client = TestClient(app)
    h1 = hashlib.md5('A'.encode()).hexdigest()
    h2 = 'ffffffffffffffffffffffffffffffff'  # No existe
    file_content = f"{h1}\n{h2}\n".encode("utf-8")
    # Mock HashRepository para evitar DB
    with patch("src.app.services.hashed.hash_service.HashRepository") as MockRepo:
        mock_repo = MockRepo.return_value
        mock_repo.save_hash.return_value = None
        mock_repo.get_original_by_hash.return_value = None
        response = client.post("/hashed/unhash-file", files={"file": ("hashes.txt", file_content, "text/plain")})
        assert response.status_code == 200
        results = response.json()["results"]
        assert len(results) == 2
        found = [r for r in results if r["original"] == 'A']
        timeouts = [r for r in results if r["timeout"]]
        assert found
        assert timeouts
