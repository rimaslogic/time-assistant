import os
import plistlib
import re

from onboarding import schedule as sch

# ---------------------------------------------------------------------------
# resolve_claude
# ---------------------------------------------------------------------------

def test_resolve_claude_which_hit():
    result = sch.resolve_claude(which=lambda name: "/usr/bin/claude")
    assert result == "/usr/bin/claude"


def test_resolve_claude_fallback(tmp_path):
    fake = tmp_path / ".local" / "bin" / "claude"
    fake.parent.mkdir(parents=True)
    fake.touch()
    result = sch.resolve_claude(which=lambda name: None, home=tmp_path)
    assert result == str(fake)


def test_resolve_claude_last_resort(tmp_path):
    result = sch.resolve_claude(which=lambda name: None, home=tmp_path)
    assert result == "claude"


# ---------------------------------------------------------------------------
# wrapper_script
# ---------------------------------------------------------------------------

def test_wrapper_script_contains_absolute_path(tmp_path):
    content = sch.wrapper_script(tmp_path / "store", claude_path="/abs/claude")
    assert "/abs/claude" in content


def test_wrapper_script_writes_to_store(tmp_path):
    store = tmp_path / "store"
    content = sch.wrapper_script(store, claude_path="/abs/claude")
    assert str(store) + "/briefs" in content
    # The brief (claude stdout) is teed into the dated file by the shell, not
    # left to claude's headless write-tool access.
    assert "tee -a" in content and '"$briefs/$d.md"' in content


def test_wrapper_script_no_bare_claude(tmp_path):
    content = sch.wrapper_script(tmp_path / "store", claude_path="/abs/claude")
    assert not re.search(r"^claude ", content, re.MULTILINE)


def test_wrapper_script_prepends_local_bin_to_path(tmp_path):
    """launchd/cron strip PATH; the wrapper must restore ~/.local/bin (Insight 1)."""
    content = sch.wrapper_script(tmp_path / "store", claude_path="/abs/claude")
    assert 'export PATH="$HOME/.local/bin:$PATH"' in content


def test_wrapper_script_handles_awkward_prompt_and_store(tmp_path):
    """Prompt containing a double-quote and store path with a space must not
    produce a broken shell script; $d must still expand at runtime."""
    store = tmp_path / "my store with spaces"
    tricky_prompt = 'Do the "morning" brief'
    content = sch.wrapper_script(store, claude_path="/usr/bin/claude", prompt=tricky_prompt)
    # Must be non-empty
    assert content
    # $d must appear outside single quotes so the shell expands it at runtime
    assert "$d" in content
    # The store path must be present (safely quoted) in the script
    assert str(store) in content
    # Single quotes must be balanced (even count)
    assert content.count("'") % 2 == 0
    # The dated path fragment must be intact for runtime expansion
    assert "$d.md" in content


# ---------------------------------------------------------------------------
# launchd_plist
# ---------------------------------------------------------------------------

def test_launchd_plist_uses_wrapper(tmp_path):
    xml = sch.launchd_plist(7, 30, wrapper_path="/tmp/wrapper.sh", store_dir=tmp_path / "store")
    d = plistlib.loads(xml.encode())
    assert d["ProgramArguments"] == ["/bin/sh", "/tmp/wrapper.sh"]


def test_launchd_plist_has_log_paths(tmp_path):
    store = tmp_path / "store"
    xml = sch.launchd_plist(7, 30, wrapper_path="/tmp/wrapper.sh", store_dir=store)
    d = plistlib.loads(xml.encode())
    expected_log = str(store / "briefs" / "scheduler.log")
    assert d.get("StandardOutPath") == expected_log
    assert d.get("StandardErrorPath") == expected_log


# ---------------------------------------------------------------------------
# cron_line / schtasks_command
# ---------------------------------------------------------------------------

def test_cron_line_uses_wrapper():
    line = sch.cron_line(7, 30, wrapper_path="/abs/wrapper.sh")
    assert "/abs/wrapper.sh" in line
    # Must not invoke bare claude — only the wrapper via /bin/sh
    assert not re.search(r'\bclaude\b', line)


def test_schtasks_uses_wrapper():
    cmd = sch.schtasks_command(7, 30, wrapper_path="/abs/wrapper.sh")
    assert "/abs/wrapper.sh" in cmd
    # Must not invoke bare claude — only the wrapper via sh
    assert not re.search(r'\bclaude\b', cmd)


# ---------------------------------------------------------------------------
# install (darwin)
# ---------------------------------------------------------------------------

def test_install_darwin_writes_wrapper(tmp_path):
    store = tmp_path / "store"
    art = sch.artifact_for("darwin", 7, 30, store_dir=store, claude_path="/usr/bin/claude", home=tmp_path)
    sch.install("darwin", art, store_dir=store, claude_path="/usr/bin/claude",
                runner=lambda c, **k: None, home=tmp_path)
    wrapper = tmp_path / "Library" / "Application Support" / "TimeAssistant" / "ta-brief-wrapper.sh"
    assert wrapper.exists()
    assert os.access(wrapper, os.X_OK)


