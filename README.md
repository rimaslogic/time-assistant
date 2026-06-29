# time-assistant

**80/20 Time Assistant** — a personal operating system that keeps you running at 80% high-value time (HVT) with a hard 20% cap on low-value operational time (LVT).

Built on **Claude Code** (scheduling + LLM reasoning), **Google Calendar MCP** (planned time), pluggable time-tracking adapters (Timeular, Toggl), and a private GitHub repo for memory.

---

## Architecture at a glance

```
07:30 daily ─► morning-brief routine ──┐
19:00 daily ─► evening-review routine ─┼─► Google Calendar (MCP)
Fri 16:00  ─► weekly-review routine ───┤   Time-tracking API (HTTP)
                                       └─► GitHub memory repo (private)
```

Three scheduled routines + a Claude Skill for on-demand analysis. No database, no self-hosted infrastructure.

---

## What's in this repo

| Directory | Contents |
|---|---|
| `skills/time-assistant/` | Claude Skill for on-demand work — installed automatically by the plugin |
| `hooks/` | Claude Code hooks (SessionStart bootstrap) |
| `welcome/` | Plugin welcome/install page |

---

## Memory repo separation

This `time-assistant` repo holds **code and prompts** — the system itself.

You also need a **second private repo** for memory (rules, scores, archives, feedback inbox). The setup wizard creates and seeds it automatically. Why separate?

- This repo is the build artifact — stable, rarely changes
- The memory repo changes on every routine run — commit churn would drown the real history
- You can grant Claude Code's GitHub connector narrow access to just the memory repo

---

## Quick start

Full instructions: [`INSTALL.md`](./INSTALL.md)

Short version:
1. Add the marketplace: `/plugin marketplace add rimaslogic/time-assistant`
2. Install: `/plugin install time-assistant@rimaslogic-plugins`
3. Run the wizard: `set up my time assistant`

~15 minutes total setup. No infrastructure to maintain afterward.

---

Built by [Rimas Lukaszewicz](https://rimaslogic.pl) · [Rimas Logic](https://rimaslogic.pl) · MIT License
