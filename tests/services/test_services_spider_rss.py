import sys
from pathlib import Path
import unittest
import asyncio
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
SRC = str(ROOT / 'src')
if SRC not in sys.path:
    sys.path.insert(0, SRC)

from app.services.scraping import spider_rss as sr

class FakeProcess:
    def __init__(self, target, args=()):
        self._target = target
        self._args = args
    def start(self):
        # call target directly
        self._target(*self._args)
    def join(self):
        return

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

class TestSpiderRSSServices(unittest.TestCase):
    def test_read_urls_from_file(self):
        tmp = Path('tmp_urls.txt')
        tmp.write_text('https://example.com\n\nhttps://a.com\n')
        try:
            urls = sr.read_urls_from_file(str(tmp))
            self.assertIn('https://example.com', urls)
            self.assertIn('https://a.com', urls)
        finally:
            tmp.unlink()

    def test_extract_rss_and_save_flow(self):
        # Prepare a fake urls file content by patching read_urls_from_file
        with mock.patch('app.services.scraping.spider_rss.read_urls_from_file', return_value=['https://feed.example/rss']):
            # Patch Process to FakeProcess so spider runs synchronously and pushes results
            with mock.patch('app.services.scraping.spider_rss.Process', new=FakeProcess):
                # Patch feedparser.parse to return feed with entries
                fake_feed = mock.Mock()
                fake_feed.entries = [1]
                fake_feed.feed = {'title':'T','link':'https://site.example'}
                with mock.patch('app.services.scraping.spider_rss.feedparser.parse', return_value=fake_feed):
                    # Patch insert_feed_to_db to a dummy async function
                    async def fake_insert(conn, feed_data):
                        # simulate success
                        return
                    with mock.patch('app.services.scraping.spider_rss.insert_feed_to_db', side_effect=fake_insert):
                        # Also patch run_rss_spider to append the feed URL into the queue
                        def fake_run_spider(urls, queue):
                            queue.put(['https://feed.example/rss'])
                        with mock.patch('app.services.scraping.spider_rss.run_rss_spider', side_effect=fake_run_spider):
                            pool = DummyPool()
                            # run coroutine
                            asyncio.run(sr.extract_rss_and_save(pool, 'ignored'))

if __name__ == '__main__':
    unittest.main()
