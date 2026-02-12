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
    Test is robust to run both in Windows and Linux CI runners.
    """
    # Simulate Windows
    monkeypatch.setattr(run_services.platform, "system", lambda: "Windows")
    monkeypatch.setattr(run_services.platform, "version", lambda: "10.0.26200")
    assert run_services.detect_host_os() == ("Windows", "10.0.26200")

    # Simulate Linux with PRETTY_NAME
    monkeypatch.setattr(run_services.platform, "system", lambda: "Linux")
    # Simular que /etc/os-release no existe, así que distro será None
    from pathlib import Path
    monkeypatch.setattr(Path, "exists", lambda self: False)
    assert run_services.detect_host_os() == ("Linux", None)

    # Simulate Darwin
    monkeypatch.setattr(run_services.platform, "system", lambda: "Darwin")
    monkeypatch.setattr(run_services.platform, "mac_ver", lambda: ("12.6.1", ("", "", ""), ""))
    assert run_services.detect_host_os() == ("Darwin", "12.6.1")

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


def test_wsl_docker_start_container_host(monkeypatch):
    """
    Happy Path: Start container on host (no WSL).
    """
    monkeypatch.setattr(run_services.platform, "system", lambda: "Linux")
    called = {}
    def fake_run(cmd, check=False):
        called['cmd'] = cmd
        return None
    monkeypatch.setattr(run_services.subprocess, "run", fake_run)
    monkeypatch.setattr(run_services.logger, "info", lambda *a, **k: None)
    run_services.wsl_docker_start_container("test_container")
    assert called['cmd'] == ["docker", "start", "test_container"]

def test_wsl_docker_start_container_wsl(monkeypatch):
    """
    Happy Path: Start container in WSL distro.
    """
    monkeypatch.setattr(run_services.platform, "system", lambda: "Windows")
    called = {}
    def fake_run(cmd, check=False):
        called['cmd'] = cmd
        return None
    monkeypatch.setattr(run_services.subprocess, "run", fake_run)
    monkeypatch.setattr(run_services.logger, "info", lambda *a, **k: None)
    run_services.wsl_docker_start_container("test_container", distro_name="Ubuntu")
    assert called['cmd'] == ["wsl", "-d", "Ubuntu", "--", "docker", "start", "test_container"]

def test_is_docker_daemon_running_true(monkeypatch):
    """
    Happy Path: Docker daemon responde correctamente.
    """
    monkeypatch.setattr(run_services, "is_docker_available", lambda: True)
    monkeypatch.setattr(run_services.subprocess, "run", lambda *a, **k: type("R", (), {"returncode": 0})())
    assert run_services.is_docker_daemon_running() is True

def test_is_docker_daemon_running_false(monkeypatch):
    """
    Edge Case: Docker no disponible o error en subprocess.
    """
    monkeypatch.setattr(run_services, "is_docker_available", lambda: False)
    assert run_services.is_docker_daemon_running() is False
    monkeypatch.setattr(run_services, "is_docker_available", lambda: True)
    monkeypatch.setattr(run_services.subprocess, "run", lambda *a, **k: (_ for _ in ()).throw(Exception("fail")))
    assert run_services.is_docker_daemon_running() is False

def test_ensure_docker_daemon_running_windows(monkeypatch):
    """
    Happy Path: Windows, intenta iniciar Docker Desktop.
    """
    monkeypatch.setattr(run_services.platform, "system", lambda: "Windows")
    monkeypatch.setattr(run_services.logger, "info", lambda *a, **k: None)
    monkeypatch.setattr(run_services.logger, "warning", lambda *a, **k: None)
    monkeypatch.setattr(run_services.logger, "error", lambda *a, **k: None)
    monkeypatch.setattr(run_services, "is_docker_daemon_running", lambda: False)
    monkeypatch.setattr(run_services.time, "sleep", lambda x: None)
    monkeypatch.setattr(run_services.subprocess, "run", lambda *a, **k: None)
    monkeypatch.setattr(run_services.Path, "exists", lambda self: False)
    # For the polling loop, always return True after attempts
    monkeypatch.setattr(run_services, "is_docker_daemon_running", lambda: True)
    assert run_services.ensure_docker_daemon_running("Windows") is True

def test_is_ollama_available(monkeypatch):
    """
    Happy Path: ollama CLI está en PATH.
    """
    monkeypatch.setattr(run_services.shutil, "which", lambda x: True)
    assert run_services.is_ollama_available() is True

def test_is_ollama_available_false(monkeypatch):
    """
    Edge Case: ollama CLI no está en PATH.
    """
    monkeypatch.setattr(run_services.shutil, "which", lambda x: None)
    assert run_services.is_ollama_available() is False

def test_os_get_euid_windows(monkeypatch):
    """
    Happy Path: Windows, siempre retorna 0.
    """
    import importlib
    importlib.reload(run_services)
    monkeypatch.setattr(run_services.platform, "system", lambda: "Windows")
    assert run_services.os_get_euid() == 0

import sys

@pytest.mark.skipif(sys.platform != "linux", reason="Solo se ejecuta en Linux")
def test_os_get_euid_linux(monkeypatch):
    """
    Happy Path: Linux, retorna valor de os.geteuid().
    """
    monkeypatch.setattr(run_services.platform, "system", lambda: "Linux")
    monkeypatch.setattr(run_services.os, "geteuid", lambda: 1234)
    assert run_services.os_get_euid() == 1234

@pytest.mark.skipif(sys.platform != "linux", reason="Solo se ejecuta en Linux")
def test_os_get_euid_exception(monkeypatch):
    """
    Edge Case: Excepción, retorna 0.
    """
    monkeypatch.setattr(run_services.platform, "system", lambda: "Linux")
    monkeypatch.setattr(run_services.os, "geteuid", lambda: (_ for _ in ()).throw(Exception("fail")))
    assert run_services.os_get_euid() == 0
