"""
@file test_scrapy_news_controller_full.py
@author naflashDev
@brief Additional tests for scrapy_news_controller endpoints.
@details Covers /newsSpider/save-feed-google-alerts and /newsSpider/start-google-alerts endpoints.
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

def test_save_feed_google_alerts_invalid(monkeypatch):
    client = TestClient(app)
    monkeypatch.setattr('feedparser.parse', lambda url: mock.Mock(entries=[]))
    resp = client.post('/newsSpider/save-feed-google-alerts', json={'feed_url':'http://x'})
    assert resp.status_code == 400

def test_start_google_alerts_missing_file(monkeypatch):
    client = TestClient(app)
    monkeypatch.setattr('os.path.exists', lambda p: False)
    resp = client.get('/newsSpider/start-google-alerts')
    assert resp.status_code == 404
