---
name: profile-audit
description: >-
  Diagnose a personal profile (小红书 / Twitter) from a screenshot and produce
  a structured improvement report with scored dimensions and concrete edits.
  Use when the user says "诊断主页", "主页诊断", "改我的主页", "audit my profile",
  "review my profile", "review my xiaohongshu", "review my twitter",
  or invokes "$profile-audit". Triggered by uploading a screenshot of a
  小红书 or Twitter/X profile page. Does NOT handle post writing,
  content scheduling, or profile creation from scratch.
---

# Profile Audit

A 30-minute diagnostic for personal profiles. Input is a screenshot. Output is a scored audit and an improvement checklist mapped to a platform-specific scorecard.

## Inputs

- One or more **screenshots** of the user's profile page (主页). Multiple screenshots are fine if scrolling is needed to see all pinned posts or recent items.
- Optional: the profile URL — used only as a label in the report. Not fetched.

The skill does not call any external API. All analysis runs on what's visible in the screenshot.

## Workflow

### Step 1: Identify Platform

This step is mandatory. It must complete before any scoring.

Look at the screenshot(s) and identify the platform from these visual signatures:

| Platform | Visual Signatures |
|----------|------------------|
| `xiaohongshu` | 红色品牌色 / 小红书 logo, "笔记 · 收藏 · 赞" 标签栏, 方形封面网格, IP 属地标签 |
| `twitter` | 黑/白 minimal UI, "Posts / Replies / Media / Likes" tabs, 蓝色 verified 勾, 时间线竖排 |

If the platform is not obvious, ask the user explicitly before proceeding:

> 我看到的像是 [best guess]，可以确认一下吗？

Once identified, load the corresponding scorecard:

- `xiaohongshu` → [references/scorecards/xiaohongshu.md](./references/scorecards/xiaohongshu.md)
- `twitter` → [references/scorecards/twitter.md](./references/scorecards/twitter.md)

Never proceed to scoring without an identified platform. Record the identified platform in the final report so the routing decision is auditable.

### Step 2: Extract Profile Snapshot

Read the screenshot(s) and produce a structured "before" baseline:

- 昵称 / handle
- 头像 / avatar (describe in 1 line: 风格、配色、是否露脸)
- bio / 个人简介 (verbatim, including emoji and line breaks)
- 关注 / 粉丝 / 获赞与收藏 (or follower / following counts on Twitter)
- 置顶笔记 / pinned posts (titles + 1-line description)
- 最近 6 条笔记 / posts (titles + visible cover style)
- 视觉一致性观察 (cover style consistency, color palette, font choice)

This snapshot is the "before" record. It goes into the final report verbatim.

### Step 3: Apply Scorecard

Read the loaded scorecard. For each dimension:

1. Score 0–10 based on visible evidence in the snapshot.
2. Cite the specific evidence (e.g., `bio 是 emoji 流水账，没有价值主张`).
3. If the dimension cannot be evaluated from the provided screenshot (e.g., requires content the user did not include), mark it `N/A` and say what would be needed. Do not guess.

Aggregate into an overall score using the scorecard's weighting if specified, otherwise a simple average across non-N/A dimensions.

### Step 4: Generate Improvement Report

Read [references/report-template.md](./references/report-template.md) for the output structure. Produce:

1. Identified platform + overall score.
2. The "before" snapshot from Step 2.
3. Per-dimension scores with cited evidence.
4. **Concrete edits** — for each low-scoring dimension, propose specific replacement text. Not "be more clear", but `改成: ___`.
5. Priority list — top 3 changes ranked by expected impact, each with a 1-line rationale.
6. Estimated effort to implement (in minutes).

## Working Rules

- **One platform per audit.** If the user uploads screenshots from two platforms, audit them separately. Don't mix scorecards.
- **Cite visual evidence for every score.** No score without grounding in something visible.
- **Concrete edits only.** Never write "make it more engaging" — write the actual replacement bio, the actual replacement title.
- **N/A is allowed.** If a dimension genuinely doesn't apply to this user, mark it N/A and exclude from the average. Don't pad.
- **Honest about visual quality.** If an avatar is bad or covers are inconsistent, say so plainly. The user is paying for problems found, not flattery.
- **Respect privacy.** Never include other users' profiles, comments, DMs, or any third-party content visible in the screenshot.

## Response Shape

- Header: `Profile Audit · [Platform] · 总分 X/10`
- "Before" snapshot from Step 2.
- Scorecard table: 维度 / 分数 / 证据 / 建议改动.
- Top 3 priorities with rationale.
- Closing: estimated implementation effort in minutes.

## References

- [references/scorecards/xiaohongshu.md](./references/scorecards/xiaohongshu.md) — 小红书 评分卡 (12 维度)
- [references/scorecards/twitter.md](./references/scorecards/twitter.md) — Twitter/X 评分卡 (9 维度)
- [references/report-template.md](./references/report-template.md) — 输出格式与示例
- [references/examples/](./references/examples/) — before/after walkthrough (小红书)
