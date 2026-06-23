#!/usr/bin/env python3
"""daily-curator v3 feed-health monitor.

The curator adds a third-party Anthropic scraper feed (and any of the 23 existing
feeds can quietly die). On a one-way push channel that goes [SILENT] on quiet
days, a dead feed is invisible — the warning would ride in a digest that never
sends. So health is tracked separately and alerts OUT OF BAND (the SKILL pushes
the alert even on a silent day).

Cadence-aware without modeling cadence
--------------------------------------
A working RSS/Atom feed always returns its backlog (its last ~10-25 items) on
every fetch, no matter how rarely the author publishes. So "feed returned >=1
parseable entry" is a HEALTH signal that is independent of publish cadence: a
monthly blog is "ok" every single day (backlog present), and only a feed that
404s / errors / returns nothing trends stale. That is why a monthly publisher
never false-alarms here, which the naive "0 items in 7 days" check got wrong.

(hnrss query feeds CAN legitimately return 0 on a quiet week, so the staleness
threshold is generous — default 14 days — to tolerate that.)

State: feed-health.json
    {"feeds": {"<url>": {"first_seen","last_ok","last_status","last_alert"}}, "updated"}

Alerts are rate-limited to once per `cadence_days` (default 7) per feed so a
persistently dead feed nags weekly, not daily.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import date

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from canon import parse_date, today_utc, state_home  # noqa: E402

HEALTH_FILE = "feed-health.json"
STALE_THRESHOLD_DAYS = 14
ALERT_CADENCE_DAYS = 7


def _path(home: str) -> str:
    return os.path.join(home, HEALTH_FILE)


def load_health(home: str) -> dict:
    p = _path(home)
    if not os.path.exists(p):
        return {"feeds": {}, "updated": ""}
    try:
        with open(p, encoding="utf-8") as fh:
            data = json.load(fh)
    except (json.JSONDecodeError, OSError):
        return {"feeds": {}, "updated": ""}
    data.setdefault("feeds", {})
    return data


def save_health(home: str, data: dict, today: date) -> None:
    data["updated"] = today.isoformat()
    tmp = _path(home) + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(data, fh, ensure_ascii=False, indent=2)
    os.replace(tmp, _path(home))


def record_run(home: str, statuses: dict, today: date | None = None) -> dict:
    """Update per-feed health from this run's fetch outcomes.

    statuses maps feed_url -> "ok" | "empty" | "unreachable" | "parse_error".
    last_ok is bumped to today only on "ok" (>=1 parsed entry). Returns the data.
    """
    if today is None:
        today = today_utc()
    data = load_health(home)
    stamp = today.isoformat()
    for url, status in statuses.items():
        feed = data["feeds"].setdefault(url, {"first_seen": stamp})
        feed["last_status"] = status
        if status == "ok":
            feed["last_ok"] = stamp
    save_health(home, data, today)
    return data


def stale_feeds(data: dict, today: date | None = None,
                threshold_days: int = STALE_THRESHOLD_DAYS) -> list[str]:
    """Feeds that haven't returned a parseable entry within threshold_days.

    A feed that has never been ok counts from first_seen (so a feed added and
    failing for two weeks is flagged), but only after the grace window.
    """
    if today is None:
        today = today_utc()
    out: list[str] = []
    for url, feed in data.get("feeds", {}).items():
        ref = feed.get("last_ok") or feed.get("first_seen")
        d = parse_date(ref)
        if d is None:
            continue
        if (today - d).days > threshold_days:
            out.append(url)
    return out


def due_for_alert(data: dict, stale: list[str], today: date | None = None,
                  cadence_days: int = ALERT_CADENCE_DAYS) -> list[str]:
    """Subset of stale feeds not alerted within cadence_days (avoid daily nag)."""
    if today is None:
        today = today_utc()
    due: list[str] = []
    for url in stale:
        last_alert = parse_date(data.get("feeds", {}).get(url, {}).get("last_alert"))
        if last_alert is None or (today - last_alert).days >= cadence_days:
            due.append(url)
    return due


def format_alert(due: list[str], data: dict) -> str:
    lines = [f"⚠️ 信源告警：{len(due)} 个信源疑似失效（>{STALE_THRESHOLD_DAYS} 天无可解析内容）"]
    for url in due:
        feed = data.get("feeds", {}).get(url, {})
        last_ok = feed.get("last_ok", "从未成功")
        lines.append(f"- {url}（最近正常：{last_ok}）")
    lines.append("请检查这些 feed 是否仍可访问。")
    return "\n".join(lines)


def cmd_check(args) -> int:
    home = state_home(args.home)
    today = today_utc()
    data = load_health(home)
    stale = stale_feeds(data, today, args.threshold)
    due = due_for_alert(data, stale, today, args.cadence)
    if not due:
        print(f"[health] ok — {len(stale)} stale, none due for alert", file=sys.stderr)
        return 0
    # rate-limit: stamp these so we don't re-alert until cadence elapses
    stamp = today.isoformat()
    for url in due:
        data["feeds"].setdefault(url, {})["last_alert"] = stamp
    save_health(home, data, today)
    print(format_alert(due, data))  # stdout = the deliverable alert
    return 0


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description="daily-curator feed-health monitor")
    sub = p.add_subparsers(dest="cmd", required=True)
    pc = sub.add_parser("check", help="emit an out-of-band alert if feeds are stale")
    pc.add_argument("--home")
    pc.add_argument("--threshold", type=int, default=STALE_THRESHOLD_DAYS)
    pc.add_argument("--cadence", type=int, default=ALERT_CADENCE_DAYS)
    pc.set_defaults(func=cmd_check)
    args = p.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
