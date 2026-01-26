"""
@file conftest.py
@author naflashDev
@brief Fixtures globales para tests unitarios.
@details Crea y elimina el archivo .env temporalmente para los tests que lo requieran.
"""
import os
import shutil
import pytest

ENV_PATH = os.path.join(os.path.dirname(__file__), '../../.env')
ENV_EXAMPLE_PATH = os.path.join(os.path.dirname(__file__), '../../.env.example')

@pytest.fixture(autouse=True)
def manage_env_file():
    # Setup: copiar .env.example a .env
    if os.path.exists(ENV_EXAMPLE_PATH):
        shutil.copyfile(ENV_EXAMPLE_PATH, ENV_PATH)
    yield
    # Teardown: eliminar .env si existe
    if os.path.exists(ENV_PATH):
        os.remove(ENV_PATH)
