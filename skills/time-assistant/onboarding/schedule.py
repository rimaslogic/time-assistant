"""Generate a per-OS daily-brief schedule entry and (on macOS/Linux) offer to
install it. The scheduled job runs `claude -p "<prompt>"` headless. We never
silently modify the system: install() is only called after the user agrees,
and Windows is always copy-paste."""
import plistlib
import subprocess
from pathlib import Path

LABEL = "pl.rimaslogic.timeassistant.dailybrief"
DEFAULT_PROMPT = "Run my time-assistant morning brief"


def brief_command(prompt=DEFAULT_PROMPT) -> list:
    return ["claude", "-p", prompt]


def launchd_plist(hour, minute, *, prompt=DEFAULT_PROMPT, label=LABEL) -> str:
    d = {
        "Label": label,
        "ProgramArguments": brief_command(prompt),
        "StartCalendarInterval": {"Hour": int(hour), "Minute": int(minute)},
        "RunAtLoad": False,
    }
    return plistlib.dumps(d).decode()


def cron_line(hour, minute, *, prompt=DEFAULT_PROMPT) -> str:
    return f"{int(minute)} {int(hour)} * * * claude -p '{prompt}'"


def schtasks_command(hour, minute, *, prompt=DEFAULT_PROMPT, name="TimeAssistantBrief") -> str:
    return (f'schtasks /Create /SC DAILY /TN "{name}" '
            f'/TR "claude -p \\"{prompt}\\"" /ST {int(hour):02d}:{int(minute):02d}')


def artifact_for(platform, hour, minute, *, prompt=DEFAULT_PROMPT) -> dict:
    if platform == "darwin":
        return {"kind": "launchd", "content": launchd_plist(hour, minute, prompt=prompt),
                "install_hint": f"~/Library/LaunchAgents/{LABEL}.plist + launchctl load"}
    if platform == "win32":
        return {"kind": "schtasks", "content": schtasks_command(hour, minute, prompt=prompt),
                "install_hint": "run this command in a terminal"}
    return {"kind": "cron", "content": cron_line(hour, minute, prompt=prompt),
            "install_hint": "added to your user crontab"}


def install(platform, artifact, *, runner=subprocess.run, home=None) -> str:
    if platform == "darwin":
        base = Path(home) if home else Path.home()
        target = base / "Library" / "LaunchAgents" / f"{LABEL}.plist"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(artifact["content"], encoding="utf-8")
        runner(["launchctl", "load", str(target)], capture_output=True)
        return f"Installed launchd job at {target} (LaunchAgents)."
    if platform == "win32":
        # Never auto-run on Windows — return the command for the user to paste.
        return f"Run this command to schedule the daily brief:\n{artifact['content']}"
    # Linux: append to the user crontab.
    existing = runner(["crontab", "-l"], capture_output=True, text=True)
    current = getattr(existing, "stdout", "") or ""
    new = current + ("" if current.endswith("\n") or not current else "\n") + artifact["content"] + "\n"
    runner(["crontab", "-"], input=new, text=True, capture_output=True)
    return "Added the daily brief to your user crontab."
