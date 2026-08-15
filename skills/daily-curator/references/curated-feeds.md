# Curated Feeds

Starter template and quality tier reference. First-run `curate.py bootstrap` seeds `~/.daily-curator/feeds.txt` from the tables below.

Source quality is reflected in the LLM relevance score (via taste.md's positive anchors), **not** as a mechanical multiplier or tiebreaker — the deterministic ranking tiebreaker is recency (see scoring-and-filtering.md). This file is the bootstrap default feed set and a human reference for which sources are "known".

## AI & LLM

| Source | Feed URL | Note |
|--------|----------|------|
| Simon Willison | `https://simonwillison.net/atom/entries/` | Prolific, practical AI/LLM coverage with working code |
| Simon Willison TIL | `https://til.simonwillison.net/tils/feed.atom` | Short, focused learnings |
| Latent Space | `https://www.latent.space/feed` | Deep technical AI/ML analysis and interviews |
| One Useful Thing | `https://www.oneusefulthing.org/feed` | Ethan Mollick — AI in education and work, accessible |
| Interconnects | `https://www.interconnects.ai/feed` | Nathan Lambert — RLHF, open models, AI policy |
| Ahead of AI | `https://magazine.sebastianraschka.com/feed` | Sebastian Raschka — ML research distilled |
| Dwarkesh Patel | `https://www.dwarkeshpatel.com/feed` | Long-form AI interviews with frontier researchers |
| Gwern | `https://gwern.substack.com/feed` | Long-form essays + statistics + AI综述 |
| Max Woolf (minimaxir) | `https://minimaxir.com/index.xml` | Data science + LLM experiments, hands-on |
| Geoffrey Litt | `https://www.geoffreylitt.com/feed.xml` | Malleable software + AI tooling experiments |
| Anthropic Engineering | `https://raw.githubusercontent.com/conoro/anthropic-engineering-rss-feed/main/anthropic_engineering_rss.xml` | Engineering posts (e.g. agent-building). **3rd-party scraper** — no official Anthropic RSS; can break silently, so watch `feeds_ok` |

## Engineering & Programming

| Source | Feed URL | Note |
|--------|----------|------|
| Julia Evans | `https://jvns.ca/atom.xml` | Systems, networking, debugging — always clear |
| Julia Evans TIL | `https://jvns.ca/til/atom.xml` | Bite-sized technical learnings |
| Dan Luu | `https://danluu.com/atom.xml` | Rigorous, data-driven engineering analysis |
| Thorsten Ball | `https://registerspill.thorstenball.com/feed` | Compilers, interpreters, craft of programming |
| Eli Bendersky | `https://eli.thegreenplace.net/feeds/all.atom.xml` | Go, compilers, systems programming |
| Mitchell Hashimoto | `https://mitchellh.com/feed.xml` | HashiCorp founder — Go/Rust, tooling philosophy |
| Hillel Wayne | `https://buttondown.com/hillelwayne/rss` | Formal methods, rigorous engineering thinking |
| Antirez | `http://antirez.com/rss` | Redis creator — engineering craft + occasional AI commentary |
| Armin Ronacher | `https://lucumr.pocoo.org/feed.atom` | Flask creator — Python depth + AI tooling in recent years |

## Open Source & Industry

| Source | Feed URL | Note |
|--------|----------|------|
| Hacker News AI (filtered) | `https://hnrss.org/newest?q=AI&points=100` | AI-tagged HN submissions with ≥100 points |
| Hacker News LLM | `https://hnrss.org/newest?q=LLM&points=80` | LLM-specific submissions with ≥80 points |
| Hacker News programming | `https://hnrss.org/newest?q=programming&points=200` | High-bar programming discussions |
| Hacker News open source | `https://hnrss.org/newest?q=open+source&points=150` | Open-source project launches and discussions |

Note: `hnrss.org/best` was tried earlier and removed — its precision under this taste was near zero (housing, politics, geopolitics dominate). The four targeted queries above give ~10-50× better signal-to-noise for the user's primary axes.

---

## How Feeds Work

**User's personal feeds** are stored in `~/.daily-curator/feeds.txt` (one URL per line). This is the primary source list once it exists.

Common user actions — all persisted to `feeds.txt`:

- "关注 https://example.com/feed.xml" → append URL
- "取消关注 example.com" → remove matching line
- "导入 OPML https://..." → extract all feed URLs via `bash "$SKILL_DIR/scripts/import-opml.sh"` and append

If `feeds.txt` is missing, run `curate.py bootstrap` — that is the only setup path. "关注" and OPML import then append to the existing file.
