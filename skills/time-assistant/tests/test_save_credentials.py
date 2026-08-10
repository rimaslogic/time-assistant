import io
import json
import pytest
from onboarding import save_credentials


def run(payload, **kw):
    """Drive main() with a JSON string and capture what it stored and printed."""
    stored, printed, errors = {}, [], []
    rc = save_credentials.main(
        [],
        stdin=io.StringIO(payload),
        setter=kw.get("setter") or (lambda n, v, provider=None: stored.__setitem__(n, v)),
        out=printed.append,
        err=errors.append,
    )
    return rc, stored, "\n".join(printed), "\n".join(errors)


def test_stores_a_single_field():
    rc, stored, out, _ = run(json.dumps({"OURA_ACCESS_TOKEN": "tok"}))
    assert rc == 0
    assert stored == {"OURA_ACCESS_TOKEN": "tok"}
    assert "OURA_ACCESS_TOKEN" in out


def test_stores_multiple_fields_in_one_call():
    rc, stored, _, _ = run(json.dumps({"EARLY_API_KEY": "k", "EARLY_API_SECRET": "s"}))
    assert rc == 0
    assert stored == {"EARLY_API_KEY": "k", "EARLY_API_SECRET": "s"}


def test_accepts_all_three_strava_fields():
    payload = {"STRAVA_CLIENT_ID": "1", "STRAVA_CLIENT_SECRET": "2",
               "STRAVA_REFRESH_TOKEN": "3"}
    rc, stored, _, _ = run(json.dumps(payload))
    assert rc == 0
    assert stored == payload


def test_never_prints_a_value():
    rc, _, out, err = run(json.dumps({"OURA_ACCESS_TOKEN": "super-secret-value"}))
    assert "super-secret-value" not in out
    assert "super-secret-value" not in err


def test_strips_surrounding_whitespace():
    rc, stored, _, _ = run(json.dumps({"OURA_ACCESS_TOKEN": "  tok\n"}))
    assert stored == {"OURA_ACCESS_TOKEN": "tok"}


def test_rejects_malformed_json():
    rc, stored, _, err = run("{not json")
    assert rc == 2
    assert stored == {}
    assert "JSON" in err


def test_rejects_unknown_field():
    rc, stored, _, err = run(json.dumps({"NOT_A_FIELD": "x"}))
    assert rc == 2
    assert stored == {}
    assert "NOT_A_FIELD" in err
    assert "OURA_ACCESS_TOKEN" in err  # lists what IS accepted


def test_rejects_empty_object():
    rc, _, _, err = run("{}")
    assert rc == 2
    assert err


def test_rejects_non_object_json():
    rc, _, _, err = run('["OURA_ACCESS_TOKEN"]')
    assert rc == 2
    assert err


def test_rejects_blank_value():
    rc, stored, _, err = run(json.dumps({"OURA_ACCESS_TOKEN": "   "}))
    assert rc == 2
    assert stored == {}


def test_rejects_non_string_value():
    rc, stored, _, err = run(json.dumps({"OURA_ACCESS_TOKEN": 12345}))
    assert rc == 2
    assert stored == {}


def test_store_guard_error_exits_one_without_leaking():
    from engine.store_guard import StoreGuardError

    def boom(n, v, provider=None):
        raise StoreGuardError("already tracked by git")

    rc, _, out, err = run(json.dumps({"OURA_ACCESS_TOKEN": "tok"}), setter=boom)
    assert rc == 1
    assert "already tracked" in err
    assert "tok" not in err


def test_known_fields_covers_every_provider():
    fields = save_credentials.known_fields()
    for expected in ("OURA_ACCESS_TOKEN", "EARLY_API_KEY", "EARLY_API_SECRET",
                     "TOGGL_API_TOKEN", "STRAVA_CLIENT_ID", "STRAVA_CLIENT_SECRET",
                     "STRAVA_REFRESH_TOKEN"):
        assert expected in fields
