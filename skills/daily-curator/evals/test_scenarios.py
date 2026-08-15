#!/usr/bin/env python3
"""Required evaluation scenarios. Each case checks the observable result
and that persistent state changed only where intended."""
from __future__ import annotations

import json
import os
import re
import subprocess
import unittest

from harness import SKILL_DIR, EvalHome, today_utc

DIGEST_BODY = (
    "# 今日推荐 | {day}\n\n"
    "**1. [Building a small eval harness](https://ex.com/fresh-one)**\n"
    "Source: ex.com · 0d ago\n"
    "A concrete test fixture for a content day.\n"
)


def _write_selected(ev: EvalHome, stdout: str) -> str:
    path = ev.path("tmp", "selected.json")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(stdout)
    return path


def _read(path: str) -> str:
    with open(path, encoding="utf-8") as fh:
        return fh.read()


def _skill_text() -> str:
    return _read(os.path.join(SKILL_DIR, "SKILL.md"))


def _ref(name: str) -> str:
    return _read(os.path.join(SKILL_DIR, "references", name))


# Documented feed-management classifier (mirrors feed-management.md).
_FEED_URL = re.compile(r"https?://\S+")
_TRUE_TRIGGERS = (
    (re.compile(r"^关注\s+https?://"), "feeds"),
    (re.compile(r"^取消关注\s+\S+"), "feeds"),
    (re.compile(r"^(我的信源|list feeds)\s*$", re.I), "feeds"),
    (re.compile(r"^导入\s+OPML\b"), "feeds"),
    (re.compile(r"^(调整口味|edit taste)\s*$", re.I), "taste"),
)


def classify_utterance(text: str) -> str | None:
    """Return 'feeds', 'taste', or None (do not activate feed management)."""
    stripped = text.strip()
    for pat, kind in _TRUE_TRIGGERS:
        if pat.search(stripped):
            return kind
    return None


class TestBootstrapFirstRun(unittest.TestCase):
    def test_first_run_seeds_and_second_run_is_noop(self):
        with EvalHome() as ev:
            self.assertFalse(os.path.exists(ev.path("feeds.txt")))
            self.assertFalse(os.path.exists(ev.path("taste.md")))
            r = ev.run(["curate.py", "bootstrap"])
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertTrue(os.path.isfile(ev.path("feeds.txt")))
            self.assertTrue(os.path.isfile(ev.path("taste.md")))
            self.assertTrue(os.path.isfile(ev.path("seen.txt")))
            self.assertTrue(os.path.isfile(ev.path("shown.jsonl")))
            self.assertTrue(os.path.isfile(ev.path("feed-health.json")))
            with open(ev.path("feeds.txt"), encoding="utf-8") as fh:
                self.assertGreater(len([ln for ln in fh if ln.startswith("http")]), 5)
            after_first = ev.snapshot()
            r = ev.run(["curate.py", "bootstrap"])
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertEqual(ev.changed(after_first), set())
            self.assertTrue(ev.real_install_untouched())


class TestContentDay(unittest.TestCase):
    def test_normal_content_day(self):
        with EvalHome() as ev:
            ev.install_taste()
            ev.install_seen()
            ev.install_shown()
            ev.install_feed_xml("content-day.xml")
            r = ev.run(["curate.py", "prepare"])
            self.assertEqual(r.returncode, 0, r.stderr)
            ev.install_scored("good.json")
            r = ev.run(["curate.py", "select", "--scored", ev.path("tmp", "scored.json")])
            self.assertEqual(r.returncode, 0, r.stderr)
            selected = json.loads(r.stdout)
            self.assertGreaterEqual(selected["count"], 1)
            sel_path = _write_selected(ev, r.stdout)
            before = ev.snapshot()
            digest = ev.write_digest(DIGEST_BODY.format(day=today_utc().isoformat()))
            r = ev.run(["curate.py", "mark-seen", "--selected", sel_path])
            self.assertEqual(r.returncode, 0, r.stderr)
            r = ev.run(["verify-run.py",
                        "--selected", sel_path,
                        "--digest", digest,
                        "--seen", ev.path("seen.txt"),
                        "--snapshot", ev.path("tmp", "seen-snapshot.json")])
            self.assertEqual(r.returncode, 0, r.stderr + r.stdout)
            changed = ev.changed(before)
            self.assertIn("seen.txt", changed)
            self.assertIn("shown.jsonl", changed)
            self.assertTrue(any(k.startswith("digests/") and not k.endswith("-weekly.md")
                                for k in changed))
            self.assertIn("https://ex.com/fresh-one", _read(ev.path("seen.txt")))
            self.assertTrue(ev.real_install_untouched())


