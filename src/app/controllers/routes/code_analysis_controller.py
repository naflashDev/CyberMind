"""
@file code_analysis_controller.py
@author naflashDev
@brief Rutas para el análisis de código fuente en busca de vulnerabilidades.
@details Define los endpoints para escanear código (texto o archivo) y devolver vulnerabilidades detectadas, integrando análisis heurístico y LLM.
"""

from fastapi import APIRouter, UploadFile, File, HTTPException, status, Depends
from fastapi.responses import JSONResponse
from loguru import logger
# Try importing CodeScanner using the 'src' package path (test environment),
# fall back to the plain 'app' package when not available.
try:
    from src.app.services.code_analysis.scanner import CodeScanner  # type: ignore
except Exception:
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
            # Generar PDF global solo si hay vulnerabilidades y preparar
            # la vista para la UI sin las explicaciones del LLM.
            pdf_b64 = scanner.generate_pdf_report(results) if results else None
        logger.debug("[scan-file] Análisis de ZIP completado.")
        ui_results = [{k: v for k, v in r.items() if k != 'explanation'} for r in results]
        content = {"vulnerabilities": ui_results, "vulnerabilities_full": results, "llm_enabled": llm_enabled, "pdf_base64": pdf_b64}
        return JSONResponse(content=content, status_code=200)
    else:
        try:
            logger.debug("[scan-file] Intentando leer el archivo subido...")
            content = (await file.read()).decode("utf-8", errors="ignore")
            logger.debug(f"[scan-file] Longitud del contenido leído: {len(content)}")
            scanner = CodeScanner()
            results = scanner.scan_text(content)
            llm_enabled = scanner.is_llm_enabled() if hasattr(scanner, 'is_llm_enabled') else False
            # Generate PDF including LLM explanations, but strip them from
            # the UI-visible payload so explanations only appear inside the PDF.
            pdf_b64 = scanner.generate_pdf_report(results) if results else None
            logger.debug("[scan-file] Análisis completado correctamente.")
            ui_results = [{k: v for k, v in r.items() if k != 'explanation'} for r in results]
            content = {"vulnerabilities": ui_results, "vulnerabilities_full": results, "llm_enabled": llm_enabled, "pdf_base64": pdf_b64}
            return JSONResponse(content=content, status_code=200)
        except Exception as e:
            logger.error(f"Error in scan_code_file: {e}")
            return JSONResponse(content={"detail": "Error interno en el análisis de archivo."}, status_code=500)
            
    # end scan_code_file


@router.post("/code/generate-pdf", tags=["Code Analysis"])
async def generate_pdf_from_vulns(payload: Dict[str, Any] = Body(...)):
    '''
    @brief Genera un PDF a partir de una lista de vulnerabilidades enviada por el cliente.

    Esto permite que la UI solicite explícitamente la generación del PDF cuando el
    endpoint principal no lo devuelva en la respuesta (por ejemplo, por limitaciones
    o para generar el PDF on-demand).

    @param payload Diccionario con la clave 'vulnerabilities' que contiene la lista.
    @return JSON con 'pdf_base64' o error.
    '''
    try:
        vulns = payload.get('vulnerabilities')
        if not isinstance(vulns, list):
            return JSONResponse(content={"detail": "El campo 'vulnerabilities' debe ser una lista."}, status_code=400)
        scanner = CodeScanner()
        pdf_b64 = scanner.generate_pdf_report(vulns) if vulns else None
        return JSONResponse(content={"pdf_base64": pdf_b64}, status_code=200)
    except Exception as e:
        logger.error(f"Error generating PDF from vulns: {e}")
        return JSONResponse(content={"detail": "Error generando PDF."}, status_code=500)


