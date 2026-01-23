"""
@file test_services_text_processor.py
@author naflashDev
@brief Unit tests for text_processor service helpers.
@details Tests helper functions and logic in the text_processor service layer, including entity extraction and language detection.
"""
import sys
from pathlib import Path
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
SRC = str(ROOT / 'src')
if SRC not in sys.path:
    sys.path.insert(0, SRC)

from app.services.spacy import text_processor as tp

class TestTextProcessor(unittest.TestCase):
    def test_detect_language_and_tag_text(self):
        # mock langdetect.detect
        with mock.patch('app.services.spacy.text_processor.detect', return_value='en'):
            fake_model = mock.Mock()
            fake_doc = mock.Mock()
            fake_ent = mock.Mock()
            fake_ent.text = 'X'
            fake_ent.label_ = 'ORG'
            fake_doc.ents = [fake_ent]
            fake_model.return_value = fake_doc
            # patch models dict to use fake_model
            with mock.patch.dict('app.services.spacy.text_processor.models', {'en': fake_model}):
                tags, lang = tp.tag_text('Hello world')
                self.assertEqual(lang, 'en')
                self.assertIsInstance(tags, list)

    def test_extract_texts(self):
        data = {'title':'T','h1':['a',''], 'p':['p1','p2']}
        texts = tp.extract_texts(data)
        self.assertIn('T', texts)
        self.assertIn('p1', texts)

if __name__ == '__main__':
    unittest.main()
