#!/usr/bin/env python3
"""daily-curator v2 -> v3 one-shot migration.

What it does (in order):
  1. Guard: refuse if seen.txt already has content (don't double-seed) unless --force.
  2. Back up queued.txt + read.txt to <home>/.curator_backups/<ts>/.
  3. Seed seen.txt with every canonical URL from queued.txt + read.txt,
     date_shown = today. Those 41-ish items have all been shown for weeks, so
     marking them seen is correct AND stops the recycling from day one.
  4. Remove queued.txt + read.txt (already backed up).
  5. Purge transient bloat: tmp_fetch.out + tmp/* (the ~230MB of fetched XML and
     LLM-generated per-run scripts that v3 no longer creates). Not backed up —
     it is regenerable junk.

Safe to dry-run first (--dry-run). Destructive step is gated and reversible via
the backup. State dir defaults to $DAILY_CURATOR_HOME or ~/.daily-curator.

    queued.txt ┐
               ├─ extract url → canonicalize → dedup → seen.txt (date_shown=today)
    read.txt   ┘
    queued.txt, read.txt ──▶ backup/ ──▶ delete
    tmp_fetch.out, tmp/*  ──▶ delete (purge)
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from canon import canonicalize_url, append_seen, load_seen_urls, today_utc  # noqa: E402


def extract_urls(jsonl_path: str) -> list[str]:
    """Canonical URLs from a v2 queued.txt/read.txt JSONL file, in file order.
    Tolerant of blank/malformed lines. Missing file -> []."""
    urls: list[str] = []
    if not os.path.exists(jsonl_path):
        return urls
    with open(jsonl_path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue
            url = canonicalize_url(obj.get("url", ""))
            if url:
                urls.append(url)
    return urls


def dedupe(urls: list[str]) -> list[str]:
    """Order-preserving dedup."""
    seen: set[str] = set()
    out: list[str] = []
    for u in urls:
        if u not in seen:
            seen.add(u)
            out.append(u)
    return out


def _dir_size(path: str) -> int:
    total = 0
    if os.path.isfile(path):
        return os.path.getsize(path)
    for root, _dirs, files in os.walk(path):
        for f in files:
            try:
                total += os.path.getsize(os.path.join(root, f))
            except OSError:
                pass
    return total


def _human(n: int) -> str:
    for unit in ("B", "KB", "MB", "GB"):
        if n < 1024 or unit == "GB":
            return f"{n:.1f}{unit}" if unit != "B" else f"{n}B"
        n /= 1024
    return f"{n:.1f}GB"


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description="daily-curator v2->v3 migration")
    p.add_argument("--home")
    p.add_argument("--force", action="store_true",
                   help="seed even if seen.txt already has content")
    p.add_argument("--dry-run", action="store_true",
                   help="report what would happen; change nothing")
    p.add_argument("--no-purge", action="store_true",
                   help="keep tmp_fetch.out and tmp/* (skip the disk reclaim)")
    args = p.parse_args(argv)

    home = os.path.expanduser(
        args.home or os.environ.get("DAILY_CURATOR_HOME", "~/.daily-curator"))
    seen_path = os.path.join(home, "seen.txt")
    queued = os.path.join(home, "queued.txt")
    read = os.path.join(home, "read.txt")
    today = today_utc()
    dry = args.dry_run

    if not os.path.isdir(home):
        print(f"[error] state dir not found: {home}", file=sys.stderr)
        return 2

    existing = load_seen_urls(seen_path)
    if existing and not args.force:
        print(f"[error] {seen_path} already has {len(existing)} entries; "
              f"refusing to re-migrate. Use --force to override.", file=sys.stderr)
        return 2

    urls = dedupe(extract_urls(queued) + extract_urls(read))
    print(f"[migrate] {'(dry-run) ' if dry else ''}seed {len(urls)} canonical "
          f"URL(s) from queued.txt + read.txt -> seen.txt", file=sys.stderr)

    # 1. Backup
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H-%M-%SZ")
    backup_dir = os.path.join(home, ".curator_backups", ts)
    for src in (queued, read):
        if os.path.exists(src):
            if dry:
                print(f"[migrate] would back up {os.path.basename(src)} -> {backup_dir}/",
                      file=sys.stderr)
            else:
                os.makedirs(backup_dir, exist_ok=True)
                shutil.copy2(src, os.path.join(backup_dir, os.path.basename(src)))

    # 2. Seed seen.txt
    if dry:
        print(f"[migrate] would append {len(urls)} rows (date_shown={today})",
              file=sys.stderr)
    else:
        appended = append_seen(seen_path, urls, today)
        print(f"[migrate] seeded {appended} new row(s) into {seen_path}",
              file=sys.stderr)

    # 3. Remove migrated state files
    for src in (queued, read):
        if os.path.exists(src):
            if dry:
                print(f"[migrate] would delete {src}", file=sys.stderr)
            else:
                os.remove(src)

    # 4. Purge transient bloat
    if not args.no_purge:
        targets = [os.path.join(home, "tmp_fetch.out"), os.path.join(home, "tmp")]
        freed = 0
        for t in targets:
            if not os.path.exists(t):
                continue
            freed += _dir_size(t)
            if dry:
                print(f"[migrate] would purge {t} ({_human(_dir_size(t))})",
                      file=sys.stderr)
            else:
                if os.path.isdir(t):
                    shutil.rmtree(t, ignore_errors=True)
                    os.makedirs(t, exist_ok=True)  # curate.py recreates content
                else:
                    os.remove(t)
        print(f"[migrate] {'would free' if dry else 'freed'} {_human(freed)} of transient files",
              file=sys.stderr)

    print(f"[migrate] {'DRY-RUN complete, nothing changed' if dry else 'done'}.",
          file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
