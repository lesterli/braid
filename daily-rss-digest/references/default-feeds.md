# Default Feeds

Use this built-in source set when the user does not provide a custom source set.

Keep the default list intentionally small. The goal is a dependable starter summary, not broad coverage.

## Feed URLs

- Simon Willison Entries: `https://simonwillison.net/atom/entries/`
- Simon Willison TIL: `https://til.simonwillison.net/tils/feed.atom`
- Julia Evans Blog: `https://jvns.ca/atom.xml`
- Julia Evans TIL: `https://jvns.ca/til/atom.xml`

## Daily Run Heuristics

- Prefer entries published in the last `24-48` hours
- Ignore obviously duplicated titles or canonical URLs
- Cap candidate inspection per feed if the feed is noisy
- Optimize for new insights, engineering depth, and clear original thinking
- If the summary would be all weak items, send the empty-day heartbeat instead
