"""
@file test_controllers_llm.py
@author naflashDev
@brief Unit tests for llm_controller endpoints.
@details Tests FastAPI endpoints for LLM query and updater, including client patching and response validation.
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
from app.controllers.routes.llm_controller import router as llm_router

class TestLLMController(unittest.TestCase):
    def setUp(self):
        app = FastAPI()
        app.include_router(llm_router)
        self.client = TestClient(app)

    def test_llm_query_uses_client(self):
        with mock.patch('app.controllers.routes.llm_controller.query_llm', return_value='ok'):
            resp = self.client.post('/llm/query', json={'prompt':'hello'})
            self.assertEqual(resp.status_code, 200)
            self.assertEqual(resp.json()['response'], 'ok')

if __name__ == '__main__':
    unittest.main()
