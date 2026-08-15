# Scoring & Filtering

One relevance score per item, a cheap pre-filter before any LLM work, and a low
floor that doubles as the silence gate.

## Pipeline

```
fetch ─▶ canonicalize ─▶ cheap filters (NO LLM) ─▶ LLM relevance 0–1 ─▶ floor ─▶ rank ─▶ cap ─▶ top-N
                              │                                            │
                  freshness + dedup + neg-anchor                    [SILENT] if empty
```

The cheap filters and the floor/rank/cap/top-N are done by
`$SKILL_DIR/scripts/curate.py` (`prepare` and `select`). Only the 0–1 relevance
score in the middle is yours.

## Cheap filters (curate.py prepare — no tokens)

Applied in order; survivors become the candidate set:

1. **Freshness**: drop items published > 14 days ago. No-date items are kept.
2. **Dedup**: drop URLs already in `seen.txt` (compared in canonical form —
   `#fragment` stripped, trailing slash normalized; see `canon.py`).
3. **Negative-anchor pre-filter**: drop titles matching literal patterns
   (`融资|IPO|估值|裁员|…`). Keep here ONLY patterns safe to drop without context.
   Override the built-in list with `~/.daily-curator/negative-anchors.txt`
   (one regex per line) if needed.

## Relevance score (your judgment, 0–1)

Read `taste.md` (primary / secondary / tertiary axes, positive anchors,
negative anchors — no track tags). Score each candidate for relevance to the
user's taste by **relative ranking anchored to examples**, not an absolute
guess (an unanchored absolute score collapses to a constant). Write a numeric
`score` field; that is the only taste signal `select` reads:

1. Anchor first. Pick 2–3 reference points from `taste.md`:
   primary-axis + positive-anchor ≈ **0.9**, borderline tertiary ≈ **0.5**,
   negative-anchor ≈ **0.1**. Score everything relative to those.
2. Rank candidates against each other; do not bunch them at one value.
3. **Negative-anchor short-circuit**: anything mainly about funding/valuation,
   launch hype with no implementation detail, leaderboard drama, prompt-list
   content, or policy/geopolitics without a concrete engineering artifact →
   collapse to ≈ 0, even from a high-quality source.
4. **Thin-roundup caution**: newsletter roundups and `[AINews]`-style items
   often mention "agent/model/benchmark" while being thin summaries. Score them
   low unless the title/summary exposes a concrete eval, API/tooling change, or
   implementation note.

| Range | Meaning |
|---|---|
| 0.9–1.0 | primary axis + positive anchor, or a first-hand artifact |
| 0.7–0.89 | primary or strong secondary, concrete implementation detail |
| 0.5–0.69 | interesting but indirect; useful background |
| 0.3–0.49 | adjacent, soft fit; usually below the floor |
| 0.0–0.29 | misfit, hype, thin summary, or negative-anchor match |

## Floor, rank, cap (curate.py select)

- **Floor (default 0.4)** — drop everything below it. If nothing clears the
  floor, the result is empty → the run is `[SILENT]`. The floor is the one tuning
  knob; calibrate it from the dry-run score distribution rather than guessing.
- **Rank** — score descending, tie-broken by newer `published`. Source quality is
  reflected in the LLM relevance score (via taste.md's positive anchors), **not**
  as a separate mechanical multiplier or tiebreaker — the only deterministic
  tiebreaker is recency.
- **Same-source cap = 2** per source bucket. All `hnrss.org/*` share one
  "hackernews" bucket so HN can't dominate; every other feed is its own bucket.
- **Top-N** — take `count` (default 5, cap 7).

## Freshness is a filter + tiebreaker, not a dimension

The user's taste leans toward essays that don't decay, and `seen.txt` already
answers "have I shown this?". So freshness only (a) hard-filters items older than
14 days and (b) breaks score ties. It does not bias ranking toward recency, so
slow monthly/quarterly sources are not disadvantaged once they publish.

## Overflow & state

- Items below the floor or beyond the cap are **not** recorded in `seen.txt` or
  `shown.jsonl`, so they re-compete next run while still inside the 14-day
  window. This rollover is best-effort: an item that rolls off its RSS feed
  before being shown is gone (fine — this is a brief, not a never-miss archive).
- Only **shown** items are appended to both ledgers. `seen.txt` is the dedup
  key (pruned to 30 days each run). `shown.jsonl` stores the structured row
  **including `score`**, which `roundup` uses to rank the weekly brief.
- Scores **are** persisted on `shown.jsonl` for weekly ranking. They do not
  appear in the human digest (no hidden `_scores` comments).

## Feed health

`prepare` writes `$DAILY_CURATOR_HOME/feed-health.json`. A working feed always
returns its backlog, so "returned ≥1 parseable entry" is a health signal
independent of publish cadence: a monthly blog stays ok every day; only a
feed that 404s, errors, or returns nothing trends stale. (hnrss query feeds
can legitimately be empty on a quiet week, so the threshold is 14 days.)

`python3 "$SKILL_DIR/scripts/health.py" check` flags feeds with no parseable
entry for >14 days and prints an out-of-band alert (deliver even on a silent
day). Alerts are rate-limited to once a week per feed (`last_alert`).
`--dry-run` prints the alert but does not stamp `last_alert`.
