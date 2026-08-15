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
  `$SKILL_DIR/scripts/curate.py` fetches, canonicalizes URLs, dedups against
  `seen.txt`, drops stale + negative-anchor items, then selects the top picks.
  `$SKILL_DIR/scripts/verify-run.py` handles pre-delivery checks. Run them, do
  not re-author them.
- **Judgment (yours).** Between `prepare` and `select`, you score each candidate
  0–1 against `taste.md` and later write the one-line "why it matters". That is
  the only part that needs a model.

```
prepare ──▶ tmp/candidates-YYYY-MM-DD.json ──▶ [you score 0–1] ──▶ tmp/scored.json
                                                                              │
              tmp/selected.json ◀── select (stdout, redirect) ◀───────────────┘
                                │
            [you write the digest prose] ──▶ mark-seen ──▶ verify ──▶ deliver
```

## Paths

All commands run from `$SKILL_DIR` — the directory that contains this `SKILL.md`.
Never invoke a bare relative `scripts/...` path from another working directory.

| Variable | Meaning |
|---|---|
| `$SKILL_DIR` | This skill directory (contains `SKILL.md` and `scripts/`) |
| `$DAILY_CURATOR_HOME` | State directory. Defaults to `~/.daily-curator` (override with the `$DAILY_CURATOR_HOME` env var or `--home`). |

Dates in working filenames are **UTC today** as `YYYY-MM-DD` — the same clock
`prepare` uses (`canon.today_utc()`). Example: `tmp/candidates-2026-08-15.json`.

Most positive-anchor sources publish weekly or slower, so on many days there is
nothing genuinely new. The skill stays **silent** rather than padding. An item
shown once is recorded in `seen.txt` and never shown again; an item that doesn't
make the cut isn't recorded, so it re-competes tomorrow while still inside the
14-day freshness window.

## Inputs

- `count`: digest size, default **5** (hard cap 7).
- `output_language`: user's language, fallback Chinese.
- `mode`: `daily` (default) or `weekly` (the Sunday roundup — see below).
- `dry_run`: default **false**. When true, write the digest under `tmp/` only,
  skip `mark-seen`, verify with `--dry-run`, and do NOT deliver — log what
  *would* push. Used for the post-install shadow period before going live.
- `force_regen`: default **false**. Bypass the same-day idempotency guard when
  you deliberately want to regenerate today's brief (e.g. after editing taste.md).

## User-managed config

| File | Purpose |
|---|---|
| `$DAILY_CURATOR_HOME/feeds.txt` | Personal RSS/Atom feed list (seeded by bootstrap) |
| `$DAILY_CURATOR_HOME/taste.md` | Taste profile: axes + positive/negative anchors (copied from the template by bootstrap) |
| `$DAILY_CURATOR_HOME/negative-anchors.txt` | Optional: one regex per line; **extends** the built-in title pre-filter (does not replace it) |

## Skill-owned state

Created empty on first bootstrap; later runs fill them in. Do not seed these by hand.

| File | Purpose |
|---|---|
| `$DAILY_CURATOR_HOME/seen.txt` | JSONL dedup ledger of shown URLs (auto-pruned to 30d) |
| `$DAILY_CURATOR_HOME/shown.jsonl` | JSONL ledger of shown items |
| `$DAILY_CURATOR_HOME/feed-health.json` | Per-feed fetch health |
| `$DAILY_CURATOR_HOME/digests/YYYY-MM-DD.md` | Daily digest (UTC date) |
| `$DAILY_CURATOR_HOME/tmp/candidates-YYYY-MM-DD.json` | `prepare` output (UTC date) |
| `$DAILY_CURATOR_HOME/tmp/scored.json` | Agent-written scores (same shape as the prepare output) |
| `$DAILY_CURATOR_HOME/tmp/selected.json` | `select` stdout redirected here |
| `$DAILY_CURATOR_HOME/tmp/seen-snapshot.json` | Pre-run `seen.txt` snapshot for the verifier |
| `$DAILY_CURATOR_HOME/tmp/digest-YYYY-MM-DD.md` | Dry-run digest only |

Conversational feed management (all persist to `feeds.txt`):

