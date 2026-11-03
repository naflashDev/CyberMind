"""
@file test_ingest_coverage_boost.py
@author naflashDev
@brief Boost coverage for ingest.py
"""
import json
import pytest
from pathlib import Path
from unittest.mock import MagicMock
from app.services.documents import ingest as ingest_mod

def test_is_blacklisted_filename():
    assert ingest_mod.is_blacklisted_filename('README.md') is True
    assert ingest_mod.is_blacklisted_filename('delta.json') is True
    assert ingest_mod.is_blacklisted_filename('.gitignore') is True
    assert ingest_mod.is_blacklisted_filename('normal.txt') is False
    assert ingest_mod.is_blacklisted_filename('') is False
    assert ingest_mod.is_blacklisted_filename(None) is False

def test_ingest_blacklisted_file_skipped(tmp_path, monkeypatch):
    monkeypatch.setattr(ingest_mod, 'DEFAULT_BASE', tmp_path)
    res = ingest_mod.ingest_document(b'test', filename='README.md')
    assert res['message'] == 'skipped_blacklisted_file'
    assert res['upserted'] is False

def test_ingest_already_in_chroma_by_source(tmp_path, monkeypatch):
    monkeypatch.setattr(ingest_mod, 'DEFAULT_BASE', tmp_path)
    monkeypatch.setattr(ingest_mod.ingest_tracker, 'exists_by_source', lambda fn: True)
    res = ingest_mod.ingest_document(b'test bytes', filename='already.txt')
    assert res['message'] == 'already ingested (chroma metadata)'
    assert res['upserted'] is True

def test_ingest_reindex_branch(tmp_path, monkeypatch):
    monkeypatch.setattr(ingest_mod, 'DEFAULT_BASE', tmp_path)
    monkeypatch.setattr(ingest_mod.ingest_tracker, 'exists_by_source', lambda fn: False)
    def fake_get(h):
        return {'doc_id': h, 'stored_path': str(tmp_path / 'stored.txt'), 'upserted': False}
    monkeypatch.setattr(ingest_mod.ingest_tracker, 'get_entry', fake_get)
    monkeypatch.setattr(ingest_mod, '_CHROMA_AVAILABLE', True)
    upsert_calls = []
    class FakeChroma:
        def __init__(self, embed_model=None):
            self.embedder = 'mock_embedder'
            self.collection = 'mock_col'
        def upsert_document(self, doc_id, text, metadata):
            upsert_calls.append((doc_id, text, metadata))
    monkeypatch.setattr('app.services.vectorstore.chroma_client.ChromaClient', FakeChroma)
    monkeypatch.setattr(ingest_mod.ingest_tracker, 'mark_upserted', lambda h: None)
    res = ingest_mod.ingest_document(b'some content', filename='stored.txt')
    assert res['message'] == 'reindexed'
    assert res['upserted'] is True
    assert len(upsert_calls) == 1

def test_ingest_cve_json_formatting_and_save_copy_false(tmp_path, monkeypatch):
    monkeypatch.setattr(ingest_mod, 'DEFAULT_BASE', tmp_path)
    monkeypatch.setattr(ingest_mod.ingest_tracker, 'exists_by_source', lambda fn: False)
    monkeypatch.setattr(ingest_mod.ingest_tracker, 'get_entry', lambda h: None)
    monkeypatch.setattr(ingest_mod.ingest_tracker, 'record_ingest', lambda *a, **k: None)
    monkeypatch.setattr(ingest_mod, '_CHROMA_AVAILABLE', True)
    cve_data = {
        'id': 'CVE-2026-9999',
        'containers': {
            'cna': {
                'descriptions': [{'lang': 'en', 'value': 'Critical vulnerability in service xyz.'}],
                'affected': [{'product': 'SuperProduct', 'versions': ['1.0']}]
            }
        },
        'references': ['https://example.com/cve-2026-9999']
    }
    raw_bytes = json.dumps(cve_data).encode('utf-8')
    upserted_docs = []
    class FakeChroma:
        def __init__(self, embed_model=None):
            self.embedder = 'mock_embedder'
            self.collection = 'mock_col'
        def upsert_document(self, doc_id, text, metadata):
            upserted_docs.append((doc_id, text, metadata))
    monkeypatch.setattr('app.services.vectorstore.chroma_client.ChromaClient', FakeChroma)
    cve_file = tmp_path / 'CVE-2026-9999.json'
    cve_file.write_bytes(raw_bytes)
    res = ingest_mod.ingest_document(
        raw_bytes,
        filename='CVE-2026-9999.json',
        save_copy=False,
        original_path=str(cve_file)
    )
    assert res['upserted'] is True
    assert res['message'] == 'saved and indexed'
    assert len(upserted_docs) == 1
    doc_id, text, meta = upserted_docs[0]
    assert 'CVE ID: CVE-2026-9999' in text

