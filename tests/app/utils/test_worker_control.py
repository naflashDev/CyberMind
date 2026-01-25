"""
@file test_worker_control.py
@author naflashDev
@brief Tests para worker_control.py
@details Cobertura de defaults, carga, guardado y errores de settings de workers.
"""
import os
import json
import tempfile
import shutil
import pytest
from unittest import mock
from src.app.utils import worker_control

def test_default_settings_keys():
    '''
    @brief Devuelve todos los workers esperados.
    '''
    defaults = worker_control.default_settings()
    assert isinstance(defaults, dict)
    for k in ["google_alerts","rss_extractor","scraping_feeds","scraping_news","spacy_nlp","llm_updater","dynamic_spider"]:
        assert k in defaults

def test_load_worker_settings_default(monkeypatch):
    '''
    @brief Si el archivo no existe, devuelve los defaults.
    '''
    monkeypatch.setattr(worker_control, "SETTINGS_PATH", "no_existe.json")
    s = worker_control.load_worker_settings()
    assert s == worker_control.default_settings()

def test_load_worker_settings_ok(tmp_path, monkeypatch):
    '''
    @brief Carga settings válidos y los fusiona con defaults.
    '''
    f = tmp_path / "worker_settings.json"
    f.write_text(json.dumps({"google_alerts": True, "llm_updater": True}))
    monkeypatch.setattr(worker_control, "SETTINGS_PATH", f)
    s = worker_control.load_worker_settings()
    assert s["google_alerts"] is True
    assert s["llm_updater"] is True
    # El resto por default
    assert s["scraping_feeds"] is False

def test_load_worker_settings_malformed(tmp_path, monkeypatch):
    '''
    @brief Si el archivo está corrupto, devuelve defaults.
    '''
    f = tmp_path / "worker_settings.json"
    f.write_text("MALFORMED")
    monkeypatch.setattr(worker_control, "SETTINGS_PATH", f)
    s = worker_control.load_worker_settings()
    assert s == worker_control.default_settings()

def test_save_worker_settings_ok(tmp_path, monkeypatch):
    '''
    @brief Guarda settings correctamente.
    '''
    f = tmp_path / "worker_settings.json"
    monkeypatch.setattr(worker_control, "SETTINGS_PATH", f)
    d = worker_control.default_settings()
    d["google_alerts"] = True
    worker_control.save_worker_settings(d)
    data = json.loads(f.read_text())
    assert data["google_alerts"] is True

def test_save_worker_settings_error(monkeypatch):
    '''
    @brief Si hay error al guardar, no lanza excepción.
    '''
    def fail_open(*a, **k):
        raise IOError("fail")
    monkeypatch.setattr(worker_control, "SETTINGS_PATH", "fail.json")
    monkeypatch.setattr("builtins.open", fail_open)
    # No debe lanzar excepción
    worker_control.save_worker_settings({"a": True})
