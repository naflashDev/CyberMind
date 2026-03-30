"""
@file test_ollama_adapter.py
@author naflashDev
@brief Unit tests for ollama_adapter
@details Test parsing of various output shapes returned by `_call_ollama_run`.
"""
from app.services.vectorstore.ollama_adapter import OllamaEmbeddingAdapter


def make_adapter_with_mocked_call(mock_return):
    # Create instance without calling __init__ to avoid shutil.which check
    inst = OllamaEmbeddingAdapter.__new__(OllamaEmbeddingAdapter)
    inst.model_name = 'dummy'
    inst.dimensions = 3

    def fake_call(prompt):
        return mock_return

    inst._call_ollama_run = fake_call
    return inst


def test_embed_parses_dict_embedding():
    ad = make_adapter_with_mocked_call({'embedding': [0.1, 0.2, 0.3]})
    res = ad.embed_texts(['a'])
    assert isinstance(res, list)
    assert len(res[0]) == 3


def test_embed_parses_list_return():
    ad = make_adapter_with_mocked_call([0.5, 0.6, 0.7])
    res = ad.embed_texts(['b'])
    assert len(res[0]) == 3


def test_embed_raises_on_unparseable():
    ad = make_adapter_with_mocked_call({'not': 'an embedding'})
    try:
        ad.embed_texts(['c'])
    except RuntimeError:
        # expected when output cannot be parsed
        assert True
    else:
        assert False, 'Expected RuntimeError for unparseable output'


def test_chunking_and_safe_split(monkeypatch):
    # Simulate _call_ollama_run raising context-length error for long chunk
    calls = []

    def fake_call(part):
        calls.append(part)
        s = str(part)
        if len(s) > 20:
            raise RuntimeError('input length exceeds context')
        return {'embedding': [1.0, 2.0, 3.0]}

    ad = make_adapter_with_mocked_call(None)
    ad._call_ollama_run = fake_call
    # Long text will be split internally and averaged
    long_text = 'word ' * 50
    import pytest
    with pytest.raises(RuntimeError):
        ad.embed_texts([long_text])
