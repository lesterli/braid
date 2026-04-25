# Scoring and Filtering

Lightweight scoring system for ranking RSS/Atom entries. All scores are conceptual guides for the agent — no numeric computation is required, but the relative weighting should be respected.

## Timeliness Score (0–1)

| Published | Score |
|-----------|-------|
| Today | 1.0 |
| Yesterday | 0.85 |
| 2 days ago | 0.7 |
| 3+ days ago | 0.5 |
| No date available | 0.6 |

In weekly mode, extend the window: anything within the past 7 days scores 0.7+.

## Source Quality (multiplier)

| Tier | Multiplier | Criteria |
|------|------------|----------|
| Tier 1 | 1.2× | Listed in curated-feeds.md AI/Engineering/Thinking categories (e.g., Simon Willison, Julia Evans, Paul Graham) |
| Tier 2 | 1.0× | Listed in curated-feeds.md Open Source & Industry category (e.g., Hacker News Best) |
| User-added | 0.9× | In `feeds.txt` but not in curated-feeds.md — unknown track record, slight discount |

## Content Depth Signal

| Signal | Adjustment |
|--------|------------|
| Long-form (>2000 chars in description) | +0.1 |
| Contains code examples or technical detail | +0.1 |
| Short news blurb (<200 chars) | −0.1 |

## Deduplication

- **Same canonical URL** → keep first seen
- **Same title** (fuzzy, >80% overlap) → keep higher-scored
- **Same topic, different sources** → keep the best, add `另见: SourceB` note

## Quality Bar

- Items scoring below 0.5 (after all adjustments) should be dropped.
- If all candidate items fall below 0.5, output: `今天没有特别值得推荐的内容` with a brief explanation of why (e.g., "信源今日更新较少且多为简短动态").
- Never pad the list with low-quality items just to fill the count.
