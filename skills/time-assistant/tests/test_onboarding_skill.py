from pathlib import Path

SKILL = Path(__file__).resolve().parent.parent


def test_helper_modules_import():
    import onboarding.setup       # noqa: F401
    import onboarding.connect     # noqa: F401
    import engine.paths           # noqa: F401


def test_skill_md_documents_wizard():
    text = (SKILL / "SKILL.md").read_text(encoding="utf-8")
    assert "set up my time assistant" in text.lower()
    assert "google calendar" in text.lower()
    assert "onboarding.setup" in text
    assert "resum" in text.lower()


def test_skill_md_documents_strava_and_scheduling():
    text = (SKILL / "SKILL.md").read_text(encoding="utf-8").lower()
    assert "strava" in text
    assert "onboarding.strava_connect" in text or "strava_connect" in text
    assert "schedule" in text and ("onboarding.schedule" in text or "schedule.py" in text or "daily brief" in text)


def test_skill_md_wizard_polish():
    """Guard: 5 UX-polish cues added in tester feedback round (insights 6,11,12,13,15,17)."""
    text = (SKILL / "SKILL.md").read_text(encoding="utf-8").lower()

    # insight 6 & 13 — batched consent: ask once, allow access
    assert "once" in text and ("allow access" in text or "allow" in text), \
        "batched-consent cue ('once' + 'allow access') not found"

    # insight 11 — one page/tab at a time
    assert ("one page" in text or "one tab" in text or "exactly one" in text), \
        "one-page-at-a-time cue not found"

    # insight 12 — paid-plan warning
    assert "paid plan" in text, \
        "paid-plan warning cue not found"

    # insight 15 — oura sync delay messaging
    assert "sync" in text, \
        "oura sync-delay messaging cue ('sync') not found"

    # insight 17 — restate confirmation with explicit type instruction
    assert ("type `yes`" in text or "restate" in text), \
        "restate-confirmation cue ('type `yes`' or 'restate') not found"
