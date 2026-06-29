<div align="center">

# ⏱️ Time Assistant

### Run your week at 80% high-value time — a personal time coach that lives inside Claude Code.

It classifies where your hours actually go (high-value vs. low-value), scores each day and week, plans the next one with you, and pulls in your calendar, sleep, and training — all **on your machine**, no servers, no spreadsheets.

[![Claude Code plugin](https://img.shields.io/badge/Claude%20Code-plugin-d97757)](https://code.claude.com/docs/en/discover-plugins)
[![Platforms](https://img.shields.io/badge/macOS%20·%20Windows%20·%20Linux-supported-2ea44f)](#requirements)
[![Python](https://img.shields.io/badge/Python-auto--installed-3776ab)](#requirements)
[![Local-first](https://img.shields.io/badge/data-local--first-blue)](#privacy--your-data)
[![License](https://img.shields.io/badge/license-MIT-lightgrey)](./LICENSE)
[![Status](https://img.shields.io/badge/status-beta%20v0.1-yellow)](#)

_by [Rimas Logic](https://rimaslogic.pl)_

</div>

---

## Quick start

You need **Claude Code** and a **paid Claude plan** ([get Claude Code](https://code.claude.com/docs/en/setup)). Then, inside Claude Code:

```text
/plugin marketplace add rimaslogic/time-assistant
/plugin install time-assistant@rimaslogic-plugins
/reload-plugins
```

…and then just type:

> **`set up my time assistant`**

A friendly wizard takes it from there. Connecting your Google Calendar alone is enough to get value — everything else is optional. **~5 minutes, nothing else to install.** Full walkthrough: [`INSTALL.md`](./INSTALL.md).

---

## Why

Most time trackers tell you *what* you did. This one tells you whether it **mattered** — and helps you fix next week.

|  | Time Assistant | Typical time tracker | Doing it by hand |
|---|:---:|:---:|:---:|
| Classifies time as high- vs low-value (80/20) | ✅ | ❌ | 😮‍💨 |
| Scores your day & week, flags drift | ✅ | partial | ❌ |
| Plans next week *with* you (Socratic, not a scheduler) | ✅ | ❌ | ❌ |
| Pulls calendar + biometrics + training automatically | ✅ | some | ❌ |
| Runs locally — your data never leaves your machine | ✅ | ❌ (cloud) | ✅ |
| Setup for non-technical users | ✅ one phrase | varies | — |

---

## What it does

- **HVT / LVT classification** — every block of time is high-value (strategic, product, content, learning, BD) or low-value (email, meetings, admin, chat, support, context-switching). Target: **80% HVT**, hard cap **20% LVT**.
- **Daily & weekly scoring** — an HVT ratio plus a 0–100 composite (value + plan adherence + low fragmentation), with drift flags.
- **Socratic planning** — “what are the 2–3 outcomes this week will be judged on?” before any blocks get drawn.
- **Learns your rules** — classification rules you confirm are remembered; correct it once and it sticks.
- **Frameworks/profiles** — *Knowledge-worker* (default) or *Consultant* (adds per-client monthly budget tracking). Categories and targets are configurable.

---

## How it works

```
  you ──"set up my time assistant"──►  Claude Code
                                          │
                 ┌────────────────────────┼─────────────────────────┐
                 ▼                        ▼                          ▼
        per-OS data folder        OS keystore (tokens)      integrations
        (rules, scores,           macOS Keychain /          • Google Calendar (1-click)
         config — local)          Credential Locker /       • Oura · Timeular (paste)
                                   Secret Service            • Strava (advanced, on-device OAuth)
                 │
                 ▼
        "how's today?"  ·  "plan my week"  ·  "why am I drifting?"  ·  daily brief
```

No backend, no database. Claude Code provides the reasoning; the plugin provides the engine, the store, and the integrations. On first run a small hook sets up its own Python — **you never install Python**.

---

## Integrations

| Source | What it adds | How you connect |
|---|---|---|
| **Google Calendar** | your scheduled plan (the zero-friction default) | one click in Claude — no token paste |
| **Oura** | sleep / readiness to time your hard cognitive work | paste a personal access token |
| **Timeular** | precise time-tracking actuals vs. plan | paste an API key + secret |
| **Strava** *(advanced)* | training load to balance recovery days | on-device OAuth — fully local, no backend |

Tokens are validated on entry and stored in your OS keystore. Every integration is optional and skippable.

---

## Privacy & your data

- **Local-first.** Your rules, scores, and config live in a folder on **your** machine (optionally a synced folder you choose). Nothing is sent to any server we run — there is no server.
- **Secrets in the OS keystore** (macOS Keychain, Windows Credential Locker, Linux Secret Service), with a permission-locked file fallback.
- **No telemetry.** The only network calls are to the services you explicitly connect.

---

## Requirements

- **Claude Code** (desktop app or CLI) — [install guide](https://code.claude.com/docs/en/setup).
- A **paid Claude plan** (Pro / Max / Team / Enterprise). The free claude.ai plan does not include Claude Code.
- **macOS, Windows, or Linux.** No manual Python install — the plugin downloads a standalone interpreter on first run if your machine doesn't already have Python 3.10+.

---

## Optional: a daily brief on a schedule

Ask the wizard to “schedule my daily brief” and it generates a per-OS schedule entry (launchd / cron / Task Scheduler) and **shows you exactly what it will add** before installing — never silently.

---

## Status

Beta (`v0.1`). Install + setup are verified; the conversational wizard and integrations are actively being tested on real machines. Feedback and issues welcome.

---

<div align="center">

Built by **[Rimas Lukaszewicz](https://rimaslogic.pl)** · **[Rimas Logic](https://rimaslogic.pl)** · MIT License

</div>
