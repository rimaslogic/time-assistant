"""Adapter registry. The single place that knows which integrations exist.
registry.json is generated from this and read by onboarding."""
import argparse
import json
from pathlib import Path

from integrations.base import Adapter
from integrations.timeular_adapter import TimeularAdapter
from integrations.oura_adapter import OuraAdapter
from integrations.strava_adapter import StravaAdapter
from integrations.toggl_adapter import TogglAdapter

ADAPTERS = {
    "timeular": TimeularAdapter,
    "oura": OuraAdapter,
    "strava": StravaAdapter,
    "toggl": TogglAdapter,
}

REGISTRY_JSON = Path(__file__).resolve().parent / "registry.json"


def get_adapter(adapter_id: str) -> Adapter:
    if adapter_id not in ADAPTERS:
        raise KeyError(f"Unknown integration: {adapter_id}")
    return ADAPTERS[adapter_id]()


def available() -> list:
    return [cls.manifest.to_dict() for cls in ADAPTERS.values()]


def emit_registry(path=None) -> None:
    path = Path(path) if path else REGISTRY_JSON
    path.write_text(json.dumps({"integrations": available()}, indent=2), encoding="utf-8")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--emit", action="store_true")
    ap.add_argument("--list", action="store_true")
    args = ap.parse_args()
    if args.emit:
        emit_registry()
        print(f"Wrote {REGISTRY_JSON}")
    if args.list:
        for m in available():
            print(f"{m['id']:10} {m['kind']:10} {m['label']}")
