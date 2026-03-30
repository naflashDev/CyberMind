import threading
from types import SimpleNamespace
import asyncio

import pytest
from fastapi import HTTPException

from app.controllers.routes.worker_controller import toggle_worker, WorkerToggle


class DummyReq:
    def __init__(self):
        self.app = SimpleNamespace()
        self.app.state = SimpleNamespace()
        # initialize dicts used by the controller
        self.app.state.worker_stop_events = {}
        self.app.state.worker_timers = {}
        self.app.state.worker_status = {}


def test_unknown_worker_raises():
    req = DummyReq()
    with pytest.raises(HTTPException):
        asyncio.run(toggle_worker("__not_a_worker__", WorkerToggle(enabled=True), req))


def test_disable_worker_signals_and_updates(monkeypatch):
    # monkeypatch load/save to avoid file IO
    monkeypatch.setattr('app.controllers.routes.worker_controller.load_worker_settings', lambda: {'test_worker': True})
    monkeypatch.setattr('app.controllers.routes.worker_controller.save_worker_settings', lambda s: None)

    req = DummyReq()
    evt = threading.Event()
    req.app.state.worker_stop_events['test_worker'] = evt
    req.app.state.worker_timers['test_worker'] = None
    req.app.state.worker_status['test_worker'] = True

    res = asyncio.run(toggle_worker('test_worker', WorkerToggle(enabled=False), req))
    assert isinstance(res, dict)
    assert 'disabled' in res.get('message') or 'disabled' in res.get('message').lower()
    assert req.app.state.worker_status['test_worker'] is False
    assert evt.is_set() is True
