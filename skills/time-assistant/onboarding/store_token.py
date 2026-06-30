"""Securely capture + validate + store an integration secret. Run it YOURSELF
with the `!` prefix so your keystrokes go to the hidden prompt and the value
never enters the chat, a command preview, or terminal history:

    ! "$TIME_ASSISTANT_PYTHON" <plugin>/skills/time-assistant/onboarding/store_token.py oura
"""
import getpass
import sys
from onboarding import connect


def main(argv=None, *, getpass_fn=getpass.getpass, validate=None, store=None,
         diagnose=None, out=print) -> int:
    argv = sys.argv[1:] if argv is None else argv
    if not argv or argv[0] not in connect.PROVIDER_FIELDS:
        out("usage: store_token.py <provider: oura | timeular | toggl>")
        return 2
    pid = argv[0]
    validate = validate or connect.validate
    store = store or connect.store
    diagnose = diagnose or connect.diagnose
    values = {f: getpass_fn(f"Paste {f} (input hidden): ").strip()
              for f in connect.PROVIDER_FIELDS[pid]}
    if not validate(pid, values):
        out(f"✗ Couldn't verify your {pid} credentials — nothing was stored.")
        reason = diagnose(pid, values)
        if reason:
            out(f"  Reason: {reason}")
        out("  Re-run this command and double-check you pasted the FULL value "
            "with no extra spaces or line breaks.")
        return 1
    store(pid, values)
    out(f"✓ {pid} connected — stored in your OS keystore. The value was never shown or logged.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
