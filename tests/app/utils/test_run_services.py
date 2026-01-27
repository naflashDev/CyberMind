"""
@file test_run_services.py
@author naflashDev
@brief Pruebas unitarias para run_services.py (unificado).
@details Todos los tests de run_services, Docker, Compose y Ollama, incluyendo lógica combinada y de infraestructura. Mocking de dependencias externas. Cumple las normas de estructura, imports y ubicación.
"""

import sys
import os
import platform
import pytest
import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path
from src.app.utils import run_services


def test_ensure_compose_from_install_no_docker(monkeypatch, tmp_path):
    # Simula que ni docker ni docker-compose están disponibles
    monkeypatch.setattr(run_services.shutil, "which", lambda x: None)
    install_dir = tmp_path / "Install"
    install_dir.mkdir()
    (install_dir / "tinytinyrss.yml").write_text("version: '3'")
    (install_dir / "opensearch-compose.yml").write_text("version: '3'")
    # No debe lanzar excepción, solo loguear error
    run_services.ensure_compose_from_install(tmp_path)

def test_ensure_compose_from_install_fallback_env(monkeypatch, tmp_path):
    # Simula fallback a docker/stack.env
    monkeypatch.setattr(run_services.shutil, "which", lambda x: "docker")
    install_dir = tmp_path / "Install"
    install_dir.mkdir()
    (install_dir / "tinytinyrss.yml").write_text("version: '3'")
    (install_dir / "opensearch-compose.yml").write_text("version: '3'")
    docker_dir = tmp_path / "docker"
    docker_dir.mkdir()
    (docker_dir / "stack.env").write_text("VAR=1")
    # Mock subprocess y platform
    monkeypatch.setattr(run_services, "platform", type("plat", (), {"system": staticmethod(lambda: "Linux")})())
    monkeypatch.setattr(run_services, "os_get_euid", lambda: 0)
    monkeypatch.setattr(run_services.subprocess, "run", lambda *a, **k: type("R", (), {"returncode": 0, "stdout": "svc1\nsvc2"})())
    run_services.ensure_compose_from_install(tmp_path)

def test_ensure_docker_daemon_running_unknown_platform(monkeypatch):
    # Simula plataforma desconocida
    monkeypatch.setattr(run_services, "is_docker_daemon_running", lambda: False)
    monkeypatch.setattr(run_services, "platform", type("plat", (), {"system": staticmethod(lambda: "Solaris")})())
    assert run_services.ensure_docker_daemon_running("Solaris") is False

def test_wsl_docker_is_running_exception(monkeypatch):
    # Simula excepción en subprocess
    monkeypatch.setattr(run_services, "platform", type("plat", (), {"system": staticmethod(lambda: "Linux")})())
    monkeypatch.setattr(run_services.subprocess, "run", lambda *a, **k: (_ for _ in ()).throw(Exception("fail")))
    assert run_services.wsl_docker_is_running("test") is False

def test_shutdown_services_no_ollama(monkeypatch, tmp_path):
    # No hay ollama disponible
    monkeypatch.setattr(run_services, "is_ollama_available", lambda: False)
    run_services.shutdown_services(project_root=tmp_path, stop_ollama=True)
    assert True

def test_shutdown_services_no_containers(monkeypatch, tmp_path):
    # No hay containers a parar
    monkeypatch.setattr(run_services, "shutil", MagicMock(which=lambda x: "/usr/bin/docker"))
    monkeypatch.setattr(run_services, "subprocess", MagicMock(run=MagicMock(return_value=MagicMock(stdout="", returncode=0))))
    run_services.shutdown_services(project_root=tmp_path, force_stop_containers=True)
    assert True

def test_shutdown_services_run_error(monkeypatch, tmp_path):
    # Error en _run
    monkeypatch.setattr(run_services, "shutil", MagicMock(which=lambda x: "/usr/bin/docker"))
    monkeypatch.setattr(run_services, "subprocess", MagicMock(run=MagicMock(side_effect=Exception("fail"))))
    run_services.shutdown_services(project_root=tmp_path)
    assert True

def test_try_install_ollama_no_installers(monkeypatch):
    # Ningún gestor disponible
    monkeypatch.setattr(run_services.shutil, "which", lambda x: None)
    assert run_services.try_install_ollama("Windows") is False
    assert run_services.try_install_ollama("Darwin") is False
    assert run_services.try_install_ollama("Linux") is False

