---
name: daily-curator
description: >-
  Curate a short daily reading brief: fetch new RSS items, dedup against what
  you've already been shown, score the survivors against your taste profile, and
  deliver only the genuinely fresh picks — staying silent on days with nothing
  worth your time. Persists a single seen.txt dedup ledger across runs.
  Use when the user says "今日推荐", "今天读什么", "daily reads", "morning briefing",
  "推荐文章", "每日推荐", "本周精选", "weekly roundup", or invokes "$daily-curator".
  Does NOT manage RSS subscriptions beyond simple feeds.txt edits, set up a feed
  reader, or rewrite content for publication.
---

# Daily Curator

A short reading brief. The skill is split into two halves:

- **Mechanics (deterministic, shipped scripts — never improvise these).**
  `scripts/curate.py` fetches, canonicalizes URLs, dedups against `seen.txt`,
  drops stale + negative-anchor items, then selects the top picks. `migrate.py`
  and `verify-run.py` handle cutover and pre-delivery checks. Run them, do not
  re-author them.
- **Judgment (yours).** Between `prepare` and `select`, you score each candidate
  0–1 against `taste.md` and later write the one-line "why it matters". That is
  the only part that needs a model.

```
prepare (script) ──▶ candidates.json ──▶ [you score 0–1] ──▶ scored.json
                                                                  │
                          selected.json ◀── select (script) ◀─────┘
                                │
            [you write the digest prose] ──▶ mark-seen (script) ──▶ verify (script) ──▶ deliver
```

Why no queue: most positive-anchor sources publish weekly or slower, so on many
days there is nothing genuinely new. v3 handles that by staying **silent**, not
by recycling a stale queue. An item shown once is recorded in `seen.txt` and
never shown again; an item that doesn't make the cut isn't recorded, so it
re-competes tomorrow while still inside the 14-day freshness window.

## Inputs

- `count`: digest size, default **5** (hard cap 7).
- `output_language`: user's language, fallback Chinese.
- `mode`: `daily` (default) or `weekly` (the Sunday roundup — see below).
- `dry_run`: default **false**. When true, run everything but write the digest
  to `tmp/` only, do NOT mark-seen, and do NOT deliver — log what *would* push.
  Used for the post-install shadow period before going live.
- `force_regen`: default **false**. Bypass the same-day idempotency guard when
  you deliberately want to regenerate today's brief (e.g. after editing taste.md).

## User-managed config

| File | Purpose |
|---|---|
| `~/.daily-curator/feeds.txt` | Personal RSS/Atom feed list |
| `~/.daily-curator/taste.md` | Taste profile: axes + positive/negative anchors |
| `~/.daily-curator/seen.txt` | JSONL ledger of shown URLs (dedup only; auto-pruned to 30d) |
| `~/.daily-curator/negative-anchors.txt` | Optional: one regex per line; **extends** the built-in title pre-filter (does not replace it) |
| `~/.daily-curator/digests/YYYY-MM-DD.md` | Per-run output |

Conversational feed management (all persist to `feeds.txt`):

- "关注 https://example.com/feed.xml" → append to `feeds.txt`
- "取消关注 example.com" → remove matching line
- "我的信源" / "list feeds" → show `feeds.txt`
- "导入 OPML https://..." → run `scripts/import-opml.sh`, append URLs
- "调整口味" / "edit taste" → show `taste.md`, accept edits

