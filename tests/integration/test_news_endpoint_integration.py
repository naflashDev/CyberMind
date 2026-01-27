"""
@file test_news_endpoint_integration.py
@author naflashDev
@brief Integration test for news endpoint and dynamic spider status.
@details Verifies that scraping news sets the correct worker status and endpoint returns expected results.
"""
from fastapi.testclient import TestClient
from main import app



def test_scrape_news_sets_dynamic_spider_status(monkeypatch):
    '''
    @brief Happy Path: Scraping news sets dynamic_spider status.
    Mocks background pool and validates endpoint interaction and status reporting.
    '''
    # Arrange
    from unittest.mock import patch
    client = TestClient(app)

    # Mock background pool and any DB/service calls if needed
    with patch('main.app.state', create=True) as mock_state:
        mock_state.pool = None  # Simula que no hay pool real

        # Act
        resp = client.get('/newsSpider/scrape-news')
        # Assert
        assert resp.status_code == 200

        # Act
        status = client.get('/status')
        # Assert
        assert status.status_code == 200
        data = status.json()
        assert data.get('workers', {}).get('dynamic_spider', False) is True
