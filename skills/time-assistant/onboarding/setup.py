"""Single-user store provisioning + resumable onboarding state. OS specifics
come from engine.paths; everything else is plain file work."""
import json
import shutil
import subprocess
from pathlib import Path

from engine import paths
from onboarding import provision

TEMPLATE_DIR = Path(__file__).resolve().parent / "template"
ONBOARDING_STEPS = ["identity", "framework", "store", "calendar",
                    "enrichments", "rules", "first_brief"]


def _config_path(store_dir) -> Path:
    return Path(store_dir) / "config.json"


def setup(name, timezone, working_days, profile, *, store_dir=None, config_dir=None,
          modules=None, tenant_id="me", seed_from=TEMPLATE_DIR, git_init=True,
          runner=subprocess.run) -> Path:
    store_dir = Path(store_dir) if store_dir else paths.default_data_dir()
    config_dir = Path(config_dir) if config_dir else paths.user_config_dir()
    store_dir.mkdir(parents=True, exist_ok=True)
    config_dir.mkdir(parents=True, exist_ok=True)

    if Path(seed_from).exists():
        for src in Path(seed_from).iterdir():
            if src.is_file() and src.name != "config.json":
                dst = store_dir / src.name
                if not dst.exists():
                    shutil.copy2(src, dst)

    cfg = provision.build_config(tenant_id, name, timezone, working_days,
                                 profile, [])
    cfg["cred_provider"] = "keystore"
    cfg["modules"] = modules or []
    cfg["onboarding"] = {"completed_steps": []}
    provision.write_tenant(cfg, store_dir)

    if git_init:
        try:
            runner(["git", "init"], cwd=str(store_dir), capture_output=True)
        except Exception:
            pass

    provision.register_tenant(tenant_id, str(store_dir), "",
                              config_dir / "tenants.json")
    return store_dir


def load_onboarding_state(store_dir) -> dict:
    fp = _config_path(store_dir)
    if not fp.exists():
        return {"completed_steps": []}
    return json.loads(fp.read_text(encoding="utf-8")).get(
        "onboarding", {"completed_steps": []})


def mark_step_done(store_dir, step) -> None:
    fp = _config_path(store_dir)
    if not fp.exists():
        return  # nothing to persist until the store step creates config.json
    cfg = json.loads(fp.read_text(encoding="utf-8"))
    ob = cfg.setdefault("onboarding", {"completed_steps": []})
    if step not in ob["completed_steps"]:
        ob["completed_steps"].append(step)
    fp.write_text(json.dumps(cfg, indent=2, ensure_ascii=False), encoding="utf-8")


def next_step(store_dir, steps=ONBOARDING_STEPS):
    done = set(load_onboarding_state(store_dir)["completed_steps"])
    for s in steps:
        if s not in done:
            return s
    return None
