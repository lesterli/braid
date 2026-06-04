---
name: article-to-insights
description: Use this skill when the user says "read <url>" or "读 <url>", when the user invokes "$article-to-insights <url>", or when the message contains only a single article or blog URL and no other instructions. It should also trigger for requests like "analyze this article", "extract insights from this URL", "summarize this blog post", "is this worth reading", "explain what this article says", or "what are the key takeaways". Use it only for single article or blog post reading, explanation, and recommendation tasks, not generic web research or non-article links such as GitHub repos, docs homepages, product pages, social posts, or video pages.
---

# Article to Insights

Turn one article URL into a structured reading result that helps the user judge whether to read it, understand the core argument, interpret the important concepts, and decide what to do next.

Keep the skill focused on article reading and sense-making. Do not drift into generic web research, full fact-checking, or broad multi-source synthesis unless the user asks for that separately.

## Inputs

- Require `url`.
- Accept `audience_level` as `beginner`, `intermediate`, or `expert` when the desired explanation depth is clear.
- Accept `mode` as `quick` or `deep`. Default to `quick`. Switch to `deep` when the user explicitly requests detailed analysis or asks "why" questions.
- Accept `output_language`. Default to the language the user is writing in. Fall back to Chinese when the language cannot be determined.

## Workflow

1. Run [scripts/validate-url.sh](./scripts/validate-url.sh) to pre-check URL reachability and content type. If the verdict is `unreachable` or `non_article`, switch to degraded output. If the verdict is `thin_page`, attempt to fetch the page but expect degraded output.
2. Fetch and read the article body from the URL with the available browsing or retrieval tools.
3. Judge whether the main body is complete enough to support a normal answer. If access fails, the page is thin, or the content is obviously incomplete, switch to degraded output and read [references/quality-guardrails.md](./references/quality-guardrails.md).
4. Extract the source-grounded content first:
   - main thesis
   - core supporting points
   - key concepts, metaphors, or frameworks that need explanation
   - evidence basis, assumptions, and visible limitations
5. Separate source-grounded claims from model inference. Never blur that boundary.
6. Draft the final response following the Output Skeleton below. Use three sections in `quick` mode and four in `deep` mode.
7. Tailor the explanation and recommendations to the user's `audience_level` and `mode`.
8. Run a final guardrail check against [references/quality-guardrails.md](./references/quality-guardrails.md) before you answer.

## Working Rules

- Prioritize helping the user answer: What is this article saying, is it worth my time, what matters for my context, and what should I do next.
- Keep the output structure stable. Vary density, not architecture.
- Explain specialized terms at the user's level instead of repeating jargon.
- Rely on section structure to separate source from interpretation. Do not add inline disclaimers.
- Prefer concise, high-signal output over long paraphrase.
- Keep the task scoped to article processing. Do not invent missing evidence.

## Output Skeleton

### quick mode (three sections)

1. `核心摘要` / `Core Summary`
   - Say what the article is fundamentally arguing or explaining. Keep it compact.
   - End with a one-sentence evidence-quality note, e.g. `（依据：主要基于个人经验，无数据支撑）`.
2. `这对你的意义` / `What This Means for You`
   - Stay grounded in the source instead of free-associating.
   - Do not add disclaimers like "以下是推断" — the section title already signals interpretation.
3. `建议` / `Recommendation`
   - Start with `值得读` or `可跳过` (or a localized equivalent) as a scan anchor.
   - If `值得读`: follow with concrete action items. Do not restate why it is worth reading.
   - If `可跳过`: follow with a one-sentence reason. No next steps needed.

Use `1-3` short bullets or short paragraphs per section. Optimize for fast reading decisions.

### deep mode (four sections)

1. `核心摘要` / `Core Summary`
   - Prefer a three-sentence summary plus `2-4` core points.
2. `这对你的意义` / `What This Means for You`
   - Same rules as quick mode but expand implications, tradeoffs, and practical meaning.
3. `建议` / `Recommendation`
   - Same verdict rules as quick mode.
   - If `值得读`: add who should read it and who can skip it.
4. `关键概念与依据` / `Key Concepts and Basis`
   - Explain the key terms, metaphors, or frameworks.
   - State the visible basis: examples, anecdotes, data, experience, or reasoning.
   - Distinguish facts, author interpretation, assumptions, and weak support.
   - This section is only included in `deep` mode.

## References

- Read [references/output-format.md](./references/output-format.md) only when you need formatting detail, heading localization guidance, or degraded-output reminders.
- Read [references/quality-guardrails.md](./references/quality-guardrails.md) whenever access is incomplete, evidence is weak, or you need to distinguish source claims from model inference.
- Read [references/examples.md](./references/examples.md) only when you need style calibration or a degraded-output example.

## Scope Boundaries

- Do not present this as a full fact-checking system.
- Do not claim universal coverage of arbitrary web pages; be explicit when the article body is unavailable or low quality.
- Do not turn a single-URL reading task into a research report unless the user asks for comparison or validation across sources.
