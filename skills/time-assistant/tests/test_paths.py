from pathlib import Path
from engine import paths


def test_config_dir_macos():
    assert paths.user_config_dir(platform="darwin", home=Path("/Users/x"), env={}) == \
        Path("/Users/x/Library/Application Support/TimeAssistant")


def test_config_dir_windows():
    assert paths.user_config_dir(platform="win32", home=Path("C:/U/x"),
                                 env={"APPDATA": "C:/U/x/AppData/Roaming"}) == \
        Path("C:/U/x/AppData/Roaming/TimeAssistant")


def test_config_dir_linux_default():
    assert paths.user_config_dir(platform="linux", home=Path("/home/x"), env={}) == \
        Path("/home/x/.config/TimeAssistant")


def test_data_dir_linux_xdg():
    assert paths.default_data_dir(platform="linux", home=Path("/home/x"),
                                  env={"XDG_DATA_HOME": "/home/x/.local/share"}) == \
        Path("/home/x/.local/share/TimeAssistant")


def test_data_dir_macos():
    assert paths.default_data_dir(platform="darwin", home=Path("/Users/x"), env={}) == \
        Path("/Users/x/Library/Application Support/TimeAssistant")
