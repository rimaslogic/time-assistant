import json
import os
from pathlib import Path
import pytest
from engine import memory


@pytest.fixture
def fake_tenants(tmp_path, monkeypatch):
    store = tmp_path / "acme-store"
    store.mkdir()
    tenants = {"tenants": {"acme": {"store_path": str(store)}}}
    tfile = tmp_path / "tenants.json"
    tfile.write_text(json.dumps(tenants))
    monkeypatch.setattr(memory, "TENANTS_FILE", tfile)
    monkeypatch.setattr(memory, "USER_REGISTRY_FILE", tmp_path / "no-user-registry.json")
    monkeypatch.delenv("TIME_ASSISTANT_TENANT", raising=False)
    monkeypatch.delenv("MEMORY_REPO_PATH", raising=False)
    return store


def test_resolve_store_explicit(fake_tenants):
    assert memory.resolve_store("acme") == fake_tenants


def test_resolve_store_from_env(fake_tenants, monkeypatch):
    monkeypatch.setenv("TIME_ASSISTANT_TENANT", "acme")
    assert memory.resolve_store() == fake_tenants


def test_rimas_falls_back_to_memory_repo_path(tmp_path, monkeypatch):
    monkeypatch.setattr(memory, "TENANTS_FILE", tmp_path / "no-such.json")
    repo = tmp_path / "rimas-repo"
    repo.mkdir()
    monkeypatch.setenv("MEMORY_REPO_PATH", str(repo))
    assert memory.resolve_store("rimas") == repo


def test_read_write_json_roundtrip(fake_tenants):
    memory.write_json("x.json", {"a": 1}, tenant_id="acme")
    assert memory.read_json("x.json", tenant_id="acme") == {"a": 1}


def test_read_missing_returns_default(fake_tenants):
    assert memory.read_json("missing.json", default=[], tenant_id="acme") == []


def test_list_tenants(fake_tenants):
    assert memory.list_tenants() == ["acme"]


# ---------- New tests ----------

def test_resolve_store_single_tenant_autopick(fake_tenants, monkeypatch):
    """With exactly one tenant and no hint, resolve_store() picks it automatically."""
    monkeypatch.delenv("TIME_ASSISTANT_TENANT", raising=False)
    monkeypatch.delenv("MEMORY_REPO_PATH", raising=False)
    assert memory.resolve_store() == fake_tenants


def test_resolve_store_unresolvable_raises(tmp_path, monkeypatch):
    """Unknown tenant with no MEMORY_REPO_PATH fallback raises RuntimeError."""
    monkeypatch.setattr(memory, "TENANTS_FILE", tmp_path / "no-such.json")
    monkeypatch.delenv("MEMORY_REPO_PATH", raising=False)
    monkeypatch.delenv("TIME_ASSISTANT_TENANT", raising=False)
    with pytest.raises(RuntimeError):
        memory.resolve_store("ghost")


def test_write_json_is_sorted_with_trailing_newline(fake_tenants):
    """write_json must produce sorted keys and a trailing newline."""
    memory.write_json("sorted.json", {"z": 1, "a": 2, "m": 3}, tenant_id="acme")
    raw = (fake_tenants / "sorted.json").read_text(encoding="utf-8")
    parsed = json.loads(raw)
    assert list(parsed.keys()) == ["a", "m", "z"]
    assert raw.endswith("\n")


def test_read_write_append_text_roundtrip(fake_tenants):
    """write_text + read_text roundtrip; append_text extends the file."""
    memory.write_text("note.md", "hello\n", tenant_id="acme")
    assert memory.read_text("note.md", tenant_id="acme") == "hello\n"
    memory.append_text("note.md", "world\n", tenant_id="acme")
    assert memory.read_text("note.md", tenant_id="acme") == "hello\nworld\n"


def test_load_and_save_rules(fake_tenants):
    """save_rules persists; load_rules retrieves the list."""
    rules = [{"id": "r1", "label": "Focus block"}, {"id": "r2", "label": "Deep work"}]
    memory.save_rules(rules, tenant_id="acme")
    assert memory.load_rules(tenant_id="acme") == rules


def test_append_daily_score(fake_tenants):
    """append_daily_score adds the row to daily_scores.json["scores"]."""
    row = {"date": "2026-06-01", "hvt_ratio": 0.8}
    memory.append_daily_score(row, tenant_id="acme")
    scores = memory.read_json("daily_scores.json", tenant_id="acme")["scores"]
    assert row in scores


def test_pending_corrections(fake_tenants):
    """pending_corrections returns only unchecked '[ ]' lines."""
    content = "[ ] todo one\n[x] done\nnot a task\n"
    memory.write_text("corrections_inbox.md", content, tenant_id="acme")
    result = memory.pending_corrections(tenant_id="acme")
    assert result == ["[ ] todo one"]


def test_rimas_unaffected_when_no_user_registry(tmp_path, monkeypatch):
    monkeypatch.setattr(memory, "USER_REGISTRY_FILE", tmp_path / "absent.json")
    monkeypatch.setattr(memory, "TENANTS_FILE", tmp_path / "absent2.json")
    repo = tmp_path / "rimas-repo"; repo.mkdir()
    monkeypatch.setenv("MEMORY_REPO_PATH", str(repo))
    monkeypatch.delenv("TIME_ASSISTANT_TENANT", raising=False)
    assert memory.resolve_store("rimas") == repo
