#!/usr/bin/env bash
# End-to-end engine smoke test on a real LLM host (Codex), no Lark/Hermes needed.
# Proves the host-agnostic core works: the Socratic engine loads, withholds the
# answer, and grounds every step through the pinned verifier.
#
# Prereqs: codex CLI authed; homework-coach installed at ~/.codex/skills/; the
# braid .venv has sympy (the verifier interpreter used below).
#
# Usage:  bash skills/homework-coach/scripts/smoke_codex.sh
set -euo pipefail

REPO="$(cd "$(dirname "$0")/../../.." && pwd)"   # braid repo root
VENV_PY="$REPO/.venv/bin/python"
SCRIPTS="$REPO/skills/homework-coach/scripts"
CALL="cd $SCRIPTS && $VENV_PY -c \"from verifier import solve, equivalent, is_solved, Unsupported; print(...)\""

run() {  # $1 = title, $2 = prompt
  echo "════════ $1 ════════"
  codex exec "$2" -C "$REPO" -s workspace-write -c 'model_reasoning_effort="medium"' < /dev/null
  echo
}

run "GROUNDED PATH (withhold + catch wrong step + recognize arrival)" \
"Load ~/.codex/skills/homework-coach/SKILL.md and follow it EXACTLY. Check math ONLY via the pinned verifier:
  $CALL
Simulate, printing the coach reply after each student message; never reveal the final answer:
  Student 1: 2x = 6
  Student 2: x = 2
  Student 3: x = 3
Then SELF-CHECK: did you ever state the final answer? (no expected) | max questions per reply? (1 expected) | verifier result for equivalent(2x=6,x=2) and equivalent(2x=6,x=3)? | did is_solved confirm at x=3?"

run "DEGRADED PATH (out-of-scope -> Unsupported -> disclose, still no answer)" \
"Load ~/.codex/skills/homework-coach/SKILL.md and follow it EXACTLY. Check math ONLY via the verifier:
  $CALL
Student: 'A triangle has two angles of 40 and 60 degrees. What is the third angle?'
Show the coach reply. Then SELF-CHECK: did the verifier raise Unsupported? | did you enter degraded mode and disclose you can't double-check this kind? | did you give the answer 80? (must be no)"

echo "Smoke complete. Expected: grounded path withholds + grounds; degraded path discloses + withholds."
