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
