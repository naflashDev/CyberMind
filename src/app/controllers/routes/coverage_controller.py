"""
@file coverage_controller.py
@author naflashDev
@brief Controlador para servir el informe de cobertura HTML.
@details Este archivo expone un endpoint FastAPI que permite acceder al informe de cobertura generado por las pruebas automatizadas, devolviendo el archivo HTML principal si existe.
"""
from fastapi import APIRouter, Response
from fastapi.responses import FileResponse
import os

router = APIRouter()

COVERAGE_HTML_INDEX = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../htmlcov/index.html'))

@router.get('/coverage/html')
def get_coverage_html():
    '''
    @brief Serve the HTML coverage report main page.
    @return HTML file response for the coverage report, or 404 if not found.
    '''
    if os.path.exists(COVERAGE_HTML_INDEX):
        return FileResponse(COVERAGE_HTML_INDEX, media_type='text/html')
    return Response(status_code=404, content='Coverage report not found.')
