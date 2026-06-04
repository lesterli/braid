# Braid

Validated agent skills distilled from real-world practice.

This repository follows the open `SKILL.md` directory format used across agent ecosystems, including Codex, Claude Code, `skills.sh`, SkillsMP, and ClawHub/OpenClaw.

## Skills

| Skill | Description |
|-------|-------------|
| [article-to-insights](./skills/article-to-insights/) | Turn one article URL into a structured reading result: core summary, relevance analysis, and actionable recommendation. |
| [daily-curator](./skills/daily-curator/) | Generate a curated daily reading list of high-quality articles from trusted sources, with scoring, dedup, and a persistent reading queue. |
| [profile-audit](./skills/profile-audit/) | Diagnose a 小红书 / Twitter profile from a screenshot. Scoped to service-providing OPC (designer / consultant / coach / freelancer / SaaS founder). Scores 5 funnel-aligned dimensions with binary sub-checks, returns a band score and concrete improvement edits. |

## Install

### `skills.sh` / `npx skills`

Install interactively:

```bash
npx skills@latest add lesterli/braid
```

Install directly from GitHub with an explicit skill name:

```bash
npx skills@latest add lesterli/braid --skill article-to-insights
npx skills@latest add lesterli/braid --skill daily-curator
npx skills@latest add lesterli/braid --skill profile-audit
```

Use `--skill <skill-name>` to install exactly the skill you want.

You can also install a single skill by GitHub tree URL:

```bash
npx skills@latest add https://github.com/lesterli/braid/tree/main/skills/daily-curator
```

### Hermes Agent

Install an individual skill from the repo path:

```bash
hermes skills install lesterli/braid/skills/daily-curator
```

Or add this repo as a Hermes tap. Hermes taps default to the `skills/`
directory, which is this repo's layout:

```bash
hermes skills tap add lesterli/braid
hermes skills install lesterli/braid/daily-curator
```

### Manual install for Codex or Claude Code

Prerequisite: the corresponding agent CLI is already installed.

```bash
# Clone the repo
git clone https://github.com/lesterli/braid.git
cd braid

# Claude Code global skills (~/.claude/skills)
mkdir -p ~/.claude/skills
cp -r skills/article-to-insights ~/.claude/skills/
cp -r skills/daily-curator ~/.claude/skills/
cp -r skills/profile-audit ~/.claude/skills/

# Codex global skills (${CODEX_HOME:-~/.codex}/skills)
mkdir -p "${CODEX_HOME:-$HOME/.codex}/skills"
cp -r skills/article-to-insights "${CODEX_HOME:-$HOME/.codex}/skills/"
cp -r skills/daily-curator "${CODEX_HOME:-$HOME/.codex}/skills/"
cp -r skills/profile-audit "${CODEX_HOME:-$HOME/.codex}/skills/"
```

Restart the agent after installation so new skills are discovered.

## Compatibility

- `skills.sh`: install from this GitHub repo with `npx skills@latest add ... --skill <skill-name>`
- Hermes Agent: install a skill directly with `hermes skills install lesterli/braid/skills/<skill-name>`, or add the repo as a tap.
- SkillsMP: compatible with the open `SKILL.md` spec and suitable for indexing or listing as-is
- ClawHub / OpenClaw: each skill directory is publishable as a standalone skill bundle

## Skill Structure

Each skill is a self-contained folder:

```text
skills/
  skill-name/
    SKILL.md            # Entry point: trigger rules, workflow, output format
    references/         # Supporting docs: examples, guardrails, format specs
    scripts/            # Helper scripts for validation or preprocessing
    agents/             # Agent-specific configs (e.g., OpenAI, Claude)
```

## License

MIT
