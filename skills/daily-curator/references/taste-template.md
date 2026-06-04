# Daily Curator — User Taste Profile (Template)

> This is a starter template. Copy to `~/.daily-curator/taste.md` on first run
> and **edit every section** to reflect your actual interests. The agent reads
> the live `~/.daily-curator/taste.md`, not this template.

This file is read by `/daily-curator` during Step 3 (Score & Filter) to compute
`relevance_to_user_taste` (0–1). It is the user-supplied "what good looks like"
signal that pure source-tier scoring cannot capture.

## Primary axis
*(REPLACE: describe the topics that count as "must read" for you. Be specific —
"new papers", "open-source tools", "engineering practice" beats "tech".)*

例：新论文、开源工具、工程实践。

## Secondary axis
*(REPLACE: topics you welcome when primary is thin. Narrower is better.)*

例：工具教程、case study。

## Tertiary axis (selective)
*(REPLACE: bullets of specific sub-topics. Delete this section if you have no
tertiary interests.)*

例：
- 大厂官方动作（Anthropic / OpenAI / Google DeepMind 等）

## Positive anchors — content I actively want more of
*(REPLACE with 5–10 specific accounts / blogs / handles. These are LLM-readable
taste anchors — concrete beats abstract.)*

- @example1 — why
- @example2 — why
- ...

## Negative anchors — never recommend
*(REPLACE with 3–7 concrete patterns. These short-circuit relevance to 0.)*

1. e.g. 反复炒冷饭的融资八卦
2. e.g. 标题党无信息量
3. e.g. 没有原始来源的二手解读
4. ...

## Scoring guide (for /daily-curator)

| Range | Meaning |
|---|---|
| 0.9 – 1.0 | matches primary axis + content from a positive anchor |
| 0.7 – 0.89 | matches primary OR secondary, no anchor overlap |
| 0.5 – 0.69 | matches tertiary axis, or peripheral but interesting |
| 0.3 – 0.49 | borderline; topic-adjacent but soft fit — usually drop |
| 0.0 – 0.29 | misfit; especially if any negative anchor pattern is present |

**Hard rule**: items scoring below 0.3 on `relevance_to_user_taste` MUST be
dropped regardless of other dimensions. Negative-anchor matches collapse the
score to 0 immediately.

## Suggested-track guidance

| Track | When to tag |
|---|---|
| `gongzhonghao` | Has depth, can be expanded into 800-1500 字 长文 |
| `xiaohongshu` | Has a clear hook + 3-5 个 takeaway points 可以浓缩成 300-500 字 |
| `deep-read` | Worth reading personally before commenting |
| `skip` | Cleared scoring bar but doesn't fit any output channel |

Items can carry multiple tags.
