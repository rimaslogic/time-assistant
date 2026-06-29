import plistlib
from onboarding import schedule as sch


def test_brief_command():
    assert sch.brief_command() == ["claude", "-p", sch.DEFAULT_PROMPT]


def test_launchd_plist_is_valid_and_scheduled():
    xml = sch.launchd_plist(7, 30)
    d = plistlib.loads(xml.encode())
    assert d["Label"] == sch.LABEL
    assert d["StartCalendarInterval"]["Hour"] == 7
    assert d["StartCalendarInterval"]["Minute"] == 30
    assert d["ProgramArguments"][:2] == ["claude", "-p"]


def test_cron_line():
    line = sch.cron_line(7, 30)
    assert line.startswith("30 7 * * * ")
    assert "claude -p" in line


def test_schtasks_command():
    cmd = sch.schtasks_command(7, 30)
    assert "schtasks" in cmd and "/Create" in cmd and "07:30" in cmd


def test_artifact_for_selects_per_os():
    assert sch.artifact_for("darwin", 7, 30)["kind"] == "launchd"
    assert sch.artifact_for("linux", 7, 30)["kind"] == "cron"
    assert sch.artifact_for("win32", 7, 30)["kind"] == "schtasks"


def test_install_macos_writes_plist_and_loads(tmp_path):
    cmds = []
    art = sch.artifact_for("darwin", 7, 30)
    summary = sch.install("darwin", art, runner=lambda c, **k: cmds.append(c), home=tmp_path)
    plist = tmp_path / "Library" / "LaunchAgents" / f"{sch.LABEL}.plist"
    assert plist.exists()
    assert any("launchctl" in c[0] for c in cmds)
    assert "LaunchAgents" in summary


def test_install_windows_does_not_autorun():
    ran = []
    art = sch.artifact_for("win32", 7, 30)
    summary = sch.install("win32", art, runner=lambda c, **k: ran.append(c))
    assert ran == []                      # never auto-runs on Windows
    assert "schtasks" in summary          # returns the command to paste


def test_install_linux_appends_to_crontab():
    import types
    recorded_inputs = []

    def spy_runner(cmd, **kwargs):
        if cmd == ["crontab", "-l"]:
            return types.SimpleNamespace(stdout="# existing\n")
        if cmd == ["crontab", "-"]:
            recorded_inputs.append(kwargs.get("input", ""))
        return types.SimpleNamespace(stdout="")

    art = sch.artifact_for("linux", 7, 30)
    summary = sch.install("linux", art, runner=spy_runner)

    assert len(recorded_inputs) == 1
    new_crontab = recorded_inputs[0]
    assert "# existing" in new_crontab
    assert art["content"] in new_crontab
    assert not new_crontab.startswith("\n")
    assert "crontab" in summary
