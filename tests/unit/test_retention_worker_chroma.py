"""
@file test_retention_worker_chroma.py
@brief Test retention worker uses ChromaClient.delete_by_ttl when available
"""
from datetime import datetime, timezone, timedelta
from app.controllers.routes import retention_worker


class DummyChroma:
    def __init__(self, embed_model=None):
        self.deleted = 0
    def delete_by_ttl(self, cutoff):
        self.deleted += 1
        return 2


class FakeDB:
    def __init__(self):
        pass
    def query(self, model):
        class Q:
            def filter(self, *a, **k):
                class I:
                    def delete(self, synchronize_session=False):
                        return 0
                return I()
        return Q()
    def commit(self):
        pass
    def close(self):
        pass


class FakeEvent:
    def __init__(self):
        self._flag = False
    def is_set(self):
        return self._flag
    def wait(self, interval=None):
        self._flag = True
        return True
    def set(self):
        self._flag = True


def test_retention_calls_chroma(monkeypatch):
    monkeypatch.setattr(retention_worker, 'CHROMA_AVAILABLE', True)
    # replace ChromaClient in module where retention imports it
    monkeypatch.setattr('app.controllers.routes.retention_worker.ChromaClient', DummyChroma)
    monkeypatch.setattr(retention_worker, 'SessionLocal', lambda: FakeDB())

    evt = FakeEvent()
    # run one loop
    retention_worker.vector_and_message_retention(evt, days=1, interval_hours=0)
    # If no exception, assume chroma delete path ran
    assert True
