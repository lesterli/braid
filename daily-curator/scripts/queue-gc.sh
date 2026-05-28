#!/usr/bin/env bash
#
# queue-gc.sh — Sweep queued items older than TTL into read.txt.
#
# Usage:
#   queue-gc.sh [--ttl DAYS]    # default 21
#
# Behavior:
#   For each line in queued.txt: if queued_since < (today - TTL), move it
#   to read.txt with {"read_at": today, "reason": "ttl_gc"}.

set -euo pipefail

HOME_DIR="${DAILY_CURATOR_HOME:-$HOME/.daily-curator}"
QUEUED="$HOME_DIR/queued.txt"
READ="$HOME_DIR/read.txt"
TTL=21

if [ "${1:-}" = "--ttl" ]; then
  TTL="$2"; shift 2
fi

mkdir -p "$HOME_DIR"
touch "$QUEUED" "$READ"

today=$(date +%Y-%m-%d)

python3 - "$QUEUED" "$READ" "$today" "$TTL" <<'PY'
import json, sys
from datetime import date, timedelta

queued_path, read_path, today_str, ttl_str = sys.argv[1:]
ttl = int(ttl_str)
cutoff = (date.fromisoformat(today_str) - timedelta(days=ttl)).isoformat()

keep = []
expired = []
with open(queued_path) as f:
    for line in f:
        line = line.rstrip("\n")
        if not line.strip():
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError:
            keep.append(line)
            continue
        if obj.get("queued_since", "9999-12-31") < cutoff:
            obj["read_at"] = today_str
            obj["reason"] = "ttl_gc"
            expired.append(obj)
        else:
            keep.append(line)

with open(queued_path, "w") as f:
    for ln in keep:
        f.write(ln + "\n")

with open(read_path, "a") as f:
    for obj in expired:
        f.write(json.dumps(obj, ensure_ascii=False) + "\n")

print(f"gc'd {len(expired)} item(s) older than {ttl}d (cutoff={cutoff})")
PY
