"""
@file test_scraping_news_worker.py
@author naflashDev
@brief Unit tests for news scraping worker endpoints.
@details Tests FastAPI endpoints and background job logic for news scraping, ensuring correct status updates and error handling.
"""
from fastapi.testclient import TestClient
import app.controllers.routes.scrapy_news_controller as scrapy_mod

class DummyThread:
    def __init__(self, *args, **kwargs):
        self._target = kwargs.get('target') or (args[0] if args else None)
        self._args = kwargs.get('args') or (args[1] if len(args) > 1 else ())
        self.daemon = kwargs.get('daemon', True)
    def start(self):
        return None


def test_start_scraping_news_updates_status(monkeypatch):
    from main import app
    monkeypatch.setattr(scrapy_mod.threading, 'Thread', DummyThread)
    client = TestClient(app)

    # call start endpoint (note router prefix /newsSpider)
    resp = client.get('/newsSpider/scrapy/google-dk/news')
    assert resp.status_code == 200

    # now request workers
    workers_resp = client.get('/workers')
    assert workers_resp.status_code == 200
    data = workers_resp.json()
    assert 'status' in data
    assert data['status'].get('scraping_news', False) is True
