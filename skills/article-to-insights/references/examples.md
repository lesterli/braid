# Examples

Use these only as calibration. Do not copy them mechanically.

## Example 1: Technical Article, Deep Mode

User request:

```text
Read this article and focus on what it means for AI coding workflows.
URL: https://example.com/ai-coding-framework
Mode: deep
Audience: intermediate
```

Response shape:

- `核心摘要`: three-sentence summary of the article's thesis, then `2-4` core claims about AI coding as a workflow framework.
- `这对你的意义`: connect the article to team process design, review loops, and task decomposition.
- `建议`: start with `值得读`, then suggest one team experiment and one validation question. Add who should read it and who can skip it.
- `关键概念与依据`: explain the framework metaphor, the operational assumptions behind it, and whether the article relies on examples, practitioner experience, or data.

## Example 2: Opinion Post, Quick Mode

User request:

```text
Analyze this article URL and tell me what matters.
URL: https://example.com/remote-work-opinion
Mode: quick
Audience: beginner
```

Response shape:

- `核心摘要`: `1-3` short bullets on the article's main claim and supporting angle. End with evidence-quality note.
- `这对你的意义`: note the practical implication for someone deciding whether the argument matters to their own work.
- `建议`: `可跳过` if the piece adds limited new insight, then suggest what kind of reader would still benefit.

## Example 3: Thin or Failed Page, Degraded Output

User request:

```text
Extract insights from this article.
URL: https://example.com/gated-landing-page
Mode: quick
```

Response shape:

- `核心摘要`: say the available page content is too limited to recover the full article argument.
- `这对你的意义`: keep inference minimal and explicitly conditional.
- `建议`: `可跳过` with low-confidence note and tell the user to paste the text, provide an archive link, or use another accessible source.

## Example 4: Mini Output Sample

User request:

```text
Read this article and tell me whether it is worth my time.
URL: https://example.com/ai-coding-framework
Mode: quick
Audience: intermediate
```

Mini output:

```text
核心摘要
- 这篇文章的核心观点是：AI 编程更像一种高层抽象框架，而不只是更快的代码生成器。
- 作者认为，AI 提升了生成速度，但也会带来抽象泄漏、控制权下降和认知债务累积。
- 文章进一步主张，更成熟的用法是把 AI 当作"库"来调用，而不是把整个工程主导权交给它。
（依据：主要基于实践经验和工程观察，非数据验证）

这对你的意义
如果你的团队在用 AI 编程工具，这篇文章提醒你：
• 别一味追求"更短的提示词"，关注程序整体结构
• 作为"总设计师"审查 AI 写的代码，不要放任 AI 主导一切
• 找到提示词的"甜蜜区"，付出"相对较少"而非"最少"的认知成本

建议：值得读
• 在下次 AI 编程时，刻意控制一个模块的提示词粒度，观察输出质量变化
• 在代码审查时单独检查 AI 生成代码的边界条件和隐含假设
```
