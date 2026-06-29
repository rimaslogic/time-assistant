"""Generate a per-OS daily-brief schedule entry and (on macOS/Linux) offer to
install it. The scheduled job runs a wrapper script that invokes claude with an
absolute path and appends the brief to a dated file in the store plus a log.
We never silently modify the system: install() is only called after the user
agrees, and Windows is always copy-paste."""
import plistlib
import shlex
import shutil
import subprocess
from pathlib import Path

from engine import paths

LABEL = "pl.rimaslogic.timeassistant.dailybrief"
DEFAULT_PROMPT = "Run my time-assistant morning brief"
WRAPPER_NAME = "ta-brief-wrapper.sh"


# ---------------------------------------------------------------------------
# resolve_claude
# ---------------------------------------------------------------------------

def resolve_claude(*, which=shutil.which, home=None) -> str:
    """Return absolute path to claude binary.

    Resolution order:
    1. which("claude") — honours the current PATH.
    2. ~/.local/bin/claude — common pipx/uv install location missing from
       launchd's stripped PATH.
    3. "claude" — last resort; logged so the operator knows it may fail.
    """
    hit = which("claude")
    if hit:
        return hit
    h = Path.home() if home is None else Path(home)
    fallback = h / ".local" / "bin" / "claude"
    if fallback.exists():
        return str(fallback)
    # Last resort — callers should log/warn about this path.
    return "claude"


# ---------------------------------------------------------------------------
# wrapper_script
# ---------------------------------------------------------------------------

def wrapper_script(store_dir, *, claude_path, prompt=DEFAULT_PROMPT) -> str:
    """Return a sh script that runs claude with absolute paths and sinks output.

    The wrapper:
    - Resolves today's date for the brief filename.
    - Creates the briefs directory if absent.
    - Appends claude output (stdout + stderr) to scheduler.log.
    - On macOS, fires a notification via osascript.

    All paths and the prompt are shell-quoted via shlex.quote() to prevent
    injection.  The dated brief path embeds $d outside the single-quoted prefix
    so the variable still expands at runtime.
    """
    store = str(store_dir)
    q_claude = shlex.quote(str(claude_path))
    q_briefs = shlex.quote(store + "/briefs")
    q_prompt = shlex.quote(prompt)
    # The shell captures claude's stdout (the brief) into the dated file via
    # `tee` — so the brief is saved deterministically, regardless of whether the
    # headless claude session has file-write tools. stderr and a copy of stdout
    # go to scheduler.log. All paths/prompt are shlex-quoted to prevent injection.
    return (
        "#!/bin/sh\n"
        'd="$(date +%F)"\n'
        f'briefs={q_briefs}\n'
        'mkdir -p "$briefs"\n'
        f'{q_claude} -p {q_prompt} 2>> "$briefs/scheduler.log"'
        ' | tee -a "$briefs/$d.md" >> "$briefs/scheduler.log"\n'
        "command -v osascript >/dev/null 2>&1 && "
        "osascript -e 'display notification \"Your time brief is ready\""
        " with title \"Time Assistant\"' || true\n"
    )


# ---------------------------------------------------------------------------
# brief_command
# ---------------------------------------------------------------------------

def brief_command(prompt, *, claude_path) -> str:
    """Return the claude invocation string using the resolved absolute path."""
    return f'"{claude_path}" -p "{prompt}"'


# ---------------------------------------------------------------------------
# Schedule-entry generators
# ---------------------------------------------------------------------------

def launchd_plist(hour, minute, *, wrapper_path, store_dir, label=LABEL) -> str:
    """Return plist XML.

    ProgramArguments invokes the wrapper via /bin/sh (not bare claude).
    StandardOutPath and StandardErrorPath both point at scheduler.log so
    output is never discarded even if the wrapper's redirect somehow fails.
    """
    log_path = str(Path(store_dir) / "briefs" / "scheduler.log")
    d = {
        "Label": label,
        "ProgramArguments": ["/bin/sh", str(wrapper_path)],
        "StartCalendarInterval": {"Hour": int(hour), "Minute": int(minute)},
        "RunAtLoad": False,
        "StandardOutPath": log_path,
        "StandardErrorPath": log_path,
    }
    return plistlib.dumps(d).decode()


def cron_line(hour, minute, *, wrapper_path) -> str:
    """Return cron line invoking wrapper_path (absolute), not bare claude."""
    return f"{int(minute)} {int(hour)} * * * /bin/sh {shlex.quote(str(wrapper_path))}"


def schtasks_command(hour, minute, *, wrapper_path, name="TimeAssistantBrief") -> str:
    """Return schtasks command invoking wrapper_path.

    NOTE (Windows): the wrapper is a POSIX shell script — it requires Git Bash
    or WSL.  The generated command uses ``sh`` from Git Bash.  If ``sh`` is not
    on PATH, users should adjust the TR value to the full path of sh.exe.
    """
    return (
        f'schtasks /Create /SC DAILY /TN "{name}" '
        f'/TR "sh \\"{str(wrapper_path)}\\"" /ST {int(hour):02d}:{int(minute):02d}'
    )


