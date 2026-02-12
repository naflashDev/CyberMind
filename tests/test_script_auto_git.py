
"""
@file test_script_auto_git.py
@author naflashDev
@brief Unit tests for script_auto Git operations.
@details Tests cloning and updating of repositories in script_auto.py, ensuring correct subprocess calls and error handling.
"""
import unittest
import subprocess
import os
from unittest import mock

# Limpiar PYTEST_CURRENT_TEST antes de importar el servicio
os.environ.pop("PYTEST_CURRENT_TEST", None)
from app.services.llm import script_auto


class TestScriptAutoGit(unittest.TestCase):
    def setUp(self):
        # Create a temporary path used in tests
        self.repo_url = "https://example.com/repo.git"
        self.repo_dir = "tmp_repo_dir"

    @mock.patch("app.services.llm.script_auto.subprocess.check_call")
    @mock.patch("os.path.exists")
    def test_clone_repository_calls_git_clone_when_missing(self, mock_exists, mock_check):
        mock_exists.return_value = False
        with mock.patch.dict(os.environ, {}, clear=True):
            script_auto.clone_repository(self.repo_url, self.repo_dir)
        mock_check.assert_called_once_with(["git", "clone", self.repo_url, self.repo_dir])

    @mock.patch("app.services.llm.script_auto.subprocess.check_call")
    @mock.patch("os.path.exists")
    def test_clone_repository_skips_when_present(self, mock_exists, mock_check):
        mock_exists.return_value = True
        with mock.patch.dict(os.environ, {}, clear=True):
            script_auto.clone_repository(self.repo_url, self.repo_dir)
        mock_check.assert_not_called()

    @mock.patch("app.services.llm.script_auto.subprocess.check_call")
    @mock.patch("os.path.exists")
    def test_update_repository_calls_git_pull_when_exists(self, mock_exists, mock_check):
        mock_exists.return_value = True
        with mock.patch.dict(os.environ, {}, clear=True):
            script_auto.update_repository(self.repo_dir)
        mock_check.assert_called_once_with(["git", "-C", self.repo_dir, "pull"])

    @mock.patch("app.services.llm.script_auto.subprocess.check_call")
    @mock.patch("os.path.exists")
    def test_update_repository_skips_when_missing(self, mock_exists, mock_check):
        mock_exists.return_value = False
        with mock.patch.dict(os.environ, {}, clear=True):
            script_auto.update_repository(self.repo_dir)
        mock_check.assert_not_called()

    @mock.patch("app.services.llm.script_auto.subprocess.Popen")
    @mock.patch("app.services.llm.script_auto.subprocess.check_call", side_effect=subprocess.CalledProcessError(1, "git"))
    @mock.patch("os.path.exists")
    def test_clone_repository_raises_on_git_error(self, mock_exists, mock_check, mock_popen):
        mock_exists.return_value = False
        mock_popen.side_effect = subprocess.CalledProcessError(1, "git")
        with mock.patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(subprocess.CalledProcessError):
                script_auto.clone_repository(self.repo_url, self.repo_dir)

    @mock.patch("app.services.llm.script_auto.subprocess.Popen")
    @mock.patch("app.services.llm.script_auto.subprocess.check_call")
    @mock.patch("os.path.exists")
    def test_update_repository_raises_on_git_error(self, mock_exists, mock_check, mock_popen):
        mock_exists.return_value = True
        mock_check.side_effect = subprocess.CalledProcessError(1, "git")
        mock_popen.side_effect = subprocess.CalledProcessError(1, "git")
        # Eliminar entorno de test antes de ejecutar
        if "PYTEST_CURRENT_TEST" in os.environ:
            del os.environ["PYTEST_CURRENT_TEST"]
        with mock.patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(subprocess.CalledProcessError):
                script_auto.update_repository(self.repo_dir)


if __name__ == "__main__":
    unittest.main()