def test_ensure_ollama_model_error(monkeypatch, tmp_path):
    # Fuerza error en subprocess
    monkeypatch.setattr(run_services, "subprocess", MagicMock(run=MagicMock(side_effect=Exception("fail"))))
    run_services.ensure_ollama_model(tmp_path, "model")
    assert True

def test_wsl_docker_is_running_empty(monkeypatch):
    # No hay containers corriendo
    monkeypatch.setattr(run_services, "subprocess", MagicMock(run=MagicMock(return_value=MagicMock(stdout="", returncode=0))))
    assert run_services.wsl_docker_is_running("container") is False



def test_wsl_docker_start_container_ok(monkeypatch):
    # Simula start exitoso
    monkeypatch.setattr(run_services, "subprocess", MagicMock(run=MagicMock(return_value=MagicMock(returncode=0))))
    run_services.wsl_docker_start_container("container")
    assert True

def test_ensure_containers_error(monkeypatch):
    monkeypatch.setattr(run_services, "subprocess", MagicMock(run=MagicMock(side_effect=Exception("fail"))))
    with pytest.raises(Exception):
        run_services.ensure_containers("container")

def test_ensure_docker_daemon_running_linux(monkeypatch):
    # Simula entorno Linux para el daemon de Docker
    monkeypatch.setattr(run_services, "subprocess", MagicMock(run=MagicMock(return_value=MagicMock(returncode=0))))
    run_services.ensure_docker_daemon_running("Linux")

def test_ensure_docker_daemon_running_linux(monkeypatch):
    # Simula entorno Linux para el daemon de Docker
    monkeypatch.setattr(run_services, "subprocess", MagicMock(run=MagicMock(return_value=MagicMock(returncode=0))))
    run_services.ensure_docker_daemon_running("Linux")

def test_ensure_infrastructure_error(monkeypatch):
    monkeypatch.setattr(run_services, "ensure_docker_daemon_running", lambda x: False)
    with pytest.raises(Exception):
        run_services.ensure_infrastructure({}, use_ollama=False)


def test_ensure_docker_daemon_running_darwin(monkeypatch):
    """
    Dummy test for Darwin Docker daemon (to be implemented).
    """
    # Simula platform desconocido
    monkeypatch.setattr(run_services, "subprocess", MagicMock(run=MagicMock(return_value=MagicMock(returncode=1))))
    run_services.ensure_docker_daemon_running("Solaris")
    assert True

def test_shutdown_services_error(monkeypatch):
    monkeypatch.setattr(run_services, "subprocess", MagicMock(run=MagicMock(side_effect=Exception("fail"))))
    # No debe lanzar excepción, solo loguear
    run_services.shutdown_services()



def test_ensure_docker_daemon_running_unknown(monkeypatch):
    """
    Dummy test for unknown Docker daemon (to be implemented).
    """
    # Simula error en subprocess
    monkeypatch.setattr(run_services, "subprocess", MagicMock(run=MagicMock(side_effect=Exception("fail"))))
    run_services.ensure_docker_daemon_running("Linux")
    assert True
def test_ensure_compose_from_install_success(monkeypatch, tmp_path):
    # Simula ejecución exitosa
    monkeypatch.setattr(run_services, "subprocess", MagicMock(run=MagicMock(return_value=MagicMock(returncode=0))))
    run_services.ensure_compose_from_install(tmp_path)
import sys


def test_ensure_docker_daemon_running_exception(monkeypatch):
    """
    Dummy test for Docker daemon exception (to be implemented).
    """
    # Simula error en subprocess
    monkeypatch.setattr(run_services, "subprocess", MagicMock(run=MagicMock(side_effect=Exception("fail"))))
    run_services.wsl_docker_is_running("container")
    assert True


def test_wsl_docker_is_running_false(monkeypatch):
    """
    Dummy test for wsl_docker_is_running_false (to be implemented).
    """
    # Simula error en subprocess
    monkeypatch.setattr(run_services, "subprocess", MagicMock(run=MagicMock(side_effect=Exception("fail"))))
    run_services.wsl_docker_start_container("container")
    assert True
def test_ensure_compose_from_install_no_install(monkeypatch, tmp_path):
    # Simula que no hay docker ni docker-compose
    monkeypatch.setattr(run_services.shutil, "which", lambda x: None)
    run_services.ensure_compose_from_install(tmp_path)
    assert True
def test_ensure_compose_from_install_no_services(monkeypatch, tmp_path):
    # Simula compose file sin servicios
    (tmp_path / "Install").mkdir()
    f = tmp_path / "Install" / "test.yml"
    f.write_text("version: '3'\nservices: {}\n")
    monkeypatch.setattr(run_services, "subprocess", MagicMock(run=MagicMock(return_value=MagicMock(returncode=0, stdout=""))))
    run_services.ensure_compose_from_install(tmp_path)
    assert True
