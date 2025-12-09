import sys
import os
import unittest
from unittest import mock
from pathlib import Path

# Ensure src is importable
ROOT = Path(__file__).resolve().parents[2]
SRC = str(ROOT / 'src')
if SRC not in sys.path:
    sys.path.insert(0, SRC)

from app.utils import run_services as rs


class TestRunServicesCombinedCompose(unittest.TestCase):

    def setUp(self):
        # create temporary project layout
        self.tmp_root = Path('tmp_project_combined')
        self.install_dir = self.tmp_root / 'Install'
        self.docker_dir = self.tmp_root / 'docker'
        self.install_dir.mkdir(parents=True, exist_ok=True)
        self.docker_dir.mkdir(parents=True, exist_ok=True)

        # create the two compose files
        (self.install_dir / 'tinytinyrss.yml').write_text('# tinytinyrss')
        (self.install_dir / 'opensearch-compose.yml').write_text('# opensearch')
        # create env file
        (self.docker_dir / 'stack.env').write_text('KEY=VALUE')

    def tearDown(self):
        # cleanup files and directories
        try:
            for p in [self.install_dir / 'tinytinyrss.yml', self.install_dir / 'opensearch-compose.yml']:
                if p.exists():
                    p.unlink()
            envf = self.docker_dir / 'stack.env'
            if envf.exists():
                envf.unlink()
            # remove dirs
            if self.install_dir.exists():
                self.install_dir.rmdir()
            if self.docker_dir.exists():
                self.docker_dir.rmdir()
            if self.tmp_root.exists():
                self.tmp_root.rmdir()
        except Exception:
            pass

    def test_combined_compose_invoked_with_envfile(self):
        # Ensure docker present
        with mock.patch('shutil.which', return_value='/usr/bin/docker'):
            calls = []

            def fake_run(cmd, check=False, **kwargs):
                # record the command
                calls.append(cmd)
                mockres = mock.Mock()
                mockres.returncode = 0
                return mockres

            with mock.patch('subprocess.run', side_effect=fake_run):
                rs.ensure_compose_from_install(self.tmp_root)

            # find the command that performed up -d for combined files and included the env-file
            str_calls = [' '.join(map(str, c)) for c in calls if isinstance(c, (list, tuple))]
            matched = [c for c in str_calls if 'tinytinyrss.yml' in c and 'opensearch-compose.yml' in c and '--env-file' in c and 'up' in c]
            # Ensure env-file path points to Install/stack.env (preferred) or at least contains 'stack.env'
            self.assertTrue(matched, f"Expected combined compose invocation, got calls: {str_calls}")
            self.assertTrue(any('Install' in c and 'stack.env' in c for c in matched), f"Expected env-file in Install/, matched calls: {matched}")

    def test_combined_compose_uses_sudo_on_linux_nonroot(self):
        # simulate Linux and non-root (os_get_euid != 0)
        with mock.patch('shutil.which', return_value='/usr/bin/docker'):
            with mock.patch('platform.system', return_value='Linux'):
                with mock.patch('app.utils.run_services.os_get_euid', return_value=1000):
                    called = []

                    def fake_run(cmd, check=False, **kwargs):
                        called.append(cmd)
                        return mock.Mock()

                    with mock.patch('subprocess.run', side_effect=fake_run):
                        rs.ensure_compose_from_install(self.tmp_root)

                    # Ensure first element of the invoked compose command list is 'sudo' at least once
                    list_calls = [c for c in called if isinstance(c, list)]
                    self.assertTrue(any(call and call[0] == 'sudo' for call in list_calls), f"Expected sudo prefix in commands, got: {list_calls}")

    def test_no_compose_command_available_logs_and_returns(self):
        # simulate neither docker nor docker-compose present
        with mock.patch('shutil.which', return_value=None):
            # Should not raise
            rs.ensure_compose_from_install(self.tmp_root)


if __name__ == '__main__':
    unittest.main()
