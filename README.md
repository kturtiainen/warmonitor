# 🔴 Warmonitor

**Live Iran–USA conflict terminal dashboard** — a modern, async TUI built with [Textual](https://textual.textualize.io/).

![Screenshot placeholder](docs/screenshot.png)

---

## Features

- Real-time RSS aggregation from verified, high-credibility sources
- Auto-refresh every 60 seconds
- DEFCON auto-calculation based on event severity
- Severity scoring (CRITICAL → INFO) with color-coded feed
- Keyword filtering for Iran/Middle East events
- Filter (≥3) and sort (severity/time) toggles

---

## Install & Run

```bash
pip install uv
uv sync
uv run warmonitor
```

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

---

## Severity Scale

| Level | Score | Keywords |
|-------|-------|---------|
| 🔴 CRITICAL | 5 | strike, attack, nuclear, war, explosion, killed, casualties |
| 🟠 HIGH | 4 | missile, drone, retaliation, military, troops |
| 🟡 MEDIUM | 3 | sanctions, diplomacy, threat, warning |
| 🔵 LOW | 2 | talks, negotiations, meeting |
| ⚪ INFO | 1 | everything else |