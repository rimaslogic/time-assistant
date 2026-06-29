"""Guard tests: onboarding docs must contain the three non-technical-user fixes.

Tester insights covered:
  1. Users typed /plugin in a plain chat window → must explain Claude Code session.
  2. `claude` gave command not found → must mention ~/.local/bin PATH workaround.
  3. /reload-plugins step was missing → must be present after install commands.
"""

from pathlib import Path

# Test file lives at skills/time-assistant/tests/test_docs_onboarding.py
# parents: [0]=tests/, [1]=time-assistant/, [2]=skills/, [3]=repo root
_REPO = Path(__file__).resolve().parents[3]


def _read(rel: str) -> str:
    p = _REPO / rel
    assert p.exists(), f"File not found: {p}"
    return p.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# INSTALL.md
# ---------------------------------------------------------------------------

def test_install_md_mentions_claude_code_session():
    text = _read("INSTALL.md")
    assert "Claude Code session" in text, (
        "INSTALL.md must tell users the /plugin commands run inside a Claude Code session"
    )


def test_install_md_mentions_local_bin_path():
    text = _read("INSTALL.md")
    assert "~/.local/bin" in text, (
        "INSTALL.md must mention ~/.local/bin as the PATH workaround for 'command not found'"
    )


def test_install_md_contains_reload_plugins():
    text = _read("INSTALL.md")
    assert "/reload-plugins" in text, (
        "INSTALL.md must include the /reload-plugins step after plugin installation"
    )


# ---------------------------------------------------------------------------
# welcome/index.html
# ---------------------------------------------------------------------------

def test_welcome_mentions_terminal_session():
    text = _read("welcome/index.html")
    # Accept either phrasing: "Claude Code session" or "terminal"
    assert "Claude Code session" in text or "terminal" in text, (
        "welcome/index.html must tell users to open a Claude Code / terminal session"
    )


def test_welcome_contains_reload_plugins():
    text = _read("welcome/index.html")
    assert "/reload-plugins" in text, (
        "welcome/index.html must include /reload-plugins after the install commands"
    )
