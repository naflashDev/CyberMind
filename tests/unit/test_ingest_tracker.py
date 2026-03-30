"""
@file test_ingest_tracker.py
@author naflashDev
@brief Unit tests for ingest_tracker module
@details Tests ensure sqlite fallback DB operations (record, exists, get, mark_upserted) behave correctly.
"""
import tempfile
from pathlib import Path

from app.services.documents import ingest_tracker


def test_record_and_get_entry(tmp_path):
    '''
    @brief Test record_ingest, exists_by_hash, get_entry and mark_upserted using a temporary DB path.
    '''
    # Point module DB_PATH to a temp file
    db_file = tmp_path / "ingest_index.db"
    ingest_tracker.DB_PATH = db_file
    # Force sqlite fallback during tests to avoid heavy SQLAlchemy usage
    ingest_tracker._USE_SQLA = False

    h = "deadbeef"
    assert not ingest_tracker.exists_by_hash(h)

    ingest_tracker.record_ingest(h, "doc1", "/tmp/doc1.txt", "doc1.txt", "folder", upserted=False)
    assert ingest_tracker.exists_by_hash(h)
    entry = ingest_tracker.get_entry(h)
    assert entry is not None
    assert entry['content_hash'] == h
    assert entry['doc_id'] == 'doc1'

    # mark upserted and verify
    ingest_tracker.mark_upserted(h)
    entry2 = ingest_tracker.get_entry(h)
    assert entry2['upserted'] is True
