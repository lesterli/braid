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

The boundary is **operator-side, not naming-side**. Personal IP and brand are not opposites — your name *is* your brand. An account named "OwlLink AI" run by 1 person is in scope (个人 IP using a brand-style name); an account run by a corporate marketing team is not. The real distinction is who's behind the keyboard.

**✅ Designed for**: 1 人 / 小核心团队驱动的 IP，无论命名是真名还是品牌名

- **Archetype A — 服务型 OPC**：designer / consultant / coach / freelancer / indie advisor. 漏斗 = 路过 → 私信 → 付费.
- **Archetype B — SaaS / Indie Hacker / build-in-public**：indie product / 工具开发者. 漏斗 = 路过 → 试用 → 订阅.
- **Archetype B-community — Community 品牌 / podcast / newsletter**：1 人 / 小团队运营的社区品牌（如 OwlLink AI、Lightcone、Latent Space 这类形态）. 漏斗 = 路过 → 持续关注 → 加入社区/参加活动.
- **Archetype C — Researcher / writer / thinker**：newsletter / 课程 / 书 变现.

**❌ Not designed for**:
- **组织化运营的企业账号**（公司市场部 / 多人轮班 / 公司销售漏斗）— 不同模型，需独立的 `brand-audit` skill
- 纯流量变现创作者 / 网红（目标是 `follow` + 广告/带货收入，不是转化为服务/产品）
- Hobby / 兴趣分享 / personal vlog（没有 conversion funnel）

判断准则不是"叫什么名字"，而是"**谁在按键、为什么按键**"。

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
> A) 让访客联系我并付费（服务型 OPC：设计师 / 咨询 / 教练 / 自由开发者）
> B) 让访客试用产品 / 关注发布 / 加入社区（SaaS / build-in-public / community 品牌 / podcast / newsletter）
> C) Researcher / writer / thinker（newsletter / 课程 / 书 变现）
> D) 纯流量变现 创作者 / 网红 — 此 skill 不适合
> E) Hobby / 个人日记 / 不商业化 — 此 skill 不适合
> F) 组织化运营的企业账号（公司市场部 / 多人轮班）— 此 skill 不适合

If the answer is **D / E / F**, refuse to audit and explain plainly:

> 这个 skill 是给"1 人 / 小团队驱动 IP 的 OPC"设计的，目标是 conversion（联系/试用/订阅/加入社区）。你的主页类型不在 scope 内，硬跑这个 scorecard 会给你误导性建议。

If the answer is **A**, proceed with full scorecard. Apply 维度 4 子检查的服务型语义（联系方式 / 私信路径）.
If **B**, proceed but apply 维度 4 子检查的 archetype-B 语义。具体语义对照表见 [scorecards/twitter.md](./references/scorecards/twitter.md) 和 [scorecards/xiaohongshu.md](./references/scorecards/xiaohongshu.md) 的 "Archetype 调整" 段。**特别注意**：community 品牌的 4.x 是"跨平台持续连接渠道 / 常驻型社区入口"，**不是某次具体活动的报名 link**——具体活动 CTA 属于那条笔记/推文的范畴，不是主页层面。
If **C**, proceed with 维度 4 = "newsletter / 写作平台订阅引导"。

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

1. Each sub-check answers `yes` / `no` / `N/A`. Cite the visible evidence inline (e.g., `bio 是 emoji 流水账，没有价值主张`).
2. Dimension band derives from sub-check pass rate (see scorecard for thresholds).

**N/A 边界规则（must-follow）**：

- 如果某个子检查无法从截图判断（e.g., 截图被裁剪、内容被设置为"仅自己可见"、需要滚动查看的内容缺失），标 `N/A` 并说出需要什么补充截图。**绝不猜测**。
- **如果一个维度的 N/A 子检查 ≥ 50%**：整个维度标 `⚠️ 不可评估`，不参与加权（从分母中扣除该维度权重），并在报告头部 flag。否则 N/A 子检查仅从该维度的分母中扣除。
- 真实例外场景：公开内容样本量过低（例如最近笔记 < 3 条且很多都是 private）会让维度 2（持续性信号）几乎全部子检查变 N/A。这种情况下不要给"假高通过率"，按上述规则把维度 2 整个标 ⚠️。

Aggregate into an overall score using the scorecard's weighting. ⚠️ 不可评估的维度从分子和分母同时移除。

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
