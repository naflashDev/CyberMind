"""
@file test_worker_controller_extra.py
@brief Tests for worker_controller enabling/disabling workers with mocked threads
"""
import types
import threading
import asyncio
import pytest

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


def test_get_workers_combines_defaults_and_status():
    import asyncio
    from app.controllers.routes import worker_controller
    # build request with app.state
    req = types.SimpleNamespace()
    req.app = types.SimpleNamespace(state=types.SimpleNamespace())
    # ensure expected state dicts exist
    req.app.state.worker_status = {}
    req.app.state.worker_stop_events = {}
    req.app.state.worker_timers = {}
    # add an extra status key not present in defaults
    req.app.state.worker_status['custom_worker'] = True
    res = asyncio.run(worker_controller.get_workers(req))
    assert 'settings' in res and 'status' in res
    assert res['status'].get('custom_worker') is True


def test_shutdown_app_adds_background_task():
    import asyncio
    from types import SimpleNamespace
    from app.controllers.routes import worker_controller

    tasks = []
    class FakeBG:
        def add_task(self, fn, *a, **kw):
            tasks.append(fn)

    req = types.SimpleNamespace()
    req.app = types.SimpleNamespace(state=types.SimpleNamespace())
    bg = FakeBG()
    res = asyncio.run(worker_controller.shutdown_app(bg, req))
    assert isinstance(res, dict)
    assert res.get('reload') is True
    assert len(tasks) == 1


def test_toggle_worker_unknown_and_disable_and_enable_checks():
    import asyncio
    from types import SimpleNamespace
    from fastapi import HTTPException
    from app.controllers.routes import worker_controller

    req = types.SimpleNamespace()
    req.app = types.SimpleNamespace(state=types.SimpleNamespace())

    # unknown worker should raise
    with pytest.raises(HTTPException):
        asyncio.run(worker_controller.toggle_worker('no_exists', SimpleNamespace(enabled=True), req))

    # disable existing worker
    from app.utils.worker_control import default_settings
    name = 'rss_extractor'
    res = asyncio.run(worker_controller.toggle_worker(name, SimpleNamespace(enabled=False), req))
    assert isinstance(res, dict)
    assert 'disabled' in res.get('message', '')
    assert req.app.state.worker_status.get(name) is False

    # enabling google_alerts should fail when feeds file missing
    with pytest.raises(HTTPException):
        asyncio.run(worker_controller.toggle_worker('google_alerts', SimpleNamespace(enabled=True), req))

    # enabling spacy_nlp should fail when input file missing
    with pytest.raises(HTTPException):
        asyncio.run(worker_controller.toggle_worker('spacy_nlp', SimpleNamespace(enabled=True), req))


def test_enable_llm_updater_starts(monkeypatch):
    import asyncio
    from app.controllers.routes import worker_controller

    req = types.SimpleNamespace()
    req.app = types.SimpleNamespace(state=types.SimpleNamespace())
    req.app.state.worker_status = {}
    req.app.state.worker_stop_events = {}
    req.app.state.worker_timers = {}

    # prevent real threading and immediately invoke target
    created = {}
    class FakeThread:
        def __init__(self, target, args=(), daemon=False):
            created['target'] = target
            created['args'] = args
        def start(self):
            try:
                created['target'](*created['args'])
            except Exception:
                pass

    monkeypatch.setattr(worker_controller, 'threading', types.SimpleNamespace(Thread=FakeThread, Event=threading.Event))
    monkeypatch.setitem(worker_controller.__dict__, 'llm_controller', types.SimpleNamespace(background_cve_and_finetune_loop=lambda evt: None))

    async def call_enable():
        return await worker_controller.toggle_worker('llm_updater', types.SimpleNamespace(enabled=True), req)

    res = asyncio.run(call_enable())
    assert 'message' in res and 'enabled' in res['message']


def test_vector_ingest_start_and_folder_creation(monkeypatch, tmp_path):
    import asyncio
    from app.controllers.routes import worker_controller

    req = types.SimpleNamespace()
    req.app = types.SimpleNamespace(state=types.SimpleNamespace())
    req.app.state.worker_status = {}
    req.app.state.worker_stop_events = {}
    req.app.state.worker_timers = {}

    # monkeypatch os.makedirs to use tmp_path
    import os as _os
    def fake_makedirs(path, exist_ok=False):
        (tmp_path / 'data' / 'documents').mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(_os, 'makedirs', fake_makedirs)

    # prevent real threading
    created = {}
    class FakeThread2:
        def __init__(self, target, args=(), daemon=False):
            created['target'] = target
            created['args'] = args
        def start(self):
            try:
                created['target'](*created['args'])
            except Exception:
                pass

    monkeypatch.setattr(worker_controller, 'threading', types.SimpleNamespace(Thread=FakeThread2, Event=threading.Event))

    async def call_enable():
        return await worker_controller.toggle_worker('vector_ingest', types.SimpleNamespace(enabled=True), req)

    res = asyncio.run(call_enable())
    assert 'message' in res
