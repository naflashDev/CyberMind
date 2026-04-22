"""
@file test_ollama_parse_shapes.py
@brief Tests for OllamaEmbeddingAdapter parsing of different output shapes.
"""
import shutil
import subprocess
from app.services.vectorstore.ollama_adapter import OllamaEmbeddingAdapter


def test_parse_embedding_from_embeddings_key(monkeypatch):
    # Simulate ollama present
    monkeypatch.setattr(shutil, 'which', lambda x: True)

    def fake_call(self, prompt):
        return {'embeddings': [[0.1, 0.2, 0.3]]}

    monkeypatch.setattr(OllamaEmbeddingAdapter, '_call_ollama_run', fake_call)
    adapter = OllamaEmbeddingAdapter(model_name='m')
    res = adapter.embed_texts(['a single short text'])
    assert isinstance(res, list)
    assert len(res[0]) == 3


def test_parse_embedding_from_list_shape(monkeypatch):
    monkeypatch.setattr(shutil, 'which', lambda x: True)

    def fake_call(self, prompt):
        return [1, 2, 3, 4]

    monkeypatch.setattr(OllamaEmbeddingAdapter, '_call_ollama_run', fake_call)
    adapter = OllamaEmbeddingAdapter(model_name='m')
    res = adapter.embed_texts(['text'])
    assert isinstance(res, list)
    assert res[0][0] == 1.0
