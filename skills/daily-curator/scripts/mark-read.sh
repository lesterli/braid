#!/usr/bin/env bash
#
# mark-read.sh — Move queued URLs into read.txt with reason=explicit.
#
# Usage:
#   mark-read.sh URL [URL...]
#   mark-read.sh --stdin              # read URLs from stdin (one per line)
#
# Storage (see SKILL.md for full data model):
#   ~/.daily-curator/queued.txt   JSONL — items still waiting to be read
#   ~/.daily-curator/read.txt     JSONL — items moved out of queue
#
# Behavior:
#   For each URL: find matching line in queued.txt, append it to read.txt
#   with added fields {"read_at": today, "reason": "explicit"}, and remove
#   it from queued.txt. URLs not found are reported on stderr.

set -euo pipefail

HOME_DIR="${DAILY_CURATOR_HOME:-$HOME/.daily-curator}"
QUEUED="$HOME_DIR/queued.txt"
READ="$HOME_DIR/read.txt"

mkdir -p "$HOME_DIR"
touch "$QUEUED" "$READ"

today=$(date +%Y-%m-%d)

urls=()
if [ "${1:-}" = "--stdin" ]; then
  while IFS= read -r line; do
    [ -n "$line" ] && urls+=("$line")
  done
elif [ $# -ge 1 ]; then
  urls=("$@")
else
  echo "Usage: mark-read.sh URL... | --stdin" >&2
  exit 1
fi

python3 - "$QUEUED" "$READ" "$today" "${urls[@]}" <<'PY'
import json, sys

def canon(url):
    """Strip #fragment for stable URL comparison across RSS quirks."""
    return url.split("#", 1)[0] if url else url

queued_path, read_path, today, *urls = sys.argv[1:]
url_set = {canon(u) for u in urls}

keep = []
matched = []
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
        if canon(obj.get("url", "")) in url_set:
            obj["read_at"] = today
            obj["reason"] = "explicit"
            matched.append(obj)
        else:
            keep.append(line)

with open(queued_path, "w") as f:
    for ln in keep:
        f.write(ln + "\n")

with open(read_path, "a") as f:
    for obj in matched:
        f.write(json.dumps(obj, ensure_ascii=False) + "\n")

matched_urls = {canon(m["url"]) for m in matched}
print(f"marked {len(matched)} as read")
for u in url_set - matched_urls:
    print(f"  [warn] not in queue: {u}", file=sys.stderr)
PY
