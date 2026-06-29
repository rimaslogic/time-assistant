from integrations.oura_adapter import OuraAdapter
from engine.records import BiometricRecord


def fake_runner(cmd, env=None):
    # Mimic `oura readiness --json` shape.
    return {"data": [
        {"day": "2026-06-01", "score": 88},
        {"day": "2026-06-02", "score": 72},
    ]}


def test_manifest():
    a = OuraAdapter()
    assert a.manifest.id == "oura"
    assert a.manifest.kind == "biometric"
    assert a.manifest.auth_fields == ["OURA_ACCESS_TOKEN"]


def test_fetch_returns_readiness_biometrics():
    a = OuraAdapter(cli_runner=fake_runner, secrets={"OURA_ACCESS_TOKEN": "t"})
    recs = a.fetch("2026-06-01", "2026-06-02")
    assert all(isinstance(r, BiometricRecord) for r in recs)
    assert recs[0].metric == "readiness"
    assert recs[0].value == 88.0
    assert recs[0].source == "oura"


def test_fetch_skips_null_score():
    def runner(cmd, env=None):
        return {"data": [
            {"day": "2026-06-01", "score": 88},
            {"day": "2026-06-02", "score": None},
        ]}
    a = OuraAdapter(cli_runner=runner, secrets={"OURA_ACCESS_TOKEN": "t"})
    recs = a.fetch("2026-06-01", "2026-06-02")
    assert len(recs) == 1
    assert recs[0].date == "2026-06-01"


def test_fetch_handles_bare_list():
    def runner(cmd, env=None):
        return [{"day": "2026-06-01", "score": 90}]
    a = OuraAdapter(cli_runner=runner, secrets={"OURA_ACCESS_TOKEN": "t"})
    recs = a.fetch("2026-06-01", "2026-06-01")
    assert len(recs) == 1
    assert recs[0].value == 90.0
