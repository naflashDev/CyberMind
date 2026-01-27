"""
@file conftest.py
@author naflashDev
@brief Fixtures globales para tests unitarios.
@details Crea y elimina el archivo .env temporalmente para los tests que lo requieran.
"""
import os
import shutil
import pytest

ENV_PATH = os.path.join(os.path.dirname(__file__), '../../.env.test')
ENV_EXAMPLE_PATH = os.path.join(os.path.dirname(__file__), '../../.env.test')

@pytest.fixture(autouse=True)
def manage_env_file():
    # Setup: ensure .env.test exists (never touch .env)
    if not os.path.exists(ENV_PATH):
        # Si no existe, crea uno mínimo para los tests
        with open(ENV_PATH, 'w', encoding='utf-8') as f:
            f.write("POSTGRES_USER=test_user\nPOSTGRES_PASSWORD=test_pass\nPOSTGRES_DB=test_db\nPOSTGRES_HOST=127.0.0.1\nPOSTGRES_PORT=5432\n")
    yield
    # Teardown: elimina .env.test tras los tests (maneja bloqueo en Windows)
    import time
    max_retries = 5
    for attempt in range(max_retries):
        try:
            if os.path.exists(ENV_PATH):
                os.remove(ENV_PATH)
            break
        except PermissionError:
            time.sleep(0.5)
    else:
        print(f"[manage_env_file] WARNING: Could not remove {ENV_PATH} after {max_retries} attempts.")
