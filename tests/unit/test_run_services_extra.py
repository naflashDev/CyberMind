"""
@file test_run_services_extra.py
@brief Extra unit tests for run_services install/model helpers.
"""
from pathlib import Path
import tempfile
import os

import pytest

from app.utils import run_services


def test_try_install_ollama_windows_winget(monkeypatch, tmp_path):
    # Simulate winget present
    monkeypatch.setattr(run_services.shutil, 'which', lambda x: True if x == 'winget' else None)
    called = {}

    def fake_run(cmd, check=False, shell=False):
        called['cmd'] = cmd
        return None

    monkeypatch.setattr(run_services.subprocess, 'run', fake_run)
    assert run_services.try_install_ollama('Windows') is True
    assert 'winget' in called['cmd'][0]


def test_try_install_ollama_linux_no_curl(monkeypatch):
    # Simulate no curl available
    monkeypatch.setattr(run_services.shutil, 'which', lambda x: None)
    assert run_services.try_install_ollama('Linux') is False


def test_ensure_ollama_model_missing_modelfile(monkeypatch, tmp_path):
    # Simulate ollama available but Modelfile missing
    monkeypatch.setattr(run_services, 'is_ollama_available', lambda: True)
    # subprocess.run for "ollama list" returns no output
    monkeypatch.setattr(run_services.subprocess, 'run', lambda *a, **k: type('R', (), {'stdout': ''})())
    # Use a temp project root without Install/Modelfile
    project_root = tmp_path
    # Should not raise
    run_services.ensure_ollama_model(project_root, model_name='cybersentinel')
