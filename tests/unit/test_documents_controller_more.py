"""
@file test_documents_controller_more.py
@brief Extra tests for documents_controller
"""
import asyncio
from fastapi import HTTPException
from app.controllers.routes import documents_controller


def test_create_folder_disabled():
    import pytest
    with pytest.raises(HTTPException) as exc:
        asyncio.run(documents_controller.create_folder('x'))
    assert exc.value.status_code == 405
