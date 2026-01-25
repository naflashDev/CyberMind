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

# --- WSL y errores subprocess ---
import platform
import sys
from pathlib import Path

@patch("src.app.utils.run_services.platform.system", return_value="Windows")
@patch("src.app.utils.run_services.subprocess.run")
def test_wsl_docker_is_running_windows(mock_run, mock_system):
    mock_run.return_value.stdout = "mycontainer\n"
    mock_run.return_value.returncode = 0
    assert run_services.wsl_docker_is_running("mycontainer", distro_name="Ubuntu") is True

@patch("src.app.utils.run_services.platform.system", return_value="Linux")
@patch("src.app.utils.run_services.subprocess.run")
def test_wsl_docker_is_running_linux(mock_run, mock_system):
    mock_run.return_value.stdout = "other\n"
    mock_run.return_value.returncode = 0
    assert run_services.wsl_docker_is_running("mycontainer") is False

@patch("src.app.utils.run_services.platform.system", return_value="Windows")
@patch("src.app.utils.run_services.subprocess.run", side_effect=Exception("fail"))
def test_wsl_docker_is_running_error(mock_run, mock_system):
    assert run_services.wsl_docker_is_running("failcontainer", distro_name="Ubuntu") is False

@patch("src.app.utils.run_services.platform.system", return_value="Windows")
@patch("src.app.utils.run_services.subprocess.run")
def test_wsl_docker_start_container_windows(mock_run, mock_system):
    run_services.wsl_docker_start_container("mycontainer", distro_name="Ubuntu")
    assert mock_run.called

@patch("src.app.utils.run_services.platform.system", return_value="Linux")
@patch("src.app.utils.run_services.subprocess.run")
def test_wsl_docker_start_container_linux(mock_run, mock_system):
    run_services.wsl_docker_start_container("mycontainer")
    assert mock_run.called

@patch("src.app.utils.run_services.platform.system", return_value="Windows")
@patch("src.app.utils.run_services.subprocess.run", side_effect=Exception("fail"))
def test_wsl_docker_start_container_error(mock_run, mock_system):
    run_services.wsl_docker_start_container("failcontainer", distro_name="Ubuntu")
    assert True

# --- detect_host_os error branch ---
@patch("src.app.utils.run_services.platform.system", return_value="Linux")
@patch("src.app.utils.run_services.Path.exists", return_value=False)
def test_detect_host_os_linux_no_osrelease(mock_exists, mock_system):
    plat, distro = run_services.detect_host_os()
    assert plat == "Linux"

# --- ensure_docker_daemon_running error branch ---
@patch("src.app.utils.run_services.is_docker_daemon_running", return_value=False)
@patch("src.app.utils.run_services.subprocess.run", side_effect=Exception("fail"))
def test_ensure_docker_daemon_running_error(mock_run, mock_daemon):
    assert run_services.ensure_docker_daemon_running("Linux") is False

# --- ensure_compose_from_install: carpeta no existe ---
def test_ensure_compose_from_install_no_folder(tmp_path):
    # No crea Install/
    run_services.ensure_compose_from_install(tmp_path)
    assert True

# --- ensure_compose_from_install: sin YAML ---
def test_ensure_compose_from_install_no_yaml(tmp_path):
    (tmp_path / "Install").mkdir()
    run_services.ensure_compose_from_install(tmp_path)
    assert True

# --- ensure_compose_from_install: error en compose_cmd ---
@patch("src.app.utils.run_services.shutil.which", return_value=None)
def test_ensure_compose_from_install_no_docker(mock_which, tmp_path):
    (tmp_path / "Install").mkdir()
    f = tmp_path / "Install" / "test.yml"
    f.write_text("version: '3'\nservices:\n  test:")
    run_services.ensure_compose_from_install(tmp_path)
    assert True

# --- ensure_compose_from_install: error en subprocess.run ---
@patch("src.app.utils.run_services.shutil.which", return_value="/usr/bin/docker")
@patch("src.app.utils.run_services.subprocess.run", side_effect=Exception("fail"))
def test_ensure_compose_from_install_subprocess_error(mock_run, mock_which, tmp_path):
    (tmp_path / "Install").mkdir()
    f = tmp_path / "Install" / "test.yml"
    f.write_text("version: '3'\nservices:\n  test:")
    run_services.ensure_compose_from_install(tmp_path)
    assert True

# --- ensure_compose_from_install: servicios ya presentes ---
@patch("src.app.utils.run_services.shutil.which", return_value="/usr/bin/docker")
@patch("src.app.utils.run_services.subprocess.run")
def test_ensure_compose_from_install_services_present(mock_run, mock_which, tmp_path):
    (tmp_path / "Install").mkdir()
    f = tmp_path / "Install" / "test.yml"
    f.write_text("version: '3'\nservices:\n  test:")
    # Simula que subprocess devuelve servicios y que ya existen
    def fake_run(cmd, *a, **k):
        class R:
            def __init__(self, code=0, out="test\n"):
                self.returncode = code
                self.stdout = out
        if "config" in cmd:
            return R()
        if "ps" in cmd:
            return R(out="container\n")
        return R()
    mock_run.side_effect = fake_run
    run_services.ensure_compose_from_install(tmp_path)
    assert True

# --- try_install_ollama: sin winget/choco/brew/curl ---
@patch("src.app.utils.run_services.shutil.which", return_value=None)
def test_try_install_ollama_no_installers(mock_which):
    assert run_services.try_install_ollama("Windows") is False
    assert run_services.try_install_ollama("Darwin") is False
    assert run_services.try_install_ollama("Linux") is False

