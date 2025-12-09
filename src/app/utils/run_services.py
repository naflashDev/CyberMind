"""
@file main.py
@brief Run dependent services.
@details This script ensures that the required infrastructure services
(OpenSearch, Dashboards, and Tiny RSS Docker container) are running inside
a specified WSL distribution before launching the FastAPI application.
@date Created: 2025-11-27 12:17:59
@author naflashDev
@project CyberMind
"""

import subprocess
import sys
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
        # Try to compose from Install/ if available
        try:
            project_root = Path(__file__).resolve().parents[1]
            ensure_compose_from_install(project_root)
        except Exception as e:
            logger.error(f"Failed to run docker compose from Install/: {e}")
        # If we are on Windows prefer to use provided WSL distro name; otherwise fall back to parameter
        if host_os == 'Windows':
            distro_arg = parameters[0] if parameters and len(parameters) > 0 else None
        else:
            distro_arg = parameters[0] if parameters and len(parameters) > 0 else None

    logger.info("Ensuring infrastructure (OpenSearch, Dashboards, Tiny stack)...")
    # pass distro_arg (None for host Docker) and the container list
    ensure_containers(parameters[1], distro_arg)
    logger.info("WSL infrastructure check finished.")
    '''
    logger.info("Starting UI service in a separate console...")
    start_ui_in_separate_terminal()
    logger.info("UI service launch command executed.")
    '''
    time.sleep(15)  # give some time for services to start
