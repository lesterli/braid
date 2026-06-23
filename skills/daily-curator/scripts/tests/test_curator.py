#!/usr/bin/env python3
"""daily-curator v3 test suite (stdlib unittest — no pip install required).

Run from anywhere:
    python3 -m unittest discover -s skills/daily-curator/scripts/tests
or:
    cd skills/daily-curator/scripts && python3 -m unittest tests.test_curator

Covers the deterministic, load-bearing paths (canonicalization, dedup,
freshness, negative-anchor, select cap, feed parse, migration, verifier) plus
one golden end-to-end run of the CLI over a file:// fixture (no network).
"""
import json
import os
import subprocess
import sys
import tempfile
import unittest
from datetime import date, datetime, timezone

SCRIPTS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, SCRIPTS)

import canon          # noqa: E402
import curate         # noqa: E402
import migrate        # noqa: E402

# verify-run.py has a hyphen; load it by path.
import importlib.util  # noqa: E402
_spec = importlib.util.spec_from_file_location(
    "verify_run", os.path.join(SCRIPTS, "verify-run.py"))
verify_run = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(verify_run)

TODAY = date(2026, 6, 23)


class TestCanon(unittest.TestCase):
    def test_fragment_and_slash(self):
        self.assertEqual(canon.canonicalize_url("https://EX.com/Post/#atom-entries"),
                         "https://ex.com/Post")
        self.assertEqual(canon.canonicalize_url("https://ex.com/a/"), "https://ex.com/a")
        self.assertEqual(canon.canonicalize_url("http://ex.com/"), "http://ex.com/")
        self.assertEqual(canon.canonicalize_url("https://ex.com/p?q=1#f"),
                         "https://ex.com/p?q=1")

    def test_variants_collapse(self):
        a = canon.canonicalize_url("https://simonwillison.net/2026/Jun/22/x/#atom-entries")
        b = canon.canonicalize_url("https://simonwillison.net/2026/Jun/22/x")
        self.assertEqual(a, b)

    def test_blank(self):
        self.assertEqual(canon.canonicalize_url(""), "")
        self.assertEqual(canon.canonicalize_url("   "), "")

    def test_parse_date(self):
        self.assertEqual(canon.parse_date("Mon, 02 Jun 2026 12:00:00 GMT"), date(2026, 6, 2))
        self.assertEqual(canon.parse_date("2026-06-02T12:00:00Z"), date(2026, 6, 2))
        self.assertEqual(canon.parse_date("2026-06-02"), date(2026, 6, 2))
        self.assertIsNone(canon.parse_date(None))
        self.assertIsNone(canon.parse_date("garbage"))


class TestSeenLedger(unittest.TestCase):
    def test_append_dedup_and_prune(self):
        with tempfile.TemporaryDirectory() as d:
            seen = os.path.join(d, "seen.txt")
            n = canon.append_seen(seen, ["https://a.com/1/", "https://a.com/1"], TODAY)
            self.assertEqual(n, 1, "trailing-slash variant should dedup to 1")
            n2 = canon.append_seen(seen, ["https://a.com/1"], TODAY)
            self.assertEqual(n2, 0, "already-present url should not re-append")
            self.assertIn("https://a.com/1", canon.load_seen_urls(seen))

    def test_prune_window(self):
        with tempfile.TemporaryDirectory() as d:
            seen = os.path.join(d, "seen.txt")
            with open(seen, "w") as fh:
                fh.write(json.dumps({"url": "https://x/recent", "date_shown": "2026-06-20"}) + "\n")
                fh.write(json.dumps({"url": "https://x/old", "date_shown": "2026-01-01"}) + "\n")
                fh.write(json.dumps({"url": "https://x/nodate", "date_shown": ""}) + "\n")
            removed = canon.prune_seen(seen, TODAY, window_days=30)
            self.assertEqual(removed, 1)
            urls = canon.load_seen_urls(seen)
            self.assertIn("https://x/recent", urls)
            self.assertNotIn("https://x/old", urls)
            self.assertIn("https://x/nodate", urls, "missing date_shown must be kept (fail safe)")