def test_install_darwin_plist_references_wrapper(tmp_path):
    store = tmp_path / "store"
    art = sch.artifact_for("darwin", 7, 30, store_dir=store, claude_path="/usr/bin/claude", home=tmp_path)
    sch.install("darwin", art, store_dir=store, claude_path="/usr/bin/claude",
                runner=lambda c, **k: None, home=tmp_path)
    plist_path = tmp_path / "Library" / "LaunchAgents" / f"{sch.LABEL}.plist"
    d = plistlib.loads(plist_path.read_bytes())
    expected_wrapper = str(
        tmp_path / "Library" / "Application Support" / "TimeAssistant" / "ta-brief-wrapper.sh"
    )
    assert d["ProgramArguments"] == ["/bin/sh", expected_wrapper]


# ---------------------------------------------------------------------------
# Existing tests — updated signatures
# ---------------------------------------------------------------------------

def test_brief_command():
    cmd = sch.brief_command(sch.DEFAULT_PROMPT, claude_path="/usr/bin/claude")
    assert "/usr/bin/claude" in cmd
    assert "-p" in cmd
    assert sch.DEFAULT_PROMPT in cmd


def test_launchd_plist_is_valid_and_scheduled(tmp_path):
    xml = sch.launchd_plist(7, 30, wrapper_path="/tmp/wrap.sh", store_dir=tmp_path)
    d = plistlib.loads(xml.encode())
    assert d["Label"] == sch.LABEL
    assert d["StartCalendarInterval"]["Hour"] == 7
    assert d["StartCalendarInterval"]["Minute"] == 30
    assert d["ProgramArguments"] == ["/bin/sh", "/tmp/wrap.sh"]


def test_cron_line():
    line = sch.cron_line(7, 30, wrapper_path="/abs/wrapper.sh")
    assert line.startswith("30 7 * * * ")
    assert "/abs/wrapper.sh" in line


def test_schtasks_command():
    cmd = sch.schtasks_command(7, 30, wrapper_path="/abs/wrapper.sh")
    assert "schtasks" in cmd and "/Create" in cmd and "07:30" in cmd


def test_artifact_for_selects_per_os(tmp_path):
    store = tmp_path / "store"
    assert sch.artifact_for("darwin", 7, 30, store_dir=store, claude_path="/usr/bin/claude")["kind"] == "launchd"
    assert sch.artifact_for("linux", 7, 30, store_dir=store, claude_path="/usr/bin/claude")["kind"] == "cron"
    assert sch.artifact_for("win32", 7, 30, store_dir=store, claude_path="/usr/bin/claude")["kind"] == "schtasks"


def test_install_macos_writes_plist_and_loads(tmp_path):
    cmds = []
    store = tmp_path / "store"
    art = sch.artifact_for("darwin", 7, 30, store_dir=store, claude_path="/usr/bin/claude", home=tmp_path)
    summary = sch.install("darwin", art, store_dir=store, claude_path="/usr/bin/claude",
                          runner=lambda c, **k: cmds.append(c), home=tmp_path)
    plist = tmp_path / "Library" / "LaunchAgents" / f"{sch.LABEL}.plist"
    assert plist.exists()
    assert any("launchctl" in c[0] for c in cmds)
    assert "LaunchAgents" in summary


def test_install_windows_does_not_autorun(tmp_path):
    ran = []
    store = tmp_path / "store"
    art = sch.artifact_for("win32", 7, 30, store_dir=store, claude_path="/usr/bin/claude", home=tmp_path)
    summary = sch.install("win32", art, store_dir=store, claude_path="/usr/bin/claude",
                          runner=lambda c, **k: ran.append(c), home=tmp_path)
    assert ran == []                      # never auto-runs on Windows
    assert "schtasks" in summary          # returns the command to paste


def test_install_linux_appends_to_crontab(tmp_path):
    import types
    recorded_inputs = []

    def spy_runner(cmd, **kwargs):
        if cmd == ["crontab", "-l"]:
            return types.SimpleNamespace(stdout="# existing\n")
        if cmd == ["crontab", "-"]:
            recorded_inputs.append(kwargs.get("input", ""))
        return types.SimpleNamespace(stdout="")

    store = tmp_path / "store"
    art = sch.artifact_for("linux", 7, 30, store_dir=store, claude_path="/usr/bin/claude", home=tmp_path)
    summary = sch.install("linux", art, store_dir=store, claude_path="/usr/bin/claude",
                          runner=spy_runner, home=tmp_path)

    assert len(recorded_inputs) == 1
    new_crontab = recorded_inputs[0]
    assert "# existing" in new_crontab
    assert art["content"] in new_crontab
    assert not new_crontab.startswith("\n")
    assert "crontab" in summary


def test_install_precreates_briefs_dir(tmp_path):
    # The launchd StandardOut/ErrPath sink must have a valid parent on first fire.
    store = tmp_path / "store"
    art = sch.artifact_for("darwin", 7, 30, store_dir=store, claude_path="/abs/claude", home=tmp_path)
    sch.install("darwin", art, store_dir=store, claude_path="/abs/claude",
                runner=lambda *a, **k: None, home=tmp_path / "home")
    assert (store / "briefs").is_dir()
