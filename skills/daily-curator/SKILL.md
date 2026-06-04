---
name: daily-curator
description: >-
  Curate a daily reading queue: ingest new RSS items, score against the user's
  taste profile, surface today's best new picks alongside spillover from
  previously-queued unread items. Persists a queue + read-history across runs.
  Use when the user says "今日推荐", "今天读什么", "daily reads", "morning briefing",
  "推荐文章", "每日推荐", "我的待读", "queue 状态", or invokes "$daily-curator".
  Also handles "已读 <url|fuzzy title>" → marks queue item as read.
  Does NOT handle RSS subscription management beyond simple feeds.txt edits,
  feed reader setup, or content rewriting for publication.
---

# Daily Curator

A reading-queue curator with daily ingestion. Every run:

1. Fetches new RSS items from `feeds.txt`
2. Scores them against `taste.md` using `q × r` (see scoring-and-filtering.md)
3. Produces a digest with two sections — **new arrivals** and **queue spillover**
4. Persists state: new items added to `queued.txt`, expired items GC'd to `read.txt`

The name "daily-curator" describes the **cadence** (you run it daily) not the
**content** (most positive-anchor sources are weekly/irregular, so the queue is
how long-form essays don't fall through the cracks).

## Inputs

- `count`: digest size, default **5** (across both sections combined)
- `queue_ttl_days`: how long unread items linger in `queued.txt`, default **21**
- `show`: `top` or `all`, default **top**. Use `all` when the user asks
  "显示全部", "剩下的", "更多", "show all", or a range like "第 6-9 条".
- `debug_scores`: default **false**. Use `true` only when the user asks why
  items ranked where they did, asks to audit scoring, or explicitly says
  "显示分数" / "show scores".
- `output_language`: user's language, fallback Chinese

(Removed in v2: `mode`, `category`, `ttl_days` — see migration note at bottom.)

## User-managed config

| File | Purpose |
|---|---|
| `~/.daily-curator/feeds.txt` | Personal RSS/Atom feed list |
| `~/.daily-curator/taste.md` | Taste profile: axes + positive/negative anchors |
| `~/.daily-curator/queued.txt` | JSONL — items shown but not yet read |
| `~/.daily-curator/read.txt` | JSONL — items moved out of queue |
| `~/.daily-curator/digests/YYYY-MM-DD.md` | Per-run output |

Users manage feeds with conversational commands:

- "关注 https://example.com/feed.xml" → append to `feeds.txt`
- "取消关注 example.com" → remove matching line
- "我的信源" / "list feeds" → show `feeds.txt`
- "导入 OPML https://..." → run `scripts/import-opml.sh`, append URLs
- "调整口味" / "edit taste" → show `taste.md`, accept edits
- "已读 <url|title 子串>" → run `scripts/mark-read.sh` (see Step 8)
- "我的待读" / "queue 状态" → cat queued.txt as a readable summary
- "更多" / "显示剩余" / "显示全部" / "第 6-9 条" → re-render queued items with
  clickable titles, continuing from the previous digest order when possible

## Workflow

### Step 0: Bootstrap (first run only)

```bash
mkdir -p ~/.daily-curator/digests
touch ~/.daily-curator/queued.txt ~/.daily-curator/read.txt
```

If `feeds.txt` missing → seed from
[references/curated-feeds.md](./references/curated-feeds.md).

If `taste.md` missing → copy
[references/taste-template.md](./references/taste-template.md) to
`~/.daily-curator/taste.md` and tell the user to edit it. Without a real
taste profile, every item scores neutrally and the digest is useless.

### Step 1: Queue GC

Before fetching anything, sweep expired queue items:

```bash
bash scripts/queue-gc.sh --ttl 21
```

This moves items where `queued_since < today - 21d` into `read.txt` with
`reason: ttl_gc`. Report the count to the user if non-zero.

### Step 2: Load Sources

Read `~/.daily-curator/feeds.txt`. Fall back to extracting URLs from
[references/curated-feeds.md](./references/curated-feeds.md) only if the
user's feeds.txt is unreadable (not just empty — empty is a real config).

### Step 3: Fetch Content

```bash
bash scripts/fetch-feeds.sh ~/.daily-curator/feeds.txt
```

Collect per entry: title, URL, published date, summary. Track
`sources_fetched_today` for the frontmatter.

### Step 4: Apply hard filters

In order:

1. **Window**: drop items where `published > 14d ago`. No-date items are kept.
2. **Stage 1 pre-filter** (cheap, no LLM): grep titles against literal
   negative-anchor patterns from `taste.md` (`融资|IPO|估值|震惊|取代|...`).
   Drop hits unconditionally.
3. **Already in queued.txt**: drop URLs already in the user's queue — they're
   not "new arrivals" any more. (They'll re-appear via spillover in Step 6.)
4. **Already in read.txt**: drop URLs already in read history. Never resurface.

Survivors of these four filters are **today's new candidates**.

**URL canonicalization** (load-bearing for filters 3 and 4): RSS feeds emit
inconsistent URL forms for the same article — Simon Willison's feed appends
`#atom-entries`, some feeds use trailing slash inconsistently. Before any URL
comparison or storage, **strip the `#fragment`** at minimum. Apply the same
canonicalization on both sides of the comparison (incoming RSS URL and stored
queued.txt / read.txt URL). The scripts already do this.

### Step 5: Score new candidates

Apply the formula (full details in
[references/scoring-and-filtering.md](./references/scoring-and-filtering.md)):

```
total = source_quality × relevance_to_user_taste
```

Hard drops on `r < 0.3` or `total < 0.4`.

### Step 6: Re-score the queue and load spillover candidates

For each item in `queued.txt`:

1. Re-compute `r` using **today's** `taste.md` (q is fixed from queue snapshot)
2. If `r < 0.3` → move to `read.txt` with `reason: taste_gc` (silent, but report
   count to the user at end of run)
3. Otherwise, this item is eligible for spillover, ranked by today's `total`

### Step 7: Select top N with same-source cap

Combine new candidates + queue-spillover candidates. Then:

1. Sort by `total` descending; tiebreaker = newer `published` first
2. Apply **same-source cap = 2** (HN feeds aggregated by domain — all
   `hnrss.org/*` count as one source). When cap is hit, the surplus item goes
   to `queued.txt` immediately (if not already there) with
   `reason: source_cap_deferred`.
3. Take top N (default 5), unless `show=all`. If both sections together produce
   fewer than N, the digest is short — never pad. **Items that scored but didn't make top N
   (and weren't cap-deferred) are simply dropped**: they'll be re-scored next
   run if still in the 14d window. They do NOT enter the queue.
4. Group output into two sub-sections:
   - **新加入**: items from Step 5
   - **从 queue 中精选**: items from Step 6 with `queued_since` shown
5. When `show=top` and more queued items exist than are displayed, end with a
   clear next action: "还有 N 篇在待读队列；说 `更多` / `显示全部` 查看。"

### Step 8: Persist

1. **Write digest file**: `~/.daily-curator/digests/YYYY-MM-DD.md`. Overwrite if
   exists. See [references/output-format.md](./references/output-format.md).

2. **Append new items to queued.txt** (JSONL — one item per line):
   ```json
   {"url":"...","queued_since":"YYYY-MM-DD","title":"...","source":"...","source_quality":1.2,"tracks":["..."],"summary_snippet":"..."}
   ```
   Items from the "新加入" section go in. Items from spillover are already in
   queued.txt — do NOT re-append.

### Step 9: Respond

Print the readable digest content to the chat. At the end, report GC effects
from Steps 1 & 6:

```
queue: +3 new · -2 ttl_gc · -1 taste_gc · 14 in queue
```

If `debug_scores=false`, do not display score details in the visible chat
output. Keep score metadata in the digest file using hidden HTML comments as
specified in [references/output-format.md](./references/output-format.md). If
`debug_scores=true`, add a compact "评分明细" section after the digest instead
of cluttering each item.

## Mark-as-read flow (separate invocation)

When the user says "已读 <url>" or "已读 <title 子串>":

1. If they gave a URL → call `bash scripts/mark-read.sh <URL>`
2. If they gave a fuzzy title → `grep` queued.txt for the title, extract URL,
   confirm with user, then call mark-read.sh
3. Confirm the move and report new queue size

## Working Rules

- Never pad to meet `count`. A short digest is honest.
- Prefer depth over breadth — one great article beats three mediocre ones.
- Keep summaries grounded in actual content, not hallucinated.
- If a feed is unreachable, skip it silently (don't error the whole run).
- The article title is the primary action. Always render it as a Markdown link:
  `**1. [Title](https://...)**`. Never output a bare, unclickable title when a
  URL is available.
- Do not prefix recommendations with boilerplate labels such as
  "一句话策展人点评：". The line after `Source:` should be the recommendation
  itself.
- Avoid generic repeated recommendations. Each item must name the article's
  specific object, claim, method, artifact, or tension. If the RSS summary is
  too thin to support that, say what is actually known instead of filling with
  a template.
- **Compute every score, but hide score metadata by default** — it lets
  downstream tools audit the run without forcing users to read machine details.
  Only show visible score details when `debug_scores=true`.
- **Always write the digest file**, even on empty days. The empty file is a
  signal that the day was processed.

## References

- [references/curated-feeds.md](./references/curated-feeds.md) — built-in source list & tier classification
- [references/scoring-and-filtering.md](./references/scoring-and-filtering.md) — scoring, GC rules, queue lifecycle
- [references/output-format.md](./references/output-format.md) — frontmatter contract, two-section template
- [references/taste-template.md](./references/taste-template.md) — starter template for new `taste.md`
- [scripts/fetch-feeds.sh](./scripts/fetch-feeds.sh) — batch RSS fetcher
- [scripts/import-opml.sh](./scripts/import-opml.sh) — OPML to URL extractor
- [scripts/mark-read.sh](./scripts/mark-read.sh) — explicit mark-as-read for queue items
- [scripts/queue-gc.sh](./scripts/queue-gc.sh) — TTL-based queue cleanup

## Downstream contract

`/daily-publisher` (a sibling skill, not yet implemented) consumes
`~/.daily-curator/digests/YYYY-MM-DD.md` by parsing:

1. YAML frontmatter (`date`, `sources_fetched_today`, `new_count`,
   `queue_filler_count`, `queue_size`, `theme_keywords`, `queue_ttl_days`)
2. Per-item hidden metadata comments with `_scores: q=... r=... → total ·
   tracks: [...]` (plus `queued_since: YYYY-MM-DD` for spillover items)
3. Filters by `tracks` to decide which items go to which output channel

Stability of the frontmatter field names and hidden `_scores:` metadata regex
is part of this contract. The score metadata is machine-readable, not part of
the default visible UX.

## Migration from v1 (2026-05)

v1 of this skill used a single `seen.txt` (URL + date) as a 7-day dedup cache.
v2 splits state into `queued.txt` (unread) + `read.txt` (processed), making
"item I haven't read" first-class instead of being implicitly tied to a TTL.

Removed inputs: `mode` (weekly was unused; 14-day window absorbs the case),
`category` (filter was never invoked), `ttl_days` (replaced by
`queue_ttl_days`, semantically different).

Removed file: `seen.txt` (one-shot migrated to `read.txt` with
`reason: legacy_migration`).

`_scores:` annotation dropped `t=` (timeliness) and `d=` (depth) in favor of
the two-dimensional `q × r` formula — see scoring-and-filtering.md for the
"why" of that earlier change.
