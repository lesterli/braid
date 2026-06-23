#!/usr/bin/env python3
"""Shared primitives for the daily-curator v3 pipeline.

The load-bearing correctness of the whole skill rests on two things living in
ONE place: URL canonicalization (so dedup never leaks) and the seen.txt ledger
(the only persistent state in v3). curate.py, migrate.py, and verify-run.py all
import from here so they can never disagree about what "the same URL" means.

seen.txt format
---------------
JSONL, one object per line:

    {"url": "<canonical url>", "date_shown": "YYYY-MM-DD"}

Append-only during a run; pruned to a rolling window (default 30d) at the start
of each run. An item published more than the freshness window (14d) ago can
never resurface, so seen rows older than 30d are dead weight and are dropped.

  feeds ──▶ canonicalize ──▶ (dedup vs seen) ──▶ ... ──▶ shown ──▶ append seen
                 ▲                  │                                   │
                 └──────────── same function ────────────────────── same file
"""
from __future__ import annotations

import json
import os
from datetime import date, datetime, timezone
from email.utils import parsedate_to_datetime
from urllib.parse import urlsplit, urlunsplit

DEFAULT_SEEN_WINDOW_DAYS = 30


def canonicalize_url(url: str) -> str:
    """Return a stable canonical form so the same article never dedups twice.

    Rules (mirror SKILL.md Step "URL canonicalization"):
      - lowercase scheme and host (case-insensitive per RFC 3986)
      - drop the #fragment (Simon Willison's feed appends #atom-entries)
      - strip a trailing slash from the path, except the root "/"
      - keep the query string untouched (some feeds need it)

    Whitespace is stripped. A blank or unparseable string returns "" so callers
    can drop it rather than store a junk key.
    """
    if not url:
        return ""
    url = url.strip()
    if not url:
        return ""
    try:
        parts = urlsplit(url)
    except ValueError:
        return ""
    scheme = parts.scheme.lower()
    netloc = parts.netloc.lower()
    # Drop a redundant default port so :80/:443 forms dedup with the bare host.
    if scheme == "http" and netloc.endswith(":80"):
        netloc = netloc[:-3]
    elif scheme == "https" and netloc.endswith(":443"):
        netloc = netloc[:-4]
    path = parts.path
    if len(path) > 1 and path.endswith("/"):
        path = path.rstrip("/")
        if path == "":
            path = "/"
    # fragment dropped; query preserved
    return urlunsplit((scheme, netloc, path, parts.query, ""))


def parse_date(value: str | None) -> date | None:
    """Parse an RSS (RFC 822) or Atom (RFC 3339 / ISO 8601) date to a date.

    Returns None when the value is missing or unparseable. No-date items are
    intentionally kept by the freshness filter, so None is a valid outcome.
    """
    if not value:
        return None
    value = value.strip()
    if not value:
        return None
    # Atom / ISO 8601 first (e.g. 2026-06-02T12:00:00Z, 2026-06-02)
    iso = value.replace("Z", "+00:00")
    try:
        return _utc_date(datetime.fromisoformat(iso))
    except ValueError:
        pass
    # RSS / RFC 822 (e.g. Mon, 02 Jun 2026 12:00:00 GMT)
    try:
        dt = parsedate_to_datetime(value)
        if dt is not None:
            return _utc_date(dt)
    except (TypeError, ValueError):
        pass
    # Bare date prefix fallback (e.g. "2026-06-02 ...")
    head = value[:10]
    try:
        return datetime.strptime(head, "%Y-%m-%d").date()
    except ValueError:
        return None


def today_utc() -> date:
    return datetime.now(timezone.utc).date()


def _utc_date(dt: datetime) -> date:
    """Calendar date of an instant in UTC. A tz-aware datetime is converted to
    UTC first so freshness (compared against today_utc) isn't off by a day for
    feeds that stamp local time, e.g. '...01:00:00 +0800' is 2026-06-01 UTC."""
    if dt.tzinfo is not None:
        dt = dt.astimezone(timezone.utc)
    return dt.date()


def read_jsonl(path: str):
    """Yield parsed objects from a JSONL file, tolerant of blank/malformed lines
    and a missing file. One place for the parse-tolerance rules so every reader
    (seen ledger, migration, shown ledger) agrees."""
    if not path or not os.path.exists(path):
        return
    with open(path, "r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                yield json.loads(line)
            except json.JSONDecodeError:
                continue


def state_home(arg_home: str | None = None) -> str:
    """Resolve the curator state dir: explicit arg, then $DAILY_CURATOR_HOME,
    then ~/.daily-curator. Single source of truth for all scripts."""
    if arg_home:
        return os.path.expanduser(arg_home)
    return os.path.expanduser(os.environ.get("DAILY_CURATOR_HOME", "~/.daily-curator"))


def unwrap_list(data, key: str) -> list:
    """Return a list from either a bare list or a {key: [...]} wrapper. Anything
    else (a dict missing `key`, a scalar) yields [] — never iterates dict keys,
    which would crash on `.get` downstream."""
    if isinstance(data, list):
        return data
    if isinstance(data, dict) and isinstance(data.get(key), list):
        return data[key]
    return []


def load_seen(path: str) -> list[dict]:
    """Read seen.txt as a list of {"url","date_shown"} dicts. Tolerant of blank
    lines and malformed rows (skips them rather than crashing a cron run)."""
    rows: list[dict] = []
    for obj in read_jsonl(path):
        url = canonicalize_url(obj.get("url", ""))
        if url:
            rows.append({"url": url, "date_shown": obj.get("date_shown", "")})
    return rows


def load_seen_urls(path: str) -> set[str]:
    """Canonical URL set for O(1) dedup lookups."""
    return {row["url"] for row in load_seen(path)}


def prune_seen(path: str, today: date | None = None,
               window_days: int = DEFAULT_SEEN_WINDOW_DAYS) -> int:
    """Drop seen rows whose date_shown is older than `window_days`.

    Rewrites the file in place. Returns the number of rows removed. Rows with a
    missing/unparseable date_shown are KEPT (fail safe — we would rather re-keep
    a dedup key than accidentally let an item resurface). No-op if the file is
    absent.
    """
    if not path or not os.path.exists(path):
        return 0
    if today is None:
        today = today_utc()
    rows = load_seen(path)
    kept: list[dict] = []
    removed = 0
    for row in rows:
        d = parse_date(row.get("date_shown"))
        if d is not None and (today - d).days > window_days:
            removed += 1
            continue
        kept.append(row)
    if removed:
        _write_seen(path, kept)
    return removed


def append_seen(path: str, urls, today: date | None = None) -> int:
    """Append canonical URLs to seen.txt with date_shown=today.

    De-dups against what is already in the file and within the batch, so a
    same-day re-run can't create duplicate rows. Returns rows appended.
    """
    if today is None:
        today = today_utc()
    existing = load_seen_urls(path)
    stamp = today.isoformat()
    appended = 0
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, "a", encoding="utf-8") as fh:
        for raw in urls:
            url = canonicalize_url(raw)
            if not url or url in existing:
                continue
            fh.write(json.dumps({"url": url, "date_shown": stamp},
                                ensure_ascii=False) + "\n")
            existing.add(url)
            appended += 1
    return appended


def _write_seen(path: str, rows: list[dict]) -> None:
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps({"url": row["url"],
                                 "date_shown": row.get("date_shown", "")},
                                ensure_ascii=False) + "\n")
    os.replace(tmp, path)
