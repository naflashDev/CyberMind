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
from app.controllers.routes.scrapy_news_controller import router as news_router, LINKS_FILE
import feedparser

class DummyPool:
    pass

class TestScrapyNewsController(unittest.TestCase):
    def setUp(self):
        app = FastAPI()
        app.include_router(news_router)
        app.state.pool = DummyPool()
        self.client = TestClient(app)

    def test_save_feed_google_alerts_invalid(self):
        # feedparser returns empty entries -> 400
        with mock.patch('feedparser.parse', return_value=mock.Mock(entries=[])):
            resp = self.client.post('/newsSpider/save-feed-google-alerts', json={'feed_url':'http://x'})
            self.assertEqual(resp.status_code, 400)

    def test_save_feed_google_alerts_valid(self):
        fake_feed = mock.Mock()
        fake_feed.entries = [1]
        fake_feed.feed = {'title':'MyFeed'}
        with mock.patch('feedparser.parse', return_value=fake_feed):
            # patch LINKS_FILE to a temp path to avoid writing repo files
            tmp = Path('tmp_links.txt')
            try:
                with mock.patch('app.controllers.routes.scrapy_news_controller.LINKS_FILE', tmp):
                    resp = self.client.post('/newsSpider/save-feed-google-alerts', json={'feed_url':'http://x'})
                    self.assertEqual(resp.status_code, 200)
                    data = resp.json()
                    self.assertIn('message', data)
            finally:
                if tmp.exists():
                    tmp.unlink()

    def test_scrape_news_calls_create_task(self):
        # avoid creating an un-awaited coroutine by returning a completed Future
        def fake_task(pool):
            f = asyncio.Future()
            f.set_result(None)
            return f

        with mock.patch('app.controllers.routes.scrapy_news_controller.run_dynamic_spider_from_db', new=fake_task):
            with mock.patch('asyncio.create_task') as create_mock:
                resp = self.client.get('/newsSpider/scrape-news')
                self.assertEqual(resp.status_code, 200)
                create_mock.assert_called()

    def test_start_google_alerts_missing_file(self):
        with mock.patch('os.path.exists', return_value=False):
            resp = self.client.get('/newsSpider/start-google-alerts')
            self.assertEqual(resp.status_code, 404)

    def test_start_google_alerts_starts_thread(self):
        with mock.patch('os.path.exists', return_value=True):
            with mock.patch('app.controllers.routes.scrapy_news_controller.threading.Thread') as ThreadMock:
                resp = self.client.get('/newsSpider/start-google-alerts')
                self.assertEqual(resp.status_code, 200)
                ThreadMock.assert_called()

if __name__ == '__main__':
    unittest.main()
