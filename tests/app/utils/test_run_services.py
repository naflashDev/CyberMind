"""
@file test_run_services.py
@author GitHub Copilot
@brief Tests for run_services.py
@details Unit tests for OS, Docker, Ollama, and infra logic. External calls and system dependencies are mocked.
"""
import pytest
from unittest.mock import patch, MagicMock
from src.app.utils import run_services

# --- detect_host_os ---
def test_detect_host_os_returns_tuple():
    os_name, distro = run_services.detect_host_os()
    assert isinstance(os_name, str)

# --- is_docker_available ---
@patch("src.app.utils.run_services.shutil.which", return_value="/usr/bin/docker")
def test_is_docker_available_true(mock_which):
    assert run_services.is_docker_available() is True

@patch("src.app.utils.run_services.shutil.which", return_value=None)
def test_is_docker_available_false(mock_which):
    assert run_services.is_docker_available() is False

# --- is_docker_daemon_running ---
@patch("src.app.utils.run_services.subprocess.run")
def test_is_docker_daemon_running_true(mock_run):
    mock_run.return_value.returncode = 0
    assert run_services.is_docker_daemon_running() is True

@patch("src.app.utils.run_services.subprocess.run")
def test_is_docker_daemon_running_false(mock_run):
    mock_run.return_value.returncode = 1
    assert run_services.is_docker_daemon_running() is False

# --- ensure_docker_daemon_running ---
@patch("src.app.utils.run_services.is_docker_daemon_running", return_value=True)
def test_ensure_docker_daemon_running_true(mock_run):
    assert run_services.ensure_docker_daemon_running("Linux") is True

# --- is_ollama_available ---
@patch("src.app.utils.run_services.shutil.which", return_value="/usr/bin/ollama")
def test_is_ollama_available_true(mock_which):
    assert run_services.is_ollama_available() is True

@patch("src.app.utils.run_services.shutil.which", return_value=None)
def test_is_ollama_available_false(mock_which):
    assert run_services.is_ollama_available() is False

# --- try_install_ollama ---
@patch("src.app.utils.run_services.subprocess.run")
def test_try_install_ollama_success(mock_run):
    mock_run.return_value.returncode = 0
    assert run_services.try_install_ollama("Linux") is True

# --- ensure_ollama_model ---
@patch("src.app.utils.run_services.is_ollama_available", return_value=True)
def test_ensure_ollama_model(mock_ollama):
    from pathlib import Path
    run_services.ensure_ollama_model(Path("."), model_name="cybersentinel")
    assert True

# --- ensure_infrastructure ---
@patch("src.app.utils.run_services.ensure_ollama_model")
@patch("src.app.utils.run_services.ensure_docker_daemon_running", return_value=True)
@patch("src.app.utils.run_services.is_docker_daemon_running", return_value=False)
def test_ensure_infrastructure(mock_is_docker_daemon_running, mock_docker, mock_ollama):
    params = {"docker": True, "dockers_name": "test_container"}
    run_services.ensure_infrastructure(params)
    assert mock_docker.called
    assert mock_ollama.called

# --- shutdown_services ---
@patch("src.app.utils.run_services.subprocess.run")
def test_shutdown_services_runs(mock_run):
    from pathlib import Path
    run_services.shutdown_services(project_root=Path("."), stop_ollama=True, force_stop_containers=True)
    assert mock_run.called
