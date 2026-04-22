"""
@file test_chroma_query_missing_meta.py
@brief Query retriever handles missing metadata entries and distances.
"""
from app.services.vectorstore import chroma_client as cc


class QCol:
    def query(self, **kwargs):
        # return documents with empty metadata and missing distances
        return {"documents": [["doc1", "doc2"]], "metadatas": [[{}, {}]]}


class FakeEmbed:
    def embed_texts(self, texts):
        return [[0.1] for _ in texts]


def make_client():
    obj = object.__new__(cc.ChromaClient)
    obj.collection = QCol()
    obj.embedder = FakeEmbed()
    return obj


def test_query_missing_meta():
    ch = make_client()
    res = ch.query_retriever('foo', k=2)
    assert isinstance(res, list)
    assert res[0]['id'] in ('0', '1')