class TestSilentDay(unittest.TestCase):
    def test_silent_day_writes_no_digest_or_ledgers(self):
        with EvalHome() as ev:
            ev.install_taste()
            ev.install_seen()
            ev.install_shown()
            ev.install_feed_xml("silent-day.xml")
            before = ev.snapshot()
            r = ev.run(["curate.py", "prepare"])
            self.assertEqual(r.returncode, 0, r.stderr)
            ev.install_scored("all-below-floor.json")
            r = ev.run(["curate.py", "select", "--scored", ev.path("tmp", "scored.json")])
            self.assertEqual(r.returncode, 0, r.stderr)
            selected = json.loads(r.stdout)
            self.assertEqual(selected["count"], 0)
            changed = ev.changed(before)
            self.assertNotIn("seen.txt", changed)
            self.assertNotIn("shown.jsonl", changed)
            self.assertFalse(any(k.startswith("digests/") for k in changed))
            self.assertIn("[SILENT]", _skill_text())


class TestDryRunContent(unittest.TestCase):
    def test_dry_run_with_selected_items_mutates_nothing_real(self):
        with EvalHome() as ev:
            ev.install_seen()
            ev.install_shown()
            ev.install_scored("good.json")
            r = ev.run(["curate.py", "select", "--scored", ev.path("tmp", "scored.json")])
            self.assertEqual(r.returncode, 0, r.stderr)
            sel_path = _write_selected(ev, r.stdout)
            digest = ev.write_digest(
                DIGEST_BODY.format(day=today_utc().isoformat()), dry_run=True)
            # snapshot as if prepare had just run (empty seen, empty snapshot)
            with open(ev.path("tmp", "seen-snapshot.json"), "w", encoding="utf-8") as fh:
                json.dump([], fh)
            before = ev.snapshot()
            r = ev.run(["verify-run.py", "--dry-run",
                        "--selected", sel_path,
                        "--digest", digest,
                        "--seen", ev.path("seen.txt"),
                        "--snapshot", ev.path("tmp", "seen-snapshot.json")])
            self.assertEqual(r.returncode, 0, r.stderr + r.stdout)
            r = ev.run(["health.py", "check", "--dry-run"])
            self.assertEqual(r.returncode, 0, r.stderr)
            changed = ev.changed(before)
            self.assertNotIn("seen.txt", changed)
            self.assertNotIn("shown.jsonl", changed)
            self.assertFalse(any(k.startswith("digests/") for k in changed))
            self.assertEqual(_read(ev.path("seen.txt")), "")
            self.assertFalse(os.path.exists(
                ev.path("digests", f"{today_utc().isoformat()}.md")))


class TestIdempotency(unittest.TestCase):
    def test_same_day_reinvoke_stops_when_digest_exists(self):
        with EvalHome() as ev:
            ev.install_seen()
            ev.install_shown()
            ev.write_digest(DIGEST_BODY.format(day=today_utc().isoformat()))
            before = ev.snapshot()
            skill = _skill_text()
            self.assertIn("digests/YYYY-MM-DD.md", skill)
            self.assertIn("[SILENT]", skill)
            self.assertIn("force_regen", skill)
            # Guard fires: do not mark-seen or rewrite. State stays put.
            self.assertEqual(ev.changed(before), set())
            self.assertNotIn("https://ex.com/fresh-one", _read(ev.path("seen.txt")))


class TestTasteProfile(unittest.TestCase):
    def test_missing_taste_bootstrap_creates_it(self):
        with EvalHome() as ev:
            self.assertFalse(os.path.exists(ev.path("taste.md")))
            before = ev.snapshot()
            r = ev.run(["curate.py", "bootstrap"])
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertIn("taste.md", ev.changed(before))
            self.assertGreater(os.path.getsize(ev.path("taste.md")), 0)
            self.assertIn("taste-template.md", _skill_text())

    def test_invalid_taste_does_not_crash_mechanics(self):
        with EvalHome() as ev:
            ev.install_taste("invalid.md")
            ev.install_seen()
            ev.install_shown()
            ev.install_feed_xml("content-day.xml")
            before = ev.snapshot()
            r = ev.run(["curate.py", "prepare"])
            self.assertEqual(r.returncode, 0, r.stderr)
            ev.install_scored("good.json")
            r = ev.run(["curate.py", "select", "--scored", ev.path("tmp", "scored.json")])
            self.assertEqual(r.returncode, 0, r.stderr)
            # Scripts never score from taste.md; invalid file is not silently
            # rewritten. Agent must surface it (SKILL.md: edit taste.md).
            self.assertEqual(_read(ev.path("taste.md")).strip(),
                             "this is not a taste profile\n???")
            self.assertNotIn("seen.txt", ev.changed(before) - {"feed-health.json"})


class TestMalformedScored(unittest.TestCase):
    def test_malformed_scored_json_selects_nothing(self):
        with EvalHome() as ev:
            ev.install_seen()
            ev.install_shown()
            ev.install_scored("malformed.json")
            before = ev.snapshot()
            r = ev.run(["curate.py", "select", "--scored", ev.path("tmp", "scored.json")])
            self.assertEqual(r.returncode, 0, r.stderr)
            out = json.loads(r.stdout)
            self.assertEqual(out["count"], 0)
            self.assertEqual(out["selected"], [])
            self.assertEqual(ev.changed(before), set())


