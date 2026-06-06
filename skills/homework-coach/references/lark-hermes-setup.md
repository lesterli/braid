# Milestone 1 setup — run homework-coach on Lark via Hermes

Goal: you (the parent) test the Socratic-loop + solver feel on Lark. Single
tenant, local backend. Steps that need YOUR Lark credentials are marked 🔑.

Current machine state (checked 2026-06-06):
- `~/.hermes` already configured + authenticated (config_version 22, auth.json).
- `code_execution.mode: project` — execute_code is on. ✓
- `skills.external_dirs: []` — empty; this is the hook to add braid.
- `hermes` binary NOT on PATH — needs (re)install.
- No `feishu`/`lark` channel block in config — Lark not connected yet.
- verifier verified: imports + runs in a clean process with sympy. ✓

## O1 — Hermes binary on PATH

Config + auth already exist, so this is just getting the runtime back. Install
Hermes Agent per its current instructions (Nous Research), then confirm:

```bash
hermes --version
hermes config get code_execution.mode    # expect: project
```

If install offers a backend choice: pick **local** for this milestone (you test
while your machine is on). Switch to Modal/Daytona serverless (~few $/mo) later
when Grace uses it unattended.

## O3 — verifier reachable from execute_code + sympy present

`code_execution.mode: project` runs code in the project working dir. The engine
imports `verifier` from this skill's `scripts/`. Make both true in that env:

```bash
# sympy in the environment Hermes uses for code execution
pip install -r skills/homework-coach/scripts/requirements.txt

# verify the exact call path the engine uses
cd skills/homework-coach/scripts && python -c \
  "from verifier import solve,equivalent,is_solved,Unsupported; print(equivalent('2*x=6','x=3'))"
# -> True
```

If Hermes runs code in an isolated/Docker env, ensure `scripts/` is mounted /
on `PYTHONPATH` and sympy is installed inside that env.

## Wire the skill in — via external_dirs (keeps git as source of truth)

Point Hermes at braid's skills dir instead of copying, so the canonical copy
stays version-controlled in this repo:

```bash
hermes skills tap add lesterli/braid          # if using taps
# or set skills.external_dirs to include the braid skills path:
hermes config set skills.external_dirs '["/Users/lyy/lester/braid/skills"]'
hermes skills list | grep homework-coach
```

## O4 — pin the engine Skill against auto-refinement 🔒

Hermes auto-extracts/refines Skills after tasks. Our invariants (never give the
answer) must not drift. Keep `SKILL.md` git-controlled as the only source of
truth, and turn off auto-refine for it:

```bash
# tune down creation/refinement nudging (config has creation_nudge_interval)
# and do NOT accept any Hermes-proposed edit to homework-coach/SKILL.md.
hermes config get skills.creation_nudge_interval
```

If Hermes proposes a refinement to this skill, reject it. If it edited the
file, `git diff` in braid will show it — revert. Treat the repo copy as law.

## O2 — connect Lark 🔑 (needs your Lark app)

No `lark`/`feishu` block exists in config yet. You need a Lark custom app:

1. 🔑 In Lark Developer Console, create a custom app; enable Bot; get
   **App ID** + **App Secret**.
2. 🔑 Add the bot to a chat with the student account (single tenant: your own
   Lark org; add Grace's account + yours as two channels later — for this
   milestone one chat is enough to feel it).
3. Connect it in Hermes gateway:
   ```bash
   hermes channels add lark            # follow prompts for App ID / Secret
   # minimize tool-schema bloat (the "Feishu is slow" footgun): keep only what
   # you need for send/receive; disable Docs/Wiki/Drive/Bitable tool groups
   # for this milestone (no state yet).
   ```
4. 🔑 Configure the event subscription / connection mode per Hermes' Lark
   gateway docs (long-poll = no tunnel; webhook = expose via ngrok).

## Smoke test (the actual milestone goal)

In your Lark chat with the bot:

- Send `27 × 6` → expect it to open with a "what's different / how to break it
  up" question, NOT the answer.
- Send `2x = 6`, then reply `x = 2` → expect it to catch the wrong step with one
  question (it called `equivalent("2*x=6","x=2")` → False), never "it's 3".
- Reply `x = 3` → expect it to recognize the win (`is_solved` True) and never
  having stated the answer itself.
- Send a geometry/word problem → expect degraded-mode disclosure ("I can't
  double-check the math on this kind yet"), still no answer given.

If all four behave, milestone 1 is proven on Lark.
