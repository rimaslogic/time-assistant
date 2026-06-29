from integrations.toggl_adapter import TogglAdapter
from engine.records import TimeRecord


def fake_http(token, start, end):
    return [
        {"start": "2026-06-01T09:00:00+00:00", "stop": "2026-06-01T10:00:00+00:00",
         "description": "Deep work", "tags": ["acme"]},
    ]


def test_manifest():
    a = TogglAdapter()
    assert a.manifest.id == "toggl"
    assert a.manifest.kind == "time"
    assert a.manifest.auth_fields == ["TOGGL_API_TOKEN"]


def test_fetch_normalizes():
    a = TogglAdapter(http_fn=fake_http, secrets={"TOGGL_API_TOKEN": "t"})
    recs = a.fetch("2026-06-01", "2026-06-01")
    assert isinstance(recs[0], TimeRecord)
    assert recs[0].activity == "Deep work"
    assert recs[0].tags == ["acme"]
    assert recs[0].duration_min == 60
    assert recs[0].source == "toggl"
