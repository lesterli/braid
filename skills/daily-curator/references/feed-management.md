# Feed management

Load this file when the user is managing subscriptions or taste — not on a
normal daily run.

Triggers (do **not** start the daily pipeline):

| User says | Action |
|---|---|
| 关注 `https://example.com/feed.xml` | Append the URL to `$DAILY_CURATOR_HOME/feeds.txt` if it is not already present |
| 取消关注 `example.com` | Remove matching lines from `feeds.txt` |
| 我的信源 / list feeds | Show `feeds.txt` |
| 导入 OPML … | `bash "$SKILL_DIR/scripts/import-opml.sh" <file-or-url>` and append unique URLs |
| 调整口味 / edit taste | Show `$DAILY_CURATOR_HOME/taste.md` and apply the requested edits |

`feeds.txt` is one URL per line (`#` comments allowed). `taste.md` is the
LLM-read profile; bootstrap copies it from
[taste-template.md](./taste-template.md) if missing.

If `feeds.txt` is missing, run `curate.py bootstrap` — that is the only setup
path. Then append.

## False positives

These do **not** activate feed management:

- "今日推荐" / "今天读什么" / "daily reads" / "本周精选"
- An article URL inside a digest or candidate list
- "关注" used as ordinary Chinese ("值得关注的论文") without a feed URL

Do not create `feeds.txt` by hand. Do not run `prepare` just to add a feed.
