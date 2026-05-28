# Scoring, Filtering, and Queue Lifecycle

Two-dimensional scoring + an append-only queue + read-history. The agent **MUST
compute and display each dimension's score** for transparency — auditable
selection, self-correcting via taste.md edits.

## Formula

```
total = relevance_to_user_taste × source_quality
```

Range: 0.0 to 1.2 (max: 1.0 × 1.2). Why these two, and not the old `t × q × (1+d)
× r`: source-quality already encodes "this author writes deep content reliably",
so a separate `d` was double-counting. And the seen-cache (now queued+read)
already answers "have I seen this yet?", so multiplying by timeliness was
double-counting that too. The new pipeline keeps timeliness as a filter and
tiebreaker, not a dimension.

## Pipeline

```
fetch → Stage 1 cheap pre-filter → drop in-queue + in-read → score new
                                                                    │
                                                                    ▼
queue → re-score r → taste_gc (r<0.3) → spillover candidates ───► merge
                                                                    │
                                                                    ▼
                                                       same-source cap=2
                                                                    │
                                                                    ▼
                                                       Top N (default 5)
                                                                    │
                                                                    ▼
                                            persist: queued.txt + digest.md
```

## Hard drops

An item is dropped **immediately, no exceptions**, if any of:

1. `published > 14 days ago` (window — fresh-enough constraint, see "Freshness")
2. Title matches a Stage 1 literal negative-anchor (cheap)
3. URL already in `queued.txt` (it'll appear via spillover, not as new)
4. URL already in `read.txt` (don't resurface)

URLs in (3) and (4) are compared in **canonical form** (`#fragment` stripped).
RSS feeds emit inconsistent variants of the same article URL; without
canonicalization, dedup leaks. See SKILL.md Step 4 for details.

5. `relevance_to_user_taste < 0.3` (off-topic for this user)
6. `total < 0.4` (overall quality bar)

## Stage 1 — Cheap pre-filter (no LLM tokens)

Right after parsing feed entries, scan every candidate's **title** against
literal patterns extracted from `~/.daily-curator/taste.md`'s "Negative
anchors" section. Drop hits unconditionally.

```bash
# Default literal set — keep in sync with taste.md negative anchors.
# Case-insensitive; matched against title only.
patterns='融资|IPO|估值|震惊|取代|要失业|10\s*个\s*prompt|10 Prompts?|股价|裁员|涨停|跌停'
grep -iEv "$patterns" candidates.tsv > survivors.tsv
```

Tuning rule: only put patterns here that are **safe to drop without context**.
"融资" is safe. "AI" is not (too broad). When in doubt, leave it for the
semantic stage.

## Stage 2 — Semantic scoring

Apply `q × r` to survivors. Two dimensions:

### Relevance to User Taste (0–1)

Read `~/.daily-curator/taste.md`. The file declares:
- Primary / Secondary / Tertiary topic axes
- Positive anchors (voices/sources the user wants more of)
- Negative anchors (patterns to never recommend)

Rubric:

| Range | Meaning |
|---|---|
| 0.9 – 1.0 | matches primary axis + positive-anchor content |
| 0.7 – 0.89 | matches primary OR secondary, no anchor overlap |
| 0.5 – 0.69 | matches tertiary axis, or peripheral but interesting |
| 0.3 – 0.49 | borderline; topic-adjacent but soft fit — usually drop |
| 0.0 – 0.29 | misfit; especially if any negative-anchor pattern present |

**Negative-anchor short-circuit**: items that slipped past Stage 1 but still
match a semantic negative anchor → set `relevance = 0.0`.

### Source Quality (multiplier)

| Tier | Multiplier | Criteria |
|------|------------|----------|
| Tier 1 | 1.2× | Listed in curated-feeds.md AI/Engineering — author reliably produces depth content |
| Tier 2 | 1.0× | Listed in curated-feeds.md Open Source & Industry |
| User-added | 0.9× | In feeds.txt but not in curated-feeds.md — unknown track record |

Source quality is the **only** depth proxy. RSS summary length is too noisy
(minimaxir gives 8 chars, Simon Willison gives full content; both write deep
posts) to support a separate depth adjustment.

## Freshness — filter + tiebreaker

Freshness is **not** a scoring dimension. It is two things:

- **Hard filter**: items published > 14 days ago are dropped. Anything still
  "fresh to you" beyond that window belongs in your own bookmark system.
- **Tiebreaker**: when two items share the same `total` (within ±0.01),
  prefer the newer one.

Rationale: the user's taste profile leans heavily toward essays and analyses
that don't decay. The queue+read state already answers "have I seen this?".

## Queue re-scoring (Step 6 in SKILL.md)

For each item in `queued.txt`, **on every run**:

1. Re-compute `r` using today's `taste.md`. (`q` is stored in the queue entry
   and never re-computed — it only changes if curated-feeds.md changes, which
   is rare and explicit.)
2. If `r < 0.3`: silently move the item to `read.txt` with
   `reason: taste_gc`. The agent reports the count to the user but doesn't
   list each item.
3. Otherwise, the item is eligible for spillover with today's
   `total = q × r_new`.

This makes the queue **live** — when the user edits taste.md, the queue
self-prunes within one run.

## Same-source cap (Step 7)

After merging new candidates + spillover candidates and sorting by total:

- **Cap = 2 per source per digest.**
- HN feeds are aggregated: all `hnrss.org/*` URLs share one source bucket.
  Other sources are their own bucket (one feed = one bucket).
- When the cap is hit, the surplus item is **deferred to the queue**:
  - If it was a new candidate: insert into `queued.txt` with
    `reason: source_cap_deferred` so it can spillover tomorrow.
  - If it was already in the queue (spillover candidate): leave it; it'll
    re-appear tomorrow when the cap might not bind.

The cap applies to the **final digest** (new + spillover combined), not to
each section individually.

## Empty Day

If, after all filters and cap, fewer items remain than `count`, just produce
a shorter digest. **Never pad**.

If zero items qualify:

```markdown
# 今日推荐 · 待读队列 | YYYY-MM-DD

今日无新增；queue 中也无可推内容（全部 <0.3 或已被 cap 限制）。
明天见。
```

The empty digest is still written to disk so downstream skills get a clear
signal.

## State files

```
~/.daily-curator/
├── queued.txt   JSONL — items shown in some past digest but not read
├── read.txt     JSONL — items processed out of queue
└── digests/YYYY-MM-DD.md
```

### `queued.txt` entry format

```json
{
  "url": "https://example.com/post",
  "queued_since": "2026-05-28",
  "title": "...",
  "source": "Hillel Wayne",
  "source_quality": 1.2,
  "tracks": ["gongzhonghao", "deep-read"],
  "summary_snippet": "First 300-500 chars of the RSS summary, used for queue re-scoring."
}
```

`summary_snippet` is stored so r-rescoring doesn't require re-fetching the
original URL — the source might have rolled off the RSS feed by then.

### `read.txt` entry format

Same as queued.txt plus two fields:

```json
{
  "...all queued.txt fields...",
  "read_at": "2026-05-28",
  "reason": "explicit | ttl_gc | taste_gc | source_cap_deferred | legacy_migration"
}
```

`reason` values:

| Reason | Trigger |
|---|---|
| `explicit` | User ran `bash scripts/mark-read.sh URL...` or said "已读 ..." |
| `ttl_gc` | `queued_since` is older than `queue_ttl_days` (default 21) |
| `taste_gc` | Re-scored `r < 0.3` after the user edited taste.md |
| `legacy_migration` | One-shot import from v1 `seen.txt` |

(Note: `source_cap_deferred` is a queue insertion reason, not a read reason. It
appears in `queued.txt` entries, not in `read.txt`.)

## Output: explicit scores per item

Every item in the digest MUST carry a one-line `_scores:` annotation. See
[output-format.md](./output-format.md) for the exact rendering. Spillover
items also carry `queued_since: YYYY-MM-DD`.

Examples:

```
_scores: q=1.2 r=0.92 → 1.10 · tracks: [gongzhonghao, deep-read]
_scores: q=1.2 r=0.85 → 1.02 · queued_since: 2026-05-25 · tracks: [deep-read]
```
