import json
from pathlib import Path
from engine.config import (
    Framework, TenantConfig, load_profile, load_tenant_config, DEFAULT_FRAMEWORK,
)


def test_default_framework_matches_legacy():
    f = DEFAULT_FRAMEWORK
    assert f.hvt_categories == {"strategic", "product", "content", "learning", "bd"}
    assert f.lvt_categories == {"email", "meeting", "admin", "chat", "support", "context-switch"}
    assert f.hvt_ratio_target == 0.80
    assert f.lvt_cap == 0.20
    assert f.weights["hvt_pts"] == 60


def test_label_for():
    f = DEFAULT_FRAMEWORK
    assert f.label_for("strategic") == "HVT"
    assert f.label_for("email") == "LVT"
    assert f.label_for("unknown") == ""


def test_load_profile_reads_knowledge_worker():
    p = load_profile("knowledge-worker")
    assert "framework" in p


def test_load_tenant_config_with_profile_and_override(tmp_path):
    cfg = {
        "tenant_id": "acme",
        "profile": "knowledge-worker",
        "user": {"name": "Dana", "timezone": "America/New_York", "working_days": ["MO", "TU"]},
        "framework": {"hvt_ratio_target": 0.70},
        "integrations": ["timeular"],
        "modules": [],
        "attribution": {}
    }
    (tmp_path / "config.json").write_text(json.dumps(cfg))
    tc = load_tenant_config(tmp_path)
    assert tc.tenant_id == "acme"
    assert tc.name == "Dana"
    assert tc.timezone == "America/New_York"
    # profile supplies categories, config override changes the target:
    assert tc.framework.hvt_categories == {"strategic", "product", "content", "learning", "bd"}
    assert tc.framework.hvt_ratio_target == 0.70
    assert tc.integrations == ["timeular"]


def test_load_tenant_config_missing_file_raises(tmp_path):
    import pytest
    with pytest.raises(FileNotFoundError):
        load_tenant_config(tmp_path)


def test_cred_provider_loaded(tmp_path):
    import json
    from engine.config import load_tenant_config
    (tmp_path / "config.json").write_text(json.dumps(
        {"tenant_id": "me", "profile": "knowledge-worker",
         "user": {"name": "N", "timezone": "UTC"}, "cred_provider": "keystore"}))
    assert load_tenant_config(tmp_path).cred_provider == "keystore"


def test_cred_provider_defaults_none(tmp_path):
    import json
    from engine.config import load_tenant_config
    (tmp_path / "config.json").write_text(json.dumps(
        {"tenant_id": "me", "profile": "knowledge-worker",
         "user": {"name": "N", "timezone": "UTC"}}))
    assert load_tenant_config(tmp_path).cred_provider is None
