# Scope is by verifier capability, not by topic

A recurring temptation is to write a scope list like "supports: arithmetic,
linear equations; not: fractions, geometry". That list is wrong twice over.

## Two different boundaries — don't conflate them

- **Capability boundary** = what `verifier.py` (sympy) can actually compute and
  compare. This is wide.
- **Curriculum boundary** = what you *choose* to tutor for a given student
  (grade level, figure-free). This is a routing/engine decision.

`Unsupported` fires on the **capability** boundary only. Curriculum gating, if
ever needed, lives in the engine/routing layer — the verifier never encodes it,
so adding grade levels never touches the verifier.

## What's in (by capability — sympy does it for free)

Arithmetic, fractions, decimals, percentages-as-arithmetic, one-variable
equations and inequalities, systems, and yes polynomials / quadratics. None of
these are hardcoded — they're in because the verifier can ground them.

- Fractions: `equivalent("1/2 + 1/3", "5/6")` → True. **Do not exclude fractions.**
- Quadratics: `equivalent("x**2 = 4", "x = 2")` → False (misses −2);
  `equivalent("x**2 = 4", "(x-2)*(x+2) = 0")` → True. In by capability.

The current *milestone* tutors figure-free arithmetic / fractions / one-variable
equations. That the verifier can also ground quadratics is fine — it just means
the guarantee holds if such a problem shows up.

## What's out → degraded (genuinely can't reduce to symbolic equality)

Geometry, constructions, graph-drawing, proofs / "show that", word-problem
*modeling* (the setup step — the verifier can check the resulting equation, not
whether she modeled the right one), interpretation. These can't become a
checkable `solution-set / value` comparison, so the verifier raises
`Unsupported` and the engine drops to degraded mode (withhold-answer stays, the
correctness guarantee is waived and disclosed).

## Growing coverage = add verifiers, not bloat sympy

Reaching proofs or geometry later means adding *different* verifiers (a geometry
engine, a proof checker) behind the same call sites — not making `verifier.py`
bigger. Bloating the sympy wrapper never reaches a proof; it's a category error.
