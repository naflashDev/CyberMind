"""
@file test_text_processor.py
@author GitHub Copilot
@brief Unit tests for text_processor.py
@details Tests for language detection, entity tagging, and JSON processing (mocks, no real spaCy or OpenSearch).
"""
import pytest
import json
from unittest.mock import patch, MagicMock
from src.app.services.spacy import text_processor


def test_detect_language_returns_code():
    '''
    @brief Should return ISO code for known text.
    '''
    assert text_processor.detect_language("Esto es español") == "es"


def test_detect_language_fallback():
    '''
    @brief Should return 'es' if detection fails.
    '''
    assert text_processor.detect_language("") == "es"


def test_extract_texts_extracts_all():
    '''
    @brief Should extract all text fields from dict.
    '''
    data = {"title": "t", "h1": ["a"], "h2": ["b"], "h3": ["c"], "h4": ["d"], "p": ["e"]}
    out = text_processor.extract_texts(data)
    assert set(out) == {"t", "a", "b", "c", "d", "e"}


def test_tag_text_returns_entities_and_lang():
    '''
    @brief Should return entities and detected language.
    '''
    with patch("src.app.services.spacy.text_processor._get_model") as mock_get_model:
        # Create a fake doc object with ents attribute
        fake_ent = MagicMock()
        fake_ent.text = "Madrid"
        fake_ent.label_ = "LOC"
        fake_doc = MagicMock()
        fake_doc.ents = [fake_ent]
        mock_model = MagicMock(return_value=fake_doc)
        mock_get_model.return_value = mock_model
        entities, lang = text_processor.tag_text("Madrid es una ciudad")
        assert lang == "es"
        assert any(e[0] == "Madrid" for e in entities)


# --- _get_model ---
@patch("src.app.services.spacy.text_processor.spacy.load")
def test_get_model_success(mock_load):
    mock_load.return_value = MagicMock()
    model = text_processor._get_model("es")
    assert model is not None

@patch("src.app.services.spacy.text_processor.spacy.load", side_effect=Exception("fail"))
def test_get_model_fallback(mock_load):
    # Falla el modelo principal y el fallback
    with patch("src.app.services.spacy.text_processor.spacy.load", side_effect=[Exception("fail"), Exception("fail2")]):
        with pytest.raises(Exception):
            text_processor._get_model("fr")

# --- tag_text extremos ---
def test_tag_text_empty():
    entities, lang = text_processor.tag_text("")
    assert entities == []
    assert lang == "es"

@patch("src.app.services.spacy.text_processor._get_model")
def test_tag_text_no_model(mock_get):
    mock_get.return_value = None
    entities, lang = text_processor.tag_text("Texto de prueba")
    assert entities == []
    assert lang == "es"

# --- process_json ---
@patch("src.app.services.spacy.text_processor.get_connection_parameters", return_value=(0, "ok", ("localhost", 9200)))
@patch("src.app.services.spacy.text_processor.ensure_index_exists")
@patch("src.app.services.spacy.text_processor.store_in_opensearch")
@patch("src.app.services.spacy.text_processor.text_exists_in_opensearch", return_value=False)
def test_process_json_basic(mock_exists, mock_store, mock_ensure, mock_conn, tmp_path):
    data = [{"title": "Madrid", "h1": ["España"]}]
    in_file = tmp_path / "in.json"
    out_file = tmp_path / "out.json"
    in_file.write_text(json.dumps(data), encoding="utf-8")
    with patch("src.app.services.spacy.text_processor.tag_text", return_value=([("Madrid", "LOC")], "es")):
        text_processor.process_json(str(in_file), str(out_file))
    assert out_file.exists()
    result = json.loads(out_file.read_text(encoding="utf-8"))
    assert any("Madrid" in r["text"] for r in result)
    assert any(r["language"] == "es" for r in result)

@patch("src.app.services.spacy.text_processor.get_connection_parameters", return_value=(1, "fail", ("localhost", 9200)))
@patch("src.app.services.spacy.text_processor.create_config_file", return_value=(0, "created", ("localhost", 9200)))
@patch("src.app.services.spacy.text_processor.ensure_index_exists")
@patch("src.app.services.spacy.text_processor.store_in_opensearch")
@patch("src.app.services.spacy.text_processor.text_exists_in_opensearch", return_value=False)
def test_process_json_creates_config(mock_exists, mock_store, mock_ensure, mock_create, mock_conn, tmp_path):
    data = [{"title": "Madrid"}]
    in_file = tmp_path / "in.json"
    out_file = tmp_path / "out.json"
    in_file.write_text(json.dumps(data), encoding="utf-8")
    with patch("src.app.services.spacy.text_processor.tag_text", return_value=([("Madrid", "LOC")], "es")):
        text_processor.process_json(str(in_file), str(out_file))
    assert out_file.exists()
    result = json.loads(out_file.read_text(encoding="utf-8"))
    assert any("Madrid" in r["text"] for r in result)
