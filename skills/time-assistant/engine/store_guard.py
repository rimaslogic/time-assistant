"""Keep the credentials file out of git.

The tenant store is a git repo the routines commit to on every run, and
docs/SETUP.md tells operators to run `git add .`. An unignored
.credentials.json in that directory would be committed and pushed."""
import subprocess
from pathlib import Path

IGNORE_RULE = ".credentials.json"


class StoreGuardError(RuntimeError):
    """The credentials file cannot be written safely."""


def _git(args, cwd):
    try:
        return subprocess.run(["git", *args], cwd=str(cwd),
                              capture_output=True, text=True)
    except OSError:
        return None  # git not installed


def is_git_repo(store_dir, *, runner=None) -> bool:
    out = (runner or _git)(["rev-parse", "--is-inside-work-tree"], store_dir)
    return out is not None and out.returncode == 0 and out.stdout.strip() == "true"


def is_tracked(store_dir, filename=IGNORE_RULE, *, runner=None) -> bool:
    out = (runner or _git)(["ls-files", "--error-unmatch", filename], store_dir)
    return out is not None and out.returncode == 0


def ensure_ignored(store_dir, *, runner=None) -> None:
    """No-op outside a git repo. Otherwise guarantee IGNORE_RULE is ignored.

    Raises StoreGuardError if the file is already tracked — writing secrets
    into a tracked file is the one outcome this must never allow silently."""
    store_dir = Path(store_dir)
    if not is_git_repo(store_dir, runner=runner):
        return
    if is_tracked(store_dir, runner=runner):
        raise StoreGuardError(
            f"{IGNORE_RULE} is already tracked by git in {store_dir}. "
            f"Run `git -C {store_dir} rm --cached {IGNORE_RULE}` and retry — "
            "then rotate any credential that was committed."
        )
    gitignore = store_dir / ".gitignore"
    text = gitignore.read_text(encoding="utf-8") if gitignore.exists() else ""
    if IGNORE_RULE in [line.strip() for line in text.splitlines()]:
        return
    separator = "" if text == "" or text.endswith("\n") else "\n"
    try:
        gitignore.write_text(text + separator + IGNORE_RULE + "\n", encoding="utf-8")
    except OSError as e:
        raise StoreGuardError(f"Cannot write {gitignore}: {e}") from e
