"""
@file run_services.py
@brief Infrastructure helpers: Docker / compose / Ollama checks.
@details This module provides utilities used at application startup to
ensure required infrastructure is available. It contains helpers to detect
and (when reasonable) start Docker/compose services, run compose files from
the project's `Install/` folder, and helper helpers for checking WSL-based
Docker usage. These functions are invoked by the FastAPI startup lifecycle
to verify and attempt to bring up dependent services before the app listens
for incoming requests.
@author naflashDev
"""

import subprocess
import sys
import os
import time
try:
    from loguru import logger
except Exception:
    import logging

    _std_logger = logging.getLogger("app.utils.run_services")
    _std_logger.setLevel(logging.DEBUG)
    if not _std_logger.handlers:
        handler = logging.StreamHandler()
        fmt = logging.Formatter("%(asctime)s | %(levelname)s | %(name)s:%(lineno)d - %(message)s")
        handler.setFormatter(fmt)
        _std_logger.addHandler(handler)

    class _LoggerShim:
        def debug(self, *args, **kwargs):
            _std_logger.debug(*args)

        def info(self, *args, **kwargs):
            _std_logger.info(*args)

        def warning(self, *args, **kwargs):
            _std_logger.warning(*args)

        def error(self, *args, **kwargs):
            _std_logger.error(*args)

        def exception(self, *args, **kwargs):
            _std_logger.exception(*args)

        def success(self, *args, **kwargs):
            _std_logger.info(*args)

    logger = _LoggerShim()
from pathlib import Path
import platform
import shutil
import shlex
import tempfile
from typing import Tuple, Optional

def wsl_docker_is_running(container_name: str, distro_name: Optional[str] = None) -> bool:
    """
    Check if a Docker container is running.

    If `distro_name` is provided on Windows, the check is executed inside that
    WSL distro via `wsl -d <distro> bash -c`. Otherwise the Docker CLI is invoked
    directly on the host (Linux/macOS or native Windows Docker).
    """
    cmd_list = ["docker", "ps", "--filter", f"name={container_name}", "--filter", "status=running", "--format", "{{.Names}}"]
    try:
        plat = platform.system()
        if plat == "Windows" and distro_name:
            # Run inside WSL distro without using a shell; pass args after `--` to wsl
            runner = ["wsl", "-d", distro_name, "--"] + cmd_list
            result = subprocess.run(runner, capture_output=True, text=True, check=False)
            context = f"WSL distro '{distro_name}'"
        else:
            # Run locally
            result = subprocess.run(cmd_list, capture_output=True, text=True, check=False)
            context = "host"

        names = result.stdout.strip().splitlines() if result.stdout else []
        is_running = container_name in names
        logger.info("Container '{}' running in {}: {}", container_name, context, is_running)
        return is_running
    except Exception as e:
        logger.error("Failed to check Docker container '{}': {}", container_name, e)
        return False

def wsl_docker_start_container(container_name: str, distro_name: Optional[str] = None) -> None:
    """
    Start a Docker container. If `distro_name` is provided and running on
    Windows, the start is executed inside that WSL distro; otherwise the Docker
    CLI is invoked on the host.
    """
    try:
        plat = platform.system()
        if plat == "Windows" and distro_name:
            logger.info("Starting Docker container '{}' in WSL distro '{}'...", container_name, distro_name)
            runner = ["wsl", "-d", distro_name, "--", "docker", "start", container_name]
            subprocess.run(runner, check=False)
        else:
            logger.info("Starting Docker container '{}' on host...", container_name)
            subprocess.run(["docker", "start", container_name], check=False)
    except Exception as e:
        logger.error("Error while trying to start container '{}': {}", container_name, e)


def detect_host_os() -> Tuple[str, Optional[str]]:
    """
    Detect the current host OS.

    Returns a tuple: (platform_name, distro_or_version)
    platform_name: 'Windows', 'Darwin' (macOS) or 'Linux'
    distro_or_version: for Linux tries to read /etc/os-release PRETTY_NAME, else None
    """
    plat = platform.system()
    distro = None
    try:
        if plat == "Linux":
            # try to read /etc/os-release for distro identification
            os_release = Path("/etc/os-release")
            if os_release.exists():
                with os_release.open("r", encoding="utf-8") as f:
                    for line in f:
                        if line.startswith("PRETTY_NAME="):
                            distro = line.strip().split("=", 1)[1].strip().strip('"')
                            break
        elif plat == "Darwin":
            distro = platform.mac_ver()[0]
        elif plat == "Windows":
            distro = platform.version()
    except Exception:
        distro = None
    return plat, distro


