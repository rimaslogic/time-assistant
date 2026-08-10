"""Credential provider abstraction. The laptop Bitwarden flow is one provider,
not a hardcoded assumption.

With no explicit provider, both reads and writes go through `keystore`: a
single 0600 JSON file in the tenant store. Reads fall back to the environment
and then to legacy locations, migrating whatever they find into the file.
Before this, writes defaulted to `keystore` while reads defaulted to `env`,
so stored tokens were invisible to the adapters."""
import json
import os
import stat
import subprocess

KEYCHAIN_SERVICE = "TimeAssistant"
CREDENTIALS_FILENAME = ".credentials.json"
LEGACY_SECRETS_FILENAME = "secrets.json"


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


def _store_dir():
    """The tenant store, or the per-OS config dir when no tenant resolves yet.

    resolve_store() raises during setup, before any tenant is registered."""
    try:
        from engine.memory import resolve_store
        return resolve_store()
    except Exception:
        from engine.paths import user_config_dir
        return user_config_dir()


def _credentials_file():
    return _store_dir() / CREDENTIALS_FILENAME


def _read_json(fp) -> dict:
    if not fp.exists():
        return {}
    try:
        data = json.loads(fp.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return data if isinstance(data, dict) else {}


def _write_secret_file(fp, data) -> None:
    fp.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(data, indent=2)
    fd = os.open(str(fp), os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        f.write(payload)
    try:
        os.chmod(fp, stat.S_IRUSR | stat.S_IWUSR)  # no-op on Windows
    except OSError:
        pass


def _file_get(name: str) -> str:
    data = _read_json(_credentials_file())
    if name not in data:
        raise KeyError(f"Secret {name!r} not found in {_credentials_file()}")
    return data[name]


def _ensure_store_ignored(store_dir) -> None:
    """Indirection so tests can stub the guard without importing subprocess."""
    from engine.store_guard import ensure_ignored
    ensure_ignored(store_dir)


def _file_set(name: str, value: str) -> None:
    fp = _credentials_file()
    _ensure_store_ignored(fp.parent)
    data = _read_json(fp)
    data[name] = value
    _write_secret_file(fp, data)


def _legacy_keychain_get(name: str) -> str:
    """Pre-2026-08 macOS Keychain location. Read-only; migrated on hit."""
    user = os.environ.get("USER", "")
    out = subprocess.run(
        ["security", "find-generic-password", "-a", user, "-s",
         f"{KEYCHAIN_SERVICE}:{name}", "-w"],
        capture_output=True, text=True,
    )
    if out.returncode != 0:
        raise KeyError(f"Keychain item {name!r} not found")
    return out.stdout.strip()


def _legacy_file_get(name: str) -> str:
    """Pre-2026-08 Linux/Windows file location. Read-only; migrated on hit."""
    from engine.paths import user_config_dir
    data = _read_json(user_config_dir() / LEGACY_SECRETS_FILENAME)
    if name not in data:
        raise KeyError(f"Secret {name!r} not found in legacy secrets file")
    return data[name]


def _chain_get(name: str) -> str:
    """Credentials file → environment → legacy locations (migrating on hit).

    Both legacy sources are tried on every platform: a missing `security`
    binary or a missing file is simply a miss, and a home directory moved
    between machines should not lose credentials to an OS guess."""
    try:
        return _file_get(name)
    except KeyError:
        pass
    if name in os.environ:
        return os.environ[name]
    for source in (_legacy_keychain_get, _legacy_file_get):
        try:
            value = source(name)
        except (KeyError, OSError):
            continue
        _file_set(name, value)
        return value
    raise KeyError(
        f"Secret {name!r} not found in {_credentials_file()}, the environment, "
        "or any legacy location"
    )


_SETTERS = {"keystore": _file_set}


def set_secret(name: str, value: str, provider: str | None = None) -> None:
    p = provider or os.environ.get("TIME_ASSISTANT_CRED_PROVIDER", "keystore")
    if p not in _SETTERS:
        raise ValueError(f"Provider {p!r} does not support storing secrets")
    _SETTERS[p](name, value)


_PROVIDERS = {"env": _from_env, "keychain": _from_keychain,
              "bitwarden": _from_bitwarden, "keystore": _chain_get}


def _resolve_provider(provider):
    name = provider or os.environ.get("TIME_ASSISTANT_CRED_PROVIDER", "keystore")
    if name not in _PROVIDERS:
        raise ValueError(f"Unknown credential provider: {name}")
    return _PROVIDERS[name]


def get_secret(name: str, provider: str | None = None) -> str:
    return _resolve_provider(provider)(name)


def get_secrets(names, provider: str | None = None) -> dict:
    fn = _resolve_provider(provider)
    return {n: fn(n) for n in names}
