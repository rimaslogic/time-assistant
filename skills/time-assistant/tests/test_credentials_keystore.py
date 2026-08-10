import json
import os
import stat
import pytest
from engine import credentials


# Every credential name these tests touch. A developer machine may have real
# values for some of them injected into the environment by a secret loader, and
# chain step 2 would return those instead of what the test set up — so the
# fixture clears them all.
TOUCHED = (
    "OURA_ACCESS_TOKEN", "EARLY_API_KEY", "EARLY_API_SECRET", "TOGGL_API_TOKEN",
    "STRAVA_CLIENT_ID", "STRAVA_CLIENT_SECRET", "STRAVA_REFRESH_TOKEN",
    "X", "NOPE",
)


@pytest.fixture
def store(tmp_path, monkeypatch):
    """Point the credentials file at a temp dir and stub out every legacy source."""
    monkeypatch.setattr(credentials, "_store_dir", lambda: tmp_path)
    monkeypatch.setattr(credentials, "_legacy_keychain_get",
                        lambda name: (_ for _ in ()).throw(KeyError(name)))
    monkeypatch.setattr(credentials, "_legacy_file_get",
                        lambda name: (_ for _ in ()).throw(KeyError(name)))
    monkeypatch.delenv("TIME_ASSISTANT_CRED_PROVIDER", raising=False)
    for name in TOUCHED:
        monkeypatch.delenv(name, raising=False)
    return tmp_path


def test_set_writes_dotfile_and_get_reads_it(store):
    credentials.set_secret("OURA_ACCESS_TOKEN", "tok")
    data = json.loads((store / ".credentials.json").read_text())
    assert data["OURA_ACCESS_TOKEN"] == "tok"
    assert credentials.get_secret("OURA_ACCESS_TOKEN") == "tok"


def test_file_is_permission_locked(store):
    credentials.set_secret("X", "y")
    if os.name == "posix":
        mode = stat.S_IMODE(os.stat(store / ".credentials.json").st_mode)
        assert mode == 0o600


def test_second_write_preserves_first(store):
    credentials.set_secret("EARLY_API_KEY", "k")
    credentials.set_secret("EARLY_API_SECRET", "s")
    data = json.loads((store / ".credentials.json").read_text())
    assert data == {"EARLY_API_KEY": "k", "EARLY_API_SECRET": "s"}


def test_chain_falls_back_to_environment(store, monkeypatch):
    monkeypatch.setenv("STRAVA_REFRESH_TOKEN", "from-env")
    assert credentials.get_secret("STRAVA_REFRESH_TOKEN") == "from-env"


def test_file_wins_over_environment(store, monkeypatch):
    credentials.set_secret("OURA_ACCESS_TOKEN", "from-file")
    monkeypatch.setenv("OURA_ACCESS_TOKEN", "from-env")
    assert credentials.get_secret("OURA_ACCESS_TOKEN") == "from-file"


def test_keychain_hit_is_migrated_into_the_file(store, monkeypatch):
    monkeypatch.setattr(credentials, "_legacy_keychain_get", lambda name: "from-keychain")
    assert credentials.get_secret("TOGGL_API_TOKEN") == "from-keychain"
    data = json.loads((store / ".credentials.json").read_text())
    assert data["TOGGL_API_TOKEN"] == "from-keychain"


def test_migrated_key_no_longer_consults_legacy(store, monkeypatch):
    calls = []

    def once(name):
        calls.append(name)
        return "from-keychain"

    monkeypatch.setattr(credentials, "_legacy_keychain_get", once)
    credentials.get_secret("TOGGL_API_TOKEN")
    credentials.get_secret("TOGGL_API_TOKEN")
    assert calls == ["TOGGL_API_TOKEN"]


def test_legacy_secrets_json_is_migrated(store, monkeypatch):
    monkeypatch.setattr(credentials, "_legacy_file_get", lambda name: "from-legacy-file")
    assert credentials.get_secret("EARLY_API_KEY") == "from-legacy-file"
    data = json.loads((store / ".credentials.json").read_text())
    assert data["EARLY_API_KEY"] == "from-legacy-file"


def test_legacy_source_oserror_is_a_miss_not_a_crash(store, monkeypatch):
    monkeypatch.setattr(credentials, "_legacy_keychain_get",
                        lambda name: (_ for _ in ()).throw(OSError("no security binary")))
    with pytest.raises(KeyError):
        credentials.get_secret("NOPE")


def test_missing_everywhere_raises_keyerror(store):
    with pytest.raises(KeyError):
        credentials.get_secret("NOPE")


def test_explicit_provider_env_bypasses_the_chain(store, monkeypatch):
    credentials.set_secret("OURA_ACCESS_TOKEN", "from-file")
    monkeypatch.setenv("OURA_ACCESS_TOKEN", "from-env")
    assert credentials.get_secret("OURA_ACCESS_TOKEN", provider="env") == "from-env"


def test_file_set_calls_the_git_guard(store, monkeypatch):
    seen = []
    monkeypatch.setattr(credentials, "_ensure_store_ignored", lambda d: seen.append(d))
    credentials.set_secret("OURA_ACCESS_TOKEN", "tok")
    assert seen == [store]


def test_store_dir_falls_back_to_user_config_dir(monkeypatch, tmp_path):
    def boom(*a, **kw):
        raise RuntimeError("no tenant")

    import engine.memory as memory
    import engine.paths as paths
    monkeypatch.setattr(memory, "resolve_store", boom)
    monkeypatch.setattr(paths, "user_config_dir", lambda *a, **kw: tmp_path)
    assert credentials._store_dir() == tmp_path
