"""
@file test_e2e_pipelines.py
@author naflashDev
@brief End-to-end tests for multiple API pipelines.
@details E2E tests for various API pipelines, patching external services and using test doubles for DB and network utilities to avoid side effects.
"""
"""
Suite de tests E2E para varias pipelines de la API.

Los tests evitan efectos secundarios parcheando funciones que arrancan
servicios externos, creando dobles ligeros para conexiones a BD y devolviendo
respuestas controladas de las utilidades de red.
"""
import asyncio
import types
import threading
import pytest

from fastapi.testclient import TestClient

from src import main


@pytest.fixture(autouse=True)
def global_patches(monkeypatch):
    # Evitar arranques pesados y operaciones externas
    monkeypatch.setattr(main, "ensure_infrastructure", lambda params: None)

    async def _dummy_init(app):
        app.state.ui_initialized = True

    monkeypatch.setattr(main, "initialize_background_tasks", _dummy_init)

    # Patch background worker functions to no-op so threads don't execute network/DB
    from src.app.controllers.routes import (
        scrapy_news_controller,
        spacy_controller,
        tiny_postgres_controller,
        llm_controller,
        network_analysis_controller,
    )

    monkeypatch.setattr(scrapy_news_controller, "background_scraping_feeds", lambda *a, **k: None)
    monkeypatch.setattr(scrapy_news_controller, "background_scraping_news", lambda *a, **k: None)
    monkeypatch.setattr(scrapy_news_controller, "recurring_google_alert_scraper", lambda *a, **k: None)
    monkeypatch.setattr(spacy_controller, "background_process_every_24h", lambda *a, **k: None)
    monkeypatch.setattr(tiny_postgres_controller, "background_rss_process_loop", lambda *a, **k: None)
    monkeypatch.setattr(llm_controller, "background_cve_and_finetune_loop", lambda *a, **k: None)

    # Also patch the same symbols on the modules imported as `app.*` (FastAPI imports these)
    import importlib
    app_scrapy = importlib.import_module("app.controllers.routes.scrapy_news_controller")
    app_spacy = importlib.import_module("app.controllers.routes.spacy_controller")
    app_tiny = importlib.import_module("app.controllers.routes.tiny_postgres_controller")
    app_llm = importlib.import_module("app.controllers.routes.llm_controller")
    app_net = importlib.import_module("app.controllers.routes.network_analysis_controller")

    monkeypatch.setattr(app_scrapy, "background_scraping_feeds", lambda *a, **k: None)
    monkeypatch.setattr(app_scrapy, "background_scraping_news", lambda *a, **k: None)
    monkeypatch.setattr(app_scrapy, "recurring_google_alert_scraper", lambda *a, **k: None)
    monkeypatch.setattr(app_spacy, "background_process_every_24h", lambda *a, **k: None)
    monkeypatch.setattr(app_tiny, "background_rss_process_loop", lambda *a, **k: None)
    monkeypatch.setattr(app_llm, "background_cve_and_finetune_loop", lambda *a, **k: None)

    # Patch network scan helpers on both controller and service modules to deterministic stubs
    def fake_scan_ports(host, ports=None, timeout=0.5):
        return [{"port": 22, "state": "open"}]

    def fake_run_nmap_scan(host, ports=None, timeout=120):
        raise FileNotFoundError("nmap not installed")

    monkeypatch.setattr(network_analysis_controller, "scan_ports", fake_scan_ports)
    monkeypatch.setattr(network_analysis_controller, "run_nmap_scan", fake_run_nmap_scan)
    monkeypatch.setattr(app_net, "scan_ports", fake_scan_ports)
    monkeypatch.setattr(app_net, "run_nmap_scan", fake_run_nmap_scan)

    # Patch service_scan_range to async stub on both import paths
    async def fake_service_scan_range(**kwargs):
        return {"hosts": ["127.0.0.1"], "count": 1}

    monkeypatch.setattr(network_analysis_controller, "service_scan_range", fake_service_scan_range)
    monkeypatch.setattr(app_net, "service_scan_range", fake_service_scan_range)

    # Patch LLM query to controlled response on both import paths
    monkeypatch.setattr(llm_controller, "query_llm", lambda prompt: f"ECHO: {prompt}")
    monkeypatch.setattr(app_llm, "query_llm", lambda prompt: f"ECHO: {prompt}")

    yield


def test_status_includes_known_workers():
    with TestClient(main.app) as client:
        r = client.get("/status")
        assert r.status_code == 200
        data = r.json()
        assert "workers" in data
        # known worker keys come from default_settings; ensure some expected keys
        for key in ("google_alerts", "spacy_nlp", "llm_updater"):
            assert key in data["workers"]


def test_network_common_ports_list():
    with TestClient(main.app) as client:
        r = client.get("/network/ports")
        assert r.status_code == 200
        j = r.json()
        assert "common_ports" in j
        assert isinstance(j["common_ports"], list)


def test_scan_host_fallback_to_tcp_scan():
    with TestClient(main.app) as client:
        payload = {"host": "127.0.0.1", "use_nmap": True}
        r = client.post("/network/scan", json=payload)
        assert r.status_code == 200
        j = r.json()
        assert j["host"] == "127.0.0.1"
        assert isinstance(j.get("results"), list)
        assert j["results"][0]["port"] == 22


def test_scan_range_delegates_to_service():
    with TestClient(main.app) as client:
        payload = {"cidr": "127.0.0.1/32"}
        r = client.post("/network/scan_range", json=payload)
        assert r.status_code == 200
        j = r.json()
        assert j.get("hosts") == ["127.0.0.1"]


def test_workers_enable_and_disable(monkeypatch):
    # Ensure worker background targets are patched (autouse fixture handles it)
    with TestClient(main.app) as client:
        # enable scraping_feeds
        r = client.post("/workers/scraping_feeds", json={"enabled": True})
        assert r.status_code == 200
        assert "enabled" in r.json().get("message", "") or "started" in r.json().get("message", "") or "enabled" in r.json().get("message", "")

        # status should reflect enabled worker
        r2 = client.get("/workers")
        assert r2.status_code == 200
        body = r2.json()
        assert body["status"].get("scraping_feeds") is True

        # now disable it
        r3 = client.post("/workers/scraping_feeds", json={"enabled": False})
        assert r3.status_code == 200
        r4 = client.get("/workers")
        assert r4.status_code == 200
        assert r4.json()["status"].get("scraping_feeds") is False


def test_llm_query_returns_echo():
    with TestClient(main.app) as client:
        r = client.post("/llm/query", json={"prompt": "hello"})
        assert r.status_code == 200
        assert r.json().get("response") == "ECHO: hello"


def test_postgres_feeds_endpoint_with_fake_pool(monkeypatch):
    # Provide a fake pool with an async context manager
    class FakeConn:
        async def fetch(self, *_a, **_k):
            return []

    class FakeAcquire:
        def __init__(self, conn):
            self.conn = conn

        async def __aenter__(self):
            return self.conn

        async def __aexit__(self, exc_type, exc, tb):
            return False

    class FakePool:
        def __init__(self, conn):
            self.conn = conn

        def acquire(self):
            return FakeAcquire(self.conn)

    # attach fake pool to app state
    main.app.state.pool = FakePool(FakeConn())
    with TestClient(main.app) as client:
        r = client.get("/postgre-ttrss/feeds?limit=5")
        # Accept 200 (feeds found) or 404 (no feeds found), matching controller logic
        assert r.status_code in (200, 404)
        if r.status_code == 200:
            assert isinstance(r.json(), list)
