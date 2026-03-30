"""
@file test_chroma_init_fallback_chroma_mod.py
@brief Ensure ChromaClient constructor falls back to `chroma` module variant when `chromadb.Client` fails.
"""
import sys
from pathlib import Path
import types

from app.services.vectorstore import chroma_client as cc


class DummyChromaClient:
    def __init__(self, persist_directory=None):
        self._pd = persist_directory

    def persist(self):
        return None


def test_init_uses_chroma_module(tmp_path, monkeypatch):
    # Force chromadb.Client to raise
    monkeypatch.setattr(cc, 'chromadb', types.SimpleNamespace(Client=lambda *a, **k: (_ for _ in ()).throw(Exception('no'))))
    # Provide a fallback 'chroma' module with ChromaClient class
    chroma_mod = types.SimpleNamespace(ChromaClient=DummyChromaClient)
    sys.modules['chroma'] = chroma_mod

    # instantiate the client (should pick up chroma.ChromaClient)
    c = cc.ChromaClient(persist_directory=str(tmp_path), collection_name='testcol', embed_model=None)
    assert getattr(c, 'client', None) is not None
