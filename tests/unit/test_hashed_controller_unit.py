# --- Happy Path: upload-hash-file ---
def test_upload_hash_file_happy(monkeypatch):
    """
    Caso: Happy Path - Subida de archivo con palabra y hash válidos
    """
    mock_service = MagicMock()
    # Simula que ningún hash existe previamente
    mock_service.repo.get_original_by_hash.return_value = None
    mock_service.repo.save_hash.return_value = None
    monkeypatch.setattr("src.app.controllers.routes.hashed_controller.HashService", lambda db: mock_service)
    with patch("src.app.controllers.routes.hashed_controller.get_db", return_value=None):
        client = TestClient(app)
        file_content = "palabra1,0123456789abcdef0123456789abcdef\npalabra2 0123456789abcdef0123456789abcdef\npalabra3\t0123456789abcdef0123456789abcdef\n".encode("utf-8")
        response = client.post("/hashed/upload-hash-file", files={"file": ("hashes.txt", file_content, "text/plain")})
    assert response.status_code == 200
    data = response.json()
    assert data["success"] == 3
    assert data["existentes"] == 0
    assert data["errores"] == 0
    assert data["total"] == 3
    for r in data["resultados"]:
        assert r["status"] == "Hash insertado correctamente"

# --- Error Handling: upload-hash-file con línea inválida ---
def test_upload_hash_file_error(monkeypatch):
    """
    Caso: Error Handling - Línea sin separador o hash inválido
    """
    mock_service = MagicMock()
    mock_service.repo.get_original_by_hash.side_effect = [None]
    mock_service.repo.save_hash.return_value = None
    monkeypatch.setattr("src.app.controllers.routes.hashed_controller.HashService", lambda db: mock_service)
    with patch("src.app.controllers.routes.hashed_controller.get_db", return_value=None):
        client = TestClient(app)
        file_content = "palabra1,0123456789abcdef0123456789abcdef\nlinea_invalida_sin_sep\n".encode("utf-8")
        response = client.post("/hashed/upload-hash-file", files={"file": ("hashes.txt", file_content, "text/plain")})
    assert response.status_code == 200
    data = response.json()
    assert data["success"] == 1
    assert data["errores"] == 1
    assert data["existentes"] == 0
    assert data["total"] == 2
    estados = [r["status"] for r in data["resultados"]]
    assert "Hash insertado correctamente" in estados
    assert "Formato no válido" in estados

# --- Edge Case: upload-hash-file archivo vacío ---
def test_upload_hash_file_empty(monkeypatch):
    mock_service = MagicMock()
    monkeypatch.setattr("src.app.controllers.routes.hashed_controller.HashService", lambda db: mock_service)
    with patch("src.app.controllers.routes.hashed_controller.get_db", return_value=None):
        client = TestClient(app)
        file_content = b"\n"
        response = client.post("/hashed/upload-hash-file", files={"file": ("hashes.txt", file_content, "text/plain")})
    assert response.status_code == 200
    data = response.json()
    assert data["success"] == 0
    assert data["errores"] == 0
    assert data["existentes"] == 0
    assert data["total"] == 0
    assert data["resultados"] == []
