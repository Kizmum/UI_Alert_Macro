"""Offline checks for the stable release. Run: python -m unittest discover -s tests -v"""
import json
import tempfile
import threading
import unittest
from pathlib import Path
from unittest.mock import patch

import cv2
import numpy as np
import ui_alert_macro_gui as macro


class RecognitionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.all_templates = macro.load_templates()
        cls.modern = {key: variants for key, variants in cls.all_templates.items() if key != macro.TGSS_KEY}
        cls.legacy = macro.load_legacy_templates()

    def test_template_counts(self):
        self.assertEqual(len(self.all_templates), 9)
        self.assertEqual(sum(map(len, self.all_templates.values())), 20)
        self.assertEqual(len(self.modern), 8)
        self.assertEqual(sum(map(len, self.modern.values())), 17)
        self.assertNotIn(macro.TGSS_KEY, self.modern)
        self.assertEqual(len(self.legacy[macro.TGSS_KEY]), 3)

    def test_modern_detects_all_non_tgss_templates(self):
        for key, variants in self.modern.items():
            for idx, variant in enumerate(variants):
                with self.subTest(biome=key, template=idx):
                    result = macro.detect_event(variant['image'], self.modern,
                                                macro.STANDARD_THRESHOLDS, set(self.modern))
                    self.assertEqual(result.event_key, key)

    def test_modern_never_reports_tgss(self):
        for variant in self.all_templates[macro.TGSS_KEY]:
            result = macro.detect_event(variant['image'], self.modern,
                                        macro.STANDARD_THRESHOLDS, set(macro.EVENTS))
            self.assertNotEqual(result.event_key, macro.TGSS_KEY)

    def test_legacy_detects_new_tgss_templates(self):
        for idx, variant in enumerate(self.legacy[macro.TGSS_KEY]):
            with self.subTest(template=idx):
                result = macro.detect_tgss_legacy(variant, self.legacy)
                self.assertTrue(result.detected)
                self.assertEqual(result.best_key, macro.TGSS_KEY)
                self.assertGreaterEqual(result.tgss_score, 0.76)

    def test_legacy_never_reports_other_biomes(self):
        for key, variants in self.all_templates.items():
            if key == macro.TGSS_KEY:
                continue
            for idx, variant in enumerate(variants):
                with self.subTest(biome=key, template=idx):
                    result = macro.detect_tgss_legacy(variant['image'], self.legacy)
                    self.assertFalse(result.detected)

    def test_legacy_rejects_blank_and_noise(self):
        rng = np.random.default_rng(7)
        for img in (
            np.zeros((140, 220, 3), dtype=np.uint8),
            np.full((140, 220, 3), 125, dtype=np.uint8),
            rng.integers(0, 255, (140, 220, 3), dtype=np.uint8),
        ):
            self.assertFalse(macro.detect_tgss_legacy(img, self.legacy).detected)


