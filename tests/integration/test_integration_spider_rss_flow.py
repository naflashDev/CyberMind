import sys
from pathlib import Path
import unittest
from unittest import mock
import asyncio

ROOT = Path(__file__).resolve().parents[2]
SRC = str(ROOT / 'src')
if SRC not in sys.path:
    sys.path.insert(0, SRC)

from app.services.scraping import spider_rss as sr


class DummyConn:
    pass

class DummyPool:
    def acquire(self):
        class Ctx:
            async def __aenter__(self):
                return DummyConn()
            async def __aexit__(self, exc_type, exc, tb):
                return False
        return Ctx()


class TestIntegrationSpiderRSSFlow(unittest.TestCase):
    def test_extract_and_save_end_to_end(self):
        # Patch external feedparser and DB insert
        fake_feed = mock.Mock()
        fake_feed.entries = [1]
        fake_feed.feed = {'title': 'IntFeed', 'link': 'https://site.example'}

        async def fake_insert(conn, feed_data):
            return

        with mock.patch('app.services.scraping.spider_rss.feedparser.parse', return_value=fake_feed):
            with mock.patch('app.models.ttrss_postgre_db.insert_feed_to_db', side_effect=fake_insert):
                pool = DummyPool()
                asyncio.run(sr.extract_rss_and_save(pool, 'ignored'))

if __name__ == '__main__':
    unittest.main()
