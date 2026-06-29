from engine.records import TimeRecord, BiometricRecord, ActivityRecord


def test_time_record_computes_duration():
    r = TimeRecord(
        start="2026-06-01T09:00:00", end="2026-06-01T10:30:00",
        activity="focus", tags=["acme"], note="", source="timeular",
    )
    assert r.duration_min == 90


def test_time_record_explicit_duration_wins():
    r = TimeRecord(
        start="", end="", activity="focus", tags=[], note="",
        source="manual", duration_min=45,
    )
    assert r.duration_min == 45


def test_time_record_roundtrip():
    r = TimeRecord(start="2026-06-01T09:00:00", end="2026-06-01T09:30:00",
                   activity="emails", tags=[], note="n", source="timeular")
    assert TimeRecord.from_dict(r.to_dict()) == r


def test_biometric_record_roundtrip():
    b = BiometricRecord(date="2026-06-01", metric="readiness", value=88.0, source="oura")
    assert BiometricRecord.from_dict(b.to_dict()) == b


def test_activity_record_roundtrip():
    a = ActivityRecord(date="2026-06-01", type="Run", duration_min=42,
                       intensity=55.0, source="strava")
    assert ActivityRecord.from_dict(a.to_dict()) == a
