"""Behavior tests for the homework-coach verifier (the pinned math truth oracle).

Tests verify behavior through the public interface only (equivalent / solve /
is_solved / Unsupported). They must survive any internal sympy refactor.
"""

import pytest

from verifier import Unsupported, equivalent, is_solved, solve


def test_equivalent_catches_wrong_algebra_step():
    # 2x = 6 has solution {3}; x = 2 has solution {2}. A kid who writes
    # "x = 2" took an invalid step. The whole reason the verifier exists is
    # to catch exactly this — so the engine can reverse-question instead of
    # rubber-stamping a wrong move.
    assert equivalent("2*x = 6", "x = 2") is False


def test_equivalent_accepts_valid_step():
    # 2x = 6 and x = 3 share solution {3}. This is the CRITICAL false-positive
    # guard from eng review: a correct step must NOT be flagged, or a kid who
    # did it right gets told she's wrong and trust collapses.
    assert equivalent("2*x = 6", "x = 3") is True


def test_equivalent_on_pure_arithmetic():
    # No variable, no "=". The same primitive must judge arithmetic so the
    # engine can catch a computation slip (Grace writes 27*6 = 160).
    assert equivalent("27*6", "162") is True
    assert equivalent("27*6", "160") is False


def test_fractions_are_in_scope():
    # Fractions are sympy-native — they must NOT be excluded. Locking this so
    # nobody later "scopes them out" by topic label (verifier = capability, not
    # curriculum).
    assert equivalent("1/2 + 1/3", "5/6") is True
    assert equivalent("1/2 + 1/3", "4/6") is False


def test_solve_returns_the_answer():
    # The engine keeps this hidden and reverse-questions toward it; it never
    # shows it to the student. Single linear solution -> "3".
    assert solve("2*x = 6") == "3"


def test_is_solved_recognizes_isolated_variable():
    # The engine uses this to know the student has arrived (variable = number),
    # so it can stop reverse-questioning and award the win.
    assert is_solved("x = 3") is True
    assert is_solved("2*x = 6") is False


def test_nonlinear_is_in_scope_by_capability():
    # Quadratics are NOT excluded by topic — sympy solves them and the
    # solution-set primitive judges them. x^2=4 -> {-2, 2}.
    assert equivalent("x**2 = 4", "x = 2") is False  # misses -2
    assert equivalent("x**2 = 4", "(x-2)*(x+2) = 0") is True


def test_ungroundable_input_raises_typed_unsupported():
    # If something the verifier cannot ground reaches it, it must raise the
    # typed Unsupported (so the engine catches it and drops to degraded mode),
    # never leak a raw sympy/Python error. This is the boundary by CAPABILITY,
    # not by topic — geometry/proofs/garbage all land here.
    with pytest.raises(Unsupported):
        solve("draw a triangle with two angles")
