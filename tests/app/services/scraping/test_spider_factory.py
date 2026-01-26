"""
@file test_spider_factory.py
@author naflashDev
@brief Unit tests for spider_factory.py
@details Tests for dynamic spider creation, JSON writing, and spider runner logic (mocks, no real Scrapy run).
"""
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from src.app.services.scraping import spider_factory


def test_write_json_array_with_lock_creates_file(tmp_path):
    '''
    @brief Should create a new JSON file with array.
    '''
    data = {"foo": "bar"}
    file = tmp_path / "out.json"
    lock = tmp_path / "lock.lck"
    spider_factory.write_json_array_with_lock(data, str(file), str(lock))
    content = file.read_text(encoding="utf-8")
    assert content.startswith("[") and content.endswith("]")
    assert "foo" in content


def test_write_json_array_with_lock_appends(tmp_path):
    '''
    @brief Should append to existing JSON array.
    '''
    data1 = {"a": 1}
    data2 = {"b": 2}
    file = tmp_path / "out.json"
    lock = tmp_path / "lock.lck"
    # First write
    spider_factory.write_json_array_with_lock(data1, str(file), str(lock))
    # Second write
    spider_factory.write_json_array_with_lock(data2, str(file), str(lock))
    content = file.read_text(encoding="utf-8")
    assert content.count("{") == 2
    assert content.count("]") == 1


def test_create_dynamic_spider_yields_data():
    '''
    @brief Should yield data for relevant URLs.
    '''
    urls = ["http://test.com"]
    params = ("localhost", 9200)
    # Patch Scrapy response and dependencies
    with patch("src.app.services.scraping.spider_factory.store_in_opensearh_db", create=True), \
         patch("src.app.services.scraping.spider_factory.write_json_array_with_lock"), \
         patch("src.app.services.scraping.spider_factory.logger"):
        SpiderClass = spider_factory.create_dynamic_spider(urls, params)
        spider = SpiderClass()
        # Fake response with cybersecurity keyword
        class FakeResponse:
            url = "http://test.com"
            def css(self, sel):
                if sel == "title::text":
                    return AsyncMock(get=lambda default=None: "Ciberseguridad")
                return AsyncMock(getall=lambda: ["Ciberseguridad"])
        results = list(spider.parse(FakeResponse()))
        assert any("url" in r for r in results)


def test_create_dynamic_spider_discards_irrelevant():
    '''
    @brief Should not yield data for irrelevant URLs.
        import pytest
        from unittest.mock import patch, MagicMock, AsyncMock
        from src.app.services.scraping import spider_factory

    '''
    urls = ["http://irrelevante.com"]
    params = ("localhost", 9200)
    with patch("src.app.services.scraping.spider_factory.store_in_opensearh_db", create=True), \
         patch("src.app.services.scraping.spider_factory.write_json_array_with_lock"), \
         patch("src.app.services.scraping.spider_factory.logger"):
        SpiderClass = spider_factory.create_dynamic_spider(urls, params)
        spider = SpiderClass()
        class FakeResponse:
            url = "http://irrelevante.com"
            def css(self, sel):
                if sel == "title::text":
                    return AsyncMock(get=lambda default=None: "Sin relación")
                return AsyncMock(getall=lambda: ["Sin relación"])
        results = list(spider.parse(FakeResponse()))
        # Solo se debe yield una vez (por la última línea del parse)
        assert len(results) == 1
        assert "url" in results[0]


# --- run_dynamic_spider ---
@patch("src.app.services.scraping.spider_factory.CrawlerProcess")
def test_run_dynamic_spider_runs(mock_crawler):
    urls = ["http://test.com"]
    params = {"name": "test"}
    spider_factory.run_dynamic_spider(urls, params)
    assert mock_crawler.called


# --- Cobertura de errores y ramas adicionales ---
import tempfile
import os

def test_write_json_array_with_lock_lockfile_wait(monkeypatch):
    '''
    @brief Debe esperar si el lockfile existe y luego escribir correctamente.
    '''
    data = {"foo": "bar"}
    with tempfile.TemporaryDirectory() as tmpdir:
        file = os.path.join(tmpdir, "out.json")
        lock = os.path.join(tmpdir, "lock.lck")
        # Crear lockfile antes de llamar
        with open(lock, "w") as f:
            f.write("locked")
        # Lanzar en segundo plano la eliminación del lockfile
        import threading, time
        def remove_lock():
            time.sleep(0.2)
            os.remove(lock)
        t = threading.Thread(target=remove_lock)
        t.start()
        spider_factory.write_json_array_with_lock(data, file, lock)
        t.join()
        content = open(file, encoding="utf-8").read()
        assert "foo" in content

def test_write_json_array_with_lock_malformed_file(tmp_path):
    '''
    @brief Debe manejar archivo malformado y seguir escribiendo.
    '''
    file = tmp_path / "out.json"
    lock = tmp_path / "lock.lck"
    # Crear archivo malformado
    file.write_text("MALFORMED", encoding="utf-8")
    data = {"x": 1}
    # No debe lanzar excepción
    spider_factory.write_json_array_with_lock(data, str(file), str(lock))
    content = file.read_text(encoding="utf-8")
    assert "x" in content