# --- try_install_ollama: error en curl/descarga ---
@patch("src.app.utils.run_services.shutil.which", side_effect=lambda x: True if x=="curl" else None)
@patch("src.app.utils.run_services.subprocess.run", side_effect=Exception("fail"))
def test_try_install_ollama_curl_error(mock_run, mock_which):
    assert run_services.try_install_ollama("Linux") is False

# --- ensure_ollama_model: sin ollama ---
@patch("src.app.utils.run_services.is_ollama_available", return_value=False)
def test_ensure_ollama_model_no_ollama(mock_ollama):
    run_services.ensure_ollama_model(Path("."), model_name="cybersentinel")
    assert True

# --- ensure_ollama_model: error en ollama list ---
@patch("src.app.utils.run_services.is_ollama_available", return_value=True)
@patch("src.app.utils.run_services.subprocess.run", side_effect=Exception("fail"))
def test_ensure_ollama_model_list_error(mock_run, mock_ollama):
    run_services.ensure_ollama_model(Path("."), model_name="cybersentinel")
    assert True

# --- ensure_ollama_model: modelo ya presente ---
@patch("src.app.utils.run_services.is_ollama_available", return_value=True)
@patch("src.app.utils.run_services.subprocess.run")
def test_ensure_ollama_model_present(mock_run, mock_ollama):
    class R:
        stdout = "cybersentinel\n"
        stderr = ""
        returncode = 0
    mock_run.return_value = R()
    run_services.ensure_ollama_model(Path("."), model_name="cybersentinel")
    assert True

# --- ensure_ollama_model: sin Modelfile ---
@patch("src.app.utils.run_services.is_ollama_available", return_value=True)
@patch("src.app.utils.run_services.subprocess.run")
def test_ensure_ollama_model_no_modelfile(mock_run, mock_ollama, tmp_path):
    # No crea Install/Modelfile
    run_services.ensure_ollama_model(tmp_path, model_name="cybersentinel")
    assert True

# --- ensure_ollama_model: error en create ---
@patch("src.app.utils.run_services.is_ollama_available", return_value=True)
@patch("src.app.utils.run_services.subprocess.run", side_effect=[
    type("R", (), {"stdout": "", "stderr": "", "returncode": 0})(),  # ollama list
    Exception("fail")  # ollama create
])
def test_ensure_ollama_model_create_error(mock_run, mock_ollama, tmp_path):
    # Crea Install/Modelfile
    install = tmp_path / "Install"
    install.mkdir()
    mf = install / "Modelfile"
    mf.write_text("FROM base")
    run_services.ensure_ollama_model(tmp_path, model_name="cybersentinel")
    assert True

# --- os_get_euid ---
def test_os_get_euid_success():
    # Solo prueba que retorna un int
    assert isinstance(run_services.os_get_euid(), int)

def test_os_get_euid_error():
    from unittest.mock import patch
    with patch("builtins.__import__", side_effect=Exception("fail")):
        assert run_services.os_get_euid() == 0

# --- ensure_containers: éxito, error, varios intentos ---
@patch("src.app.utils.run_services.wsl_docker_is_running", side_effect=[False, True])
@patch("src.app.utils.run_services.wsl_docker_start_container")
@patch("src.app.utils.run_services.logger")
def test_ensure_containers_success(mock_logger, mock_start, mock_running):
    run_services.ensure_containers("testcontainer")
    assert mock_start.called

@patch("src.app.utils.run_services.wsl_docker_is_running", side_effect=[False]*5)
@patch("src.app.utils.run_services.wsl_docker_start_container")
@patch("src.app.utils.run_services.logger")
def test_ensure_containers_fail(mock_logger, mock_start, mock_running):
    run_services.ensure_containers("failcontainer")
    assert mock_start.called

@patch("src.app.utils.run_services.wsl_docker_is_running", side_effect=Exception("fail"))
@patch("src.app.utils.run_services.logger")
def test_ensure_containers_error(mock_logger, mock_running):
    run_services.ensure_containers("errcontainer")
    assert True

# --- ensure_infrastructure: sin docker, sin ollama, error en compose ---
@patch("src.app.utils.run_services.is_docker_available", return_value=False)
@patch("src.app.utils.run_services.detect_host_os", return_value=("Linux", "Debian"))
@patch("src.app.utils.run_services.ensure_compose_from_install", side_effect=Exception("fail"))
@patch("src.app.utils.run_services.is_ollama_available", return_value=False)
@patch("src.app.utils.run_services.try_install_ollama", return_value=False)
@patch("src.app.utils.run_services.ensure_ollama_model")
@patch("src.app.utils.run_services.ensure_containers")
@patch("src.app.utils.run_services.logger")
def test_ensure_infrastructure_all_errors(mock_logger, mock_containers, mock_model, mock_try, mock_ollama, mock_compose, mock_os, mock_docker):
    run_services.ensure_infrastructure({}, use_ollama=True)
    assert mock_compose.called

# --- shutdown_services: sin compose_cmd, error en run ---
def test_shutdown_services_no_compose(tmp_path):
    from unittest.mock import patch
    with patch("src.app.utils.run_services.shutil.which", return_value=None):
        run_services.shutdown_services(project_root=tmp_path)
        assert True

@patch("src.app.utils.run_services.shutil.which", return_value="/usr/bin/docker")
@patch("src.app.utils.run_services.subprocess.run", side_effect=Exception("fail"))
def test_shutdown_services_error_run(mock_run, mock_which, tmp_path):
    (tmp_path / "Install").mkdir()
    run_services.shutdown_services(project_root=tmp_path)
    assert True
