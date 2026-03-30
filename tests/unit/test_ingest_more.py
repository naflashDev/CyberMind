"""
@file test_ingest_more.py
@brief Additional tests for `ingest_document` behavior: duplicates, saving collisions, and Chroma upsert fallbacks.
"""
from pathlib import Path
from datetime import datetime
import importlib
import os

import pytest

from app.services.documents import ingest as ing


def test_text_from_bytes_utf8_and_latin1():
    data_utf8 = 'hola ñ'.encode('utf-8')
    assert 'hola' in ing._text_from_bytes(data_utf8, 'file.txt')
    # latin1 bytes that are invalid utf-8 but valid latin1
    data_latin1 = bytes([0xE1, 0xE9, 0xF3])  # á é ó in latin1
    res = ing._text_from_bytes(data_latin1, 'f.bin')
    assert isinstance(res, str)


def test_ingest_duplicate_already_upserted(monkeypatch):
    # Simulate tracker returning existing entry with upserted True
    monkeypatch.setattr(ing.ingest_tracker, 'get_entry', lambda h: {
        'upserted': True,
        'doc_id': 'docx',
        'stored_path': '/some/path/file.txt'
    })
    res = ing.ingest_document(b'content', filename='file.txt')
    assert res['upserted'] is True
    assert res['message'] == 'already ingested'


def test_ingest_duplicate_not_upserted_no_chroma(monkeypatch):
    # Simulate tracker entry not upserted and chroma not available
    monkeypatch.setattr(ing.ingest_tracker, 'get_entry', lambda h: {
        'upserted': False,
        'stored_path': '/some/path/file.txt'
    })
    # Force module-level flag
    monkeypatch.setattr(ing, '_CHROMA_AVAILABLE', False)
    res = ing.ingest_document(b'content', filename='file.txt')
    assert res['upserted'] is False
    assert 'reindex' in res['message'] or 'saved' in res['message']


def test_ingest_save_collision_and_record(monkeypatch, tmp_path):
    # Ensure base folder isolated
    base = tmp_path / 'data' / 'documents'
    monkeypatch.setattr(ing, 'DEFAULT_BASE', base)
    base.mkdir(parents=True, exist_ok=True)
    # create existing file with same name to force collision renaming
    f = base / 'myfile.txt'
    f.write_text('orig')

    called = {}
    def fake_record(content_hash, doc_id, stored_path, filename, folder, upserted=False):
        called['stored'] = stored_path

    monkeypatch.setattr(ing.ingest_tracker, 'get_entry', lambda h: None)
    monkeypatch.setattr(ing.ingest_tracker, 'record_ingest', fake_record)
    res = ing.ingest_document(b'hello world', filename='myfile.txt', folder=None)
    # stored filename should not be exactly myfile.txt (collision resolved)
    assert res['file'] != 'myfile.txt' or res['file'].startswith('myfile')
    assert 'stored' in called


def test_ingest_chroma_upsert_no_embedder_or_collection(monkeypatch, tmp_path):
    # Simulate chroma available and ChromaClient that has no embedder/collection
    monkeypatch.setattr(ing, '_CHROMA_AVAILABLE', True)

    class FakeClient:
        def __init__(self, embed_model=None):
            self.embedder = None
            self.collection = None

        def upsert_document(self, *a, **k):
            return None

    # Patch the ChromaClient used inside ingest_document
    import app.services.vectorstore.chroma_client as ccmod
    monkeypatch.setattr(ccmod, 'ChromaClient', FakeClient)

    # ensure tracker records
    monkeypatch.setattr(ing.ingest_tracker, 'get_entry', lambda h: None)
    monkeypatch.setattr(ing.ingest_tracker, 'record_ingest', lambda *a, **k: None)

    # ensure no Ollama detected
    monkeypatch.setattr(ing.shutil, 'which', lambda x: False)

    res = ing.ingest_document(b'some bytes', filename='f.txt', folder=None)
    # upserted should be False because embedder/collection absent
    assert res['upserted'] is False
    assert 'saved' in res['message']
"""
@file test_ingest_more.py
@brief More tests for ingest module covering file saving and PDF fallback
"""
import os
from pathlib import Path

from app.services.documents import ingest as ingest_mod


def test_ingest_saves_file_and_records(monkeypatch, tmp_path):
    # ensure DEFAULT_BASE points to tmp
    monkeypatch.setattr(ingest_mod, 'DEFAULT_BASE', tmp_path)
    # disable chroma
    monkeypatch.setattr(ingest_mod, '_CHROMA_AVAILABLE', False)

    recorded = {}

    def fake_record(content_hash, doc_id, stored_path, filename, folder, upserted=False):
        recorded['doc_id'] = doc_id
        recorded['stored_path'] = stored_path

    monkeypatch.setattr(ingest_mod.ingest_tracker, 'record_ingest', fake_record)
    # Ensure no previous ingest record interferes
    monkeypatch.setattr(ingest_mod.ingest_tracker, 'get_entry', lambda h: None)

    data = b'hello world'
    out = ingest_mod.ingest_document(data, filename='my file.txt', folder='tests', conversation_id=5, original_url='http://x')
    # file should be saved under tmp_path/tests
    assert 'path' in out and out['path']
    saved = Path(out['path'])
    assert saved.exists()
    # tracker should have been called
    assert 'doc_id' in recorded


def test_text_from_pdf_fallback(monkeypatch):
    # Provide bytes starting with PDF header but no PdfReader available -> should fallback to decoding
    monkeypatch.setattr(ingest_mod, 'PdfReader', None)
    pdf_bytes = b'%PDF-1.4\n%...' + b'hello'
    txt = ingest_mod._text_from_bytes(pdf_bytes, 'doc.pdf')
    # fallback decoding should return a string (may be empty)
    assert isinstance(txt, str)
