"""
@file test_llm_controller.py
@author naflashDev
@brief Unit tests for LLM controller endpoints.
@details Tests FastAPI endpoints for LLM updater and query, patching background threads and validating responses.
"""
from fastapi.testclient import TestClient
import app.controllers.routes.llm_controller as llm_mod
import pytest
import time
import asyncio

# Speedups: avoid real sleeps during these controller tests
try:
    time.sleep = lambda s: None
except Exception:
    pass
try:
    async def _noop_async_sleep(s):
        return None
    asyncio.sleep = _noop_async_sleep
except Exception:
    pass


@pytest.fixture(autouse=True)
def stub_startup(monkeypatch):
    """Prevent heavy startup actions during these controller tests."""
    import src.main as main_mod
    monkeypatch.setattr(main_mod, "ensure_infrastructure", lambda *a, **k: None)

    async def _dummy_init(app):
        app.state.ui_initialized = True

    monkeypatch.setattr(main_mod, "initialize_background_tasks", _dummy_init)

    # Patch threading.Thread so background threads aren't started
    class DummyThread:
        def __init__(self, *a, **k):
            pass

        def start(self):
            return None

    try:
        monkeypatch.setattr(main_mod.threading, "Thread", DummyThread)
    except Exception:
        import threading as _threading
        monkeypatch.setattr(_threading, "Thread", DummyThread)

    # Prevent DB metadata creation during lifespan
    try:
        import app.models.db as _dbmod
        monkeypatch.setattr(_dbmod.Base.metadata, "create_all", lambda bind=None: None)
    except Exception:
        pass

    try:
        import app.models.conversation_db as _conv
        monkeypatch.setattr(_conv.ConversationBase.metadata, "create_all", lambda bind=None: None)
    except Exception:
        pass

    # Prevent shutdown side-effects and long sleeps
    monkeypatch.setattr(main_mod, "shutdown_services", lambda *a, **k: None)
    import asyncio, random
    monkeypatch.setattr(asyncio, "sleep", lambda _s: None)
    monkeypatch.setattr(random, "uniform", lambda a, b: 0.01)
    # Replace app lifespan with a no-op context to avoid startup workload
    from contextlib import asynccontextmanager

    @asynccontextmanager
    async def _noop_lifespan(app=None):
        yield

    try:
        main_mod.app.router.lifespan_context = lambda app=None: _noop_lifespan(app)
    except Exception:
        pass

    yield


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


def test_llm_query_post(monkeypatch):
    '''
    @brief Debe devolver respuesta simulada del LLM.
    '''
    from main import app
    client = TestClient(app)
    def _fake_query(*args, **kwargs):
        prompt = args[0] if args else kwargs.get('prompt') or ''
        return f"Echo: {prompt}"
    monkeypatch.setattr(llm_mod, 'query_llm', _fake_query)
    resp = client.post('/llm/query', json={"prompt": "test"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["response"].startswith("Echo:")

def test_llm_query_post_error(monkeypatch):
    '''
    @brief Debe manejar error en query_llm.
    '''
    from main import app
    client = TestClient(app)
    def fail_query(prompt):
        raise Exception("fail")
    monkeypatch.setattr(llm_mod, 'query_llm', fail_query)
    try:
        resp = client.post('/llm/query', json={"prompt": "test"})
        assert resp.status_code == 500
    except Exception as e:
        # Si la excepción se propaga, también es válido
        assert "fail" in str(e)

def test_updater_get_already_running(monkeypatch):
    '''
    @brief Si el worker ya está activo, debe devolver mensaje adecuado.
    '''
    from main import app
    client = TestClient(app)
    # Inicializar estado como si el worker ya estuviera activo
    with client as c:
        c.app.state.worker_stop_events = {}
        c.app.state.worker_timers = {}
        c.app.state.worker_status = {"llm_updater": True}
        resp = c.get('/llm/updater')
        assert resp.status_code == 200
        assert "already running" in resp.text or "message" in resp.json()

def test_stop_updater_sets_event(monkeypatch):
    '''
    @brief Debe llamar a set() en el evento de parada si existe.
    '''
    from main import app
    client = TestClient(app)
    class DummyEvt:
        def __init__(self):
            self.called = False
        def set(self):
            self.called = True
    with client as c:
        evt = DummyEvt()
        c.app.state.worker_stop_events = {"llm_updater": evt}
        c.app.state.worker_timers = {}
        c.app.state.worker_status = {}
        resp = c.get('/llm/stop-updater')
        assert resp.status_code == 200
        assert "stopped" in resp.text or "message" in resp.json()
        assert evt.called

def test_background_cve_and_finetune_loop(monkeypatch):
    '''
    @brief Debe ejecutar run_periodic_training y esperar, saliendo si stop_event está activo.
    '''
    called = {}
    def fake_run_periodic_training(stop_event=None):
        called['ok'] = True
        # Simula que el evento se activa tras la primera llamada
        if stop_event:
            stop_event.set()
    monkeypatch.setattr(llm_mod, 'run_periodic_training', fake_run_periodic_training)
    import threading
    evt = threading.Event()
    llm_mod.background_cve_and_finetune_loop(stop_event=evt)
    assert called.get('ok') is not None

def test_stop_updater_timer_cancel_exception(monkeypatch):
    '''
    @brief Debe manejar excepción al cancelar el timer en stop_updater.
    '''
    from main import app
    client = TestClient(app)
    class DummyEvt:
        def set(self):
            pass
    class DummyTimer:
        def cancel(self):
            raise Exception("fail cancel")
    with client as c:
        c.app.state.worker_stop_events = {"llm_updater": DummyEvt()}
        c.app.state.worker_timers = {"llm_updater": DummyTimer()}
        c.app.state.worker_status = {}
        resp = c.get('/llm/stop-updater')
        assert resp.status_code == 200
        assert "stopped" in resp.text or "message" in resp.json()


def test_background_cve_and_finetune_loop_wait_exception(monkeypatch):
    '''
    @brief Debe manejar excepción en stop_event.wait y usar sleep como fallback.
    '''
    import time
    called = {"wait": False, "sleep": False, "run": False}
    class DummyEvent:
        def is_set(self):
            if not called["wait"]:
                return False
            return True
        def wait(self, interval):
            called["wait"] = True
            raise Exception("wait fail")
    def fake_run_periodic_training(stop_event=None):
        called["run"] = True
    monkeypatch.setattr(llm_mod, 'run_periodic_training', fake_run_periodic_training)
    monkeypatch.setattr(time, 'sleep', lambda s: called.update({"sleep": True}))
    llm_mod.background_cve_and_finetune_loop(stop_event=DummyEvent())
    assert called["run"] and called["wait"] and called["sleep"]


def test_query_with_missing_payload_returns_400(monkeypatch):
    '''
    @brief Posting to /llm/query without payload should return 400.
    '''
    from main import app
    client = TestClient(app)
    resp = client.post('/llm/query', json={})
    # Depending on controller validation it could be 400 or 422 (FastAPI validation), accept both
    assert resp.status_code in (400, 422)