(There is no mark-as-read flow in v3 — delivery is one-way, so "read state"
isn't tracked. `seen.txt` only answers "have I already shown this?".)

## Workflow (daily)

### Step 0: Bootstrap (first run only)
```bash
mkdir -p ~/.daily-curator/digests
```
If `feeds.txt` is missing → seed from
[references/curated-feeds.md](./references/curated-feeds.md). If `taste.md` is
missing → copy [references/taste-template.md](./references/taste-template.md)
and tell the user to edit it (without it, scoring is meaningless).

### Step 1: Idempotency guard
If `~/.daily-curator/digests/<today>.md` already exists and `force_regen` is
false → today already ran. Respond `[SILENT]` and stop. This prevents a retry or
manual re-run from pushing a second, different brief to a one-way channel.

### Step 2: Prepare candidates (deterministic)
```bash
python3 scripts/curate.py prepare
```
This prunes `seen.txt` to 30 days, snapshots it, fetches every feed, parses
RSS/Atom, canonicalizes URLs, and drops: items published >14d ago, URLs already
in `seen.txt`, and titles matching the negative-anchor pre-filter. It writes
`tmp/candidates-<today>.json` (also printed to stdout) with the survivors.

### Step 3: Score candidates (your judgment)
Read `taste.md`. For each candidate, assign `score` ∈ [0,1] for relevance to the
user's taste, then write the candidates back with a `score` field as
`tmp/scored.json` (same shape as candidates.json).

Score by **relative ranking, anchored to taste.md**, not by guessing an absolute
number in a vacuum (that is what collapsed v2's scores to a constant):

1. Pick 2–3 anchored exemplars from `taste.md` first — a clear primary-axis +
   positive-anchor item ≈ 0.9, a borderline tertiary item ≈ 0.5, a negative-anchor
   item ≈ 0.1 — and score everything relative to those.
2. Rank the candidates against each other; don't bunch them at one value.
3. Collapse to ≈0 anything matching a semantic negative anchor (funding, launch
   hype, policy/geopolitics without an engineering artifact, thin roundups).
See [references/scoring-and-filtering.md](./references/scoring-and-filtering.md).

### Step 4: Select (deterministic)
```bash
python3 scripts/curate.py select --scored tmp/scored.json
```
Applies the floor (default **0.4** — the [SILENT] gate), ranks by score then
recency, enforces a **same-source cap of 2** (all `hnrss.org/*` share one
bucket), and takes the top `count`. Writes `tmp/selected.json`. Items below the
floor or beyond the cap are simply not selected — they are NOT recorded, so they
re-compete next run.

### Step 5: Write the digest (only if there is content)
If `selected` is non-empty, write the digest as clean human Markdown, starting at
an H1, **no YAML frontmatter and no hidden score comments** (the v2 machine layer
is gone). Path: `~/.daily-curator/digests/<today>.md` on a normal run, but
**`tmp/digest-<today>.md` when `dry_run`** — so a shadow run never creates the
real file the Step 1 guard keys on. One item per pick:
```
**1. [Title](https://canonical-url)**
Source: <Source> · <Nd ago>
<one concrete line naming the article's actual artifact/claim/method>
```

### Step 6: Persist + verify (deterministic)
Let `<digest>` be the path written in Step 5. On a normal run:
```bash
python3 scripts/curate.py mark-seen --selected tmp/selected.json
python3 scripts/verify-run.py --selected tmp/selected.json --digest <digest> \
    --seen ~/.daily-curator/seen.txt --snapshot tmp/seen-snapshot.json
python3 scripts/health.py check   # prints a stale-feed alert (or nothing) — see Step 7
```
If `verify-run.py` exits non-zero, do NOT deliver — report the failure instead.
In `dry_run`: skip `mark-seen` (state stays untouched), still run `verify-run` and
`health.py check` against the tmp digest, and log the brief that *would* push.

### Step 7: Deliver (a feed alert can override silence)
Decide the final reply by precedence:
- **Content day** (`selected` non-empty): reply with the digest body from the H1
  down. If `health.py check` printed an alert, append it as a short trailer.
- **Silent day + feed alert**: reply with the health alert text — NOT `[SILENT]`
  — so a broken feed surfaces even when there is nothing to recommend.
- **Silent day, no alert**: reply with exactly `[SILENT]`.

Never call send_message; cron delivers the reply to Feishu. In `dry_run`, deliver
nothing — just log what would have been sent.

## Workflow (weekly roundup — `mode=weekly`, Sundays)
The weekly run is the **heartbeat**: it always delivers, so the channel never
goes dark for a week (and a 7-day silence then means something is broken).
```bash
python3 scripts/curate.py roundup --days 7   # items from the last 7 daily digests
```
`roundup` returns the week's shown items ranked best-first (by score). Pick the
3–5 strongest — no new scoring — and write a short "本周精选" brief in the weekly
format (see [references/output-format.md](./references/output-format.md)). Write it
to `~/.daily-curator/digests/<today>-weekly.md` (a distinct name so it never
collides with the daily file or the daily idempotency guard). If the week produced
nothing, send a one-line "本周无新增。" rather than `[SILENT]`.

Note: this heartbeat only holds once the Sunday `mode=weekly` cron entry is
installed (see the cutover playbook); nothing else triggers the weekly run.

## Feed health
`curate.py prepare` records each feed's fetch outcome to `feed-health.json`.
`scripts/health.py check` flags any feed that has returned no parseable entry for
> 14 days and emits an out-of-band alert (delivered even on silent days — see
Step 7), rate-limited to once a week per feed. This is cadence-aware *without*
modeling cadence: a healthy feed always serves its backlog, so a monthly
publisher stays "ok" every day and never false-alarms; only a genuinely broken
feed — including the third-party Anthropic Engineering scraper — trends stale.

## Working Rules
- Never pad to meet `count`. A short brief, or `[SILENT]`, is honest.
- Depth over breadth — one great article beats three mediocre ones.
- Always render the title as a clickable Markdown link; never a bare title.
- No boilerplate lead-ins ("一句话点评："). The line after `Source:` is the point.
- Each recommendation must name the article's specific artifact, claim, method,
  or tension — not a generic category. If the RSS summary is too thin to support
  that, say what is actually known.
- Keep summaries grounded in the fetched content, never hallucinated.
- Run the scripts; do not re-implement their logic inline.

## References
- [scripts/curate.py](./scripts/curate.py) — prepare / select / mark-seen / roundup
- [scripts/health.py](./scripts/health.py) — feed-health tracking + stale-feed alert
- [scripts/migrate.py](./scripts/migrate.py) — one-shot v2→v3 state migration
- [scripts/verify-run.py](./scripts/verify-run.py) — pre-delivery invariant check
- [scripts/canon.py](./scripts/canon.py) — shared URL canonicalization + seen.txt ledger
- [scripts/tests/](./scripts/tests/) — `python3 -m unittest` suite
- [scripts/import-opml.sh](./scripts/import-opml.sh) — OPML → URL extractor
- [references/curated-feeds.md](./references/curated-feeds.md) — built-in source list & tiers
- [references/scoring-and-filtering.md](./references/scoring-and-filtering.md) — scoring guidance
- [references/taste-template.md](./references/taste-template.md) — starter `taste.md`

## Migration from v2 (2026-06)
v2 kept a persistent `queued.txt` + `read.txt` with spillover, TTL/taste GC, a
mark-read flow, and a two-section digest with hidden `_scores`/YAML frontmatter.
In practice the queue silted (nobody marks read on a one-way push channel), the
same items recycled for days, and the LLM-authored scorer collapsed to a
constant. v3 replaces all of it with one `seen.txt` dedup ledger, deterministic
shipped scripts, a silent-unless-fresh gate, and a clean human-only digest.

Run once at cutover:
```bash
python3 scripts/migrate.py --dry-run   # preview: seeds seen.txt, purges tmp bloat
python3 scripts/migrate.py             # backs up queued/read, seeds seen.txt, reclaims disk
```
Removed: `queued.txt`, `read.txt`, `queue-gc.sh`, `mark-read.sh`, the `mode`
(v2-internal), `queue_ttl_days`, `show`, `debug_scores` inputs, the `q × r`
formula, tracks, hidden `_scores`, and YAML frontmatter.
