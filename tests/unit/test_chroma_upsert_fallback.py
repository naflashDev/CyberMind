"""
@file test_chroma_upsert_fallback.py
@brief Test ChromaClient upsert fallback to add when upsert raises.
"""
from pathlib import Path
from app.services.vectorstore import chroma_client as cc


class BadCollection:
    def __init__(self):
        self.add_called = False

    def upsert(self, **kwargs):
        raise Exception('upsert not supported')

    def add(self, **kwargs):
        self.add_called = True


class FakeEmbedder:
    def embed_texts(self, texts):
        return [[1.0] for _ in texts]


def make_client(tmp_path):
    obj = object.__new__(cc.ChromaClient)
    obj.persist_directory = str(tmp_path)
    obj.collection = BadCollection()
    obj.client = None
    obj.embedder = FakeEmbedder()
    obj._backup_path = tmp_path / 'backup.jsonl'
    return obj


def test_upsert_fallback_to_add(tmp_path):
    ch = make_client(tmp_path)
    ch.upsert_document('doc1', 'some text', metadata={'a': 1})
    assert ch.collection.add_called is True