def is_docker_available() -> bool:
    """Return True if `docker` CLI is present on PATH."""
    return shutil.which("docker") is not None


def is_docker_daemon_running() -> bool:
    """Quick check whether the Docker daemon responds to `docker info`."""
    if not is_docker_available():
        return False
    try:
        result = subprocess.run(["docker", "info"], capture_output=True, text=True, check=False)
        return result.returncode == 0
    except Exception:
        return False


def ensure_docker_daemon_running(host_platform: str) -> bool:
    """
    Attempt to start the Docker daemon depending on the host platform.
    Returns True if the daemon appears running after attempts, False otherwise.
    """
    try:
        if host_platform == "Windows":
            # Try to start Docker Desktop service
            logger.info("Attempting to start Docker service on Windows (sc start com.docker.service)")
            subprocess.run(["sc", "start", "com.docker.service"], check=False)
            time.sleep(3)
            # fallback: try starting Docker Desktop application
            if not is_docker_daemon_running():
                possible_paths = [
                    r"C:\Program Files\Docker\Docker\Docker Desktop.exe",
                    r"C:\Program Files (x86)\Docker\Docker\Docker Desktop.exe",
                ]
                for p in possible_paths:
                    if Path(p).exists():
                        logger.info("Starting Docker Desktop from {}", p)
                        try:
                            subprocess.Popen([p], shell=False)
                        except Exception:
                            logger.exception("Failed to launch Docker Desktop executable: {}", p)
                        break
        elif host_platform == "Linux":
            # Try systemctl then service
            logger.info("Attempting to start Docker daemon via systemctl/service")
            subprocess.run(["sudo", "systemctl", "start", "docker"], check=False)
            time.sleep(2)
            if not is_docker_daemon_running():
                subprocess.run(["sudo", "service", "docker", "start"], check=False)
        elif host_platform == "Darwin":
            # macOS: try to open Docker.app
            logger.info("Attempting to open Docker.app on macOS")
            subprocess.run(["open", "-a", "Docker"], check=False)
        else:
            logger.warning("Automatic Docker start not implemented for platform: {}", host_platform)
    except Exception as e:
        logger.error("Error attempting to start Docker daemon: {}", e)

    # Give it a few seconds to settle
    for _ in range(6):
        if is_docker_daemon_running():
            logger.success("Docker daemon is running.")
            return True
        time.sleep(2)
    return False


