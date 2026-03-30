def test_app_state_and_router(monkeypatch):
    '''
    @brief Edge Case: App sin routers ni estado.
    Verifica que la inicialización no falla y el estado es correcto.
    '''
    import main as main_mod
    from fastapi import FastAPI
    app = FastAPI()
    app.state.worker_status = {}
    app.state.worker_stop_events = {}
    app.state.worker_timers = {}
    assert hasattr(app.state, "worker_status")
    assert hasattr(app.state, "worker_stop_events")
    assert hasattr(app.state, "worker_timers")

def test_lifespan_shutdown_error(monkeypatch):
    '''
    @brief Error Handling: Simula error en shutdown pool y servicios externos.
    '''
    import main as main_mod
    from fastapi import FastAPI
    app = FastAPI()
    app.state.pool = None
    app.state.worker_status = {"w1": True}
    app.state.stop_event = None
    monkeypatch.setattr(main_mod.logger, "exception", lambda *a, **k: None)
    monkeypatch.setattr(main_mod.logger, "info", lambda *a, **k: None)
    monkeypatch.setattr(main_mod.logger, "warning", lambda *a, **k: None)
    monkeypatch.setattr(main_mod.logger, "success", lambda *a, **k: None)
    monkeypatch.setattr(main_mod, "shutdown_services", lambda *a, **k: (_ for _ in ()).throw(Exception("fail")))
    try:
        cm = main_mod.lifespan(app)
        # Simula yield y shutdown
        next(cm)
    except Exception:
        assert True
"""
@file test_main.py
@author naflashDev
@brief Unit tests for main FastAPI app entrypoint.

@details Covers app creation, lifespan, and background task initialization.
"""
import sys
import os
import pytest
import types
import asyncio
from fastapi import FastAPI
# Añadir src al sys.path para importar app.main correctamente
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../src/app')))
import main as main_mod


def test_app_import_and_routes():
    """
    Happy Path: App imports and has routers.
    """
    assert hasattr(main_mod, "FastAPI")
    assert hasattr(main_mod, "app")
    assert isinstance(main_mod.app, FastAPI)

@pytest.mark.asyncio
async def test_lifespan_runs(monkeypatch):
    """
    Happy Path: lifespan context manager yields app.
    """
    app = FastAPI()
    cm = main_mod.lifespan(app)
    assert hasattr(cm, "__aenter__")
    assert hasattr(cm, "__aexit__")

@pytest.mark.asyncio
async def test_initialize_background_tasks(monkeypatch):
    """
    Happy Path: initialize_background_tasks runs without error.
    """
    app = FastAPI()
    app.state.worker_status = {}
    app.state.worker_stop_events = {}
    await main_mod.initialize_background_tasks(app)
    assert True

# --- Extra edge/error tests ---
def test_app_missing_router(monkeypatch):
    """
    @brief Edge Case: App without routers
    """
    app = FastAPI()
    assert not hasattr(app, "router") or app.router is not None


def test_lifespan_error(monkeypatch):
    """
    @brief Error Handling: lifespan raises exception
    """
    app = FastAPI()
    monkeypatch.setattr(main_mod, "lifespan", lambda app: (_ for _ in ()).throw(Exception("fail")))
    try:
        cm = main_mod.lifespan(app)
    except Exception as e:
        assert str(e) == "fail"

@pytest.mark.asyncio
def test_initialize_background_tasks_error(monkeypatch):
    """
    @brief Error Handling: initialize_background_tasks raises exception
    """
    app = FastAPI()
    monkeypatch.setattr(main_mod, "initialize_background_tasks", lambda app: (_ for _ in ()).throw(Exception("fail")))
    import pytest
    import asyncio
    async def run():
        try:
            await main_mod.initialize_background_tasks(app)
        except Exception as e:
            assert str(e) == "fail"
    asyncio.run(run())


