"""Timeular/EARLY adapter — wraps the standalone `early` skill CLI.

Always uses --json (the early `entries` text formatter crashes on null notes).
"""
import os
import sys

from integrations.base import CliAdapter, Manifest, KIND_TIME
from engine.records import TimeRecord

EARLY_CLI = os.path.join(os.path.dirname(__file__), "clients", "early_client.py")


class TimeularAdapter(CliAdapter):
    CLI_PATH = EARLY_CLI
    manifest = Manifest(
        id="timeular", kind=KIND_TIME, label="Timeular / EARLY (time tracking)",
        auth_fields=["EARLY_API_KEY", "EARLY_API_SECRET"],
        capabilities=["entries", "tags", "activities"],
        how_to_obtain="profile.timeular.com → Integrations → API (key + secret)",
    )

    def check_auth(self) -> bool:
        try:
            self._run([sys.executable, self._cli, "--json", "auth"], env=self._env())
            return True
        except Exception:
            return False

    def fetch(self, start: str, end: str) -> list:
        raw = self._run(
            [sys.executable, self._cli, "--json", "entries", "--start", start, "--end", end],
            env=self._env(),
        )
        records = []
        for e in raw:
            records.append(TimeRecord(
                start=e.get("startedAt", ""), end=e.get("stoppedAt", ""),
                activity=e.get("activity", ""), tags=list(e.get("tags") or []),
                note=e.get("note") or "", source="timeular",
            ))
        return records
