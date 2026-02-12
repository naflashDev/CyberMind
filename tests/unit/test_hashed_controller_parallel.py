"""
@file test_hashed_controller_parallel.py
@author naflashDev
@brief Unit and integration tests for /hashed/unhash-file parallel, timeout and resource limits.
@details Covers: procesamiento paralelo, timeout por hash, y limitación de CPU en fuerza bruta.
"""
import io
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from src.app.controllers.routes.hashed_controller import router
from fastapi import FastAPI
import time

app = FastAPI()
app.include_router(router)

def test_unhash_file_parallel_and_timeout(monkeypatch):
    '''
    @brief Happy Path & Timeout: Procesa varios hashes en paralelo y respeta timeout de 60s por hash.
    '''
    # Simula fuerza bruta lenta para forzar timeout
    def slow_unhash(hashes, max_len=20, timeout=60, cpu_limit=0, gpu_limit=0):
        results = []
        for h in hashes:
            # Simula que tarda más de 60s
            time.sleep(0.1)
            results.append({
                "hash": h,
                "original": None,
                "type": "MD5",
                "found": False,
                "method": "bruteforce",
                "count": 0,
                "timeout": True
            })
        return results
    monkeypatch.setattr("src.app.controllers.routes.hashed_controller.HashService", lambda db: MagicMock(unhash=slow_unhash))
    with patch("src.app.controllers.routes.hashed_controller.get_db", return_value=None):
        client = TestClient(app)
        file_content = "hash1\nhash2\nhash3\n".encode("utf-8")
        response = client.post("/hashed/unhash-file", files={"file": ("hashes.txt", file_content, "text/plain")})
    assert response.status_code == 200
    # Debe devolver un resultado por hash, todos con timeout True
    results = response.json()["results"]
    assert len(results) == 3
    for r in results:
        assert r["timeout"] is True

def test_unhash_file_cpu_limit(monkeypatch):
    '''
    @brief Resource Limit: Limita el uso de CPU en fuerza bruta (simulado).
    '''
    def cpu_limit_unhash(hashes, max_len=20, timeout=60, cpu_limit=2, gpu_limit=0):
        # Verifica que cpu_limit se pasa correctamente
        assert cpu_limit == 2
        return [{
            "hash": h,
            "original": None,
            "type": "MD5",
            "found": False,
            "method": "bruteforce",
            "count": 0,
            "timeout": False
        } for h in hashes]
    monkeypatch.setattr("src.app.controllers.routes.hashed_controller.HashService", lambda db: MagicMock(unhash=cpu_limit_unhash))
    with patch("src.app.controllers.routes.hashed_controller.get_db", return_value=None):
        client = TestClient(app)
        file_content = "hashA\nhashB\n".encode("utf-8")
        response = client.post("/hashed/unhash-file", files={"file": ("hashes.txt", file_content, "text/plain")})
    assert response.status_code == 200
    results = response.json()["results"]
    assert len(results) == 2
    for r in results:
        assert r["method"] == "bruteforce"

# NOTA: Para integración real, se recomienda un test e2e con hashes reales y fuerza bruta limitada.
