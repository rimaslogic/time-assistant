#!/usr/bin/env python3
"""
EARLY (formerly Timeular) API Client
Direct REST API implementation - no external SDK dependency
"""

import os
import sys
import json
import argparse
from datetime import datetime, timedelta
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode

# Configuration
API_BASE = "https://api.early.app/api/v4"
API_KEY = os.environ.get("EARLY_API_KEY", "")
API_SECRET = os.environ.get("EARLY_API_SECRET", "")
ACCESS_TOKEN = os.environ.get("EARLY_ACCESS_TOKEN", "")


def api_request(method, endpoint, data=None, token=None):
    """Make authenticated API request"""
    url = f"{API_BASE}{endpoint}"
    headers = {"Content-Type": "application/json"}
    
    if token:
        headers["Authorization"] = f"Bearer {token}"
    
    body = json.dumps(data).encode() if data else None
    req = Request(url, data=body, headers=headers, method=method)
    
    try:
        with urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode())
    except HTTPError as e:
        error_body = e.read().decode() if e.fp else ""
        print(f"Error {e.code}: {error_body}", file=sys.stderr)
        sys.exit(1)
    except URLError as e:
        print(f"Connection error: {e.reason}", file=sys.stderr)
        sys.exit(1)


def get_token():
    """Get access token - use cached or sign in"""
    if ACCESS_TOKEN:
        return ACCESS_TOKEN
    
    if not API_KEY or not API_SECRET:
        print("Error: Set EARLY_API_KEY and EARLY_API_SECRET environment variables", file=sys.stderr)
        print("Get them from: https://profile.timeular.com/#/app/ → Integrations → API", file=sys.stderr)
        sys.exit(1)
    
    resp = api_request("POST", "/developer/sign-in", {
        "apiKey": API_KEY,
        "apiSecret": API_SECRET
    })
    return resp.get("token")


# ============ Authentication ============

def cmd_auth_test(args):
    """Test authentication"""
    token = get_token()
    resp = api_request("GET", "/me", token=token)
    print(json.dumps(resp, indent=2))


# ============ Activities ============

def cmd_activities_list(args):
    """List all activities"""
    token = get_token()
    resp = api_request("GET", "/activities", token=token)
    
    activities = resp.get("activities", [])
    if args.json:
        print(json.dumps(activities, indent=2))
    else:
        print(f"{'ID':<10} {'Name':<30} {'Color':<10} {'Integration'}")
        print("-" * 60)
        for act in activities:
            print(f"{act['id']:<10} {act['name'][:28]:<30} {act.get('color', 'N/A'):<10} {act.get('integration', 'none')}")


def cmd_activities_create(args):
    """Create a new activity"""
    token = get_token()
    data = {"name": args.name, "color": args.color}
    if args.integration:
        data["integration"] = args.integration
    
    resp = api_request("POST", "/activities", data, token=token)
    print(json.dumps(resp, indent=2))


def cmd_activities_archive(args):
    """Archive an activity"""
    token = get_token()
    resp = api_request("DELETE", f"/activities/{args.activity_id}", token=token)
    print(f"Activity {args.activity_id} archived")


# ============ Time Entries ============

def cmd_entries_list(args):
    """List time entries in date range"""
    token = get_token()
    
    # Default: today
    if args.start:
        start = datetime.strptime(args.start, "%Y-%m-%d")
    else:
        start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    
    if args.end:
        end = datetime.strptime(args.end, "%Y-%m-%d")
    else:
        end = start + timedelta(days=1)
    
    # API expects ISO format with timezone
    start_str = start.strftime("%Y-%m-%dT%H:%M:%S.000")
    end_str = end.strftime("%Y-%m-%dT%H:%M:%S.000")
    
    resp = api_request("GET", f"/time-entries/{start_str}/{end_str}", token=token)
    
    entries = resp.get("timeEntries", [])
    if args.json:
        print(json.dumps(entries, indent=2))
    else:
        total_seconds = 0
        print(f"{'Activity':<25} {'Start':<20} {'Duration':<12} {'Note'}")
        print("-" * 80)
        for entry in entries:
            activity = entry.get("activity", {}).get("name", "Unknown")[:23]
            start_time = entry.get("duration", {}).get("startedAt", "")[:19].replace("T", " ")
            
            # Calculate duration
            started = entry.get("duration", {}).get("startedAt", "")
            stopped = entry.get("duration", {}).get("stoppedAt", "")
            if started and stopped:
                try:
                    s = datetime.fromisoformat(started.replace("Z", "+00:00"))
                    e = datetime.fromisoformat(stopped.replace("Z", "+00:00"))
                    dur_sec = (e - s).total_seconds()
                    total_seconds += dur_sec
                    dur_str = f"{int(dur_sec//3600)}h {int((dur_sec%3600)//60)}m"
                except:
                    dur_str = "N/A"
            else:
                dur_str = "ongoing"
            
            note = entry.get("note", {}).get("text", "")[:20] if entry.get("note") else ""
            print(f"{activity:<25} {start_time:<20} {dur_str:<12} {note}")
        
        print("-" * 80)
        print(f"Total: {int(total_seconds//3600)}h {int((total_seconds%3600)//60)}m")