def ensure_compose_from_install(project_root: Path) -> None:
    """
    If there are docker-compose / compose v2 files in the `Install/` folder at project root,
    run `docker compose -f <file> up -d` for each file found. If `docker compose` is not
    available but `docker-compose` is, use that.

    Notes:
    - This function assumes the host has Docker installed. If not, it will log an error.
    - On Linux the compose commands may require root privileges (sudo).
    """
    install_dir = project_root / "Install"
    if not install_dir.exists() or not install_dir.is_dir():
        logger.warning("Install folder not found at {}; skipping compose step.", install_dir)
        return

    # Find compose files
    compose_files = list(install_dir.glob("*.yml")) + list(install_dir.glob("*.yaml"))
    if not compose_files:
        logger.warning("No YAML files found in {}; nothing to compose.", install_dir)
        return

    # If both ttrss and opensearch compose files exist, prefer running them together
    tinytinyrss_file = install_dir / "tinytinyrss.yml"
    opensearch_file = install_dir / "opensearch-compose.yml"
    project_root_dir = project_root
    if tinytinyrss_file.exists() and opensearch_file.exists():
        logger.info("Detected TinyTinyRSS and OpenSearch compose files; checking services to decide compose actions.")

        # Determine compose command (prefer `docker compose` v2)
        if shutil.which("docker"):
            base_compose = ["docker", "compose"]
        elif shutil.which("docker-compose"):
            base_compose = ["docker-compose"]
        else:
            logger.error("Neither `docker` nor `docker-compose` found on PATH; cannot run combined compose.")
            base_compose = None

        if base_compose:
            # Determine env file preference: Install/stack.env preferred, fallback to docker/stack.env
            env_file = install_dir / "stack.env"
            if not env_file.exists():
                fallback_env = project_root_dir / "docker" / "stack.env"
                if fallback_env.exists():
                    env_file = fallback_env
                    logger.info("Using fallback env-file: {}", env_file)

            # Helper to get services for a compose file
            def _get_services_for(cf_path):
                try:
                    cfg_cmd = base_compose + ["-f", str(cf_path), "config", "--services"]
                    proc = subprocess.run(cfg_cmd, capture_output=True, text=True, check=False)
                    if proc.returncode == 0 and proc.stdout:
                        return [s.strip() for s in proc.stdout.splitlines() if s.strip()]
                except Exception as e:
                    logger.debug("Could not parse services from {}: {}", cf_path, e)
                return []

            services_tiny = _get_services_for(tinytinyrss_file)
            services_opensearch = _get_services_for(opensearch_file)

            # If we couldn't parse services from one or both files, fall back to combined compose
            if not services_tiny or not services_opensearch:
                logger.warning("Could not parse services from one or both compose files; falling back to combined compose.")
                cmd = base_compose + ["-f", str(tinytinyrss_file), "-f", str(opensearch_file)]
                if env_file.exists():
                    cmd += ["--env-file", str(env_file)]
                cmd += ["up", "-d"]
                if platform.system() == "Linux" and os_get_euid() != 0:
                    cmd = ["sudo"] + cmd
                try:
                    logger.info("Executing fallback combined compose: {}", ' '.join(cmd))
                    subprocess.run(cmd, check=False)
                    logger.success("Fallback combined compose executed successfully.")
                    return
                except Exception as e:
                    logger.error("Failed to execute fallback combined compose command: {}", e)
                    # fall through to continue with other logic

            # Helper to check if any service has an existing container (by compose label)
            def _service_exists(svc_name):
                try:
                    check_cmd = ["docker", "ps", "-a", "--filter", f"label=com.docker.compose.service={svc_name}", "--format", "{{.Names}}"]
                    chk = subprocess.run(check_cmd, capture_output=True, text=True, check=False)
                    return bool(chk.stdout and chk.stdout.strip())
                except Exception:
                    return False

            missing_tiny = [s for s in services_tiny if not _service_exists(s)] if services_tiny else []
            missing_opensearch = [s for s in services_opensearch if not _service_exists(s)] if services_opensearch else []

            # Decide actions based on missing services
            if not missing_tiny and not missing_opensearch:
                logger.info("All TinyTinyRSS and OpenSearch services are present; skipping compose.")
                return

            # If both missing -> run combined compose with env-file (if present)
            if missing_tiny and missing_opensearch:
                cmd = base_compose + ["-f", str(tinytinyrss_file), "-f", str(opensearch_file)]
                if env_file.exists():
                    cmd += ["--env-file", str(env_file)]
                cmd += ["up", "-d"]
                # sudo on Linux if needed
                if platform.system() == "Linux" and os_get_euid() != 0:
                    cmd = ["sudo"] + cmd
                try:
                    logger.info("Bringing up TinyTinyRSS+OpenSearch (combined): {}", ' '.join(cmd))
                    subprocess.run(cmd, check=False)
                    logger.success("Combined compose executed successfully.")
                    return
                except Exception as e:
                    logger.error("Failed to execute combined compose command: {}", e)
                    # fall through to attempt per-file brings

            # If only TinyTinyRSS missing -> bring up tinytinyrss with env-file
            if missing_tiny and not missing_opensearch:
                cmd = base_compose + ["-f", str(tinytinyrss_file)]
                if env_file.exists():
                    cmd += ["--env-file", str(env_file)]
                cmd += ["up", "-d"]
                if platform.system() == "Linux" and os_get_euid() != 0:
                    cmd = ["sudo"] + cmd
                try:
                    logger.info("Bringing up TinyTinyRSS services: {}", ' '.join(cmd))
                    subprocess.run(cmd, check=False)
                    logger.success("TinyTinyRSS compose executed successfully.")
                    return
                except Exception as e:
                    logger.error("Failed to execute TinyTinyRSS compose: {}", e)

            # If only OpenSearch missing -> bring up opensearch compose
            if missing_opensearch and not missing_tiny:
                cmd = base_compose + ["-f", str(opensearch_file), "up", "-d"]
                if platform.system() == "Linux" and os_get_euid() != 0:
                    cmd = ["sudo"] + cmd
                try:
                    logger.info("Bringing up OpenSearch services: {}", ' '.join(cmd))
                    subprocess.run(cmd, check=False)
                    logger.success("OpenSearch compose executed successfully.")
                    return
                except Exception as e:
                    logger.error("Failed to execute OpenSearch compose: {}", e)

    # Determine compose command
    compose_cmd = None
    if shutil.which("docker"):
        # prefer `docker compose` (v2)
        compose_cmd = ["docker", "compose"]
    elif shutil.which("docker-compose"):
        compose_cmd = ["docker-compose"]
    else:
        logger.error("Neither `docker` nor `docker-compose` found on PATH; cannot run compose.")
        return

    for cf in compose_files:
        logger.info("Inspecting compose file: {}", cf)

        # Try to obtain the list of services defined in the compose file
        services = []
        try:
            config_cmd = compose_cmd + ["-f", str(cf), "config", "--services"]
            proc = subprocess.run(config_cmd, capture_output=True, text=True, check=False)
            if proc.returncode == 0 and proc.stdout:
                services = [s.strip() for s in proc.stdout.splitlines() if s.strip()]
                logger.info("Services declared in {}: {}", cf, services)
            else:
                logger.warning("Could not get services from {}; falling back to full compose up.", cf)
                services = []
        except Exception as e:
            logger.error("Error reading services from {}: {}", cf, e)
            services = []

        # If we have a services list, check which ones are missing
        missing_services = []
        if services:
            for svc in services:
                try:
                    # Check for existing containers created by compose (label)
                    check_cmd = ["docker", "ps", "-a", "--filter", f"label=com.docker.compose.service={svc}", "--format", "{{.Names}}"]
                    check_proc = subprocess.run(check_cmd, capture_output=True, text=True, check=False)
                    exists = bool(check_proc.stdout and check_proc.stdout.strip())
                    if not exists:
                        missing_services.append(svc)
                except Exception as e:
                    logger.error("Error while checking existing containers for service '{}': {}", svc, e)
                    missing_services.append(svc)

            if not missing_services:
                logger.info("All services from {} are already present; skipping compose.", cf)
                continue

            # Build up command to bring up only missing services
            up_cmd = compose_cmd + ["-f", str(cf), "up", "-d"] + missing_services
            # on Linux we try with sudo first if not root
            use_sudo = False
            if platform.system() == "Linux" and os_get_euid() != 0:
                use_sudo = True
            if use_sudo:
                up_cmd = ["sudo"] + up_cmd

            try:
                logger.info("Bringing up missing services for {}: {}", cf, missing_services)
                subprocess.run(up_cmd, check=False)
                logger.success("Compose executed for {} (services: {})", cf, missing_services)
            except Exception as e:
                logger.error("Failed to execute compose for {}: {}", cf, e)
        else:
            # Fallback: no services discovered — run full compose up
            logger.info("No services parsed for {}; running full compose up", cf)
            cmd = compose_cmd + ["-f", str(cf), "up", "-d"]
            try:
                subprocess.run(cmd, check=False)
                logger.success("Compose executed for {}", cf)
            except Exception as e:
                logger.error("Failed to execute compose for {}: {}", cf, e)