import io
import time
"""
@file test_hashed_controller_unit.py
@author naflashDev
@brief Unit tests for hashed_controller endpoints.
@details Covers happy path, edge cases, and error handling for /hashed endpoints.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from src.app.controllers.routes.hashed_controller import router
from fastapi import FastAPI

# Setup FastAPI app for testing
app = FastAPI()
app.include_router(router)

# --- Happy Path: Hash phrase ---
def test_hash_phrase_happy(monkeypatch):
    """
    Caso: Happy Path - Hashing a phrase with supported algorithm
    """
    mock_service = MagicMock()
    mock_service.hash_phrase.return_value = "fakehash"
    monkeypatch.setattr("src.app.controllers.routes.hashed_controller.HashService", lambda db: mock_service)
    
    payload = {"phrase": "test", "algorithm": "MD5"}
    with patch("src.app.controllers.routes.hashed_controller.get_db", return_value=None):
        client = TestClient(app)
        response = client.post("/hashed/hash", json=payload)
    assert response.status_code == 200
    assert response.json() == {"hashed_value": "fakehash"}

# --- Error Handling: Hash phrase (Exception) ---
def test_hash_phrase_error(monkeypatch):
    """
    Caso: Error Handling - Exception during hashing
    """
    mock_service = MagicMock()
    mock_service.hash_phrase.side_effect = Exception("fail")
    monkeypatch.setattr("src.app.controllers.routes.hashed_controller.HashService", lambda db: mock_service)
    payload = {"phrase": "test", "algorithm": "MD5"}
    with patch("src.app.controllers.routes.hashed_controller.get_db", return_value=None):
        client = TestClient(app)
        response = client.post("/hashed/hash", json=payload)
    assert response.status_code == 400
    assert "error" in response.text or "Ha ocurrido un error interno" in response.text

# --- Happy Path: Unhash phrase ---
def test_unhash_phrase_happy(monkeypatch):
    """
    Caso: Happy Path - Unhashing a known hash
    """
    mock_service = MagicMock()
    # Simula la respuesta esperada por el endpoint: lista de MultiUnhashResponseItem
    mock_service.unhash.return_value = [{
        "hash": "fakehash",
        "original": "original",
        "type": "MD5",
        "found": True,
        "method": "db"
    }]
    monkeypatch.setattr("src.app.controllers.routes.hashed_controller.HashService", lambda db: mock_service)
    # El endpoint espera 'hashes' como string multilínea y 'max_len' opcional
    payload = {"hashes": "fakehash", "max_len": 20}
    with patch("src.app.controllers.routes.hashed_controller.get_db", return_value=None):
        client = TestClient(app)
        response = client.post("/hashed/unhash", json=payload)
    assert response.status_code == 200
    # La respuesta es una lista de MultiUnhashResponseItem
    assert isinstance(response.json(), list)
    assert response.json()[0]["original"] == "original"

# --- Edge Case: Unhash not found ---
def test_unhash_phrase_not_found(monkeypatch):
    """
    Caso: Edge Case - Unhashing a hash not in DB
    """
    mock_service = MagicMock()
    # Simula la respuesta de no encontrado: lista con found=False
    mock_service.unhash.return_value = [{
        "hash": "notfound",
        "original": None,
        "type": None,
        "found": False,
        "method": None
    }]
    monkeypatch.setattr("src.app.controllers.routes.hashed_controller.HashService", lambda db: mock_service)
    payload = {"hashes": "notfound", "max_len": 20}
    with patch("src.app.controllers.routes.hashed_controller.get_db", return_value=None):
        client = TestClient(app)
        response = client.post("/hashed/unhash", json=payload)
    # El endpoint devuelve 200 aunque no encuentre, pero el campo 'found' será False
    assert response.status_code == 200
    assert isinstance(response.json(), list)
    assert response.json()[0]["found"] is False


# --- Happy Path: unhash-file con archivo utf-8 ---
def test_unhash_file_utf8(monkeypatch):
    mock_service = MagicMock()
    mock_service.unhash.return_value = [{
        "hash": "fakehash",
        "original": "original",
        "type": "MD5",
        "found": True,
        "method": "db"
    }]
    monkeypatch.setattr("src.app.controllers.routes.hashed_controller.HashService", lambda db: mock_service)
    with patch("src.app.controllers.routes.hashed_controller.get_db", return_value=None):
        client = TestClient(app)
        file_content = "fakehash\n".encode("utf-8")
        response = client.post("/hashed/unhash-file", files={"file": ("hashes.txt", file_content, "text/plain")})
    assert response.status_code == 200
    assert response.json()["results"][0]["original"] == "original"

# --- Edge Case: unhash-file con archivo latin1 ---
def test_unhash_file_latin1(monkeypatch):
    mock_service = MagicMock()
    mock_service.unhash.return_value = [{
        "hash": "fäkehash",
        "original": "original",
        "type": "MD5",
        "found": True,
        "method": "db"
    }]
    monkeypatch.setattr("src.app.controllers.routes.hashed_controller.HashService", lambda db: mock_service)
    with patch("src.app.controllers.routes.hashed_controller.get_db", return_value=None):
        client = TestClient(app)
        file_content = "fäkehash\n".encode("latin1")
        response = client.post("/hashed/unhash-file", files={"file": ("hashes.txt", file_content, "text/plain")})
    assert response.status_code == 200
    assert response.json()["results"][0]["original"] == "original"


# --- Edge Case: unhash-file archivo vacío ---
def test_unhash_file_empty(monkeypatch):
    mock_service = MagicMock()
    mock_service.unhash.return_value = []
    monkeypatch.setattr("src.app.controllers.routes.hashed_controller.HashService", lambda db: mock_service)
    with patch("src.app.controllers.routes.hashed_controller.get_db", return_value=None):
        client = TestClient(app)
        file_content = b"\n"
        response = client.post("/hashed/unhash-file", files={"file": ("hashes.txt", file_content, "text/plain")})
    assert response.status_code == 200
    assert response.json()["results"] == []
