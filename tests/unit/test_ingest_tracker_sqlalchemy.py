"""
@file test_ingest_tracker_sqlalchemy.py
@brief Tests ingest_tracker SQLAlchemy path by mocking SessionLocal and model
"""
from datetime import datetime, timezone
import pytest

from app.services.documents import ingest_tracker


class FakeObj:
    def __init__(self, content_hash, doc_id=None, stored_path=None, filename=None, folder=None, upserted=False):
        self.content_hash = content_hash
        self.doc_id = doc_id
        self.stored_path = stored_path
        self.filename = filename
        self.folder = folder
        self.upserted = bool(upserted)
        self.timestamp = datetime.now(timezone.utc)


class FakeSession:
    def __init__(self):
        self.storage = {}

    def get(self, model, key):
        return self.storage.get(key)

    def add(self, obj):
        self.storage[obj.content_hash] = obj

    def commit(self):
        pass

    def close(self):
        pass


def test_sqlalchemy_record_and_get(monkeypatch):
    # If the module was not imported with SQLAlchemy support, skip this test.
    if not getattr(ingest_tracker, '_USE_SQLA', False):
        pytest.skip('ingest_tracker not configured to use SQLAlchemy in this environment')

    ingest_tracker._USE_SQLA = True

    # Fake model and SessionLocal
    FakeModelClass = FakeObj

    sess = FakeSession()

    def fake_SessionLocal():
        return sess

    monkeypatch.setattr(ingest_tracker, 'SessionLocal', fake_SessionLocal)
    # IngestedDocument may not exist in module when SQLA not imported; allow setting it
    monkeypatch.setattr(ingest_tracker, 'IngestedDocument', FakeModelClass, raising=False)

    # Call record_ingest which should use sqlalchemy path
    ingest_tracker.record_ingest('h1', 'docx', '/p', 'f.txt', 'fld', upserted=True)
    assert ingest_tracker.exists_by_hash('h1')
    entry = ingest_tracker.get_entry('h1')
    assert entry['doc_id'] == 'docx'

    ingest_tracker.mark_upserted('h1')
    entry2 = ingest_tracker.get_entry('h1')
    assert entry2['upserted'] is True
