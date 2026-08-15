# daily-curator evaluations

Fixture-driven suite. Every case uses a throwaway `--home`; it never
touches `~/.daily-curator`.

```bash
# from the repo root
python3 -m unittest discover -s skills/daily-curator/evals -v

# from this directory
python3 -m unittest discover -v
```

Stdlib only. Feed bodies are `file://` fixtures (no network).

`harness.py` is the shared runner: isolated state, fixture install
(seen / shown / taste / feeds / scored), script invocation from
`$SKILL_DIR`, and before/after state diffs. Scenario tests live in
`test_*.py`.
