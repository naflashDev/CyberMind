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
