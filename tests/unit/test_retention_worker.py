"""
@file test_retention_worker.py
@author naflashDev
@brief Unit tests for retention_worker loop
@details Uses a fake stop_event and stubbed SessionLocal to run one iteration.
"""
from datetime import datetime, timezone, timedelta

from app.controllers.routes import retention_worker


class FakeDB:
    def __init__(self):
        self.closed = False

    def query(self, model):
        class Q:
            def filter(self, *args, **kwargs):
                class Inner:
                    def delete(self, synchronize_session=False):
                        return 0
                return Inner()
        return Q()

    def commit(self):
        pass

    def close(self):
        self.closed = True


class FakeEvent:
    def __init__(self):
        self._flag = False
        self.wait_called = False

    def is_set(self):
        return self._flag

    def wait(self, interval=None):
        # On first wait, set the flag so next loop exits
        self.wait_called = True
        self._flag = True
        return True

    def set(self):
        self._flag = True


def test_vector_and_message_retention_runs_one_iteration(monkeypatch):
    '''
    @brief Run retention loop body once by providing FakeEvent and fake SessionLocal.
    '''
    # Replace SessionLocal with one that returns FakeDB
    monkeypatch.setattr(retention_worker, 'SessionLocal', lambda: FakeDB())

    evt = FakeEvent()
    # Ensure CHROMA_AVAILABLE is False to skip chroma initialization
    monkeypatch.setattr(retention_worker, 'CHROMA_AVAILABLE', False)

    # Run function; it should do one loop then exit due to FakeEvent.wait
    retention_worker.vector_and_message_retention(evt, days=0, interval_hours=0)
