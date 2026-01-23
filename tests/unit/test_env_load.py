"""
@file test_env_load.py
@author naflashDev
@brief Test para verificar la carga de variables de entorno desde .env
@details Comprueba que las variables críticas de PostgreSQL se cargan correctamente usando python-dotenv.
"""
import os
from dotenv import load_dotenv

def test_env_variables_loaded():
    '''
    @brief Verifica que las variables de entorno críticas están presentes tras cargar .env

    Carga el archivo .env y comprueba que las variables POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_DB, POSTGRES_HOST y POSTGRES_PORT existen y no están vacías.

    @return None. Lanza AssertionError si alguna variable falta o está vacía.
    '''
    load_dotenv()
    required_vars = [
        "POSTGRES_USER",
        "POSTGRES_PASSWORD",
        "POSTGRES_DB",
        "POSTGRES_HOST",
        "POSTGRES_PORT"
    ]
    for var in required_vars:
        value = os.getenv(var)
        assert value is not None and value != "", f"La variable {var} no está definida o está vacía."
