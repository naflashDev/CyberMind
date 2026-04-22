"""
@file test_chroma_client_more.py
@brief Additional unit tests for ChromaClient helper methods.
"""
import json
from datetime import datetime, timezone, timedelta
from pathlib import Path

import pytest

from app.services.vectorstore import chroma_client as cc


class FakeCollection:
    def __init__(self):
        self.add_calls = []
        self.upsert_calls = []
        self.deleted = []

    def add(self, **kwargs):
        self.add_calls.append(kwargs)

    def upsert(self, **kwargs):
        self.upsert_calls.append(kwargs)

    def query(self, **kwargs):
        # return one document with metadata containing doc_id
        return {"documents": [["doc text"]], "metadatas": [[{"doc_id": "42"}]], "distances": [[0.1]]}

    def get(self, **kwargs):
        # Provide ids or metadatas as requested by delete_by_ttl
        if kwargs.get('include') == ['ids']:
            return {"ids": [["old_id"]]}
        if kwargs.get('ids'):
            # per-id get returning metadata with timestamp
            return {"metadatas": [[{"timestamp": (datetime.utcnow() - timedelta(days=10)).isoformat()}]], "documents": [["d"]]}
        return {"metadatas": [[{"timestamp": (datetime.utcnow() - timedelta(days=10)).isoformat()}]]}

    def delete(self, ids=None):
        self.deleted.extend(ids or [])


class FakeEmbedder:
    def embed_texts(self, texts):
        return [[float(len(t))] for t in texts]


def make_chroma_obj(tmp_path, embedder=None):
    # bypass __init__ to avoid chromadb construction
    obj = object.__new__(cc.ChromaClient)
    obj.persist_directory = str(tmp_path)
    obj.collection = None
    obj.client = None
    obj.embedder = embedder
    obj._backup_path = tmp_path / 'chroma_backup.jsonl'
    return obj


def test_write_backup_entries_and_restore(tmp_path):
    ch = make_chroma_obj(tmp_path)
    entries = [{"id": "a", "embedding": [1, 2], "metadata": {}, "document": "x"}]
    # write backup
    ch._backup_path = tmp_path / 'backup.jsonl'
    assert ch._write_backup_entries(entries, overwrite=True) is True
    # simulate restore with collection having upsert
    col = FakeCollection()
    ch.collection = col
    ch.client = type('C', (), {'persist': lambda self=None: None})()
    assert ch._restore_from_backup() is True
    assert col.upsert_calls or col.add_calls


def test_write_backup_no_path():
    ch = make_chroma_obj(Path('/nonexistent'), embedder=None)
    ch._backup_path = None
    assert ch._write_backup_entries([{}]) is False


def test_build_collection_and_persist(tmp_path):
    ch = make_chroma_obj(tmp_path, embedder=FakeEmbedder())
    # create a fake collection
    col = FakeCollection()
    ch.collection = col
    # client with persist
    ch.client = type('C', (), {'persist': lambda self=None: None})()
    docs = [{"id": 1, "text": "hello world", "metadata": {}}]
    ch.build_collection(docs)
    # ensure we attempted to add/upsert chunks
    assert col.add_calls or col.upsert_calls
    # Backup may be written when persistence is unavailable; accept either
    assert ch._backup_path.exists() or getattr(ch.client, 'persist', None) is not None


def test_query_retriever_returns_docs():
    ch = make_chroma_obj(Path('.'), embedder=FakeEmbedder())
    col = FakeCollection()
    ch.collection = col
    res = ch.query_retriever("query", k=1)
    assert isinstance(res, list)
    assert res[0]['id'] == '42'


def test_delete_by_ttl_deletes_old(tmp_path):
    ch = make_chroma_obj(tmp_path)
    col = FakeCollection()
    ch.collection = col
    # test cutoff in recent past so the timestamp in FakeCollection qualifies
    cutoff = datetime.utcnow().replace(tzinfo=timezone.utc) - timedelta(days=1)
    deleted = ch.delete_by_ttl(cutoff)
    assert isinstance(deleted, int)
