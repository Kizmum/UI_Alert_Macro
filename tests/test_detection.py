"""Offline recognition checks. Run after installation: python -m unittest discover -s tests."""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import cv2
import numpy as np
from ui_alert_macro_gui import (
    EVENTS, STANDARD_THRESHOLDS, TGSS_KEY, load_templates, load_legacy_templates,
    detect_event, detect_tgss_legacy, modern_tgss_score, tgss_is_suspected,
    CooldownTracker,
)


class RecognitionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.modern = load_templates()
        cls.legacy = load_legacy_templates()

    def test_all_twenty_modern_templates(self):
        self.assertEqual(sum(map(len, self.modern.values())), 20)
        for key, variants in self.modern.items():
            for variant in variants:
                with self.subTest(biome=key):
                    result = detect_event(variant['image'], self.modern, STANDARD_THRESHOLDS, set(EVENTS))
                    self.assertEqual(result.event_key, key)

    def test_legacy_tgss_original_frame(self):
        result = detect_tgss_legacy(self.legacy[TGSS_KEY], self.legacy)
        self.assertTrue(result.detected)
        self.assertGreaterEqual(result.tgss_score, 0.76)

    def test_legacy_does_not_alert_on_other_modern_templates(self):
        for key, variants in self.modern.items():
            if key == TGSS_KEY:
                continue
            for variant in variants:
                with self.subTest(biome=key):
                    self.assertFalse(detect_tgss_legacy(variant['image'], self.legacy).detected)

    def test_legacy_rejects_blank_and_noise(self):
        rng = np.random.default_rng(7)
        for img in (
            np.zeros((140, 220, 3), dtype=np.uint8),
            np.full((140, 220, 3), 125, dtype=np.uint8),
            rng.integers(0, 255, (140, 220, 3), dtype=np.uint8),
        ):
            self.assertFalse(detect_tgss_legacy(img, self.legacy).detected)

    def test_suspicion_and_cooldown(self):
        self.assertTrue(tgss_is_suspected(.541, .66))
        self.assertFalse(tgss_is_suspected(.539, .66))
        tracker = CooldownTracker()
        tracker.record_success('one', TGSS_KEY, 10, True)
        self.assertEqual(tracker.remaining('one', TGSS_KEY, 11), 4)
        self.assertEqual(tracker.remaining('two', TGSS_KEY, 11), 0)
        for i in range(4):
            tracker.record_success('one', TGSS_KEY, 15 + i*5, True)
        self.assertEqual(tracker.remaining('one', TGSS_KEY, 35), 715)


if __name__ == '__main__':
    unittest.main()
