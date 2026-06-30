import json
from onboarding import setup


def test_setup_provisions_store_and_registry(tmp_path):
    store = setup.setup("Dana", "Europe/Warsaw", ["MO", "TU"], "knowledge-worker",
                        store_dir=tmp_path / "store", config_dir=tmp_path / "cfg",
                        git_init=False)
    cfg = json.loads((store / "config.json").read_text())
    assert cfg["tenant_id"] == "me"
    assert cfg["cred_provider"] == "keystore"
    assert cfg["onboarding"] == {"completed_steps": []}
    reg = json.loads((tmp_path / "cfg" / "tenants.json").read_text())
    assert reg["tenants"]["me"]["store_path"] == str(tmp_path / "store")


def test_setup_seeds_template_without_overwrite(tmp_path):
    seed = tmp_path / "tpl"; seed.mkdir()
    (seed / "rules.json").write_text('{"rules": ["seed"]}')
    (seed / "config.json").write_text('{"from": "seed-should-be-ignored"}')
    store = tmp_path / "s"; store.mkdir()
    # Pre-existing files in the store must NOT be overwritten by seeding.
    (store / "rules.json").write_text('{"rules": ["mine"]}')
    setup.setup("X", "UTC", ["MO"], "knowledge-worker",
                store_dir=store, config_dir=tmp_path / "c",
                seed_from=seed, git_init=False)
    # pre-existing rules.json untouched (dst-exists guard):
    import json
    assert json.loads((store / "rules.json").read_text())["rules"] == ["mine"]
    # config.json is the one setup wrote (tenant_id "me"), NOT the seed's:
    assert json.loads((store / "config.json").read_text())["tenant_id"] == "me"


def test_onboarding_state_resumable_idempotent(tmp_path):
    store = setup.setup("X", "UTC", ["MO"], "knowledge-worker",
                        store_dir=tmp_path / "s", config_dir=tmp_path / "c",
                        git_init=False)
    assert setup.next_step(store) == "identity"
    setup.mark_step_done(store, "identity")
    setup.mark_step_done(store, "identity")
    assert setup.load_onboarding_state(store)["completed_steps"] == ["identity"]
    assert setup.next_step(store) == "framework"


def test_rules_step_runs_after_enrichments_before_first_brief(tmp_path):
    """Classification rules are gathered before the first brief so it isn't
    dominated by 'unclassified' time (tester Insight 3)."""
    steps = setup.ONBOARDING_STEPS
    assert steps.index("rules") == steps.index("enrichments") + 1
    assert steps.index("rules") < steps.index("first_brief")


def test_mark_step_done_noop_before_store(tmp_path):
    # No config.json yet -> must not raise.
    setup.mark_step_done(tmp_path / "nonexistent-store", "identity")


def test_next_step_returns_none_when_all_done(tmp_path):
    store = setup.setup("X", "UTC", ["MO"], "knowledge-worker",
                        store_dir=tmp_path / "s", config_dir=tmp_path / "c",
                        git_init=False)
    for step in setup.ONBOARDING_STEPS:
        setup.mark_step_done(store, step)
    assert setup.next_step(store) is None