class TestFilters(unittest.TestCase):
    def test_is_fresh(self):
        self.assertTrue(curate.is_fresh("2026-06-22T00:00:00Z", TODAY))
        self.assertFalse(curate.is_fresh("2026-05-01T00:00:00Z", TODAY))
        self.assertTrue(curate.is_fresh(None, TODAY))

    def test_negative_anchor(self):
        pats = curate.DEFAULT_NEGATIVE_PATTERNS
        self.assertTrue(curate.title_matches_negative("某公司完成B轮融资", pats))
        self.assertTrue(curate.title_matches_negative("This startup IPO is huge", pats))
        self.assertFalse(curate.title_matches_negative("Building effective agents", pats))

    def test_filter_pipeline(self):
        entries = [
            {"url": "https://a.com/1", "title": "good", "published": "2026-06-22", "summary": "", "source_bucket": "a"},
            {"url": "https://a.com/1", "title": "dup", "published": "2026-06-22", "summary": "", "source_bucket": "a"},
            {"url": "https://b.com/2", "title": "old", "published": "2026-01-01", "summary": "", "source_bucket": "b"},
            {"url": "https://c.com/3", "title": "IPO 来了", "published": "2026-06-22", "summary": "", "source_bucket": "c"},
            {"url": "https://seen.com/x", "title": "already", "published": "2026-06-22", "summary": "", "source_bucket": "s"},
        ]
        out = curate.filter_candidates(entries, {"https://seen.com/x"}, TODAY,
                                       curate.DEFAULT_NEGATIVE_PATTERNS)
        self.assertEqual([e["url"] for e in out], ["https://a.com/1"])


class TestSelect(unittest.TestCase):
    def _scored(self):
        return [
            {"url": "h1", "score": 0.9, "published": "2026-06-20", "source_bucket": "hackernews"},
            {"url": "h2", "score": 0.85, "published": "2026-06-21", "source_bucket": "hackernews"},
            {"url": "h3", "score": 0.8, "published": "2026-06-22", "source_bucket": "hackernews"},
            {"url": "s1", "score": 0.7, "published": "2026-06-22", "source_bucket": "simon"},
            {"url": "lo", "score": 0.2, "published": "2026-06-22", "source_bucket": "x"},
        ]

    def test_floor_rank_cap(self):
        sel = curate.select(self._scored(), count=5, floor=0.4)
        urls = [s["url"] for s in sel]
        self.assertNotIn("lo", urls, "below-floor must drop")
        self.assertEqual(urls[0], "h1", "highest score ranks first")
        self.assertEqual(sum(u.startswith("h") for u in urls), 2, "same-source cap=2")
        self.assertNotIn("h3", urls, "third HN item capped out")

    def test_topn(self):
        sel = curate.select(self._scored(), count=1, floor=0.4)
        self.assertEqual(len(sel), 1)

    def test_silent_gate(self):
        sel = curate.select([{"url": "a", "score": 0.1, "source_bucket": "x"}], floor=0.4)
        self.assertEqual(sel, [], "all below floor => empty => [SILENT]")


class TestParse(unittest.TestCase):
    def test_rss(self):
        rss = ('<?xml version="1.0"?><rss version="2.0"><channel><title>F</title>'
               '<item><title>RSS One</title><link>https://ex.com/one/</link>'
               '<pubDate>Sun, 22 Jun 2026 08:00:00 GMT</pubDate>'
               '<description>hi</description></item></channel></rss>')
        out = curate.parse_feed(rss, "https://ex.com/feed")
        self.assertEqual(out[0]["url"], "https://ex.com/one")
        self.assertEqual(out[0]["title"], "RSS One")

    def test_atom(self):
        atom = ('<?xml version="1.0"?><feed xmlns="http://www.w3.org/2005/Atom">'
                '<entry><title>Atom One</title>'
                '<link href="https://ex.com/two#atom-entries" rel="alternate"/>'
                '<published>2026-06-21T10:00:00Z</published>'
                '<summary>yo</summary></entry></feed>')
        out = curate.parse_feed(atom, "https://ex.com/atom")
        self.assertEqual(out[0]["url"], "https://ex.com/two")
        self.assertEqual(out[0]["title"], "Atom One")

    def test_malformed_and_bucket(self):
        self.assertEqual(curate.parse_feed("<not xml", "u"), [])
        self.assertEqual(curate.source_bucket("https://hnrss.org/newest?q=AI"), "hackernews")
        self.assertEqual(curate.source_bucket("https://simonwillison.net/atom/"), "simonwillison.net")


class TestMigrate(unittest.TestCase):
    def test_extract_and_dedupe(self):
        with tempfile.TemporaryDirectory() as d:
            q = os.path.join(d, "queued.txt")
            with open(q, "w") as fh:
                fh.write(json.dumps({"url": "https://a.com/1/"}) + "\n")
                fh.write("\n")  # blank
                fh.write("not json\n")  # malformed
                fh.write(json.dumps({"url": "https://a.com/1"}) + "\n")  # canon dup
            urls = migrate.extract_urls(q)
            self.assertEqual(urls, ["https://a.com/1", "https://a.com/1"])
            self.assertEqual(migrate.dedupe(urls), ["https://a.com/1"])
        self.assertEqual(migrate.extract_urls("/no/such/file"), [])


