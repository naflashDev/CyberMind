"""
@file test_documents_controller.py
@author naflashDev
@brief Unit tests for documents_controller
@details Tests the _list_folders helper.
"""
from pathlib import Path
import shutil

from app.controllers.routes import documents_controller


def test_list_folders(tmp_path):
    '''
    @brief _list_folders should return created directories under BASE_DOCS
    '''
    # Monkeypatch BASE_DOCS
    documents_controller.BASE_DOCS = tmp_path
    (tmp_path / 'alpha').mkdir()
    (tmp_path / 'beta').mkdir()

    res = documents_controller._list_folders()
    names = [r['name'] for r in res]
    assert 'alpha' in names
    assert 'beta' in names
