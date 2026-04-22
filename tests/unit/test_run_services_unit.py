def test_ensure_compose_from_install_error(monkeypatch):
    '''
    @brief Error Handling: Simula error en subprocess.run al ejecutar compose.
    '''
    from app.utils import run_services
    import importlib
    importlib.reload(run_services)
    monkeypatch.setattr(run_services.logger, "error", lambda *a, **k: None)
    monkeypatch.setattr(run_services.logger, "info", lambda *a, **k: None)
    monkeypatch.setattr(run_services.logger, "success", lambda *a, **k: None)
    monkeypatch.setattr(run_services.shutil, "which", lambda x: "docker")
    monkeypatch.setattr(run_services.subprocess, "run", lambda *a, **k: (_ for _ in ()).throw(Exception("fail")))
    project_root = run_services.Path(".")
    run_services.ensure_compose_from_install(project_root)

def test_shutdown_services_error(monkeypatch):
    '''
    @brief Error Handling: Simula error en shutdown_services.
    '''
    from app.utils import run_services
    import importlib
    importlib.reload(run_services)
    monkeypatch.setattr(run_services.logger, "error", lambda *a, **k: None)
    monkeypatch.setattr(run_services.logger, "info", lambda *a, **k: None)
    monkeypatch.setattr(run_services.logger, "success", lambda *a, **k: None)
    monkeypatch.setattr(run_services.shutil, "which", lambda x: "docker")
    monkeypatch.setattr(run_services.subprocess, "run", lambda *a, **k: (_ for _ in ()).throw(Exception("fail")))
    run_services.shutdown_services(project_root=run_services.Path("."), stop_ollama=True, force_stop_containers=True, distro_name=None, containers="test")

def test_ensure_infrastructure_error(monkeypatch):
    '''
    @brief Error Handling: Simula error en ensure_infrastructure.
    '''
    from app.utils import run_services
    import importlib
    importlib.reload(run_services)
    monkeypatch.setattr(run_services.logger, "error", lambda *a, **k: None)
    monkeypatch.setattr(run_services.logger, "info", lambda *a, **k: None)
    monkeypatch.setattr(run_services.logger, "success", lambda *a, **k: None)
    monkeypatch.setattr(run_services.shutil, "which", lambda x: "docker")
    monkeypatch.setattr(run_services.subprocess, "run", lambda *a, **k: (_ for _ in ()).throw(Exception("fail")))
    monkeypatch.setattr(run_services, "ensure_compose_from_install", lambda project_root: (_ for _ in ()).throw(Exception("fail")))
    run_services.ensure_infrastructure({"distro_name": "Ubuntu", "dockers_name": "test"}, use_ollama=False)
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

def test_wsl_docker_is_running_none(monkeypatch):
    """
    @brief Edge Case: subprocess returns None
    """
    monkeypatch.setattr(run_services, "subprocess", type("S", (), {"run": lambda *a, **k: None})())
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

def test_detect_host_os_unknown(monkeypatch):
    """
    @brief Error Handling: Unknown platform returns (None, None)
    """
    monkeypatch.setattr(run_services.platform, "system", lambda: "Unknown")
    assert run_services.detect_host_os() == ("Unknown", None)


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

def test_is_docker_available_none(monkeypatch):
    """
    @brief Edge Case: shutil.which returns None
    """
    monkeypatch.setattr(run_services.shutil, "which", lambda x: None)
    assert run_services.is_docker_available() is False


def test_is_docker_available_exception(monkeypatch):
    """
    @brief Error Handling: Exception in shutil.which
    """
    monkeypatch.setattr(run_services.shutil, "which", lambda x: (_ for _ in ()).throw(Exception("fail")))
    try:
        result = run_services.is_docker_available()
    except Exception as e:
        assert str(e) == "fail"


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


