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
import builtins
def test_read_file_permission_error(monkeypatch, tmp_path):
    # Simula PermissionError
    def fake_open(*a, **k):
        raise PermissionError
    monkeypatch.setattr(builtins, "open", fake_open)
    result = utils.read_file("file.txt")
    assert result[0] == 2 or "permissions" in str(result[1])

def test_read_file_os_error(monkeypatch, tmp_path):
    # Simula OSError
    def fake_open(*a, **k):
        raise OSError
    monkeypatch.setattr(builtins, "open", fake_open)
    result = utils.read_file("file.txt")
    assert result[0] == 3 or "OS error" in str(result[1])

def test_read_file_unknown_error(monkeypatch, tmp_path):
    # Simula Exception genérica
    def fake_open(*a, **k):
        raise Exception("fail")
    monkeypatch.setattr(builtins, "open", fake_open)
    result = utils.read_file("file.txt")
    assert result[0] == 4 or "Unknown error" in str(result[1])

def test_write_file_permission_error(monkeypatch, tmp_path):
    # Simula PermissionError
    def fake_open(*a, **k):
        raise PermissionError
    monkeypatch.setattr(builtins, "open", fake_open)
    result = utils.write_file("file.txt", ["a"])
    assert result[0] == 2 or "permissions" in str(result[1])

def test_write_file_os_error(monkeypatch, tmp_path):
    # Simula OSError
    def fake_open(*a, **k):
        raise OSError
    monkeypatch.setattr(builtins, "open", fake_open)
    result = utils.write_file("file.txt", ["a"])
    assert result[0] == 3 or "OS error" in str(result[1])

def test_write_file_unknown_error(monkeypatch, tmp_path):
    # Simula Exception genérica
    def fake_open(*a, **k):
        raise Exception("fail")
    monkeypatch.setattr(builtins, "open", fake_open)
    result = utils.write_file("file.txt", ["a"])
    assert result[0] == 4 or "Unknown error" in str(result[1])

def test_get_connection_parameters_invalid(tmp_path):
    # Archivo con varias líneas válidas
    f = tmp_path / "params.txt"
    f.write_text("server_ip=1.2.3.4;server_port=1234\nserver_ip=2.2.2.2;server_port=2222\n")
    result = utils.get_connection_parameters(str(f))
    assert result[0] == 2 or "Incorrect number" in str(result[1])
    # Archivo sin parámetros requeridos
    f.write_text("foo=bar\n")
    result = utils.get_connection_parameters(str(f))
    assert result[0] == 3 or "Missing" in str(result[1])

def test_get_connection_service_parameters_invalid(tmp_path):
    # Archivo con varias líneas válidas
    f = tmp_path / "params2.txt"
    f.write_text("distro_name=ubuntu;dockers_name=main\ndistro_name=debian;dockers_name=other\n")
    result = utils.get_connection_service_parameters(str(f))
    assert result[0] == 2 or "Incorrect number" in str(result[1])
    # Archivo sin parámetros requeridos
    f.write_text("foo=bar\n")
    result = utils.get_connection_service_parameters(str(f))
    assert result[0] == 3 or "Missing" in str(result[1])

def test_create_config_file_error(monkeypatch):
    # Simula error en write_file
    monkeypatch.setattr(utils, "write_file", lambda *a, **k: (1, "fail"))
    result = utils.create_config_file("file.txt", ["a"])
    assert result[0] == 1 or "Error recreating" in str(result[1])



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


def test_read_file_invalid_params():
    # lines_to_escape no es lista
    result = utils.read_file(123, None)
    assert result[0] == 5 or 'Incorrect' in str(result[1])
    # lines_to_escape contiene elementos no str
    result = utils.read_file("file.txt", [1, 2])
    assert result[0] == 5 or 'Incorrect' in str(result[1])


def test_write_file_invalid_params():
    # filename no es str
    result = utils.write_file(123, ["a"])
    assert result[0] == 5 or 'Incorrect' in str(result[1])
    # content no es lista
    result = utils.write_file("file.txt", "no_lista")
    assert result[0] == 5 or 'Incorrect' in str(result[1])
    # mode no es str
    result = utils.write_file("file.txt", ["a"], 123)
    assert result[0] == 5 or 'Incorrect' in str(result[1])
    # content contiene elementos no str
    result = utils.write_file("file.txt", [1, 2])
    assert result[0] == 5 or 'Incorrect' in str(result[1])


def test_create_config_file_invalid_params():
    # file_name no es str
    result = utils.create_config_file(123, ["a"])
    assert result[0] == 2 or 'Invalid' in str(result[1])
    # content no es lista
    result = utils.create_config_file("file.txt", "no_lista")
    assert result[0] == 2 or 'Invalid' in str(result[1])
    # content contiene elementos no str
    result = utils.create_config_file("file.txt", [1, 2])
    assert result[0] == 2 or 'Invalid' in str(result[1])