def is_ollama_available() -> bool:
    """Return True if the `ollama` CLI is available on PATH."""
    return shutil.which("ollama") is not None


def try_install_ollama(host_platform: str) -> bool:
    """
    Attempt to install Ollama depending on platform using common package managers.
    Returns True if an installation attempt was executed (success not guaranteed).
    """
    logger.info("Attempting to install Ollama on platform: {}", host_platform)
    try:
        # Windows: prefer winget, fallback to choco
        if host_platform == "Windows":
            if shutil.which("winget"):
                cmd = ["winget", "install", "-e", "--id", "Ollama.Ollama"]
                logger.info("Running: {}", ' '.join(cmd))
                subprocess.run(cmd, check=False)
                return True
            if shutil.which("choco"):
                cmd = ["choco", "install", "ollama", "-y"]
                logger.info("Running: {}", ' '.join(cmd))
                subprocess.run(cmd, check=False)
                return True
            logger.warning("No winget/choco found on PATH; cannot auto-install Ollama on Windows.")
            return False

        # macOS: try brew
        if host_platform == "Darwin":
            if shutil.which("brew"):
                cmd = ["brew", "install", "ollama"]
                logger.info("Running: {}", ' '.join(cmd))
                subprocess.run(cmd, check=False)
                return True
            logger.warning("Homebrew not found on macOS; cannot auto-install Ollama.")
            return False

        # Linux: try curl installer (if curl present)
        if host_platform == "Linux":
            if shutil.which("curl"):
                # Safer approach: download the installer script to a temp file and execute it
                try:
                    tf_fd, tf_path = tempfile.mkstemp(suffix=".sh")
                    os.close(tf_fd)
                    # Use a shell command string so callers that expect shell=True
                    # (tests/mocking) observe the correct behavior.
                    curl_cmd = f"curl -sSL https://ollama.ai/install -o {shlex.quote(tf_path)}"
                    logger.info("Attempting to download Ollama installer script via curl to temporary file")
                    subprocess.run(curl_cmd, shell=True, check=False)
                    logger.info("Executing Ollama installer script from {}", tf_path)
                    subprocess.run(f"sh {shlex.quote(tf_path)}", shell=True, check=False)
                    try:
                        os.remove(tf_path)
                    except Exception:
                        pass
                    return True
                except Exception as e:
                    logger.error("Failed to run Ollama installer via temp script: {}", e)
                    try:
                        if os.path.exists(tf_path):
                            os.remove(tf_path)
                    except Exception:
                        pass
                    return False
            logger.warning("curl not found on Linux; cannot auto-install Ollama.")
            return False

    except Exception as e:
        logger.error("Error while attempting to install Ollama: {}", e)
    return False


