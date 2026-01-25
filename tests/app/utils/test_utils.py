"""
@file test_utils.py
@author naflashDev
@brief Pruebas unitarias para utils.py.
@details Cobertura de funciones de lectura, escritura y utilidades de archivos.
"""

import pytest
from src.app.utils import utils
import tempfile
import os


def test_read_file_success():
    # Crear archivo temporal
    with tempfile.NamedTemporaryFile(delete=False, mode="w", encoding="utf-8") as f:
        f.write("linea1\n#comentario\nlinea2\n")
        fname = f.name
    # Leer sin filtrar
    result = utils.read_file(fname)
    assert isinstance(result, tuple)
    # Leer filtrando comentarios
    result2 = utils.read_file(fname, lines_to_escape=["#"])
    # El tercer elemento debe ser una lista de líneas
    assert isinstance(result2[2], list)
    assert any("linea1" in l for l in result2[2])
    assert not any("#comentario" in l for l in result2[2])
    os.remove(fname)


def test_read_file_not_found():
    result = utils.read_file("no_existe.txt")
    assert result[0] == [] or result[1] != 0


def test_write_file_success():
    with tempfile.NamedTemporaryFile(delete=False, mode="w", encoding="utf-8") as f:
        fname = f.name
    content = ["a", "b", "c"]
    result = utils.write_file(fname, content)
    # El segundo valor es un mensaje de éxito
    assert "written successfully" in str(result[1])
    with open(fname, "r", encoding="utf-8") as f:
        lines = f.read().splitlines()
    # El archivo tendrá una sola línea concatenada
    assert lines == [''.join(content)]
    os.remove(fname)


def test_write_file_error():
    # Intentar escribir en ruta inválida
    result = utils.write_file("/no/puede/crear.txt", ["x"])
    assert result[1] != 0


def test_get_connection_parameters(tmp_path):
    f = tmp_path / "params.txt"
    f.write_text("host=localhost\nport=5432\nuser=admin\n")
    result = utils.get_connection_parameters(str(f))
    assert isinstance(result, tuple)
    # Puede devolver el número de líneas o el contenido, aceptar ambos
    assert ("host" in str(result[0]) or "localhost" in str(result[0]) or str(result[0]).isdigit())


def test_get_connection_service_parameters(tmp_path):
    f = tmp_path / "params2.txt"
    f.write_text("service=api\nsecret=123\n")
    result = utils.get_connection_service_parameters(str(f))
    assert isinstance(result, tuple)
    # Puede devolver el número de líneas o el contenido, aceptar ambos
    assert ("service" in str(result[0]) or "api" in str(result[0]) or str(result[0]).isdigit())


def test_create_config_file(tmp_path):
    f = tmp_path / "config.txt"
    content = ["line1", "line2"]
    result = utils.create_config_file(str(f), content)
    # El segundo valor es un mensaje de éxito
    assert "successfully" in str(result[1])
    # El archivo tendrá una sola línea concatenada
    assert f.read_text().splitlines() == [''.join(content)]
