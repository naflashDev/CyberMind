"""
@file test_worker_controller.py
@author naflashDev
@brief Unit tests for worker_controller toggle behavior
@details Ensure unknown worker names return 404.
"""
import asyncio

from fastapi import HTTPException

from app.controllers.routes import worker_controller


class DummyRequest:
    def __init__(self):
        class AppState:
            pass
        self.app = types.SimpleNamespace(state=types.SimpleNamespace())


def test_toggle_worker_unknown(monkeypatch):
    '''
    @brief toggle_worker should raise HTTPException for unknown worker names.
    '''
    # Ensure load_worker_settings returns empty dict
    import types
    monkeypatch.setattr(worker_controller, 'load_worker_settings', lambda: {})

    # Create a dummy request
    req = types.SimpleNamespace()
    req.app = types.SimpleNamespace(state=types.SimpleNamespace())

    # Prepare payload type
    payload = types.SimpleNamespace(enabled=True)

    async def call():
        try:
            await worker_controller.toggle_worker('nonexistent', payload, req)
        except HTTPException as he:
            return he
        return None

    he = asyncio.run(call())
    assert he is not None
    assert he.status_code == 404
