"""
@file documents_controller.py
@author naflashDev
@brief Rutas para ingestión de documentos usados por el LLM
@details Define endpoints para subir documentos que serán indexados por el vectorstore y usados como fuente por el LLM.
"""
from fastapi import APIRouter, UploadFile, File, HTTPException, Form
from fastapi.responses import JSONResponse
from loguru import logger
import asyncio

from app.services.documents.ingest import ingest_document
from pathlib import Path
from typing import List

BASE_DOCS = Path('data') / 'documents'


def _list_folders() -> List[dict]:
    BASE_DOCS.mkdir(parents=True, exist_ok=True)
    res = []
    for p in sorted([x for x in BASE_DOCS.iterdir() if x.is_dir()], key=lambda x: x.name):
        res.append({'name': p.name, 'path': str(p.as_posix())})
    return res

router = APIRouter(prefix="/documents", tags=["Documents"])


@router.post('/upload')
async def upload_document(
    file: list[UploadFile] | UploadFile = File(...),
    folder: str | None = Form(None),
    conversation_id: int | None = Form(None),
):
    '''
    @brief Endpoint para subir un documento (ZIP, txt, md, json, pdf).

    Guarda el archivo en disco bajo `data/documents/{folder}` (si se proporciona) y llama al servicio
    de ingestión que normaliza el texto y lo sube al vectorstore. Devuelve metadatos del documento.

    @param file Archivo subido (UploadFile).
    @param folder Nombre de carpeta destino (opcional).
    @param conversation_id Id de la conversación a la que se asocia (opcional).
    @return JSON con información del documento indexado.
    '''
    # Support single upload or multiple files
    files = []
    if isinstance(file, list):
        files = file
    else:
        files = [file]

    if not files:
        raise HTTPException(status_code=400, detail='No file uploaded')

    results = []
    try:
        for f in files:
            content = await f.read()
            # Run ingest in thread to avoid blocking
            result = await asyncio.to_thread(ingest_document, content, getattr(f, 'filename', None), folder, conversation_id)
            results.append(result)
        return JSONResponse(content={'results': results})
    except ValueError as ve:
        logger.error(f"Validation error in upload_document: {ve}")
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        logger.exception('Error in upload_document')
        raise HTTPException(status_code=500, detail='Internal server error during document upload')


@router.get('/folders')
async def list_folders():
    """List existing document folders under data/documents"""
    try:
        return JSONResponse(content={'folders': _list_folders()})
    except Exception:
        logger.exception('Error listing folders')
        raise HTTPException(status_code=500, detail='Error listing folders')


@router.post('/folders')
async def create_folder(name: str):
    """Folder creation endpoint removed.

    This operation is disabled by project policy. Return 405 Method Not Allowed.
    """
    raise HTTPException(status_code=405, detail='Folder creation is disabled')
