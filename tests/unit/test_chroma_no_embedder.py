"""
@file test_chroma_no_embedder.py
@brief Tests ChromaClient behavior when embedder or collection is missing
"""
from app.services.vectorstore.chroma_client import ChromaClient


def test_upsert_and_query_when_disabled():
    # Create instance without calling __init__ to avoid heavy init
    obj = ChromaClient.__new__(ChromaClient)
    # No embedder and no collection
    obj.embedder = None
    obj.collection = None
    obj.client = None

    # build_collection should early return and not raise
    obj.build_collection([])

    # upsert_document should early return as well
    obj.upsert_document('id', 'text')

    # query_retriever should return empty list when no embedder/collection
    res = obj.query_retriever('q')
    assert res == []
