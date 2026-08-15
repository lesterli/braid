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

`harness.py` is the shared runner. `test_scenarios.py` covers:

bootstrap, content day, silent day, content dry run, same-day
idempotency, missing/invalid taste, malformed scored JSON, weekly
roundup, zero-item weekly heartbeat, feed-management triggers, and
trigger false positives.

Each scenario asserts the observable result and that persistent state
changed only where intended.
