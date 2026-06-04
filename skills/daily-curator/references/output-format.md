# Output Format

The `/daily-curator` skill produces **two parallel outputs**:

1. **Chat output** — what the user sees in the conversation
2. **Digest file** — written to `~/.daily-curator/digests/YYYY-MM-DD.md`,
   the structured contract that downstream skills (e.g. `/daily-publisher`)
   parse to produce 公众号 / 小红书 drafts

The visible content should be the same. The digest file may include hidden
HTML comments for machine-readable metadata. Those comments are not part of the
default user-facing reading experience.

## File path & naming

`~/.daily-curator/digests/YYYY-MM-DD.md`. If a file for today already exists
(the user re-ran the skill), **overwrite it**. The new run reflects the
latest taste / feeds / queue state.

## Standard format

```markdown
---
date: YYYY-MM-DD
sources_fetched_today: <N>
new_count: <X>
queue_filler_count: <Y>
queue_size: <Z>
queue_ttl_days: 21
theme_keywords: [keyword A, keyword B, keyword C]
---

# 今日推荐 · 待读队列 | YYYY-MM-DD

> 主题关键词：Keyword A / Keyword B / Keyword C

---

## 新加入（<X> 条）

**1. [Article Title](https://...)**
Source: Author or Blog Name · 3h ago
Why this specific article is worth opening, without a boilerplate label.
<!-- _scores: q=1.2 r=0.92 → 1.10 · tracks: [gongzhonghao, deep-read]_ -->

**2. [Article Title](https://...)**
Source: Author or Blog Name · Yesterday
What makes this one distinct from the item above.
<!-- _scores: q=1.0 r=0.80 → 0.80 · tracks: [xiaohongshu]_ -->

## 从 queue 中精选（<Y> 条）

**3. [Article Title](https://...)**
Source: Author or Blog Name · 5d ago
Why it remains worth attention after sitting in the queue.
<!-- _scores: q=1.2 r=0.85 → 1.02 · queued_since: 2026-05-23 · tracks: [deep-read]_ -->

---
_今日 <X> 新增 · <Y> queue 精选 · queue 中共 <Z> 篇待读_

还有 <R> 篇在待读队列；说 `更多` / `显示全部` 查看。
```

## Frontmatter contract (machine-readable)

The YAML frontmatter is the **stable contract** for downstream consumers:

| Field | Type | Description |
|---|---|---|
| `date` | string | ISO date of digest run |
| `sources_fetched_today` | int | Feeds reached on this run |
| `new_count` | int | Items in the "新加入" section |
| `queue_filler_count` | int | Items in the "从 queue 中精选" section |
| `queue_size` | int | Total entries in queued.txt after this run |
| `queue_ttl_days` | int | TTL used for queue GC this run |
| `theme_keywords` | string[] | Top 3–5 themes spanning the digest |

Downstream parsers MAY read the frontmatter directly. Do not change field
names without updating this contract.

## Section ordering

Always two sections in this order: **新加入** then **从 queue 中精选**.

- If `new_count == 0`: the "新加入" heading still appears, with empty body
  ("今日无新增"), so the structure is parseable by downstream tools.
- If `queue_filler_count == 0`: the "从 queue 中精选" section can be omitted
  entirely (queue is exhausted today).
- Total items in both sections combined ≤ `count` (default 5).
- When `queue_size` is larger than the number of displayed items, show an
  explicit next action at the bottom: `还有 N 篇在待读队列；说 更多 / 显示全部 查看。`
- When the user asks "更多", "显示剩余", "显示全部", or a range like "第 6-9 条",
  render the remaining queued items with the same item format and clickable
  title links.

## Per-item annotation contract

Each item carries one hidden annotation line in the digest file:

```
<!-- _scores: q=<source_quality> r=<relevance> → <total> · [queued_since: <YYYY-MM-DD> · ]tracks: [<tag>, <tag>...]_ -->
```

- `q` = source quality multiplier (0.9 / 1.0 / 1.2)
- `r` = relevance to user taste (0–1)
- `total` = `q × r`, display to 2 decimal places
- `queued_since` = **only present for spillover items**, the date this item
  first entered queued.txt
- `tracks` = subset of `[gongzhonghao, xiaohongshu, deep-read, skip]`

Regex for downstream parsing:

```
<!-- _scores: q=([\d.]+) r=([\d.]+) → ([\d.]+)( · queued_since: (\d{4}-\d{2}-\d{2}))? · tracks: \[([^\]]*)\]_ -->
```

