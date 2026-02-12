__all__ = ["router"]
"""
@file hashed_controller.py
@author naflashDev
@brief FastAPI router for hash operations.
@details Exposes endpoints for hashing and unhashing phrases using supported algorithms.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from typing import Literal
from app.models.db import get_db
from app.services.hashed.hash_service import HashService
from app.services.hashed.hash_repository import HashAlgorithm
from sqlalchemy.orm import Session
from fastapi import UploadFile, File
import io
import codecs
import time
from fastapi.responses import JSONResponse
import base64
class HashRequest(BaseModel):
    phrase: str = Field(..., description="Phrase to hash")
    algorithm: Literal["MD5", "SHA256", "SHA512"] = Field(..., description="Hash algorithm")




class MultiUnhashRequest(BaseModel):
    hashes: str = Field(..., description="Hashes separados por línea (multilínea)")
    max_len: int = Field(20, description="Longitud máxima para fuerza bruta")



class MultiUnhashResponseItem(BaseModel):
    hash: str
    original: str | None
    type: str | None
    found: bool
    method: str | None

# Nuevo modelo para respuesta de archivo (debe ir después de MultiUnhashResponseItem)
class MultiUnhashFileResponse(BaseModel):
    results: list[MultiUnhashResponseItem]

class HashResponse(BaseModel):
    hashed_value: str

class UnhashResponse(BaseModel):
    original_value: str

router = APIRouter(prefix="/hashed", tags=["Hashed"])

@router.post("/hash", response_model=HashResponse)
def hash_phrase(request: HashRequest, db: Session = Depends(get_db)):
    '''
    @brief Endpoint to hash a phrase.
    '''
    service = HashService(db)
    try:
        hashed = service.hash_phrase(request.phrase, HashAlgorithm(request.algorithm))
        return {"hashed_value": hashed}
    except Exception as e:
        # Generic error message for UI, no internal details
        raise HTTPException(status_code=400, detail="Ha ocurrido un error interno. Por favor, contacte con el administrador.")

@router.post("/unhash", response_model=list[MultiUnhashResponseItem])
def unhash(request: MultiUnhashRequest, db: Session = Depends(get_db)):
    '''
    @brief Endpoint para deshashear uno o varios hashes (multilínea, auto-detecta tipo, DB y fuerza bruta).
    '''
    service = HashService(db)
    hashes = [h.strip() for h in request.hashes.splitlines() if h.strip()]
    results = service.unhash(hashes, max_len=request.max_len)
    return results

@router.post("/hash-file")
async def hash_file(file: UploadFile = File(...), algorithm: str = "SHA256", db: Session = Depends(get_db)):
    '''
    @brief Endpoint to upload a file of words and store hashes.

    Allows uploading a text file where each line is a word. The user selects the hash algorithm (MD5, SHA256, SHA512).
    For each word, the hash is calculated and stored in the database if not already present. Returns a list of objects with the word, its hash, and status.

    @param file Uploaded text file (UploadFile).
    @param algorithm Hash algorithm to use (str).
    @param db Database session.
    @return List of cards with word, hash, and status.
    '''
    service = HashService(db)
    content = await file.read()
    try:
        text = content.decode("utf-8")
    except UnicodeDecodeError:
        text = content.decode("latin1")
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    results = []
    allowed = {"MD5", "SHA256", "SHA512"}
    if algorithm not in allowed:
        raise HTTPException(status_code=400, detail=f"Algoritmo no soportado: {algorithm}")
    for idx, palabra in enumerate(lines, 1):
        try:
            hashed = service.hash_phrase(palabra, algorithm)
            # Comprobar si ya existe en la BBDD
            existe = service.repo.get_original_by_hash(hashed, HashAlgorithm(algorithm))
            if existe is not None:
                results.append({
                    "line": idx,
                    "palabra": palabra,
                    "hash": hashed,
                    "algorithm": algorithm,
                    "status": "Hash ya almacenado en el sistema"
                })
            else:
                service.repo.save_hash(palabra, hashed, HashAlgorithm(algorithm))
                results.append({
                    "line": idx,
                    "palabra": palabra,
                    "hash": hashed,
                    "algorithm": algorithm,
                    "status": "Hash insertado correctamente"
                })
        except Exception as e:
            results.append({
                "line": idx,
                "palabra": palabra,
                "hash": None,
                "algorithm": algorithm,
                "error": str(e),
                "status": "Error al insertar"
            })
    return {
        "resultados": results,
        "total": len(lines),
        "success": sum(1 for r in results if r.get("status") == "Hash insertado correctamente"),
        "existentes": sum(1 for r in results if r.get("status") == "Hash ya almacenado en el sistema"),
        "errores": sum(1 for r in results if r.get("status") == "Error al insertar")
    }

@router.post("/upload-hash-file")
async def upload_hash_file(file: UploadFile = File(...), db: Session = Depends(get_db)):
    '''
    @brief Endpoint to upload a file with word and hash per line (drag & drop).

    Allows uploading a txt file where each line contains a word and its hash, separated by comma, space or tab.
    Automatically detects the hash type and stores each entry in the database.

    @param file Uploaded file (UploadFile).
    @param db Database session.
    @return Summary of processed lines and errors.
    '''
    service = HashService(db)
    content = await file.read()
    # Intentar decodificar como utf-8, si falla usar latin1
    try:
        text = content.decode("utf-8")
    except UnicodeDecodeError:
        text = content.decode("latin1")
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    resultados = []
    for idx, line in enumerate(lines, 1):
        for sep in [',', '\t', ' ', ':']:
            if sep in line:
                parts = line.split(sep)
                break
        else:
            resultados.append({"line": idx, "palabra": None, "hash": None, "hash_type": None, "status": "Formato no válido"})
            continue
        if len(parts) < 2:
            resultados.append({"line": idx, "palabra": None, "hash": None, "hash_type": None, "status": "Formato no válido"})
            continue
        palabra = parts[0].strip()
        hashval = parts[1].strip()
        from app.services.hashed.bruteforce_utils import detect_hash_type
        hash_type = detect_hash_type(hashval)
        if not hash_type:
            resultados.append({"line": idx, "palabra": palabra, "hash": hashval, "hash_type": None, "status": "Tipo de hash desconocido"})
            continue
        # Comprobar si ya existe
        existe = service.repo.get_original_by_hash(hashval, HashAlgorithm(hash_type))
        if existe is not None:
            resultados.append({"line": idx, "palabra": palabra, "hash": hashval, "hash_type": hash_type, "status": "Hash ya almacenado en el sistema"})
            continue
        try:
            service.repo.save_hash(palabra, hashval, HashAlgorithm(hash_type))
            resultados.append({"line": idx, "palabra": palabra, "hash": hashval, "hash_type": hash_type, "status": "Hash insertado correctamente"})
        except Exception:
            resultados.append({"line": idx, "palabra": palabra, "hash": hashval, "hash_type": hash_type, "status": "Error al insertar"})
    return JSONResponse(content={
        "resultados": resultados,
        "total": len(lines),
        "success": sum(1 for r in resultados if r["status"] == "Hash insertado correctamente"),
        "existentes": sum(1 for r in resultados if r["status"] == "Hash ya almacenado en el sistema"),
        "errores": sum(1 for r in resultados if r["status"] not in ["Hash insertado correctamente", "Hash ya almacenado en el sistema"])
    })

@router.post("/unhash-file", response_model=MultiUnhashFileResponse)
async def unhash_file(file: UploadFile = File(...), db: Session = Depends(get_db)):
    '''
    @brief Endpoint to unhash hashes from a file (one per line, drag & drop).

    Processes a text file with hashes (one per line), applies a timeout of 5 minutes per hash.
    Returns the results in the same format as the multi-unhash endpoint.

    @param file Uploaded file (UploadFile).
    @param db Database session.
    @return List of unhash results per hash.
    '''
    service = HashService(db)
    # Leer el archivo como texto
    content = await file.read()
    # Intentar decodificar como utf-8, si falla usar latin1
    try:
        text = content.decode("utf-8")
    except UnicodeDecodeError:
        text = content.decode("latin1")
    hashes = [h.strip() for h in text.splitlines() if h.strip()]
    import asyncio
    results = []
    found_lines = []
    # Procesar los hashes de manera secuencial, con timeout de 60s por hash
    for h in hashes:
        import concurrent.futures
        loop = asyncio.get_running_loop()
        t0 = time.time()
        try:
            res = await asyncio.wait_for(
                loop.run_in_executor(None, lambda: service.unhash([h], max_len=20, timeout=60)),
                timeout=65
            )
        except asyncio.TimeoutError:
            res = [{"hash": h, "original": None, "type": None, "found": False, "method": "bruteforce", "count": 0, "timeout": True}]
        t1 = time.time()
        for r in res:
            if (t1 - t0) > 60:
                r["timeout"] = True
            if r.get("found") and r.get("original"):
                found_lines.append(f"{r['hash']} {r['original']}")
        results.extend(res)
    # Generar archivo txt solo con los encontrados
    from fastapi.responses import JSONResponse
    from fastapi.encoders import jsonable_encoder
    import base64
    txt_content = "\n".join(found_lines)
    txt_b64 = base64.b64encode(txt_content.encode("utf-8")).decode("ascii")
    # Devolver JSON con resultados y archivo en base64
    return JSONResponse(content={
        "results": jsonable_encoder(results),
        "found_file_b64": txt_b64,
        "found_file_name": "hashes_encontrados.txt"
    })