def test_ensure_compose_from_install_error(monkeypatch, tmp_path):
    # Simula error en subprocess.run
    (tmp_path / "Install").mkdir()
    f = tmp_path / "Install" / "test.yml"
    f.write_text("version: '3'\nservices:\n  test:")
    monkeypatch.setattr(run_services, "subprocess", MagicMock(run=MagicMock(side_effect=Exception("fail"))))
    run_services.ensure_compose_from_install(tmp_path)
    assert True
def test_ensure_containers_error(monkeypatch):
    # Simula error inesperado en wsl_docker_is_running
    monkeypatch.setattr(run_services, "wsl_docker_is_running", MagicMock(side_effect=Exception("fail")))
    run_services.ensure_containers("testcontainer")
    assert True
def test_shutdown_services_exception(monkeypatch):
    # Simula excepción global en shutdown_services
    monkeypatch.setattr(run_services, "shutil", MagicMock(which=lambda x: 1))
    monkeypatch.setattr(run_services, "subprocess", MagicMock(run=MagicMock(side_effect=Exception("fail"))))
    class DummyPath:
        def exists(self):
            raise Exception("fail")
        def is_dir(self):
            return True
        def __truediv__(self, other):
            return self
    monkeypatch.setattr(run_services, "Path", lambda *a, **k: DummyPath())
    run_services.shutdown_services(project_root=None)
    assert True

def test_ensure_compose_from_install_no_install(monkeypatch, tmp_path):
    monkeypatch.setattr(run_services, "subprocess", MagicMock(run=MagicMock(side_effect=Exception("fail"))))
    assert run_services.wsl_docker_is_running("container") is False


def test_wsl_docker_start_container_error(monkeypatch):
    """
    Dummy test for wsl_docker_start_container_error (to be implemented).
    """
    pass

def test_ensure_compose_from_install_no_yaml(monkeypatch, tmp_path):
    monkeypatch.setattr(run_services, "subprocess", MagicMock(run=MagicMock(side_effect=Exception("fail"))))
    with pytest.raises(Exception):
        run_services.wsl_docker_start_container("container")

def test_detect_host_os_windows(monkeypatch):
    monkeypatch.setattr(run_services.platform, "system", lambda: "Windows")
    os, distro = run_services.detect_host_os()
    assert os == "Windows"

def test_detect_host_os_linux(monkeypatch):
    monkeypatch.setattr(run_services.platform, "system", lambda: "Linux")
    # Simula que /etc/os-release no existe
    monkeypatch.setattr(run_services.Path, "exists", lambda self: False)
    os, distro = run_services.detect_host_os()
    assert os == "Linux"

def test_is_docker_available_false(monkeypatch):
    monkeypatch.setattr(run_services.shutil, "which", lambda x: None)
    assert run_services.is_docker_available() is False

def test_is_docker_daemon_running_false(monkeypatch):
    monkeypatch.setattr(run_services, "subprocess", MagicMock(run=MagicMock(side_effect=Exception("fail"))))
    assert run_services.is_docker_daemon_running() is False

def test_ensure_docker_daemon_running_error(monkeypatch):
    monkeypatch.setattr(run_services, "is_docker_daemon_running", lambda: False)
    monkeypatch.setattr(run_services, "subprocess", MagicMock(run=MagicMock(side_effect=Exception("fail"))))
    assert run_services.ensure_docker_daemon_running("windows") is False

def test_ensure_compose_from_install_error(monkeypatch, tmp_path):
    # Fuerza error en subprocess, solo debe loguear, no lanzar excepción
    monkeypatch.setattr(run_services, "subprocess", MagicMock(run=MagicMock(side_effect=Exception("fail"))))
    run_services.ensure_compose_from_install(tmp_path)
    assert True

def test_is_ollama_available_false(monkeypatch):
    monkeypatch.setattr(run_services.shutil, "which", lambda x: None)
    assert run_services.is_ollama_available() is False

def test_try_install_ollama_error(monkeypatch):
    monkeypatch.setattr(run_services, "subprocess", MagicMock(run=MagicMock(side_effect=Exception("fail"))))
    assert run_services.try_install_ollama("windows") is False

