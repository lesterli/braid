#!/usr/bin/env python3
"""daily-curator v3 — deterministic pipeline mechanics (no LLM).

The skill splits work into mechanics (here, fixed + tested) and judgment (the
LLM scores relevance + writes the why-line). This script owns everything that
has one correct answer, so it never gets re-improvised per run.

    feeds.txt
       │  fetch (stdlib urllib, per-feed, failures skipped)
       ▼
    parse RSS/Atom ──▶ canonicalize URL
       │
       ▼  cheap filters (NO LLM):
    drop published > window(14d)          [freshness]
    drop url ∈ seen.txt                   [dedup]
    drop title ~ negative-anchor regex    [stage-1 grep]
       │
       ▼
    candidates.json  ──▶  [LLM scores each 0–1]  ──▶  scored.json
                                                          │
                                                          ▼  select (NO LLM):
                                              drop score < floor(0.4)
                                              rank: score desc, newer first
                                              same-source cap = 2
                                              take top N (default 5)
                                                          │
                                                          ▼
                                              selected.json ─▶ [LLM writes digest]
                                                          │
                                                          ▼  mark-seen
                                              append shown URLs to seen.txt

Subcommands:
  prepare    fetch + filter + dedup; prune seen; snapshot seen; write candidates
  select     scored.json -> selected.json (floor, rank, same-source cap, top-N)
  mark-seen  append selected URLs to seen.txt (call only after a real delivery)

State dir defaults to $DAILY_CURATOR_HOME or ~/.daily-curator.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import urllib.request
import xml.etree.ElementTree as ET
from datetime import date

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from canon import (  # noqa: E402
    canonicalize_url, parse_date, today_utc,
    load_seen_urls, prune_seen, append_seen,
)

FRESHNESS_WINDOW_DAYS = 14
DEFAULT_COUNT = 5
DEFAULT_FLOOR = 0.4
SAME_SOURCE_CAP = 2
TMP_KEEP_RUNS = 3
FETCH_TIMEOUT = 12
UA = "Mozilla/5.0 (compatible; DailyCurator/3.0)"

# Stage-1 negative anchors: literal-ish regexes matched against the TITLE only.
# Keep ONLY patterns safe to drop without context (per scoring-and-filtering.md).
DEFAULT_NEGATIVE_PATTERNS = [
    r"融资", r"\bIPO\b", r"估值", r"震惊", r"取代", r"要失业", r"股价",
    r"裁员", r"涨停", r"跌停", r"\b10\s*个\s*prompt", r"\b10\s+prompts?\b",
]


# ---------------------------------------------------------------------------
# Feed I/O + parsing
# ---------------------------------------------------------------------------
def fetch_feed(url: str, timeout: int = FETCH_TIMEOUT) -> str | None:
    """Fetch one feed; return body text or None (unreachable feeds are skipped,
    never fatal — one dead feed must not kill the whole run)."""
    try:
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read()
        return raw.decode("utf-8", errors="replace")
    except Exception as exc:  # network, TLS, HTTP, decode — all non-fatal
        print(f"[warn] unreachable: {url} ({exc})", file=sys.stderr)
        return None


def _local(tag: str) -> str:
    """Strip an XML namespace, returning the local tag name lowercased."""
    if "}" in tag:
        tag = tag.split("}", 1)[1]
    return tag.lower()


def _child_text(entry: ET.Element, names: set[str]) -> str:
    for child in entry:
        if _local(child.tag) in names and child.text:
            return child.text.strip()
    return ""


def _atom_link(entry: ET.Element) -> str:
    """Pick the best <link> for an Atom entry: prefer rel=alternate, else the
    first link with an href, else <link> text content (RSS style)."""
    fallback = ""
    for child in entry:
        if _local(child.tag) != "link":
            continue
        href = child.attrib.get("href")
        if href:
            rel = child.attrib.get("rel", "alternate")
            if rel == "alternate":
                return href.strip()
            fallback = fallback or href.strip()
        elif child.text:
            fallback = fallback or child.text.strip()
    return fallback


def source_bucket(feed_url: str) -> str:
    """Group feeds for the same-source cap. All hnrss.org queries share one
    bucket so HN can't dominate a digest; every other feed is its own bucket."""
    host = ""
    try:
        host = canonicalize_url(feed_url).split("//", 1)[-1].split("/", 1)[0]
    except Exception:
        host = feed_url
    if "hnrss.org" in host:
        return "hackernews"
    return host or feed_url


