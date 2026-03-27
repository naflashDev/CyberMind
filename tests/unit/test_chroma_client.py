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

    client = chroma.ChromaClient(persist_directory=str(tmp_path), collection_name='test')
    docs = [
        {"id": "1", "text": "This is a test document about cats.", "metadata": {"source": "s1"}},
        {"id": "2", "text": "Another doc about dogs.", "metadata": {"source": "s2"}},
    ]
    client.build_collection(docs)
    res = client.query_retriever("cats", k=2)
    assert isinstance(res, list)
    assert any(d['id'] == '1' for d in res)


def test_delete_by_ttl(tmp_path):
    _inject_fakes()
    import importlib
    chroma = importlib.import_module('app.services.vectorstore.chroma_client')
    importlib.reload(chroma)

    client = chroma.ChromaClient(persist_directory=str(tmp_path), collection_name='test')
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
    assert deleted == 1
    remaining = client.collection.get()
    assert 'a' not in (remaining.get('ids') or [])[0]
