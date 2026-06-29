from pathlib import Path

SKILL = Path(__file__).resolve().parent.parent


def test_legacy_scripts_removed():
    assert not (SKILL / "scripts" / "score.py").exists()
    assert not (SKILL / "scripts" / "memory.py").exists()
    assert not (SKILL / "scripts" / "timeular_client.py").exists()


def test_engine_is_importable_entrypoint():
    import engine.score, engine.memory, engine.config  # noqa: F401


def test_skill_md_is_persona_neutral():
    text = (SKILL / "SKILL.md").read_text(encoding="utf-8")
    # Description/framing must not hardcode the single user as owner.
    assert "Rimas's 80/20 Time Assistant" not in text
    assert "tenant" in text.lower()
