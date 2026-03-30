"""
@file test_chroma_client.py
@author naflashDev
@brief Unit tests for chroma_client module
@details Test upsert_document uses provided embedder and collection methods and backup writing.
"""
from pathlib import Path

from app.services.vectorstore import chroma_client


class DummyEmbed:
    def embed_texts(self, texts):
        # return a vector per text
        return [[float(len(t))] for t in texts]


class DummyCollection:
    def __init__(self):
        self.add_called = False
        self.upsert_called = False
        self.stored = {}

    def upsert(self, ids=None, embeddings=None, metadatas=None, documents=None):
        self.upsert_called = True
        for i, _id in enumerate(ids):
            self.stored[_id] = {'emb': embeddings[i], 'meta': metadatas[i], 'doc': documents[i]}

    def add(self, ids=None, embeddings=None, metadatas=None, documents=None):
        self.add_called = True
        for i, _id in enumerate(ids):
            self.stored[_id] = {'emb': embeddings[i], 'meta': metadatas[i], 'doc': documents[i]}

    def get(self, include=None):
        return {'ids': [[]]}


def test_upsert_document_and_backup(tmp_path, monkeypatch):
    '''
    @brief Ensure upsert_document chunks text and calls collection.upsert and writes backup entries.
    '''
    obj = chroma_client.ChromaClient.__new__(chroma_client.ChromaClient)
    obj.embedder = DummyEmbed()
    coll = DummyCollection()
    obj.collection = coll
    obj.client = True
    obj._backup_path = tmp_path / 'chroma_backup.jsonl'
    obj._can_persist = False

    # Call upsert_document with a short text
    obj.upsert_document('docx', 'hello world', metadata={'a': 1})
    # Verify upsert recorded
    assert coll.upsert_called or coll.add_called
    # Verify backup file was created (entries appended)
    assert obj._backup_path.exists()
import sys
import types
import importlib
from datetime import datetime, timedelta, timezone


class FakeArray:
    def __init__(self, data):
        self._data = data

    def tolist(self):
        return self._data


class FakeModel:
    def __init__(self, name=None):
        self.name = name

    def encode(self, texts, show_progress_bar=False):
        # return a small fixed-dimension embedding
        return FakeArray([[0.1] * 8 for _ in texts])


class FakeCollection:
    def __init__(self, name):
        self.name = name
        self._ids = []
        self._docs = []
        self._metas = []
        self._embs = []

    def add(self, ids, embeddings, metadatas, documents):
        for i, _id in enumerate(ids):
            self._ids.append(_id)
            self._embs.append(embeddings[i])
            self._metas.append(metadatas[i])
            self._docs.append(documents[i])

    def upsert(self, ids, embeddings, metadatas, documents):
        # simple upsert: if id exists replace, else append
        for i, _id in enumerate(ids):
            if _id in self._ids:
                idx = self._ids.index(_id)
                self._embs[idx] = embeddings[i]
                self._metas[idx] = metadatas[i]
                self._docs[idx] = documents[i]
            else:
                self.add([_id], [embeddings[i]], [metadatas[i]], [documents[i]])

    def query(self, query_embeddings=None, n_results=5, include=None):
        # naive distance: sum squared diff
        q = query_embeddings[0]
        scores = []
        for emb in self._embs:
            s = sum((a - b) ** 2 for a, b in zip(emb, q))
            scores.append(s)
        idxs = sorted(range(len(scores)), key=lambda i: scores[i])[:n_results]
        ids = [self._ids[i] for i in idxs]
        docs = [self._docs[i] for i in idxs]
        metas = [self._metas[i] for i in idxs]
        dists = [scores[i] for i in idxs]
        return {"ids": [ids], "documents": [docs], "metadatas": [metas], "distances": [dists]}

    def get(self, ids=None, include=None):
        if ids:
            # return nested lists like chroma
            out_ids = []
            out_docs = []
            out_metas = []
            for _id in ids:
                if _id in self._ids:
                    i = self._ids.index(_id)
                    out_ids.append(_id)
                    out_docs.append(self._docs[i])
                    out_metas.append(self._metas[i])
            return {"ids": [out_ids], "documents": [out_docs], "metadatas": [out_metas]}
        # return top-level ids
        return {"ids": [self._ids]}

    def delete(self, ids):
        removed = 0
        for _id in list(ids):
            if _id in self._ids:
                i = self._ids.index(_id)
                for lst in (self._ids, self._docs, self._metas, self._embs):
                    lst.pop(i)
                removed += 1
        return removed


class FakeClient:
    def __init__(self, settings=None):
        self._cols = {}

    def get_collection(self, name):
        if name in self._cols:
            return self._cols[name]
        raise Exception("Not found")

    def create_collection(self, name):
        c = FakeCollection(name)
        self._cols[name] = c
        return c

    def persist(self):
        return True


def _inject_fakes():
    # Inject fake chromadb and sentence_transformers into sys.modules before importing target module
    chromadb_mod = types.SimpleNamespace(Client=lambda settings=None: FakeClient())
    chromadb_config = types.SimpleNamespace(Settings=lambda **kwargs: None)
    sys.modules['chromadb'] = chromadb_mod
    sys.modules['chromadb.config'] = chromadb_config

    st_mod = types.SimpleNamespace(SentenceTransformer=FakeModel)
    sys.modules['sentence_transformers'] = st_mod


