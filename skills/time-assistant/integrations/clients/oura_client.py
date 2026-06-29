#!/usr/bin/env python3
"""Oura Ring API v2 — read-only client for health data."""

import os
import sys
import json
import argparse
from datetime import datetime, timedelta
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

BASE_URL = "https://api.ouraring.com/v2/usercollection"
ACCESS_TOKEN = os.environ.get("OURA_ACCESS_TOKEN", "")


def get_headers():
    """Return authorization headers."""
    if not ACCESS_TOKEN:
        print("ERROR: OURA_ACCESS_TOKEN not set", file=sys.stderr)
        print("Get your token from: https://cloud.ouraring.com/personal-access-tokens", file=sys.stderr)
        sys.exit(1)
    return {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Accept": "application/json",
    }


def api_get(endpoint, params=None):
    """Make a GET request to the Oura API."""
    url = f"{BASE_URL}/{endpoint}"
    if params:
        query = "&".join(f"{k}={v}" for k, v in params.items() if v)
        if query:
            url += f"?{query}"

    req = Request(url, headers=get_headers())
    try:
        with urlopen(req) as resp:
            return json.loads(resp.read().decode())
    except HTTPError as e:
        body = e.read().decode() if e.fp else ""
        print(f"ERROR: HTTP {e.code} — {body}", file=sys.stderr)
        sys.exit(1)
    except URLError as e:
        print(f"ERROR: Connection failed — {e.reason}", file=sys.stderr)
        sys.exit(1)


def default_dates():
    """Return default start/end dates (last 7 days)."""
    end = datetime.now().strftime("%Y-%m-%d")
    start = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
    return start, end


def mask_email(email):
    """Mask email for privacy."""
    if not email or "@" not in email:
        return email or ""
    local, domain = email.split("@", 1)
    return f"{local[0]}***@{domain}"


def fmt_seconds(seconds):
    """Format seconds as Xh Ym."""
    if not seconds:
        return "—"
    h = seconds // 3600
    m = (seconds % 3600) // 60
    return f"{h}h {m}m"


def fmt_temp(temp):
    """Format temperature deviation."""
    if temp is None:
        return "—"
    sign = "+" if temp >= 0 else ""
    return f"{sign}{temp:.1f}°C"


# ── Commands ──────────────────────────────────────────────

def cmd_sleep(args):
    start = args.start or default_dates()[0]
    end = args.end or default_dates()[1]
    data = api_get("daily_sleep", {"start_date": start, "end_date": end})

    if args.json:
        print(json.dumps(data, indent=2, ensure_ascii=False))
        return

    items = data.get("data", [])
    if not items:
        print("No sleep data found.")
        return

    print(f"{'Date':<12} {'Score':>5} {'Total':>7} {'Deep':>7} {'REM':>7} {'Light':>7} {'Effic':>5} {'HRV':>5}")
    print("─" * 70)
    for d in items:
        contributors = d.get("contributors", {})
        print(
            f"{d.get('day', '—'):<12} "
            f"{d.get('score', '—'):>5} "
            f"{fmt_seconds(d.get('total_sleep_duration')):>7} "
            f"{fmt_seconds(d.get('deep_sleep_duration')):>7} "
            f"{fmt_seconds(d.get('rem_sleep_duration')):>7} "
            f"{fmt_seconds(d.get('light_sleep_duration')):>7} "
            f"{contributors.get('efficiency', '—'):>5} "
            f"{contributors.get('deep_sleep', '—'):>5}"
        )
    print(f"\n{len(items)} days | {start} → {end}")