def cmd_entries_create(args):
    """Create a time entry"""
    token = get_token()
    
    data = {
        "activityId": args.activity_id,
        "startedAt": args.start,
        "stoppedAt": args.end
    }
    if args.note:
        data["note"] = {"text": args.note}
    
    resp = api_request("POST", "/time-entries", data, token=token)
    print(json.dumps(resp, indent=2))


def cmd_entries_delete(args):
    """Delete a time entry"""
    token = get_token()
    api_request("DELETE", f"/time-entries/{args.entry_id}", token=token)
    print(f"Time entry {args.entry_id} deleted")


# ============ Current Tracking ============

def cmd_tracking_status(args):
    """Get current tracking status"""
    token = get_token()
    resp = api_request("GET", "/tracking", token=token)
    
    current = resp.get("currentTracking")
    if current:
        activity = current.get("activity", {}).get("name", "Unknown")
        started = current.get("startedAt", "")[:19].replace("T", " ")
        note = current.get("note", {}).get("text", "") if current.get("note") else ""
        print(f"Currently tracking: {activity}")
        print(f"Started: {started}")
        if note:
            print(f"Note: {note}")
    else:
        print("Not currently tracking")
    
    if args.json:
        print(json.dumps(resp, indent=2))


def cmd_tracking_start(args):
    """Start tracking an activity"""
    token = get_token()
    
    started_at = args.start or datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.000")
    data = {"startedAt": started_at}
    
    resp = api_request("POST", f"/tracking/{args.activity_id}/start", data, token=token)
    print(f"Started tracking activity {args.activity_id}")
    if args.json:
        print(json.dumps(resp, indent=2))


def cmd_tracking_stop(args):
    """Stop current tracking"""
    token = get_token()
    
    # First get current tracking to find activity ID
    current = api_request("GET", "/tracking", token=token)
    tracking = current.get("currentTracking")
    
    if not tracking:
        print("Not currently tracking anything")
        return
    
    activity_id = tracking.get("activity", {}).get("id")
    stopped_at = args.end or datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.000")
    
    data = {"stoppedAt": stopped_at}
    resp = api_request("POST", f"/tracking/{activity_id}/stop", data, token=token)
    print(f"Stopped tracking")
    if args.json:
        print(json.dumps(resp, indent=2))


# ============ Reports ============

def cmd_report(args):
    """Generate report for date range"""
    token = get_token()
    
    if args.start:
        start = datetime.strptime(args.start, "%Y-%m-%d")
    else:
        start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=7)
    
    if args.end:
        end = datetime.strptime(args.end, "%Y-%m-%d")
    else:
        end = datetime.now()
    
    start_ts = start.strftime("%Y-%m-%dT%H:%M:%S.000")
    end_ts = end.strftime("%Y-%m-%dT%H:%M:%S.000")
    
    resp = api_request("GET", f"/report/{start_ts}/{end_ts}", token=token)
    
    if args.json:
        print(json.dumps(resp, indent=2))
    else:
        # Summary by activity
        entries = resp.get("timeEntries", [])
        by_activity = {}
        
        for entry in entries:
            act_name = entry.get("activity", {}).get("name", "Unknown")
            started = entry.get("duration", {}).get("startedAt", "")
            stopped = entry.get("duration", {}).get("stoppedAt", "")
            
            if started and stopped:
                try:
                    s = datetime.fromisoformat(started.replace("Z", "+00:00"))
                    e = datetime.fromisoformat(stopped.replace("Z", "+00:00"))
                    dur_sec = (e - s).total_seconds()
                    by_activity[act_name] = by_activity.get(act_name, 0) + dur_sec
                except:
                    pass
        
        print(f"Report: {start.date()} to {end.date()}")
        print("-" * 50)
        total = 0
        for act, secs in sorted(by_activity.items(), key=lambda x: -x[1]):
            hours = secs / 3600
            total += hours
            print(f"{act:<35} {hours:>6.1f}h")
        print("-" * 50)
        print(f"{'Total':<35} {total:>6.1f}h")


