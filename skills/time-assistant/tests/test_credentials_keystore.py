import json
import os
import stat
import pytest
from engine import credentials


@pytest.fixture
def cfg_dir(tmp_path, monkeypatch):
    monkeypatch.setattr(credentials, "_keystore_dir", lambda: tmp_path)
    monkeypatch.setattr(credentials, "_use_keychain", lambda: False)  # force file path
    return tmp_path


def test_set_then_get_via_file(cfg_dir):
    credentials.set_secret("OURA_ACCESS_TOKEN", "tok", provider="keystore")
    data = json.loads((cfg_dir / "secrets.json").read_text())
    assert data["OURA_ACCESS_TOKEN"] == "tok"
    assert credentials.get_secret("OURA_ACCESS_TOKEN", provider="keystore") == "tok"


def test_file_is_permission_locked(cfg_dir):
    credentials.set_secret("X", "y", provider="keystore")
    if os.name == "posix":
        assert stat.S_IMODE(os.stat(cfg_dir / "secrets.json").st_mode) == 0o600


def test_get_missing_raises(cfg_dir):
    with pytest.raises(KeyError):
        credentials.get_secret("NOPE", provider="keystore")


def test_keychain_path_dispatches_to_security(monkeypatch, tmp_path):
    monkeypatch.setattr(credentials, "_keystore_dir", lambda: tmp_path)
    monkeypatch.setattr(credentials, "_use_keychain", lambda: True)  # mac path
    calls = []
    def fake_run(cmd, **kw):
        calls.append(cmd)
        class R:  # mimic subprocess.CompletedProcess
            returncode = 0
            stdout = "tok\n"
        return R()
    monkeypatch.setattr(credentials.subprocess, "run", fake_run)
    credentials.set_secret("K", "tok", provider="keystore")
    assert any(c[0] == "security" for c in calls)
    assert credentials.get_secret("K", provider="keystore") == "tok"


def test_keychain_set_failure_raises(monkeypatch, tmp_path):
    monkeypatch.setattr(credentials, "_keystore_dir", lambda: tmp_path)
    monkeypatch.setattr(credentials, "_use_keychain", lambda: True)
    class R:
        returncode = 1
        stdout = ""
    monkeypatch.setattr(credentials.subprocess, "run", lambda cmd, **kw: R())
    import pytest
    with pytest.raises(RuntimeError):
        credentials.set_secret("K", "tok", provider="keystore")


def test_default_get_provider_still_env(monkeypatch):
    monkeypatch.delenv("TIME_ASSISTANT_CRED_PROVIDER", raising=False)
    monkeypatch.setenv("S", "v")
    assert credentials.get_secret("S") == "v"