def cmd_readiness(args):
    start = args.start or default_dates()[0]
    end = args.end or default_dates()[1]
    data = api_get("daily_readiness", {"start_date": start, "end_date": end})

    if args.json:
        print(json.dumps(data, indent=2, ensure_ascii=False))
        return

    items = data.get("data", [])
    if not items:
        print("No readiness data found.")
        return

    print(f"{'Date':<12} {'Score':>5} {'Temp':>8} {'RestHR':>6} {'HRV Bal':>7} {'Recovery':>8}")
    print("─" * 55)
    for d in items:
        contributors = d.get("contributors", {})
        print(
            f"{d.get('day', '—'):<12} "
            f"{d.get('score', '—'):>5} "
            f"{fmt_temp(d.get('temperature_deviation')):>8} "
            f"{contributors.get('resting_heart_rate', '—'):>6} "
            f"{contributors.get('hrv_balance', '—'):>7} "
            f"{contributors.get('recovery_index', '—'):>8}"
        )
    print(f"\n{len(items)} days | {start} → {end}")


def cmd_activity(args):
    start = args.start or default_dates()[0]
    end = args.end or default_dates()[1]
    data = api_get("daily_activity", {"start_date": start, "end_date": end})

    if args.json:
        print(json.dumps(data, indent=2, ensure_ascii=False))
        return

    items = data.get("data", [])
    if not items:
        print("No activity data found.")
        return

    print(f"{'Date':<12} {'Score':>5} {'Steps':>7} {'Calories':>8} {'Active':>8} {'Move':>8}")
    print("─" * 55)
    for d in items:
        print(
            f"{d.get('day', '—'):<12} "
            f"{d.get('score', '—'):>5} "
            f"{d.get('steps', '—'):>7} "
            f"{d.get('total_calories', '—'):>8} "
            f"{fmt_seconds(d.get('high_activity_time')):>8} "
            f"{fmt_seconds(d.get('medium_activity_time')):>8}"
        )
    print(f"\n{len(items)} days | {start} → {end}")


def cmd_heart_rate(args):
    start = args.start or default_dates()[0]
    end = args.end or default_dates()[1]
    data = api_get("heartrate", {"start_datetime": f"{start}T00:00:00", "end_datetime": f"{end}T23:59:59"})

    if args.json:
        print(json.dumps(data, indent=2, ensure_ascii=False))
        return

    items = data.get("data", [])
    if not items:
        print("No heart rate data found.")
        return

    # Group by day and show summary
    days = {}
    for d in items:
        ts = d.get("timestamp", "")[:10]
        bpm = d.get("bpm", 0)
        if ts not in days:
            days[ts] = {"min": bpm, "max": bpm, "sum": bpm, "count": 1}
        else:
            days[ts]["min"] = min(days[ts]["min"], bpm)
            days[ts]["max"] = max(days[ts]["max"], bpm)
            days[ts]["sum"] += bpm
            days[ts]["count"] += 1

    print(f"{'Date':<12} {'Min':>5} {'Avg':>5} {'Max':>5} {'Readings':>8}")
    print("─" * 40)
    for day in sorted(days.keys()):
        s = days[day]
        avg = s["sum"] // s["count"]
        print(f"{day:<12} {s['min']:>5} {avg:>5} {s['max']:>5} {s['count']:>8}")
    print(f"\n{len(items)} readings across {len(days)} days")


def cmd_spo2(args):
    start = args.start or default_dates()[0]
    end = args.end or default_dates()[1]
    data = api_get("daily_spo2", {"start_date": start, "end_date": end})

    if args.json:
        print(json.dumps(data, indent=2, ensure_ascii=False))
        return

    items = data.get("data", [])
    if not items:
        print("No SpO2 data found.")
        return

    print(f"{'Date':<12} {'Avg %':>6} {'Breathing':>10}")
    print("─" * 30)
    for d in items:
        avg = d.get("spo2_percentage", {}).get("average", "—")
        breathing = d.get("breathing_disturbance_index", "—")
        print(f"{d.get('day', '—'):<12} {avg:>6} {breathing:>10}")
    print(f"\n{len(items)} days | {start} → {end}")


