"""
@file test_chroma_delete_no_ids.py
@brief Test delete_by_ttl when no ids can be derived (should return 0).
"""
from datetime import datetime, timezone, timedelta
from pathlib import Path
from app.services.vectorstore import chroma_client as cc


class StrangeCollection:
    def get(self, **kwargs):
        # Simulate raising when asking for ids
        if kwargs.get('include') == ['ids']:
            raise Exception('get ids not supported')
        return {'metadatas': [[]]}


def make_client(tmp_path):
    obj = object.__new__(cc.ChromaClient)
    obj.persist_directory = str(tmp_path)
    obj.collection = StrangeCollection()
    obj.client = None
    obj._backup_path = tmp_path / 'backup.jsonl'
    return obj


def test_delete_by_ttl_no_ids(tmp_path):
    ch = make_client(tmp_path)
    cutoff = datetime.utcnow().replace(tzinfo=timezone.utc)
    res = ch.delete_by_ttl(cutoff)
    assert res == 0
