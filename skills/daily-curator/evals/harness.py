#!/usr/bin/env python3
"""Isolated evaluation harness for daily-curator.

Every EvalHome is a TemporaryDirectory passed as --home. Scripts run
from $SKILL_DIR. Fixtures are file:// RSS, taste profiles, ledgers, and
scored JSON. Evaluations never read or write ~/.daily-curator.
"""
from __future__ import annotations

import os
import re
import subprocess
import sys
import tempfile
from datetime import datetime, timedelta, timezone
from email.utils import format_datetime

EVALS_DIR = os.path.dirname(os.path.abspath(__file__))
SKILL_DIR = os.path.dirname(EVALS_DIR)
SCRIPTS_DIR = os.path.join(SKILL_DIR, "scripts")
FIXTURES_DIR = os.path.join(EVALS_DIR, "fixtures")

sys.path.insert(0, SCRIPTS_DIR)
from canon import today_utc  # noqa: E402

STATE_FILES = (
    "seen.txt",
    "shown.jsonl",
    "feed-health.json",
    "taste.md",
    "feeds.txt",
)


def _today() -> datetime:
    return datetime.now(timezone.utc)


def render_placeholders(text: str) -> str:
    """Fill {{TODAY}}, {{DAYS_AGO:N}}, {{PUBDATE}} from UTC now."""
    now = _today()
    today = today_utc()

    def days_ago(match: re.Match) -> str:
        n = int(match.group(1))
        return (today - timedelta(days=n)).isoformat()

    text = text.replace("{{TODAY}}", today.isoformat())
    text = text.replace("{{PUBDATE}}", format_datetime(now, usegmt=True))
    return re.sub(r"\{\{DAYS_AGO:(\d+)\}\}", days_ago, text)


class EvalHome:
    """One isolated curator install for a single evaluation."""

    def __init__(self) -> None:
        self._tmp = tempfile.TemporaryDirectory(prefix="daily-curator-eval-")
        self.home = self._tmp.name
        os.makedirs(self.path("tmp"), exist_ok=True)
        os.makedirs(self.path("digests"), exist_ok=True)

    def close(self) -> None:
        self._tmp.cleanup()

    def __enter__(self) -> "EvalHome":
        return self

    def __exit__(self, *exc) -> None:
        self.close()

    def path(self, *parts: str) -> str:
        return os.path.join(self.home, *parts)

    def fixture(self, *parts: str) -> str:
        return os.path.join(FIXTURES_DIR, *parts)

    def _install_text(self, dest: str, src: str) -> str:
        with open(src, encoding="utf-8") as fh:
            body = render_placeholders(fh.read())
        os.makedirs(os.path.dirname(os.path.abspath(dest)), exist_ok=True)
        with open(dest, "w", encoding="utf-8") as fh:
            fh.write(body)
        return dest

    def install_taste(self, name: str = "valid.md") -> str:
        return self._install_text(self.path("taste.md"), self.fixture("taste", name))

    def install_seen(self, name: str = "seen-empty.txt") -> str:
        return self._install_text(self.path("seen.txt"), self.fixture("state", name))

    def install_shown(self, name: str = "shown-empty.jsonl") -> str:
        return self._install_text(self.path("shown.jsonl"), self.fixture("state", name))

    def install_scored(self, name: str) -> str:
        dest = self.path("tmp", "scored.json")
        return self._install_text(dest, self.fixture("scored", name))

    def install_feed_xml(self, name: str) -> str:
        """Copy an RSS fixture into the home and point feeds.txt at file:// it."""
        dest = self.path("feeds", name)
        self._install_text(dest, self.fixture("feeds", name))
        url = "file://" + dest
        with open(self.path("feeds.txt"), "w", encoding="utf-8") as fh:
            fh.write(url + "\n")
        return dest

    def write_digest(self, body: str, *, dry_run: bool = False) -> str:
        stamp = today_utc().isoformat()
        if dry_run:
            dest = self.path("tmp", f"digest-{stamp}.md")
        else:
            dest = self.path("digests", f"{stamp}.md")
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        with open(dest, "w", encoding="utf-8") as fh:
            fh.write(body)
        return dest

    def snapshot(self) -> dict[str, str | None]:
        """Map relative state path → file text (None if missing)."""
        out: dict[str, str | None] = {}
        for name in STATE_FILES:
            p = self.path(name)
            if os.path.isfile(p):
                with open(p, encoding="utf-8") as fh:
                    out[name] = fh.read()
            else:
                out[name] = None
        digests = self.path("digests")
        if os.path.isdir(digests):
            for fn in sorted(os.listdir(digests)):
                with open(os.path.join(digests, fn), encoding="utf-8") as fh:
                    out[f"digests/{fn}"] = fh.read()
        return out

    def changed(self, before: dict[str, str | None],
                after: dict[str, str | None] | None = None) -> set[str]:
        if after is None:
            after = self.snapshot()
        keys = set(before) | set(after)
        return {k for k in keys if before.get(k) != after.get(k)}

    def run(self, argv: list[str]) -> subprocess.CompletedProcess:
        """Run a script from $SKILL_DIR/scripts with this home.

        argv[0] is the script basename (curate.py, verify-run.py, health.py).
        --home is injected for curate.py / health.py unless already present.
        """
        if not argv:
            raise ValueError("run() needs a script name")
        script, *rest = argv
        cmd = [sys.executable, os.path.join(SCRIPTS_DIR, script), *rest]
        accepts_home = script in {"curate.py", "health.py"}
        if accepts_home and "--home" not in rest:
            cmd.extend(["--home", self.home])
        return subprocess.run(
            cmd, cwd=SKILL_DIR, capture_output=True, text=True, check=False,
        )

    def real_install_untouched(self) -> bool:
        """True when this home is not the user's real ~/.daily-curator."""
        real = os.path.realpath(os.path.expanduser("~/.daily-curator"))
        return os.path.realpath(self.home) != real
