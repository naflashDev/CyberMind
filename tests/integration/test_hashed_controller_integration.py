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

app = FastAPI()
app.include_router(router)

def test_unhash_file_secuencial_timeout():
    '''
    @brief Happy Path, Edge Case y Error Handling: Procesa varios hashes reales de forma secuencial, comprobando timeout y resultado correcto.
    '''
    client = TestClient(app)
    # Genera 2 hashes: uno fácil (A), uno imposible
    h1 = hashlib.md5('A'.encode()).hexdigest()
    h2 = 'ffffffffffffffffffffffffffffffff'  # No existe
    file_content = f"{h1}\n{h2}\n".encode("utf-8")
    response = client.post("/hashed/unhash-file", files={"file": ("hashes.txt", file_content, "text/plain")})
    assert response.status_code == 200
    results = response.json()["results"]
    assert len(results) == 2
    # Al menos uno debe encontrarse, el otro timeout
    found = [r for r in results if r["original"] == 'A']
    timeouts = [r for r in results if r["timeout"]]
    assert found
    assert timeouts