def cmd_stress(args):
    start = args.start or default_dates()[0]
    end = args.end or default_dates()[1]
    data = api_get("daily_stress", {"start_date": start, "end_date": end})

    if args.json:
        print(json.dumps(data, indent=2, ensure_ascii=False))
        return

    items = data.get("data", [])
    if not items:
        print("No stress data found.")
        return

    print(f"{'Date':<12} {'Stress High':>11} {'Recovery':>10} {'Rest':>8}")
    print("─" * 45)
    for d in items:
        print(
            f"{d.get('day', '—'):<12} "
            f"{d.get('stress_high', '—'):>11} "
            f"{d.get('recovery_high', '—'):>10} "
            f"{d.get('day_summary', '—'):>8}"
        )
    print(f"\n{len(items)} days | {start} → {end}")


def cmd_workout(args):
    start = args.start or default_dates()[0]
    end = args.end or default_dates()[1]
    data = api_get("workout", {"start_date": start, "end_date": end})

    if args.json:
        print(json.dumps(data, indent=2, ensure_ascii=False))
        return

    items = data.get("data", [])
    if not items:
        print("No workout data found.")
        return

    print(f"{'Date':<12} {'Type':<15} {'Duration':>8} {'Calories':>8} {'Intensity':<10}")
    print("─" * 58)
    for d in items:
        day = d.get("day", "—")
        activity = d.get("activity", "unknown")
        duration = fmt_seconds(d.get("duration"))
        calories = d.get("calories", "—")
        intensity = d.get("intensity", "—")
        print(f"{day:<12} {activity:<15} {duration:>8} {calories:>8} {intensity:<10}")
    print(f"\n{len(items)} workouts | {start} → {end}")


def cmd_info(args):
    data = api_get("personal_info")

    if args.json:
        # Mask email even in JSON mode
        if "email" in data:
            data["email"] = mask_email(data.get("email"))
        print(json.dumps(data, indent=2, ensure_ascii=False))
        return

    print("Personal Info")
    print("─" * 30)
    print(f"  Email:        {mask_email(data.get('email'))}")
    print(f"  Age:          {data.get('age', '—')}")
    print(f"  Weight:       {data.get('weight', '—')} kg")
    print(f"  Height:       {data.get('height', '—')} cm")
    print(f"  Sex:          {data.get('biological_sex', '—')}")


# ── Main ──────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Oura Ring API v2 client")
    parser.add_argument("--json", action="store_true", help="Output raw JSON")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # Date args shared by most commands
    def add_date_args(p):
        p.add_argument("--start", help="Start date (YYYY-MM-DD)")
        p.add_argument("--end", help="End date (YYYY-MM-DD)")
        p.add_argument("--json", action="store_true", help="Output raw JSON")

    p_sleep = subparsers.add_parser("sleep", help="Daily sleep summaries")
    add_date_args(p_sleep)
    p_sleep.set_defaults(func=cmd_sleep)

    p_readiness = subparsers.add_parser("readiness", help="Daily readiness scores")
    add_date_args(p_readiness)
    p_readiness.set_defaults(func=cmd_readiness)

    p_activity = subparsers.add_parser("activity", help="Daily activity data")
    add_date_args(p_activity)
    p_activity.set_defaults(func=cmd_activity)

    p_hr = subparsers.add_parser("heart-rate", help="Heart rate time series")
    add_date_args(p_hr)
    p_hr.set_defaults(func=cmd_heart_rate)

    p_spo2 = subparsers.add_parser("spo2", help="Blood oxygen data")
    add_date_args(p_spo2)
    p_spo2.set_defaults(func=cmd_spo2)

    p_stress = subparsers.add_parser("stress", help="Daily stress data")
    add_date_args(p_stress)
    p_stress.set_defaults(func=cmd_stress)

    p_workout = subparsers.add_parser("workout", help="Workout sessions")
    add_date_args(p_workout)
    p_workout.set_defaults(func=cmd_workout)

    p_info = subparsers.add_parser("info", help="Personal info")
    p_info.add_argument("--json", action="store_true", help="Output raw JSON")
    p_info.set_defaults(func=cmd_info)

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        sys.exit(1)

    args.func(args)


if __name__ == "__main__":
    main()