def ensure_ollama_model(project_root: Path, model_name: str = "cybersentinel") -> None:
    """
    Ensure the named Ollama model is present. If not, create it using the Modelfile
    inside the project's `Install/Modelfile` (path: <project_root>/Install/Modelfile).
    """
    try:
        if not is_ollama_available():
            logger.warning("Cannot ensure Ollama model because `ollama` CLI is not available.")
            return

        # Check existing models
        try:
            proc = subprocess.run(["ollama", "list"], capture_output=True, text=True, check=False)
            out = proc.stdout or proc.stderr or ""
        except Exception as e:
            logger.error("Failed to run `ollama list`: {}", e)
            out = ""

        if model_name in out:
            logger.info("Ollama model '{}' already present.", model_name)
            return

        # Model missing: look for Modelfile
        modelfile = project_root / "Install" / "Modelfile"
        if not modelfile.exists():
            logger.error("Modelfile not found at {}; cannot create Ollama model '{}'", modelfile, model_name)
            return

        cmd = ["ollama", "create", model_name, "-f", str(modelfile)]
        logger.info("Creating Ollama model '{}' using Modelfile: {}", model_name, ' '.join(cmd))
        subprocess.run(cmd, check=False)
        logger.success("Ollama model '{}' create command executed.", model_name)
    except Exception as e:
        logger.error("Error ensuring Ollama model: {}", e)


def os_get_euid() -> int:
    """Return effective uid on POSIX, or 0 on non-POSIX systems."""
    try:
        return getattr(__import__('os'), 'geteuid')()
    except Exception:
        return 0


def ensure_containers(CONTAINERES: str, distro_name: Optional[str] = None):
    """
    Ensure the Docker container that hosts DB + Tiny RSS is running.

    If running on Windows and `distro_name` is provided, the checks/starts will be
    executed inside that WSL distro. Otherwise they run on the host.
    """
    for name in CONTAINERES.split(','):
        try:
            if wsl_docker_is_running(name, distro_name):
                logger.info(f"Container '{name}' already running.")
                continue
            exit_loop = False
            attempts = 0
            while not exit_loop and attempts < 5:
                attempts += 1
                wsl_docker_start_container(name, distro_name)
                time.sleep(1)
                if wsl_docker_is_running(name, distro_name):
                    logger.success(f"Container '{name}' started successfully.")
                    exit_loop = True
                else:
                    logger.warning(
                        f"Container '{name}' is not running and could not be started (attempt {attempts})."
                    )
            if not exit_loop:
                logger.error(f"Container '{name}' could not be started after {attempts} attempts.")
        except Exception as e:
            logger.error(f"Unexpected error ensuring container '{name}': {e}")

