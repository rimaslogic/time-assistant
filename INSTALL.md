# Installing Time Assistant

## Requirements

- **Claude Code** — install the desktop app or CLI from
  [code.claude.com/docs/en/setup](https://code.claude.com/docs/en/setup)
  (desktop app for macOS/Windows, or `curl -fsSL https://claude.ai/install.sh | bash`).
  Requires a paid Claude plan (Pro, Max, Team, or Enterprise) — the free claude.ai plan
  does not include Claude Code.
- **No Python install required** — the plugin bootstraps its own interpreter on first run.

---

## Install

### Step 1 — Add the marketplace

```
/plugin marketplace add rimaslogic/time-assistant
```

This registers the `rimaslogic-plugins` catalog with your Claude Code.
No plugins are installed yet.

### Step 2 — Install the plugin

```
/plugin install time-assistant@rimaslogic-plugins
```

Installs to user scope by default (available in all your projects).

### Step 3 — Reload plugins

```
/reload-plugins
```

### Step 4 — Run the setup wizard

Type in Claude Code:

```
set up my time assistant
```

The wizard will:
1. Create your private data store in the plugin's per-OS application-data folder
   (or a synced folder you choose).
2. Walk you through connecting **Google Calendar** (zero-friction, no token paste).
3. Optionally prompt for an **Oura** token and/or a **Timeular** API key, validate each,
   and store it in the OS keystore.
4. Optionally connect **Strava** (advanced — needs a Strava API app; on-device OAuth).
5. Render your first time brief.
6. Optionally offer to schedule a daily brief (you see exactly what gets installed first).

Every step is skippable; the assistant is useful with just Google Calendar connected.

---

## Python bootstrap (automatic)

On first run, the `SessionStart` hook checks for a compatible Python (≥3.10).
If none is found it downloads a standalone CPython build (via `python-build-standalone`)
into the plugin's per-OS data folder and exports `TIME_ASSISTANT_PYTHON` via
`CLAUDE_ENV_FILE`. Subsequent sessions reuse the cached interpreter — no network call
after the first run.

You do **not** need to install or configure Python yourself.

---

## QA checklist (bare-machine gates)

These gates cannot be covered by the unit-test suite — run them on a real machine
before marking a release "installable."

### Gate 1 — Plugin validation

```bash
claude plugin validate /path/to/rimaslogic/time-assistant
```

**Expected:** no errors; `time-assistant` listed as a recognised plugin.

> On this repo's checkout: `claude plugin validate /path/to/time-assistant`

---

### Gate 2 — No-Python bootstrap (macOS / Linux / Windows)

Scenario: fresh user account with no Python ≥3.10 in `$PATH`.

1. Install the plugin per the steps above.
2. Start Claude Code. Watch the `SessionStart` hook output.
3. Confirm the hook logs a download message and completes without error.
4. In a Bash tool call, run:
   ```bash
   echo $TIME_ASSISTANT_PYTHON
   ```
   **Expected:** a non-empty path to the downloaded standalone Python binary, and
   `"$TIME_ASSISTANT_PYTHON" --version` reports 3.12.x.

> Verified in a sandbox on macOS arm64: with all `python*` shadowed, the bootstrap
> downloaded `cpython-3.12.13 … aarch64-apple-darwin`, resolved it, wrote the export,
> and the engine imported on it.

---

### Gate 3 — Full `set up my time assistant` end-to-end

Run on a clean tenant (no existing data store):

| Check | Expected |
|-------|----------|
| Data store created | the per-OS data folder (or chosen folder) contains `config.json` + seeded files after the wizard completes |
| Google Calendar | connector authorises; at least one calendar event is readable |
| Oura token | validates against the Oura API; stored in the OS keystore |
| Timeular token | validates against Timeular API v3; stored in the OS keystore |
| First brief | morning brief renders without errors |

---

### Gate 4 — Windows (Git Bash)

1. Install Git for Windows (provides Git Bash).
2. Install the plugin and start Claude Code.
3. Confirm the `SessionStart` hook executes under Git Bash without error.
4. Run Gate 3 above.

**Known constraint:** the bootstrap is a bash script; on Windows it runs under Git Bash
(Claude Code's default shell-tool there). Without Git Bash the SessionStart hook won't run.

---

### Gate 5 — Strava (advanced, optional)

Scenario: user wants training-load data.

1. In the wizard's enrichment step, choose Strava.
2. Confirm it opens the Strava API page; create an app and paste Client ID + Secret.
3. Confirm the browser opens Strava's authorize page; approve.
4. Confirm the localhost listener captures the code, the token exchange succeeds, and
   `STRAVA_CLIENT_ID` / `STRAVA_CLIENT_SECRET` / `STRAVA_REFRESH_TOKEN` are stored in the keystore.
5. Confirm a subsequent brief can read Strava load.

---

### Gate 6 — Scheduling (optional)

1. Accept the "schedule a daily brief" offer; pick a time.
2. Confirm the wizard **shows** the exact artifact (launchd plist / cron line / schtasks
   command) before installing.
3. macOS/Linux: after you agree, confirm the launchd job / cron line is installed and the
   scheduled `claude -p` brief fires at the chosen time. Windows: confirm the printed
   `schtasks` command, run it, and verify the task.

---

## CLI equivalents

For scripted / CI installs use the `claude` CLI:

```bash
claude plugin marketplace add rimaslogic/time-assistant
claude plugin install time-assistant@rimaslogic-plugins --scope user
```

---

## Uninstall

```
/plugin uninstall time-assistant@rimaslogic-plugins
/plugin marketplace remove rimaslogic-plugins
```

Your data store and the downloaded Python live in the plugin's per-OS data folder and are
**not** removed automatically — delete that folder manually if you want a clean slate.
