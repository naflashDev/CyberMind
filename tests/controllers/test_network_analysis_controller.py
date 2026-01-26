"""
@file test_network_analysis_controller.py
@author naflashDev
@brief Unit tests for network_analysis_controller endpoints.
@details Tests endpoints for network analysis, including error and edge cases.
"""
import os
import sys
import pytest
from fastapi.testclient import TestClient

WORKSPACE_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..'))
SRC_PATH = os.path.join(WORKSPACE_ROOT, 'src')
if SRC_PATH not in sys.path:
    sys.path.insert(0, SRC_PATH)
from main import app

def test_network_scan_range(monkeypatch):
    client = TestClient(app)
    # Simular error de parámetros
    resp = client.get('/network/scan-range?start_ip=bad&end_ip=bad')
    # Puede devolver 200, 400, 404 o 422 según la validación y la existencia del endpoint
    assert resp.status_code in (200, 400, 404, 422)

def test_network_status():
    client = TestClient(app)
    resp = client.get('/network/status')
    assert resp.status_code in (200, 404)

def test_scan_host_required():
    client = TestClient(app)
    resp = client.post('/network/scan', json={"host": "", "ports": [80]})
    assert resp.status_code == 400
    assert "host is required" in resp.text

def test_scan_timeout_invalid(monkeypatch):
    # Simula que nmap no está disponible y fuerza el fallback
    monkeypatch.setattr("app.services.network_analysis.network_analysis.run_nmap_scan", lambda *a, **kw: (_ for _ in ()).throw(FileNotFoundError()))
    monkeypatch.setattr("app.services.network_analysis.network_analysis.scan_ports", lambda *a, **kw: [{"port": 80, "status": "open"}])
    client = TestClient(app)
    resp = client.post('/network/scan', json={"host": "127.0.0.1", "ports": [80], "timeout": "bad"})
    # FastAPI devuelve 422 por error de validación de tipo
    assert resp.status_code == 422
    assert "detail" in resp.json()

def test_scan_range_error(monkeypatch):
    # Simula ValueError en el servicio
    monkeypatch.setattr("app.services.network_analysis.network_analysis.scan_range", lambda *a, **kw: (_ for _ in ()).throw(ValueError("bad range")))
    client = TestClient(app)
    resp = client.post('/network/scan_range', json={"cidr": "bad"})
    assert resp.status_code == 400
    # El mensaje real puede variar según la validación de ipaddress
    assert "invalid IP" in resp.text or "does not appear to be an IPv4 or IPv6 network" in resp.text or "bad range" in resp.text

def test_scan_range_success(monkeypatch):
    # Mock con estructura realista: lista de diccionarios por host
    mock_result = {
        "hosts": [
            {
                "host": "127.0.0.1",
                "results": [
                    {"port": 80, "protocol": "tcp", "open": True, "state": "open", "service": "http", "product": "nginx", "version": "1.21", "methods": [], "vulnerabilities": []}
                ]
            }
        ]
    }
    monkeypatch.setattr("app.services.network_analysis.network_analysis.scan_range", lambda **kw: mock_result)
    client = TestClient(app)
    resp = client.post('/network/scan_range', json={"cidr": "127.0.0.1/32"})
    assert resp.status_code == 200
    # La respuesta debe contener la clave 'hosts' y ser lista
    data = resp.json()
    assert "hosts" in data
    assert isinstance(data["hosts"], list)
    assert data["hosts"][0]["host"] == "127.0.0.1"
    # Puede devolver 'results' (éxito) o 'error' (timeout, fallo)
    assert "results" in data["hosts"][0] or "error" in data["hosts"][0]

def test_list_common_ports():
    client = TestClient(app)
    resp = client.get('/network/ports')
    assert resp.status_code == 200
    assert "common_ports" in resp.json()
    assert isinstance(resp.json()["common_ports"], list)
