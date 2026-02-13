"""
@file test_worker_control_unit.py
@author naflashDev
@brief Unit tests for worker settings persistence and restoration.
@details Tests the correct saving and loading of worker states in worker_settings.json, including shutdown persistence logic.
"""

import os
import json
import tempfile
import shutil
import pytest
from pathlib import Path
from app.utils import worker_control

@pytest.fixture
def temp_settings_file(monkeypatch):
    # Create a temporary directory and patch SETTINGS_PATH
    tmpdir = tempfile.mkdtemp()
    settings_path = Path(tmpdir) / "worker_settings.json"
    monkeypatch.setattr(worker_control, "SETTINGS_PATH", settings_path)
    yield settings_path
    shutil.rmtree(tmpdir)


def test_save_and_load_worker_settings(temp_settings_file):
    """
    @brief Happy Path: Save and load worker settings.
    Test that saving a settings dict and then loading it returns the same values.
    """
    settings = {
        "google_alerts": True,
        "rss_extractor": False,
        "scraping_feeds": True,
        "scraping_news": False,
        "spacy_nlp": True,
        "llm_updater": False,
        "dynamic_spider": True,
    }
    worker_control.save_worker_settings(settings)
    loaded = worker_control.load_worker_settings()
    assert loaded == settings


def test_load_defaults_on_missing_file(monkeypatch, temp_settings_file):
    """
    @brief Edge Case: Load defaults if file missing.
    If worker_settings.json does not exist, defaults are returned.
    """
    if temp_settings_file.exists():
        temp_settings_file.unlink()
    loaded = worker_control.load_worker_settings()
    assert loaded == worker_control.default_settings()


def test_save_handles_invalid_data(monkeypatch, temp_settings_file):
    """
    @brief Error Handling: Save handles invalid data.
    If the file is corrupted, loading returns defaults.
    """
    # Write invalid JSON
    with open(temp_settings_file, "w", encoding="utf-8") as f:
        f.write("not a json")
    loaded = worker_control.load_worker_settings()
    assert loaded == worker_control.default_settings()


def test_shutdown_persists_stopped_state(monkeypatch, temp_settings_file):
    """
    @brief Happy Path: Shutdown persists all workers as stopped.
    Simulate shutdown logic: mark all as False and persist.
    """
    # Start with some workers active
    initial = {
        "google_alerts": True,
        "rss_extractor": True,
        "scraping_feeds": True,
        "scraping_news": True,
        "spacy_nlp": True,
        "llm_updater": True,
        "dynamic_spider": True,
    }
    worker_control.save_worker_settings(initial)
    # Simulate shutdown logic
    stopped = {k: False for k in initial}
    worker_control.save_worker_settings(stopped)
    loaded = worker_control.load_worker_settings()
    assert all(v is False for v in loaded.values())
