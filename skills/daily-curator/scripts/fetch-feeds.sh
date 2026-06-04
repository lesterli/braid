#!/usr/bin/env bash
#
# fetch-feeds.sh — Batch RSS/Atom fetcher
#
# Usage:
#   echo "https://example.com/feed.xml" | bash fetch-feeds.sh
#   bash fetch-feeds.sh feeds.txt
#
# Output: Raw XML for each feed, separated by markers.
# Unreachable feeds are skipped with a warning to stderr.

set -euo pipefail

UA="Mozilla/5.0 (compatible; DailyCurator/1.0)"
TIMEOUT=10
MARKER="---FEED-BOUNDARY---"

fetch_feed() {
  local url="$1"
  local body
  if body=$(curl -sL --max-time "$TIMEOUT" -A "$UA" "$url" 2>/dev/null); then
    if [ -n "$body" ]; then
      echo "$MARKER"
      echo "# URL: $url"
      echo "$body"
    else
      echo "[warn] Empty response: $url" >&2
    fi
  else
    echo "[warn] Unreachable: $url" >&2
  fi
}

# Read URLs from file argument or stdin
if [ $# -ge 1 ] && [ "$1" != "-" ]; then
  input="$1"
else
  input="/dev/stdin"
fi

while IFS= read -r url; do
  # Skip empty lines and comments
  [[ -z "$url" || "$url" == \#* ]] && continue
  fetch_feed "$url"
done < "$input"
