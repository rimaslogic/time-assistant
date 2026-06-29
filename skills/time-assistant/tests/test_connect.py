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
