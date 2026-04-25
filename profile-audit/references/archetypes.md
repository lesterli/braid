# Archetypes

profile-audit 在 4 个 archetype 上运行。SKILL.md 的 Step 1b 询问用户主页属于哪种 archetype；scorecard 的维度 4（行动钩子）子检查含义因 archetype 而变。

**这个文件是 archetype 路由的 single source of truth**——所有跨平台、跨 scorecard 共享的 archetype 语义都集中在这里。新增 archetype 只改这一个文件。

---

## Archetype 列表

| Code | Name | 漏斗终点 | 主要平台 |
|------|------|---------|---------|
| **A** | 服务型 OPC（设计师 / 咨询 / 教练 / 自由开发者 / 独立顾问） | 路过 → 私信 → 付费 | 小红书 / Twitter / LinkedIn |
| **B** | SaaS / Indie Hacker / build-in-public 工程师 | 路过 → 试用 → 订阅 | Twitter > 小红书 |
| **B-community** | Community 品牌 / podcast / newsletter / 社区主理人 | 路过 → 持续关注 → 加入社区 / 参加活动 | Twitter / 小红书 |
| **C** | Researcher / writer / thinker | 路过 → 订阅 → 课程/书变现 | Twitter / Substack |

❌ 不在 scope 内（不在表中列出）：组织化运营企业账号 · 纯流量变现网红 · Hobby / 不商业化主页。详见 SKILL.md 的 Scope Contract。

---

## 维度 4 子检查的 archetype-specific 解释

scorecard 里的 4.1 / 4.2 用 archetype-agnostic 描述（"持续连接路径" / "路径长度 ≤ 2 步"）。具体什么算"持续连接"和"下一步"取决于 archetype。

### 4.1 持续连接渠道

**通用问题**：访客看完主页后，能不能在主页之外继续跟你？

⚠️ 这是**主页层面**的持续连接——某次具体活动 / 产品发布的报名 link 属于那条具体内容的 CTA，**不在主页评分范围内**。这是设计上明确的边界。

| Archetype | 4.1 通过条件 |
|-----------|------------|
| **A** | Bio / 置顶里有联系方式：私信触发词 / 微信号 / 邮箱 / 个人 portfolio link |
| **B** | Bio / 置顶里有产品链接：try-it-now / 落地页 / app store link / GitHub repo |
| **B-community** | Bio / 置顶里有跨平台持续连接渠道：公众号 / 微信群 / Discord / newsletter / 同名其他平台 |
| **C** | Bio / 置顶里有 newsletter 订阅 / 写作平台 link / 课程主页 |

### 4.2 路径长度

**通用问题**：访客决定行动后，到达下一步要走几步？

| Archetype | 4.2 通过条件（≤ 2 步） |
|-----------|---------------------|
| **A** | 直接 DM / 邮箱 = 1 步；点 bio link → 联系页 = 2 步 |
| **B** | 点产品 link → 落地页 = 1-2 步 |
| **B-community** | 关注公众号 / 加群 / 订阅 newsletter ≤ 2 步 |
| **C** | 订阅 newsletter / 跳到写作平台 ≤ 2 步 |

---

## 平台 × Archetype 常见组合

| 平台 | A 服务型 | B SaaS | B-community | C Writer |
|------|---------|--------|-------------|----------|
| 小红书 | ✅ 主流 | ⚠️ 较少（生态弱） | ✅ 上升中 | ⚠️ 较少 |
| Twitter | ✅ 常见 | ✅ 主流（indie hacker 大本营） | ✅ 主流（podcast / community） | ✅ 主流（writer Twitter） |

---

## 添加新 archetype 的步骤

将来如果增加新 archetype（如 "Open Source Maintainer" / "Educator" / "Investor"）：

1. 在 "Archetype 列表" 加一行
2. 在 4.1 / 4.2 表里加对应解释
3. 在 SKILL.md Step 1b 的选项里加一项

**不需要修改任何 scorecard 文件**。这就是 single source of truth 的价值——scope 增长是 O(1) 改动，不是 O(N×平台数)。
