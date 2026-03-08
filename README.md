# Braid

Validated agent skills distilled from real-world practice.

Each skill is a self-contained prompt package — including workflow, references, guardrails, and scripts — that can be plugged into any LLM-powered agent to handle a specific task reliably.

## Skills

| Skill | Description |
|-------|-------------|
| [article-to-insights](./article-to-insights/) | Turn one article URL into a structured reading result: core summary, relevance analysis, and actionable recommendation. |

## Installation

Prerequisite: the corresponding agent CLI is already installed. Copy the skill folder into your global skill directory:

```bash
# Clone the repo
git clone https://github.com/lesterli/braid.git
cd braid

# Claude Code global skills (~/.claude/skills)
mkdir -p ~/.claude/skills
cp -r article-to-insights ~/.claude/skills/

# Codex global skills (${CODEX_HOME:-~/.codex}/skills)
mkdir -p "${CODEX_HOME:-$HOME/.codex}/skills"
cp -r article-to-insights "${CODEX_HOME:-$HOME/.codex}/skills/"
```

Each skill uses `SKILL.md` as the entry point.

## Skill Structure

```
skill-name/
  SKILL.md              # Entry point: trigger rules, workflow, output format
  references/           # Supporting docs: examples, guardrails, format specs
  scripts/              # Helper scripts for validation or preprocessing
  agents/               # Agent-specific configs (e.g., OpenAI, Claude)
```

## TODO

- [ ] Publish skills to the Claude Code skill marketplace
- [ ] Publish skills to [ClawHub](https://clawhub.com)
- [ ] Add skill evaluation framework (automated quality & consistency checks)
- [ ] Add more skills

## License

MIT
