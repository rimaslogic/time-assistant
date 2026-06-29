"""Tenant onboarding: build + validate a config, write it into a tenant store,
register the tenant locally. Cloning the template repo is a documented git step
(see SETUP.md); this module handles config assembly so it is unit-testable."""
import argparse
import json
from pathlib import Path

from engine.config import PROFILES_DIR
from integrations.registry import ADAPTERS

SKILL_ROOT = Path(__file__).resolve().parent.parent


def build_config(tenant_id, name, timezone, working_days, profile, integrations) -> dict:
    return {
        "tenant_id": tenant_id,
        "profile": profile,
        "user": {"name": name, "timezone": timezone, "working_days": working_days},
        "framework": {},
        "integrations": list(integrations),
        "modules": [],
        "attribution": {},
    }


def validate_config(cfg: dict) -> list:
    errs = []
    for key in ("tenant_id", "user"):
        if not cfg.get(key):
            errs.append(f"missing required key: {key}")
    if "user" in cfg:
        for key in ("name", "timezone"):
            if not cfg["user"].get(key):
                errs.append(f"missing user.{key}")
    profile = cfg.get("profile", "knowledge-worker")
    if not (PROFILES_DIR / f"{profile}.json").exists():
        errs.append(f"unknown profile: {profile}")
    for integ in cfg.get("integrations", []):
        if integ not in ADAPTERS:
            errs.append(f"unknown integration: {integ}")
    return errs


def write_tenant(cfg: dict, store_path) -> None:
    store = Path(store_path)
    store.mkdir(parents=True, exist_ok=True)
    (store / "config.json").write_text(json.dumps(cfg, indent=2, ensure_ascii=False),
                                       encoding="utf-8")


def register_tenant(tenant_id, store_path, github_repo, tenants_file) -> None:
    tfile = Path(tenants_file)
    data = json.loads(tfile.read_text()) if tfile.exists() else {"tenants": {}}
    data.setdefault("tenants", {})[tenant_id] = {
        "store_path": str(store_path), "github_repo": github_repo,
    }
    tfile.write_text(json.dumps(data, indent=2), encoding="utf-8")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--tenant", required=True)
    ap.add_argument("--name", required=True)
    ap.add_argument("--tz", required=True)
    ap.add_argument("--working-days", default="MO,TU,WE,TH,FR")
    ap.add_argument("--profile", default="knowledge-worker")
    ap.add_argument("--integrations", default="")
    ap.add_argument("--store", required=True)
    ap.add_argument("--repo", default="")
    a = ap.parse_args()
    integs = [s for s in a.integrations.split(",") if s]
    cfg = build_config(a.tenant, a.name, a.tz, a.working_days.split(","), a.profile, integs)
    errs = validate_config(cfg)
    if errs:
        raise SystemExit("Invalid config:\n  " + "\n  ".join(errs))
    write_tenant(cfg, a.store)
    register_tenant(a.tenant, a.store, a.repo, SKILL_ROOT / "tenants.json")
    print(f"Provisioned tenant {a.tenant} at {a.store}")