def ensure_infrastructure(parameters, use_ollama=True):
    '''
    @brief Ensures all required infrastructure services are running.

    This function checks and starts Docker containers, OpenSearch, Dashboards, and Tiny RSS stack. Optionally installs and initializes Ollama if requested and hardware requirements are met.

    @param parameters Tuple with infrastructure configuration parameters.
    @param use_ollama Boolean flag to control Ollama installation/initialization.
    @return None.
    '''
    
    # Ensure docker daemon is running on host before interacting with containers
    host_os, distro = detect_host_os()
    logger.info("Host OS detected: {} (distro: {})", host_os, distro)
    # derive project root (repo root) so Install/ can be located
    project_root = Path(__file__).resolve().parents[3]
    # Decide whether to operate against the host Docker or inside WSL
    distro_arg = None
    dockers_arg = None
    if isinstance(parameters, dict):
        distro_arg = parameters.get('distro_name')
        dockers_arg = parameters.get('dockers_name')
    elif isinstance(parameters, (list, tuple)):
        if len(parameters) > 0:
            distro_arg = parameters[0]
        if len(parameters) > 1:
            dockers_arg = parameters[1]

    if is_docker_available():
        logger.info("Docker CLI available on host: using host Docker (distro_name=None)")
        # Ensure daemon running
        if not is_docker_daemon_running():
            logger.warning("Docker daemon does not appear to be running on host. Attempting to start it...")
            started = ensure_docker_daemon_running(host_os)
            if not started:
                logger.error("Could not start Docker daemon automatically. Please start it manually.")
    else:
        logger.warning("Docker CLI not found on host PATH. Will attempt to compose Install/ files or use WSL distro if provided.")
        # If we are on Windows prefer to use provided WSL distro name; otherwise fall back to parameter
        if host_os == 'Windows':
            pass # distro_arg ya extraído

    # Regardless of docker CLI presence, attempt to run compose files from Install/ (if present).
    try:
        ensure_compose_from_install(project_root)
    except Exception as e:
        logger.error("Failed to run docker compose from Install/: {}", e)

    # Solo instalar/inicializar Ollama si use_ollama es True
    if use_ollama:
        try:
            # attempt to detect/install ollama if missing
            if not is_ollama_available():
                logger.warning("Ollama CLI not found on PATH. Attempting automatic installation...")
                installed_attempt = try_install_ollama(host_os)
                if installed_attempt and is_ollama_available():
                    logger.success("Ollama installed and available on PATH.")
                else:
                    logger.warning("Ollama not available after automatic installation attempts. Please install Ollama manually if you require model features.")
            else:
                logger.info("Ollama CLI detected on PATH.")

            # ensure the model exists (create from Modelfile if missing)
            if is_ollama_available():
                ensure_ollama_model(project_root, model_name="cybersentinel")
        except Exception as e:
            logger.error(f"Error while ensuring Ollama/model: {e}")
    else:
        logger.info("Ollama no será instalado ni inicializado por configuración (use_ollama=False).")

    logger.info("Ensuring infrastructure (OpenSearch, Dashboards, Tiny stack)...")
    # pass distro_arg (None for host Docker) and the container list
    ensure_containers(dockers_arg, distro_arg)
    logger.info("Infrastructure check finished.")
    '''
    logger.info("Starting UI service in a separate console...")
    start_ui_in_separate_terminal()
    logger.info("UI service launch command executed.")
    '''
    time.sleep(1)  # give some time for services to start


