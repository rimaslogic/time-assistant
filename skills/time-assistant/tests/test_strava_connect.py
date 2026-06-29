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
