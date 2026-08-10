"""Store credentials the user pasted into the Claude Code chat.

Reads ONE JSON object from stdin — never argv — so the values do not appear
in a process listing, a command preview, or shell history:

    echo '{"OURA_ACCESS_TOKEN": "..."}' | "$TIME_ASSISTANT_PYTHON" \\
        <plugin>/skills/time-assistant/onboarding/save_credentials.py

Prints only the field names it stored. Values are never echoed, including on
error paths. Nothing is validated against the provider APIs: a well-formed but
wrong value is stored and surfaces later as an adapter error."""
import json
import sys
from pathlib import Path

# Run-by-path support: `python .../onboarding/save_credentials.py` puts only
# this directory on sys.path, so the skill root must be added for package
# imports.
if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from engine import credentials
from engine.store_guard import StoreGuardError
from onboarding import connect


def known_fields() -> list:
    return sorted({f for fields in connect.PROVIDER_FIELDS.values() for f in fields})


def main(argv=None, *, stdin=None, setter=None, out=print, err=None) -> int:
    stdin = stdin or sys.stdin
    setter = setter or credentials.set_secret
    err = err or (lambda msg: print(msg, file=sys.stderr))

    try:
        data = json.loads(stdin.read())
    except ValueError as e:
        err(f"Could not parse stdin as JSON: {e}")
        return 2

    if not isinstance(data, dict) or not data:
        err("Expected a non-empty JSON object mapping FIELD_NAME to value.")
        return 2

    allowed = known_fields()
    unknown = sorted(k for k in data if k not in allowed)
    if unknown:
        err(f"Unknown field(s): {', '.join(unknown)}. "
            f"Accepted: {', '.join(allowed)}")
        return 2

    blank = sorted(k for k, v in data.items()
                   if not isinstance(v, str) or not v.strip())
    if blank:
        err(f"Empty or non-string value(s) for: {', '.join(blank)}")
        return 2

    try:
        for field in sorted(data):
            setter(field, data[field].strip(), provider="keystore")
    except StoreGuardError as e:
        err(str(e))
        return 1
    except Exception as e:  # never let a traceback carry a value to the console
        err(f"Could not store credentials: {type(e).__name__}: {e}")
        return 1

    out("Stored: " + ", ".join(sorted(data)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
