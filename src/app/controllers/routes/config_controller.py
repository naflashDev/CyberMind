"""
@file config_controller.py
@author naflashDev
@brief Endpoints para gestión y edición de archivos .ini de configuración.
@details Permite consultar y modificar los parámetros de los archivos .ini principales del sistema (cfg_services.ini, cfg.ini) vía API REST.
"""

from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel
from pathlib import Path
import os

router = APIRouter(
    prefix="",
    tags=["Configuración"],
)

INI_FILES = [
    {"name": "cfg_services.ini", "path": Path(__file__).resolve().parents[3] / "cfg_services.ini"},
    {"name": "cfg.ini", "path": Path(__file__).resolve().parents[3] / "cfg.ini"},
]

class IniParam(BaseModel):
    file: str
    key: str
    value: str

@router.get("/config")
async def get_config():
    """
    @brief Devuelve los parámetros de los archivos .ini principales.
    @details Retorna una lista de archivos, cada uno con sus parámetros y tipo (boolean/text).
    """
    result = []
    for ini in INI_FILES:
        params = []
        if ini["path"].exists():
            with ini["path"].open("r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#"): continue
                    # Separar por ; y buscar pares clave=valor
                    parts = line.split(";")
                    for p in parts:
                        if "=" in p:
                            k, v = p.split("=", 1)
                            k = k.strip()
                            v = v.strip()
                            param_type = "boolean" if v.lower() in ["true", "false"] else "text"
                            params.append({"key": k, "value": v, "type": param_type})
        result.append({"file": ini["name"], "params": params})
    return {"files": result}


@router.post("/config")
async def update_config(data: dict):
    """
    @brief Actualiza los parámetros de un archivo .ini y gestiona la sección cybersentinel.

    Modifica el archivo .ini indicado, añade el bloque [cybersentinel] si se activa use_ollama y lo arranca automáticamente.

    @param data Diccionario con 'file' y 'params'.
    @return Diccionario con estado.
    """
    from app.utils.run_services import ensure_infrastructure

    file = data.get("file")
    params = data.get("params")
    ini = next((i for i in INI_FILES if i["name"] == file), None)
    if not ini:
        raise HTTPException(status_code=404, detail="Archivo no encontrado")

    ini_path = ini["path"]
    # Leer comentarios existentes
    comments = []
    if ini_path.exists():
        with ini_path.open("r", encoding="utf-8") as f:
            for line in f:
                if line.strip().startswith("#"):
                    comments.append(line.rstrip())

    # Construir la línea de parámetros en formato clave=valor;clave=valor;...
    param_line = ";".join([f"{p['key']}={p['value']}" for p in params if p["key"]])

    # Guardar solo comentarios y la línea de parámetros
    new_content = "\n".join(comments + [param_line]) + "\n"
    with ini_path.open("w", encoding="utf-8") as f:
        f.write(new_content)

    # Si se activa use_ollama, lanzar infraestructura Ollama
    use_ollama = any(p["key"] == "use_ollama" and str(p["value"]).lower() == "true" for p in params)
    if use_ollama:
        # Extraer distro_name y dockers_name para pasarlos como parámetros
        distro_name = next((p["value"] for p in params if p["key"] == "distro_name"), None)
        dockers_name = next((p["value"] for p in params if p["key"] == "dockers_name"), None)
        parameters = [distro_name, dockers_name]
        ensure_infrastructure(parameters, use_ollama=True)

    return {"status": "ok"}
