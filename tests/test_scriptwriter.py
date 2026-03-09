"""
tests/test_scriptwriter.py — Unit tests for src/scriptwriter.py

Tests the template-based script generator with no external API calls.
Run with: python -m pytest tests/ -v
"""

import unittest

import sys
from unittest.mock import MagicMock

# Stub heavy optional imports not needed for scriptwriter tests
for mod in ("edge_tts", "gtts", "moviepy", "moviepy.editor",
            "PIL", "PIL.Image", "PIL.ImageDraw", "PIL.ImageFont",
            "pydub", "mutagen", "mutagen.mp3",
            "googleapiclient", "googleapiclient.discovery"):
    sys.modules.setdefault(mod, MagicMock())


class TestGenerateScript(unittest.TestCase):
    """Tests for scriptwriter.generate_script()."""

    def setUp(self):
        from src.scriptwriter import generate_script
        self.generate_script = generate_script

    def test_returns_required_keys(self):
        """Result must contain all keys that pipeline.py depends on."""
        result = self.generate_script("AI advancements")
        required_keys = {"title", "script", "caption_script", "hook", "scenes", "tags", "description"}
        self.assertEqual(required_keys, required_keys & result.keys(),
                         f"Missing keys: {required_keys - result.keys()}")

    def test_title_is_non_empty_string(self):
        result = self.generate_script("climate change")
        self.assertIsInstance(result["title"], str)
        self.assertTrue(result["title"].strip(), "title must not be blank")

    def test_title_max_100_chars(self):
        """YouTube limits titles to 100 characters."""
        result = self.generate_script("a very long topic name " * 5)
        self.assertLessEqual(len(result["title"]), 100,
                             "title exceeds 100-character YouTube limit")

    def test_script_is_non_empty_string(self):
        result = self.generate_script("space exploration")
        self.assertIsInstance(result["script"], str)
        self.assertTrue(result["script"].strip(), "script must not be blank")

    def test_script_has_no_ssml_tags(self):
        """TTS receives the script — it must be plain text with no SSML markup."""
        result = self.generate_script("quantum computing")
        script = result["script"]
        self.assertNotIn("<speak", script, "script must not contain SSML <speak> tag")
        self.assertNotIn("<voice", script, "script must not contain SSML <voice> tag")
        self.assertNotIn("<prosody", script, "script must not contain SSML <prosody> tag")

    def test_tags_is_list_of_strings(self):
        result = self.generate_script("electric vehicles")
        tags = result["tags"]
        self.assertIsInstance(tags, list)
        self.assertTrue(all(isinstance(t, str) for t in tags),
                        "all tags must be strings")

    def test_scenes_is_non_empty_list(self):
        result = self.generate_script("machine learning")
        scenes = result["scenes"]
        self.assertIsInstance(scenes, list)
        self.assertGreater(len(scenes), 0, "scenes list must not be empty")

    def test_description_is_string(self):
        result = self.generate_script("cryptocurrency")
        self.assertIsInstance(result["description"], str)

    def test_hook_is_non_empty_string(self):
        result = self.generate_script("social media trends")
        self.assertIsInstance(result["hook"], str)
        self.assertTrue(result["hook"].strip(), "hook must not be blank")

    def test_deterministic_structure(self):
        """Two calls with the same topic must both return all required keys."""
        r1 = self.generate_script("renewable energy")
        r2 = self.generate_script("renewable energy")
        self.assertEqual(set(r1.keys()), set(r2.keys()))

    def test_various_topics_do_not_raise(self):
        """Scriptwriter must handle a variety of topics without crashing."""
        topics = [
            "How to be alone",
            "Bitcoin hits new high",
            "NASA Mars mission",
            "Top 10 Python tips",
            "Ask HN: Career advice",
            "",          # empty topic — should not crash
            "  spaces  ",
        ]
        for topic in topics:
            with self.subTest(topic=topic):
                try:
                    result = self.generate_script(topic)
                    self.assertIn("title", result)
                except Exception as exc:
                    self.fail(f"generate_script({topic!r}) raised unexpectedly: {exc}")


class TestCaptionScript(unittest.TestCase):
    """Tests for the caption_script field used by video_creator."""

    def test_caption_script_is_string(self):
        from src.scriptwriter import generate_script
        result = generate_script("health tips")
        self.assertIsInstance(result["caption_script"], str)

    def test_caption_script_no_markup(self):
        """caption_script is rendered as subtitle text — must be plain."""
        from src.scriptwriter import generate_script
        result = generate_script("fitness motivation")
        cap = result["caption_script"]
        self.assertNotIn("<", cap, "caption_script must not contain HTML/XML tags")
        self.assertNotIn(">", cap, "caption_script must not contain HTML/XML tags")


if __name__ == "__main__":
    unittest.main()
