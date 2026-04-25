# Twitter / X 主页 评分卡

## 适用范围

边界是 **operator-side**（1 人 / 小团队 vs 组织化运营），不是 naming-side。完整定义见 SKILL.md 的 Scope Contract。Twitter 上的 archetype 比小红书多样：

✅ **A · 服务型 OPC**：独立顾问 / freelancer / 教练 / 设计师。
✅ **B · SaaS / Indie Hacker / build-in-public**：**Twitter 上的主流 OPC 类型**。
✅ **B-community · Podcast / newsletter / community 品牌**（Lightcone / Latent Space 形态）。
✅ **C · Researcher / writer / thinker**：影响力变现（newsletter / 课程 / 书）。

❌ **不适用**：组织化运营企业账号 · 纯流量变现网红 · Hobby

---

## 设计前提

和小红书评分卡共享同一个底层模型：访客是从一条推文 / 转推 / reply 进入主页的，**已经被某条内容 pre-qualified 过**。主页要做的是确认 + 兑现，不是说服。

骨架与 [xiaohongshu.md](./xiaohongshu.md) 完全一致——同样 5 维度、同样权重、同样二元子检查、同样 band 制。**这本身就证明了 Harness 的复用性：换平台只换 scorecard 的内容，不动结构。**

不同点：Twitter 上一些信号比小红书更突出（pinned tweet、reply 节奏、verified 状态），一些信号在 Twitter 上意义不同（封面 banner 的作用 ≠ 小红书的笔记封面）。

---

## 评分原则

同 [xiaohongshu.md](./xiaohongshu.md)：每个子检查只回答 yes / no / N/A。维度 band 由通过率决定。

---

## 维度

### 维度 1: 身份确认（权重 ×2）

**问题**：访客 5 秒内能不能确认 "这是 [刚才那条推文] 的作者，是个 [明确职业身份] 的人"？

| 子检查 | 通过条件 |
|-------|---------|
| **1.1** Display name + handle 是职业身份标签 | Display name 包含职业关键词或独特定位（"@alice / Indie iOS Dev"），不是纯艺名或匿名（"@xx_dreamer"） |
| **1.2** Bio 第一行回答了"我做什么 / 我是谁" | 价值主张句或角色定位句，不是 quote / "🇺🇸 SF / coffee / typed weights" 兴趣拼贴 |
| **1.3** Profile picture + Banner 整体传递职业感 | pfp 清晰且与定位一致；banner 不是空白默认或纯生活照（banner 是 Twitter 上仅次于 bio 的"价值主张位"） |

---

### 维度 2: 持续性信号（权重 ×2）

**问题**：最近 timeline 能不能传递 "这是个持续在做这件事的人，不是偶然写出一条好推文"？

| 子检查 | 通过条件 |
|-------|---------|
| **2.1** 最近 10 条原创推文主题垂直聚焦 | ≥60% 围绕同一专业领域；reply / quote 不计入分母 |
| **2.2** Reply / 互动节奏正常 | 看 Replies tab — 有近期 reply（不是只发不互动的"广播账号"） |
| **2.3** 最近一条原创推文在 14 天内 | 时间戳在 14 天以内；超过 = "可能不再做这个"信号 |

---

### 维度 3: 可信度扩展（权重 ×1）

**问题**：Bio + Pinned tweet 里，有没有刚才那条推文承载不了的"更多"？

| 子检查 | 通过条件 |
|-------|---------|
| **3.1** Bio 或 Pinned tweet 里有具体数字证据 | follower 数本身不算（被动指标）；服务过 N 个客户 / shipped N 个产品 / 写过 N 篇 / 担任 X 角色等主动证据 |
| **3.2** 有别人重复不了的独特视角 | Pinned tweet 或最近输出里能看出独特方法 / 特殊背景 / 小众细分领域 |

---

### 维度 4: 行动钩子（权重 ×1.5）

**问题**：访客决定采取下一步行动时，能不能在 30 秒内找到路径？

| 子检查 | 通过条件 |
|-------|---------|
| **4.1** 主页有明确的"持续连接"路径 | Bio / pinned tweet 里有让访客继续跟你的渠道。**具体什么算"持续连接"取决于 archetype**——详见 [archetypes.md 的 4.1 表](../archetypes.md#41-持续连接渠道)。Twitter 特别注意：DM-open 状态是一个被忽视但关键的信号 |
| **4.2** 该路径在 2 步以内 | 从主页到下一步行动 ≤ 2 次点击 / 操作。**具体的"下一步"形态取决于 archetype**——详见 [archetypes.md 的 4.2 表](../archetypes.md#42-路径长度) |

**重要边界**：这是主页层面的持续连接。某次产品发布 / 活动报名的具体 link 属于那条 tweet 的 CTA，**不在主页评分范围内**。

---

### 维度 5: 一致性兜底（权重 ×0.5）

**问题**：访客刷到推文 → 点进主页，会不会感觉 "主页和刚才那条像两个人"？

| 子检查 | 通过条件 |
|-------|---------|
| **5.1** Display name + bio + pfp + banner 综合人设与最近内容 tone 一致 | 不出现"内容很专业但主页气质很娱乐"或反之的割裂 |

---

## 总分计算

完全同 [xiaohongshu.md](./xiaohongshu.md)。

```
weighted_sum = Σ (维度通过率 × 权重)
total_weight = 2 + 2 + 1 + 1.5 + 0.5 = 7
percent = weighted_sum / total_weight × 100
```

Band 分级与 xiaohongshu.md 共享。

---

## Twitter 上的 5 个常见 anti-pattern

供 audit 时快速识别：

1. **匿名 + emoji 拼贴 bio**：`🇺🇸 SF / coffee / typed weights / shipping fast` —— 1.2 直接挂掉
2. **空白 banner**：放着不动 = 浪费一个最大价值主张位
3. **永远 quote-tweet 不原创**：2.1 通过率会极低，访客无从判断你的独立观点
4. **DM 关闭 + bio 无 link**：4.1 直接挂掉，所有 inbound 全部死路
5. **Pinned tweet 是 6 个月前的"hello world"**：表达"已弃号"信号
