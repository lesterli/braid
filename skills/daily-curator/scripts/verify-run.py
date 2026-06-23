#!/usr/bin/env python3
"""daily-curator v3 run verifier — the unattended safety net before delivery.

The cron pushes to a one-way Feishu channel, so a broken run is invisible unless
something checks it first. This asserts the invariants v3 actually guarantees,
sized to v3 (the old frontmatter/_scores/queue checks are gone with the queue).

Checks (exit 1 on any failure, 0 if clean):
  content runs (selected non-empty):
    - digest file exists and is non-empty
    - digest body starts at an H1 ("# "), with no YAML frontmatter or hidden
      _scores comment leaking into what gets delivered
    - every shown URL is present in seen.txt        (dedup integrity)
    - no shown URL was already in seen BEFORE the run (didn't re-show a seen item)
  silent runs (selected empty): nothing to verify; a [SILENT] day is valid.

Usage:
  verify-run.py --selected selected.json --digest digests/<date>.md \\
                --seen ~/.daily-curator/seen.txt --snapshot tmp/seen-snapshot.json
"""
from __future__ import annotations

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from canon import canonicalize_url, load_seen_urls  # noqa: E402


def _load_selected_urls(path: str) -> list[str]:
    with open(path, encoding="utf-8") as fh:
        data = json.load(fh)
    items = data.get("selected", data) if isinstance(data, dict) else data
    return [canonicalize_url(it["url"]) for it in items if it.get("url")]


def _load_snapshot(path: str | None) -> set[str]:
    if not path or not os.path.exists(path):
        return set()
    with open(path, encoding="utf-8") as fh:
        data = json.load(fh)
    return {canonicalize_url(u) for u in data if u}


def check_digest_body(text: str) -> list[str]:
    """Return a list of problems with the digest body (empty = clean)."""
    problems: list[str] = []
    stripped = text.lstrip()
    if not stripped:
        problems.append("digest file is empty")
        return problems
    if stripped.startswith("---"):
        problems.append("digest leaks YAML frontmatter (starts with '---')")
    first = stripped.splitlines()[0]
    if not first.startswith("# "):
        problems.append(f"digest body does not start at an H1: {first!r}")
    if "<!-- _scores" in text:
        problems.append("digest leaks hidden _scores comment (dropped in v3)")
    return problems


def verify(selected_urls: list[str], digest_path: str, seen_urls: set[str],
           snapshot_urls: set[str]) -> list[str]:
    """Pure check core. Returns a list of failure strings (empty = PASS)."""
    failures: list[str] = []

    if not selected_urls:
        return failures  # [SILENT] day — valid, nothing delivered

    if not digest_path or not os.path.exists(digest_path):
        failures.append(f"content selected but digest missing: {digest_path}")
    else:
        with open(digest_path, encoding="utf-8") as fh:
            failures.extend(check_digest_body(fh.read()))

    missing = [u for u in selected_urls if u not in seen_urls]
    if missing:
        failures.append(f"{len(missing)} shown URL(s) not in seen.txt "
                        f"(dedup integrity): {missing[:3]}")

    re_shown = [u for u in selected_urls if u in snapshot_urls]
    if re_shown:
        failures.append(f"{len(re_shown)} shown URL(s) were already seen before "
                        f"this run (re-showed a seen item): {re_shown[:3]}")

    return failures


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description="daily-curator v3 run verifier")
    p.add_argument("--selected", required=True)
    p.add_argument("--digest", required=True)
    p.add_argument("--seen", required=True)
    p.add_argument("--snapshot")
    args = p.parse_args(argv)

    selected_urls = _load_selected_urls(args.selected)
    seen_urls = load_seen_urls(args.seen)
    snapshot_urls = _load_snapshot(args.snapshot)

    failures = verify(selected_urls, args.digest, seen_urls, snapshot_urls)

    if not selected_urls:
        print("[verify] PASS — [SILENT] day, nothing to deliver")
        return 0
    if failures:
        print(f"[verify] FAIL — {len(failures)} problem(s):", file=sys.stderr)
        for f in failures:
            print(f"  - {f}", file=sys.stderr)
        return 1
    print(f"[verify] PASS — {len(selected_urls)} item(s), digest + dedup integrity OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
