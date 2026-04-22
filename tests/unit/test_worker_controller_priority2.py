"""
@file test_worker_controller_priority2.py
@brief Additional worker_controller tests: unknown worker, dynamic_spider DB failure, shutdown endpoint.
"""
import asyncio
import types

import pytest

from fastapi import Response
from fastapi import BackgroundTasks as _BG

from app.controllers.routes import worker_controller as wc


def make_request_state():
    class AppState:
        pass

    class App:
        def __init__(self):
            self.state = AppState()

    return types.SimpleNamespace(app=App())


def test_toggle_unknown_worker_404(monkeypatch):
    monkeypatch.setattr(wc, 'load_worker_settings', lambda: {'known': True})
    req = make_request_state()
    with pytest.raises(Exception) as ei:
        asyncio.run(wc.toggle_worker('not_a_worker', wc.WorkerToggle(enabled=True), req))
    assert '404' in str(ei.value) or 'Unknown worker' in str(ei.value)


def test_toggle_dynamic_spider_db_create_fail_returns_503(monkeypatch, tmp_path):
    # Ensure settings include dynamic_spider
    monkeypatch.setattr(wc, 'load_worker_settings', lambda: {'dynamic_spider': False})
    monkeypatch.setattr(wc, 'save_worker_settings', lambda s: None)

    # Ensure pool is None so code attempts to create it
    req = make_request_state()
    req.app.state.worker_stop_events = {}
    req.app.state.worker_timers = {}
    req.app.state.worker_status = {}

    async def fake_create_pool(*a, **k):
        raise Exception('db fail')

    monkeypatch.setattr(wc.asyncpg, 'create_pool', fake_create_pool)

    res = asyncio.run(wc.toggle_worker('dynamic_spider', wc.WorkerToggle(enabled=True), req))
    assert isinstance(res, Response)
    assert res.status_code == 503


def test_shutdown_app_adds_background_task(monkeypatch):
    # Fake BackgroundTasks that records tasks but does not execute them
    class FakeBG:
        def __init__(self):
            self.tasks = []

        def add_task(self, fn):
            self.tasks.append(fn)

    req = make_request_state()
    bg = FakeBG()
    res = asyncio.run(wc.shutdown_app(bg, req))
    assert isinstance(res, dict)
    assert res.get('reload') is True
    assert any(callable(t) for t in bg.tasks)