# ============ Tags ============

def cmd_tags_list(args):
    """List all tags and mentions"""
    token = get_token()
    resp = api_request("GET", "/tags-and-mentions", token=token)
    
    if args.json:
        print(json.dumps(resp, indent=2))
    else:
        tags = resp.get("tags", [])
        mentions = resp.get("mentions", [])
        
        print("Tags:")
        for tag in tags:
            print(f"  #{tag.get('key', '')} - {tag.get('label', '')}")
        
        print("\nMentions:")
        for mention in mentions:
            print(f"  @{mention.get('key', '')} - {mention.get('label', '')}")


# ============ Main ============

def main():
    parser = argparse.ArgumentParser(description="EARLY (Timeular) API Client")
    parser.add_argument("--json", action="store_true", help="Output raw JSON")
    subparsers = parser.add_subparsers(dest="command", help="Commands")
    
    # Auth
    p = subparsers.add_parser("auth", help="Test authentication")
    p.set_defaults(func=cmd_auth_test)
    
    # Activities
    p = subparsers.add_parser("activities", help="List activities")
    p.set_defaults(func=cmd_activities_list)
    
    p = subparsers.add_parser("activity-create", help="Create activity")
    p.add_argument("name", help="Activity name")
    p.add_argument("--color", default="#4CAF50", help="Color hex code")
    p.add_argument("--integration", help="Integration name")
    p.set_defaults(func=cmd_activities_create)
    
    p = subparsers.add_parser("activity-archive", help="Archive activity")
    p.add_argument("activity_id", help="Activity ID")
    p.set_defaults(func=cmd_activities_archive)
    
    # Time entries
    p = subparsers.add_parser("entries", help="List time entries")
    p.add_argument("--start", help="Start date (YYYY-MM-DD)")
    p.add_argument("--end", help="End date (YYYY-MM-DD)")
    p.set_defaults(func=cmd_entries_list)
    
    p = subparsers.add_parser("entry-create", help="Create time entry")
    p.add_argument("activity_id", help="Activity ID")
    p.add_argument("start", help="Start time (ISO format)")
    p.add_argument("end", help="End time (ISO format)")
    p.add_argument("--note", help="Note text")
    p.set_defaults(func=cmd_entries_create)
    
    p = subparsers.add_parser("entry-delete", help="Delete time entry")
    p.add_argument("entry_id", help="Entry ID")
    p.set_defaults(func=cmd_entries_delete)
    
    # Tracking
    p = subparsers.add_parser("status", help="Current tracking status")
    p.set_defaults(func=cmd_tracking_status)
    
    p = subparsers.add_parser("start", help="Start tracking")
    p.add_argument("activity_id", help="Activity ID")
    p.add_argument("--start", help="Start time (ISO format, default: now)")
    p.set_defaults(func=cmd_tracking_start)
    
    p = subparsers.add_parser("stop", help="Stop tracking")
    p.add_argument("--end", help="End time (ISO format, default: now)")
    p.set_defaults(func=cmd_tracking_stop)
    
    # Reports
    p = subparsers.add_parser("report", help="Generate report")
    p.add_argument("--start", help="Start date (YYYY-MM-DD)")
    p.add_argument("--end", help="End date (YYYY-MM-DD)")
    p.set_defaults(func=cmd_report)
    
    # Tags
    p = subparsers.add_parser("tags", help="List tags and mentions")
    p.set_defaults(func=cmd_tags_list)
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    args.func(args)


if __name__ == "__main__":
    main()