def test_ingest_cve_json_list_format(tmp_path, monkeypatch):
    monkeypatch.setattr(ingest_mod, 'DEFAULT_BASE', tmp_path)
    monkeypatch.setattr(ingest_mod.ingest_tracker, 'exists_by_source', lambda fn: False)
    monkeypatch.setattr(ingest_mod.ingest_tracker, 'get_entry', lambda h: None)
    monkeypatch.setattr(ingest_mod.ingest_tracker, 'record_ingest', lambda *a, **k: None)
    monkeypatch.setattr(ingest_mod, '_CHROMA_AVAILABLE', True)
    cve_list = [{
        'CVE_data_meta': {'ID': 'CVE-2025-1111'},
        'description': {'description_data': [{'value': 'Sample description for list test'}]},
        'references': {'reference_data': [{'url': 'https://nvd.nist.gov/vuln/detail/CVE-2025-1111'}]}
    }]
    raw_bytes = json.dumps(cve_list).encode('utf-8')
    upserted_docs = []
    class FakeChroma:
        def __init__(self, embed_model=None):
            self.embedder = 'mock_embedder'
            self.collection = 'mock_col'
        def upsert_document(self, doc_id, text, metadata):
            upserted_docs.append((doc_id, text, metadata))
    monkeypatch.setattr('app.services.vectorstore.chroma_client.ChromaClient', FakeChroma)
    res = ingest_mod.ingest_document(
        raw_bytes,
        filename='cve-list.json',
        save_copy=True
    )
    assert res['upserted'] is True
    doc_id, text, meta = upserted_docs[0]
    assert 'CVE ID: CVE-2025-1111' in text

def test_ingest_cve_json_extra_branches(tmp_path, monkeypatch):
    monkeypatch.setattr(ingest_mod, 'DEFAULT_BASE', tmp_path)
    monkeypatch.setattr(ingest_mod.ingest_tracker, 'exists_by_source', lambda fn: False)
    monkeypatch.setattr(ingest_mod.ingest_tracker, 'get_entry', lambda h: None)
    monkeypatch.setattr(ingest_mod.ingest_tracker, 'record_ingest', lambda *a, **k: None)
    monkeypatch.setattr(ingest_mod, '_CHROMA_AVAILABLE', True)
    
    # Test cna summary + problemtype + affects + references + regex pattern
    cve_data = {
        'CVE_data_meta': {'ID': 'CVE-2024-5555'},
        'containers': {
            'cna': {
                'summary': 'Summary of vulnerability',
                'problemtype': [{'descriptions': [{'description': 'CWE-79 XSS'}]}],
                'affected': [{'vendor': 'Apache', 'product': 'HTTP Server'}]
            }
        },
        'affects': ['Apache 2.4'],
        'vendors': ['The Apache Software Foundation'],
        'products': ['Apache'],
        'configurations': ['default config'],
        'references': ['https://httpd.apache.org/security/vulnerabilities_24.html']
    }
    raw_bytes = json.dumps(cve_data).encode('utf-8')
    upserted_docs = []
    class FakeChroma:
        def __init__(self, embed_model=None):
            self.embedder = 'mock_embedder'
            self.collection = 'mock_col'
        def upsert_document(self, doc_id, text, metadata):
            upserted_docs.append((doc_id, text, metadata))
    monkeypatch.setattr('app.services.vectorstore.chroma_client.ChromaClient', FakeChroma)
    res = ingest_mod.ingest_document(
        raw_bytes,
        filename='cve-2024-5555.json',
        save_copy=True
    )
    assert res['upserted'] is True
    doc_id, text, meta = upserted_docs[0]
    assert 'CVE ID: CVE-2024-5555' in text
    assert 'Summary of vulnerability' in text

def test_ingest_cve_json_invalid_syntax(tmp_path, monkeypatch):
    monkeypatch.setattr(ingest_mod, 'DEFAULT_BASE', tmp_path)
    monkeypatch.setattr(ingest_mod.ingest_tracker, 'exists_by_source', lambda fn: False)
    monkeypatch.setattr(ingest_mod.ingest_tracker, 'get_entry', lambda h: None)
    monkeypatch.setattr(ingest_mod.ingest_tracker, 'record_ingest', lambda *a, **k: None)
    monkeypatch.setattr(ingest_mod, '_CHROMA_AVAILABLE', True)
    
    # Broken json with cve name
    broken_bytes = b'{invalid json cve'
    upserted_docs = []
    class FakeChroma:
        def __init__(self, embed_model=None):
            self.embedder = 'mock_embedder'
            self.collection = 'mock_col'
        def upsert_document(self, doc_id, text, metadata):
            upserted_docs.append((doc_id, text, metadata))
    monkeypatch.setattr('app.services.vectorstore.chroma_client.ChromaClient', FakeChroma)
    res = ingest_mod.ingest_document(
        broken_bytes,
        filename='cve-broken.json',
        save_copy=True
    )
    assert res['upserted'] is True

