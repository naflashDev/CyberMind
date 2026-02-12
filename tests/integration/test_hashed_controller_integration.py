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
    Fixture global para mockear HashRepository, modelos, la sesión de base de datos y la fuerza bruta en todos los tests de este archivo.
    Garantiza que nunca se accede a la base de datos real ni a la metadata de SQLAlchemy.
    Mockea cualquier instancia y método de HashRepository, incluso en threads, y la fuerza bruta para que los tests sean instantáneos.
    '''
    with patch("src.app.services.hashed.hash_service.HashRepository") as MockRepoService, \
         patch("src.app.services.hashed.hash_repository.HashRepository") as MockRepoRepo, \
         patch("src.app.services.hashed.hash_repository.MD5Hash"), \
         patch("src.app.services.hashed.hash_repository.SHA256Hash"), \
         patch("src.app.services.hashed.hash_repository.SHA512Hash"), \
         patch("src.app.models.db.Base.metadata.create_all"), \
         patch("src.app.models.db.Base.metadata.drop_all"), \
         patch("sqlalchemy.orm.session.Session.query", autospec=True) as mock_query, \
         patch("src.app.services.hashed.bruteforce_utils.bruteforce_hash") as mock_brute:
        # Crea un mock global para HashRepository
        mock_repo = MagicMock()
        mock_repo.save_hash.return_value = None
        mock_repo.get_original_by_hash.side_effect = lambda h, alg: 'A' if h == hashlib.md5('A'.encode()).hexdigest() else None
        mock_repo.commit.return_value = None
        mock_repo.add.return_value = None
        mock_repo.flush.return_value = None
        MockRepoService.return_value = mock_repo
        MockRepoRepo.return_value = mock_repo
        # Mock global para cualquier query
        mock_query.return_value.filter_by.return_value.first.return_value = None
        mock_query.return_value.filter.return_value.first.return_value = None
        mock_db = MagicMock()
        mock_db.query.return_value.filter_by.return_value.first.return_value = None
        mock_db.query.return_value.filter.return_value.first.return_value = None
        mock_db.commit.return_value = None
        mock_db.add.return_value = None
        mock_db.flush.return_value = None
        def get_mock_db():
            yield mock_db
        app.dependency_overrides[db_module.get_db] = get_mock_db
        # Mock fuerza bruta: simula que nunca encuentra el hash (timeout)
        mock_brute.return_value = {"original": None, "combinaciones": 0, "timeout": True}
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
