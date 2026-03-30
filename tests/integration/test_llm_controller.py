import sys
import types
import importlib
from fastapi import FastAPI
from fastapi.testclient import TestClient


def _inject_fakes():
    # Fake chromadb and sentence_transformers and create a real module for app.services.llm.llm_client
    import types
    from types import ModuleType

    class FakeArray:
        def __init__(self, d):
            self._d = d
        def tolist(self):
            return self._d

    class FakeModel:
        def __init__(self, name=None):
            pass
        def encode(self, texts, show_progress_bar=False):
            return FakeArray([[0.1] * 8 for _ in texts])

    # chromadb module shim
    chromadb_mod = ModuleType('chromadb')
    def chromadb_client_factory(settings=None):
        return types.SimpleNamespace(get_collection=lambda name: types.SimpleNamespace(add=lambda *a, **k: None, upsert=lambda *a, **k: None, query=lambda *a, **k: {"ids": [["x"]], "documents": [["doc"]], "metadatas": [[{"source": "s1"}]], "distances": [[0.0]]}, get=lambda *a, **k: {"ids": [["x"]]}, delete=lambda *a, **k: None))
    chromadb_mod.Client = chromadb_client_factory
    chromadb_config = ModuleType('chromadb.config')
    chromadb_config.Settings = lambda **kwargs: None
    sys.modules['chromadb'] = chromadb_mod
    sys.modules['chromadb.config'] = chromadb_config

    # sentence_transformers shim
    st_mod = ModuleType('sentence_transformers')
    st_mod.SentenceTransformer = FakeModel
    sys.modules['sentence_transformers'] = st_mod

    # Ensure package modules exist and inject a ModuleType for the llm client
    app_mod = sys.modules.get('app') or ModuleType('app')
    services_mod = sys.modules.get('app.services') or ModuleType('app.services')
    llm_pkg = sys.modules.get('app.services.llm') or ModuleType('app.services.llm')
    llm_client_mod = ModuleType('app.services.llm.llm_client')
    def fake_query_llm(*args, **kwargs):
        # Accept either prompt=..., messages=[{role,content}] or positional
        if 'messages' in kwargs:
            msgs = kwargs.get('messages') or []
            # prefer last user content
            for m in reversed(msgs):
                if isinstance(m, dict) and m.get('role') == 'user' and m.get('content'):
                    return f'FAKE_RESPONSE'
            return 'FAKE_RESPONSE'
        if args:
            first = args[0]
            if isinstance(first, str):
                return 'FAKE_RESPONSE'
            if isinstance(first, list):
                for m in reversed(first):
                    if isinstance(m, dict) and m.get('role') == 'user' and m.get('content'):
                        return 'FAKE_RESPONSE'
                return 'FAKE_RESPONSE'
        return 'FAKE_RESPONSE'
    llm_client_mod.query_llm = fake_query_llm
    # also provide a llm_trainer module used by the controller
    llm_trainer_mod = ModuleType('app.services.llm.llm_trainer')
    def fake_run_periodic_training(stop_event=None):
        return None
    llm_trainer_mod.run_periodic_training = fake_run_periodic_training
    # mark package modules so Python import machinery treats them as packages
    for m in (app_mod, services_mod, llm_pkg):
        if not getattr(m, '__path__', None):
            m.__path__ = []

    # attach submodules as attributes to mimic package structure
    llm_pkg.llm_client = llm_client_mod
    services_mod.llm = llm_pkg
    app_mod.services = services_mod

    # insert into sys.modules for direct import resolution
    sys.modules['app'] = app_mod
    sys.modules['app.services'] = services_mod
    sys.modules['app.services.llm'] = llm_pkg
    sys.modules['app.services.llm.llm_client'] = llm_client_mod


def test_llm_query_flow(tmp_path):
    # Inject fakes before importing router to avoid import-time failures
    _inject_fakes()
    # Ensure any real module's function is overridden with our fake
    try:
        import importlib
        real_mod = importlib.import_module('app.services.llm.llm_client')
        # replace query_llm if present
        if hasattr(real_mod, 'query_llm'):
            real_mod.query_llm = sys.modules.get('app.services.llm.llm_client').query_llm
    except Exception:
        # ignore; if module not importable, our sys.modules shim will be used
        pass
    # configure DB to use in-memory for tests
    import app.models.db as db
    db.set_db_url("sqlite:///:memory:")
    # import models and create tables
    import app.models.conversation as conv_mod
    db.Base.metadata.create_all(bind=db.engine)

    # import the router after fakes and DB prepared
    import app.controllers.routes.llm_controller as llm_controller
    # ensure the controller uses our fake query_llm even if import-time binding picked real one
    if hasattr(llm_controller, 'query_llm'):
        llm_controller.query_llm = sys.modules.get('app.services.llm.llm_client').query_llm

    app = FastAPI()
    app.include_router(llm_controller.router)
    client = TestClient(app)

    # create a conversation
    r = client.post('/llm/conversations', json={"title": "test conv"})
    assert r.status_code == 200
    data = r.json()
    conv_id = data['id']

    # call query endpoint (this should use fake retriever and fake LLM)
    r2 = client.post('/llm/query', json={"prompt": "hello", "conversation_id": conv_id, "top_k": 1})
    assert r2.status_code == 200
    out = r2.json()
    assert out['response'] == 'FAKE_RESPONSE'
    assert isinstance(out.get('retrieved'), list)