def test_ingest_chroma_exceptions_and_no_embedder(tmp_path, monkeypatch):
    monkeypatch.setattr(ingest_mod, 'DEFAULT_BASE', tmp_path)
    monkeypatch.setattr(ingest_mod.ingest_tracker, 'exists_by_source', lambda fn: False)
    monkeypatch.setattr(ingest_mod.ingest_tracker, 'get_entry', lambda h: None)
    monkeypatch.setattr(ingest_mod.ingest_tracker, 'record_ingest', lambda *a, **k: None)
    monkeypatch.setattr(ingest_mod, '_CHROMA_AVAILABLE', True)

    class ChromaFail:
        def __init__(self, embed_model=None):
            self.embedder = 'mock'
            self.collection = 'mock'
        def upsert_document(self, *a, **k):
            raise RuntimeError('Chroma boom')

    monkeypatch.setattr('app.services.vectorstore.chroma_client.ChromaClient', ChromaFail)
    res = ingest_mod.ingest_document(b'content', filename='fail.txt')
    assert res['upserted'] is False

def test_ingest_chroma_not_available(tmp_path, monkeypatch):
    monkeypatch.setattr(ingest_mod, 'DEFAULT_BASE', tmp_path)
    monkeypatch.setattr(ingest_mod.ingest_tracker, 'exists_by_source', lambda fn: False)
    monkeypatch.setattr(ingest_mod.ingest_tracker, 'get_entry', lambda h: None)
    monkeypatch.setattr(ingest_mod.ingest_tracker, 'record_ingest', lambda *a, **k: None)
    monkeypatch.setattr(ingest_mod, '_CHROMA_AVAILABLE', False)

    res = ingest_mod.ingest_document(b'no chroma here', filename='no_chroma.txt')
    assert res['upserted'] is False

def test_ingest_save_copy_with_original_path_inside_base(tmp_path, monkeypatch):
    base = tmp_path / 'documents'
    base.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(ingest_mod, 'DEFAULT_BASE', base)
    monkeypatch.setattr(ingest_mod.ingest_tracker, 'exists_by_source', lambda fn: False)
    monkeypatch.setattr(ingest_mod.ingest_tracker, 'get_entry', lambda h: None)
    monkeypatch.setattr(ingest_mod.ingest_tracker, 'record_ingest', lambda *a, **k: None)
    monkeypatch.setattr(ingest_mod, '_CHROMA_AVAILABLE', False)

    existing_file = base / 'existing_in_base.txt'
    existing_file.write_text('content already here')
    
    res = ingest_mod.ingest_document(
        b'content already here',
        filename='existing_in_base.txt',
        save_copy=True,
        original_path=str(existing_file)
    )
    assert res['path'] == str(existing_file.as_posix())

def test_ingest_save_copy_false_empty_path(tmp_path, monkeypatch):
    monkeypatch.setattr(ingest_mod, 'DEFAULT_BASE', tmp_path)
    monkeypatch.setattr(ingest_mod.ingest_tracker, 'exists_by_source', lambda fn: False)
    monkeypatch.setattr(ingest_mod.ingest_tracker, 'get_entry', lambda h: None)
    monkeypatch.setattr(ingest_mod.ingest_tracker, 'record_ingest', lambda *a, **k: None)
    monkeypatch.setattr(ingest_mod, '_CHROMA_AVAILABLE', False)

    res = ingest_mod.ingest_document(b'test bytes', filename='no_copy.txt', save_copy=False)
    assert res['path'] == ''

def test_ingest_chroma_collection_none(tmp_path, monkeypatch):
    monkeypatch.setattr(ingest_mod, 'DEFAULT_BASE', tmp_path)
    monkeypatch.setattr(ingest_mod.ingest_tracker, 'exists_by_source', lambda fn: False)
    monkeypatch.setattr(ingest_mod.ingest_tracker, 'get_entry', lambda h: None)
    monkeypatch.setattr(ingest_mod.ingest_tracker, 'record_ingest', lambda *a, **k: None)
    monkeypatch.setattr(ingest_mod, '_CHROMA_AVAILABLE', True)

    class ChromaNoCol:
        def __init__(self, embed_model=None):
            self.embedder = 'mock'
            self.collection = None
        def upsert_document(self, *a, **k):
            pass

    monkeypatch.setattr('app.services.vectorstore.chroma_client.ChromaClient', ChromaNoCol)
    res = ingest_mod.ingest_document(b'content', filename='no_col.txt')
    assert res['upserted'] is False
    assert res['message'] == 'saved (no collection)'

