import json
from integrations import registry
from integrations.base import Adapter


def test_known_adapters_present():
    assert set(["timeular", "oura", "strava"]).issubset(registry.ADAPTERS.keys())


def test_get_adapter_returns_instance():
    a = registry.get_adapter("oura")
    assert isinstance(a, Adapter)
    assert a.manifest.id == "oura"


def test_get_adapter_unknown_raises():
    import pytest
    with pytest.raises(KeyError):
        registry.get_adapter("nope")


def test_available_lists_manifests():
    av = {m["id"]: m for m in registry.available()}
    assert av["strava"]["kind"] == "activity"
    assert "auth_fields" in av["timeular"]


def test_emit_registry_writes_json(tmp_path):
    out = tmp_path / "registry.json"
    registry.emit_registry(out)
    data = json.loads(out.read_text())
    assert {"timeular", "oura", "strava"}.issubset({m["id"] for m in data["integrations"]})
