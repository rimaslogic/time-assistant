"""Tests for onboarding/store_token.py — secure hidden-input token entry."""
from onboarding import connect
from onboarding import store_token


def test_success_path_calls_store_and_prints_confirmation():
    stored = {}
    messages = []

    def fake_getpass(prompt):
        return "super-secret-token"

    def fake_validate(pid, values):
        return True

    def fake_store(pid, values):
        stored["pid"] = pid
        stored["values"] = values

    rc = store_token.main(
        ["oura"],
        getpass_fn=fake_getpass,
        validate=fake_validate,
        store=fake_store,
        out=messages.append,
    )

    assert rc == 0
    assert stored["pid"] == "oura"
    assert stored["values"] == {"OURA_ACCESS_TOKEN": "super-secret-token"}
    # Success message must not contain the token value
    assert len(messages) == 1
    assert "super-secret-token" not in messages[0]
    assert "oura" in messages[0]


def test_failure_path_returns_1_and_does_not_call_store():
    stored = {}
    messages = []

    def fake_getpass(prompt):
        return "bad-token"

    def fake_validate(pid, values):
        return False

    def fake_store(pid, values):
        stored["called"] = True

    rc = store_token.main(
        ["oura"],
        getpass_fn=fake_getpass,
        validate=fake_validate,
        store=fake_store,
        diagnose=lambda pid, vals: "the provider's API did not accept the credential",
        out=messages.append,
    )

    assert rc == 1
    assert "called" not in stored
    blob = "\n".join(messages)
    assert "nothing was stored" in blob
    assert "Re-run" in blob
    # The actionable reason from diagnose() is surfaced to the user.
    assert "did not accept" in blob
    # The secret value is never echoed back.
    assert "bad-token" not in blob


def test_failure_path_skips_reason_line_when_diagnose_empty():
    """When diagnose() returns '' the Reason line is omitted (still actionable)."""
    messages = []
    rc = store_token.main(
        ["oura"],
        getpass_fn=lambda p: "bad",
        validate=lambda pid, vals: False,
        store=lambda pid, values: None,
        diagnose=lambda pid, vals: "",
        out=messages.append,
    )
    assert rc == 1
    blob = "\n".join(messages)
    assert "Reason:" not in blob
    assert "Re-run" in blob


def test_unknown_provider_returns_2():
    messages = []
    rc = store_token.main(
        ["nonexistent"],
        getpass_fn=lambda p: "x",
        out=messages.append,
    )
    assert rc == 2
    assert "usage" in messages[0]


def test_no_args_returns_2():
    messages = []
    rc = store_token.main(
        [],
        getpass_fn=lambda p: "x",
        out=messages.append,
    )
    assert rc == 2


def test_captured_values_passed_to_validate_and_store():
    """validate and store both receive the dict with exactly the right key/value."""
    validate_calls = []
    store_calls = []

    def fake_getpass(prompt):
        # Return distinct value per field name (embedded in prompt)
        return f"value-for-{prompt.split()[1]}"

    def fake_validate(pid, values):
        validate_calls.append((pid, dict(values)))
        return True

    def fake_store(pid, values):
        store_calls.append((pid, dict(values)))

    store_token.main(
        ["timeular"],
        getpass_fn=fake_getpass,
        validate=fake_validate,
        store=fake_store,
        out=lambda _: None,
    )

    assert len(validate_calls) == 1
    assert validate_calls[0][0] == "timeular"
    assert "EARLY_API_KEY" in validate_calls[0][1]
    assert "EARLY_API_SECRET" in validate_calls[0][1]

    assert len(store_calls) == 1
    assert store_calls[0][0] == "timeular"
    assert store_calls[0][1] == validate_calls[0][1]


def test_toggl_path_stores_and_hides_value():
    stored = {}
    messages = []

    rc = store_token.main(
        ["toggl"],
        getpass_fn=lambda prompt: "tok",
        validate=lambda pid, vals: True,
        store=lambda pid, values: stored.update({"pid": pid, "values": values}),
        out=messages.append,
    )

    assert rc == 0
    assert stored["pid"] == "toggl"
    assert stored["values"] == {"TOGGL_API_TOKEN": "tok"}
    assert len(messages) == 1
    assert "tok" not in messages[0]


def test_default_store_is_connect_store():
    """The default store argument is connect.store (writes via keystore provider)."""
    import inspect
    sig = inspect.signature(store_token.main)
    assert sig.parameters["store"].default is None  # injected at call time
    # Verify that when no store is provided the real connect.store is used
    # by checking the source refers to connect.store
    import ast, textwrap
    src = inspect.getsource(store_token.main)
    assert "connect.store" in src
