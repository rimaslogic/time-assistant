"""Self-contained guided paste-token validation + storage. No dependency on
sibling skills: validation is a direct urllib call. HTTP is injectable for
tests. The wizard (SKILL.md) opens the page and collects the paste in chat."""
import json
import urllib.request

from engine import credentials

PROVIDER_FIELDS = {
    "oura": ["OURA_ACCESS_TOKEN"],
    "timeular": ["EARLY_API_KEY", "EARLY_API_SECRET"],
}
PROVIDER_PAGES = {
    "oura": "https://cloud.ouraring.com/personal-access-tokens",
    "timeular": "https://profile.timeular.com/#/app/account/developerTools",
}


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


def validate(provider_id, values, *, http=None) -> bool:
    fn = http or _default_http
    return bool(fn(provider_id, values))


def store(provider_id, values, *, setter=credentials.set_secret) -> None:
    for field in PROVIDER_FIELDS[provider_id]:
        setter(field, values[field], provider="keystore")