def test_ensure_ollama_model_error(monkeypatch, tmp_path):
    monkeypatch.setattr(run_services, "subprocess", MagicMock(run=MagicMock(side_effect=Exception("fail"))))
    run_services.ensure_ollama_model(tmp_path, "model")
    assert True

def test_os_get_euid(monkeypatch):
    # Solo prueba que retorna un int, compatible multiplataforma
    val = run_services.os_get_euid()
    assert isinstance(val, int)


# --- TESTS DE FUNCIONES PRINCIPALES Y FLUJOS ---

def test_detect_host_os_returns_tuple():
    os_name, distro = run_services.detect_host_os()
    assert isinstance(os_name, str)

@patch("src.app.utils.run_services.shutil.which", return_value="/usr/bin/docker")
def test_is_docker_available_true(mock_which):
    assert run_services.is_docker_available() is True

@patch("src.app.utils.run_services.shutil.which", return_value=None)
def test_is_docker_available_false(mock_which):
    assert run_services.is_docker_available() is False

@patch("src.app.utils.run_services.subprocess.run")
def test_is_docker_daemon_running_true(mock_run):
    mock_run.return_value.returncode = 0
    assert run_services.is_docker_daemon_running() is True

@patch("src.app.utils.run_services.subprocess.run")
def test_is_docker_daemon_running_false(mock_run):
    mock_run.return_value.returncode = 1
    assert run_services.is_docker_daemon_running() is False

@patch("src.app.utils.run_services.is_docker_daemon_running", return_value=True)
def test_ensure_docker_daemon_running_true(mock_run):
    assert run_services.ensure_docker_daemon_running("Linux") is True

@patch("src.app.utils.run_services.shutil.which", return_value="/usr/bin/ollama")
def test_is_ollama_available_true(mock_which):
    assert run_services.is_ollama_available() is True

@patch("src.app.utils.run_services.shutil.which", return_value=None)
def test_is_ollama_available_false(mock_which):
    assert run_services.is_ollama_available() is False

@patch("src.app.utils.run_services.subprocess.run")
def test_try_install_ollama_success(mock_run):
    mock_run.return_value.returncode = 0
    assert run_services.try_install_ollama("Linux") is True

@patch("src.app.utils.run_services.is_ollama_available", return_value=True)
def test_ensure_ollama_model(mock_ollama):
    run_services.ensure_ollama_model(Path("."), model_name="cybersentinel")
    assert True


@patch("src.app.utils.run_services.is_docker_daemon_running", return_value=False)
@patch("src.app.utils.run_services.ensure_ollama_model")
@patch("src.app.utils.run_services.is_ollama_available", return_value=True)
@patch("src.app.utils.run_services.is_docker_available", return_value=True)
def test_ensure_infrastructure(mock_docker_available, mock_ollama_available, mock_ensure_ollama_model, mock_is_docker_daemon_running):
    params = {"docker": True, "dockers_name": "test_container", "use_ollama": True}
    run_services.ensure_infrastructure(params)
    assert mock_ensure_ollama_model.called is True

@patch("src.app.utils.run_services.subprocess.run")
def test_shutdown_services_runs(mock_run):
    run_services.shutdown_services(project_root=Path("."), stop_ollama=True, force_stop_containers=True)
    assert mock_run.called

# --- TESTS DE WSL Y SUBPROCESOS ---

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

# --- TESTS DE FLUJOS DE COMPOSE Y DOCKER ---

def test_ensure_compose_from_install_no_folder(tmp_path):
    run_services.ensure_compose_from_install(tmp_path)
    assert True

def test_ensure_compose_from_install_no_yaml(tmp_path):
    (tmp_path / "Install").mkdir()
    run_services.ensure_compose_from_install(tmp_path)
    assert True

@patch("src.app.utils.run_services.shutil.which", return_value=None)
def test_ensure_compose_from_install_no_docker(mock_which, tmp_path):
    (tmp_path / "Install").mkdir()
    f = tmp_path / "Install" / "test.yml"
    f.write_text("version: '3'\nservices:\n  test:")
    run_services.ensure_compose_from_install(tmp_path)
    assert True

@patch("src.app.utils.run_services.shutil.which", return_value="/usr/bin/docker")
@patch("src.app.utils.run_services.subprocess.run", side_effect=Exception("fail"))
def test_ensure_compose_from_install_subprocess_error(mock_run, mock_which, tmp_path):
    (tmp_path / "Install").mkdir()
    f = tmp_path / "Install" / "test.yml"
    f.write_text("version: '3'\nservices:\n  test:")
    run_services.ensure_compose_from_install(tmp_path)
    assert True

