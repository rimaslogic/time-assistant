import sys
from pathlib import Path
from integrations.strava_adapter import StravaAdapter

CLIENTS = Path(__file__).resolve().parent.parent / "integrations" / "clients"


def test_strava_client_bundled_and_stdlib_only():
    src = (CLIENTS / "strava_client.py").read_text()
    assert "import requests" not in src
    assert "urllib" in src


def test_strava_adapter_points_at_bundled_client():
    assert "integrations/clients" in StravaAdapter()._cli.replace("\\", "/")


def test_strava_adapter_invokes_with_sys_executable():
    captured = {}
    def fake_runner(cmd, env=None):
        captured["cmd"] = cmd
        return []
    StravaAdapter(cli_runner=fake_runner, secrets={
        "STRAVA_CLIENT_ID": "1", "STRAVA_CLIENT_SECRET": "2", "STRAVA_REFRESH_TOKEN": "3"
    }).fetch("2026-06-01", "2026-06-02")
    assert captured["cmd"][0] == sys.executable
    assert "strava_client.py" in captured["cmd"][1]
