---
name: daily-curator
description: >-
  Generate a curated daily reading list of high-quality articles.
  Use when the user says "今日推荐", "今天读什么", "daily reads",
  "morning briefing", "推荐文章", "每日推荐", or invokes "$daily-curator".
  Also triggers on "本周推荐" (weekly mode) or "只看 AI" (category filter).
  Does NOT handle RSS subscription management, feed reader setup,
  or newsletter configuration.
---

# Daily Curator

A curator with taste — picks today's most worth-reading articles from high-quality sources.

## Inputs

- `mode`: daily (default) | weekly
- `category`: all (default) | ai | engineering | thinking
- `count`: 5–10 (default 7)
- `output_language`: user's language, fallback Chinese

## Feed Management

Users manage their feeds with simple conversational commands:

- "关注 https://example.com/feed.xml" → append to `~/.daily-curator/feeds.txt`
- "取消关注 example.com" → remove matching line from `feeds.txt`
- "我的信源" / "list feeds" → show current `feeds.txt` content
- "导入 OPML https://..." → run `scripts/import-opml.sh`, append all extracted URLs to `feeds.txt`

The file `~/.daily-curator/feeds.txt` is one URL per line, dead simple:

```
https://simonwillison.net/atom/entries/
https://jvns.ca/atom.xml
https://danluu.com/atom.xml
```

Lines starting with `#` are comments. Empty lines are ignored.

### Source Resolution Order

1. `~/.daily-curator/feeds.txt` — user's personal feeds (primary)
2. `references/curated-feeds.md` — built-in defaults (fallback if feeds.txt doesn't exist)

When `feeds.txt` exists, it IS the source list. The curated-feeds.md serves only as a starter template and reference for quality tier classification.

## Workflow

### Step 1: Load Sources

- If `~/.daily-curator/feeds.txt` exists, use it as the source list.
- Otherwise, fall back to extracting URLs from [references/curated-feeds.md](./references/curated-feeds.md).
- If the user specified a category filter, cross-reference against [references/curated-feeds.md](./references/curated-feeds.md) for category tags; user-added feeds without a known category are included in all categories.

### Step 2: Fetch Content

- Run `scripts/fetch-feeds.sh` to batch-fetch all feeds in one pass.
- If the script is unavailable, fall back to WebFetch for each feed URL.
- Collect from each entry: title, URL, published date, summary or description.

### Step 3: Score & Filter

- Read [references/scoring-and-filtering.md](./references/scoring-and-filtering.md).
- Apply the scoring formula: timeliness × source quality × content depth.
- Deduplicate by canonical URL and fuzzy title similarity.
- If a previous digest exists in conversation context, skip already-recommended items.

### Step 4: Select Top N

- Rank by composite score, select the top `count` items.
- If fewer than 3 items clear the quality bar, say so honestly rather than padding.
- Group by natural topic clusters when applicable.

### Step 5: Format Output

- Read [references/output-format.md](./references/output-format.md).
- Generate the structured reading list.

## Working Rules

- Never pad the list with low-quality items to meet `count`.
- Prefer depth over breadth — one great article beats three mediocre ones.
- Keep summaries grounded in actual content, not hallucinated.
- If a feed is unreachable, skip it silently (don't error the whole run).
- Same-topic merge: if 2+ articles cover the same event, keep the best and note `另见: SourceB`.

## Response Shape

- Short preamble: date + theme keywords.
- Numbered list of recommendations.
- Each item: title, source, one-line curator's note, link.
- Footer: source count and quality note.

## References

- Read [references/curated-feeds.md](./references/curated-feeds.md) for the source list.
- Read [references/scoring-and-filtering.md](./references/scoring-and-filtering.md) for scoring rules.
- Read [references/output-format.md](./references/output-format.md) for format details and examples.
