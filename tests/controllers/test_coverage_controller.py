"""
@file test_coverage_controller.py
@author naflashDev
@brief Unit tests for the coverage_controller endpoints.
@details Tests the /coverage/html endpoint for correct responses and error handling.
"""

import os
import sys
import pytest
from fastapi.testclient import TestClient

# Permitir importar main.py correctamente según la estructura del proyecto
WORKSPACE_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..'))
SRC_PATH = os.path.join(WORKSPACE_ROOT, 'src')
if SRC_PATH not in sys.path:
    sys.path.insert(0, SRC_PATH)
import sys
import importlib.util
import os
# Add src directory to sys.path for dynamic import
SRC_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src'))
if SRC_PATH not in sys.path:
    sys.path.insert(0, SRC_PATH)
spec = importlib.util.spec_from_file_location("main", os.path.join(SRC_PATH, "main.py"))
main = importlib.util.module_from_spec(spec)
spec.loader.exec_module(main)
app = main.app

client = TestClient(app)


# Build portable path for coverage HTML report
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..'))
COVERAGE_HTML_PATH = os.path.join(PROJECT_ROOT, 'htmlcov', 'index.html')

def test_coverage_html_exists(monkeypatch):
    '''
    @brief Test /coverage/html returns 200 and HTML if report exists.
    '''
    # Ensure the file exists for this test
    monkeypatch.setattr(os.path, 'exists', lambda p: True)
    fake_html = '<html><head><title>Coverage report</title></head><body>Coverage report</body></html>'
    monkeypatch.setattr('builtins.open', lambda *a, **k: type('F', (), {'__enter__': lambda s: s, '__exit__': lambda s, *a: None, 'read': lambda s: fake_html})())
    response = client.get('/coverage/html')
    assert response.status_code == 200
    assert 'text/html' in response.headers['content-type']
    assert b'Coverage report' in response.content

def test_coverage_html_not_found(monkeypatch):
    '''
    @brief Test /coverage/html returns 404 if report does not exist.
    '''
    monkeypatch.setattr(os.path, 'exists', lambda p: False)
    response = client.get('/coverage/html')
    assert response.status_code == 404
    assert b'Coverage report not found' in response.content
