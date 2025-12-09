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

def wsl_docker_is_running(container_name: str, distro_name: str) -> bool:
    """
    Check if a Docker container is running inside the given WSL distribution.
    """
    cmd = (
        f"docker ps "
        f"--filter name={container_name} "
        f"--filter status=running "
        f"--format '{{{{.Names}}}}'"
    )
    try:
        result = subprocess.run(
            ["wsl", "-d", distro_name, "bash", "-c", cmd],
            capture_output=True,
            text=True,
            check=False,
        )
        names = result.stdout.strip().splitlines()
        is_running = container_name in names
        logger.info(
            f"Container '{container_name}' running in WSL distro "
            f"'{distro_name}': {is_running}"
        )
        return is_running
    except Exception as e:
        logger.error(
            f"Failed to check Docker container '{container_name}' in WSL distro "
            f"'{distro_name}': {e}"
        )
        return False

def wsl_docker_start_container(container_name: str, distro_name: str) -> None:
    """
    Start a Docker container inside the given WSL distribution if it exists
    but is stopped.
    """
    try:
        logger.info(
            f"Trying to start Docker container '{container_name}' in "
            f"WSL distro '{distro_name}'..."
        )
        subprocess.run(
            ["wsl", "-d", distro_name, "bash", "-c", f"docker start {container_name}"],
            check=False,
        )
    except Exception as e:
        logger.error(
            f"Error while trying to start container '{container_name}' in "
            f"WSL distro '{distro_name}': {e}"
        )

def ensure_opensearch_scripts(distro_name: str, user: str, delay_seconds: int = 10):
    """
    Start OpenSearch and OpenSearch Dashboards in separate Windows Terminal (wt.exe)
    windows, running inside the specified WSL distribution.

    This function launches two independent wt.exe instances, each running a WSL
    command to start OpenSearch or OpenSearch Dashboards. Logs stay visible in
    their own terminals and do not mix with the main launcher logs.

    Args:
        distro_name (str): Name of the WSL distribution (for example, "Ubuntu").
        user (str): Linux username inside the WSL distribution.
        delay_seconds (int): Time to wait (in seconds) between starting
            OpenSearch and starting OpenSearch Dashboards.
    """
    # Linux paths inside WSL to the OpenSearch binaries
    opensearch_bin = f"/home/{user}/opensearch-2.12.0/bin/opensearch"
    dashboards_bin = f"/home/{user}/opensearch-dashboards-2.9.0/bin/opensearch-dashboards"

    # Command lines for wt.exe (each opens a new Windows Terminal window)
    opensearch_cmd = f'wsl -d {distro_name} bash -lc "{opensearch_bin}"'
    dashboards_cmd = f'wsl -d {distro_name} bash -lc "{dashboards_bin}"'

    # 1) Start OpenSearch in its own Windows Terminal window
    try:
        logger.info(
            f"Opening Windows Terminal for OpenSearch in WSL distro '{distro_name}'..."
        )
        subprocess.Popen(
            [
                "wt.exe",
                "new-tab",
                "cmd",
                "/k",
                opensearch_cmd,
            ],
            shell=False,
        )
        logger.success("OpenSearch started in a separate Windows Terminal window.")
    except Exception as e:
        logger.error(
            f"Error starting OpenSearch in Windows Terminal (distro '{distro_name}'): {e}"
        )

    # 2) Wait a bit to give OpenSearch time to boot
    if delay_seconds > 0:
        logger.info(f"Waiting {delay_seconds} seconds before starting Dashboards...")
        time.sleep(delay_seconds)

    # 3) Start OpenSearch Dashboards in its own Windows Terminal window
    try:
        logger.info(
            f"Opening Windows Terminal for OpenSearch Dashboards in WSL distro "
            f"'{distro_name}'..."
        )
        subprocess.Popen(
            [
                "wt.exe",
                "new-tab",
                "cmd",
                "/k",
                dashboards_cmd,
            ],
            shell=False,
        )
        logger.success(
            "OpenSearch Dashboards started in a separate Windows Terminal window."
        )
    except Exception as e:
        logger.error(
            f"Error starting OpenSearch Dashboards in Windows Terminal "
            f"(distro '{distro_name}'): {e}"
        )

def ensure_tiny_stack_container(TINY_STACK_CONTAINERES: str, distro_name: str):
    """
    Ensure the Docker container that hosts DB + Tiny RSS is running in WSL.
    If the container is stopped, try to start it.
    """
    for name in TINY_STACK_CONTAINERES.split(','):
        try:
            if wsl_docker_is_running(name, distro_name):
                logger.info(f"Container '{name}' already running in WSL.")
                continue
            exit = False
            while not exit:
                wsl_docker_start_container(name, distro_name)
                if wsl_docker_is_running(name, distro_name):
                    logger.success(f"Container '{name}' started successfully in WSL.")
                    exit = True
                else:
                    logger.warning(
                        f"Container '{name}' is not running and could not be started. "
                        f"Check if it exists or how it is created."
                    )
        except Exception as e:
            logger.error(f"Unexpected error ensuring container '{name}': {e}")

def ensure_infrastructure(parameters):
    """
    Ensure all infrastructure services are up in WSL:
    - OpenSearch (via .sh)
    - OpenSearch Dashboards (via .sh)
    - Docker container with DB + Tiny RSS (via docker start)
    """
    logger.info("Ensuring WSL infrastructure (OpenSearch, Dashboards, Tiny stack)...")
    #ensure_opensearch_scripts(parameters[0],parameters[1])
    ensure_tiny_stack_container(parameters[2],parameters[0])
    logger.info("WSL infrastructure check finished.")
    logger.info("Starting UI service in a separate console...")
    start_ui_in_separate_terminal()
    logger.info("UI service launch command executed.")

def start_ui_in_separate_terminal():
    """
    Start the UI Python script in a separate Windows Terminal (wt.exe) window.

    This function automatically detects the project root (the directory that
    contains the 'Scraping_web' folder) and runs
    `python Scraping_web/ui/ui_main.py` from there, so imports work correctly.
    """
    try:
        # Current file: .../Scraping_web/main.py
        # Project root: directory that contains "Scraping_web"
        project_root = Path(__file__).resolve().parent.parent
        ui_script = project_root /"ui" / "ui_main.py"

        logger.info(f"Project root detected as: {project_root}")
        logger.info(f"UI script path: {ui_script}")

        subprocess.Popen(
            [
                "wt.exe",
                "new-tab",
                "cmd",
                "/k",
                f"python {ui_script}",
            ],
            shell=False,
            cwd=str(project_root),
        )
        logger.success("UI script started in a separate Windows Terminal.")
    except Exception as e:
        logger.error(f"Error starting UI script in Windows Terminal: {e}")
