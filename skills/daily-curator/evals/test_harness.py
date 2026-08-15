#!/usr/bin/env python3
"""Smoke tests for the isolated evaluation harness (not the full scenario suite)."""
from __future__ import annotations

import json
import os
import unittest

from harness import EVALS_DIR, SKILL_DIR, EvalHome, render_placeholders


class TestHarnessIsolation(unittest.TestCase):
    def test_home_is_not_the_real_install(self):
        with EvalHome() as ev:
            self.assertTrue(ev.real_install_untouched())
            self.assertTrue(ev.home.startswith("/tmp") or "daily-curator-eval-" in ev.home)
            real = os.path.realpath(os.path.expanduser("~/.daily-curator"))
            self.assertNotEqual(os.path.realpath(ev.home), real)

    def test_default_env_cannot_point_at_eval_home(self):
        with EvalHome() as ev:
            leaked = os.environ.get("DAILY_CURATOR_HOME")
            if leaked:
                self.assertNotEqual(os.path.realpath(leaked), os.path.realpath(ev.home))


class TestFixtureInstall(unittest.TestCase):
    def test_installs_taste_seen_shown_and_file_feed(self):
        with EvalHome() as ev:
            ev.install_taste("valid.md")
            ev.install_seen("seen-populated.txt")
            ev.install_shown("shown-week.jsonl")
            ev.install_feed_xml("content-day.xml")
            with open(ev.path("taste.md"), encoding="utf-8") as fh:
                self.assertIn("engineering practice", fh.read())
            with open(ev.path("seen.txt"), encoding="utf-8") as fh:
                seen = fh.read()
            self.assertIn("https://ex.com/already-shown", seen)
            self.assertNotIn("{{DAYS_AGO", seen)
            with open(ev.path("shown.jsonl"), encoding="utf-8") as fh:
                shown = fh.read()
            self.assertIn("week-high", shown)
            self.assertNotIn("{{DAYS_AGO", shown)
            with open(ev.path("feeds.txt"), encoding="utf-8") as fh:
                feeds = fh.read().strip()
            self.assertTrue(feeds.startswith("file://"))
            with open(ev.path("feeds", "content-day.xml"), encoding="utf-8") as fh:
                xml = fh.read()
            self.assertNotIn("{{PUBDATE}}", xml)
            self.assertIn("Building a small eval harness", xml)

    def test_placeholders_render_today(self):
        out = render_placeholders("d={{TODAY}} ago={{DAYS_AGO:2}}")
        self.assertNotIn("{{", out)
        self.assertRegex(out, r"d=\d{4}-\d{2}-\d{2}")


class TestHarnessRunsScripts(unittest.TestCase):
    def test_prepare_content_day_no_network(self):
        with EvalHome() as ev:
            ev.install_taste()
            ev.install_seen()
            ev.install_shown()
            ev.install_feed_xml("content-day.xml")
            before = ev.snapshot()
            r = ev.run(["curate.py", "prepare"])
            self.assertEqual(r.returncode, 0, r.stderr)
            cand_name = [f for f in os.listdir(ev.path("tmp"))
                         if f.startswith("candidates-")]
            self.assertEqual(len(cand_name), 1)
            with open(ev.path("tmp", cand_name[0]), encoding="utf-8") as fh:
                cand = json.load(fh)
            self.assertGreaterEqual(cand["count"], 1)
            urls = [c["url"] for c in cand["candidates"]]
            self.assertIn("https://ex.com/fresh-one", urls)
            # prepare may write feed-health.json; it must not touch a real install
            self.assertTrue(ev.real_install_untouched())
            self.assertNotIn("seen.txt", ev.changed(before) - {"feed-health.json"})

    def test_snapshot_detects_mark_seen(self):
        with EvalHome() as ev:
            ev.install_seen()
            ev.install_shown()
            ev.install_scored("good.json")
            r = ev.run(["curate.py", "select", "--scored", ev.path("tmp", "scored.json")])
            self.assertEqual(r.returncode, 0, r.stderr)
            selected = ev.path("tmp", "selected.json")
            with open(selected, "w", encoding="utf-8") as fh:
                fh.write(r.stdout)
            before = ev.snapshot()
            r = ev.run(["curate.py", "mark-seen", "--selected", selected])
            self.assertEqual(r.returncode, 0, r.stderr)
            changed = ev.changed(before)
            self.assertIn("seen.txt", changed)
            self.assertIn("shown.jsonl", changed)
            self.assertNotIn("taste.md", changed)


class TestLayout(unittest.TestCase):
    def test_skill_dir_contains_skill_md(self):
        self.assertTrue(os.path.isfile(os.path.join(SKILL_DIR, "SKILL.md")))
        self.assertTrue(os.path.isdir(os.path.join(EVALS_DIR, "fixtures")))


if __name__ == "__main__":
    unittest.main()
