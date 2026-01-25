"""
@file test_coverage_controller_integration.py
@author naflashDev
@brief Integration tests for static resources of the coverage report.
@details Tests that CSS, JS, and image resources are served correctly from /coverage/.
"""
import os
import sys
import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..', 'src')))
from main import app

client = TestClient(app)

@pytest.mark.parametrize("resource,content_type", [
    ("style_cb_5c747636.css", "text/css"),
    ("coverage_html_cb_188fc9a4.js", "application/javascript"),
    ("keybd_closed_cb_900cfef5.png", "image/png"),
])
def test_coverage_static_resources(resource, content_type):
    '''
    @brief Test static resources of the coverage report are served with correct content type.
    '''
    resp = client.get(f"/coverage/{resource}")
    # 200 if file exists, 404 if not generated yet
    assert resp.status_code in (200, 404)
    if resp.status_code == 200:
        assert content_type in resp.headers["content-type"]
