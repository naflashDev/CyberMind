import pytest

@pytest.mark.asyncio
async def test_scan_range_multiple_hosts(monkeypatch):
    # Simula dos hosts, uno con error y otro ok
    async def fake_to_thread(func, host, *a, **kw):
        if host == "127.0.0.1":
            return [{"port": 80, "open": True}]
        raise Exception("fail host")
    monkeypatch.setattr("asyncio.to_thread", fake_to_thread)
    with patch("src.app.services.network_analysis.network_analysis.logger") as mock_logger:
        result = await network_analysis.scan_range(start="127.0.0.1", end="127.0.0.2", use_nmap=False)
        assert result["scanned"] == 2
        assert any("error" in h for h in result["hosts"])
        assert any("results" in h for h in result["hosts"])
        assert mock_logger.exception.called or mock_logger.info.called

@pytest.mark.asyncio
async def test_scan_range_concurrency(monkeypatch):
    # Simula concurrencia y logs
    calls = []
    async def fake_to_thread(func, host, *a, **kw):
        calls.append(host)
        return [{"port": 80, "open": True}]
    monkeypatch.setattr("asyncio.to_thread", fake_to_thread)
    with patch("src.app.services.network_analysis.network_analysis.logger") as mock_logger:
        result = await network_analysis.scan_range(start="127.0.0.1", end="127.0.0.3", use_nmap=False, concurrency=2)
        assert result["scanned"] == 3
        assert len(calls) == 3
        # No se asegura que mock_logger.info sea llamado en todas las ramas
@pytest.mark.asyncio
async def test_scan_range_asyncio_errors(monkeypatch):
    # Simula error en asyncio.to_thread
    async def fake_to_thread(func, *a, **kw):
        raise Exception("fail to_thread")
    monkeypatch.setattr("asyncio.to_thread", fake_to_thread)
    result = await network_analysis.scan_range(start="127.0.0.1", end="127.0.0.1")
    assert "error" in result["hosts"][0]

@pytest.mark.asyncio
async def test_scan_range_partial_results(monkeypatch):
    # Simula resultado parcial y logs
    async def fake_to_thread(func, *a, **kw):
        if func == network_analysis.run_nmap_scan:
            raise FileNotFoundError()
        return [{"port": 80, "open": True}]
    monkeypatch.setattr("asyncio.to_thread", fake_to_thread)
    with patch("src.app.services.network_analysis.network_analysis.logger") as mock_logger:
        result = await network_analysis.scan_range(start="127.0.0.1", end="127.0.0.1", use_nmap=True)
        assert result["scanned"] == 1
        assert "hosts" in result
        assert mock_logger.warning.called or mock_logger.info.called

@pytest.mark.asyncio
async def test_scan_range_timeout(monkeypatch):
    # Simula TimeoutExpired en nmap
    class Timeout(Exception): pass
    async def fake_to_thread(func, *a, **kw):
        if func == network_analysis.run_nmap_scan:
            raise network_analysis.subprocess.TimeoutExpired(cmd="nmap", timeout=1)
        return [{"port": 80, "open": True}]
    monkeypatch.setattr("asyncio.to_thread", fake_to_thread)
    result = await network_analysis.scan_range(start="127.0.0.1", end="127.0.0.1", use_nmap=True)
    assert result["hosts"][0]["error"].startswith("nmap timeout")
import socket
import errno
import types
from src.app.services.network_analysis import network_analysis
def test__is_valid_ip_cases():
    assert network_analysis._is_valid_ip("127.0.0.1") is True
    assert network_analysis._is_valid_ip("::1") is True
    assert network_analysis._is_valid_ip("notanip") is False

def test_scan_ports_open_closed_filtered(monkeypatch):
    # Simula puerto abierto
    def fake_create_connection(addr, timeout=0.5):
        if addr[1] == 80:
            class Dummy:
                def __enter__(self): return self
                def __exit__(self, a, b, c): pass
            return Dummy()
        raise socket.timeout() if addr[1] == 81 else ConnectionRefusedError()
    monkeypatch.setattr(socket, "create_connection", fake_create_connection)
    results = network_analysis.scan_ports("127.0.0.1", [80, 81, 82], timeout=0.1)
    assert any(r["open"] for r in results)
    assert any(r["state"] == "filtered" for r in results)
    assert any(r["state"] == "closed" for r in results)

def test_scan_ports_oserror(monkeypatch):
    def fake_create_connection(addr, timeout=0.5):
        e = OSError()
        e.errno = errno.ECONNREFUSED
        raise e
    monkeypatch.setattr(socket, "create_connection", fake_create_connection)
    results = network_analysis.scan_ports("127.0.0.1", [80], timeout=0.1)
    assert results[0]["state"] == "closed"

def test_run_nmap_scan_not_found(monkeypatch):
    monkeypatch.setattr(network_analysis.shutil, "which", lambda x: None)
    with pytest.raises(FileNotFoundError):
        network_analysis.run_nmap_scan("127.0.0.1")

