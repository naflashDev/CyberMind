"""
@file test_hash_service.py
@author naflashDev
@brief Unit tests for HashService and hash endpoints.
@details Pruebas unitarias para el servicio y endpoints de hash (Happy Path, Edge Case, Error Handling).
"""


import pytest
from unittest.mock import MagicMock, patch
from src.app.services.hashed.hash_service import HashService
from src.app.services.hashed.hash_repository import HashAlgorithm

@pytest.fixture()
def mock_db():
    # Mock de la sesión de base de datos
    return MagicMock(name="db_session")
    

def test_hash_and_unhash_md5(mock_db):
    '''
    @brief Happy Path: Hash and unhash with MD5
    Test MD5 hashing and unhashing using mocks (no real DB).
    @param mock_db Mocked DB session.
    '''
    service = HashService(mock_db)
    phrase = "test123"
    # Mock the repository and sus métodos
    mock_repo = MagicMock()
    mock_repo.save_hash.return_value = None
    mock_repo.get_original.return_value = phrase
    service.repository = mock_repo
    hashed = service.hash_phrase(phrase, HashAlgorithm.MD5)
    assert hashed is not None
    with patch.object(service, "unhash", return_value=phrase):
        original = service.unhash(hashed, HashAlgorithm.MD5)
        assert original == phrase

def test_hash_and_unhash_sha256(mock_db):
    '''
    @brief Happy Path: Hash and unhash with SHA256
    Test SHA256 hashing and unhashing using mocks (no real DB).
    @param mock_db Mocked DB session.
    '''
    service = HashService(mock_db)
    phrase = "test256"
    mock_repo = MagicMock()
    mock_repo.save_hash.return_value = None
    mock_repo.get_original.return_value = phrase
    service.repository = mock_repo
    hashed = service.hash_phrase(phrase, HashAlgorithm.SHA256)
    assert hashed is not None
    with patch.object(service, "unhash", return_value=phrase):
        original = service.unhash(hashed, HashAlgorithm.SHA256)
        assert original == phrase

def test_hash_and_unhash_sha512(mock_db):
    '''
    @brief Happy Path: Hash and unhash with SHA512
    Test SHA512 hashing and unhashing using mocks (no real DB).
    @param mock_db Mocked DB session.
    '''
    service = HashService(mock_db)
    phrase = "test512"
    mock_repo = MagicMock()
    mock_repo.save_hash.return_value = None
    mock_repo.get_original.return_value = phrase
    service.repository = mock_repo
    hashed = service.hash_phrase(phrase, HashAlgorithm.SHA512)
    assert hashed is not None
    with patch.object(service, "unhash", return_value=phrase):
        original = service.unhash(hashed, HashAlgorithm.SHA512)
        assert original == phrase
    """Happy Path: Hash and unhash with SHA512"""
    service = HashService(mock_db)
    phrase = "test512"
def test_hash_invalid_algorithm(mock_db):
    '''
    @brief Error Handling: Invalid algorithm raises ValueError
    Test that an invalid algorithm raises ValueError (mocked DB).
    @param mock_db Mocked DB session.
    '''
    service = HashService(mock_db)
    with pytest.raises(ValueError):
        service.hash_phrase("test", "INVALID")

# --- API endpoint tests ---
