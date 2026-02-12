"""
@file test_hashed_controller_hash_file.py
@author naflashDev
@brief Unit tests for the /hashed/hash-file endpoint.
@details Covers happy path, edge cases, and error handling for uploading a file of words and hashing them with a selected algorithm.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from src.app.controllers.routes.hashed_controller import router
from fastapi import FastAPI

# Setup FastAPI app for testing
app = FastAPI()
app.include_router(router)

# --- Happy Path: hash-file ---
def test_hash_file_happy(monkeypatch):
    '''
    @brief Happy Path - Upload file with words, get hashes (SHA256)
    '''
    mock_service = MagicMock()
    mock_service.hash_phrase.side_effect = lambda palabra, algorithm: f"hash_{palabra}_{algorithm}"
    monkeypatch.setattr("src.app.controllers.routes.hashed_controller.HashService", lambda db: mock_service)
    with patch("src.app.controllers.routes.hashed_controller.get_db", return_value=None):
        client = TestClient(app)
        file_content = "palabra1\npalabra2\npalabra3\n".encode("utf-8")
        response = client.post("/hashed/hash-file?algorithm=SHA256", files={"file": ("palabras.txt", file_content, "text/plain")})
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 3
    for idx, r in enumerate(data["resultados"], 1):
        assert r["palabra"] == f"palabra{idx}"
        assert r["hash"] == f"hash_palabra{idx}_SHA256"
        assert r["algorithm"] == "SHA256"
        assert "error" not in r

# --- Error Handling: algoritmo no soportado ---
def test_hash_file_invalid_algorithm(monkeypatch):
    '''
    @brief Error Handling - Algoritmo no soportado
    '''
    mock_service = MagicMock()
    monkeypatch.setattr("src.app.controllers.routes.hashed_controller.HashService", lambda db: mock_service)
    with patch("src.app.controllers.routes.hashed_controller.get_db", return_value=None):
        client = TestClient(app)
        file_content = "palabra1\n".encode("utf-8")
        response = client.post("/hashed/hash-file?algorithm=NOPE", files={"file": ("palabras.txt", file_content, "text/plain")})
    assert response.status_code == 400
    assert "Algoritmo no soportado" in response.text

# --- Edge Case: archivo vacío ---
def test_hash_file_empty(monkeypatch):
    '''
    @brief Edge Case - Archivo vacío
    '''
    mock_service = MagicMock()
    monkeypatch.setattr("src.app.controllers.routes.hashed_controller.HashService", lambda db: mock_service)
    with patch("src.app.controllers.routes.hashed_controller.get_db", return_value=None):
        client = TestClient(app)
        file_content = b"\n"
        response = client.post("/hashed/hash-file?algorithm=MD5", files={"file": ("palabras.txt", file_content, "text/plain")})
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 0
    assert data["resultados"] == []

# --- Error Handling: excepción en hash_phrase ---
def test_hash_file_hashphrase_exception(monkeypatch):
    '''
    @brief Error Handling - Excepción en hash_phrase
    '''
    mock_service = MagicMock()
    mock_service.hash_phrase.side_effect = Exception("fail")
    monkeypatch.setattr("src.app.controllers.routes.hashed_controller.HashService", lambda db: mock_service)
    with patch("src.app.controllers.routes.hashed_controller.get_db", return_value=None):
        client = TestClient(app)
        file_content = "palabra1\npalabra2\n".encode("utf-8")
        response = client.post("/hashed/hash-file?algorithm=SHA512", files={"file": ("palabras.txt", file_content, "text/plain")})
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2
    errores = [r for r in data["resultados"] if "error" in r]
    assert len(errores) == 2
    for r in errores:
        assert r["error"] == "fail"
