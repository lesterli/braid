#!/usr/bin/env bash
#
# import-opml.sh — Extract feed URLs from an OPML file
#
# Usage:
#   bash import-opml.sh feeds.opml
#   bash import-opml.sh https://example.com/feeds.opml
#   curl -sL https://example.com/feeds.opml | bash import-opml.sh
#
# Output: One feed URL per line (suitable for piping to fetch-feeds.sh)

set -euo pipefail

UA="Mozilla/5.0 (compatible; DailyCurator/1.0)"

get_content() {
  local input="${1:--}"
  if [[ "$input" == http://* || "$input" == https://* ]]; then
    curl -sL --max-time 15 -A "$UA" "$input"
  elif [[ "$input" == "-" ]]; then
    cat
  else
    cat "$input"
  fi
}

# Extract xmlUrl attributes from OPML outline elements
get_content "${1:--}" \
  | grep -oE 'xmlUrl="[^"]*"' \
  | sed 's/xmlUrl="//;s/"$//' \
  | sort -u
