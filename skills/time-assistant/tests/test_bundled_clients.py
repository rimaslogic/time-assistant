import sys
from pathlib import Path
from integrations.timeular_adapter import TimeularAdapter
from integrations.oura_adapter import OuraAdapter

CLIENTS = Path(__file__).resolve().parent.parent / "integrations" / "clients"


def test_bundled_clients_exist():
    assert (CLIENTS / "early_client.py").exists()
    assert (CLIENTS / "oura_client.py").exists()


def test_timeular_and_oura_point_at_bundled_clients():
    assert "integrations/clients" in TimeularAdapter()._cli.replace("\\", "/")
    assert "integrations/clients" in OuraAdapter()._cli.replace("\\", "/")


def test_timeular_invokes_with_sys_executable():
    captured = {}
    def fake_runner(cmd, env=None):
        captured["cmd"] = cmd
        return []
    TimeularAdapter(cli_runner=fake_runner, secrets={"EARLY_API_KEY": "k", "EARLY_API_SECRET": "s"}).fetch("2026-06-01", "2026-06-01")
    assert captured["cmd"][0] == sys.executable
    assert "early_client.py" in captured["cmd"][1]