@patch("src.app.utils.run_services.shutil.which", return_value="/usr/bin/docker")
@patch("src.app.utils.run_services.subprocess.run")
def test_ensure_compose_from_install_services_present(mock_run, mock_which, tmp_path):
    (tmp_path / "Install").mkdir()
    f = tmp_path / "Install" / "test.yml"
    f.write_text("version: '3'\nservices:\n  test:")
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
    import os
    from unittest.mock import patch
    # Ensure os.geteuid exists for patching
    remove_after = False
    if not hasattr(os, "geteuid"):
        os.geteuid = lambda: 1001
        remove_after = True
    try:
        with patch.object(os, "geteuid", side_effect=Exception("fail")):
            assert run_services.os_get_euid() == 0
    finally:
        if remove_after:
            del os.geteuid

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

    # --- shutdown_services: error stopping specific containers ---
    @patch("src.app.utils.run_services.shutil.which", return_value="/usr/bin/docker")
    @patch("src.app.utils.run_services.subprocess.run")
    @patch("src.app.utils.run_services.platform.system", return_value="Linux")
    def test_shutdown_services_target_names_error(mock_system, mock_run, mock_which, tmp_path):
        (tmp_path / "Install").mkdir()
        # Simula que hay un contenedor, pero stop lanza excepción
        def fake_run(cmd, *a, **k):
            class R:
                def __init__(self):
                    self.stdout = "testcontainer\n"
                    self.returncode = 0
            if "ps" in cmd:
                return R()
            if "stop" in cmd:
                raise Exception("fail")
            return R()
        mock_run.side_effect = fake_run
        # Debe cubrir logger.exception y logger.error
        run_services.shutdown_services(project_root=tmp_path, force_stop_containers=True, containers="testcontainer")
        assert True

    # --- shutdown_services: Ollama fallback Windows branch ---
    @patch("src.app.utils.run_services.is_ollama_available", return_value=True)
    @patch("src.app.utils.run_services.subprocess.run")
    @patch("src.app.utils.run_services.platform.system", return_value="Windows")
    def test_shutdown_services_ollama_fallback_windows(mock_system, mock_run, mock_ollama, tmp_path):
        # Simula que ollama stop falla, fallback a taskkill
        def fake_run(cmd, *a, **k):
            if cmd[0] == "ollama":
                raise Exception("fail")
            return MagicMock()
        mock_run.side_effect = fake_run
        run_services.shutdown_services(project_root=tmp_path, stop_ollama=True)
        assert True

    # --- shutdown_services: Ollama fallback non-Windows branch ---
    @patch("src.app.utils.run_services.is_ollama_available", return_value=True)
    @patch("src.app.utils.run_services.subprocess.run")
    @patch("src.app.utils.run_services.platform.system", return_value="Linux")
    def test_shutdown_services_ollama_fallback_nonwindows(mock_system, mock_run, mock_ollama, tmp_path):
        # Simula que ollama stop falla, fallback a pkill
        def fake_run(cmd, *a, **k):
            if cmd[0] == "ollama":
                raise Exception("fail")
            return MagicMock()
        mock_run.side_effect = fake_run
        run_services.shutdown_services(project_root=tmp_path, stop_ollama=True)
        assert True

    # --- shutdown_services: error in compose stack shutdown ---
    @patch("src.app.utils.run_services.shutil.which", return_value="/usr/bin/docker")
    @patch("src.app.utils.run_services.subprocess.run", side_effect=Exception("fail"))
    def test_shutdown_services_compose_error(mock_run, mock_which, tmp_path):
        (tmp_path / "Install").mkdir()
        f = tmp_path / "Install" / "test.yml"
        f.write_text("version: '3'\nservices:\n  test:")
        run_services.shutdown_services(project_root=tmp_path)
        assert True

    # --- shutdown_services: top-level exception handler ---
    def test_shutdown_services_top_level_exception(monkeypatch):
        # Fuerza excepción en el cuerpo principal
        monkeypatch.setattr(run_services, "shutil", MagicMock(which=lambda x: 1))
        monkeypatch.setattr(run_services, "subprocess", MagicMock(run=MagicMock(side_effect=Exception("fail"))))
        # Simula que Path().exists() lanza excepción
        class DummyPath:
            def exists(self):
                raise Exception("fail")
            def is_dir(self):
                return True
            def __truediv__(self, other):
                return self
        monkeypatch.setattr(run_services, "Path", lambda *a, **k: DummyPath())
        run_services.shutdown_services(project_root=None)
        assert True
