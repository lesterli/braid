"""homework-coach verifier — the pinned, deterministic math truth oracle.

The engine (a Socratic tutoring Skill) NEVER computes math itself. It calls
this module via the host's code-execution tool to get ground truth, then
withholds the answer and reverse-questions the student. Keeping the math here
(not in the model) is what turns "the AI got the math wrong" into a checkable
invariant.

Pure functions only. No I/O, no state, no natural language — the model
formalizes the student's fuzzy input into expression strings before calling.
"""

import functools

from sympy import Eq, simplify, solve as _sympy_solve
from sympy.parsing.sympy_parser import parse_expr


class Unsupported(Exception):
    """The verifier cannot ground this input.

    Parse failure, an unsolvable equation, or any kind that does not reduce to
    a symbolic value/solution-set (geometry, proofs, free-form). The engine
    catches this and drops to degraded mode (withhold-answer stays, the
    correctness guarantee is waived and disclosed). The boundary is CAPABILITY,
    not curriculum topic — fractions and quadratics are in; nothing here is a
    hardcoded topic list.
    """


def _grounded(fn):
    """Guarantee a public verifier call never leaks a raw sympy/Python error.

    Any internal failure becomes Unsupported so the engine has one typed signal
    to route on.
    """

    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except Unsupported:
            raise
        except Exception as exc:  # noqa: BLE001 — intentional: one typed exit
            raise Unsupported(str(exc)) from exc

    return wrapper


def _parse_equation(equation: str):
    """Parse "lhs = rhs" into a sympy Eq and the variable to solve for."""
    lhs, rhs = equation.split("=")
    eq = Eq(parse_expr(lhs), parse_expr(rhs))
    symbol = sorted(eq.free_symbols, key=str)[0]
    return eq, symbol


def _solution_set(equation: str) -> set:
    """Solve a single-variable equation string into its set of solutions.

    "2*x = 6" -> {3}
    """
    eq, symbol = _parse_equation(equation)
    return set(_sympy_solve(eq, symbol))


@_grounded
def equivalent(a: str, b: str) -> bool:
    """True iff a and b describe the same solution set.

    The single primitive the engine uses to judge a student's step: is the
    new line still equivalent to the previous one? Catches both algebra and
    arithmetic errors, because a wrong step changes the solution set (for
    equations) or the value (for plain expressions).
    """
    if "=" in a or "=" in b:
        return _solution_set(a) == _solution_set(b)
    return simplify(parse_expr(a) - parse_expr(b)) == 0


@_grounded
def solve(problem: str) -> str:
    """Return the answer the engine keeps hidden.

    Single solution -> "3"; multiple -> comma-joined in a stable order.
    """
    eq, symbol = _parse_equation(problem)
    solutions = _sympy_solve(eq, symbol)
    return ", ".join(str(s) for s in sorted(solutions, key=str))


@_grounded
def is_solved(equation: str) -> bool:
    """True iff the equation is in solved form: variable = number.

    "x = 3" -> True; "2*x = 6" -> False. Lets the engine recognize the
    student has arrived and stop reverse-questioning.
    """
    lhs, rhs = (parse_expr(side) for side in equation.split("="))
    return (lhs.is_symbol and not rhs.free_symbols) or (
        rhs.is_symbol and not lhs.free_symbols
    )
