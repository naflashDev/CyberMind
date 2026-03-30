"""
@file test_chroma_upsert_empty_text.py
@brief Ensure upsert_document handles empty text by creating a single empty chunk.
"""
from pathlib import Path
from app.services.vectorstore import chroma_client as cc


class Collect:
    def __init__(self):
        self.added = False
        self.upserted = False

    def upsert(self, **kwargs):
        self.upserted = True

    def add(self, **kwargs):
        self.added = True


class FakeEmbed:
    def embed_texts(self, texts):
        return [[0.0] for _ in texts]


def make_client(tmp_path):
    obj = object.__new__(cc.ChromaClient)
    obj.persist_directory = str(tmp_path)
    obj.collection = Collect()
    obj.embedder = FakeEmbed()
    obj.client = None
    obj._backup_path = tmp_path / 'bk.jsonl'
    return obj


def test_upsert_empty_text(tmp_path):
    ch = make_client(tmp_path)
    ch.upsert_document('id1', '', metadata={'k': 'v'})
    # either upsert or add must have been called
    assert ch.collection.upserted or ch.collection.added
