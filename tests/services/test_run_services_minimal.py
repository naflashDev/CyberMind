"""
@file test_run_services_minimal.py
@author naflashDev
@brief Minimal unit tests for run_services helpers.
@details Minimal tests for infrastructure detection and helper functions in run_services.py, focusing on edge cases and minimal configuration.
"""
import sys
import subprocess


def test_python_exec_prints_ok():
    """Minimal cross-platform smoke test used by CI to ensure subprocess
    invocation using argument lists works (no shell required).
    """
    proc = subprocess.run([sys.executable, "-c", "print('ok')"], capture_output=True, text=True, check=True)
    assert proc.stdout.strip() == "ok"