- "关注 https://example.com/feed.xml" → append to `feeds.txt`
- "取消关注 example.com" → remove matching line
- "我的信源" / "list feeds" → show `feeds.txt`
- "导入 OPML https://..." → run `bash "$SKILL_DIR/scripts/import-opml.sh"`, append URLs
- "调整口味" / "edit taste" → show `taste.md`, accept edits

(Delivery is one-way, so read state isn't tracked. `seen.txt` only answers
"have I already shown this?".)

## Workflow (daily)

### Step 0: Bootstrap (the only setup path)
```bash
python3 "$SKILL_DIR/scripts/curate.py" bootstrap --home "$DAILY_CURATOR_HOME"
```
Creates `$DAILY_CURATOR_HOME` (plus `digests/` and `tmp/`) if needed. Seeds
`feeds.txt` from [references/curated-feeds.md](./references/curated-feeds.md)
and `taste.md` from [references/taste-template.md](./references/taste-template.md)
when those files are missing, and initializes empty `seen.txt`, `shown.jsonl`,
and `feed-health.json` on demand. Idempotent: a second run on an initialized
install changes nothing. Tell the user to edit `taste.md` (without it, scoring
is meaningless). Do not mkdir or copy these files by hand — this command is
the only setup path.

### Step 1: Idempotency guard
If `$DAILY_CURATOR_HOME/digests/YYYY-MM-DD.md` already exists (UTC today) and
`force_regen` is false → today already ran. Respond `[SILENT]` and stop. This
prevents a retry or manual re-run from pushing a second, different brief to a
one-way channel.

### Step 2: Prepare candidates (deterministic)
```bash
python3 "$SKILL_DIR/scripts/curate.py" prepare --home "$DAILY_CURATOR_HOME"
```
This prunes `seen.txt` to 30 days, snapshots it, fetches every feed, parses
RSS/Atom, canonicalizes URLs, and drops: items published >14d ago, URLs already
in `seen.txt`, and titles matching the negative-anchor pre-filter. It writes
`$DAILY_CURATOR_HOME/tmp/candidates-YYYY-MM-DD.json` (also printed to stdout)
where `YYYY-MM-DD` is UTC today.

### Step 3: Score candidates (your judgment)
Read `taste.md`. For each candidate, assign `score` ∈ [0,1] for relevance to the
user's taste, then write the candidates back with a `score` field as
`$DAILY_CURATOR_HOME/tmp/scored.json` (same wrapper shape as the prepare file).

Score by **relative ranking, anchored to taste.md**, not by guessing an absolute
number in a vacuum (an unanchored score collapses to a constant):

1. Pick 2–3 anchored exemplars from `taste.md` first — a clear primary-axis +
   positive-anchor item ≈ 0.9, a borderline tertiary item ≈ 0.5, a negative-anchor
   item ≈ 0.1 — and score everything relative to those.
2. Rank the candidates against each other; don't bunch them at one value.
3. Collapse to ≈0 anything matching a semantic negative anchor (funding, launch
   hype, policy/geopolitics without an engineering artifact, thin roundups).
See [references/scoring-and-filtering.md](./references/scoring-and-filtering.md).

### Step 4: Select (deterministic)
```bash
python3 "$SKILL_DIR/scripts/curate.py" select \
    --scored "$DAILY_CURATOR_HOME/tmp/scored.json" \
    > "$DAILY_CURATOR_HOME/tmp/selected.json"
```
Applies the floor (default **0.4** — the [SILENT] gate), ranks by score then
recency, enforces a **same-source cap of 2** (all `hnrss.org/*` share one
bucket), and takes the top `count`. Prints selected JSON to **stdout only** —
the redirect above is required; the script does not write a file. Items below
the floor or beyond the cap are simply not selected — they are NOT recorded, so
they re-compete next run.

### Step 5: Write the digest (only if there is content)
If `selected` is non-empty, write the digest as clean human Markdown, starting at
an H1, **no YAML frontmatter and no hidden score comments**. Path:
`$DAILY_CURATOR_HOME/digests/YYYY-MM-DD.md` on a normal run (UTC today), but
**`$DAILY_CURATOR_HOME/tmp/digest-YYYY-MM-DD.md` when `dry_run`** — so a shadow
run never creates the real file the Step 1 guard keys on. One item per pick:
```
**1. [Title](https://canonical-url)**
Source: <Source> · <Nd ago>
<one concrete line naming the article's actual artifact/claim/method>
```

