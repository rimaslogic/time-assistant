import pytest
from engine import store_guard


class FakeGit:
    """Minimal git stand-in. `tracked` controls ls-files --error-unmatch."""

    def __init__(self, is_repo=True, tracked=False, available=True):
        self.is_repo, self.tracked, self.available = is_repo, tracked, available
        self.calls = []

    def __call__(self, args, cwd):
        self.calls.append(args)
        if not self.available:
            return None

        class R:
            returncode = 0
            stdout = ""

        r = R()
        if args[0] == "rev-parse":
            r.returncode = 0 if self.is_repo else 128
            r.stdout = "true\n" if self.is_repo else ""
        elif args[0] == "ls-files":
            r.returncode = 0 if self.tracked else 1
        return r


def test_appends_rule_to_existing_gitignore(tmp_path):
    (tmp_path / ".gitignore").write_text("*.pyc\n", encoding="utf-8")
    store_guard.ensure_ignored(tmp_path, runner=FakeGit())
    assert (tmp_path / ".gitignore").read_text() == "*.pyc\n.credentials.json\n"


def test_creates_gitignore_when_absent(tmp_path):
    store_guard.ensure_ignored(tmp_path, runner=FakeGit())
    assert (tmp_path / ".gitignore").read_text() == ".credentials.json\n"


def test_handles_gitignore_without_trailing_newline(tmp_path):
    (tmp_path / ".gitignore").write_text("*.pyc", encoding="utf-8")
    store_guard.ensure_ignored(tmp_path, runner=FakeGit())
    assert (tmp_path / ".gitignore").read_text() == "*.pyc\n.credentials.json\n"


def test_is_idempotent(tmp_path):
    store_guard.ensure_ignored(tmp_path, runner=FakeGit())
    store_guard.ensure_ignored(tmp_path, runner=FakeGit())
    assert (tmp_path / ".gitignore").read_text() == ".credentials.json\n"


def test_noop_when_not_a_git_repo(tmp_path):
    store_guard.ensure_ignored(tmp_path, runner=FakeGit(is_repo=False))
    assert not (tmp_path / ".gitignore").exists()


def test_noop_when_git_is_unavailable(tmp_path):
    store_guard.ensure_ignored(tmp_path, runner=FakeGit(available=False))
    assert not (tmp_path / ".gitignore").exists()


def test_raises_when_credentials_file_already_tracked(tmp_path):
    with pytest.raises(store_guard.StoreGuardError) as e:
        store_guard.ensure_ignored(tmp_path, runner=FakeGit(tracked=True))
    assert "rm --cached" in str(e.value)


def test_raises_when_gitignore_is_unwritable(tmp_path, monkeypatch):
    def boom(*a, **kw):
        raise OSError("read-only filesystem")

    monkeypatch.setattr(store_guard.Path, "write_text", boom)
    with pytest.raises(store_guard.StoreGuardError):
        store_guard.ensure_ignored(tmp_path, runner=FakeGit())
