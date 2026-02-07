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
    mock_service.unhash.return_value = "original"
    monkeypatch.setattr("src.app.controllers.routes.hashed_controller.HashService", lambda db: mock_service)
    payload = {"hashed_value": "fakehash", "algorithm": "MD5"}
    with patch("src.app.controllers.routes.hashed_controller.get_db", return_value=None):
        client = TestClient(app)
        response = client.post("/hashed/unhash", json=payload)
    assert response.status_code == 200
    assert response.json() == {"original_value": "original"}

# --- Edge Case: Unhash not found ---
def test_unhash_phrase_not_found(monkeypatch):
    """
    Caso: Edge Case - Unhashing a hash not in DB
    """
    mock_service = MagicMock()
    mock_service.unhash.return_value = None
    monkeypatch.setattr("src.app.controllers.routes.hashed_controller.HashService", lambda db: mock_service)
    payload = {"hashed_value": "notfound", "algorithm": "MD5"}
    with patch("src.app.controllers.routes.hashed_controller.get_db", return_value=None):
        client = TestClient(app)
        response = client.post("/hashed/unhash", json=payload)
    assert response.status_code == 404
    assert "Hash no encontrado" in response.text
