import pytest
import types


class DummyApp:
    pass


class DummyRequest:
    def __init__(self):
        self.app = DummyApp()
        self.app.state = types.SimpleNamespace()


@pytest.mark.asyncio
async def test_search_and_insert_rss_file_missing(monkeypatch):
    from app.controllers.routes import tiny_postgres_controller
    req = DummyRequest()
    # ensure pool exists so function does not attempt to create asyncpg pool
    req.app.state.pool = object()

    # Force the URL file to be missing
    import os
    monkeypatch.setattr(os.path, 'exists', lambda p: False)

    with pytest.raises(Exception):
        await tiny_postgres_controller.search_and_insert_rss(req)
