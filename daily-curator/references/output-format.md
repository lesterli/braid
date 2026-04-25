# Output Format

## Standard Daily Format

```markdown
# 今日推荐 | YYYY-MM-DD

> 主题关键词：Keyword A / Keyword B / ...

---

**1. [Article Title](url)**
Source: Author or Blog Name · Time ago
一句话策展人点评：为什么这篇值得读。

**2. [Article Title](url)**
Source: Author or Blog Name · Time ago
一句话策展人点评。

...

---
_从 N 个信源中精选 M 篇 · 质量优先，宁缺毋滥_
```

## Weekly Mode

- Heading: `本周推荐 | MM-DD ~ MM-DD`
- Count increases to 10–15
- Structure otherwise identical

## Category Filter Mode

- Heading adds category tag: `今日推荐 · AI | YYYY-MM-DD`
- Only show items from the filtered category

## Empty Day

When nothing clears the quality bar:

```markdown
# 今日推荐 | YYYY-MM-DD

今天没有特别值得推荐的内容。信源更新较少，已有内容多为简短动态，未达到推荐标准。

明天见。
```

## Example Output

```markdown
# 今日推荐 | 2026-03-14

> 主题关键词：AI Agents / CSS Debugging / Mental Models

---

**1. [Building Reliable AI Agents with Tool Use](https://simonwillison.net/2026/Mar/14/reliable-agents/)**
Source: Simon Willison · 3h ago
把 Agent 可靠性问题拆解成具体的工程实践，附完整代码，非常实用。

**2. [How I debug CSS](https://jvns.ca/blog/2026/03/13/debug-css/)**
Source: Julia Evans · Yesterday
用她一贯清晰的方式把 CSS 调试变成可重复的方法论，适合前后端都看看。

**3. [The Leverage of Mental Models](https://fs.blog/mental-models-leverage/)**
Source: Farnam Street · Yesterday
讲心智模型如何在决策中产生杠杆效应，案例扎实。

**4. [Latent Space Podcast: The State of Open Models](https://www.latent.space/p/open-models-2026)**
Source: Latent Space · 2h ago
对开源模型生态的深度分析，数据翔实。另见: Interconnects 本周也有相关讨论。

**5. [Measuring Developer Productivity](https://newsletter.pragmaticengineer.com/p/measuring-productivity)**
Source: The Pragmatic Engineer · Today
用 DORA 框架之外的视角重新审视工程效率度量。

---
_从 18 个信源中精选 5 篇 · 质量优先，宁缺毋滥_
```
