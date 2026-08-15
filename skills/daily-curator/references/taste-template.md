# Daily Curator — User Taste Profile (Template)

> This is a starter template. First-run `curate.py bootstrap` copies it to
> `$DAILY_CURATOR_HOME/taste.md`. **Edit every section** to reflect your actual
> interests. The agent reads the live `taste.md`, not this template.

This file is LLM-read during scoring. For each candidate the agent assigns a
single numeric `score` ∈ [0, 1] — that is the field `curate.py select` reads.
`select` does not parse this file and does not read track tags.

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

## Scoring guide

Assign one `score` per candidate. Ranges match
[scoring-and-filtering.md](./scoring-and-filtering.md):

| Range | Meaning |
|---|---|
| 0.9 – 1.0 | matches primary axis + content from a positive anchor, or a first-hand artifact |
| 0.7 – 0.89 | matches primary OR strong secondary, concrete implementation detail |
| 0.5 – 0.69 | tertiary axis, or peripheral but interesting |
| 0.3 – 0.49 | adjacent, soft fit — usually below the floor |
| 0.0 – 0.29 | misfit; especially if any negative anchor pattern is present |

**Hard rule**: `select` drops anything with `score` **< 0.4** (the [SILENT]
gate). Negative-anchor matches collapse the score to 0 immediately. Do not
attach track tags (`gongzhonghao`, `xiaohongshu`, `deep-read`, `skip`) — they
are not scored or selected on.
