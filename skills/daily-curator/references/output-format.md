# Output Format

Load this file when rendering **weekly** output (see [weekly.md](./weekly.md)).
The daily digest template lives inline in `SKILL.md` — do not come here for a
normal daily run.

## Weekly roundup (mode=weekly, Sundays)

The Sunday run always delivers (it is the heartbeat). `curate.py roundup`
reads `shown.jsonl` (not daily digest files), ranks by the persisted score,
and you pick the 3–5 strongest items and write:

```markdown
# 本周精选 | YYYY-MM-DD

> 本周 N 篇值得回看

**1. [Title](https://...)**
Source: ... · <which day this week>
One line on why it mattered this week.
```

If the week produced nothing, send a one-line `本周无新增。` instead of `[SILENT]`,
so the channel still shows a heartbeat.
