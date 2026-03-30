"""
@file test_chroma_client_extra.py
@author naflashDev
@brief Additional unit tests for chroma_client
@details Covers delete_by_ttl and query_retriever behaviors using fake collection/embedder.
"""
from datetime import datetime, timedelta, timezone
from app.services.vectorstore import chroma_client


class FakeCollectionForDelete:
    def __init__(self, metas):
        # metas: dict mapping id -> metadata dict
        self._metas = metas
        self.deleted = []

    def get(self, ids=None, include=None):
        # two modes: include=['ids'] -> return ids list; include=['metadatas','documents'] -> return metadatas
        if include and 'ids' in include:
            return {'ids': [list(self._metas.keys())]}
        if ids is not None:
            # return metadata for the requested id
            md = self._metas.get(ids[0])
            return {'metadatas': [[md]] if md is not None else [[]], 'documents': [[self._metas.get(ids[0], {}).get('doc', '')]]}
        # fallback
        return {'metadatas': [list(self._metas.values())]}

    def delete(self, ids=None):
        for i in ids:
            self.deleted.append(i)


def test_delete_by_ttl_deletes_old_items():
    now = datetime.now(timezone.utc)
    old_ts = (now - timedelta(days=5)).isoformat()
    new_ts = (now - timedelta(days=1)).isoformat()

    metas = {
        'doc_old': {'timestamp': old_ts},
        'doc_new': {'timestamp': new_ts}
    }

    obj = chroma_client.ChromaClient.__new__(chroma_client.ChromaClient)
    obj.collection = FakeCollectionForDelete(metas)
    # call delete_by_ttl with cutoff = now - 2 days => old should be deleted
    cutoff = now - timedelta(days=2)
    deleted = obj.delete_by_ttl(cutoff)
    assert deleted == 1
    assert 'doc_old' in obj.collection.deleted


class DummyEmbed:
    def embed_texts(self, texts):
        return [[1.0, 2.0, 3.0] for _ in texts]


class FakeCollectionForQuery:
    def query(self, query_embeddings=None, n_results=5, include=None):
        return {
            'documents': [['doc text']],
            'metadatas': [[{'doc_id': 'did', 'source': 'src'}]],
            'distances': [[0.123]]
        }


def test_query_retriever_returns_structured_docs():
    obj = chroma_client.ChromaClient.__new__(chroma_client.ChromaClient)
    obj.embedder = DummyEmbed()
    obj.collection = FakeCollectionForQuery()

    res = obj.query_retriever('hello', k=1)
    assert isinstance(res, list)
    assert res[0]['id'] == 'did' or res[0]['id'] == '0'
    assert 'text' in res[0]


def test_write_backup_and_restore(tmp_path):
    # create a fake client with backup path and a fake collection to receive restored entries
    entries = [
        {'id': '1', 'embedding': [0.1], 'metadata': {'doc_id': '1'}, 'document': 'doc1'},
        {'id': '2', 'embedding': [0.2], 'metadata': {'doc_id': '2'}, 'document': 'doc2'},
    ]
    bp = tmp_path / 'chroma_backup.jsonl'
    obj = chroma_client.ChromaClient.__new__(chroma_client.ChromaClient)
    obj._backup_path = bp

    # write backup
    ok = obj._write_backup_entries(entries, overwrite=True)
    assert ok
    assert bp.exists()

    # Prepare fake collection that records add/upsert calls
    class RecvColl:
        def __init__(self):
            self.added = []
            self.upserted = []

        def upsert(self, ids=None, embeddings=None, metadatas=None, documents=None):
            self.upserted.extend(ids)

        def add(self, ids=None, embeddings=None, metadatas=None, documents=None):
            self.added.extend(ids)

    recv = RecvColl()
    obj.collection = recv
    # restore should call collection.upsert or add and return True
    res = obj._restore_from_backup()
    assert res is True
    # verify that some ids were restored
    assert recv.upserted or recv.added


def test_build_collection_uses_embedder_and_writes_backup(tmp_path):
    obj = chroma_client.ChromaClient.__new__(chroma_client.ChromaClient)
    obj.persist_directory = str(tmp_path)
    obj._backup_path = tmp_path / 'chroma_backup.jsonl'
    class Coll:
        def __init__(self):
            self.add_called = False
        def add(self, ids=None, embeddings=None, metadatas=None, documents=None):
            self.add_called = True

    obj.collection = Coll()
    class E:
        def embed_texts(self, texts):
            return [[float(len(t))] for t in texts]
    obj.embedder = E()

    docs = [{'id': 'a', 'text': 'hello', 'metadata': {'m': 1}}, {'id': 'b', 'text': 'world', 'metadata': {}}]
    obj.build_collection(docs)
    # backup file should exist
    assert obj._backup_path.exists()