class TestVerify(unittest.TestCase):
    def test_pass(self):
        f = verify_run.verify(["https://a/1"], _digest_ok(), {"https://a/1"}, set())
        self.assertEqual(f, [])

    def test_silent_day(self):
        self.assertEqual(verify_run.verify([], "/nope", set(), set()), [])

    def test_missing_from_seen(self):
        f = verify_run.verify(["https://a/1"], _digest_ok(), set(), set())
        self.assertTrue(any("not in seen" in x for x in f))

    def test_reshow(self):
        f = verify_run.verify(["https://a/1"], _digest_ok(), {"https://a/1"}, {"https://a/1"})
        self.assertTrue(any("already seen" in x for x in f))

    def test_body_checks(self):
        self.assertIn("frontmatter", " ".join(verify_run.check_digest_body("---\ndate: x\n---\n# T")))
        self.assertIn("H1", " ".join(verify_run.check_digest_body("no heading here")))
        self.assertTrue(any("_scores" in x for x in
                            verify_run.check_digest_body("# T\n<!-- _scores: q=1 -->")))
        self.assertEqual(verify_run.check_digest_body("# 今日推荐\n\nbody"), [])


_DIGEST_HANDLES = []


def _digest_ok():
    tf = tempfile.NamedTemporaryFile("w", suffix=".md", delete=False)
    tf.write("# 今日推荐\n\n**1. [x](https://a/1)**\nSource: a\n")
    tf.close()
    _DIGEST_HANDLES.append(tf.name)
    return tf.name


class TestGoldenE2E(unittest.TestCase):
    """Full CLI run over a file:// fixture: prepare -> score -> select -> mark-seen -> verify."""
    def test_end_to_end(self):
        with tempfile.TemporaryDirectory() as home:
            stamp = datetime.now(timezone.utc).strftime("%a, %d %b %Y 08:00:00 GMT")
            sample = os.path.join(home, "sample.xml")
            with open(sample, "w") as fh:
                fh.write('<?xml version="1.0"?><rss version="2.0"><channel><title>S</title>'
                         f'<item><title>Fresh post</title><link>https://ex.com/fresh/#x</link>'
                         f'<pubDate>{stamp}</pubDate><description>real</description></item>'
                         '<item><title>融资 news</title><link>https://ex.com/money</link>'
                         f'<pubDate>{stamp}</pubDate><description>x</description></item>'
                         '<item><title>Stale</title><link>https://ex.com/stale</link>'
                         '<pubDate>Thu, 01 Jan 2026 08:00:00 GMT</pubDate><description>old</description></item>'
                         '</channel></rss>')
            with open(os.path.join(home, "feeds.txt"), "w") as fh:
                fh.write("file://" + sample + "\n")

            def run(args):
                return subprocess.run([sys.executable] + args, cwd=SCRIPTS,
                                      capture_output=True, text=True)

            r = run(["curate.py", "prepare", "--home", home])
            self.assertEqual(r.returncode, 0, r.stderr)
            today = canon.today_utc().isoformat()
            with open(os.path.join(home, "tmp", f"candidates-{today}.json")) as fh:
                cand = json.load(fh)
            self.assertEqual(cand["count"], 1, "only the fresh non-negative item survives")
            self.assertEqual(cand["candidates"][0]["url"], "https://ex.com/fresh")

            for c in cand["candidates"]:
                c["score"] = 0.8
            scored = os.path.join(home, "scored.json")
            with open(scored, "w") as fh:
                json.dump(cand, fh)
            r = run(["curate.py", "select", "--scored", scored, "--home", home])
            self.assertEqual(r.returncode, 0, r.stderr)
            selected = os.path.join(home, "selected.json")
            with open(selected, "w") as fh:
                fh.write(r.stdout)
            self.assertEqual(json.loads(r.stdout)["count"], 1)

            digest = os.path.join(home, "tmp", "digest.md")
            with open(digest, "w") as fh:
                fh.write("# 今日推荐\n\n**1. [Fresh post](https://ex.com/fresh)**\nSource: ex.com\n")
            r = run(["curate.py", "mark-seen", "--selected", selected, "--home", home])
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertIn("https://ex.com/fresh", canon.load_seen_urls(os.path.join(home, "seen.txt")))

            r = run(["verify-run.py", "--selected", selected, "--digest", digest,
                     "--seen", os.path.join(home, "seen.txt"),
                     "--snapshot", os.path.join(home, "tmp", "seen-snapshot.json")])
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)


def tearDownModule():
    for p in _DIGEST_HANDLES:
        try:
            os.remove(p)
        except OSError:
            pass


if __name__ == "__main__":
    unittest.main()