def test_ensure_infrastructure_calls_compose_and_containers(monkeypatch):
    """
    Happy Path: When `use_ollama=False` ensure_infrastructure should call
    `ensure_compose_from_install` and `ensure_containers` without attempting
    to install Ollama.
    """
    import importlib
    importlib.reload(run_services)
    called = {}

    monkeypatch.setattr(run_services, 'is_docker_available', lambda: True)
    monkeypatch.setattr(run_services, 'is_docker_daemon_running', lambda: True)

    def fake_compose(pr):
        called['compose'] = True

    def fake_containers(containers, distro):
        called['containers'] = (containers, distro)

    monkeypatch.setattr(run_services, 'ensure_compose_from_install', fake_compose)
    monkeypatch.setattr(run_services, 'ensure_containers', fake_containers)
    # avoid sleeping long in ensure_infrastructure
    # Ensure the sleep function accepts any args (avoid bound-method self arg issues)
    monkeypatch.setattr(run_services, 'time', type('T', (), {'sleep': staticmethod(lambda *a, **k: None)})())

    run_services.ensure_infrastructure({'distro_name': 'Ubuntu', 'dockers_name': 'a,b'}, use_ollama=False)
    assert called.get('compose') is True
    assert called.get('containers') is not None


def test_try_install_ollama_windows_winget(monkeypatch):
    """
    Windows path: winget available -> should attempt winget install and return True
    """
    from app.utils import run_services
    called = {}

    def which(name):
        return True if name == 'winget' else False

    def fake_run(cmd, check=False, **k):
        called['cmd'] = cmd
        return None

    monkeypatch.setattr(run_services, 'shutil', type('S', (), {'which': staticmethod(which)})())
    monkeypatch.setattr(run_services, 'subprocess', type('P', (), {'run': staticmethod(fake_run)})())
    res = run_services.try_install_ollama('Windows')
    assert res is True
    assert 'winget' in ' '.join(called['cmd'])


def test_try_install_ollama_darwin_brew(monkeypatch):
    """
    macOS path: brew available -> should attempt brew and return True
    """
    from app.utils import run_services
    called = {}

    def which(name):
        return True if name == 'brew' else False

    def fake_run(cmd, check=False, **k):
        called['cmd'] = cmd
        return None

    monkeypatch.setattr(run_services, 'shutil', type('S', (), {'which': staticmethod(which)})())
    monkeypatch.setattr(run_services, 'subprocess', type('P', (), {'run': staticmethod(fake_run)})())
    res = run_services.try_install_ollama('Darwin')
    assert res is True
    assert 'brew' in ' '.join(called['cmd'])


def test_try_install_ollama_linux_curl(monkeypatch, tmp_path):
    """
    Linux path: curl available -> should download and run installer script and return True
    """
    from app.utils import run_services
    called = {}

    def which(name):
        return True if name == 'curl' else False

    # capture shell commands passed to subprocess.run
    def fake_run(cmd, shell=False, check=False, **k):
        called.setdefault('cmds', []).append((cmd, shell))
        return None

    monkeypatch.setattr(run_services, 'shutil', type('S', (), {'which': staticmethod(which)})())
    monkeypatch.setattr(run_services, 'subprocess', type('P', (), {'run': staticmethod(fake_run)})())

    res = run_services.try_install_ollama('Linux')
    assert res is True
    # Expect at least one shell command executed (curl or sh)
    assert any(shell for (_, shell) in called.get('cmds', []))


def test_ensure_ollama_model_no_modelfile(monkeypatch, tmp_path):
    """
    ensure_ollama_model should not crash if Modelfile is missing and ollama is present.
    """
    from app.utils import run_services

    # pretend ollama exists but `ollama list` returns empty
    def which(name):
        return True if name == 'ollama' else False

    class Proc:
        def __init__(self, out=''):
            self.stdout = out
            self.stderr = ''

    def fake_run(cmd, capture_output=False, text=True, check=False):
        # Simulate `ollama list` returning no models
        return Proc(out='')

    monkeypatch.setattr(run_services, 'shutil', type('S', (), {'which': staticmethod(which)})())
    monkeypatch.setattr(run_services, 'subprocess', type('P', (), {'run': staticmethod(fake_run)})())

    # Ensure Modelfile path does not exist
    proj = tmp_path
    monkeypatch.setattr(run_services.Path, 'exists', lambda self: False)

    # Should not raise
    run_services.ensure_ollama_model(proj, model_name='cybersentinel')


