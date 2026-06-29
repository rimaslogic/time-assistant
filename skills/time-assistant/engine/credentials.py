"""Credential provider abstraction. The laptop Bitwarden flow is one provider,
not a hardcoded assumption. Default provider = env (works on the VPS / CI)."""
import json
import os
import stat
import subprocess
import sys

KEYCHAIN_SERVICE = "TimeAssistant"
SECRETS_FILENAME = "secrets.json"


def _from_env(name: str) -> str:
    if name not in os.environ:
        raise KeyError(f"Secret {name!r} not set in environment")
    return os.environ[name]


def _from_keychain(name: str) -> str:
    user = os.environ.get("USER", "")
    out = subprocess.run(
        ["security", "find-generic-password", "-a", user, "-s", name, "-w"],
        capture_output=True, text=True,
    )
    if out.returncode != 0:
        raise KeyError(f"Keychain item {name!r} not found")
    return out.stdout.strip()


def _from_bitwarden(name: str) -> str:
    session = os.environ.get("BW_SESSION")
    if not session:
        raise RuntimeError("BW_SESSION not set; unlock the vault before fetching secrets")
    out = subprocess.run(
        ["bw", "get", "password", name, "--session", session],
        capture_output=True, text=True,
    )
    if out.returncode != 0:
        raise KeyError(f"Vault item {name!r} not found")
    return out.stdout.strip()


def _use_keychain() -> bool:
    return sys.platform == "darwin"


def _keystore_dir():
    from engine.paths import user_config_dir
    return user_config_dir()


def _secrets_file():
    return _keystore_dir() / SECRETS_FILENAME


def _file_get(name: str) -> str:
    fp = _secrets_file()
    data = json.loads(fp.read_text(encoding="utf-8")) if fp.exists() else {}
    if name not in data:
        raise KeyError(f"Secret {name!r} not found in local secret file")
    return data[name]


def _file_set(name: str, value: str) -> None:
    fp = _secrets_file()
    fp.parent.mkdir(parents=True, exist_ok=True)
    data = json.loads(fp.read_text(encoding="utf-8")) if fp.exists() else {}
    data[name] = value
    payload = json.dumps(data, indent=2)
    try:
        fd = os.open(str(fp), os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(payload)
    except OSError:
        fp.write_text(payload, encoding="utf-8")
    try:
        os.chmod(fp, stat.S_IRUSR | stat.S_IWUSR)  # belt-and-suspenders (no-op on Windows)
    except OSError:
        pass


def _keystore_get(name: str) -> str:
    if not _use_keychain():
        return _file_get(name)
    user = os.environ.get("USER", "")
    out = subprocess.run(
        ["security", "find-generic-password", "-a", user, "-s",
         f"{KEYCHAIN_SERVICE}:{name}", "-w"],
        capture_output=True, text=True,
    )
    if out.returncode != 0:
        raise KeyError(f"Keychain item {name!r} not found")
    return out.stdout.strip()


def _keystore_set(name: str, value: str) -> None:
    if not _use_keychain():
        _file_set(name, value)
        return
    user = os.environ.get("USER", "")
    out = subprocess.run(
        ["security", "add-generic-password", "-U", "-a", user, "-s",
         f"{KEYCHAIN_SERVICE}:{name}", "-w", value],
        capture_output=True, text=True,
    )
    if out.returncode != 0:
        raise RuntimeError(f"Keychain write failed for {name!r}")


_SETTERS = {"keystore": _keystore_set}


def set_secret(name: str, value: str, provider: str | None = None) -> None:
    p = provider or os.environ.get("TIME_ASSISTANT_CRED_PROVIDER", "keystore")
    if p not in _SETTERS:
        raise ValueError(f"Provider {p!r} does not support storing secrets")
    _SETTERS[p](name, value)


_PROVIDERS = {"env": _from_env, "keychain": _from_keychain,
              "bitwarden": _from_bitwarden, "keystore": _keystore_get}


def _resolve_provider(provider):
    name = provider or os.environ.get("TIME_ASSISTANT_CRED_PROVIDER", "env")
    if name not in _PROVIDERS:
        raise ValueError(f"Unknown credential provider: {name}")
    return _PROVIDERS[name]


def get_secret(name: str, provider: str | None = None) -> str:
    return _resolve_provider(provider)(name)


def get_secrets(names, provider: str | None = None) -> dict:
    fn = _resolve_provider(provider)
    return {n: fn(n) for n in names}
