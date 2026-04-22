"""
@file test_worker_controller_extra_branches.py
@brief Tests for additional worker_controller branches (spacy_nlp, llm_updater).
"""
import asyncio
import sys
import types
from pathlib import Path

import pytest

from app.controllers.routes import worker_controller as wc


class DummyThread:
    def __init__(self, target=None, args=(), daemon=True):
        self.target = target
        self.args = args
        self.daemon = daemon
        self.started = False

    def start(self):
        self.started = True


def make_request_state():
    class AppState:
        pass

    class App:
        def __init__(self):
            self.state = AppState()

    return types.SimpleNamespace(app=App())


def test_enable_spacy_nlp_starts_thread(monkeypatch, tmp_path):
    # ensure input file exists
    out_dir = Path('outputs')
    out_dir.mkdir(exist_ok=True)
    inp = out_dir / 'result.json'
    inp.write_text('{}')

    monkeypatch.setattr(wc, 'load_worker_settings', lambda: {'spacy_nlp': False})
    monkeypatch.setattr(wc, 'save_worker_settings', lambda s: None)

    started = {}

    def fake_thread_factory(target=None, args=(), daemon=True):
        started['target'] = target
        started['args'] = args
        return DummyThread(target=target, args=args, daemon=daemon)

    monkeypatch.setattr(wc.threading, 'Thread', fake_thread_factory)

    req = make_request_state()
    req.app.state.worker_stop_events = {}
    req.app.state.worker_timers = {}
    req.app.state.worker_status = {}

    res = asyncio.run(wc.toggle_worker('spacy_nlp', wc.WorkerToggle(enabled=True), req))
    # check stop event created and thread target recorded
    assert 'spacy_nlp' in req.app.state.worker_stop_events
    assert callable(started.get('target'))


def test_enable_llm_updater_starts_thread(monkeypatch):
    monkeypatch.setattr(wc, 'load_worker_settings', lambda: {'llm_updater': False})
    monkeypatch.setattr(wc, 'save_worker_settings', lambda s: None)

    # stub background function
    monkeypatch.setattr(wc.llm_controller, 'background_cve_and_finetune_loop', lambda evt: None)

    started = {}

    def fake_thread_factory(target=None, args=(), daemon=True):
        started['target'] = target
        started['args'] = args
        return DummyThread(target=target, args=args, daemon=daemon)

    monkeypatch.setattr(wc.threading, 'Thread', fake_thread_factory)

    req = make_request_state()
    req.app.state.worker_stop_events = {}
    req.app.state.worker_timers = {}
    req.app.state.worker_status = {}

    res = asyncio.run(wc.toggle_worker('llm_updater', wc.WorkerToggle(enabled=True), req))
    assert 'llm_updater' in req.app.state.worker_stop_events
    assert callable(started.get('target'))
