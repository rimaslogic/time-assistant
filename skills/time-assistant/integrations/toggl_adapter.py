"""Toggl Track adapter — proves the contract generalizes to a brand-new source
with no pre-existing skill. Uses Toggl API v9 via stdlib urllib."""
import base64
import json
import urllib.request

from integrations.base import Adapter, Manifest, KIND_TIME
from engine.records import TimeRecord
from engine import credentials


def _default_http(token: str, start: str, end: str):
    url = f"https://api.track.toggl.com/api/v9/me/time_entries?start_date={start}&end_date={end}"
    auth = base64.b64encode(f"{token}:api_token".encode()).decode()
    req = urllib.request.Request(url, headers={"Authorization": f"Basic {auth}"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode())


class TogglAdapter(Adapter):
    manifest = Manifest(
        id="toggl", kind=KIND_TIME, label="Toggl Track (time tracking)",
        auth_fields=["TOGGL_API_TOKEN"], capabilities=["entries", "tags"],
        how_to_obtain="track.toggl.com → Profile → API Token",
    )

    def __init__(self, http_fn=_default_http, secrets=None):
        self._http = http_fn
        self._secrets = secrets

    def _token(self) -> str:
        if self._secrets:
            return self._secrets["TOGGL_API_TOKEN"]
        return credentials.get_secret("TOGGL_API_TOKEN")

    def check_auth(self) -> bool:
        try:
            self._http(self._token(), "2026-01-01", "2026-01-02")
            return True
        except Exception:
            return False

    def fetch(self, start: str, end: str) -> list:
        raw = self._http(self._token(), start, end)
        records = []
        for e in raw:
            records.append(TimeRecord(
                start=e.get("start", ""), end=e.get("stop", ""),
                activity=e.get("description", ""), tags=list(e.get("tags") or []),
                note="", source="toggl",
            ))
        return records
