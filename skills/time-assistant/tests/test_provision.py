import json
from onboarding import provision


def test_build_config_valid():
    cfg = provision.build_config(
        tenant_id="acme", name="Dana", timezone="America/New_York",
        working_days=["MO", "TU"], profile="knowledge-worker",
        integrations=["timeular", "oura"])
    assert cfg["tenant_id"] == "acme"
    assert cfg["user"]["name"] == "Dana"
    assert cfg["profile"] == "knowledge-worker"
    assert provision.validate_config(cfg) == []


def test_validate_rejects_unknown_profile():
    cfg = provision.build_config("a", "B", "UTC", ["MO"], "nope", [])
    errs = provision.validate_config(cfg)
    assert any("profile" in e for e in errs)


def test_validate_rejects_unknown_integration():
    cfg = provision.build_config("a", "B", "UTC", ["MO"], "knowledge-worker", ["fitbit"])
    errs = provision.validate_config(cfg)
    assert any("integration" in e for e in errs)


def test_write_and_register(tmp_path):
    store = tmp_path / "store"; store.mkdir()
    tfile = tmp_path / "tenants.json"
    cfg = provision.build_config("acme", "Dana", "UTC", ["MO"], "knowledge-worker", ["timeular"])
    provision.write_tenant(cfg, store)
    provision.register_tenant("acme", str(store), "org/acme-mem", tfile)
    assert json.loads((store / "config.json").read_text())["tenant_id"] == "acme"
    assert json.loads(tfile.read_text())["tenants"]["acme"]["store_path"] == str(store)