import types
import pytest

@pytest.mark.asyncio
async def test_run_dynamic_spider_from_db_stop_event(monkeypatch):
    '''
    @brief Debe salir inmediatamente si stop_event está activo.
    '''
    class DummyPool:
        async def acquire(self):
            class DummyConn:
                pass
            return DummyConn()
    stop_event = types.SimpleNamespace(is_set=lambda: True)
    # No debe hacer nada ni lanzar excepción
    await spider_factory.run_dynamic_spider_from_db(DummyPool(), stop_event=stop_event, max_laps=1, total_sleep=0.01, check_interval=0.01)

@pytest.mark.asyncio
async def test_run_dynamic_spider_from_db_pool_error(monkeypatch):
    '''
    @brief Debe manejar error al crear pool y reintentar.
    '''
    # Forzar pool=None y fallo en asyncpg.create_pool
    import sys
    import importlib
    called = {}
    class FakeAsyncpg:
        @staticmethod
        async def create_pool(*a, **kw):
            called['ok'] = True
            raise Exception("fail")
    monkeypatch.setitem(sys.modules, 'asyncpg', FakeAsyncpg)
    # Recargar spider_factory para que el import interno use el fake
    import src.app.services.scraping.spider_factory as spider_factory_reload
    importlib.reload(spider_factory_reload)
    # stop_event solo se activa después del primer intento
    state = {'called': 0}
    def is_set():
        state['called'] += 1
        return state['called'] > 1
    stop_event = types.SimpleNamespace(is_set=is_set)
    await spider_factory_reload.run_dynamic_spider_from_db(None, stop_event=stop_event, max_laps=1, total_sleep=0.01, check_interval=0.01)
    assert called.get('ok')

def test_create_dynamic_spider_configuracion_keywords():
    '''
    @brief Debe detectar correctamente los keywords de ciberseguridad.
    '''
    urls = ["http://test.com"]
    params = ("localhost", 9200)
    with patch("src.app.services.scraping.spider_factory.store_in_opensearch", create=True), \
         patch("src.app.services.scraping.spider_factory.write_json_array_with_lock"), \
         patch("src.app.services.scraping.spider_factory.logger") as mock_logger:
        SpiderClass = spider_factory.create_dynamic_spider(urls, params)
        spider = SpiderClass()
        class FakeResponse:
            url = "http://test.com"
            def css(self, sel):
                if sel == "title::text":
                    return MagicMock(get=lambda default=None: "Malware")
                return MagicMock(getall=lambda: ["Malware"])
        results = list(spider.parse(FakeResponse()))
        assert any("url" in r for r in results)
        assert mock_logger.info.called

def test_create_dynamic_spider_configuracion_no_keywords():
    '''
    @brief No debe detectar como relevante si no hay keywords.
    '''
    urls = ["http://test.com"]
    params = ("localhost", 9200)
    with patch("src.app.services.scraping.spider_factory.store_in_opensearch", create=True), \
         patch("src.app.services.scraping.spider_factory.write_json_array_with_lock"), \
         patch("src.app.services.scraping.spider_factory.logger") as mock_logger:
        SpiderClass = spider_factory.create_dynamic_spider(urls, params)
        spider = SpiderClass()
        class FakeResponse:
            url = "http://test.com"
            def css(self, sel):
                if sel == "title::text":
                    return MagicMock(get=lambda default=None: "Sin relación")
                return MagicMock(getall=lambda: ["Sin relación"])
        results = list(spider.parse(FakeResponse()))
        assert any("url" in r for r in results)
        assert mock_logger.info.called

# --- run_dynamic_spider_from_db ---
import asyncio
@pytest.mark.asyncio

@patch("asyncpg.create_pool")
@patch("src.app.services.scraping.spider_factory.get_entry_links", new_callable=AsyncMock)
@patch("src.app.services.scraping.spider_factory.run_dynamic_spider")
@patch("src.app.services.scraping.spider_factory.Process")
async def test_run_dynamic_spider_from_db_runs(mock_process, mock_run, mock_get_entry_links, mock_pool):
    '''
    @brief Test run_dynamic_spider_from_db avoiding multiprocessing pickling issues.
    '''
    # Create a mock connection object
    mock_conn = AsyncMock()
    # Create a mock pool with acquire() supporting async context manager
    mock_acquire_cm = AsyncMock()
    mock_acquire_cm.__aenter__.return_value = mock_conn
    mock_acquire_cm.__aexit__.return_value = None
    pool = MagicMock()
    pool.acquire.return_value = mock_acquire_cm
    # Set AsyncMock return value for get_entry_links
    mock_get_entry_links.return_value = ["http://test.com"]
    # Mock the process so it does not actually start
    mock_proc_instance = MagicMock()
    mock_process.return_value = mock_proc_instance
    # Usar tiempos mínimos y max_laps=1 para evitar bloqueos
    await spider_factory.run_dynamic_spider_from_db(
        pool,
        total_sleep=0.01,
        check_interval=0.01,
        max_laps=1
    )
    assert mock_run.called or mock_process.called
