"""
@file test_scan_range_end.py
@author naflashDev
@brief Unit tests for scan_range_end service helpers.
@details Tests helper functions and logic in the scan_range_end service layer, including range validation and edge cases.
"""
import sys
import os
import asyncio

sys.path.insert(0, os.path.abspath('src'))

from app.services.network_analysis.network_analysis import scan_range


def test_scan_range_prefers_start_end():
    # Use a small range and ensure the 'end' IP is included when both
    # `cidr` and `start`/`end` are provided in the payload.
    result = asyncio.run(scan_range(cidr='10.0.3.0/24', start='10.0.3.0', end='10.0.3.10', use_nmap=False, ports=[22], concurrency=2, timeout=0.5))
    assert isinstance(result, dict)
    assert result.get('scanned') == 11
    hosts = [h.get('host') for h in result.get('hosts', [])]
    assert hosts[0] == '10.0.3.0'
    assert hosts[-1] == '10.0.3.10'
    assert len(hosts) == 11
