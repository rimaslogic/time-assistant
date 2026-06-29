"""Tenant configuration + scoring framework loading.

A tenant's config.json may reference a named profile (profiles/<name>.json)
and override any framework field inline. The engine reads everything from here;
no scoring constants live in code.
"""
import json
from dataclasses import dataclass, field
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parent.parent
PROFILES_DIR = SKILL_ROOT / "profiles"


@dataclass
class Framework:
    hvt_categories: set
    lvt_categories: set
    hvt_ratio_target: float
    lvt_cap: float
    weights: dict

    def label_for(self, category: str) -> str:
        if category in self.hvt_categories:
            return "HVT"
        if category in self.lvt_categories:
            return "LVT"
        return ""

    @classmethod
    def from_dict(cls, d: dict) -> "Framework":
        return cls(
            hvt_categories=set(d["hvt_categories"]),
            lvt_categories=set(d["lvt_categories"]),
            hvt_ratio_target=float(d["hvt_ratio_target"]),
            lvt_cap=float(d["lvt_cap"]),
            weights=dict(d["weights"]),
        )


def load_profile(name: str) -> dict:
    fp = PROFILES_DIR / f"{name}.json"
    if not fp.exists():
        raise FileNotFoundError(f"Profile not found: {fp}")
    return json.loads(fp.read_text(encoding="utf-8"))


def _merge_framework(base: dict, override: dict) -> dict:
    out = dict(base)
    for k, v in (override or {}).items():
        if k == "weights" and isinstance(v, dict):
            out["weights"] = {**base.get("weights", {}), **v}
        else:
            out[k] = v
    return out


DEFAULT_FRAMEWORK = Framework.from_dict(load_profile("knowledge-worker")["framework"])


@dataclass
class TenantConfig:
    tenant_id: str
    name: str
    timezone: str
    working_days: list
    framework: Framework
    integrations: list = field(default_factory=list)
    modules: list = field(default_factory=list)
    attribution: dict = field(default_factory=dict)
    raw: dict = field(default_factory=dict)
    cred_provider: str | None = None


def load_tenant_config(store_path: Path) -> TenantConfig:
    store_path = Path(store_path)
    fp = store_path / "config.json"
    if not fp.exists():
        raise FileNotFoundError(f"Tenant config not found: {fp}")
    cfg = json.loads(fp.read_text(encoding="utf-8"))

    profile_name = cfg.get("profile", "knowledge-worker")
    profile = load_profile(profile_name)
    fw_dict = _merge_framework(profile["framework"], cfg.get("framework", {}))
    modules = cfg.get("modules", profile.get("modules", []))

    user = cfg.get("user", {})
    return TenantConfig(
        tenant_id=cfg["tenant_id"],
        name=user.get("name", ""),
        timezone=user.get("timezone", "UTC"),
        working_days=user.get("working_days", ["MO", "TU", "WE", "TH", "FR"]),
        framework=Framework.from_dict(fw_dict),
        integrations=cfg.get("integrations", []),
        modules=modules,
        attribution=cfg.get("attribution", {}),
        raw=cfg,
        cred_provider=cfg.get("cred_provider"),
    )
