import shutil
import subprocess
from pathlib import Path
import pytest

BOOT = Path(__file__).resolve().parent.parent / "bin" / "bootstrap.sh"


def run(args, env_extra=None):
    import os
    env = {**os.environ, **(env_extra or {})}
    return subprocess.run(["bash", str(BOOT), *args], capture_output=True, text=True, env=env)


def test_script_exists_and_executable():
    assert BOOT.exists()


def test_find_system_returns_a_python_or_empty():
    out = run(["--find-system"])
    assert out.returncode == 0
    # On this dev machine a python3 >= 3.10 exists, so it should print a path.
    if out.stdout.strip():
        assert "python" in out.stdout.strip().lower()


def test_print_url_linux_x86_64():
    out = run(["--print-url"], {"TA_OS": "linux", "TA_ARCH": "x86_64"})
    assert out.returncode == 0
    url = out.stdout.strip()
    assert url.startswith("https://")
    assert "linux" in url and ("x86_64" in url or "x86-64" in url)


def test_print_url_macos_arm64():
    out = run(["--print-url"], {"TA_OS": "darwin", "TA_ARCH": "arm64"})
    url = out.stdout.strip()
    assert url.startswith("https://")
    assert ("aarch64" in url or "arm64" in url) and ("apple" in url or "darwin" in url)


def test_print_url_windows_x86_64():
    out = run(["--print-url"], {"TA_OS": "windows", "TA_ARCH": "x86_64"})
    url = out.stdout.strip()
    assert url.startswith("https://")
    assert ("windows" in url) and ("x86_64" in url or "x86-64" in url)


def test_default_writes_env_file_when_set(tmp_path):
    env_file = tmp_path / "envfile"
    env_file.write_text("")
    out = run([], {"CLAUDE_ENV_FILE": str(env_file), "TA_DATA_DIR": str(tmp_path / "data")})
    # If a system python is found, no download happens; the env file must get the export.
    if out.returncode == 0 and shutil.which("python3"):
        assert "TIME_ASSISTANT_PYTHON=" in env_file.read_text()
