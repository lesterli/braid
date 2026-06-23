# Output Format (v3)

The digest is a single clean, human-readable Markdown document — no YAML
frontmatter, no hidden `_scores` comments, no tracks. The v2 machine layer (which
fed an unbuilt `/daily-publisher`) is gone. The file written to disk and the chat
reply are identical, starting at the H1.

## File path & naming

`~/.daily-curator/digests/YYYY-MM-DD.md`. The same-day idempotency guard means a
real re-run does NOT overwrite-and-re-push; it stays `[SILENT]` (use
`force_regen` to deliberately regenerate). In `dry_run`, write under `tmp/`
instead so the guard and `seen.txt` stay untouched.

## Daily digest format

```markdown
# 今日推荐 | YYYY-MM-DD

**1. [Article Title](https://canonical-url)**
Source: Author or Blog Name · 1d ago
One concrete line naming the article's actual artifact, claim, method, or tension.

**2. [Article Title](https://canonical-url)**
Source: Author or Blog Name · 3d ago
What makes this one worth opening — specific, not a generic category.
```

That is the whole file. Items are ranked best-first (see scoring-and-filtering.md).

## Item writing rules

- The title line is the primary action and MUST be a Markdown link:
  `**N. [Title](https://...)**`. Never a bare title when a URL exists.
- Use the **canonical** URL (fragment stripped) so a click matches what dedup
  recorded.
- No boilerplate lead-ins (`一句话点评：`, `一句话策展人点评：`). The line after
  `Source:` is the recommendation itself.
- Each line must name the article's specific object/claim/method/artifact. If the
  RSS summary is too thin to support that, state the concrete known signal rather
  than inventing substance. Do not repeat a generic line across items.
- Keep it grounded in the fetched content, never hallucinated.

## Silent day

If nothing clears the floor, do **not** write a digest file and do **not** pad.
Respond with exactly `[SILENT]` so the cron suppresses delivery.

## Weekly roundup (mode=weekly, Sundays)

The Sunday run always delivers (it is the heartbeat). Read the last 7 days of
`digests/*.md`, pick the 3–5 strongest items, and write:

```markdown
# 本周精选 | YYYY-MM-DD

> 本周 N 篇值得回看

**1. [Title](https://...)**
Source: ... · <which day this week>
One line on why it mattered this week.
```

If the week produced nothing, send a one-line `本周无新增。` instead of `[SILENT]`,
so the channel still shows a heartbeat.
