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


def test_llm_query_post(monkeypatch):
    '''
    @brief Debe devolver respuesta simulada del LLM.
    '''
    from main import app
    client = TestClient(app)
    monkeypatch.setattr(llm_mod, 'query_llm', lambda prompt: f"Echo: {prompt}")
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
