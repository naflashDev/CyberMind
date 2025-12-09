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


class TestIntegrationLLMFlow(unittest.TestCase):
    def setUp(self):
        app = FastAPI()
        app.include_router(llm_router)
        self.client = TestClient(app)

    def test_llm_query_end_to_end(self):
        # Patch the lower-level client to return a known answer
        with mock.patch('app.controllers.routes.llm_controller.query_llm', return_value='integrated-answer'):
            resp = self.client.post('/llm/query', json={'prompt': 'Tell me a joke'})
            self.assertEqual(resp.status_code, 200)
            data = resp.json()
            self.assertIn('response', data)
            self.assertEqual(data['response'], 'integrated-answer')


if __name__ == '__main__':
    unittest.main()
