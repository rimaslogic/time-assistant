from onboarding import connect


def test_every_provider_has_fields_and_a_page():
    assert set(connect.PROVIDER_FIELDS) == set(connect.PROVIDER_PAGES)
    for provider, fields in connect.PROVIDER_FIELDS.items():
        assert fields, f"{provider} has no auth fields"
        assert connect.PROVIDER_PAGES[provider].startswith("https://")


def test_expected_field_names():
    assert connect.PROVIDER_FIELDS["oura"] == ["OURA_ACCESS_TOKEN"]
    assert connect.PROVIDER_FIELDS["timeular"] == ["EARLY_API_KEY", "EARLY_API_SECRET"]
    assert connect.PROVIDER_FIELDS["toggl"] == ["TOGGL_API_TOKEN"]
    assert connect.PROVIDER_FIELDS["strava"] == [
        "STRAVA_CLIENT_ID", "STRAVA_CLIENT_SECRET", "STRAVA_REFRESH_TOKEN"]


def test_no_network_helpers_remain():
    """Validation was removed by design — guard against it creeping back."""
    for gone in ("validate", "diagnose", "store", "resolve_toggl_token"):
        assert not hasattr(connect, gone), f"connect.{gone} should be deleted"
