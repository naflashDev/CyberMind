import asyncio
import time

import pytest

from app.services.scraping import spider_rss as sr


def test_extract_rss_and_save_does_not_block_event_loop(monkeypatch, tmp_path):
    # Replace multiprocessing.Process and Queue with dummy implementations
    # so we don't attempt to pickle local functions on Windows spawn.
    def fake_run_rss_spider(urls, q):
        time.sleep(0.5)
        q.put(["http://example.com/feed"])

    class DummyQueue:
        def __init__(self):
            self._val = None
        def put(self, v):
            self._val = v
        def get(self):
            return self._val

    class DummyProcess:
        def __init__(self, target=None, args=()):
            self._target = target
            self._args = args
        def start(self):
            # run target synchronously in this thread (the thread created by asyncio.to_thread)
            if callable(self._target):
                self._target(*self._args)
        def join(self):
            return None

    monkeypatch.setattr(sr, 'Queue', DummyQueue)
    monkeypatch.setattr(sr, 'Process', DummyProcess)
    monkeypatch.setattr(sr, 'run_rss_spider', fake_run_rss_spider)

    # Patch insert_feed_to_db used inside module to be an async no-op
    async def fake_insert_feed_to_db(conn, feed_data):
        return None

    monkeypatch.setattr(sr, 'insert_feed_to_db', fake_insert_feed_to_db)

    # Provide a dummy pool with async acquire context manager
    class DummyConn:
        pass

    class DummyAcquire:
        def __init__(self, conn):
            self.conn = conn

        async def __aenter__(self):
            return self.conn

        async def __aexit__(self, exc_type, exc, tb):
            return False

    class DummyPool:
        def __init__(self):
            self._conn = DummyConn()

        def acquire(self):
            return DummyAcquire(self._conn)

    pool = DummyPool()

    # create a small urls file
    path = tmp_path / "urls.txt"
    path.write_text("http://example.com\n", encoding='utf-8')

    async def runner():
        # Event that a short-lived coroutine will set quickly if loop is responsive
        evt = asyncio.Event()

        async def short_task():
            await asyncio.sleep(0.05)
            evt.set()

        # Start both the short task and the long-running extract concurrently
        short = asyncio.create_task(short_task())
        extract_task = asyncio.create_task(sr.extract_rss_and_save(pool, str(path)))

        # If event is set while extract is running, loop was not blocked
        await asyncio.wait_for(evt.wait(), timeout=1.0)

        # wait for extract to finish
        await extract_task

    # Run the async runner
    asyncio.run(runner())
