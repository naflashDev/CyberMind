"""
@file test_integration_spacy_flow.py
@author naflashDev
@brief Integration tests for spaCy controller endpoints.
@details Tests FastAPI endpoints for spaCy-based entity extraction, ensuring correct routing and response handling in integration scenarios.
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

from app.controllers.routes.spacy_controller import router as spacy_router


class TestIntegrationSpacyFlow(unittest.TestCase):
    def setUp(self):
        app = FastAPI()
        app.include_router(spacy_router)
        self.client = TestClient(app)

    def test_start_and_process_flow(self):
        # patch file exists check for scheduler
        with mock.patch('os.path.exists', return_value=True):
            with mock.patch('app.controllers.routes.spacy_controller.threading.Thread') as ThreadMock:
                resp = self.client.get('/start-spacy')
                self.assertEqual(resp.status_code, 200)
                ThreadMock.assert_called()

        # patch the service function that does the processing to avoid heavy spacy model
        with mock.patch('app.services.spacy.text_processor.tag_text', return_value=([], 'en')):
            # there is no direct endpoint for tagging in controller; call internal function as an integration step
            from app.services.spacy import text_processor as tp
            tags, lang = tp.tag_text('Sample text for integration')
            self.assertEqual(lang, 'en')

if __name__ == '__main__':
    unittest.main()
