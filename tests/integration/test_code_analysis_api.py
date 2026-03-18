"""
@file test_code_analysis_api.py
@author naflashDev
@brief Tests de integración para los endpoints de análisis de código.
@details Cubre casos Happy Path, Edge Case y Error Handling para /code/scan-text y /code/scan-file.
"""
import pytest
from fastapi.testclient import TestClient
from src.main import app
import base64

# Create TestClient per-test so monkeypatching affects runtime imports

def test_scan_text_happy(monkeypatch):
    '''
    @brief Happy Path: código Python vulnerable.
    '''
    # Patch the scanner using the runtime import path used by the app
    monkeypatch.setattr('src.app.services.code_analysis.scanner.CodeScanner.scan_text', lambda self, code: [{"line":1,"severity":"HIGH","description":"Vuln test.","cwe":"CWE-1","explanation":"Exp."}])
    monkeypatch.setattr('src.app.services.code_analysis.scanner.CodeScanner.generate_pdf_report', lambda self, v: base64.b64encode(b'PDF').decode())
    client = TestClient(app)
    resp = client.post("/code/scan-text", json={"code": "eval('2+2')"})
    assert resp.status_code == 200
    data = resp.json()
    assert "vulnerabilities" in data and "pdf_base64" in data
    assert data["vulnerabilities"][0]["severity"] == "HIGH"

def test_scan_text_invalid():
    '''
    @brief Error Handling: campo code ausente.
    '''
    client = TestClient(app)
    resp = client.post("/code/scan-text", json={})
    assert resp.status_code == 400

def test_scan_file_happy(monkeypatch, tmp_path):
    '''
    @brief Happy Path: archivo Python vulnerable.
    '''
    # Patch the scanner using the runtime import path used by the app
    monkeypatch.setattr('src.app.services.code_analysis.scanner.CodeScanner.scan_text', lambda self, code: [{"line":1,"severity":"HIGH","description":"Vuln test.","cwe":"CWE-1","explanation":"Exp."}])
    monkeypatch.setattr('src.app.services.code_analysis.scanner.CodeScanner.generate_pdf_report', lambda self, v: base64.b64encode(b'PDF').decode())
    file_path = tmp_path / "test.py"
    file_path.write_text("eval('2+2')")
    with open(file_path, "rb") as f:
        client = TestClient(app)
        resp = client.post("/code/scan-file", files={"file": ("test.py", f, "text/x-python")})
    assert resp.status_code == 200
    data = resp.json()
    assert "vulnerabilities" in data and "pdf_base64" in data

def test_scan_file_no_file():
    '''
    @brief Error Handling: no se sube archivo.
    '''
    client = TestClient(app)
    resp = client.post("/code/scan-file", files={})
    assert resp.status_code == 400

def test_scan_file_unsupported():
    '''
    @brief Error Handling: tipo de archivo no soportado.
    '''
    with open(__file__, "rb") as f:
        client = TestClient(app)
        resp = client.post("/code/scan-file", files={"file": ("test.unsupported", f, "text/plain")})
    assert resp.status_code == 415
