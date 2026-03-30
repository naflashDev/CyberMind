"""
@file test_chroma_restore_invalid_json.py
@brief _restore_from_backup should skip invalid JSON lines and return False if no ids.
"""
from pathlib import Path
from app.services.vectorstore import chroma_client as cc


class FakeCol:
    def add(self, **kwargs):
        pass


def test_restore_invalid_json(tmp_path):
    bk = tmp_path / 'bad.jsonl'
    bk.write_text('not-json\nanother-bad')
    ch = object.__new__(cc.ChromaClient)
    ch._backup_path = bk
    ch.collection = FakeCol()
    res = ch._restore_from_backup()
    # invalid lines -> no ids -> should return False
    assert res is False
