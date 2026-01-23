"""
@file test_controllers_spacy.py
@author naflashDev
@brief Unit tests for spacy_controller endpoints.
@details Tests FastAPI endpoints for spaCy entity extraction, patching file existence and background threads, and validating responses.
"""
import sys
from pathlib import Path
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
SRC = str(ROOT / 'src')
if SRC not in sys.path:
    sys.path.insert(0, SRC)

from fastapi.testclient import TestClient
from fastapi import FastAPI
import threading

from app.controllers.routes.spacy_controller import router as spacy_router

class TestSpacyController(unittest.TestCase):
    def setUp(self):
        app = FastAPI()
        app.include_router(spacy_router)
        self.client = TestClient(app)

    def test_start_spacy_missing_file(self):
        with mock.patch('os.path.exists', return_value=False):
            resp = self.client.get('/start-spacy')
            self.assertEqual(resp.status_code, 404)

    def test_start_spacy_starts_thread(self):
        with mock.patch('os.path.exists', return_value=True):
            with mock.patch('app.controllers.routes.spacy_controller.threading.Thread') as ThreadMock:
                resp = self.client.get('/start-spacy')
                self.assertEqual(resp.status_code, 200)
                ThreadMock.assert_called()

if __name__ == '__main__':
    unittest.main()
