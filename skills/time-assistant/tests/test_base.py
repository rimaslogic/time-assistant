import pytest
from integrations.base import Manifest, Adapter, KIND_TIME, run_cli
from engine.records import TimeRecord


def test_manifest_roundtrip():
    m = Manifest(id="x", kind=KIND_TIME, label="X", auth_fields=["X_KEY"],
                 capabilities=["entries"], how_to_obtain="get a key")
    assert Manifest.from_dict(m.to_dict()) == m


def test_adapter_requires_manifest():
    class Bad(Adapter):
        def fetch(self, start, end): return []
        def check_auth(self): return True
    with pytest.raises(NotImplementedError):
        Bad().manifest_or_raise()


def test_concrete_adapter_fetch():
    class Fake(Adapter):
        manifest = Manifest(id="fake", kind=KIND_TIME, label="Fake",
                            auth_fields=[], capabilities=["entries"],
                            how_to_obtain="n/a")
        def check_auth(self): return True
        def fetch(self, start, end):
            return [TimeRecord(start="2026-06-01T09:00:00",
                               end="2026-06-01T10:00:00", activity="focus",
                               tags=[], note="", source="fake")]
    recs = Fake().fetch("2026-06-01", "2026-06-01")
    assert recs[0].duration_min == 60


def test_run_cli_parses_json(tmp_path):
    script = tmp_path / "fake_cli.py"
    script.write_text('import json,sys; print(json.dumps({"ok": True}))')
    import sys
    assert run_cli([sys.executable, str(script)]) == {"ok": True}


def test_run_cli_raises_on_nonzero_exit(tmp_path):
    import sys
    script = tmp_path / "fail_cli.py"
    script.write_text("import sys; sys.exit(1)")
    with pytest.raises(RuntimeError):
        run_cli([sys.executable, str(script)])
