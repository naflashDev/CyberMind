"""
@file test_services_llm.py
@author naflashDev
@brief Unit tests for LLM service helpers.
@details Tests helper functions and logic in the LLM service layer, including prompt handling and model selection.
"""
import sys
from pathlib import Path
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
SRC = str(ROOT / 'src')
if SRC not in sys.path:
    sys.path.insert(0, SRC)

from app.services.llm import llm_client, llm_trainer

class TestLLMClient(unittest.TestCase):
    def test_query_llm_success(self):
        fake_resp = mock.Mock()
        fake_resp.json.return_value = {'message': {'content': 'answer'}}
        fake_resp.raise_for_status.return_value = None
        with mock.patch('requests.post', return_value=fake_resp):
            res = llm_client.query_llm('hi')
            self.assertEqual(res, 'answer')

    def test_query_llm_failure(self):
        with mock.patch('requests.post', side_effect=Exception('no')):
            res = llm_client.query_llm('hi')
            self.assertTrue(res.startswith('Error'))

class TestLLMTrainer(unittest.TestCase):
    def test_run_periodic_training_calls_steps(self):
        with mock.patch('app.services.llm.llm_trainer.update_cve_repo') as up_mock:
            with mock.patch('app.services.llm.llm_trainer.prepare_dataset') as prep_mock:
                llm_trainer.run_periodic_training()
                up_mock.assert_called()
                prep_mock.assert_called()

if __name__ == '__main__':
    unittest.main()
