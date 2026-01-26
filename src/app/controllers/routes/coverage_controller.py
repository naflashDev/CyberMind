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
        # Modificar el HTML: eliminar <link rel="stylesheet"> y añadir el de la UI
        soup = BeautifulSoup(html, 'html.parser')
        # Eliminar todos los <link rel="stylesheet">
        for link in soup.find_all('link', rel='stylesheet'):
            link.decompose()
        # Añadir el CSS de la UI
        head = soup.head
        if head:
            ui_css = soup.new_tag('link', rel='stylesheet', href='/ui/styles.css')
            head.append(ui_css)
        # Opcional: eliminar estilos <style> embebidos del coverage
        for style in soup.find_all('style'):
            style.decompose()
        # Opcional: eliminar favicon del coverage
        for link in soup.find_all('link', rel='icon'):
            link.decompose()
        return HTMLResponse(str(soup))
    except Exception as e:
        return Response(status_code=500, content=f'Error procesando el informe de cobertura: {e}')