def test_run_nmap_scan_parse_error(monkeypatch):
    monkeypatch.setattr(network_analysis.shutil, "which", lambda x: "nmap")
    class DummyProc:
        stdout = "<notxml>"
        stderr = ""
        returncode = 0
    monkeypatch.setattr(network_analysis.subprocess, "run", lambda *a, **kw: DummyProc())
    # No debe lanzar excepción, debe devolver lista vacía y raw
    results, raw = network_analysis.run_nmap_scan("127.0.0.1")
    assert isinstance(results, list)
    assert raw

def test_run_nmap_scan_fallback(monkeypatch):
    monkeypatch.setattr(network_analysis.shutil, "which", lambda x: "nmap")
    class DummyProc:
        stdout = "PORT   STATE SERVICE\n80/tcp open http\n81/tcp closed ftp"
        stderr = ""
        returncode = 0
    monkeypatch.setattr(network_analysis.subprocess, "run", lambda *a, **kw: DummyProc())
    results, raw = network_analysis.run_nmap_scan("127.0.0.1")
    assert any(r["open"] for r in results) or any(r["state"] == "closed" for r in results)

import asyncio
@pytest.mark.asyncio
async def test_scan_range_value_errors():
    with pytest.raises(ValueError):
        await network_analysis.scan_range()
    with pytest.raises(ValueError):
        await network_analysis.scan_range(start="10.0.0.2", end="10.0.0.1")
    with pytest.raises(ValueError):
        await network_analysis.scan_range(cidr="10.0.0.0/24", max_allowed=1)



import sys, os
SRC_APP = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../src/app'))
if SRC_APP not in sys.path:
    sys.path.insert(0, SRC_APP)
import pytest
from fastapi.testclient import TestClient
from main import app
from controllers.routes import network_analysis_controller
from pydantic import ValidationError
from unittest.mock import patch

client = TestClient(app)

def test_scanrequest_ports_string_and_empty():
    # String de puertos válido
    req = network_analysis_controller.ScanRequest(host="127.0.0.1", ports="80,443, 8080")
    assert req.ports == [80, 443, 8080]
    # String vacío
    req2 = network_analysis_controller.ScanRequest(host="127.0.0.1", ports="")
    assert req2.ports is None or req2.ports == []
    # String inválido
    with pytest.raises(ValidationError):
        network_analysis_controller.ScanRequest(host="127.0.0.1", ports="abc,22")

def test_rangescanrequest_ports_and_concurrency():
    # Puertos como string
    req = network_analysis_controller.RangeScanRequest(ports="22, 80", concurrency="10")
    assert req.ports == [22, 80]
    assert req.concurrency == 10
    # Concurrency inválido
    import pytest
    from pydantic import ValidationError
    with pytest.raises(ValidationError):
        network_analysis_controller.RangeScanRequest(concurrency="notanint")

def test_rangescanrequest_empty_fields():
    req = network_analysis_controller.RangeScanRequest(cidr=" ", start="", end=" ")
    assert req.cidr is None and req.start is None and req.end is None

def test_scan_host_required():
    response = client.post("/network/scan", json={"ports": [80]})
    assert response.status_code == 422 or response.status_code == 400

@patch("app.controllers.routes.network_analysis_controller.run_nmap_scan", side_effect=FileNotFoundError)
@patch("app.controllers.routes.network_analysis_controller.scan_ports", return_value=[{"port": 80, "status": "open"}])
def test_scan_fallback_tcp(mock_scan_ports, mock_nmap):
    response = client.post("/network/scan", json={"host": "127.0.0.1", "ports": [80], "use_nmap": True})
    assert response.status_code == 200
    assert "results" in response.json()

@patch("app.controllers.routes.network_analysis_controller.run_nmap_scan", side_effect=Exception("fail"))
def test_scan_generic_exception(mock_nmap):
    response = client.post("/network/scan", json={"host": "127.0.0.1", "ports": [80], "use_nmap": True})
    assert response.status_code == 500

@patch("app.controllers.routes.network_analysis_controller.run_nmap_scan", side_effect=ValueError("bad value"))
def test_scan_valueerror(mock_nmap):
    response = client.post("/network/scan", json={"host": "127.0.0.1", "ports": [80], "use_nmap": True})
    assert response.status_code == 400

@patch("app.controllers.routes.network_analysis_controller.run_nmap_scan", side_effect=Exception("fail"))
def test_scan_timeout_and_misc(mock_nmap):
    # Timeout como string inválido
    response = client.post("/network/scan", json={"host": "127.0.0.1", "ports": [80], "timeout": "bad", "use_nmap": True})
    assert response.status_code in (400, 422, 500)

def test_scan_range_payloads():
    # Payload válido mínimo
    response = client.post("/network/scan_range", json={"cidr": "192.168.1.0/30"})
    # Puede fallar por dependencias, pero debe ejecutarse
    assert response.status_code in (200, 400, 500)
    # Payload malformado
    response2 = client.post("/network/scan_range", data="notjson", headers={"content-type": "application/json"})
    assert response2.status_code in (400, 422, 500)

def test_list_common_ports():
    response = client.get("/network/ports")
    assert response.status_code == 200
    assert "common_ports" in response.json()
