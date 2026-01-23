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
        # Should not raise
        script_auto.clone_repository(self.repo_url, self.repo_dir)
        mock_check.assert_called_once_with(["git", "clone", self.repo_url, self.repo_dir])

    @mock.patch("app.services.llm.script_auto.subprocess.check_call")
    @mock.patch("os.path.exists")
    def test_clone_repository_skips_when_present(self, mock_exists, mock_check):
        mock_exists.return_value = True
        script_auto.clone_repository(self.repo_url, self.repo_dir)
        mock_check.assert_not_called()

    @mock.patch("app.services.llm.script_auto.subprocess.check_call")
    @mock.patch("os.path.exists")
    def test_update_repository_calls_git_pull_when_exists(self, mock_exists, mock_check):
        mock_exists.return_value = True
        script_auto.update_repository(self.repo_dir)
        mock_check.assert_called_once_with(["git", "-C", self.repo_dir, "pull"])

    @mock.patch("app.services.llm.script_auto.subprocess.check_call")
    @mock.patch("os.path.exists")
    def test_update_repository_skips_when_missing(self, mock_exists, mock_check):
        mock_exists.return_value = False
        script_auto.update_repository(self.repo_dir)
        mock_check.assert_not_called()

    @mock.patch("app.services.llm.script_auto.subprocess.check_call", side_effect=subprocess.CalledProcessError(1, "git"))
    @mock.patch("os.path.exists")
    def test_clone_repository_raises_on_git_error(self, mock_exists, mock_check):
        mock_exists.return_value = False
        with self.assertRaises(subprocess.CalledProcessError):
            script_auto.clone_repository(self.repo_url, self.repo_dir)

    @mock.patch("app.services.llm.script_auto.subprocess.check_call", side_effect=subprocess.CalledProcessError(1, "git"))
    @mock.patch("os.path.exists")
    def test_update_repository_raises_on_git_error(self, mock_exists, mock_check):
        mock_exists.return_value = True
        with self.assertRaises(subprocess.CalledProcessError):
            script_auto.update_repository(self.repo_dir)


if __name__ == "__main__":
    unittest.main()
