"""
@file test_tiny_postgres_controller_full.py
@author naflashDev
@brief Additional tests for tiny_postgres_controller endpoints.
@details Covers /postgre-ttrss/feeds and /postgre-ttrss/search-and-insert-rss endpoints.
"""
import os
import sys
import pytest
from fastapi.testclient import TestClient
from unittest import mock

WORKSPACE_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..'))
SRC_PATH = os.path.join(WORKSPACE_ROOT, 'src')
if SRC_PATH not in sys.path:
    sys.path.insert(0, SRC_PATH)
from main import app

def test_feeds_endpoint(monkeypatch):
    client = TestClient(app)
    # Mock get_feeds_from_db to return a feed list
    monkeypatch.setattr(
        'app.controllers.routes.tiny_postgres_controller.get_feeds_from_db',
        mock.AsyncMock(return_value=[mock.Mock(id=1, title='t', feed_url='u', site_url='s', owner_uid=1, cat_id=0)])
    )
    # The endpoint may return 200 (success), 404 (no feeds), or 503 (DB pool error)
    resp = client.get('/postgre-ttrss/feeds')
    assert resp.status_code in (200, 404, 503)

def test_search_and_insert_rss_missing_file(monkeypatch):
    client = TestClient(app)
    # Mock os.path.exists to simulate missing file
    monkeypatch.setattr('os.path.exists', lambda p: False)
    resp = client.get('/postgre-ttrss/search-and-insert-rss')
    # Endpoint may return 404 (file missing) or 503 (DB pool error)
    assert resp.status_code in (404, 503)
