import sys
from pathlib import Path
import asyncio
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
SRC = str(ROOT / 'src')
if SRC not in sys.path:
    sys.path.insert(0, SRC)

from fastapi.testclient import TestClient
from fastapi import FastAPI
from app.controllers.routes.tiny_postgres_controller import router as ttrss_router
from app.models.ttrss_postgre_db import FeedResponse

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
    def __init__(self):
        pass
    def acquire(self):
        return DummyPool._Acquire()

class TestTinyPostgresController(unittest.TestCase):
    def setUp(self):
        app = FastAPI()
        app.include_router(ttrss_router)
        # attach dummy pool
        app.state.pool = DummyPool()
        self.client = TestClient(app)

    def test_feeds_endpoint_returns_list(self):
        # Mock get_feeds_from_db to return sample data
        sample = [FeedResponse(id=1, title='t', feed_url='u', site_url='s', owner_uid=1, cat_id=0)]
        async def fake_get_feeds(conn, limit):
            return sample

        with mock.patch('app.controllers.routes.tiny_postgres_controller.get_feeds_from_db', new=mock.AsyncMock(side_effect=fake_get_feeds)):
            resp = self.client.get('/postgre-ttrss/feeds')
            self.assertEqual(resp.status_code, 200)
            data = resp.json()
            self.assertIsInstance(data, list)
            self.assertEqual(data[0]['title'], 't')

    def test_search_and_insert_rss_missing_file(self):
        # Ensure file does not exist
        with mock.patch('os.path.exists', return_value=False):
            resp = self.client.get('/postgre-ttrss/search-and-insert-rss')
            self.assertEqual(resp.status_code, 404)

if __name__ == '__main__':
    unittest.main()
