import pytest
from pathlib import Path


@pytest.fixture(autouse=True)
def isolate_test_files(tmp_path, monkeypatch):
    """Run each test in an isolated temporary workspace so relative paths
    like './outputs' and './data' are created under the test directory
    rather than the project root.

    This fixture changes the current working directory to a temporary
    folder and ensures `outputs` and `data` subfolders exist.
    """
    test_root = tmp_path / "workspace"
    test_root.mkdir()
    (test_root / "outputs").mkdir()
    (test_root / "data").mkdir()
    monkeypatch.chdir(test_root)
    yield
import os
import sys

# Ensure the project's `src/` directory is on sys.path so tests can import `app` package
ROOT = os.path.dirname(os.path.dirname(__file__))
SRC = os.path.join(ROOT, "src")
if SRC not in sys.path:
    sys.path.insert(0, SRC)

# Clean up outputs and data folders in project root after all tests
import shutil

def pytest_sessionfinish(session, exitstatus):
    """
    @brief Remove outputs and data folders from project root after all tests.

    This hook ensures that any 'outputs' and 'data' folders created in the project root are deleted after the test session.

    @param session Pytest session object.
    @param exitstatus Exit status code.
    @return None
    """
    root = Path(__file__).parent.parent
    for folder in ["outputs", "data"]:
        target = root / folder
        if target.exists() and target.is_dir():
            shutil.rmtree(target)
