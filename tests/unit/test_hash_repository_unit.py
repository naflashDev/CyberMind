"""
@file test_hash_repository_unit.py
@author naflashDev
@brief Pruebas unitarias para hash_repository.py.
@details Cobertura de casos normales, extremos y manejo de errores para la clase HashRepository.
"""

import pytest
from unittest.mock import MagicMock
from src.app.services.hashed.hash_repository import HashRepository, HashAlgorithm

class DummySession:
    def __init__(self):
        self.added = []
        self.committed = False
    def add(self, obj):
        self.added.append(obj)
    def commit(self):
        self.committed = True

class DummyMD5Hash:
    def __init__(self, original_value, hashed_value):
        self.original_value = original_value
        self.hashed_value = hashed_value

class DummySHA256Hash(DummyMD5Hash):
    pass

class DummySHA512Hash(DummyMD5Hash):
    pass

@pytest.fixture
def repo(monkeypatch):
    session = DummySession()
    monkeypatch.setattr('src.app.services.hashed.hash_repository.MD5Hash', DummyMD5Hash)
    monkeypatch.setattr('src.app.services.hashed.hash_repository.SHA256Hash', DummySHA256Hash)
    monkeypatch.setattr('src.app.services.hashed.hash_repository.SHA512Hash', DummySHA512Hash)
    return HashRepository(session), session

# Happy Path: Guardar hash MD5
# Debe guardar correctamente el objeto MD5Hash
def test_save_hash_md5(repo):
    repository, session = repo
    repository.save_hash('test', 'md5hash', HashAlgorithm.MD5)
    assert isinstance(session.added[0], DummyMD5Hash)
    assert session.committed

# Happy Path: Guardar hash SHA256
# Debe guardar correctamente el objeto SHA256Hash
def test_save_hash_sha256(repo):
    repository, session = repo
    repository.save_hash('test', 'sha256hash', HashAlgorithm.SHA256)
    assert isinstance(session.added[0], DummySHA256Hash)
    assert session.committed

# Happy Path: Guardar hash SHA512
# Debe guardar correctamente el objeto SHA512Hash
def test_save_hash_sha512(repo):
    repository, session = repo
    repository.save_hash('test', 'sha512hash', HashAlgorithm.SHA512)
    assert isinstance(session.added[0], DummySHA512Hash)
    assert session.committed

# Edge Case: Algoritmo no soportado
# Debe lanzar ValueError
def test_save_hash_unsupported_algorithm(repo):
    repository, _ = repo
    with pytest.raises(ValueError):
        repository.save_hash('test', 'hash', 'UNSUPPORTED')

# Error Handling: commit falla
# Debe propagar excepción
def test_save_hash_commit_error(repo, monkeypatch):
    repository, session = repo
    monkeypatch.setattr(session, 'commit', lambda: (_ for _ in ()).throw(Exception('commit error')))
    with pytest.raises(Exception):
        repository.save_hash('test', 'md5hash', HashAlgorithm.MD5)

# Happy Path: get_original_by_hash (mock)
# Debe retornar el valor original si existe
@pytest.mark.skip(reason="Implementar mock de query para get_original_by_hash si aplica")
def test_get_original_by_hash():
    pass
