"""
@file test_chroma_persist_safe.py
@brief Tests for ChromaClient _persist_safe success and failure.
"""
from pathlib import Path
from app.services.vectorstore import chroma_client as cc


def make_client_with_persist(tmp_path, succeed=True):
    obj = object.__new__(cc.ChromaClient)
    obj.persist_directory = str(tmp_path)
    if succeed:
        obj.client = type('C', (), {'persist': lambda self=None: None})()
    else:
        def bad():
            raise Exception('no persist')
        obj.client = type('C', (), {'persist': bad})()
    obj._can_persist = True
    return obj


def test_persist_safe_success(tmp_path):
    ch = make_client_with_persist(tmp_path, succeed=True)
    assert ch._persist_safe() is True


def test_persist_safe_failure(tmp_path):
    ch = make_client_with_persist(tmp_path, succeed=False)
    assert ch._persist_safe() is False
