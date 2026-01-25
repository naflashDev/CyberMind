"""
@file test_finetune_dataset_builder.py
@author naflashDev
@brief Unit tests for finetune_dataset_builder.py
@details Tests for dataset building utilities for LLM fine-tuning.
"""
import os
import json
import tempfile
import shutil
import pytest
from pathlib import Path

from src.app.services.llm import finetune_dataset_builder as builder

def test_load_json_returns_none_for_missing_file():
    '''
    @brief Should return None if file does not exist.
    '''
    assert builder._load_json('nonexistent_file.json') is None

def test_load_json_returns_data(tmp_path):
    '''
    @brief Should load valid JSON content.
    '''
    data = {"foo": "bar"}
    file = tmp_path / "test.json"
    file.write_text(json.dumps(data), encoding="utf-8")
    assert builder._load_json(str(file)) == data

def test_load_json_handles_invalid_json(tmp_path):
    '''
    @brief Should return None if JSON is invalid.
    '''
    file = tmp_path / "bad.json"
    file.write_text("not a json", encoding="utf-8")
    assert builder._load_json(str(file)) is None

def test_build_finetune_dataset_creates_jsonl(tmp_path):
    '''
    @brief Should create a JSONL file with CVE and news examples.
    '''
    cve_data = [
        {"instruction": "inst1", "input": "in1", "output": "out1"},
        {"instruction": "inst2", "input": "in2", "output": "out2"}
    ]
    news_data = {"title": "Noticia", "p": ["parrafo1", "parrafo2"]}
    cve_path = tmp_path / "cve.json"
    news_path = tmp_path / "news.json"
    output_path = tmp_path / "finetune.jsonl"
    cve_path.write_text(json.dumps(cve_data), encoding="utf-8")
    news_path.write_text(json.dumps(news_data), encoding="utf-8")
    builder.build_finetune_dataset(str(cve_path), str(news_path), str(output_path))
    lines = output_path.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 3
    # Check CVE records
    for i in range(2):
        rec = json.loads(lines[i])
        assert rec["instruction"] == cve_data[i]["instruction"]
        assert rec["input"] == cve_data[i]["input"]
        assert rec["output"] == cve_data[i]["output"]
        assert rec["source"] == "cve"
    # Check news record
    rec = json.loads(lines[2])
    assert rec["source"] == "news"
    assert "noticia" in rec["input"].lower()
    assert rec["instruction"].startswith("Resume en tres frases")

def test_build_finetune_dataset_handles_empty_inputs(tmp_path):
    '''
    @brief Should not fail if input files are empty or missing.
    '''
    output_path = tmp_path / "finetune.jsonl"
    builder.build_finetune_dataset("nonexistent_cve.json", "nonexistent_news.json", str(output_path))
    assert output_path.exists()
    assert output_path.read_text(encoding="utf-8").strip() == ""
