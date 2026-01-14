import pytest
from fastapi.testclient import TestClient

from main import app


client = TestClient(app)


def test_scan_range_cidr_fallback(monkeypatch):
    # Patch scan_ports to avoid real network activity
    def fake_scan(host, ports=None, timeout=0.5):
        return [
            {"port": 22, "open": True, "service": "ssh", "methods": ["SSH"], "vulnerabilities": []},
            {"port": 80, "open": False, "service": "http", "methods": ["HTTP"], "vulnerabilities": []},
        ]

    monkeypatch.setattr('app.services.network_analysis.network_analysis.scan_ports', fake_scan)

    payload = {"cidr": "127.0.0.0/30", "use_nmap": False, "ports": [22, 80], "concurrency": 5}
    r = client.post('/network/scan_range', json=payload)
    assert r.status_code == 200
    j = r.json()
    assert 'scanned' in j and isinstance(j['scanned'], int)
    assert 'hosts' in j and isinstance(j['hosts'], list)
    assert j['scanned'] == len(j['hosts'])
    for h in j['hosts']:
        assert 'host' in h
        assert 'results' in h and isinstance(h['results'], list)


def test_scan_range_too_large():
    # Large CIDR should be rejected by server (limit enforced)
    r = client.post('/network/scan_range', json={"cidr": "10.0.0.0/16"})
    assert r.status_code == 400
    j = r.json()
    assert 'detail' in j and 'too large' in j['detail'].lower()
