"""
@file test_integration_news_flow.py
@author naflashDev
@brief Integration tests for news scraping endpoints.
@details Tests FastAPI endpoints for news scraping and RSS feed ingestion, ensuring correct background job scheduling and data persistence.
"""
import sys
from pathlib import Path
import unittest
from unittest import mock
import asyncio

ROOT = Path(__file__).resolve().parents[2]
SRC = str(ROOT / 'src')
if SRC not in sys.path:
    sys.path.insert(0, SRC)

from fastapi.testclient import TestClient
from fastapi import FastAPI

from app.controllers.routes.scrapy_news_controller import router as news_router
from app.controllers.routes.tiny_postgres_controller import router as ttrss_router


class DummyPool:
    class _Conn:
        pass
    class _Acquire:
        def __init__(self):
            self.conn = DummyPool._Conn()
        async def __aenter__(self):
            return self.conn
        async def __aexit__(self, exc_type, exc, tb):
            return False
    def acquire(self):
        return DummyPool._Acquire()


class TestIntegrationNewsFlow(unittest.TestCase):
    def setUp(self):
        app = FastAPI()
        app.include_router(news_router)
        app.include_router(ttrss_router)
        app.state.pool = DummyPool()
        self.client = TestClient(app)

    def test_save_feed_and_trigger_scrape(self):
        # Prepare fake feedparser result
        fake_feed = mock.Mock()
        fake_feed.entries = [1]
        fake_feed.feed = {'title': 'FF', 'link': 'https://site.example'}

        async def fake_insert(conn, feed_data):
            # emulate DB insert
            return

        # run_dynamic_spider_from_db should be patched to return a completed future
        def fake_run_dynamic(pool):
            f = asyncio.Future()
            f.set_result(None)
            return f

        with mock.patch('feedparser.parse', return_value=fake_feed):
            with mock.patch('app.models.ttrss_postgre_db.insert_feed_to_db', side_effect=fake_insert):
                # save-feed-google-alerts should succeed
                resp = self.client.post('/newsSpider/save-feed-google-alerts', json={'feed_url': 'http://x'})
                self.assertEqual(resp.status_code, 200)

        # Trigger scrape-news which should create a background task
        with mock.patch('app.controllers.routes.scrapy_news_controller.run_dynamic_spider_from_db', new=fake_run_dynamic):
            with mock.patch('asyncio.create_task') as create_task_mock:
                resp2 = self.client.get('/newsSpider/scrape-news')
                self.assertEqual(resp2.status_code, 200)
                create_task_mock.assert_called()


if __name__ == '__main__':
    unittest.main()
