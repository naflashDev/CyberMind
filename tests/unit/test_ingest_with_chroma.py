"""
@file test_ingest_with_chroma.py
@brief Test ingest_document path when chroma is available and upsert succeeds
"""
from pathlib import Path
from datetime import datetime, timezone

from app.services.documents import ingest as ingest_mod


class DummyChromaClient:
    def __init__(self, embed_model=None):
        self.embedder = True
        self.collection = True
    def upsert_document(self, doc_id, text, metadata=None):
        # emulate success
        return True


def test_ingest_with_chroma_upsert(monkeypatch, tmp_path):
    # point DEFAULT_BASE to tmp
    monkeypatch.setattr(ingest_mod, 'DEFAULT_BASE', tmp_path)
    # enable CHROMA
    monkeypatch.setattr(ingest_mod, '_CHROMA_AVAILABLE', True)
    # ensure no ollama usage
    monkeypatch.setattr('shutil.which', lambda x: False)

    # patch chroma client used inside function
    import app.services.vectorstore.chroma_client as chroma_mod
    monkeypatch.setattr(chroma_mod, 'ChromaClient', DummyChromaClient)

    data = b'hello chroma'
    out = ingest_mod.ingest_document(data, filename='c.txt', folder=None)
    # Should have attempted upsert and recorded
    assert 'upserted' in out