Do not show score metadata visibly by default. If the user asks to audit
ranking, add a compact `评分明细` section after the digest instead of showing
scores under every item.

## Item Writing Rules

- The title line is the primary action and MUST be a Markdown link:
  `**1. [Title](https://...)**`.
- Never output a bare title when the URL is available.
- Do not use boilerplate prefixes like `一句话策展人点评：` or `一句话点评：`.
- The recommendation line should name the article's specific object, claim,
  method, artifact, or tension.
- Avoid repeating generic lines across multiple items. If the feed summary is
  too thin, state the concrete visible signal, such as the author/source/title
  evidence, rather than inventing substance.

## Track tagging rules

Read `~/.daily-curator/taste.md` for the user's track guidance. Default rules:

| Track | Tag when item is... |
|---|---|
| `gongzhonghao` | Has depth — can be expanded into 800–1500 字 长文 |
| `xiaohongshu` | Has a clear hook + 3–5 takeaways — compressible to 300–500 字 |
| `deep-read` | High-density essay/paper/experiment that deserves the user's own commentary before any republishing |
| `skip` | Cleared the score bar but doesn't fit any output channel — kept for awareness only |

Items MAY carry multiple tags. `deep-read` is non-exclusive.

## Empty Day

When the merged candidate pool produces zero items (rare — usually queue
spillover saves the day):

```markdown
---
date: YYYY-MM-DD
sources_fetched_today: <N>
new_count: 0
queue_filler_count: 0
queue_size: <Z>
queue_ttl_days: 21
theme_keywords: []
---

# 今日推荐 · 待读队列 | YYYY-MM-DD

今日无新增；queue 中也无可推内容（全部 <0.3 或已被 cap 限制）。
明天见。
```

The empty digest is still written to disk.

## Example Output

```markdown
---
date: 2026-05-28
sources_fetched_today: 22
new_count: 2
queue_filler_count: 3
queue_size: 14
queue_ttl_days: 21
theme_keywords: [LLM 架构, 训练方法论, AI agents 基础设施]
---

# 今日推荐 · 待读队列 | 2026-05-28

> 主题关键词：LLM 架构 / 训练方法论 / Agent 基础设施

---

## 新加入（2 条）

**1. [Hy3 LLM topping OpenRouter](https://minimaxir.com/2026/05/openrouter-hy3/)**
Source: Max Woolf · Today
Max 标志性的"先观察排行榜异常 → 上 evals 验证"流程。
<!-- _scores: q=1.2 r=0.90 → 1.08 · tracks: [xiaohongshu, deep-read]_ -->

**2. [Clanker: A Word For The Machine](https://lucumr.pocoo.org/2026/5/26/clankers/)**
Source: Armin Ronacher · Today
工程师视角的命名学切片：怎么称呼"它"决定怎么使用"它"。
<!-- _scores: q=1.2 r=0.70 → 0.84 · tracks: [gongzhonghao]_ -->

## 从 queue 中精选（3 条）

**3. [Assumptions weaken properties](https://buttondown.com/hillelwayne/archive/assumptions-weaken-properties/)**
Source: Hillel Wayne · 8d ago
STRONG ⇒ WEAK 形式化拆解，从命题逻辑反推测试设计。
<!-- _scores: q=1.2 r=0.90 → 1.08 · queued_since: 2026-05-22 · tracks: [gongzhonghao, deep-read]_ -->

**4. [Notes on pretraining parallelisms](https://www.dwarkesh.com/p/notes-on-pretraining-parallelisms)**
Source: Dwarkesh Patel · 12d ago
和 frontier lab 工程师私聊后的内部观察。
<!-- _scores: q=1.2 r=0.90 → 1.08 · queued_since: 2026-05-20 · tracks: [gongzhonghao, deep-read]_ -->

**5. [Giving Agents Computers](https://www.latent.space/p/daytona)**
Source: Latent.Space · 7d ago
Daytona CEO 访谈：bare-metal sandbox 给 Agent 用。
<!-- _scores: q=1.2 r=0.85 → 1.02 · queued_since: 2026-05-21 · tracks: [gongzhonghao, deep-read]_ -->

---
_今日 2 新增 · 3 queue 精选 · queue 中共 14 篇待读_

还有 9 篇在待读队列；说 `更多` / `显示全部` 查看。
```
