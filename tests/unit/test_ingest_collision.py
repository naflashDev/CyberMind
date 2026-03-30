"""
@file test_ingest_collision.py
@brief Test ingest handles filename collisions by adding suffix
"""
from pathlib import Path
from app.services.documents import ingest as ingest_mod


def test_filename_collision(monkeypatch, tmp_path):
    monkeypatch.setattr(ingest_mod, 'DEFAULT_BASE', tmp_path)
    monkeypatch.setattr(ingest_mod, '_CHROMA_AVAILABLE', False)

    # Avoid interacting with existing ingest tracker records
    monkeypatch.setattr(ingest_mod.ingest_tracker, 'get_entry', lambda h: None)
    monkeypatch.setattr(ingest_mod.ingest_tracker, 'record_ingest', lambda *a, **k: None)

    data = b'content'
    # Create an existing file with same name
    # Create existing file in the DEFAULT_BASE folder (tmp_path)
    (tmp_path / 'dup.txt').write_bytes(b'old')

    out1 = ingest_mod.ingest_document(data, filename='dup.txt', folder=None)
    out2 = ingest_mod.ingest_document(data, filename='dup.txt', folder=None)

    # second call should create a file with suffix
    assert out1['file'] != out2['file']
    assert out2['file'].startswith('dup')
