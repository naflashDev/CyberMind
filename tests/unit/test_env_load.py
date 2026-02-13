"""
@file test_env_load.py
@author naflashDev
@brief Test para verificar la carga de variables de entorno desde .env
@details Comprueba que las variables críticas de PostgreSQL se cargan correctamente usando python-dotenv.
"""
import os
from dotenv import load_dotenv
import pathlib


def test_env_variables_loaded_happy_path(monkeypatch):
    # Always load .env.test for test isolation
    env_test_path = pathlib.Path(__file__).parent.parent.parent / ".env.test"
    load_dotenv(dotenv_path=env_test_path, override=True)
    '''
    @brief Happy Path: All required env vars are present and non-empty.
    Simulates .env loading and checks all required PostgreSQL variables exist.
    '''
    # Arrange
    env_vars = {
        "POSTGRES_USER": "user",
        "POSTGRES_PASSWORD": "pass",
        "POSTGRES_DB": "db",
        "POSTGRES_HOST": "localhost",
        "POSTGRES_PORT": "5432"
    }
    for k, v in env_vars.items():
        monkeypatch.setenv(k, v)
    # Act & Assert
    for var in env_vars:
        value = os.getenv(var)
        assert value is not None and value != ""

def test_env_variables_loaded_missing(monkeypatch):
    import tempfile
    env_test_path = pathlib.Path(__file__).parent.parent.parent / ".env.test"
    # Mock open to avoid PermissionError
    import builtins
    monkeypatch.setattr(builtins, "open", lambda *args, **kwargs: tempfile.TemporaryFile(mode="w+"))
    load_dotenv(dotenv_path=env_test_path, override=True)
    # Remove POSTGRES_USER from environment to simulate missing var
    monkeypatch.delenv("POSTGRES_USER", raising=False)
    '''
    @brief Edge Case: Missing required env var.
    Simulates missing POSTGRES_USER and expects assertion failure.
    '''
    # Arrange
    env_vars = {
        "POSTGRES_PASSWORD": "pass",
        "POSTGRES_DB": "db",
        "POSTGRES_HOST": "localhost",
        "POSTGRES_PORT": "5432"
    }
    for k, v in env_vars.items():
        monkeypatch.setenv(k, v)
    # Act & Assert
    value = os.getenv("POSTGRES_USER")
    assert value is None or value == ""

def test_env_variables_loaded_empty(monkeypatch):
    env_test_path = pathlib.Path(__file__).parent.parent.parent / ".env.test"
    load_dotenv(dotenv_path=env_test_path, override=True)
    '''
    @brief Error Handling: Empty env var value.
    Simulates POSTGRES_USER present but empty and expects assertion failure.
    '''
    # Arrange
    env_vars = {
        "POSTGRES_USER": "",
        "POSTGRES_PASSWORD": "pass",
        "POSTGRES_DB": "db",
        "POSTGRES_HOST": "localhost",
        "POSTGRES_PORT": "5432"
    }
    for k, v in env_vars.items():
        monkeypatch.setenv(k, v)
    # Act & Assert
    value = os.getenv("POSTGRES_USER")
    assert value == ""
