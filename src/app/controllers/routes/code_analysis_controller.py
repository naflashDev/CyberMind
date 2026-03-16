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
        pdf_b64 = scanner.generate_pdf_report(results) if results else None
        return {"vulnerabilities": results, "llm_enabled": llm_enabled, "pdf_base64": pdf_b64}
    except ValueError as ve:
        logger.error(f"Error de validación en scan_code_text: {ve}")
        raise HTTPException(status_code=400, detail=f"Error de validación: {ve}")
    except Exception as e:
        logger.error(f"Error in scan_code_text: {e}")
        raise HTTPException(status_code=500, detail="Error interno en el análisis de código.")

@router.post("/code/scan-file", tags=["Code Analysis"])
async def scan_code_file(file: UploadFile = File(...)):
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
    if not file.filename.endswith((".py", ".js", ".java", ".c", ".cpp", ".rb", ".go", ".zip")):
        logger.warning(f"Unsupported file type: {file.filename}")
        raise HTTPException(status_code=415, detail="Tipo de archivo no soportado.")
    import zipfile, tempfile, os
    results = []
    pdf_b64 = None
    llm_enabled = False
    if file.filename.endswith('.zip'):
        logger.debug("[scan-file] Archivo ZIP recibido. Procesando...")
        with tempfile.NamedTemporaryFile(delete=False, suffix='.zip') as tmp_zip:
            tmp_zip.write(await file.read())
            tmp_zip_path = tmp_zip.name
        with zipfile.ZipFile(tmp_zip_path, 'r') as zip_ref:
            extract_dir = tempfile.mkdtemp()
            zip_ref.extractall(extract_dir)
            logger.debug(f"[scan-file] ZIP extraído en: {extract_dir}")
            # Recorrer archivos extraídos y analizar los de código soportados
            extensiones = ('.py', '.js', '.java', '.c', '.cpp', '.rb', '.go')
            scanner = CodeScanner()
            llm_enabled = scanner.is_llm_enabled() if hasattr(scanner, 'is_llm_enabled') else False
            for root, _, files in os.walk(extract_dir):
                for fname in files:
                    if fname.endswith(extensiones):
                        fpath = os.path.join(root, fname)
                        logger.debug(f"[scan-file] Analizando archivo en ZIP: {fpath}")
                        with open(fpath, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read()
                        try:
                            res = scanner.scan_text(content)
                            # Añadir nombre de archivo a cada vulnerabilidad
                            for v in res:
                                v['filename'] = fname
                            results.extend(res)
                        except Exception as e:
                            logger.error(f"[scan-file] Error analizando {fname}: {e}")
            # Generar PDF global solo si hay vulnerabilidades
            pdf_b64 = scanner.generate_pdf_report(results) if results else None
        logger.debug("[scan-file] Análisis de ZIP completado.")
        return {"vulnerabilities": results, "llm_enabled": llm_enabled, "pdf_base64": pdf_b64}
    else:
        try:
            logger.debug("[scan-file] Intentando leer el archivo subido...")
            content = (await file.read()).decode("utf-8", errors="ignore")
            logger.debug(f"[scan-file] Longitud del contenido leído: {len(content)}")
            scanner = CodeScanner()
            results = scanner.scan_text(content)
            llm_enabled = scanner.is_llm_enabled() if hasattr(scanner, 'is_llm_enabled') else False
            pdf_b64 = scanner.generate_pdf_report(results) if results else None
            logger.debug("[scan-file] Análisis completado correctamente.")
            return {"vulnerabilities": results, "llm_enabled": llm_enabled, "pdf_base64": pdf_b64}
        except Exception as e:
            logger.error(f"Error in scan_code_file: {e}")
            raise HTTPException(status_code=500, detail="Error interno en el análisis de archivo.")
