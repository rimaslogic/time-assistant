"""On-device Strava OAuth loopback — no backend. The wizard guides the user to
create a Strava API app (open APP_PAGE), collects client id+secret in chat,
then this module captures the OAuth code on a localhost listener and exchanges
it for a refresh token. HTTP and the loopback server are injectable for tests."""
import json
import urllib.parse
import urllib.request
import urllib.error

from engine import credentials

APP_PAGE = "https://www.strava.com/settings/api"
AUTHORIZE = "https://www.strava.com/oauth/authorize"
TOKEN = "https://www.strava.com/oauth/token"
DEFAULT_PORT = 8721
SCOPE = "activity:read_all"


def build_authorize_url(client_id, *, port=DEFAULT_PORT, scope=SCOPE) -> str:
    q = urllib.parse.urlencode({
        "client_id": client_id,
        "redirect_uri": f"http://localhost:{port}/",
        "response_type": "code",
        "approval_prompt": "force",
        "scope": scope,
    })
    return f"{AUTHORIZE}?{q}"


def _default_http(url, form) -> dict:
    data = urllib.parse.urlencode(form).encode()
    req = urllib.request.Request(url, data=data, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            return json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"Strava token exchange failed: {e.code} {e.reason}") from e
    except urllib.error.URLError as e:
        raise RuntimeError(f"Strava token exchange network error: {e}") from e


def exchange_code(client_id, client_secret, code, *, http=None) -> dict:
    fn = http or _default_http
    out = fn(TOKEN, {
        "client_id": client_id, "client_secret": client_secret,
        "code": code, "grant_type": "authorization_code",
    })
    if "refresh_token" not in out:
        raise RuntimeError("Strava did not return a refresh_token")
    return out


class _LoopbackServer:
    """Serves one request on localhost:<port>, returns its ?code= value."""
    def __init__(self, port):
        self._port = port

    def serve_until_code(self, timeout):
        from http.server import BaseHTTPRequestHandler, HTTPServer
        captured = {}

        class Handler(BaseHTTPRequestHandler):
            def do_GET(self):
                qs = urllib.parse.urlparse(self.path).query
                params = urllib.parse.parse_qs(qs)
                captured["code"] = params.get("code", [""])[0]
                captured["error"] = params.get("error", [""])[0]
                self.send_response(200)
                self.send_header("Content-Type", "text/html")
                self.end_headers()
                self.wfile.write(b"<h2>Strava connected. You can close this tab.</h2>")
            def log_message(self, *a):
                pass

        srv = HTTPServer(("localhost", self._port), Handler)
        srv.timeout = timeout
        srv.handle_request()
        srv.server_close()
        error = captured.get("error", "")
        if error:
            raise RuntimeError(f"Strava authorization failed: {error}")
        code = captured.get("code", "")
        if not code:
            raise TimeoutError(f"No OAuth redirect received within {timeout}s — did you approve in the browser?")
        return code


def capture_code(*, port=DEFAULT_PORT, server_factory=None, timeout=180) -> str:
    factory = server_factory or _LoopbackServer
    server = factory(port)
    return server.serve_until_code(timeout)


def store(client_id, client_secret, refresh_token, *, setter=credentials.set_secret) -> None:
    setter("STRAVA_CLIENT_ID", client_id, provider="keystore")
    setter("STRAVA_CLIENT_SECRET", client_secret, provider="keystore")
    setter("STRAVA_REFRESH_TOKEN", refresh_token, provider="keystore")


def main(argv=None, *, getpass_fn=None, opener=None, capture=None,
         exchange=None, store_fn=None, out=print) -> int:
    """Securely connect Strava: reads client id/secret via hidden input, runs
    on-device OAuth, and stores credentials — secrets never appear in argv,
    stdout, or terminal history.  Run with the `!` prefix:

        ! "$TIME_ASSISTANT_PYTHON" <plugin>/skills/time-assistant/onboarding/strava_connect.py
    """
    import getpass as _getpass
    import webbrowser

    getpass_fn = getpass_fn or _getpass.getpass
    opener = opener or webbrowser.open
    capture_fn = capture or capture_code
    exchange_fn = exchange or exchange_code
    store_fn = store_fn or store

    client_id = getpass_fn("Paste STRAVA_CLIENT_ID (input hidden): ").strip()
    client_secret = getpass_fn("Paste STRAVA_CLIENT_SECRET (input hidden): ").strip()

    auth_url = build_authorize_url(client_id)
    out(f"Opening Strava authorization page… (approve in the browser, then return here)")
    opener(auth_url)

    code = capture_fn()
    token_data = exchange_fn(client_id, client_secret, code)
    refresh_token = token_data["refresh_token"]
    store_fn(client_id, client_secret, refresh_token)
    out("✓ Strava connected — credentials stored in your OS keystore. The values were never shown or logged.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
