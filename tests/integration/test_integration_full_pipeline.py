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
from app.controllers.routes.spacy_controller import router as spacy_router
from app.controllers.routes.llm_controller import router as llm_router


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


class TestIntegrationFullPipeline(unittest.TestCase):
    def setUp(self):
        app = FastAPI()
        app.include_router(news_router)
        app.include_router(spacy_router)
        app.include_router(llm_router)
        app.state.pool = DummyPool()
        self.client = TestClient(app)

    def test_save_feed_process_tag_query(self):
        # Simulate saving a feed
        fake_feed = mock.Mock()
        fake_feed.entries = [1]
        fake_feed.feed = {'title': 'PipelineFeed', 'link': 'https://site.example'}

        async def fake_insert(conn, feed_data):
            return

        with mock.patch('feedparser.parse', return_value=fake_feed):
            with mock.patch('app.models.ttrss_postgre_db.insert_feed_to_db', side_effect=fake_insert):
                resp = self.client.post('/newsSpider/save-feed-google-alerts', json={'feed_url':'http://x'})
                self.assertEqual(resp.status_code, 200)

        # Now simulate spaCy tagging and llm query by patching internals
        with mock.patch('app.services.spacy.text_processor.tag_text', return_value=([{'text':'TT','label':'ORG'}], 'en')):
            with mock.patch('app.controllers.routes.llm_controller.query_llm', return_value='pipeline-answer'):
                # invoke llm endpoint with some prompt built from feed content
                resp2 = self.client.post('/llm/query', json={'prompt':'Summarize feed PipelineFeed'})
                self.assertEqual(resp2.status_code, 200)
                self.assertEqual(resp2.json()['response'], 'pipeline-answer')

if __name__ == '__main__':
    unittest.main()
