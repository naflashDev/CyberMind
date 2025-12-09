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

class TestRunServices(unittest.TestCase):

    def test_detect_host_os_returns_tuple(self):
        plat, distro = rs.detect_host_os()
        self.assertIsInstance(plat, str)
        # distro may be None or str

    def test_is_docker_available_true_false(self):
        with mock.patch('shutil.which', return_value='C:\\docker'):
            self.assertTrue(rs.is_docker_available())
        with mock.patch('shutil.which', return_value=None):
            self.assertFalse(rs.is_docker_available())

    def test_is_docker_daemon_running_checks_docker_info(self):
        # Simulate docker available and docker info returning 0
        with mock.patch('app.utils.run_services.is_docker_available', return_value=True):
            mock_res = mock.Mock()
            mock_res.returncode = 0
            with mock.patch('subprocess.run', return_value=mock_res) as run_mock:
                self.assertTrue(rs.is_docker_daemon_running())
                run_mock.assert_called()

            mock_res.returncode = 1
            with mock.patch('subprocess.run', return_value=mock_res):
                self.assertFalse(rs.is_docker_daemon_running())

    def test_ensure_compose_from_install_no_folder(self):
        # Create a temporary non-existing project root
        tmp = Path('tmp_nonexistent_project_root')
        if tmp.exists():
            for f in tmp.rglob('*'):
                f.unlink()
            tmp.rmdir()
        # Call function; should not raise
        rs.ensure_compose_from_install(tmp)

    def test_ensure_compose_from_install_executes_compose(self):
        # Build a temporary project root with Install/ and a dummy yaml
        tmp_root = Path('tmp_project_root')
        install_dir = tmp_root / 'Install'
        try:
            install_dir.mkdir(parents=True, exist_ok=True)
            cf = install_dir / 'docker-compose.yml'
            cf.write_text('# dummy')

            # Patch shutil.which to return that docker exists
            with mock.patch('shutil.which', return_value='/usr/bin/docker'):
                # Simulate subprocess.run behavior depending on the command
                calls = []
                def fake_run(cmd, capture_output=False, text=False, check=False, **kwargs):
                    calls.append(cmd)
                    cmd_str = ' '.join(cmd if isinstance(cmd, list) else [str(cmd)])
                    mock_res = mock.Mock()
                    # If docker compose config --services -> return a stdout with service names
                    if 'config' in cmd_str and '--services' in cmd_str:
                        mock_res.returncode = 0
                        mock_res.stdout = 'svc_a\nsvc_b\n'
                        return mock_res
                    # If docker ps -a label check -> return empty stdout to indicate missing
                    if 'ps' in cmd_str and '--filter' in cmd_str:
                        mock_res.returncode = 0
                        mock_res.stdout = ''
                        return mock_res
                    # For the up -d call
                    if 'up' in cmd_str:
                        mock_res.returncode = 0
                        mock_res.stdout = ''
                        return mock_res
                    mock_res.returncode = 0
                    mock_res.stdout = ''
                    return mock_res

                with mock.patch('subprocess.run', side_effect=fake_run):
                    rs.ensure_compose_from_install(tmp_root)

                # Ensure config and up were called
                called_cmds = [' '.join(map(str, c)) for c in calls]
                self.assertTrue(any('config --services' in c for c in called_cmds))
                self.assertTrue(any(' up -d' in c for c in called_cmds))
        finally:
            # Cleanup
            try:
                if cf.exists():
                    cf.unlink()
                if install_dir.exists():
                    install_dir.rmdir()
                if tmp_root.exists():
                    tmp_root.rmdir()
            except Exception:
                pass

    def test_ensure_docker_daemon_running_flow(self):
        # Simulate behavior: is_docker_daemon_running returns False first, then True
        seq = {'count': 0}
        def fake_is_running():
            seq['count'] += 1
            return seq['count'] >= 2

        with mock.patch('app.utils.run_services.is_docker_daemon_running', side_effect=fake_is_running):
            # Patch platform.system to Linux to execute systemctl branch (we'll patch subprocess.run to noop)
            with mock.patch('platform.system', return_value='Linux'):
                with mock.patch('subprocess.run', return_value=mock.Mock()):
                    result = rs.ensure_docker_daemon_running('Linux')
                    self.assertTrue(result)

    def test_wsl_docker_is_running_host_and_wsl(self):
        # Host path (Linux)
        with mock.patch('platform.system', return_value='Linux'):
            mock_res = mock.Mock()
            mock_res.stdout = 'mycontainer\n'
            with mock.patch('subprocess.run', return_value=mock_res) as run_mock:
                self.assertTrue(rs.wsl_docker_is_running('mycontainer', None))
                run_mock.assert_called()

        # WSL path on Windows (distro provided)
        with mock.patch('platform.system', return_value='Windows'):
            mock_res = mock.Mock()
            mock_res.stdout = 'wc\n'
            def fake_run(args, capture_output=True, text=True, check=False):
                # expect wsl invocation
                self.assertEqual(args[0], 'wsl')
                return mock_res

            with mock.patch('subprocess.run', side_effect=fake_run):
                self.assertTrue(rs.wsl_docker_is_running('wc', 'Ubuntu'))

    def test_wsl_docker_start_container_host_and_wsl(self):
        # Host start
        with mock.patch('platform.system', return_value='Linux'):
            with mock.patch('subprocess.run') as run_mock:
                rs.wsl_docker_start_container('c1', None)
                run_mock.assert_called_with(['docker', 'start', 'c1'], check=False)

        # WSL start on Windows
        with mock.patch('platform.system', return_value='Windows'):
            def fake_run(args, check=False):
                # expect wsl command
                assert args[0] == 'wsl'
                return mock.Mock()

            with mock.patch('subprocess.run', side_effect=fake_run) as run_mock:
                rs.wsl_docker_start_container('c2', 'Ubuntu')
                # ensure subprocess.run was invoked at least once
                self.assertTrue(run_mock.called)


if __name__ == '__main__':
    unittest.main()
