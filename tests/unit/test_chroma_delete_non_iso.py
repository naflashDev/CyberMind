"""
@file test_chroma_delete_non_iso.py
@brief delete_by_ttl handles non-ISO timestamps gracefully (skips them).
"""
from datetime import datetime, timezone, timedelta
from app.services.vectorstore import chroma_client as cc


class BadMetaCol:
    def get(self, **kwargs):
        # When asked per-id, return a metadata with invalid timestamp
        if kwargs.get('ids'):
            return {"metadatas": [[{"timestamp": "not-a-timestamp"}]]}
        # when asked for metadatas list
        return {"metadatas": [[{"timestamp": "not-a-timestamp"}]]}


def make_client():
    obj = object.__new__(cc.ChromaClient)
    obj.collection = BadMetaCol()
    obj.client = None
    return obj


def test_delete_by_ttl_non_iso():
    ch = make_client()
    cutoff = datetime.utcnow().replace(tzinfo=timezone.utc) - timedelta(days=1)
    res = ch.delete_by_ttl(cutoff)
    assert res == 0
