"""
@file code_analysis_controller.py
@author naflashDev
@brief Rutas para el análisis de código fuente en busca de vulnerabilidades.
@details Define los endpoints para escanear código (texto o archivo) y devolver vulnerabilidades detectadas, integrando análisis heurístico y LLM.
"""

from fastapi import APIRouter, UploadFile, File, HTTPException, status, Depends
from fastapi.responses import JSONResponse
from loguru import logger
from app.services.code_analysis.scanner import CodeScanner
from typing import Any, Dict
import base64
from fastapi import Body

router = APIRouter()

@router.post("/code/scan-text", tags=["Code Analysis"])
async def scan_code_text(payload: Dict[str, Any]):
    '''
    @brief Analiza un fragmento de código recibido como texto.

    Recibe un JSON con el campo 'code' y devuelve las vulnerabilidades encontradas y un informe PDF.

    @param payload Diccionario con el campo 'code' (str).
    @return JSON con lista de vulnerabilidades y PDF en base64.
    '''
    code = payload.get("code")
    if not code or not isinstance(code, str):
        logger.warning("Invalid code input for scan-text endpoint.")
        raise HTTPException(status_code=400, detail="El campo 'code' es obligatorio y debe ser texto.")
    try:
        scanner = CodeScanner()
        results = scanner.scan_text(code)
        llm_enabled = scanner.is_llm_enabled() if hasattr(scanner, 'is_llm_enabled') else False
        # Keep full results for PDF generation (include LLM explanations).
        # Return a UI-friendly copy without 'explanation' and also include
        # the full results under 'vulnerabilities_full' so the UI can request
        # a PDF containing the LLM explanations on-demand.
        pdf_b64 = scanner.generate_pdf_report(results) if results else None
        ui_results = []
        for r in results:
            ui_results.append({k: v for k, v in r.items() if k != 'explanation'})
        content = {"vulnerabilities": ui_results, "vulnerabilities_full": results, "llm_enabled": llm_enabled, "pdf_base64": pdf_b64}
        return JSONResponse(content=content, status_code=200)
    except ValueError as ve:
        logger.error(f"Error de validación en scan_code_text: {ve}")
        raise HTTPException(status_code=400, detail=f"Error de validación: {ve}")
    except Exception as e:
        logger.error(f"Error in scan_code_text: {e}")
        raise HTTPException(status_code=500, detail="Error interno en el análisis de código.")

@router.post("/code/scan-file", tags=["Code Analysis"])
async def scan_code_file(file: UploadFile = File(None)):
    '''
    @brief Analiza un archivo de código subido por el usuario.

    Recibe un archivo y devuelve las vulnerabilidades encontradas y un informe PDF.

    @param file Archivo subido (UploadFile).
    @return JSON con lista de vulnerabilidades y PDF en base64.
    '''
    # --- LOGS DE DEPURACIÓN PARA UPLOADS (reducidos) ---
    logger.debug(f"[scan-file] Petición recibida. file: {file}")
    if file:
        logger.debug(f"[scan-file] file.filename: {getattr(file, 'filename', None)}")
        logger.debug(f"[scan-file] file.content_type: {getattr(file, 'content_type', None)}")
    else:
        logger.warning("[scan-file] file es None")

    if not file:
        logger.warning("No file uploaded to scan-file endpoint.")
        raise HTTPException(status_code=400, detail="No se ha subido ningún archivo.")
    # Minimal endpoint: read bytes and delegate processing to the CodeScanner service
    try:
        file_bytes = await file.read()
        scanner = CodeScanner()
        response = scanner.scan_uploaded_file(file_bytes, getattr(file, 'filename', None))
        return JSONResponse(content=response, status_code=200)
    except ValueError as ve:
        logger.error(f"Validation error in scan_code_file: {ve}")
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        logger.error(f"Error in scan_code_file: {e}")
        return JSONResponse(content={"detail": "Error interno en el análisis de archivo."}, status_code=500)
            
    # end scan_code_file





