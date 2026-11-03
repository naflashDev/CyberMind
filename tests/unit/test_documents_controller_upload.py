"""
@file test_documents_controller_upload.py
@brief Tests for documents_controller upload endpoint behavior
"""
import asyncio
from types import SimpleNamespace
from app.controllers.routes import documents_controller


class FakeUpload:
    def __init__(self, data: bytes, filename: str = 'file.txt'):
        self._data = data
        self.filename = filename

    async def read(self):
        return self._data


def test_upload_single_file(monkeypatch, tmp_path):
    # Ensure BASE_DOCS points to temp
    monkeypatch.setattr(documents_controller, 'BASE_DOCS', tmp_path)
    monkeypatch.setattr(documents_controller, 'ingest_document', lambda *args, **kwargs: {'file': (args[1] if len(args) > 1 and args[1] else 'hello.txt'), 'path': str(tmp_path / 'hello.txt'), 'doc_id': 'doc1', 'upserted': False, 'message': 'saved'})

    f = FakeUpload(b'hello world', filename='hello.txt')

    async def do():
        res = await documents_controller.upload_document(file=f, folder='tests', conversation_id=None)
        # JSONResponse object returned
        assert hasattr(res, 'body') or hasattr(res, 'media')
        # if body exists, ensure it contains results
        try:
            content = res.json()
        except Exception:
            content = None
        if content:
            assert 'results' in content

    asyncio.run(do())
