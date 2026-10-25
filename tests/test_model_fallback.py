import os
import unittest

from tailor import get_model_candidates


class TestGroqModelSelection(unittest.TestCase):
    def test_default_candidates_include_fallbacks(self):
        models = get_model_candidates()
        self.assertIn("openai/gpt-oss-120b", models)
        self.assertIn("openai/gpt-oss-20b", models)

    def test_environment_override_is_first(self):
        old_value = os.environ.get("GROQ_MODEL")
        os.environ["GROQ_MODEL"] = "custom-model"
        try:
            self.assertEqual(get_model_candidates()[0], "custom-model")
        finally:
            if old_value is None:
                os.environ.pop("GROQ_MODEL", None)
            else:
                os.environ["GROQ_MODEL"] = old_value


if __name__ == "__main__":
    unittest.main()