def parse_feed(xml_text: str, feed_url: str) -> list[dict]:
    """Parse RSS or Atom into a list of entry dicts. Tolerant: a malformed feed
    yields [] rather than raising."""
    if not xml_text:
        return []
    try:
        root = ET.fromstring(xml_text.encode("utf-8", errors="replace"))
    except ET.ParseError as exc:
        print(f"[warn] parse error: {feed_url} ({exc})", file=sys.stderr)
        return []

    bucket = source_bucket(feed_url)
    entries: list[dict] = []
    for el in root.iter():
        if _local(el.tag) not in ("item", "entry"):
            continue
        title = _child_text(el, {"title"})
        url = _atom_link(el)
        if not url:
            url = _child_text(el, {"link", "guid", "id"})
        url = canonicalize_url(url)
        if not url:
            continue
        published = (_child_text(el, {"pubdate", "published", "date"})
                     or _child_text(el, {"updated", "issued"}))
        summary = (_child_text(el, {"description", "summary"})
                   or _child_text(el, {"encoded", "content"}))
        entries.append({
            "url": url,
            "title": title,
            "published": published,
            "summary": summary,
            "source_bucket": bucket,
        })
    return entries


# ---------------------------------------------------------------------------
# Cheap filters (pure, unit-tested)
# ---------------------------------------------------------------------------
def is_fresh(published: str | None, today: date,
             window: int = FRESHNESS_WINDOW_DAYS) -> bool:
    """Keep items published within `window` days. No-date items are kept."""
    d = parse_date(published)
    if d is None:
        return True
    return 0 <= (today - d).days <= window or d > today


def title_matches_negative(title: str, patterns: list[str]) -> bool:
    if not title:
        return False
    for pat in patterns:
        if re.search(pat, title, re.IGNORECASE):
            return True
    return False


