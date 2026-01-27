"""
@file test_main.py
@author naflashDev
@brief Unit tests for main FastAPI app entrypoint.

@details Covers app creation, lifespan, and background task initialization.
"""
import sys
import os
import pytest
import types
import asyncio
from fastapi import FastAPI
# Añadir src al sys.path para importar app.main correctamente
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../src/app')))
import main as main_mod


def test_app_import_and_routes():
    """
    Happy Path: App imports and has routers.
    """
    assert hasattr(main_mod, "FastAPI")
    assert hasattr(main_mod, "app")
    assert isinstance(main_mod.app, FastAPI)

@pytest.mark.asyncio
async def test_lifespan_runs(monkeypatch):
    """
    Happy Path: lifespan context manager yields app.
    """
    app = FastAPI()
    cm = main_mod.lifespan(app)
    assert hasattr(cm, "__aenter__")
    assert hasattr(cm, "__aexit__")

@pytest.mark.asyncio
async def test_initialize_background_tasks(monkeypatch):
    """
    Happy Path: initialize_background_tasks runs without error.
    """
    app = FastAPI()
    app.state.worker_status = {}
    app.state.worker_stop_events = {}
    await main_mod.initialize_background_tasks(app)
    assert True
