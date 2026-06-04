# Quality Guardrails

Use this file whenever source quality is uncertain or you are at risk of overstating what the article supports.

## Source vs Inference

- Keep source-grounded claims and model inference separate through section structure: `核心摘要` is source-grounded, `这对你的意义` is interpretation.
- Do not write model interpretation as if it were the author's conclusion.
- Do not add explicit disclaimers like "以下是推断". The section titles already signal the boundary.
- If the user asks for quotes or exact wording, use only short excerpts that you can verify from the source.

## Access and Completeness Checks

Before writing a normal answer, check:

- Did you access the article body, not just the homepage or preview card?
- Does the page contain enough text to identify a thesis and supporting points?
- Is the page mainly article content rather than navigation, ads, signup prompts, or product marketing?
- Does the visible content look truncated, paywalled, or partially loaded?

If any answer is "no", lower confidence and switch to degraded output.

## Degraded Output Rules

Switch to degraded output when:

- the URL cannot be accessed
- the page body cannot be extracted
- the page is mostly navigation, ads, or promotion
- the visible content is too short to support real analysis
- the article looks incomplete or truncated

In degraded output:

- state what you could verify
- state what is missing and why that limits confidence
- avoid pretending to know the full argument
- suggest the next best input, such as pasting the article text or using an alternate source

## Confidence Ratings

Use a short confidence marker when helpful:

- `高` / `High`: the body is clear, substantial, and internally coherent
- `中` / `Medium`: the body is readable but some context or support is missing
- `低` / `Low`: access is partial, content is thin, or inference dominates

Lower confidence when:

- the article relies mostly on anecdote without much support
- the visible text omits context that seems important
- your interpretation depends heavily on unstated assumptions

## Final Checks

Before answering, verify:

- The verdict matches the evidence quality.
- The summary does not invent claims, examples, or data.
- The explanation reflects the user's requested level.
- The recommendations are specific rather than generic advice.
- Uncertainty is visible wherever the evidence is weak.
