# Curated Feeds

Starter template and quality tier reference. When a user first says "今日推荐" and has no `~/.daily-curator/feeds.txt` yet, these feeds are used as the default source list.

This file also serves as the **tier classification reference** — feeds listed here under Tier 1 categories get the 1.2× quality multiplier even when loaded from `feeds.txt`.

## AI & LLM

| Source | Feed URL | Note |
|--------|----------|------|
| Simon Willison | `https://simonwillison.net/atom/entries/` | Prolific, practical AI/LLM coverage with working code |
| Simon Willison TIL | `https://til.simonwillison.net/tils/feed.atom` | Short, focused learnings |
| Latent Space | `https://www.latent.space/feed` | Deep technical AI/ML analysis and interviews |
| One Useful Thing | `https://www.oneusefulthing.org/feed` | Ethan Mollick — AI in education and work, accessible |
| Interconnects | `https://www.interconnects.ai/feed` | Nathan Lambert — RLHF, open models, AI policy |
| Ahead of AI | `https://magazine.sebastianraschka.com/feed` | Sebastian Raschka — ML research distilled |

## Engineering & Programming

| Source | Feed URL | Note |
|--------|----------|------|
| Julia Evans | `https://jvns.ca/atom.xml` | Systems, networking, debugging — always clear |
| Julia Evans TIL | `https://jvns.ca/til/atom.xml` | Bite-sized technical learnings |
| Dan Luu | `https://danluu.com/atom.xml` | Rigorous, data-driven engineering analysis |
| Thorsten Ball | `https://registerspill.thorstenball.com/feed` | Compilers, interpreters, craft of programming |
| Eli Bendersky | `https://eli.thegreenplace.net/feeds/all.atom.xml` | Go, compilers, systems programming |
| Martin Fowler | `https://martinfowler.com/feed.atom` | Software architecture and design patterns |

## Thinking & Essays

| Source | Feed URL | Note |
|--------|----------|------|
| Paul Graham | `http://www.aaronsw.com/2002/feeds/pgessays.rss` | Startups, thinking, writing |
| Farnam Street | `https://fs.blog/feed/` | Mental models and decision-making |
| James Clear | `https://jamesclear.com/feed` | Habits, systems thinking |
| Astral Codex Ten | `https://www.astralcodexten.com/feed` | Scott Alexander — rationality, science, society |

## Open Source & Industry

| Source | Feed URL | Note |
|--------|----------|------|
| Hacker News Best | `https://hnrss.org/best` | Community-voted top stories |
| The Pragmatic Engineer | `https://newsletter.pragmaticengineer.com/feed` | Gergely Orosz — engineering culture and industry |

---

## How Feeds Work

**User's personal feeds** are stored in `~/.daily-curator/feeds.txt` (one URL per line). This is the primary source list once it exists.

Common user actions — all persisted to `feeds.txt`:

- "关注 https://example.com/feed.xml" → append URL
- "取消关注 example.com" → remove matching line
- "导入 OPML https://..." → extract all feed URLs via `scripts/import-opml.sh` and append

If `feeds.txt` doesn't exist yet, the agent uses the tables above as the default starter set. On first "关注" or OPML import, the agent creates `feeds.txt` — seeded with the defaults above plus the user's addition.