# ---------------------------------------------------------------------------
# Internal helper
# ---------------------------------------------------------------------------

def _wrapper_path_for(platform, *, home=None) -> Path:
    """Return the canonical wrapper path for the given platform."""
    config_dir = paths.user_config_dir(platform=platform, home=home)
    return config_dir / WRAPPER_NAME


# ---------------------------------------------------------------------------
# artifact_for
# ---------------------------------------------------------------------------

def artifact_for(
    platform, hour, minute, *, store_dir, claude_path, prompt=DEFAULT_PROMPT, home=None
) -> dict:
    """Return schedule artifact dict for the given platform.

    The ``content`` field contains the ready-to-install schedule entry
    (plist XML, cron line, or schtasks command) referencing the canonical
    wrapper path for the platform/home combination.
    """
    wp = _wrapper_path_for(platform, home=home)
    if platform == "darwin":
        return {
            "kind": "launchd",
            "content": launchd_plist(hour, minute, wrapper_path=wp, store_dir=store_dir),
            "wrapper_path": str(wp),
            "store_dir": str(store_dir),
            "claude_path": claude_path,
            "prompt": prompt,
            "hour": hour,
            "minute": minute,
            "install_hint": f"~/Library/LaunchAgents/{LABEL}.plist + launchctl load",
        }
    if platform == "win32":
        return {
            "kind": "schtasks",
            "content": schtasks_command(hour, minute, wrapper_path=wp),
            "wrapper_path": str(wp),
            "store_dir": str(store_dir),
            "claude_path": claude_path,
            "prompt": prompt,
            "hour": hour,
            "minute": minute,
            "install_hint": "run this command in a terminal (requires Git Bash / WSL)",
        }
    # Linux / everything else → cron
    return {
        "kind": "cron",
        "content": cron_line(hour, minute, wrapper_path=wp),
        "wrapper_path": str(wp),
        "store_dir": str(store_dir),
        "claude_path": claude_path,
        "prompt": prompt,
        "hour": hour,
        "minute": minute,
        "install_hint": "added to your user crontab",
    }


# ---------------------------------------------------------------------------
# install
# ---------------------------------------------------------------------------

def install(platform, artifact, *, store_dir, claude_path, runner=subprocess.run, home=None) -> str:
    """Write wrapper (chmod +x) under the OS config dir, install the schedule
    entry, and return a human-readable summary including all relevant paths.

    The wrapper is always written first so the schedule entry can reference it.
    On Windows the schedule entry is NOT auto-installed; the schtasks command is
    returned for the user to paste (Git Bash / WSL required for the wrapper).
    """
    prompt = artifact.get("prompt", DEFAULT_PROMPT)

    # 1. Write the wrapper script into the config dir.
    config_dir = paths.user_config_dir(platform=platform, home=home)
    config_dir.mkdir(parents=True, exist_ok=True)
    wp = config_dir / WRAPPER_NAME
    wp.write_text(wrapper_script(store_dir, claude_path=claude_path, prompt=prompt), encoding="utf-8")
    wp.chmod(0o755)

    # Pre-create the briefs dir so the launchd StandardOut/ErrPath sink is valid
    # on the very first scheduled run (launchd opens the redirect before exec and
    # won't create missing parents).
    (Path(store_dir) / "briefs").mkdir(parents=True, exist_ok=True)

    if platform == "darwin":
        base = Path(home) if home else Path.home()
        plist_path = base / "Library" / "LaunchAgents" / f"{LABEL}.plist"
        plist_path.parent.mkdir(parents=True, exist_ok=True)
        plist_content = launchd_plist(
            artifact["hour"], artifact["minute"],
            wrapper_path=wp, store_dir=store_dir,
        )
        plist_path.write_text(plist_content, encoding="utf-8")
        runner(["launchctl", "load", str(plist_path)], capture_output=True)
        return (
            f"Installed launchd job at {plist_path} (LaunchAgents).\n"
            f"Wrapper: {wp}\n"
            f"Briefs/log: {store_dir}/briefs/"
        )

    if platform == "win32":
        # Never auto-run on Windows — return the command for the user to paste.
        cmd = schtasks_command(artifact["hour"], artifact["minute"], wrapper_path=wp)
        return (
            f"Run this command to schedule the daily brief:\n{cmd}\n"
            f"Wrapper written to: {wp}\n"
            "Note: the wrapper is a shell script — Git Bash or WSL must be available."
        )

    # Linux: append to the user crontab.
    line = cron_line(artifact["hour"], artifact["minute"], wrapper_path=wp)
    existing = runner(["crontab", "-l"], capture_output=True, text=True)
    current = getattr(existing, "stdout", "") or ""
    new = current + ("" if current.endswith("\n") or not current else "\n") + line + "\n"
    runner(["crontab", "-"], input=new, text=True, capture_output=True)
    return (
        f"Added the daily brief to your user crontab.\n"
        f"Wrapper: {wp}\n"
        f"Briefs/log: {store_dir}/briefs/"
    )
