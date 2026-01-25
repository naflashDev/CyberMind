"""
@file test_config_controller.py
@author naflashDev
@brief Unit tests for config_controller endpoints.
@details Tests endpoints for reading and updating .ini config files, including error cases.
"""
import os
import sys
import pytest
from fastapi.testclient import TestClient


# Forzar importación de main y config_controller usando importlib
import importlib.util


# Build portable paths for main.py and config_controller
SRC_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src'))
MAIN_PATH = os.path.join(SRC_PATH, 'main.py')
CONFIG_CONTROLLER_PATH = os.path.join(SRC_PATH, 'app', 'controllers', 'routes', 'config_controller.py')
if SRC_PATH not in sys.path:
    sys.path.insert(0, SRC_PATH)

# Check existence and import main.py
if not os.path.exists(MAIN_PATH):
    raise FileNotFoundError(f"main.py not found at {MAIN_PATH}. Please check your workspace structure.")
spec_main = importlib.util.spec_from_file_location('main', MAIN_PATH)
main = importlib.util.module_from_spec(spec_main)
spec_main.loader.exec_module(main)
app = main.app

# Check existence and import config_controller
if not os.path.exists(CONFIG_CONTROLLER_PATH):
    raise FileNotFoundError(f"config_controller.py not found at {CONFIG_CONTROLLER_PATH}. Please check your workspace structure.")
spec_config = importlib.util.spec_from_file_location('app.controllers.routes.config_controller', CONFIG_CONTROLLER_PATH)
config_controller = importlib.util.module_from_spec(spec_config)
spec_config.loader.exec_module(config_controller)

def test_get_config(monkeypatch):
    from unittest.mock import mock_open
    client = TestClient(app)
    # Simular que los archivos existen
    monkeypatch.setattr(os.path, 'exists', lambda p: True)
    # Simular contenido de archivo ini
    fake_ini = '#comentario\ndistro_name="Ubuntu";dockers_name="nginx";use_ollama="false"\n'
    m = mock_open(read_data=fake_ini)
    monkeypatch.setattr('builtins.open', m)
    # Simular Path.open (para pathlib)
    import pathlib
    monkeypatch.setattr(pathlib.Path, 'open', lambda self, *a, **kw: m())
    resp = client.get('/config')
    assert resp.status_code == 200
    assert 'files' in resp.json()

def test_update_config_file_not_found():
    client = TestClient(app)
    data = {'file': 'noexiste.ini', 'params': []}
    resp = client.post('/config', json=data)
    assert resp.status_code == 404

def test_update_config_ok(monkeypatch, tmp_path):
    client = TestClient(app)
    # Crear archivo temporal para simular ini
    ini_path = tmp_path / 'cfg_services.ini'
    ini_path.write_text('#comentario\nclave=valor\n')
import sys
import importlib.util

