import sys
import subprocess


def test_python_exec_prints_ok():
    """Minimal cross-platform smoke test used by CI to ensure subprocess
    invocation using argument lists works (no shell required).
    """
    proc = subprocess.run([sys.executable, "-c", "print('ok')"], capture_output=True, text=True, check=True)
    assert proc.stdout.strip() == "ok"
