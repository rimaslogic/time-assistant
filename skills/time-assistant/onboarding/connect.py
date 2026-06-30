"""Self-contained token validation + storage. No dependency on sibling skills:
validation is a direct urllib call. HTTP is injectable for tests. The wizard
(SKILL.md) opens the provider page, then hands off to the `!`-run hidden-input
helper `store_token.py` to capture the secret — tokens are never pasted into
chat, a command preview, or terminal history."""
import base64
import json
import urllib.request

from engine import credentials

PROVIDER_FIELDS = {
    "oura": ["OURA_ACCESS_TOKEN"],
    "timeular": ["EARLY_API_KEY", "EARLY_API_SECRET"],
    "toggl": ["TOGGL_API_TOKEN"],
}
PROVIDER_PAGES = {
    "oura": "https://cloud.ouraring.com/personal-access-tokens",
    "timeular": "https://profile.timeular.com/#/app/account/developerTools",
    # Token found at: toggl.com → Profile → API Token.
    # Toggl now issues toggl_sk_… service-account tokens. resolve_toggl_token()
    # exchanges any pasted value for the canonical 32-char api_token via
    # GET /api/v9/me before storing, so the adapter's Basic auth always works.
    "toggl": "https://track.toggl.com/profile",
}

_TOGGL_ME_URL = "https://api.track.toggl.com/api/v9/me"


def _http_ok(url, headers=None, data=None, method="GET") -> bool:
    req = urllib.request.Request(url, headers=headers or {}, data=data, method=method)
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            return 200 <= r.status < 300
    except Exception:
        return False


def _default_http(provider_id, values) -> bool:
    if provider_id == "oura":
        return _http_ok("https://api.ouraring.com/v2/usercollection/personal_info",
                        headers={"Authorization": f"Bearer {values['OURA_ACCESS_TOKEN']}"})
    if provider_id == "timeular":
        body = json.dumps({"apiKey": values["EARLY_API_KEY"],
                           "apiSecret": values["EARLY_API_SECRET"]}).encode()
        return _http_ok("https://api.timeular.com/api/v3/developer/sign-in",
                        headers={"Content-Type": "application/json"},
                        data=body, method="POST")
    return False


def _real_toggl_http(scheme: str, token: str):
    """Live HTTP for resolve_toggl_token. Returns parsed JSON dict on 2xx, else None."""
    if scheme == "Basic":
        raw = f"{token}:api_token".encode()
        auth_header = "Basic " + base64.b64encode(raw).decode()
    elif scheme == "Bearer":
        auth_header = f"Bearer {token}"
    else:
        return None
    req = urllib.request.Request(_TOGGL_ME_URL,
                                 headers={"Authorization": auth_header, "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            if 200 <= r.status < 300:
                return json.loads(r.read().decode())
    except Exception:
        pass
    return None


def resolve_toggl_token(pasted: str, *, http=None) -> str:
    """Validate *pasted* against GET /api/v9/me, trying auth schemes in order:

      1. Basic base64("<pasted>:api_token") — the classic api_token format
      2. Bearer <pasted>                    — toggl_sk_… service-account token

    On the first 2xx response, return the ``api_token`` field from the JSON body
    (the canonical 32-char classic token).  Falls back to the pasted value if
    the field is absent but auth succeeded.  Raises RuntimeError if all schemes
    fail.

    ``http(scheme, token) -> dict | None`` is injectable for tests (None = auth
    failure; exceptions are caught and treated as failure so the next scheme is
    tried).
    """
    _http = http or _real_toggl_http
    pasted = pasted.strip()  # paste often carries a trailing newline / stray space
    for scheme in ("Basic", "Bearer"):
        try:
            result = _http(scheme, pasted)
        except Exception:
            result = None
        if result is not None:
            return result.get("api_token") or pasted
    raise RuntimeError("Toggl token did not authenticate")


def validate(provider_id, values, *, http=None) -> bool:
    """Return True iff the provider credentials are accepted by the live API.

    For *toggl*, ``http`` is forwarded to ``resolve_toggl_token`` with signature
    ``(scheme, token) -> dict | None``.  For all other providers, ``http`` has
    the legacy signature ``(provider_id, values) -> bool``.
    """
    if provider_id == "toggl":
        try:
            resolve_toggl_token(values["TOGGL_API_TOKEN"], http=http)
            return True
        except Exception:
            return False
    fn = http or _default_http
    return bool(fn(provider_id, values))


def diagnose(provider_id, values, *, http=None) -> str:
    """Return '' if the credentials validate, else a short human-readable reason.

    Lets ``store_token.py`` tell the user *why* a token was rejected instead of a
    silent "no". For *toggl*, surfaces the ``resolve_toggl_token`` error message;
    for other providers, reports that the API rejected the credential. The reason
    never contains the secret itself.
    """
    if provider_id == "toggl":
        try:
            resolve_toggl_token(values["TOGGL_API_TOKEN"], http=http)
            return ""
        except Exception as e:
            return str(e)
    return "" if validate(provider_id, values, http=http) else \
        "the provider's API did not accept the credential"


def store(provider_id, values, *, setter=credentials.set_secret, http=None) -> None:
    """Persist credentials via *setter*.

    For *toggl*, the pasted token is first resolved to the canonical classic
    api_token via ``resolve_toggl_token`` (using the injected *http* if given).
    The resolved classic token is what gets stored so that the adapter's Basic
    auth always works.
    """
    if provider_id == "toggl":
        resolved = resolve_toggl_token(values["TOGGL_API_TOKEN"], http=http)
        setter("TOGGL_API_TOKEN", resolved, provider="keystore")
        return
    for field in PROVIDER_FIELDS[provider_id]:
        setter(field, values[field], provider="keystore")
