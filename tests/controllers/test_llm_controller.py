"""
@file test_llm_controller.py
@author naflashDev
@brief Unit tests for LLM controller endpoints.
@details Tests FastAPI endpoints for LLM updater and query, patching background threads and validating responses.
"""
from fastapi.testclient import TestClient
import app.controllers.routes.llm_controller as llm_mod


class DummyThread:
    def __init__(self, *args, **kwargs):
        self._target = kwargs.get('target') or (args[0] if args else None)
        self._args = kwargs.get('args') or (args[1] if len(args) > 1 else ())
        self.daemon = kwargs.get('daemon', True)
    def start(self):
        return None


def test_llm_updater_endpoints(monkeypatch):
    from main import app
    monkeypatch.setattr(llm_mod.threading, 'Thread', DummyThread)
    client = TestClient(app)

    resp = client.get('/llm/updater')
    assert resp.status_code == 200
    data = resp.json()
    assert 'message' in data

    resp2 = client.get('/llm/stop-updater')
    assert resp2.status_code == 200
    data2 = resp2.json()
    assert 'message' in data2
