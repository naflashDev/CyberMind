"""
@file test_run_services.py
@author naflashDev
@brief Unit tests for run_services infrastructure helpers.
@details Covers Docker/compose/WSL helpers, mocks subprocess and OS calls for edge and error cases.
"""
import pytest
from app.utils import run_services


def test_wsl_docker_is_running_true(monkeypatch):
    """
    Happy Path: Docker container is running.
    """
    # El mock debe devolver el nombre del contenedor en la salida
    monkeypatch.setattr(run_services, "subprocess", type("S", (), {"run": lambda *a, **k: type("R", (), {"stdout": "test\n"})()})())
    assert run_services.wsl_docker_is_running("test") is True

def test_wsl_docker_is_running_false(monkeypatch):
    """
    Edge Case: Docker container is not running.
    """
    monkeypatch.setattr(run_services, "subprocess", type("S", (), {"run": lambda *a, **k: type("R", (), {"stdout": b""})()})())
    assert run_services.wsl_docker_is_running("test") is False

def test_detect_host_os(monkeypatch):
    """
    Happy Path: Returns platform and version.
    """
    monkeypatch.setattr(run_services.platform, "system", lambda: "Windows")
    monkeypatch.setattr(run_services.platform, "release", lambda: "10.0.26200")
    assert run_services.detect_host_os() == ("Windows", "10.0.26200")

def test_is_docker_available(monkeypatch):
    """
    Happy Path: Docker is available.
    """
    monkeypatch.setattr(run_services.shutil, "which", lambda x: True)
    assert run_services.is_docker_available() is True

def test_is_docker_available_false(monkeypatch):
    """
    Edge Case: Docker is not available.
    """
    import importlib
    importlib.reload(run_services)
    monkeypatch.setattr(run_services.shutil, "which", lambda x: None)
    assert run_services.is_docker_available() is False