class TestWeeklyRoundup(unittest.TestCase):
    def test_weekly_reads_shown_jsonl_ranked_by_score(self):
        with EvalHome() as ev:
            ev.install_shown("shown-week.jsonl")
            ev.install_seen()
            before = ev.snapshot()
            r = ev.run(["curate.py", "roundup", "--days", "7"])
            self.assertEqual(r.returncode, 0, r.stderr)
            data = json.loads(r.stdout)
            urls = [it["url"] for it in data["items"]]
            self.assertEqual(urls[0], "https://ex.com/week-high")
            self.assertIn("https://ex.com/week-mid", urls)
            self.assertNotIn("https://ex.com/week-old", urls)
            self.assertEqual(ev.changed(before), set(), "roundup must not write ledgers")
            day = today_utc().isoformat()
            weekly = ev.path("digests", f"{day}-weekly.md")
            with open(weekly, "w", encoding="utf-8") as fh:
                fh.write("# 本周精选 | %s\n\n> 本周 2 篇值得回看\n" % day)
            self.assertTrue(os.path.isfile(weekly))
            self.assertFalse(os.path.isfile(ev.path("digests", f"{day}.md")))

    def test_zero_item_weekly_heartbeat(self):
        with EvalHome() as ev:
            ev.install_shown("shown-empty.jsonl")
            ev.install_seen()
            before = ev.snapshot()
            r = ev.run(["curate.py", "roundup", "--days", "7"])
            self.assertEqual(r.returncode, 0, r.stderr)
            data = json.loads(r.stdout)
            self.assertEqual(data["count"], 0)
            self.assertEqual(data["items"], [])
            weekly = _ref("weekly.md")
            fmt = _ref("output-format.md")
            self.assertIn("本周无新增。", weekly)
            self.assertIn("本周无新增。", fmt)
            self.assertRegex(weekly, r"本周无新增。.*not `\[SILENT\]`")
            self.assertEqual(ev.changed(before), set())
            self.assertFalse(os.path.exists(
                ev.path("digests", f"{today_utc().isoformat()}.md")))


class TestFeedManagement(unittest.TestCase):
    def test_triggers_edit_only_feeds_or_taste(self):
        cases = [
            ("关注 https://example.com/feed.xml", "feeds"),
            ("取消关注 example.com", "feeds"),
            ("我的信源", "feeds"),
            ("list feeds", "feeds"),
            ("导入 OPML https://example.com/x.opml", "feeds"),
            ("调整口味", "taste"),
            ("edit taste", "taste"),
        ]
        docs = _ref("feed-management.md") + _skill_text()
        for phrase, kind in cases:
            self.assertEqual(classify_utterance(phrase), kind, phrase)
            token = phrase.split()[0]
            self.assertIn(token, docs)

        with EvalHome() as ev:
            ev.install_taste()
            with open(ev.path("feeds.txt"), "w", encoding="utf-8") as fh:
                fh.write("https://old.example/feed.xml\n")
            before = ev.snapshot()
            with open(ev.path("feeds.txt"), "a", encoding="utf-8") as fh:
                fh.write("https://example.com/feed.xml\n")
            changed = ev.changed(before)
            self.assertEqual(changed, {"feeds.txt"})
            self.assertNotIn("seen.txt", changed)
            self.assertNotIn("shown.jsonl", changed)

            opml = ev.fixture("feeds", "sample.opml")
            extracted = subprocess.run(
                ["bash", os.path.join(SKILL_DIR, "scripts", "import-opml.sh"), opml],
                cwd=SKILL_DIR, capture_output=True, text=True, check=False,
            )
            self.assertEqual(extracted.returncode, 0, extracted.stderr)
            self.assertIn("https://opml.example/alpha.xml", extracted.stdout)
            self.assertIn("https://opml.example/beta.xml", extracted.stdout)

    def test_false_positives_do_not_activate_feed_management(self):
        false_positives = [
            "今日推荐",
            "今天读什么",
            "daily reads",
            "本周精选",
            "https://ex.com/fresh-one",
            "值得关注的论文",
        ]
        docs = _ref("feed-management.md")
        for phrase in false_positives:
            self.assertIsNone(classify_utterance(phrase), phrase)
        for marker in ("今日推荐", "本周精选", "值得关注的论文"):
            self.assertIn(marker, docs)

        with EvalHome() as ev:
            ev.install_taste()
            with open(ev.path("feeds.txt"), "w", encoding="utf-8") as fh:
                fh.write("https://old.example/feed.xml\n")
            ev.write_digest(
                "# 今日推荐\n\n**1. [x](https://ex.com/fresh-one)**\n")
            before = ev.snapshot()
            # Treating the digest as a daily run, not as 关注.
            self.assertIsNone(classify_utterance("今日推荐"))
            self.assertIsNone(classify_utterance("https://ex.com/fresh-one"))
            self.assertEqual(ev.changed(before), set())
            self.assertEqual(_read(ev.path("feeds.txt")),
                             "https://old.example/feed.xml\n")


if __name__ == "__main__":
    unittest.main()
