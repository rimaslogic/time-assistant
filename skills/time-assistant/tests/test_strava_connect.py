from onboarding import strava_connect as sc


def test_build_authorize_url():
    url = sc.build_authorize_url("12345", port=8721)
    assert url.startswith("https://www.strava.com/oauth/authorize?")
    assert "client_id=12345" in url
    assert "redirect_uri=http%3A%2F%2Flocalhost%3A8721%2F" in url
    assert "response_type=code" in url
    assert "activity%3Aread_all" in url


def test_exchange_code_returns_refresh_token():
    def fake_http(url, form):
        assert url == "https://www.strava.com/oauth/token"
        assert form["grant_type"] == "authorization_code"
        assert form["code"] == "THECODE"
        return {"refresh_token": "rt", "access_token": "at", "expires_at": 1}
    out = sc.exchange_code("id", "secret", "THECODE", http=fake_http)
    assert out["refresh_token"] == "rt"


def test_store_writes_three_secrets_via_keystore():
    calls = []
    sc.store("id", "secret", "rt", setter=lambda n, v, provider=None: calls.append((n, v, provider)))
    names = {c[0]: c for c in calls}
    assert names["STRAVA_CLIENT_ID"] == ("STRAVA_CLIENT_ID", "id", "keystore")
    assert names["STRAVA_CLIENT_SECRET"] == ("STRAVA_CLIENT_SECRET", "secret", "keystore")
    assert names["STRAVA_REFRESH_TOKEN"] == ("STRAVA_REFRESH_TOKEN", "rt", "keystore")


def test_capture_code_with_injected_server():
    # Simulate the loopback: a fake server whose handle() yields a code.
    class FakeServer:
        def __init__(self): self.captured = "ABC123"
        def serve_until_code(self, timeout): return self.captured
    out = sc.capture_code(server_factory=lambda port: FakeServer())
    assert out == "ABC123"


def test_capture_code_propagates_access_denied():
    class DeniedServer:
        def __init__(self, port): pass
        def serve_until_code(self, timeout):
            raise RuntimeError("Strava authorization failed: access_denied")

    import pytest
    with pytest.raises(RuntimeError, match="Strava authorization failed: access_denied"):
        sc.capture_code(server_factory=DeniedServer)


def test_main_orchestrates_full_flow():
    """main() reads id/secret via hidden prompts, opens auth URL, captures
    code, exchanges it, and stores — secrets are never returned or printed."""
    stored = {}
    messages = []
    opened_urls = []
    getpass_values = iter(["myclientid", "myclientsecret"])

    def fake_getpass(prompt):
        return next(getpass_values)

    def fake_opener(url):
        opened_urls.append(url)

    def fake_capture():
        return "OAUTH_CODE"

    def fake_exchange(client_id, client_secret, code):
        assert code == "OAUTH_CODE"
        return {"refresh_token": "rt123", "access_token": "at123"}

    def fake_store(client_id, client_secret, refresh_token):
        stored["client_id"] = client_id
        stored["client_secret"] = client_secret
        stored["refresh_token"] = refresh_token

    rc = sc.main(
        getpass_fn=fake_getpass,
        opener=fake_opener,
        capture=fake_capture,
        exchange=fake_exchange,
        store_fn=fake_store,
        out=messages.append,
    )

    assert rc == 0
    assert stored == {
        "client_id": "myclientid",
        "client_secret": "myclientsecret",
        "refresh_token": "rt123",
    }
    # At least one URL was opened (the auth URL)
    assert len(opened_urls) == 1
    assert "strava.com" in opened_urls[0]
    # Success message must not contain any secret value
    full_output = " ".join(messages)
    assert "myclientid" not in full_output
    assert "myclientsecret" not in full_output
    assert "rt123" not in full_output
