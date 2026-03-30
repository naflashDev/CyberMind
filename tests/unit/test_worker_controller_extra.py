"""
@file test_worker_controller_extra.py
@brief Tests for worker_controller enabling/disabling workers with mocked threads
"""
import types
import threading
import asyncio

from fastapi import HTTPException

from app.controllers.routes import worker_controller


class DummyTimer:
    def __init__(self):
        self.cancelled = False

    def cancel(self):
        self.cancelled = True


def test_toggle_vector_retention_enable_disable(monkeypatch):
    # prepare load_worker_settings to include vector_retention
    monkeypatch.setattr(worker_controller, 'load_worker_settings', lambda: {'vector_retention': False})

    # prevent actual threading.Thread from starting
    created = {}

    class FakeThread:
        def __init__(self, target, args=(), daemon=False):
            created['target'] = target
            created['args'] = args
        def start(self):
            # call target synchronously for test safety
            try:
                created['target'](*created['args'])
            except Exception:
                pass

    monkeypatch.setattr(worker_controller, 'threading', types.SimpleNamespace(Thread=FakeThread, Event=threading.Event))

    # monkeypatch retention worker to a no-op function
    def fake_retention(evt, days, hours):
        # set event to stop immediately
        try:
            evt.set()
        except Exception:
            pass

    monkeypatch.setitem(worker_controller.__dict__, 'scrapy_news_controller', types.SimpleNamespace())
    monkeypatch.setitem(worker_controller.__dict__, 'tiny_postgres_controller', types.SimpleNamespace())
    monkeypatch.setitem(worker_controller.__dict__, 'spacy_controller', types.SimpleNamespace())
    monkeypatch.setitem(worker_controller.__dict__, 'llm_controller', types.SimpleNamespace())
    # ensure retention import resolves to our fake
    import importlib
    # Inject fake module into import system so __import__ in code finds it
    import sys
    modname = 'app.controllers.routes.retention_worker'
    sys.modules[modname] = types.SimpleNamespace(vector_and_message_retention=fake_retention)

    # build request with app.state
    req = types.SimpleNamespace()
    req.app = types.SimpleNamespace(state=types.SimpleNamespace())

    payload = types.SimpleNamespace(enabled=True)

    # call async toggle via asyncio.run
    async def call_enable():
        return await worker_controller.toggle_worker('vector_retention', payload, req)

    res = asyncio.run(call_enable())
    assert 'message' in res

    # Now disable
    monkeypatch.setattr(worker_controller, 'load_worker_settings', lambda: {'vector_retention': True})
    payload2 = types.SimpleNamespace(enabled=False)

    async def call_disable():
        return await worker_controller.toggle_worker('vector_retention', payload2, req)

    res2 = asyncio.run(call_disable())
    assert 'message' in res2