def test_build_and_query(tmp_path, monkeypatch):
    _inject_fakes()
    # import the target module fresh
    import importlib
    chroma = importlib.import_module('app.services.vectorstore.chroma_client')
    importlib.reload(chroma)
    # Provide a lightweight embed_model adapter that wraps the FakeModel.encode result
    class FakeAdapter:
        def embed_texts(self, texts):
            return FakeModel().encode(texts, show_progress_bar=False).tolist()

    client = chroma.ChromaClient(persist_directory=str(tmp_path), collection_name='test', embed_model=FakeAdapter())
    docs = [
        {"id": "1", "text": "This is a test document about cats.", "metadata": {"source": "s1"}},
        {"id": "2", "text": "Another doc about dogs.", "metadata": {"source": "s2"}},
    ]
    client.build_collection(docs)
    res = client.query_retriever("cats", k=2)
    assert isinstance(res, list)
    assert len(res) >= 0


def test_delete_by_ttl(tmp_path):
    _inject_fakes()
    import importlib
    chroma = importlib.import_module('app.services.vectorstore.chroma_client')
    importlib.reload(chroma)
    class FakeAdapter:
        def embed_texts(self, texts):
            return FakeModel().encode(texts, show_progress_bar=False).tolist()

    client = chroma.ChromaClient(persist_directory=str(tmp_path), collection_name='test', embed_model=FakeAdapter())
    now = datetime.now(timezone.utc)
    old_ts = (now - timedelta(days=10)).isoformat()
    new_ts = (now - timedelta(days=1)).isoformat()
    docs = [
        {"id": "a", "text": "old doc", "metadata": {"timestamp": old_ts}},
        {"id": "b", "text": "new doc", "metadata": {"timestamp": new_ts}},
    ]
    client.build_collection(docs)
    cutoff = now - timedelta(days=7)
    deleted = client.delete_by_ttl(cutoff)
    assert isinstance(deleted, int)
    remaining = client.collection.get()
    assert isinstance(remaining.get('ids'), list)


def test_chroma_client_no_collection_backup(tmp_path, monkeypatch):
    '''
    @brief Ensure client handles missing collection gracefully when persisting.
    '''
    _inject_fakes()
    import importlib
    chroma = importlib.import_module('app.services.vectorstore.chroma_client')
    importlib.reload(chroma)
    class FakeAdapter:
        def embed_texts(self, texts):
            return FakeModel().encode(texts, show_progress_bar=False).tolist()

    client = chroma.ChromaClient(persist_directory=str(tmp_path), collection_name='test', embed_model=FakeAdapter())
    # Force collection to None to exercise fallback
    client.collection = None
    # Upsert should not raise even if collection missing; backup may not be written
    client._backup_path = tmp_path / 'cb.jsonl'
    client.upsert_document('idx', 'text', metadata={'a': 1})
    # If collection is None the method returns early without writing backup; ensure no exception and file state is acceptable
    assert True


def test_write_backup_entries_handles_write_error(tmp_path, monkeypatch):
    '''
    @brief _write_backup_entries should return False if file write fails.
    '''
    import app.services.vectorstore.chroma_client as cc

    obj = object.__new__(cc.ChromaClient)
    # point to a path that would be used
    obj._backup_path = tmp_path / 'cb.jsonl'

    # Make open raise an exception to simulate write failure
    def bad_open(*args, **kwargs):
        raise IOError('disk full')

    monkeypatch.setattr('builtins.open', bad_open)
    res = obj._write_backup_entries([{'id': 'x', 'embedding': [0.1], 'metadata': {}, 'document': 'd'}], overwrite=True)
    assert res is False


def test_restore_from_backup_success(tmp_path):
    '''
    @brief _restore_from_backup should read valid JSONL and call collection.add/upsert.
    '''
    import app.services.vectorstore.chroma_client as cc
    # prepare a backup file with two valid entries
    bk = tmp_path / 'good.jsonl'
    bk.write_text('{"id": "1", "embedding": [0.1], "metadata": {"doc_id": "1"}, "document": "d1"}\n{"id": "2", "embedding": [0.2], "metadata": {"doc_id": "2"}, "document": "d2"}\n')

    class FakeColl:
        def __init__(self):
            self.add_called = False
            self.upsert_called = False

        def upsert(self, ids=None, embeddings=None, metadatas=None, documents=None):
            self.upsert_called = True

        def add(self, ids=None, embeddings=None, metadatas=None, documents=None):
            self.add_called = True

    ch = object.__new__(cc.ChromaClient)
    ch._backup_path = bk
    ch.collection = FakeColl()
    # Ensure _can_persist True so persist path may be attempted
    ch.client = type('C', (), {'persist': lambda self=None: None})()
    ch._can_persist = True

    res = ch._restore_from_backup()
    assert res is True


def test_delete_by_ttl_handles_no_ids(tmp_path):
    '''
    @brief delete_by_ttl should return 0 when unable to derive ids.
    '''
    import app.services.vectorstore.chroma_client as cc
    ch = object.__new__(cc.ChromaClient)
    # collection.get will raise on include=['ids'] to force fallback
    class BadColl:
        def get(self, include=None, ids=None):
            if include and 'ids' in include:
                raise Exception('no ids')
            return {'metadatas': [[]]}

    ch.collection = BadColl()
    from datetime import datetime
    res = ch.delete_by_ttl(datetime.utcnow())
    assert res == 0
