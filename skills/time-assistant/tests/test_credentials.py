import pytest
from engine import credentials


def test_env_provider(monkeypatch):
    monkeypatch.setenv("MY_SECRET", "abc123")
    assert credentials.get_secret("MY_SECRET", provider="env") == "abc123"


def test_env_provider_missing_raises(monkeypatch):
    monkeypatch.delenv("NOPE", raising=False)
    with pytest.raises(KeyError):
        credentials.get_secret("NOPE", provider="env")


def test_default_provider_from_env(monkeypatch):
    monkeypatch.setenv("TIME_ASSISTANT_CRED_PROVIDER", "env")
    monkeypatch.setenv("FOO", "bar")
    assert credentials.get_secret("FOO") == "bar"


def test_get_secrets_batch(monkeypatch):
    monkeypatch.setenv("A", "1")
    monkeypatch.setenv("B", "2")
    assert credentials.get_secrets(["A", "B"], provider="env") == {"A": "1", "B": "2"}


def test_unknown_provider_raises():
    with pytest.raises(ValueError):
        credentials.get_secret("X", provider="bogus")
