import pytest


class DummyUpload:
    def __init__(self, data=b'print("hi")', filename='test.py'):
        self._data = data
        self.filename = filename
        self.content_type = 'text/x-python'

    async def read(self):
        return self._data


def test_scan_code_file_with_dummy(monkeypatch):
    from app.controllers.routes import code_analysis_controller

    class DummyScanner:
        def scan_uploaded_file(self, b, fn):
            return {"vulnerabilities": [], "vulnerabilities_full": [], "llm_enabled": False, "pdf_base64": None}

    monkeypatch.setattr(code_analysis_controller, 'CodeScanner', DummyScanner)

    dummy = DummyUpload()
    # call the async endpoint manually
    import asyncio
    # Use asyncio.run to create and run a new event loop for the coroutine
    res = asyncio.run(code_analysis_controller.scan_code_file(dummy))
    assert hasattr(res, 'status_code') and res.status_code == 200
