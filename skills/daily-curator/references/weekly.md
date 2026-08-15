# Weekly roundup

Load this file when `mode=weekly` or the user says "本周精选" / "weekly
roundup". Then read [output-format.md](./output-format.md) for the weekly
template.

The Sunday run is the heartbeat: it always delivers, so a full week of
silence means something is broken.

```bash
python3 "$SKILL_DIR/scripts/curate.py" roundup --days 7 --home "$DAILY_CURATOR_HOME"
```

`roundup` reads `$DAILY_CURATOR_HOME/shown.jsonl` — **not** `digests/*.md`.
Items are ranked best-first by the persisted `score`. Pick the 3–5 strongest
(no new scoring). Write:

`$DAILY_CURATOR_HOME/digests/YYYY-MM-DD-weekly.md`

UTC today. The `-weekly` suffix must not collide with the daily digest or
the daily idempotency guard.

If the week produced nothing, send exactly `本周无新增。` — not `[SILENT]`.

Do not call `mark-seen` again; these items are already in both ledgers.
