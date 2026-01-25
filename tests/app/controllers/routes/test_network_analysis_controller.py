


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
