"""Tenant-aware store router. Each tenant maps to a local git checkout
(one repo per customer). Rimas (tenant 0) falls back to MEMORY_REPO_PATH so
his existing setup keeps working with no tenants.json.

This module is a strict superset of the legacy scripts/memory.py — every
text helper and domain helper is here, made tenant-aware via a trailing
``tenant_id`` keyword argument."""
import json
import os
import subprocess
from pathlib import Path
from typing import Any

SKILL_ROOT = Path(__file__).resolve().parent.parent
TENANTS_FILE = SKILL_ROOT / "tenants.json"


def _user_registry_default() -> Path:
    from engine.paths import user_config_dir
    return user_config_dir() / "tenants.json"


USER_REGISTRY_FILE = _user_registry_default()


def _registry_file() -> Path:
    if Path(USER_REGISTRY_FILE).exists():
        return Path(USER_REGISTRY_FILE)
    return TENANTS_FILE


def _load_tenants() -> dict:
    fp = _registry_file()
    if not fp.exists():
        return {}
    return json.loads(fp.read_text(encoding="utf-8")).get("tenants", {})


def list_tenants() -> list:
    return list(_load_tenants().keys())


def _expand(p: str) -> Path:
    return Path(os.path.expanduser(p))


def resolve_store(tenant_id: str | None = None) -> Path:
    tenants = _load_tenants()
    tid = tenant_id or os.environ.get("TIME_ASSISTANT_TENANT")
    if not tid:
        if len(tenants) == 1:
            tid = next(iter(tenants))
        else:
            tid = "rimas"  # tenant 0 default

    if tid in tenants:
        return _expand(tenants[tid]["store_path"])

    if tid == "rimas":
        legacy = os.environ.get("MEMORY_REPO_PATH")
        if legacy:
            p = _expand(legacy)
            if p.exists():
                return p
    raise RuntimeError(
        f"Cannot resolve store for tenant {tid!r}: not in tenants.json and no "
        "MEMORY_REPO_PATH fallback."
    )


# ---------- Low-level I/O helpers ----------

def read_json(relative: str, default: Any = None, *, tenant_id: str | None = None) -> Any:
    fp = resolve_store(tenant_id) / relative
    if not fp.exists():
        return default if default is not None else {}
    return json.loads(fp.read_text(encoding="utf-8"))


def write_json(relative: str, data: Any, commit_message: str | None = None,
               *, tenant_id: str | None = None) -> None:
    store = resolve_store(tenant_id)
    fp = store / relative
    fp.parent.mkdir(parents=True, exist_ok=True)
    with fp.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False, sort_keys=True)
        f.write("\n")
    if commit_message:
        _commit(str(fp), commit_message, tenant_id=tenant_id)


def read_text(relative: str, default: str = "", *, tenant_id: str | None = None) -> str:
    fp = resolve_store(tenant_id) / relative
    if not fp.exists():
        return default
    return fp.read_text(encoding="utf-8")


def write_text(relative: str, content: str, commit_message: str | None = None,
               *, tenant_id: str | None = None) -> None:
    store = resolve_store(tenant_id)
    fp = store / relative
    fp.parent.mkdir(parents=True, exist_ok=True)
    fp.write_text(content, encoding="utf-8")
    if commit_message:
        _commit(str(fp), commit_message, tenant_id=tenant_id)


def append_text(relative: str, content: str, commit_message: str | None = None,
                *, tenant_id: str | None = None) -> None:
    store = resolve_store(tenant_id)
    fp = store / relative
    fp.parent.mkdir(parents=True, exist_ok=True)
    with fp.open("a", encoding="utf-8") as f:
        f.write(content)
    if commit_message:
        _commit(str(fp), commit_message, tenant_id=tenant_id)


def _commit(path: str, message: str, *, tenant_id: str | None = None) -> None:
    """Stage + commit + push. Fails silently if git is not configured."""
    cwd = str(resolve_store(tenant_id))
    try:
        subprocess.run(["git", "add", path], cwd=cwd, check=True, capture_output=True)
        # Only commit if there are staged changes
        result = subprocess.run(
            ["git", "diff", "--cached", "--quiet"], cwd=cwd, capture_output=True
        )
        if result.returncode == 0:
            return  # nothing to commit
        subprocess.run(
            ["git", "commit", "-m", message], cwd=cwd, check=True, capture_output=True
        )
        subprocess.run(["git", "push"], cwd=cwd, check=False, capture_output=True)
    except subprocess.CalledProcessError as e:
        # Don't block the skill on git failures — the file write succeeded.
        print(f"[memory] git operation failed: {e}")


# ---------- Domain-specific helpers ----------

def load_rules(*, tenant_id: str | None = None) -> list:
    data = read_json("rules.json", default={"rules": []}, tenant_id=tenant_id)
    return data.get("rules", [])


def save_rules(rules: list, commit_message: str | None = None,
               *, tenant_id: str | None = None) -> None:
    write_json("rules.json", {"rules": rules}, commit_message, tenant_id=tenant_id)


def append_daily_score(row: dict, *, tenant_id: str | None = None) -> None:
    data = read_json("daily_scores.json", default={"scores": []}, tenant_id=tenant_id)
    data.setdefault("scores", []).append(row)
    write_json(
        "daily_scores.json",
        data,
        commit_message=f"score {row.get('date', '?')}: {row.get('hvt_ratio', '?')} HVT",
        tenant_id=tenant_id,
    )


def pending_corrections(*, tenant_id: str | None = None) -> list[str]:
    """Parse corrections_inbox.md — return lines starting with '[ ]'."""
    text = read_text("corrections_inbox.md", tenant_id=tenant_id)
    return [
        line.strip() for line in text.splitlines()
        if line.strip().startswith("[ ]")
    ]
