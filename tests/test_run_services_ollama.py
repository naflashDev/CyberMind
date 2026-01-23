"""
@file test_run_services_ollama.py
@author naflashDev
@brief Unit tests for Ollama-related helpers in run_services.
@details Tests helper functions for detecting and interacting with Ollama in run_services.py, including process mocks and error handling.
"""
import sys
from pathlib import Path
import json
import types

import pytest

# Ensure src is on path so we can import app.utils.run_services
ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
sys.path.insert(0, str(SRC))

from app.utils import run_services


class _Proc:
    def __init__(self, returncode=0, stdout="", stderr=""):
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


def test_is_ollama_available(monkeypatch):
    monkeypatch.setattr(run_services.shutil, "which", lambda name: "/usr/bin/ollama" if name == "ollama" else None)
    assert run_services.is_ollama_available() is True

    monkeypatch.setattr(run_services.shutil, "which", lambda name: None)
    assert run_services.is_ollama_available() is False


def test_try_install_ollama_windows_winget(monkeypatch):
    calls = []

    monkeypatch.setattr(run_services.shutil, "which", lambda name: "/usr/bin/winget" if name == "winget" else None)

    def fake_run(cmd, check=False, **kwargs):
        calls.append(cmd)
        return _Proc()

    monkeypatch.setattr(run_services.subprocess, "run", fake_run)

    res = run_services.try_install_ollama("Windows")
    assert res is True
    assert calls, "Expected subprocess.run to be invoked"
    assert calls[0][0] == "winget"


def test_try_install_ollama_linux_curl(monkeypatch):
    calls = []
    monkeypatch.setattr(run_services.shutil, "which", lambda name: "/usr/bin/curl" if name == "curl" else None)

    def fake_run(cmd, shell=False, check=False, **kwargs):
        calls.append((cmd, shell))
        return _Proc()

    monkeypatch.setattr(run_services.subprocess, "run", fake_run)

    res = run_services.try_install_ollama("Linux")
    assert res is True
    assert calls, "Expected subprocess.run to be called"
    # linux path uses a shell string
    assert calls[0][1] is True


def test_ensure_ollama_model_already_present(monkeypatch, tmp_path):
    # make ollama available
    monkeypatch.setattr(run_services.shutil, "which", lambda name: "/usr/bin/ollama" if name == "ollama" else None)

    # fake `ollama list` returning the model name
    def fake_run(cmd, capture_output=False, text=False, check=False, **kwargs):
        if isinstance(cmd, list) and cmd[:2] == ["ollama", "list"]:
            return _Proc(stdout="cybersentinel\n")
        return _Proc()

    monkeypatch.setattr(run_services.subprocess, "run", fake_run)

    # project root doesn't need Modelfile as model exists
    run_services.ensure_ollama_model(tmp_path, model_name="cybersentinel")


def test_ensure_ollama_model_create(monkeypatch, tmp_path):
    # make ollama available
    monkeypatch.setattr(run_services.shutil, "which", lambda name: "/usr/bin/ollama" if name == "ollama" else None)

    calls = []

    # prepare Install/Modelfile
    install_dir = tmp_path / "Install"
    install_dir.mkdir()
    modelfile = install_dir / "Modelfile"
    modelfile.write_text("model: dummy")

    def fake_run(cmd, capture_output=False, text=False, check=False, **kwargs):
        # record calls
        calls.append(cmd)
        # if `ollama list` return empty
        if isinstance(cmd, list) and cmd[:2] == ["ollama", "list"]:
            return _Proc(stdout="")
        return _Proc()

    monkeypatch.setattr(run_services.subprocess, "run", fake_run)

    run_services.ensure_ollama_model(tmp_path, model_name="cybersentinel")

    # Expect a create command to have been executed
    found = any(isinstance(c, list) and c[:3] == ["ollama", "create", "cybersentinel"] for c in calls)
    assert found, f"Expected ollama create to be called; calls: {calls}"
