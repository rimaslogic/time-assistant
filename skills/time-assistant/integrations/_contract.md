# Integration Adapter Contract

Every data source the time-assistant uses is exposed through an **adapter** that
conforms to this contract. The engine never calls a tool's CLI directly — it
asks an adapter for normalized records. This is what lets a new tracker or
biometric source plug in without touching the engine or SKILL.md.

## An adapter MUST

1. Define a class-level `manifest: Manifest` declaring:
   - `id` — stable lowercase id (e.g. `"timeular"`, `"oura"`, `"strava"`)
   - `kind` — one of `time` | `biometric` | `activity`
   - `label` — human name shown in onboarding
   - `auth_fields` — env-var / secret names the adapter needs
   - `capabilities` — list of metric/record keys it can return
   - `how_to_obtain` — one line telling a customer how to get the credentials
2. Implement `check_auth() -> bool` (cheap call; True if creds work).
3. Implement `fetch(start, end) -> list[Record]` returning **only** normalized
   records (`TimeRecord` / `BiometricRecord` / `ActivityRecord`) for its kind.
   Date range is inclusive `YYYY-MM-DD`.
4. Read its secrets via `engine.credentials.get_secrets(self.manifest.auth_fields)`
   — never hardcode a vault item name or a credential source.

## An adapter MUST NOT

- Write to the tenant store, print secrets, or assume a specific tenant.
- Change the underlying skill's CLI (wrap it; the skill stays standalone).

## Normalized shapes (see engine/records.py)

- `TimeRecord(start, end, activity, tags, note, source, duration_min)`
- `BiometricRecord(date, metric, value, source)`
- `ActivityRecord(date, type, duration_min, intensity, source)`

## Registration

Add the adapter class to `integrations/registry.py::ADAPTERS`. Run
`python3 -m integrations.registry --emit` to regenerate `registry.json`.
Onboarding reads `registry.json` to show the integration menu.