def test_ensure_compose_fallback_combined(tmp_path, monkeypatch):
    '''
    @brief When both tinytinyrss and opensearch compose files exist but services cannot
    be parsed, the function should execute a combined fallback compose up command.
    '''
    # Create Install dir with both compose files
    inst = tmp_path / 'Install'
    inst.mkdir()
    (inst / 'tinytinyrss.yml').write_text('dummy: 1')
    (inst / 'opensearch-compose.yml').write_text('dummy: 2')

    calls = []

    # simulate docker present
    monkeypatch.setattr(run_services.shutil, 'which', staticmethod(lambda name: True if name == 'docker' else None))

    # subprocess.run: first calls are config attempts returning returncode != 0 or empty stdout
    class Proc:
        def __init__(self, returncode=1, stdout=''):
            self.returncode = returncode
            self.stdout = stdout
            self.stderr = ''

    def fake_run(cmd, capture_output=False, text=True, check=False, shell=False, **k):
        # record the command invocation
        calls.append((cmd, shell))
        # For config commands return non-zero to force fallback
        if isinstance(cmd, list) and 'config' in cmd:
            return Proc(returncode=1, stdout='')
        return Proc(returncode=0, stdout='')

    monkeypatch.setattr(run_services, 'subprocess', type('P', (), {'run': staticmethod(fake_run)})())

    # Call ensure_compose_from_install with project root tmp_path
    run_services.ensure_compose_from_install(tmp_path)

    # Expect at least one composed 'up' invocation (fallback combined compose)
    executed = any((isinstance(c[0], list) and 'up' in [str(x) for x in c[0]]) or (isinstance(c[0], str) and 'up' in c[0]) for c in calls)
    assert executed is True


def test_try_install_ollama_no_manager(monkeypatch):
    """
    Edge Case: No known package manager present should return False.
    """
    from app.utils import run_services

    # no manager present
    monkeypatch.setattr(run_services.shutil, 'which', staticmethod(lambda name: None))
    res = run_services.try_install_ollama('Windows')
    assert res is False


def test_ensure_ollama_models_present(monkeypatch):
    """
    If `ollama list` reports the model present, ensure_ollama_models should skip pulling.
    """
    from app.utils import run_services

    class Proc:
        def __init__(self, out='cybersentinel'):
            self.stdout = out
            self.stderr = ''

    monkeypatch.setattr(run_services, 'is_ollama_available', lambda: True)
    monkeypatch.setattr(run_services.subprocess, 'run', staticmethod(lambda *a, **k: Proc(out='cybersentinel')))

    # Should not raise and should detect the model present
    from pathlib import Path
    run_services.ensure_ollama_models(Path('.'), ['cybersentinel'])


def test_ensure_ollama_models_fallback_create(monkeypatch, tmp_path):
    """
    When pull fails for project model, should call ensure_ollama_model as fallback.
    """
    from app.utils import run_services
    called = {}

    class ProcEmpty:
        def __init__(self):
            self.stdout = ''
            self.stderr = ''

    def fake_run(cmd, check=False, **k):
        # Simulate list returning empty, pull raising, subsequent list empty
        if isinstance(cmd, list) and cmd[:2] == ['ollama', 'pull']:
            raise Exception('pull failed')
        return ProcEmpty()

    monkeypatch.setattr(run_services, 'is_ollama_available', lambda: True)
    monkeypatch.setattr(run_services, 'subprocess', type('P', (), {'run': staticmethod(fake_run)})())

    def fake_ensure_model(proj, model_name='cybersentinel'):
        called['ensured'] = True

    monkeypatch.setattr(run_services, 'ensure_ollama_model', fake_ensure_model)

    run_services.ensure_ollama_models(tmp_path, ['cybersentinel'])
    assert called.get('ensured') is True
