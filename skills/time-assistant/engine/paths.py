"""Per-OS directories. The only OS-branching in the engine. Injectable
platform/env/home so all three OSes are testable on one machine."""
import os
import sys
from pathlib import Path

APP = "TimeAssistant"


def _plat(platform):
    return platform or sys.platform


def _env(env):
    return os.environ if env is None else env


def _home(home):
    return Path.home() if home is None else home


def user_config_dir(app=APP, *, platform=None, env=None, home=None) -> Path:
    p, e, h = _plat(platform), _env(env), _home(home)
    if p == "darwin":
        return h / "Library" / "Application Support" / app
    if p == "win32":
        return Path(e.get("APPDATA") or str(h / "AppData" / "Roaming")) / app
    return Path(e.get("XDG_CONFIG_HOME") or str(h / ".config")) / app


def default_data_dir(app=APP, *, platform=None, env=None, home=None) -> Path:
    p, e, h = _plat(platform), _env(env), _home(home)
    if p == "darwin":
        return h / "Library" / "Application Support" / app
    if p == "win32":
        return Path(e.get("APPDATA") or str(h / "AppData" / "Roaming")) / app
    return Path(e.get("XDG_DATA_HOME") or str(h / ".local" / "share")) / app
