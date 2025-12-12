from fastapi.testclient import TestClient
from main import app


def test_scrape_news_sets_dynamic_spider_status(monkeypatch):
    client = TestClient(app)

    # call endpoint (scrape-news should be tolerant of missing pool)
    resp = client.get('/newsSpider/scrape-news')
    assert resp.status_code == 200

    # status should report the dynamic_spider worker as running
    status = client.get('/status')
    assert status.status_code == 200
    data = status.json()
    assert data.get('workers', {}).get('dynamic_spider', False) is True