def shutdown_services(project_root: Optional[Path] = None, stop_ollama: bool = True, force_stop_containers: bool = False, distro_name: Optional[str] = None, containers: Optional[str] = None) -> None:
    '''
    @brief Gracefully shuts down all infrastructure services started by the application.

    This function brings down Docker compose stacks, stops containers, and terminates Ollama processes if requested. It supports both host and WSL environments.

    @param project_root Optional path to the repository root.
    @param stop_ollama Boolean flag to stop Ollama processes.
    @param force_stop_containers Boolean flag to stop all running containers.
    @param distro_name Optional WSL distro name for Windows.
    @param containers Optional string with container names to stop.
    @return None.
    '''
    try:
        install_dir = project_root / "Install" if project_root else Path(__file__).resolve().parents[3] / "Install"

        def _run(cmd, capture_output=False, text=True):
            if platform.system() == "Windows" and distro_name:
                if isinstance(cmd, list):
                    runner = ["wsl", "-d", distro_name, "--"] + cmd
                else:
                    runner = ["wsl", "-d", distro_name, "--"] + shlex.split(cmd)
                return subprocess.run(runner, capture_output=capture_output, text=text, check=False)
            else:
                if isinstance(cmd, list):
                    return subprocess.run(cmd, capture_output=capture_output, text=text, check=False)
                else:
                    return subprocess.run(shlex.split(cmd), capture_output=capture_output, text=text, check=False)

        compose_cmd = None
        if shutil.which("docker"):
            compose_cmd = ["docker", "compose"]
        elif shutil.which("docker-compose"):
            compose_cmd = ["docker-compose"]

        if install_dir.exists() and install_dir.is_dir() and compose_cmd:
            yaml_files = list(install_dir.glob("*.yml")) + list(install_dir.glob("*.yaml"))
            for cf in yaml_files:
                cmd = compose_cmd + ["-f", str(cf), "down", "-v"]
                try:
                    logger.info("Shutting down compose stack defined in {}: {}", cf, ' '.join(cmd))
                    _run(cmd)
                    logger.success("Compose stack {} brought down.", cf)
                except Exception as exc:
                    logger.error("Failed to bring down compose file {}: {}", cf, exc)

        if force_stop_containers and shutil.which("docker"):
            target_names = None
            if containers and isinstance(containers, str):
                target_names = [c.strip() for c in containers.split(',') if c.strip()]

            if not target_names:
                if platform.system() == "Windows" and distro_name:
                    proc = subprocess.run(["wsl", "-d", distro_name, "--", "docker", "ps", "-q"], capture_output=True, text=True, check=False)
                else:
                    proc = subprocess.run(["docker", "ps", "-q"], capture_output=True, text=True, check=False)
                ids = [s.strip() for s in (proc.stdout or "").splitlines() if s.strip()]
                if ids:
                    logger.info("Stopping {} running Docker containers...", len(ids))
                    for cid in ids:
                        try:
                            _run(["docker", "stop", cid])
                        except Exception:
                            logger.exception("Failed to stop container {}", cid)
                    logger.success("Requested stop for all running containers.")
                else:
                    logger.info("No running Docker containers to stop.")
            else:
                stopped = 0
                for name in target_names:
                    try:
                        if platform.system() == "Windows" and distro_name:
                            ps_proc = subprocess.run(["wsl", "-d", distro_name, "--", "docker", "ps", "-q", "--filter", f"name={name}"], capture_output=True, text=True, check=False)
                        else:
                            ps_proc = subprocess.run(["docker", "ps", "-q", "--filter", f"name={name}"], capture_output=True, text=True, check=False)
                        out = ps_proc.stdout or ''
                        ids = [s.strip() for s in out.splitlines() if s.strip()]
                        if not ids:
                            logger.info("No running containers found matching '{}' to stop.", name)
                            continue
                        for cid in ids:
                            try:
                                _run(["docker", "stop", cid])
                                stopped += 1
                            except Exception:
                                logger.exception("Failed to stop container {} (target '{}')", cid, name)
                    except Exception as exc:
                        logger.error("Error while attempting to stop target container '{}': {}", name, exc)
                if stopped:
                    logger.success("Requested stop for {} target container(s).", stopped)
                else:
                    logger.info("No target containers were stopped.")

        if stop_ollama:
            if is_ollama_available():
                try:
                    res = subprocess.run(["ollama", "stop"], capture_output=True, text=True, check=False)
                    logger.info("Ollama stop output: {}", (res.stdout or '').strip())
                    logger.success("Ollama stop command executed (if supported).")
                except Exception as exc:
                    logger.warning("`ollama stop` failed: {}; trying process kill fallback", exc)
                    try:
                        if platform.system() == "Windows" and (distro_name is None or not distro_name):
                            subprocess.run(["taskkill", "/F", "/IM", "ollama.exe"], check=False)
                        else:
                            subprocess.run(["pkill", "-f", "ollama"], check=False)
                        logger.success("Ollama processes signalled for termination.")
                    except Exception as exc2:
                        logger.error("Failed to kill Ollama processes: {}", exc2)
            else:
                logger.info("Ollama CLI not present; skipping Ollama shutdown.")

        logger.info("Shutdown requests issued for infrastructure.")
    except Exception as e:
        logger.error("Error during shutdown_services: {}", e)
