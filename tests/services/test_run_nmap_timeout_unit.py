"""
@file test_run_nmap_timeout_unit.py
@author naflashDev
@brief Unit tests for nmap timeout handling in network service.
@details Tests timeout scenarios and error handling for nmap integration in the network service layer.
"""
import subprocess
import shutil
import pytest

from app.services.network_analysis import network_analysis as na


def test_run_nmap_scan_raises_timeout(monkeypatch):
    # Ensure nmap is 'found'
    monkeypatch.setattr('shutil.which', lambda name: '/usr/bin/nmap')

    def fake_run(args, capture_output, text, timeout):
        raise subprocess.TimeoutExpired(cmd=args, timeout=timeout)

    monkeypatch.setattr('subprocess.run', fake_run)

    with pytest.raises(subprocess.TimeoutExpired):
        na.run_nmap_scan('127.0.0.1', ports=None, timeout=1)
