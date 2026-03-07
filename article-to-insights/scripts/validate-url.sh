#!/usr/bin/env bash
# Pre-check URL reachability and content quality before full article processing.
# Always exits 0 and outputs a verdict line for the caller to interpret.
# Non-zero exit only on script-level errors (missing argument, curl not found).
# Usage: validate-url.sh <url>

set -euo pipefail

url="${1:?Usage: validate-url.sh <url>}"

response=$(curl -sL -o /dev/null -w '%{http_code}\t%{content_type}\t%{size_download}\t%{url_effective}' \
  -A "Mozilla/5.0" --max-time 15 "$url" 2>/dev/null) || {
  echo "url: $url"
  echo "verdict: unreachable (curl failed)"
  exit 0
}

http_code=$(echo "$response" | cut -f1)
content_type=$(echo "$response" | cut -f2)
size_bytes=$(echo "$response" | cut -f3)
final_url=$(echo "$response" | cut -f4)

echo "url: $url"
[ "$final_url" != "$url" ] && echo "redirected_to: $final_url"
echo "status: $http_code"
echo "content_type: $content_type"
echo "size_bytes: $size_bytes"

# Verdict — always exit 0; caller reads the verdict line to decide next step.
if [ "$http_code" -lt 200 ] || [ "$http_code" -ge 400 ]; then
  echo "verdict: unreachable"
elif echo "$content_type" | grep -qiv "text/html\|text/plain\|application/xhtml+xml"; then
  echo "verdict: non_article (content_type: $content_type)"
elif [ "$size_bytes" -lt 1000 ]; then
  echo "verdict: thin_page (likely paywall, login gate, or stub)"
else
  echo "verdict: ok"
fi