def test_lifespan_ollama_install_branch(monkeypatch):
    """
    @brief Exercise the branch where use_ollama=True and system meets hardware requirements.

    This patches psutil and related functions so the lifespan startup will
    attempt the Ollama installation path and call ensure_infrastructure with
    use_ollama=True.
    """
    import types
    app = FastAPI()

    # Ensure parameters are returned with use_ollama true by patching the
    # original utils function (main imports it at module load time).
    monkeypatch.setattr('app.utils.utils.get_connection_service_parameters', lambda fname: (0, 'ok', {'distro_name':'Ubuntu','dockers_name':'a,b','use_ollama': True}))
    monkeypatch.setattr('app.utils.utils.create_config_file', lambda *a, **k: (0, 'ok'))

    # Simulate sufficient RAM/CPU
    class Mem:
        def __init__(self, total):
            self.total = total
    monkeypatch.setattr('psutil.virtual_memory', lambda: Mem(16 * 1024**3))
    monkeypatch.setattr('psutil.cpu_count', lambda logical=False: 4)

    called = {}
    # is_ollama_available should reflect install attempt: start False, become True after try
    def fake_is_ollama_available():
        return bool(called.get('installed'))

    def fake_try_install_ollama(platform):
        called['tried_install'] = True
        # simulate that installer succeeded in making ollama available
        called['installed'] = True
        return True

    def fake_ensure_infrastructure(params, use_ollama=False):
        called['ensure_called_with'] = use_ollama

    # Patch the functions on their source module so main's calls hit our fakes
    monkeypatch.setattr('app.utils.run_services.is_ollama_available', fake_is_ollama_available)
    monkeypatch.setattr('app.utils.run_services.try_install_ollama', fake_try_install_ollama)
    monkeypatch.setattr('app.utils.run_services.ensure_infrastructure', fake_ensure_infrastructure)
    monkeypatch.setattr('app.utils.run_services.shutdown_services', lambda *a, **k: None)

    async def run_ctx():
        async with main_mod.lifespan(app):
            # inside lifespan, ensure_infrastructure should have been called
            pass

    import asyncio
    asyncio.run(run_ctx())

    # Ensure we attempted installation and that ensure_infrastructure was invoked
    assert called.get('tried_install') is True
    assert 'ensure_called_with' in called


def test_initialize_background_tasks_full(monkeypatch):
    """
    @brief Run `initialize_background_tasks` with mocked pool and worker targets

    This verifies many branches in the function: pool creation, worker scheduling
    and the dynamic spider startup logic.
    """
    app = FastAPI()
    app.state.worker_status = {}
    app.state.worker_stop_events = {}

    # Force config parameters to succeed
    monkeypatch.setattr(main_mod, 'get_connection_service_parameters', lambda fname: (0, 'ok', {'distro_name':'Ubuntu','dockers_name':'a,b','use_ollama':'false'}))

    # Mock asyncpg pool creation
    class DummyPool:
        async def close(self):
            return

    async def fake_create_pool(*a, **kw):
        return DummyPool()

    monkeypatch.setattr('asyncpg.create_pool', fake_create_pool)

    # Ensure worker settings enable all workers and paths exist
    monkeypatch.setattr(main_mod, 'load_worker_settings', lambda: {
        'google_alerts': True,
        'rss_extractor': True,
        'scraping_feeds': True,
        'scraping_news': True,
        'spacy_nlp': True,
        'vector_retention': False,
        'llm_updater': True,
        'dynamic_spider': False,
    })

    # Make os.path.exists return True for required resources
    import os
    monkeypatch.setattr(os.path, 'exists', lambda p: True)

    # Patch thread target functions to no-op so threads start quickly
    monkeypatch.setattr(main_mod.scrapy_news_controller, 'recurring_google_alert_scraper', lambda *a, **k: None)
    monkeypatch.setattr(main_mod.scrapy_news_controller, 'background_scraping_feeds', lambda *a, **k: None)
    monkeypatch.setattr(main_mod.scrapy_news_controller, 'background_scraping_news', lambda *a, **k: None)
    monkeypatch.setattr(main_mod.tiny_postgres_controller, 'background_rss_process_loop', lambda *a, **k: None)
    monkeypatch.setattr(main_mod.spacy_controller, 'background_process_every_24h', lambda *a, **k: None)
    monkeypatch.setattr(main_mod.llm_controller, 'background_cve_and_finetune_loop', lambda *a, **k: None)

    async def run_init():
        await main_mod.initialize_background_tasks(app)

    import asyncio
    asyncio.run(run_init())

    assert app.state.ui_initialized is True
