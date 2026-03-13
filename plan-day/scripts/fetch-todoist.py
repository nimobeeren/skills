#!/usr/bin/env python3
"""Fetch today's Todoist tasks via API v1."""

import os
import sys
from datetime import date

import requests

token = os.environ.get("TODOIST_API_TOKEN")
if not token:
    raise RuntimeError("TODOIST_API_TOKEN environment variable is not set")

target_date = sys.argv[1] if len(sys.argv) > 1 else date.today().isoformat()

response = requests.get(
    "https://api.todoist.com/api/v1/tasks/filter",
    params={"query": target_date},
    headers={"Authorization": f"Bearer {token}"},
)
response.raise_for_status()

tasks = response.json().get("results", [])
if not tasks:
    print(f"No tasks found for {target_date}.")
    sys.exit(0)

for task in tasks:
    priority = task.get("priority", 1)
    marker = "!" * (5 - priority) if priority > 1 else ""
    prefix = f"[{marker}] " if marker else "- "
    due = task.get("due", {})
    time_str = ""
    if due and due.get("datetime"):
        time_str = f" (due {due['datetime']})"
    print(f"{prefix}{task['content']}{time_str}")
