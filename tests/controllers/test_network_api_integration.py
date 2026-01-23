"""
@file test_network_api_integration.py
@author naflashDev
@brief Unit tests for network API integration endpoints.
@details Tests FastAPI endpoints for network API integration, including port listing and response validation.
"""
import json

import pytest
from fastapi.testclient import TestClient

from main import app


client = TestClient(app)


def test_get_common_ports():
    r = client.get('/network/ports')
    assert r.status_code == 200
    j = r.json()
    assert 'common_ports' in j
    assert isinstance(j['common_ports'], list)
    assert any('port' in it and 'service' in it for it in j['common_ports'])


def test_post_scan_fallback(monkeypatch):
    # patch the scan_ports function to avoid real networking
    def fake_scan(host, ports=None, timeout=0.5):
        return [{'port': 80, 'open': True, 'service': 'http', 'methods': ['HTTP'], 'vulnerabilities': []}]

    monkeypatch.setattr('app.services.network_analysis.network_analysis.scan_ports', fake_scan)
    payload = {'host': '127.0.0.1', 'use_nmap': False}
    r = client.post('/network/scan', json=payload)
    assert r.status_code == 200
    j = r.json()
    assert j.get('host') == '127.0.0.1'
    assert 'results' in j and isinstance(j['results'], list)
    assert 'duration_seconds' in j
