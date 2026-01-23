
"""
@file docs_controller.py
@author naflashDev
@brief FastAPI router to serve static documentation files via API.
@details Exposes endpoints to list and serve Markdown documentation files from the Docs directory and README.md for the UI.
"""


import os
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse, JSONResponse

router = APIRouter()

DOCS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../..', 'Docs'))
README_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../..', 'README.md'))


def list_docs_files():
    '''
    @brief Returns a list of documentation files available in the Docs directory.

    Scans the Docs directory for Markdown files and returns their filenames as a list.

    @return List of Markdown filenames (list[str]).
    '''
    try:
        files = [f for f in os.listdir(DOCS_DIR) if os.path.isfile(os.path.join(DOCS_DIR, f)) and f.endswith('.md')]
        return files
    except Exception as e:
        return []


@router.get('/docs/list')
def get_docs_list():
    '''
    @brief Endpoint to list all documentation files in the Docs directory.

    Calls list_docs_files() to retrieve the list of Markdown documentation files and returns them as a JSON response.

    @return JSONResponse containing the list of documentation filenames.
    '''
    files = list_docs_files()
    return JSONResponse(files)


@router.get('/docs/readme')
def get_readme():
    '''
    @brief Endpoint to get the README.md file content.

    Returns the README.md file as a FileResponse if it exists, otherwise raises a 404 error.

    @return FileResponse with README.md content or HTTPException if not found.
    '''
    if not os.path.exists(README_PATH):
        raise HTTPException(status_code=404, detail="README.md not found")
    return FileResponse(README_PATH, media_type='text/markdown', filename='README.md')


@router.get('/docs/file/{filename}')
def get_doc_file(filename: str):
    '''
    @brief Endpoint to get a specific documentation file from the Docs directory.

    Returns the requested Markdown file as a FileResponse if it exists in the Docs directory, otherwise raises a 404 error.

    @param filename Name of the documentation file to retrieve.
    @return FileResponse with the file content or HTTPException if not found.
    '''
    safe_path = os.path.join(DOCS_DIR, filename)
    if not os.path.exists(safe_path) or not safe_path.endswith('.md'):
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(safe_path, media_type='text/markdown', filename=filename)
