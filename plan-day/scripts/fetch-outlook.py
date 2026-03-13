#!/usr/bin/env python3
"""Fetch today's Outlook calendar events via Microsoft Graph API."""

import json
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import msal
import requests

CONFIG_DIR = Path.home() / ".config" / "plan-day"
CONFIG_FILE = CONFIG_DIR / "outlook-config.json"
TOKEN_CACHE_FILE = CONFIG_DIR / "tokens.json"

SCOPES = ["Calendars.Read"]

if not CONFIG_FILE.exists():
    raise RuntimeError(
        f"Outlook config not found at {CONFIG_FILE}. "
        "Create it with application_id and tenant_id from your Entra app registration."
    )

config = json.loads(CONFIG_FILE.read_text())
client_id = config["application_id"]
tenant_id = config["tenant_id"]
authority = f"https://login.microsoftonline.com/{tenant_id}"

# Set up token cache with persistence
cache = msal.SerializableTokenCache()
if TOKEN_CACHE_FILE.exists():
    cache.deserialize(TOKEN_CACHE_FILE.read_text())


def _save_cache():
    if cache.has_state_changed:
        TOKEN_CACHE_FILE.write_text(cache.serialize())


app = msal.PublicClientApplication(client_id, authority=authority, token_cache=cache)

# Try silent auth first (cached token / refresh token)
accounts = app.get_accounts()
result = None
if accounts:
    result = app.acquire_token_silent(SCOPES, account=accounts[0])

if not result or "access_token" not in result:
    # Fall back to device code flow
    flow = app.initiate_device_flow(scopes=SCOPES)
    if "user_code" not in flow:
        raise RuntimeError(f"Device flow initiation failed: {flow}")
    print(flow["message"], flush=True)
    result = app.acquire_token_by_device_flow(flow)

_save_cache()

if "access_token" not in result:
    raise RuntimeError(f"Authentication failed: {result.get('error_description', result)}")

access_token = result["access_token"]

# Determine date range
target_date = date.fromisoformat(sys.argv[1]) if len(sys.argv) > 1 else date.today()
start = datetime.combine(target_date, datetime.min.time(), tzinfo=timezone.utc)
end = start + timedelta(days=1)

response = requests.get(
    "https://graph.microsoft.com/v1.0/me/calendarview",
    params={
        "startDateTime": start.isoformat(),
        "endDateTime": end.isoformat(),
        "$orderby": "start/dateTime",
        "$select": "subject,start,end,isAllDay,location,isCancelled",
    },
    headers={"Authorization": f"Bearer {access_token}"},
)
response.raise_for_status()

events = response.json().get("value", [])
if not events:
    print(f"No calendar events for {target_date}.")
    sys.exit(0)

for event in events:
    if event.get("isCancelled"):
        continue
    subject = event.get("subject", "(no subject)")
    if event.get("isAllDay"):
        print(f"  [all day]    {subject}")
    else:
        start_time = datetime.fromisoformat(event["start"]["dateTime"]).strftime("%H:%M")
        end_time = datetime.fromisoformat(event["end"]["dateTime"]).strftime("%H:%M")
        location = event.get("location", {}).get("displayName", "")
        loc_str = f" @ {location}" if location else ""
        print(f"  {start_time}-{end_time}  {subject}{loc_str}")