def test_ingest_with_ollama_adapter_branch(tmp_path, monkeypatch):
    monkeypatch.setattr(ingest_mod, 'DEFAULT_BASE', tmp_path)
    monkeypatch.setattr(ingest_mod.ingest_tracker, 'exists_by_source', lambda fn: False)
    monkeypatch.setattr(ingest_mod.ingest_tracker, 'get_entry', lambda h: None)
    monkeypatch.setattr(ingest_mod.ingest_tracker, 'record_ingest', lambda *a, **k: None)
    monkeypatch.setattr(ingest_mod, '_CHROMA_AVAILABLE', True)
    
    import shutil
    monkeypatch.setattr(shutil, 'which', lambda x: '/usr/bin/ollama' if x == 'ollama' else None)
    
    class FakeAdapter:
        def __init__(self, model_name=None):
            self.model_name = model_name
            
    monkeypatch.setattr(ingest_mod, 'OllamaEmbeddingAdapter', FakeAdapter)
    
    class FakeChroma:
        def __init__(self, embed_model=None):
            self.embedder = embed_model
            self.collection = 'mock'
        def upsert_document(self, *a, **k):
            pass
            
    monkeypatch.setattr('app.services.vectorstore.chroma_client.ChromaClient', FakeChroma)
    res = ingest_mod.ingest_document(b'testing ollama embed model branch', filename='doc_ollama.txt')
    assert res['upserted'] is True
    assert res['message'] == 'saved and indexed'

def test_ingest_with_ollama_adapter_raises(tmp_path, monkeypatch):
    monkeypatch.setattr(ingest_mod, 'DEFAULT_BASE', tmp_path)
    monkeypatch.setattr(ingest_mod.ingest_tracker, 'exists_by_source', lambda fn: False)
    monkeypatch.setattr(ingest_mod.ingest_tracker, 'get_entry', lambda h: None)
    monkeypatch.setattr(ingest_mod.ingest_tracker, 'record_ingest', lambda *a, **k: None)
    monkeypatch.setattr(ingest_mod, '_CHROMA_AVAILABLE', True)
    
    import shutil
    monkeypatch.setattr(shutil, 'which', lambda x: '/usr/bin/ollama' if x == 'ollama' else None)
    
    def fake_adapter_boom(*a, **k):
        raise RuntimeError('ollama adapter error')
        
    monkeypatch.setattr(ingest_mod, 'OllamaEmbeddingAdapter', fake_adapter_boom)
    
    class FakeChroma:
        def __init__(self, embed_model=None):
            self.embedder = embed_model
            self.collection = 'mock'
        def upsert_document(self, *a, **k):
            pass
            
    monkeypatch.setattr('app.services.vectorstore.chroma_client.ChromaClient', FakeChroma)
    res = ingest_mod.ingest_document(b'testing ollama embed model error branch', filename='doc_ollama_err.txt')
    assert res['upserted'] is False
    assert res['message'] == 'saved (no embedder)'

def test_ensure_folder_sanitization(tmp_path, monkeypatch):
    monkeypatch.setattr(ingest_mod, 'DEFAULT_BASE', tmp_path)
    b1 = ingest_mod._ensure_folder('my folder!@#')
    assert b1.name == 'myfolder'
    b2 = ingest_mod._ensure_folder('!@#$%')
    assert b2.name == 'default'

def test_ingest_record_ingest_failure(tmp_path, monkeypatch):
    monkeypatch.setattr(ingest_mod, 'DEFAULT_BASE', tmp_path)
    monkeypatch.setattr(ingest_mod.ingest_tracker, 'exists_by_source', lambda fn: False)
    monkeypatch.setattr(ingest_mod.ingest_tracker, 'get_entry', lambda h: None)
    
    def bad_record(*a, **k):
        raise RuntimeError('record failed')
    monkeypatch.setattr(ingest_mod.ingest_tracker, 'record_ingest', bad_record)
    monkeypatch.setattr(ingest_mod, '_CHROMA_AVAILABLE', False)

    res = ingest_mod.ingest_document(b'test bytes', filename='record_fail.txt')
    assert res['upserted'] is False
