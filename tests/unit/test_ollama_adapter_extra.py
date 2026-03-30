"""
@file test_ollama_adapter_extra.py
@brief Additional unit tests for OllamaEmbeddingAdapter parsing and splitting behavior.
"""
import os
import shutil
import subprocess
from pathlib import Path

import pytest

from app.services.vectorstore.ollama_adapter import OllamaEmbeddingAdapter


class DummyProc:
    def __init__(self, returncode=0, stdout=b"", stderr=b""):
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


def test_call_ollama_run_nonzero(monkeypatch):
    monkeypatch.setattr(shutil, "which", lambda x: True)
    def fake_run(cmd, input=None, capture_output=None):
        return DummyProc(returncode=1, stdout=b"", stderr=b"bad")
    monkeypatch.setattr(subprocess, "run", fake_run)
    adapter = OllamaEmbeddingAdapter.__new__(OllamaEmbeddingAdapter)
    adapter.model_name = "m"
    with pytest.raises(RuntimeError):
        adapter._call_ollama_run("x")


def test_call_ollama_run_json(monkeypatch):
    monkeypatch.setattr(shutil, "which", lambda x: True)
    def fake_run(cmd, input=None, capture_output=None):
        return DummyProc(returncode=0, stdout=b'{"embedding": [1, 2, 3]}')
    monkeypatch.setattr(subprocess, "run", fake_run)
    adapter = OllamaEmbeddingAdapter(model_name="m")
    out = adapter._call_ollama_run("hello")
    assert isinstance(out, dict)


def test_embed_texts_parse_and_dump(tmp_path, monkeypatch):
    # when output cannot be parsed to embedding, adapter should dump raw output and raise
    monkeypatch.setattr(shutil, "which", lambda x: True)
    def fake_call(self, prompt):
        return "not json"
    monkeypatch.setattr(OllamaEmbeddingAdapter, "_call_ollama_run", fake_call)
    adapter = OllamaEmbeddingAdapter.__new__(OllamaEmbeddingAdapter)
    adapter.model_name = "m"
    adapter.dimensions = 3
    # run should raise due to parse failure
    with pytest.raises(RuntimeError):
        adapter.embed_texts(["some text with \x00 null"])
    # expect a dump file created under data/ollama_raw
    dump_dir = Path('data') / 'ollama_raw'
    assert dump_dir.exists()


def test_embed_texts_split_and_average(monkeypatch):
    monkeypatch.setattr(shutil, "which", lambda x: True)
    # create behavior: if chunk length > 30 raise context error, else return embedding
    def fake_call(self, prompt):
        if len(prompt) > 30:
            raise Exception('input length exceeds context')
        return {"embedding": [1.0, 1.0, 1.0]}

    monkeypatch.setattr(OllamaEmbeddingAdapter, "_call_ollama_run", fake_call)
    adapter = OllamaEmbeddingAdapter(model_name="m")
    # Lower MIN_CHUNK_SIZE so splitting is attempted instead of giving up
    monkeypatch.setenv('OLLAMA_MIN_CHUNK_CHARS', '10')
    res = adapter.embed_texts(["this is a long text that will be split"])
    assert isinstance(res, list) and isinstance(res[0], list)
