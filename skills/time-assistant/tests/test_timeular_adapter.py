from integrations.timeular_adapter import TimeularAdapter
from engine.records import TimeRecord


def fake_runner(cmd, env=None):
    # Mimic `early entries --json` decoded output.
    return [
        {"startedAt": "2026-06-01T07:00:00.000", "stoppedAt": "2026-06-01T08:30:00.000",
         "activity": "focus", "tags": ["acme"], "note": "arch review"},
        {"startedAt": "2026-06-01T09:00:00.000", "stoppedAt": "2026-06-01T09:20:00.000",
         "activity": "emails", "tags": [], "note": None},
    ]


def test_manifest():
    a = TimeularAdapter()
    assert a.manifest.id == "timeular"
    assert a.manifest.kind == "time"
    assert a.manifest.auth_fields == ["EARLY_API_KEY", "EARLY_API_SECRET"]


def test_fetch_normalizes_and_handles_null_note():
    a = TimeularAdapter(cli_runner=fake_runner, secrets={"EARLY_API_KEY": "k", "EARLY_API_SECRET": "s"})
    recs = a.fetch("2026-06-01", "2026-06-01")
    assert all(isinstance(r, TimeRecord) for r in recs)
    assert recs[0].duration_min == 90
    assert recs[0].tags == ["acme"]
    assert recs[1].note == ""   # null note coerced to empty string (known early bug)
    assert recs[1].source == "timeular"
