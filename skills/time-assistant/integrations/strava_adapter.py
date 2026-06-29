"""Strava adapter — wraps the standalone `strava` skill CLI (activities)."""
import os
import sys
from integrations.base import CliAdapter, Manifest, KIND_ACTIVITY
from engine.records import ActivityRecord

STRAVA_CLI = os.path.join(os.path.dirname(__file__), "clients", "strava_client.py")


class StravaAdapter(CliAdapter):
    CLI_PATH = STRAVA_CLI
    manifest = Manifest(
        id="strava", kind=KIND_ACTIVITY, label="Strava (training load)",
        auth_fields=["STRAVA_CLIENT_ID", "STRAVA_CLIENT_SECRET", "STRAVA_REFRESH_TOKEN"],
        capabilities=["activities", "load", "suffer_score"],
        how_to_obtain="strava.com/settings/api → client id+secret, then OAuth for refresh token",
    )

    def check_auth(self) -> bool:
        try:
            self._run([sys.executable, self._cli, "--json", "athlete"], env=self._env())
            return True
        except Exception:
            return False

    def fetch(self, start: str, end: str) -> list:
        raw = self._run(
            [sys.executable, self._cli, "--json", "activities", "--after", start, "--limit", "100"],
            env=self._env(),
        )
        records = []
        for a in raw:
            day = (a.get("start_date_local", "")[:10])
            if not day or day < start or day > end:
                continue
            records.append(ActivityRecord(
                date=day, type=a.get("type", ""),
                duration_min=int(a.get("moving_time", 0)) // 60,
                intensity=float(a.get("suffer_score") or 0.0), source="strava",
            ))
        return records
