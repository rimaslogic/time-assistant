from integrations.strava_adapter import StravaAdapter
from engine.records import ActivityRecord


def fake_runner(cmd, env=None):
    # Mimic `strava activities --json` list shape.
    return [
        {"start_date_local": "2026-06-01T17:00:00Z", "type": "Run",
         "moving_time": 2520, "suffer_score": 55, "name": "Evening run"},
        {"start_date_local": "2026-06-03T17:00:00Z", "type": "Ride",
         "moving_time": 3600, "suffer_score": 40, "name": "Out of range"},
    ]


def test_manifest():
    a = StravaAdapter()
    assert a.manifest.id == "strava"
    assert a.manifest.kind == "activity"
    assert "STRAVA_REFRESH_TOKEN" in a.manifest.auth_fields


def test_fetch_filters_range_and_maps_fields():
    a = StravaAdapter(cli_runner=fake_runner, secrets={
        "STRAVA_CLIENT_ID": "1", "STRAVA_CLIENT_SECRET": "2", "STRAVA_REFRESH_TOKEN": "3"})
    recs = a.fetch("2026-06-01", "2026-06-02")
    assert len(recs) == 1                       # second activity is out of range
    assert isinstance(recs[0], ActivityRecord)
    assert recs[0].type == "Run"
    assert recs[0].duration_min == 42
    assert recs[0].intensity == 55.0
    assert recs[0].source == "strava"
