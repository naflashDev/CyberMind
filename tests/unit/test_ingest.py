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


def test_text_from_bytes_pdf_fallback(monkeypatch):
    '''
    @brief If pypdf is missing or fails, ensure fallback decoding is used.
    '''
    # Force PdfReader to None to simulate missing dependency
    monkeypatch.setattr(ingest_mod, 'PdfReader', None)
    content = b'%PDF somepdfdata'
    res = ingest_mod._text_from_bytes(content, 'doc.pdf')
    # With PdfReader missing, it should fallback to decoding (likely empty or str)
    assert isinstance(res, str)


def test_ingest_document_name_collision(monkeypatch, tmp_path):
    '''
    @brief Ensure ingest_document handles existing filename collisions by creating numbered copies.
    '''
    monkeypatch.setattr(ingest_mod, 'DEFAULT_BASE', tmp_path)
    # Create an existing file with same name
    target = tmp_path / 'file.txt'
    target.write_bytes(b'existing')
    data = b'new content'
    # Ensure tracker returns None so branch saves new file with incremented name
    monkeypatch.setattr(ingest_mod.ingest_tracker, 'get_entry', lambda ch: None)
    out = ingest_mod.ingest_document(data, filename='file.txt', folder=None)
    assert out['file'] != 'file.txt' or out['file'].startswith('file_')


def test_text_from_bytes_pdf_with_pypdf(monkeypatch):
    '''
    @brief When PdfReader is available, ensure page.extract_text is used.
    '''
    class FakePage:
        def __init__(self, text):
            self._text = text

        def extract_text(self):
            return self._text

    class FakePdfReader:
        def __init__(self, stream):
            self.pages = [FakePage('page1'), FakePage('page2')]

    monkeypatch.setattr(ingest_mod, 'PdfReader', FakePdfReader)
    content = b'%PDF 1.4 dummy'
    txt = ingest_mod._text_from_bytes(content, 'file.PDF')
    assert 'page1' in txt and 'page2' in txt


def test_text_from_bytes_pdf_reader_raises(monkeypatch):
    '''
    @brief If PdfReader raises, fallback to decoding should be used.
    '''
    class BadPdf:
        def __init__(self, stream):
            raise Exception('fail')

    monkeypatch.setattr(ingest_mod, 'PdfReader', BadPdf)
    content = b'%PDF something utf8'
    res = ingest_mod._text_from_bytes(content, 'doc.pdf')
    assert isinstance(res, str)


def test_ingest_document_upsert_no_embedder_or_collection(monkeypatch, tmp_path):
    '''
    @brief Simulate chroma available but ChromaClient without embedder/collection.
    '''
    monkeypatch.setattr(ingest_mod, 'DEFAULT_BASE', tmp_path)
    monkeypatch.setattr(ingest_mod, '_CHROMA_AVAILABLE', True)

    # Fake ChromaClient in the module path used by ingest_document
    class FakeClient:
        def __init__(self, embed_model=None):
            self.embedder = None
            self.collection = None

        def upsert_document(self, doc_id, text, metadata):
            # pretend to accept the upsert
            return None

    monkeypatch.setattr('app.services.vectorstore.chroma_client.ChromaClient', FakeClient)
    # ensure no previous entry
    monkeypatch.setattr(ingest_mod.ingest_tracker, 'get_entry', lambda ch: None)
    # capture record_ingest calls
    recorded = {}
    def fake_record_ingest(ch, doc_id, path, filename, folder, upserted=False):
        recorded['called'] = True

    monkeypatch.setattr(ingest_mod.ingest_tracker, 'record_ingest', fake_record_ingest)

    data = b'hello for chroma'
    out = ingest_mod.ingest_document(data, filename='c.txt', folder=None)
    assert recorded.get('called', False) is True
    # since embedder is None we expect upserted False and message mentioning 'no embedder' or 'saved'
    assert out['upserted'] is False

