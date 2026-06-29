#!/usr/bin/env python3
"""Minimal Strava API v3 client. Read-only.

Auto-refreshes access token using STRAVA_REFRESH_TOKEN.
"""
import argparse
import json
import os
import sys
import time
from datetime import datetime, timezone

import urllib.parse
import urllib.request
import urllib.error


def _http_json(method, url, *, headers=None, form=None, params=None, timeout=20):
    if params:
        url = f"{url}?{urllib.parse.urlencode(params)}"
    data = urllib.parse.urlencode(form).encode() if form is not None else None
    req = urllib.request.Request(url, data=data, headers=headers or {}, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"Strava API {method} {url} failed: {e.code} {e.reason}") from e
    except urllib.error.URLError as e:
        raise RuntimeError(f"Strava API {method} {url} failed: {e}") from e


CLIENT_ID = os.environ.get("STRAVA_CLIENT_ID", "")
CLIENT_SECRET = os.environ.get("STRAVA_CLIENT_SECRET", "")
REFRESH_TOKEN = os.environ.get("STRAVA_REFRESH_TOKEN", "")
BASE = "https://www.strava.com/api/v3"

_cached = {"access_token": None, "expires_at": 0}


def get_token():
    if _cached["access_token"] and _cached["expires_at"] > time.time() + 60:
        return _cached["access_token"]
    if not (CLIENT_ID and CLIENT_SECRET and REFRESH_TOKEN):
        print("Error: set STRAVA_CLIENT_ID, STRAVA_CLIENT_SECRET, STRAVA_REFRESH_TOKEN", file=sys.stderr)
        sys.exit(1)
    d = _http_json("POST", "https://www.strava.com/oauth/token", form={
        "client_id": CLIENT_ID, "client_secret": CLIENT_SECRET,
        "refresh_token": REFRESH_TOKEN, "grant_type": "refresh_token",
    }, timeout=15)
    _cached["access_token"] = d["access_token"]
    _cached["expires_at"] = d["expires_at"]
    return d["access_token"]


def api(path, params=None):
    token = get_token()
    return _http_json("GET", f"{BASE}{path}",
                      headers={"Authorization": f"Bearer {token}"},
                      params=params or {})


def cmd_athlete(args):
    print(json.dumps(api("/athlete"), indent=2))


def cmd_activities(args):
    params = {"per_page": args.limit}
    if args.after:
        params["after"] = int(datetime.fromisoformat(args.after).replace(tzinfo=timezone.utc).timestamp())
    if args.before:
        params["before"] = int(datetime.fromisoformat(args.before).replace(tzinfo=timezone.utc).timestamp())
    data = api("/athlete/activities", params)
    if args.json:
        print(json.dumps(data, indent=2))
        return
    print(f"{'Date':<12}{'Type':<14}{'Dur':>6}{'Dist':>7}{'Suffer':>7}  Name")
    print("-" * 80)
    for a in data:
        date = a["start_date_local"][:10]
        dur = int(a["moving_time"] / 60)
        dist = a["distance"] / 1000
        suf = a.get("suffer_score") or "-"
        print(f"{date:<12}{a['type']:<14}{dur:>5}m{dist:>6.1f}k{str(suf):>7}  {a['name']}")


def cmd_stats(args):
    ath = api("/athlete")
    data = api(f"/athletes/{ath['id']}/stats")
    print(json.dumps(data, indent=2))


def cmd_load(args):
    """Compute recent training load: last N days of activities with suffer_score."""
    from datetime import timedelta

    n = args.days
    after = int((datetime.now(timezone.utc) - timedelta(days=n)).timestamp())
    data = api("/athlete/activities", {"per_page": 100, "after": after})
    total_min = sum(a["moving_time"] for a in data) / 60
    total_km = sum(a["distance"] for a in data) / 1000
    total_suffer = sum((a.get("suffer_score") or 0) for a in data)
    hiit_count = sum(1 for a in data if (a["type"] in ("Ride", "VirtualRide", "Workout") and (a.get("suffer_score") or 0) >= 50))
    print(f"Last {n} days: {len(data)} activities")
    print(f"  Total time: {total_min/60:.1f}h")
    print(f"  Total distance: {total_km:.1f} km")
    print(f"  Total suffer_score: {total_suffer}")
    print(f"  Probable HIIT/hard sessions: {hiit_count}")
    if args.json:
        print(json.dumps({
            "days": n,
            "activities": len(data),
            "total_hours": round(total_min / 60, 2),
            "total_km": round(total_km, 2),
            "total_suffer": total_suffer,
            "hiit_count": hiit_count,
            "by_type": {t: sum(1 for a in data if a["type"] == t) for t in set(a["type"] for a in data)},
        }, indent=2))


def main():
    p = argparse.ArgumentParser(description="Strava API v3 client (read-only)")
    p.add_argument("--json", action="store_true")
    sub = p.add_subparsers(dest="cmd")

    p_ath = sub.add_parser("athlete", help="Show authenticated athlete")
    p_ath.set_defaults(func=cmd_athlete)

    p_act = sub.add_parser("activities", help="List recent activities")
    p_act.add_argument("--limit", type=int, default=20)
    p_act.add_argument("--after", help="ISO date (inclusive lower bound)")
    p_act.add_argument("--before", help="ISO date (exclusive upper bound)")
    p_act.set_defaults(func=cmd_activities)

    p_st = sub.add_parser("stats", help="Lifetime/recent stats")
    p_st.set_defaults(func=cmd_stats)

    p_load = sub.add_parser("load", help="Training load summary")
    p_load.add_argument("--days", type=int, default=7)
    p_load.set_defaults(func=cmd_load)

    args = p.parse_args()
    if not args.cmd:
        p.print_help()
        sys.exit(0)
    args.func(args)


if __name__ == "__main__":
    main()
