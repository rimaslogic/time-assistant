"""Oura adapter — wraps the standalone `oura` skill CLI (readiness)."""
import os
import sys
from integrations.base import CliAdapter, Manifest, KIND_BIOMETRIC
from engine.records import BiometricRecord

OURA_CLI = os.path.join(os.path.dirname(__file__), "clients", "oura_client.py")


class OuraAdapter(CliAdapter):
    CLI_PATH = OURA_CLI
    manifest = Manifest(
        id="oura", kind=KIND_BIOMETRIC, label="Oura Ring (sleep / readiness)",
        auth_fields=["OURA_ACCESS_TOKEN"],
        capabilities=["readiness", "sleep", "hrv"],
        how_to_obtain="cloud.ouraring.com/personal-access-tokens (active membership required)",
    )

    def check_auth(self) -> bool:
        try:
            self._run([sys.executable, self._cli, "info", "--json"], env=self._env())
            return True
        except Exception:
            return False

    def fetch(self, start: str, end: str) -> list:
        raw = self._run(
            [sys.executable, self._cli, "readiness", "--start", start, "--end", end, "--json"],
            env=self._env(),
        )
        rows = raw.get("data", raw) if isinstance(raw, dict) else raw
        records = []
        for row in rows:
            if row.get("score") is None:
                continue
            records.append(BiometricRecord(
                date=row.get("day", ""), metric="readiness",
                value=float(row["score"]), source="oura",
            ))
        return records
