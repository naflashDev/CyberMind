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

from src.app.models import db as db_module


from unittest.mock import MagicMock, patch

@pytest.fixture(autouse=True)
def patch_hash_repository_and_db():
    '''
    Fixture global para mockear HashRepository y la sesión de base de datos en todos los tests de este archivo.
    Garantiza que nunca se accede a la base de datos real.
    '''
    with patch("src.app.services.hashed.hash_service.HashRepository") as MockRepoService, \
         patch("src.app.services.hashed.hash_repository.HashRepository") as MockRepoRepo, \
         patch("src.app.services.hashed.hash_repository.MD5Hash"), \
         patch("src.app.services.hashed.hash_repository.SHA256Hash"), \
         patch("src.app.services.hashed.hash_repository.SHA512Hash"):
        mock_repo = MockRepoService.return_value
        MockRepoRepo.return_value = mock_repo
        mock_repo.save_hash.return_value = None
        mock_repo.get_original_by_hash.side_effect = lambda h, alg: 'A' if h == hashlib.md5('A'.encode()).hexdigest() else None
        mock_db = MagicMock()
        mock_db.query.return_value.filter_by.return_value.first.return_value = None
        def get_mock_db():
            yield mock_db
        app.dependency_overrides[db_module.get_db] = get_mock_db
        yield

def test_unhash_file_secuencial_timeout():
    '''
    @brief Happy Path, Edge Case y Error Handling: Procesa varios hashes reales de forma secuencial, comprobando timeout y resultado correcto.
    '''
    client = TestClient(app)
    h1 = hashlib.md5('A'.encode()).hexdigest()
    h2 = 'ffffffffffffffffffffffffffffffff'  # No existe
    file_content = f"{h1}\n{h2}\n".encode("utf-8")
    response = client.post("/hashed/unhash-file", files={"file": ("hashes.txt", file_content, "text/plain")})
    assert response.status_code == 200
    results = response.json()["results"]
    assert len(results) == 2
    found = [r for r in results if r["original"] == 'A']
    timeouts = [r for r in results if r["timeout"]]
    assert found
    assert timeouts
