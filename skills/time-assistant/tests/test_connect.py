import pytest
from onboarding import connect


def test_fields_and_pages_present():
    assert connect.PROVIDER_FIELDS["timeular"] == ["EARLY_API_KEY", "EARLY_API_SECRET"]
    assert connect.PROVIDER_PAGES["oura"].startswith("https://")


def test_validate_oura_true_false():
    assert connect.validate("oura", {"OURA_ACCESS_TOKEN": "good"},
                            http=lambda pid, vals: vals["OURA_ACCESS_TOKEN"] == "good") is True
    assert connect.validate("oura", {"OURA_ACCESS_TOKEN": "bad"},
                            http=lambda pid, vals: False) is False


def test_store_writes_each_field_via_keystore():
    calls = []
    connect.store("timeular", {"EARLY_API_KEY": "k", "EARLY_API_SECRET": "s"},
                  setter=lambda n, v, provider=None: calls.append((n, v, provider)))
    assert ("EARLY_API_KEY", "k", "keystore") in calls
    assert ("EARLY_API_SECRET", "s", "keystore") in calls


def test_toggl_provider_fields_present():
    assert connect.PROVIDER_FIELDS["toggl"] == ["TOGGL_API_TOKEN"]
    assert connect.PROVIDER_PAGES["toggl"].startswith("https://")


# ── resolve_toggl_token ───────────────────────────────────────────────────────

def test_resolve_toggl_token_classic_via_basic():
    """Classic 32-char api_token validates via Basic auth and is returned."""
    def fake_http(scheme, token):
        if scheme == "Basic" and token == "classic32":
            return {"api_token": "classic32"}
        return None

    result = connect.resolve_toggl_token("classic32", http=fake_http)
    assert result == "classic32"


def test_resolve_toggl_token_sk_falls_back_to_bearer():
    """toggl_sk_ token: Basic fails, Bearer succeeds, returns resolved api_token."""
    def fake_http(scheme, token):
        if scheme == "Basic":
            return None
        if scheme == "Bearer" and token == "toggl_sk_x":
            return {"api_token": "resolved-classic"}
        return None

    result = connect.resolve_toggl_token("toggl_sk_x", http=fake_http)
    assert result == "resolved-classic"


def test_resolve_toggl_token_bearer_no_api_token_field():
    """Bearer succeeds but response lacks api_token → pasted value returned."""
    def fake_http(scheme, token):
        if scheme == "Basic":
            return None
        if scheme == "Bearer":
            return {"id": 42, "email": "x@example.com"}  # no api_token field
        return None

    result = connect.resolve_toggl_token("toggl_sk_fallback", http=fake_http)
    assert result == "toggl_sk_fallback"


def test_resolve_toggl_token_strips_whitespace():
    """A pasted token with a trailing newline/space still resolves."""
    seen = {}

    def fake_http(scheme, token):
        seen["token"] = token
        if scheme == "Basic":
            return {"api_token": token}
        return None

    result = connect.resolve_toggl_token("  classic32\n", http=fake_http)
    assert result == "classic32"
    assert seen["token"] == "classic32"  # http received the stripped value


def test_resolve_toggl_token_invalid_raises():
    """All schemes fail → RuntimeError."""
    def fake_http(scheme, token):
        return None

    with pytest.raises(RuntimeError, match="Toggl token did not authenticate"):
        connect.resolve_toggl_token("bad-token", http=fake_http)


def test_resolve_toggl_token_http_exception_is_treated_as_failure():
    """http raising an exception counts as scheme failure, tries next."""
    calls = []

    def fake_http(scheme, token):
        calls.append(scheme)
        if scheme == "Basic":
            raise ConnectionError("network down")
        return {"api_token": "ok"}

    result = connect.resolve_toggl_token("some_token", http=fake_http)
    assert result == "ok"
    assert calls == ["Basic", "Bearer"]


# ── validate / store (toggl, new interface) ───────────────────────────────────

def test_validate_toggl_true_via_resolve():
    """validate('toggl', ...) → True when resolve_toggl_token succeeds."""
    def fake_http(scheme, token):
        if scheme == "Basic":
            return {"api_token": token}
        return None

    assert connect.validate("toggl", {"TOGGL_API_TOKEN": "good"}, http=fake_http) is True


def test_validate_toggl_false_via_resolve():
    """validate('toggl', ...) → False when all schemes fail."""
    def fake_http(scheme, token):
        return None

    assert connect.validate("toggl", {"TOGGL_API_TOKEN": "bad"}, http=fake_http) is False


def test_store_toggl_writes_resolved_classic_token():
    """store('toggl', ...) resolves the token via /me and stores the classic api_token."""
    def fake_http(scheme, token):
        if scheme == "Basic":
            return None  # sk token → Basic fails
        if scheme == "Bearer" and token == "toggl_sk_input":
            return {"api_token": "classic-resolved"}
        return None

    calls = []
    connect.store(
        "toggl",
        {"TOGGL_API_TOKEN": "toggl_sk_input"},
        setter=lambda n, v, provider=None: calls.append((n, v, provider)),
        http=fake_http,
    )

    assert ("TOGGL_API_TOKEN", "classic-resolved", "keystore") in calls


def test_diagnose_toggl_returns_reason_on_failure():
    """diagnose('toggl', ...) surfaces the resolve error string when auth fails."""
    def fake_http(scheme, token):
        return None  # all schemes fail

    reason = connect.diagnose("toggl", {"TOGGL_API_TOKEN": "bad"}, http=fake_http)
    assert "did not authenticate" in reason


def test_diagnose_toggl_empty_on_success():
    def fake_http(scheme, token):
        return {"api_token": token} if scheme == "Basic" else None

    assert connect.diagnose("toggl", {"TOGGL_API_TOKEN": "good"}, http=fake_http) == ""


def test_diagnose_other_provider_reports_rejection():
    reason = connect.diagnose("oura", {"OURA_ACCESS_TOKEN": "bad"},
                              http=lambda pid, vals: False)
    assert reason  # non-empty reason string
    assert connect.diagnose("oura", {"OURA_ACCESS_TOKEN": "good"},
                            http=lambda pid, vals: True) == ""


def test_store_toggl_raises_if_token_invalid():
    """store('toggl', ...) raises RuntimeError if token fails all schemes."""
    def fake_http(scheme, token):
        return None

    with pytest.raises(RuntimeError):
        connect.store(
            "toggl",
            {"TOGGL_API_TOKEN": "invalid"},
            setter=lambda n, v, provider=None: None,
            http=fake_http,
        )