def load_negative_patterns(home: str) -> list[str]:
    """Patterns from <home>/negative-anchors.txt (one regex per line) if present,
    else the built-in default. Keeps the literal set in one editable place."""
    path = os.path.join(home, "negative-anchors.txt")
    if os.path.exists(path):
        out = []
        with open(path, encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if line and not line.startswith("#"):
                    out.append(line)
        if out:
            return out
    return list(DEFAULT_NEGATIVE_PATTERNS)


def filter_candidates(entries: list[dict], seen_urls: set[str], today: date,
                      patterns: list[str],
                      window: int = FRESHNESS_WINDOW_DAYS) -> list[dict]:
    """Apply the four cheap drops in order, de-duping within the batch too."""
    out: list[dict] = []
    batch_seen: set[str] = set()
    for e in entries:
        url = e["url"]
        if url in seen_urls or url in batch_seen:
            continue
        if not is_fresh(e.get("published"), today, window):
            continue
        if title_matches_negative(e.get("title", ""), patterns):
            continue
        batch_seen.add(url)
        out.append(e)
    return out


# ---------------------------------------------------------------------------
# Selection (pure, unit-tested)
# ---------------------------------------------------------------------------
def select(scored: list[dict], count: int = DEFAULT_COUNT,
           floor: float = DEFAULT_FLOOR,
           cap: int = SAME_SOURCE_CAP) -> list[dict]:
    """Gate + rank + same-source cap + top-N. Input items carry a 'score' float.

    Items below `floor` are dropped (this is also the [SILENT] gate: empty
    result => nothing to push). Remaining items rank by score desc, newer first.
    No more than `cap` items per source_bucket. Overflow is simply not selected;
    it is NOT marked seen, so it re-competes next run while still in-window.
    """
    passing = [dict(it) for it in scored if float(it.get("score", 0)) >= floor]

    def sort_key(it):
        d = parse_date(it.get("published"))
        # higher score first; then newer published first; None date sorts last
        return (-float(it.get("score", 0)),
                -(d.toordinal() if d else 0))

    passing.sort(key=sort_key)

    selected: list[dict] = []
    per_bucket: dict[str, int] = {}
    for it in passing:
        if len(selected) >= count:
            break
        bucket = it.get("source_bucket", it.get("url", ""))
        if per_bucket.get(bucket, 0) >= cap:
            continue
        per_bucket[bucket] = per_bucket.get(bucket, 0) + 1
        selected.append(it)
    return selected


# ---------------------------------------------------------------------------
# Paths + tmp hygiene
# ---------------------------------------------------------------------------
def state_home(arg_home: str | None) -> str:
    if arg_home:
        return os.path.expanduser(arg_home)
    return os.path.expanduser(os.environ.get("DAILY_CURATOR_HOME", "~/.daily-curator"))


def _prune_tmp(tmp_dir: str, keep: int = TMP_KEEP_RUNS) -> None:
    """Keep only the last `keep` fetched-*.xml debug dumps."""
    if not os.path.isdir(tmp_dir):
        return
    dumps = sorted(
        (f for f in os.listdir(tmp_dir) if f.startswith("fetched-") and f.endswith(".xml")),
        reverse=True,
    )
    for stale in dumps[keep:]:
        try:
            os.remove(os.path.join(tmp_dir, stale))
        except OSError:
            pass


# ---------------------------------------------------------------------------
# Subcommands
# ---------------------------------------------------------------------------
def cmd_prepare(args) -> int:
    home = state_home(args.home)
    feeds_path = args.feeds or os.path.join(home, "feeds.txt")
    seen_path = os.path.join(home, "seen.txt")
    tmp_dir = os.path.join(home, "tmp")
    os.makedirs(tmp_dir, exist_ok=True)
    today = today_utc()

    if not os.path.exists(feeds_path):
        print(f"[error] feeds file not found: {feeds_path}", file=sys.stderr)
        return 2
    with open(feeds_path, encoding="utf-8") as fh:
        feeds = [ln.strip() for ln in fh
                 if ln.strip() and not ln.strip().startswith("#")]

    # Prune the seen ledger first, then snapshot it for the verifier.
    removed = prune_seen(seen_path, today, args.seen_window)
    seen_urls = load_seen_urls(seen_path)
    snapshot_path = os.path.join(tmp_dir, "seen-snapshot.json")
    with open(snapshot_path, "w", encoding="utf-8") as fh:
        json.dump(sorted(seen_urls), fh, ensure_ascii=False)

    patterns = load_negative_patterns(home)
    all_entries: list[dict] = []
    fetched_blobs: list[str] = []
    ok_feeds = 0
    for url in feeds:
        body = fetch_feed(url)
        if not body:
            continue
        ok_feeds += 1
        fetched_blobs.append(f"<!-- {url} -->\n{body}")
        all_entries.extend(parse_feed(body, url))

    candidates = filter_candidates(all_entries, seen_urls, today, patterns, args.window)

    # Debug dump (kept last N runs only), then prune older dumps.
    with open(os.path.join(tmp_dir, f"fetched-{today.isoformat()}.xml"), "w",
              encoding="utf-8") as fh:
        fh.write("\n".join(fetched_blobs))
    _prune_tmp(tmp_dir)

    out = {
        "generated_at": today.isoformat(),
        "window_days": args.window,
        "feeds_total": len(feeds),
        "feeds_ok": ok_feeds,
        "seen_pruned": removed,
        "seen_size": len(seen_urls),
        "count": len(candidates),
        "candidates": candidates,
    }
    cand_path = os.path.join(tmp_dir, f"candidates-{today.isoformat()}.json")
    with open(cand_path, "w", encoding="utf-8") as fh:
        json.dump(out, fh, ensure_ascii=False, indent=2)
    json.dump(out, sys.stdout, ensure_ascii=False, indent=2)
    print()
    print(f"[prepare] feeds {ok_feeds}/{len(feeds)} ok · {len(candidates)} candidates "
          f"· seen {len(seen_urls)} (-{removed}) · {cand_path}", file=sys.stderr)
    return 0


def cmd_select(args) -> int:
    with open(args.scored, encoding="utf-8") as fh:
        data = json.load(fh)
    scored = data.get("candidates", data) if isinstance(data, dict) else data
    selected = select(scored, args.count, args.floor)
    out = {"count": len(selected), "floor": args.floor, "selected": selected}
    json.dump(out, sys.stdout, ensure_ascii=False, indent=2)
    print()
    print(f"[select] {len(selected)}/{len(scored)} pass floor {args.floor} "
          f"(top {args.count}, cap {SAME_SOURCE_CAP})", file=sys.stderr)
    return 0


def cmd_mark_seen(args) -> int:
    home = state_home(args.home)
    seen_path = os.path.join(home, "seen.txt")
    with open(args.selected, encoding="utf-8") as fh:
        data = json.load(fh)
    items = data.get("selected", data) if isinstance(data, dict) else data
    urls = [it["url"] for it in items if it.get("url")]
    n = append_seen(seen_path, urls)
    print(f"[mark-seen] appended {n} url(s) to {seen_path}", file=sys.stderr)
    return 0


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description="daily-curator v3 deterministic pipeline")
    sub = p.add_subparsers(dest="cmd", required=True)

    pp = sub.add_parser("prepare", help="fetch + filter + dedup -> candidates.json")
    pp.add_argument("--home")
    pp.add_argument("--feeds")
    pp.add_argument("--window", type=int, default=FRESHNESS_WINDOW_DAYS)
    pp.add_argument("--seen-window", type=int, default=30)
    pp.set_defaults(func=cmd_prepare)

    ps = sub.add_parser("select", help="scored.json -> selected.json")
    ps.add_argument("--scored", required=True)
    ps.add_argument("--count", type=int, default=DEFAULT_COUNT)
    ps.add_argument("--floor", type=float, default=DEFAULT_FLOOR)
    ps.add_argument("--home")
    ps.set_defaults(func=cmd_select)

    pm = sub.add_parser("mark-seen", help="append selected URLs to seen.txt")
    pm.add_argument("--selected", required=True)
    pm.add_argument("--home")
    pm.set_defaults(func=cmd_mark_seen)

    args = p.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
