"""
@file coverage_controller.py
@author naflashDev
@brief Controlador para servir el informe de cobertura HTML.
@details Este archivo expone un endpoint FastAPI que permite acceder al informe de cobertura generado por las pruebas automatizadas, devolviendo el archivo HTML principal si existe.
"""

from fastapi import APIRouter, Response
from fastapi.responses import HTMLResponse
import os

from bs4 import BeautifulSoup

router = APIRouter()

COVERAGE_HTML_INDEX = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../htmlcov/index.html'))


@router.get('/coverage/html')
def get_coverage_html():
    '''
    @brief Serve the HTML coverage report main page with UI CSS.

    Reads the generated coverage HTML, removes its own CSS, and injects the UI CSS for a unified look.

    @return HTML file response for the coverage report, or 404 if not found.
    '''
    if not os.path.exists(COVERAGE_HTML_INDEX):
        return Response(status_code=404, content='Coverage report not found.')

    try:
        with open(COVERAGE_HTML_INDEX, encoding='utf-8') as f:
            html = f.read()
        try:
            from bs4 import BeautifulSoup
        except ImportError:
            return Response(status_code=500, content='BeautifulSoup4 no está instalado. Añádelo a requirements.txt.')
        # Modificar el HTML: eliminar <link rel="stylesheet"> y añadir el de la UI
        soup = BeautifulSoup(html, 'html.parser')
        for link in soup.find_all('link', rel='stylesheet'):
            link.decompose()
        head = soup.head
        if head:
            ui_css = soup.new_tag('link', rel='stylesheet', href='/ui/styles.css')
            head.append(ui_css)
        for style in soup.find_all('style'):
            style.decompose()
        for link in soup.find_all('link', rel='icon'):
            link.decompose()
        # Siempre devolver como HTML
        return HTMLResponse(str(soup), media_type='text/html')
    except Exception as e:
        # Generic error message for UI, no internal details
        return Response(status_code=500, content='Ha ocurrido un error interno. Por favor, contacte con el administrador.', media_type='text/html')