class SettingsTests(unittest.TestCase):
    def test_defaults_and_version(self):
        cfg = macro.default_config()
        self.assertEqual(macro.VERSION, '1.0.0')
        self.assertEqual(cfg['config_version'], '1.0.0')
        self.assertEqual(macro.CHECK_INTERVAL, 5.0)
        self.assertEqual(macro.TGSS_LEGACY_INTERVAL, 2.0)
        self.assertEqual(macro.LEGACY_MATCH_THRESHOLD, .76)
        self.assertTrue(cfg['gss_multi_ping'])
        self.assertEqual(macro.digits('<@&1537542231953506305>'), '1537542231953506305')

    def test_upgrade_keeps_settings(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / 'app_config.json'
            cfg = macro.default_config()
            cfg.update(config_version='6.0', webhook_url='https://discord.com/api/webhooks/abc/def',
                       language='ru', theme='dark')
            cfg['role_ids'][macro.TGSS_KEY] = '123456789012345678'
            cfg['biome_enabled'][macro.TGSS_KEY] = True
            cfg['windows'][0]['vip_url'] = 'https://example.com/private'
            cfg['windows'][0]['region'] = {'left': 24, 'top': 99, 'width': 150, 'height': 130}
            path.write_text(json.dumps(cfg), encoding='utf-8')
            with patch.object(macro, 'CONFIG_PATH', path):
                restored = macro.load_config()
                self.assertEqual(restored['webhook_url'], cfg['webhook_url'])
                self.assertEqual(restored['role_ids'][macro.TGSS_KEY], '123456789012345678')
                self.assertEqual(restored['windows'][0]['vip_url'], cfg['windows'][0]['vip_url'])
                self.assertEqual(restored['windows'][0]['region'], cfg['windows'][0]['region'])
                self.assertEqual(restored['language'], 'ru')
                self.assertEqual(restored['theme'], 'dark')

    def test_workspace_cooldowns_and_tgss_multi_ping(self):
        tracker = macro.CooldownTracker()
        tracker.record_success('first', macro.TGSS_KEY, 10, True)
        self.assertEqual(tracker.remaining('first', macro.TGSS_KEY, 11), 4)
        self.assertEqual(tracker.remaining('second', macro.TGSS_KEY, 11), 0)
        for idx in range(4):
            tracker.record_success('first', macro.TGSS_KEY, 15 + idx*5, True)
        self.assertEqual(tracker.remaining('first', macro.TGSS_KEY, 35), 715)
        tracker.record_success('second', 'blood_moon', 35, False)
        self.assertEqual(tracker.remaining('second', 'blood_moon', 36), 359)
        self.assertEqual(tracker.remaining('second', 'rainy_world', 36), 0)

    def test_discord_message_is_english(self):
        data = macro.discord_payload('123456789012345678', macro.TGSS_KEY, '', 'picture.jpg')
        self.assertIn('detected!', data['content'])
        self.assertEqual(data['allowed_mentions']['roles'], ['123456789012345678'])


class SchedulerTests(unittest.TestCase):
    def _run(self, tgss=True, other=True):
        times_modern, times_legacy = [], []
        class Clock:
            now = 100.0
            @classmethod
            def monotonic(cls): return cls.now
            @classmethod
            def sleep(cls, seconds):
                cls.now += seconds
                if cls.now >= 111.0:
                    app.shutdown.set()

        class Screen:
            def __enter__(self): return self
            def __exit__(self, *args): return False

        app = macro.App.__new__(macro.App)
        app.shutdown = threading.Event()
        app.lock = threading.RLock()
        window = macro.default_window()
        window['running'] = True
        app.windows = [window]
        app.active_id = window['id']
        app.config = macro.default_config()
        for key in ('rainy_world', macro.TGSS_KEY):
            app.config['biome_enabled'][key] = bool(other if key == 'rainy_world' else tgss)
            app.config['role_ids'][key] = '123456789012345678'
        app.next_checks = {}
        app.next_tgss_legacy = {}
        app.cooldowns = macro.CooldownTracker()
        app.legacy_templates = {'some': 1}
        app.modern_templates = {'rainy_world': []}
        import queue
        app.messages = queue.Queue()

        def detect_modern(shot, templates, thresholds, enabled):
            self.assertNotIn(macro.TGSS_KEY, templates)
            self.assertNotIn(macro.TGSS_KEY, enabled)
            times_modern.append(round(Clock.now - 100, 2))
            return macro.DetectionResult(None, 'rainy_world', .15, .02, .66)

        def detect_legacy(shot, templates):
            times_legacy.append(round(Clock.now - 100, 2))
            return macro.LegacyTGSSResult(False, 'rainy_world', .10, .05)

        with patch.object(macro.mss, 'mss', lambda: Screen()), \
             patch.object(macro, 'capture_region', lambda *args: np.zeros((140, 220, 3), dtype=np.uint8)), \
             patch.object(macro, 'detect_event', detect_modern), \
             patch.object(macro, 'detect_tgss_legacy', detect_legacy), \
             patch.object(macro.time, 'monotonic', Clock.monotonic), \
             patch.object(macro.time, 'sleep', Clock.sleep):
            app._monitor_loop()
        return times_modern, times_legacy

    def test_dispatch_biomes_and_shared_tgss_cooldown(self):
        modern_events, legacy_events, delivered = [], [], []
        class Clock:
            now = 100.0
            @classmethod
            def monotonic(cls): return cls.now
            @classmethod
            def sleep(cls, seconds):
                cls.now += seconds
                if cls.now >= 111.0:
                    app.shutdown.set()
        class Screen:
            def __enter__(self): return self
            def __exit__(self, *args): return False
        import queue
        app = macro.App.__new__(macro.App)
        app.shutdown = threading.Event()
        app.lock = threading.RLock()
        win = macro.default_window()
        win['running'] = True
        app.windows = [win]
        app.active_id = win['id']
        app.config = macro.default_config()
        app.config['webhook_url'] = 'https://discord.com/api/webhooks/123/test'
        for key in ('blood_moon', macro.TGSS_KEY):
            app.config['biome_enabled'][key] = True
            app.config['role_ids'][key] = '123456789012345678'
        app.next_checks = {}
        app.next_tgss_legacy = {}
        app.cooldowns = macro.CooldownTracker()
        app.modern_templates = {'blood_moon': []}
        app.legacy_templates = {macro.TGSS_KEY: []}
        app.messages = queue.Queue()
        app._get_window = lambda wid=None: win

        def modern(*args):
            modern_events.append(round(Clock.now-100, 2))
            return macro.DetectionResult('blood_moon', 'blood_moon', .88, .30, .66)
        def legacy(*args):
            legacy_events.append(round(Clock.now-100, 2))
            return macro.LegacyTGSSResult(True, macro.TGSS_KEY, .90, .25)
        def delivered_alert(sct, window, cfg, shot, keys, biome, trigger, title):
            if app.cooldowns.remaining(window['id'], biome, Clock.now):
                return
            delivered.append((round(Clock.now-100, 2), biome, trigger))
            app.cooldowns.record_success(window['id'], biome, Clock.now, cfg['gss_multi_ping'])
        app._deliver_alert = delivered_alert

        with patch.object(macro.mss, 'mss', lambda: Screen()), \
             patch.object(macro, 'capture_region', lambda *args: np.zeros((140, 220, 3), dtype=np.uint8)), \
             patch.object(macro, 'detect_event', modern), \
             patch.object(macro, 'detect_tgss_legacy', legacy), \
             patch.object(macro.time, 'monotonic', Clock.monotonic), \
             patch.object(macro.time, 'sleep', Clock.sleep):
            app._monitor_loop()
        self.assertEqual(len(modern_events), 3)
        self.assertEqual(len(legacy_events), 3)  # TGSS scans pause during the shared cooldown
        self.assertEqual([item[1] for item in delivered].count('blood_moon'), 1)
        tgss = [item for item in delivered if item[1] == macro.TGSS_KEY]
        self.assertGreaterEqual(len(tgss), 2)
        self.assertTrue(all('Legacy' in item[2] for item in tgss))
        self.assertTrue(all(b[0] - a[0] >= 5.0 for a,b in zip(tgss, tgss[1:])))

    def test_independent_scan_rates(self):
        modern, legacy = self._run(tgss=True, other=True)
        self.assertEqual(len(modern), 3)  # 0, 5, 10 sec
        self.assertEqual(len(legacy), 6)  # 0, 2, 4, 6, 8, 10 sec
        self.assertAlmostEqual(modern[1] - modern[0], 5.0, delta=0.06)
        self.assertAlmostEqual(legacy[1] - legacy[0], 2.0, delta=0.06)

    def test_tgss_only_does_not_start_modern(self):
        modern, legacy = self._run(tgss=True, other=False)
        self.assertEqual(modern, [])
        self.assertEqual(len(legacy), 6)

    def test_other_biome_only_does_not_start_legacy(self):
        modern, legacy = self._run(tgss=False, other=True)
        self.assertEqual(len(modern), 3)
        self.assertEqual(legacy, [])


if __name__ == '__main__':
    unittest.main()
