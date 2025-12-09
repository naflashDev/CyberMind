import unittest

from app.services.spacy import text_processor


class TestTextProcessorModelsAlias(unittest.TestCase):
    def test_models_alias_exists(self):
        """Ensure the module exposes `models` (alias for internal `_models`)."""
        self.assertTrue(hasattr(text_processor, "models"), "text_processor should expose `models` alias")
        # The public alias should reference the same dict object
        self.assertIs(text_processor.models, text_processor._models)


if __name__ == "__main__":
    unittest.main()
