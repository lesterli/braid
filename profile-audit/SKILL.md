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

## Scope Contract

This skill is opinionated about who it serves. It is not a generic profile reviewer.

**✅ Designed for**: 服务型 OPC — anyone whose profile's job is to convert a passing visitor into a paying client (independent designer / consultant / coach / freelancer / indie advisor).

**⚠️ Partial fit, run with awareness**: SaaS / Indie Hacker / build-in-public engineer. The funnel logic still applies, but the "行动钩子" (CTA) dimension means "click product link" or "follow for launch updates" rather than "send DM". On Twitter especially, this is the more common archetype.

**❌ Not designed for**:
- Pure content creator / 流量变现 profile (goal is `follow`, not contact)
- Hobby / 兴趣分享 / personal vlog (no conversion funnel exists)
- Anonymous accounts / 化名 KOL (`身份确认` dimension is structurally inapplicable)
- Brand / 企业官号 (different model — needs a separate `brand-audit` skill)

If the user's profile falls in ❌, say so plainly and refuse to score. Forcing this scorecard onto a misfit profile produces misleading advice. Telling the user "this skill isn't right for you" is the correct outcome.

## Inputs

- One or more **screenshots** of the user's profile page (主页). Multiple screenshots are fine if scrolling is needed to see all pinned posts or recent items.
- Optional: the profile URL — used only as a label in the report. Not fetched.

The skill does not call any external API. All analysis runs on what's visible in the screenshot.

## Workflow

### Step 1: Identify Platform & Verify Scope

This step is mandatory. It must complete before any scoring.

**1a. Platform identification.** Look at the screenshot(s) and identify the platform from these visual signatures:

| Platform | Visual Signatures |
|----------|------------------|
| `xiaohongshu` | 红色品牌色 / 小红书 logo, "笔记 · 收藏 · 赞" 标签栏, 方形封面网格, IP 属地标签 |
| `twitter` | 黑/白 minimal UI, "Posts / Replies / Media / Likes" tabs, 蓝色 verified 勾, 时间线竖排 |

If the platform is not obvious, ask the user explicitly: `我看到的像是 [best guess]，可以确认一下吗？`

**1b. Scope verification.** Ask the user one question:

> 这个主页的目标是哪种？
> A) 让访客联系我并付费（服务型 OPC）— 全维度适用
> B) 让访客试用我的产品 / 关注产品发布（SaaS / build-in-public）— 注意 行动钩子 含义不同
> C) 让访客关注我看更多内容（创作者 / 流量变现）— 此 skill 不适合
> D) Hobby / 个人日记 / 不商业化 — 此 skill 不适合
> E) 匿名账号 / 化名 KOL / 企业官号 — 此 skill 不适合

If the answer is **C / D / E**, refuse to audit and explain plainly:

> 这个 skill 是给"想靠主页拿到付费客户"的服务型 OPC 设计的。你的主页类型不在 scope 内，硬跑这个 scorecard 会给你误导性建议。如果你在做 [类型]，建议自建一份匹配那个漏斗终点的 scorecard。

If the answer is **A**, proceed with full scorecard.
If **B**, proceed but flag that 维度 4（行动钩子）的子检查需要按"产品试用/follow"语义解释（具体见 [scorecards/twitter.md](./references/scorecards/twitter.md) "Twitter archetype 调整"段）。

**1c. Load scorecard.**

- `xiaohongshu` → [references/scorecards/xiaohongshu.md](./references/scorecards/xiaohongshu.md)
- `twitter` → [references/scorecards/twitter.md](./references/scorecards/twitter.md)

Never proceed to scoring without an identified platform AND a scope-verified profile type. Record both in the final report so the routing decision is auditable.

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
