# 🔴 Warmonitor

**Live Iran–USA conflict terminal dashboard** — a modern, async TUI built with [Textual](https://textual.textualize.io/).

```
┌────────────────────────────────────────────────────────────────────────────┐
│ 🔴 WARMONITOR  Iran–USA Conflict Dashboard              2025-06-01 12:00 UTC│
├──────────────┬───────────────────────────────────────┬─────────────────────┤
│ STATUS       │ ⚡ LIVE FEED                           │ SOURCES             │
│ DEFCON: 3    │ 🔴 [2m ago] Strike on facility         │ 🟢 ISW — Iran       │
│ Last event:  │     ↳ Reuters World News              │ 🟢 Reuters          │
│ 2m ago       │ 🟠 [15m ago] Missile launch detected  │ 🟢 BBC News         │
│ Events/hr: 3 │     ↳ BBC News — World                │ 🟡 Critical Threats │
│              │ 🟡 [1h ago] Sanctions warning         │                     │
│              │     ↳ Soufan Center                   │ [R] Refresh         │
│              │                                       │ [Q] Quit            │
│              │                                       │ [F] Filter          │
│              │                                       │ [S] Sort            │
│              │                                       │ [O] Open URL        │
└──────────────┴───────────────────────────────────────┴─────────────────────┘
```

---

## Features

- Real-time RSS aggregation from verified, high-credibility sources
- Auto-refresh every 60 seconds
- DEFCON auto-calculation based on event severity
- Severity scoring (CRITICAL → INFO) with color-coded feed
- Keyword filtering for Iran/Middle East events
- Filter (≥3) and sort (severity/time) toggles
- **Persistent event cache** across restarts (`~/.warmonitor_cache.json`)
- **Configurable sources** via `~/.warmonitor.toml`
- **Clickable events** — press `O` or `Enter` on a highlighted row to open in browser

---

## Install & Run

```bash
pip install uv
uv sync
uv run warmonitor
```

---

## Configuration (`~/.warmonitor.toml`)

You can customize or extend the built-in source list with a TOML config file:

```toml
# Set to true to replace all built-in sources with your own
replace_defaults = false

[[sources]]
id = "ap_news"
name = "AP News"
url = "https://feeds.apnews.com/rss/apf-topnews"
type = "rss"
keywords = ["Iran", "Israel", "US military", "Middle East"]
credibility = "HIGH"
color = "green"
```

If the file does not exist or contains errors, the built-in sources are used automatically.

---

## Persistent Cache (`~/.warmonitor_cache.json`)

Events are saved to `~/.warmonitor_cache.json` after each fetch so the feed is
pre-populated immediately on restart. Up to 500 events are stored. The file is
created automatically; delete it to start fresh.

---

## Sources

| Source | Type | Credibility |
|--------|------|-------------|
| ISW — Iran Updates | RSS | HIGH |
| Critical Threats (AEI) | RSS | HIGH |
| Soufan Center IntelBrief | RSS | HIGH |
| Reuters World News | RSS | HIGH |
| BBC News — World | RSS | HIGH |
| Crisis Group CrisisWatch | RSS | HIGH |

---

## Key Bindings

| Key | Action |
|-----|--------|
| `R` | Force refresh all feeds |
| `Q` | Quit |
| `F` | Toggle filter (severity ≥ 3) |
| `S` | Toggle sort (severity / time) |
| `O` / `Enter` | Open highlighted event URL in browser |
| `↑` / `↓` | Move focus between event rows |

---

## Severity Scale

| Level | Score | Keywords |
|-------|-------|---------|
| 🔴 CRITICAL | 5 | strike, attack, nuclear, war, explosion, killed, casualties |
| 🟠 HIGH | 4 | missile, drone, retaliation, military, troops |
| 🟡 MEDIUM | 3 | sanctions, diplomacy, threat, warning |
| 🔵 LOW | 2 | talks, negotiations, meeting |
| ⚪ INFO | 1 | everything else |