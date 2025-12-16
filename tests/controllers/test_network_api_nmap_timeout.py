import subprocess
import shutil
import pytest
from fastapi.testclient import TestClient

from main import app


client = TestClient(app)


def test_network_scan_returns_504_on_nmap_timeout(monkeypatch):
    # nmap is present
    monkeypatch.setattr('shutil.which', lambda name: '/usr/bin/nmap')

    def fake_run(args, capture_output, text, timeout):
        raise subprocess.TimeoutExpired(cmd=args, timeout=timeout)

    monkeypatch.setattr('subprocess.run', fake_run)

    r = client.post('/network/scan', json={"host": "127.0.0.1", "use_nmap": True, "timeout": 1})
    assert r.status_code == 504
    j = r.json()
    assert 'timed out' in j.get('detail', '').lower() or 'timeout' in j.get('detail', '').lower()
