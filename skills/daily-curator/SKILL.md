---
name: daily-curator
description: >-
  Curate a short daily reading brief: fetch new RSS items, dedup against what
  you've already been shown, score the survivors against your taste profile, and
  deliver only the genuinely fresh picks — staying silent on days with nothing
  worth your time. Persists two ledgers: seen.txt (dedup) and shown.jsonl
  (shown items plus scores, for the weekly roundup).
  Use when the user says "今日推荐", "今天读什么", "daily reads", "morning briefing",
  "推荐文章", "每日推荐", "本周精选", "weekly roundup", or invokes "$daily-curator".
  Also use for feed management: "关注" / "取消关注" / "我的信源" / "list feeds" /
  "导入 OPML" / "调整口味" / "edit taste".
  Does NOT set up a feed reader or rewrite content for publication.
---

# Daily Curator

A short reading brief. Scripts own fetch, dedup, select, persist, and verify.
You own the 0–1 `score` and the one-line "why it matters". Never pad: a short
brief or `[SILENT]` is honest.

## Critical gotchas

- **Run from `$SKILL_DIR`** — the directory that contains this `SKILL.md`.
  Every command uses `"$SKILL_DIR/scripts/..."`. Never a bare `scripts/...`
  from another cwd.
- **Never deliver before verification.** If `verify-run.py` exits non-zero,
  report the failure. Do not send the digest.
- **A content dry run must not mutate real state.** Skip `mark-seen`. Write
  the digest only under `tmp/`. Call `verify-run.py --dry-run` and
  `health.py check --dry-run`. Do not write `seen.txt`, `shown.jsonl`,
  `digests/YYYY-MM-DD.md`, or stamp `feed-health.json`.
- **Weekly reads `shown.jsonl`**, not `digests/*.md`. Scores persist on
  `shown.jsonl` for ranking. The digest stays human-only (no hidden `_scores`).

`$SKILL_DIR` = this skill directory. `$DAILY_CURATOR_HOME` = state dir
(default `~/.daily-curator`). Dates in filenames are **UTC today**
(`YYYY-MM-DD`, `canon.today_utc()`).

## Daily checklist

bootstrap → idempotency → prepare → score → select → render → persist → verify → deliver

### 1. Bootstrap

```bash
python3 "$SKILL_DIR/scripts/curate.py" bootstrap --home "$DAILY_CURATOR_HOME"
```

Only setup path. Idempotent. Seeds `feeds.txt` and `taste.md` if missing;
creates empty `seen.txt`, `shown.jsonl`, `feed-health.json`. Tell the user
to edit `taste.md`.

### 2. Idempotency

If `$DAILY_CURATOR_HOME/digests/YYYY-MM-DD.md` exists and `force_regen` is
false → reply `[SILENT]` and stop.

### 3. Prepare

```bash
python3 "$SKILL_DIR/scripts/curate.py" prepare --home "$DAILY_CURATOR_HOME"
```

Writes `$DAILY_CURATOR_HOME/tmp/candidates-YYYY-MM-DD.json` (UTC today).

### 4. Score

Read `$DAILY_CURATOR_HOME/taste.md`. Assign `score` ∈ [0, 1] by relative
ranking anchored to that file (primary+positive ≈ 0.9, tertiary ≈ 0.5,
negative ≈ 0.1; collapse semantic negatives to ≈ 0). Write
`$DAILY_CURATOR_HOME/tmp/scored.json` (same wrapper as the prepare file).
Before scoring, read [references/scoring-and-filtering.md](./references/scoring-and-filtering.md).

### 5. Select

```bash
python3 "$SKILL_DIR/scripts/curate.py" select \
    --scored "$DAILY_CURATOR_HOME/tmp/scored.json" \
    > "$DAILY_CURATOR_HOME/tmp/selected.json"
```

Stdout only — the redirect is required. Floor **0.4** is the `[SILENT]`
gate. Empty `selected` → skip render/persist; still run health, then deliver.

### 6. Render

Content day only. No YAML frontmatter, no hidden score comments.

- Live: `$DAILY_CURATOR_HOME/digests/YYYY-MM-DD.md`
- `dry_run`: `$DAILY_CURATOR_HOME/tmp/digest-YYYY-MM-DD.md`

```markdown
# 今日推荐 | YYYY-MM-DD

**1. [Title](https://canonical-url)**
Source: <Source> · <Nd ago>
One concrete line naming the article's actual artifact, claim, method, or tension.
```

Canonical URL. No `一句话点评：`. If the RSS summary is thin, say what is
known. File and reply are identical from the H1 down.

### 7. Persist

Live only:

```bash
python3 "$SKILL_DIR/scripts/curate.py" mark-seen \
    --selected "$DAILY_CURATOR_HOME/tmp/selected.json" \
    --home "$DAILY_CURATOR_HOME"
```

Writes `seen.txt` (dedup) and `shown.jsonl` (shown items + score). Skip on
`dry_run` and on a silent day.

### 8. Verify

Live:

```bash
python3 "$SKILL_DIR/scripts/verify-run.py" \
    --selected "$DAILY_CURATOR_HOME/tmp/selected.json" \
    --digest "$DAILY_CURATOR_HOME/digests/YYYY-MM-DD.md" \
    --seen "$DAILY_CURATOR_HOME/seen.txt" \
    --snapshot "$DAILY_CURATOR_HOME/tmp/seen-snapshot.json"
python3 "$SKILL_DIR/scripts/health.py" check --home "$DAILY_CURATOR_HOME"
```

`dry_run`:

```bash
python3 "$SKILL_DIR/scripts/verify-run.py" --dry-run \
    --selected "$DAILY_CURATOR_HOME/tmp/selected.json" \
    --digest "$DAILY_CURATOR_HOME/tmp/digest-YYYY-MM-DD.md" \
    --seen "$DAILY_CURATOR_HOME/seen.txt" \
    --snapshot "$DAILY_CURATOR_HOME/tmp/seen-snapshot.json"
python3 "$SKILL_DIR/scripts/health.py" check --dry-run --home "$DAILY_CURATOR_HOME"
```

### 9. Deliver

Never call send_message; cron delivers the reply. `dry_run`: log what would
have been sent, deliver nothing.

- Content day → digest from the H1; append a health-alert trailer if any.
- Silent day + health alert → the alert text, not `[SILENT]`.
- Silent day, no alert → exactly `[SILENT]`.

## Load when

Do not preload references. There is no migration document.

- **Before scoring** → [references/scoring-and-filtering.md](./references/scoring-and-filtering.md)
- **Missing or first-run `taste.md`** → [references/taste-template.md](./references/taste-template.md)
- **User is managing feeds or taste** (关注 / 取消关注 / 我的信源 / list feeds / 导入 OPML / 调整口味 / edit taste) → [references/feed-management.md](./references/feed-management.md)
- **`mode=weekly` or 本周精选 / weekly roundup** → [references/weekly.md](./references/weekly.md), then [references/output-format.md](./references/output-format.md) for the weekly template only
- **Feed-health rationale** (why backlog ≠ stale) → scoring-and-filtering.md, Feed health section

The daily digest template, commands, and deliver rules above are complete.
Do not open `output-format.md` on a daily run.
