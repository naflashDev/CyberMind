"""
@file test_ingest.py
@author naflashDev
@brief Unit tests for ingest module
@details Tests cover _text_from_bytes and ingest_document duplicate handling.
"""
import os
import shutil
from pathlib import Path
import tempfile
import types

from app.services.documents import ingest as ingest_mod


def test_text_from_bytes_utf8_and_latin1():
    '''
    @brief Validate _text_from_bytes decodes UTF-8 and falls back to latin1.
    '''
    s = 'café – prueba'.encode('utf-8')
    assert 'café' in ingest_mod._text_from_bytes(s, 'test.txt')

    # latin1-only bytes (invalid utf-8 sequence)
    b = bytes([0xff, 0xfe, 0x41, 0x42])
    res = ingest_mod._text_from_bytes(b, 'weird.bin')
    assert isinstance(res, str)


def test_ingest_document_existing_entry(monkeypatch, tmp_path):
    '''
    @brief When ingest_tracker reports an existing, upserted entry, ingest_document should return existing metadata and skip saving.
    '''
    # Prepare module to write into tmp base
    monkeypatch.setattr(ingest_mod, 'DEFAULT_BASE', tmp_path)

    # Simulate ingest_tracker.get_entry returning an already upserted record
    def fake_get_entry(ch):
        return {'content_hash': ch, 'doc_id': 'doc123', 'stored_path': str(tmp_path / 'doc.txt'), 'upserted': True}

    monkeypatch.setattr(ingest_mod.ingest_tracker, 'get_entry', fake_get_entry)

    data = b'hello world'
    out = ingest_mod.ingest_document(data, filename='file.txt', folder=None)
    assert out['doc_id'] == 'doc123'
    assert out['upserted'] is True

    # Now simulate existing but not upserted -> should attempt reindex branch (with chroma disabled this path still returns)
    def fake_get_entry2(ch):
        return {'content_hash': ch, 'doc_id': 'doc123', 'stored_path': str(tmp_path / 'doc.txt'), 'upserted': False}

    monkeypatch.setattr(ingest_mod.ingest_tracker, 'get_entry', fake_get_entry2)
    # monkeypatch chroma availability to False to avoid upsert attempts
    monkeypatch.setattr(ingest_mod, '_CHROMA_AVAILABLE', False)
    out2 = ingest_mod.ingest_document(data, filename='file2.txt', folder=None)
    assert out2['doc_id'] is not None
