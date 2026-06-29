"""Adapter contract base classes. See integrations/_contract.md."""
import json
import os
import subprocess
from abc import ABC, abstractmethod
from dataclasses import dataclass, asdict, field

KIND_TIME = "time"
KIND_BIOMETRIC = "biometric"
KIND_ACTIVITY = "activity"
KINDS = {KIND_TIME, KIND_BIOMETRIC, KIND_ACTIVITY}


@dataclass(eq=True)
class Manifest:
    id: str
    kind: str
    label: str
    auth_fields: list = field(default_factory=list)
    capabilities: list = field(default_factory=list)
    how_to_obtain: str = ""

    def __post_init__(self):
        if self.kind not in KINDS:
            raise ValueError(f"Invalid kind {self.kind!r}")

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "Manifest":
        return cls(id=d["id"], kind=d["kind"], label=d["label"],
                   auth_fields=list(d.get("auth_fields", [])),
                   capabilities=list(d.get("capabilities", [])),
                   how_to_obtain=d.get("how_to_obtain", ""))


class Adapter(ABC):
    manifest: Manifest = None

    def manifest_or_raise(self) -> Manifest:
        if self.manifest is None:
            raise NotImplementedError(f"{type(self).__name__} has no manifest")
        return self.manifest

    @abstractmethod
    def fetch(self, start: str, end: str) -> list: ...

    @abstractmethod
    def check_auth(self) -> bool: ...


def run_cli(cmd: list, env: dict | None = None):
    out = subprocess.run(cmd, capture_output=True, text=True, env=env)
    if out.returncode != 0:
        raise RuntimeError(f"CLI failed ({out.returncode}): {' '.join(cmd)}\n{out.stderr}")
    return json.loads(out.stdout)


from engine import credentials  # safe: engine never imports integrations, so no cycle


class CliAdapter(Adapter):
    """Base for adapters that shell out to a standalone skill CLI.

    Subclasses set class attrs CLI_PATH and manifest, and implement
    fetch() / check_auth().
    """
    CLI_PATH: str = ""

    def __init__(self, cli_runner=run_cli, cli_path=None, secrets=None):
        self._run = cli_runner
        self._cli = cli_path or self.CLI_PATH
        self._secrets = secrets

    def _env(self) -> dict:
        secrets = self._secrets or credentials.get_secrets(self.manifest.auth_fields)
        return {**os.environ, **secrets}