### Step 6: Persist + verify (deterministic)
Let `<digest>` be the path written in Step 5. On a normal run:
```bash
python3 "$SKILL_DIR/scripts/curate.py" mark-seen \
    --selected "$DAILY_CURATOR_HOME/tmp/selected.json" \
    --home "$DAILY_CURATOR_HOME"
python3 "$SKILL_DIR/scripts/verify-run.py" \
    --selected "$DAILY_CURATOR_HOME/tmp/selected.json" \
    --digest "$DAILY_CURATOR_HOME/digests/YYYY-MM-DD.md" \
    --seen "$DAILY_CURATOR_HOME/seen.txt" \
    --snapshot "$DAILY_CURATOR_HOME/tmp/seen-snapshot.json"
python3 "$SKILL_DIR/scripts/health.py" check --home "$DAILY_CURATOR_HOME"
```
If `verify-run.py` exits non-zero, do NOT deliver — report the failure instead.

In `dry_run`: skip `mark-seen`. Write the digest only to
`$DAILY_CURATOR_HOME/tmp/digest-YYYY-MM-DD.md`. Then:

```bash
python3 "$SKILL_DIR/scripts/verify-run.py" --dry-run \
    --selected "$DAILY_CURATOR_HOME/tmp/selected.json" \
    --digest "$DAILY_CURATOR_HOME/tmp/digest-YYYY-MM-DD.md" \
    --seen "$DAILY_CURATOR_HOME/seen.txt" \
    --snapshot "$DAILY_CURATOR_HOME/tmp/seen-snapshot.json"
python3 "$SKILL_DIR/scripts/health.py" check --dry-run --home "$DAILY_CURATOR_HOME"
```

`--dry-run` treats selected URLs as would-be seen, so a content run passes
without writing `seen.txt` or `shown.jsonl`. Digest + re-show checks still
run. `health.py check --dry-run` prints an alert if due but does not stamp
`feed-health.json`. No real state is written. Log the brief that *would*
push; do not deliver.

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
python3 "$SKILL_DIR/scripts/curate.py" roundup --days 7 --home "$DAILY_CURATOR_HOME"
```
`roundup` reads `$DAILY_CURATOR_HOME/shown.jsonl` and prints the week's shown
items ranked best-first (by score) to stdout. Pick the 3–5 strongest — no new
scoring — and write a short "本周精选" brief in the weekly format (see
[references/output-format.md](./references/output-format.md)). Write it to
`$DAILY_CURATOR_HOME/digests/YYYY-MM-DD-weekly.md` (UTC today; a distinct name
so it never collides with the daily file or the daily idempotency guard). If the
week produced nothing, send a one-line "本周无新增。" rather than `[SILENT]`.

Note: this heartbeat only holds once the Sunday `mode=weekly` cron entry is
installed; nothing else triggers the weekly run.

## Feed health
`curate.py prepare` records each feed's fetch outcome to `feed-health.json`.
`python3 "$SKILL_DIR/scripts/health.py" check` flags any feed that has returned no parseable entry for
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
- [scripts/curate.py](./scripts/curate.py) — bootstrap / prepare / select / mark-seen / roundup
- [scripts/health.py](./scripts/health.py) — feed-health tracking + stale-feed alert
- [scripts/verify-run.py](./scripts/verify-run.py) — pre-delivery invariant check
- [scripts/canon.py](./scripts/canon.py) — shared URL canonicalization + seen.txt ledger
- [scripts/tests/](./scripts/tests/) — `python3 -m unittest` suite
- [scripts/import-opml.sh](./scripts/import-opml.sh) — OPML → URL extractor
- [references/curated-feeds.md](./references/curated-feeds.md) — built-in source list & tiers
- [references/scoring-and-filtering.md](./references/scoring-and-filtering.md) — scoring guidance
- [references/taste-template.md](./references/taste-template.md) — starter `taste.md`
