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
@date Created: 2025-11-27 12:17:59
@author naflashDev
@project CyberMind
"""

import subprocess
import sys
import os
import time
from loguru import logger
from pathlib import Path
import platform
import shutil
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
            # Run inside WSL distro
            cmd = ' '.join(cmd_list)
            runner = ["wsl", "-d", distro_name, "bash", "-c", cmd]
            result = subprocess.run(runner, capture_output=True, text=True, check=False)
            context = f"WSL distro '{distro_name}'"
        else:
            # Run locally
            result = subprocess.run(cmd_list, capture_output=True, text=True, check=False)
            context = "host"

        names = result.stdout.strip().splitlines() if result.stdout else []
        is_running = container_name in names
        logger.info(f"Container '{container_name}' running in {context}: {is_running}")
        return is_running
    except Exception as e:
        logger.error(f"Failed to check Docker container '{container_name}': {e}")
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
            logger.info(f"Starting Docker container '{container_name}' in WSL distro '{distro_name}'...")
            cmd = f"docker start {container_name}"
            subprocess.run(["wsl", "-d", distro_name, "bash", "-c", cmd], check=False)
        else:
            logger.info(f"Starting Docker container '{container_name}' on host...")
            subprocess.run(["docker", "start", container_name], check=False)
    except Exception as e:
        logger.error(f"Error while trying to start container '{container_name}': {e}")


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
                        logger.info(f"Starting Docker Desktop from {p}")
                        subprocess.Popen([p], shell=False)
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
            logger.warning(f"Automatic Docker start not implemented for platform: {host_platform}")
    except Exception as e:
        logger.error(f"Error attempting to start Docker daemon: {e}")

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
        logger.warning(f"Install folder not found at {install_dir}; skipping compose step.")
        return

    # Find compose files
    compose_files = list(install_dir.glob("*.yml")) + list(install_dir.glob("*.yaml"))
    if not compose_files:
        logger.warning(f"No YAML files found in {install_dir}; nothing to compose.")
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
                    logger.info(f"Using fallback env-file: {env_file}")

            # Helper to get services for a compose file
            def _get_services_for(cf_path):
                try:
                    cfg_cmd = base_compose + ["-f", str(cf_path), "config", "--services"]
                    proc = subprocess.run(cfg_cmd, capture_output=True, text=True, check=False)
                    if proc.returncode == 0 and proc.stdout:
                        return [s.strip() for s in proc.stdout.splitlines() if s.strip()]
                except Exception as e:
                    logger.debug(f"Could not parse services from {cf_path}: {e}")
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
                    logger.info(f"Executing fallback combined compose: {' '.join(cmd)}")
                    subprocess.run(cmd, check=False)
                    logger.success("Fallback combined compose executed successfully.")
                    return
                except Exception as e:
                    logger.error(f"Failed to execute fallback combined compose command: {e}")
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
                    logger.info(f"Bringing up TinyTinyRSS+OpenSearch (combined): {' '.join(cmd)}")
                    subprocess.run(cmd, check=False)
                    logger.success("Combined compose executed successfully.")
                    return
                except Exception as e:
                    logger.error(f"Failed to execute combined compose command: {e}")
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
                    logger.info(f"Bringing up TinyTinyRSS services: {' '.join(cmd)}")
                    subprocess.run(cmd, check=False)
                    logger.success("TinyTinyRSS compose executed successfully.")
                    return
                except Exception as e:
                    logger.error(f"Failed to execute TinyTinyRSS compose: {e}")

            # If only OpenSearch missing -> bring up opensearch compose
            if missing_opensearch and not missing_tiny:
                cmd = base_compose + ["-f", str(opensearch_file), "up", "-d"]
                if platform.system() == "Linux" and os_get_euid() != 0:
                    cmd = ["sudo"] + cmd
                try:
                    logger.info(f"Bringing up OpenSearch services: {' '.join(cmd)}")
                    subprocess.run(cmd, check=False)
                    logger.success("OpenSearch compose executed successfully.")
                    return
                except Exception as e:
                    logger.error(f"Failed to execute OpenSearch compose: {e}")

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
        logger.info(f"Inspecting compose file: {cf}")

        # Try to obtain the list of services defined in the compose file
        services = []
        try:
            config_cmd = compose_cmd + ["-f", str(cf), "config", "--services"]
            proc = subprocess.run(config_cmd, capture_output=True, text=True, check=False)
            if proc.returncode == 0 and proc.stdout:
                services = [s.strip() for s in proc.stdout.splitlines() if s.strip()]
                logger.info(f"Services declared in {cf}: {services}")
            else:
                logger.warning(f"Could not get services from {cf}; falling back to full compose up.")
                services = []
        except Exception as e:
            logger.error(f"Error reading services from {cf}: {e}")
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
                    logger.error(f"Error while checking existing containers for service '{svc}': {e}")
                    missing_services.append(svc)

            if not missing_services:
                logger.info(f"All services from {cf} are already present; skipping compose.")
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
                logger.info(f"Bringing up missing services for {cf}: {missing_services}")
                subprocess.run(up_cmd, check=False)
                logger.success(f"Compose executed for {cf} (services: {missing_services})")
            except Exception as e:
                logger.error(f"Failed to execute compose for {cf}: {e}")
        else:
            # Fallback: no services discovered — run full compose up
            logger.info(f"No services parsed for {cf}; running full compose up")
            cmd = compose_cmd + ["-f", str(cf), "up", "-d"]
            try:
                subprocess.run(cmd, check=False)
                logger.success(f"Compose executed for {cf}")
            except Exception as e:
                logger.error(f"Failed to execute compose for {cf}: {e}")


def is_ollama_available() -> bool:
    """Return True if the `ollama` CLI is available on PATH."""
    return shutil.which("ollama") is not None


def try_install_ollama(host_platform: str) -> bool:
    """
    Attempt to install Ollama depending on platform using common package managers.
    Returns True if an installation attempt was executed (success not guaranteed).
    """
    logger.info(f"Attempting to install Ollama on platform: {host_platform}")
    try:
        # Windows: prefer winget, fallback to choco
        if host_platform == "Windows":
            if shutil.which("winget"):
                cmd = ["winget", "install", "-e", "--id", "Ollama.Ollama"]
                logger.info(f"Running: {' '.join(cmd)}")
                subprocess.run(cmd, check=False)
                return True
            if shutil.which("choco"):
                cmd = ["choco", "install", "ollama", "-y"]
                logger.info(f"Running: {' '.join(cmd)}")
                subprocess.run(cmd, check=False)
                return True
            logger.warning("No winget/choco found on PATH; cannot auto-install Ollama on Windows.")
            return False

        # macOS: try brew
        if host_platform == "Darwin":
            if shutil.which("brew"):
                cmd = ["brew", "install", "ollama"]
                logger.info(f"Running: {' '.join(cmd)}")
                subprocess.run(cmd, check=False)
                return True
            logger.warning("Homebrew not found on macOS; cannot auto-install Ollama.")
            return False

        # Linux: try curl installer (if curl present)
        if host_platform == "Linux":
            if shutil.which("curl"):
                # This runs the official Ollama installer script if present.
                cmd = "bash -c \"curl -sSL https://ollama.ai/install | sh\""
                logger.info("Attempting to run Ollama installer script via curl")
                subprocess.run(cmd, shell=True, check=False)
                return True
            logger.warning("curl not found on Linux; cannot auto-install Ollama.")
            return False

    except Exception as e:
        logger.error(f"Error while attempting to install Ollama: {e}")
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
            logger.error(f"Failed to run `ollama list`: {e}")
            out = ""

        if model_name in out:
            logger.info(f"Ollama model '{model_name}' already present.")
            return

        # Model missing: look for Modelfile
        modelfile = project_root / "Install" / "Modelfile"
        if not modelfile.exists():
            logger.error(f"Modelfile not found at {modelfile}; cannot create Ollama model '{model_name}'.")
            return

        cmd = ["ollama", "create", model_name, "-f", str(modelfile)]
        logger.info(f"Creating Ollama model '{model_name}' using Modelfile: {' '.join(cmd)}")
        subprocess.run(cmd, check=False)
        logger.success(f"Ollama model '{model_name}' create command executed.")
    except Exception as e:
        logger.error(f"Error ensuring Ollama model: {e}")


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

def ensure_infrastructure(parameters):
    """
    Ensure all infrastructure services are up in WSL:
    - OpenSearch (via .sh)
    - OpenSearch Dashboards (via .sh)
    - Docker container with DB + Tiny RSS (via docker start)
    """
    
    # Ensure docker daemon is running on host before interacting with containers
    host_os, distro = detect_host_os()
    logger.info(f"Host OS detected: {host_os} (distro: {distro})")
    # derive project root (repo root) so Install/ can be located
    project_root = Path(__file__).resolve().parents[3]
    # Decide whether to operate against the host Docker or inside WSL
    if is_docker_available():
        logger.info("Docker CLI available on host: using host Docker (distro_name=None)")
        distro_arg = None
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
            distro_arg = parameters[0] if parameters and len(parameters) > 0 else None
        else:
            distro_arg = parameters[0] if parameters and len(parameters) > 0 else None

    # Regardless of docker CLI presence, attempt to run compose files from Install/ (if present).
    try:
        ensure_compose_from_install(project_root)
    except Exception as e:
        logger.error(f"Failed to run docker compose from Install/: {e}")

    # Ensure Ollama and model presence
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

    logger.info("Ensuring infrastructure (OpenSearch, Dashboards, Tiny stack)...")
    # pass distro_arg (None for host Docker) and the container list
    ensure_containers(parameters[1], distro_arg)
    logger.info("Infrastructure check finished.")
    '''
    logger.info("Starting UI service in a separate console...")
    start_ui_in_separate_terminal()
    logger.info("UI service launch command executed.")
    '''
    time.sleep(15)  # give some time for services to start


def shutdown_services(project_root: Optional[Path] = None, stop_ollama: bool = True, force_stop_containers: bool = False, distro_name: Optional[str] = None, containers: Optional[str] = None) -> None:
    """
    Gracefully shut down infrastructure started by the application.

    - Brings down compose files located in <project_root>/Install (if present).
    - If `force_stop_containers` is True attempts to stop all running Docker
      containers on the host (use with caution).
    - Attempts to stop the Ollama daemon via the CLI (`ollama stop`) when
      available; falls back to platform-specific process termination.

    Args:
        project_root: Repository root path. If None it is inferred from this file.
        stop_ollama: Whether to attempt to stop Ollama processes.
        force_stop_containers: If True, stop all running containers.
        distro_name: Optional WSL distro to target on Windows.
    """
    try:
        if project_root is None:
            project_root = Path(__file__).resolve().parents[3]

        install_dir = project_root / "Install"

        # Helper to run commands either on host or inside WSL distro when requested
        def _run(cmd, shell=False):
            """Run a command list or shell string; if running on Windows and
            `distro_name` is provided, execute inside that WSL distro."""
            try:
                if platform.system() == "Windows" and distro_name:
                    # Always use a shell invocation inside WSL to preserve quoting
                    if isinstance(cmd, list):
                        cmdstr = ' '.join(map(str, cmd))
                    else:
                        cmdstr = cmd
                    runner = ["wsl", "-d", distro_name, "bash", "-c", cmdstr]
                    return subprocess.run(runner, capture_output=False, text=True, check=False)
                else:
                    if isinstance(cmd, list):
                        return subprocess.run(cmd, check=False)
                    else:
                        return subprocess.run(cmd, shell=True, check=False)
            except Exception as e:
                logger.error(f"Command execution failed ({cmd}): {e}")
                raise

        # Determine compose command availability (host-side check)
        compose_cmd = None
        if shutil.which("docker"):
            compose_cmd = ["docker", "compose"]
        elif shutil.which("docker-compose"):
            compose_cmd = ["docker-compose"]

        # Bring down compose stacks found in Install/
        if install_dir.exists() and install_dir.is_dir() and compose_cmd:
            yaml_files = list(install_dir.glob("*.yml")) + list(install_dir.glob("*.yaml"))
            for cf in yaml_files:
                # Build host command, but _run will route to WSL if requested
                cmd = compose_cmd + ["-f", str(cf), "down", "-v"]
                try:
                    logger.info(f"Shutting down compose stack defined in {cf}: {' '.join(cmd)}")
                    _run(cmd)
                    logger.success(f"Compose stack {cf} brought down.")
                except Exception as e:
                    logger.error(f"Failed to bring down compose file {cf}: {e}")

        # Optionally stop containers (dangerous - explicit). If `containers` is provided
        # it should be a comma-separated string or single name; only those containers
        # will be targeted. If `containers` is None and force_stop_containers is True,
        # the previous behavior (stop all containers) is preserved.
        if force_stop_containers and shutil.which("docker"):
            try:
                target_names = None
                if containers:
                    # accept comma-separated string or single name
                    if isinstance(containers, str):
                        target_names = [c.strip() for c in containers.split(',') if c.strip()]
                # If no explicit targets, fall back to stopping all containers (existing behavior)
                if not target_names:
                    proc = _run(["docker", "ps", "-q"]) if not (platform.system() == "Windows" and distro_name) else _run("docker ps -q", shell=True)
                    stdout = ''
                    if hasattr(proc, 'stdout') and proc.stdout:
                        stdout = proc.stdout
                    elif hasattr(proc, 'returncode'):
                        # When _run invoked wsl runner without capture_output, re-run with capture
                        try:
                            if platform.system() == "Windows" and distro_name:
                                proc = subprocess.run(["wsl", "-d", distro_name, "bash", "-c", "docker ps -q"], capture_output=True, text=True, check=False)
                                stdout = proc.stdout or ''
                        except Exception:
                            stdout = ''
                    ids = [s.strip() for s in (stdout or "").splitlines() if s.strip()]
                    if ids:
                        logger.info(f"Stopping {len(ids)} running Docker containers...")
                        for cid in ids:
                            try:
                                _run(["docker", "stop", cid])
                            except Exception:
                                logger.exception(f"Failed to stop container {cid}")
                        logger.success("Requested stop for all running containers.")
                    else:
                        logger.info("No running Docker containers to stop.")
                else:
                    # Stop only the containers listed in target_names
                    stopped = 0
                    for name in target_names:
                        try:
                            # Query running container ids that match the provided name
                            if platform.system() == "Windows" and distro_name:
                                ps_proc = subprocess.run(["wsl", "-d", distro_name, "bash", "-c", f"docker ps -q --filter \"name={name}\""], capture_output=True, text=True, check=False)
                                out = ps_proc.stdout or ''
                            else:
                                ps_proc = subprocess.run(["docker", "ps", "-q", "--filter", f"name={name}"], capture_output=True, text=True, check=False)
                                out = ps_proc.stdout or ''
                            ids = [s.strip() for s in out.splitlines() if s.strip()]
                            if not ids:
                                logger.info(f"No running containers found matching '{name}' to stop.")
                                continue
                            for cid in ids:
                                try:
                                    _run(["docker", "stop", cid])
                                    stopped += 1
                                except Exception:
                                    logger.exception(f"Failed to stop container {cid} (target '{name}')")
                        except Exception as e:
                            logger.error(f"Error while attempting to stop target container '{name}': {e}")
                    if stopped:
                        logger.success(f"Requested stop for {stopped} target container(s).")
                    else:
                        logger.info("No target containers were stopped.")
            except Exception as e:
                logger.error(f"Error while attempting to stop containers: {e}")

        # Attempt to stop Ollama
        if stop_ollama:
            if is_ollama_available() or (platform.system() == "Windows" and distro_name):
                try:
                    # Preferred graceful stop via CLI (host or inside WSL)
                    logger.info("Attempting to stop Ollama via CLI...")
                    if platform.system() == "Windows" and distro_name:
                        _run(["ollama", "stop"])  # routed into WSL by _run
                    else:
                        subprocess.run(["ollama", "stop"], check=False)
                    logger.success("Ollama stop command executed (if supported).")
                except Exception as e:
                    logger.warning(f"`ollama stop` failed: {e}; trying process kill fallback")
                    # Fallback: terminate processes by name
                    try:
                        if platform.system() == "Windows" and not distro_name:
                            subprocess.run(["taskkill", "/F", "/IM", "ollama.exe"], check=False)
                        else:
                            # If inside WSL or on POSIX, attempt pkill
                            _run(["pkill", "-f", "ollama"]) if not (platform.system() == "Windows" and distro_name) else _run("pkill -f ollama", shell=True)
                        logger.success("Ollama processes signalled for termination.")
                    except Exception as e2:
                        logger.error(f"Failed to kill Ollama processes: {e2}")
            else:
                logger.info("Ollama CLI not present; skipping Ollama shutdown.")

        logger.info("Shutdown requests issued for infrastructure.")
    except Exception as e:
        logger.error(f"Error during shutdown_services: {e}")
