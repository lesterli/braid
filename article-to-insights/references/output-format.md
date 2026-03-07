# Output Format

## Heading Rules

- Localize headings to the requested `output_language`.
- Default to the language the user is writing in. Fall back to Chinese headings when the language cannot be determined.
- Keep the section order fixed per mode.
- If helpful, add a one-line metadata preface with the URL, mode, and confidence rating.

## quick mode (three sections)

1. `核心摘要` / `Core Summary`
2. `这对你的意义` / `What This Means for You`
3. `建议` / `Recommendation`

## deep mode (four sections)

1. `核心摘要` / `Core Summary`
2. `这对你的意义` / `What This Means for You`
3. `建议` / `Recommendation`
4. `关键概念与依据` / `Key Concepts and Basis`

## Section Requirements

### 1. Core Summary

- Answer what the article is fundamentally arguing or explaining.
- Keep it high signal; avoid throat-clearing.
- In `quick` mode, keep compact and end with a one-sentence evidence-quality note.
- In `deep` mode, prefer a three-sentence summary plus `2-4` core points.

### 2. What This Means for You

- Focus on implications, tradeoffs, or practical meaning for the user rather than repeating the article.
- Stay grounded in the source; infer only one step beyond the evidence unless the user asks for speculation.
- Do not add disclaimers like "以下是推断". The section title already signals interpretation.

### 3. Recommendation

- Start with `值得读` or `可跳过` (or a localized equivalent) as a scan anchor.
- If `值得读`: follow with concrete action items. Do not restate why it is worth reading.
- If `可跳过`: follow with a one-sentence reason. No next steps needed.
- In `deep` mode, optionally add who should read it and who can skip it.

### 4. Key Concepts and Basis (deep mode only)

- Explain the terms, metaphors, or frameworks the article depends on.
- State what the article appears to use as evidence: examples, anecdotes, data, experience, or reasoning.
- Distinguish facts, author interpretation, and visible assumptions.
- Flag missing context or weak support when the article does not substantiate a claim well.

## Degraded Output

When the article body is inaccessible, thin, or incomplete:

- Keep the same sections if possible.
- Fill each section only with what is genuinely supported.
- State the limitation early and plainly.
- End with a recommendation to provide the article text or a better source if needed.
