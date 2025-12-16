import types
import subprocess
from types import SimpleNamespace

import pytest

from app.services.network_analysis import network_analysis as na


class DummyConn:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


def test_scan_ports_tcp_monkeypatch(monkeypatch):
    # simulate port 22 open, others closed
    def fake_create_connection(addr, timeout=0.5):
        host, port = addr
        if port == 22:
            return DummyConn()
        raise OSError("refused")

    monkeypatch.setattr('socket.create_connection', fake_create_connection)
    res = na.scan_ports('127.0.0.1', ports=[22, 23], timeout=0.1)
    assert isinstance(res, list)
    assert any(r['port'] == 22 and r['open'] for r in res)
    assert any(r['port'] == 23 and not r['open'] for r in res)


def test_run_nmap_scan_parsing(monkeypatch):
    # provide fake nmap xml output
    xml = '''<?xml version="1.0"?>
<nmaprun>
  <host>
    <ports>
      <port protocol="tcp" portid="22">
        <state state="open"/>
        <service name="ssh" product="OpenSSH" version="7.9"/>
      </port>
    </ports>
  </host>
</nmaprun>
'''

    monkeypatch.setattr('shutil.which', lambda name: '/usr/bin/nmap')

    def fake_run(args, capture_output, text, timeout):
        return SimpleNamespace(returncode=0, stdout=xml, stderr='')

    monkeypatch.setattr('subprocess.run', fake_run)
    results, raw = na.run_nmap_scan('127.0.0.1', ports=None, timeout=5)
    assert raw
    assert isinstance(results, list)
    assert any(r['port'] == 22 and r['open'] and r['service'] == 'ssh' for r in results)
