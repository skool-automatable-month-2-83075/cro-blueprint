"""The one PostHog client every script here uses.

Reads .env at the repo root:
  POSTHOG_PERSONAL_API_KEY  phx_...  Settings > Personal API keys. "All access", or these scopes:
                                     user:read project:read project:write action:write insight:write dashboard:write
                                     feature_flag:write experiment:write session_recording:read
                                     session_recording_playlist:write query:read
  POSTHOG_PROJECT_ID        the number in every PostHog URL: app.posthog.com/project/<id>/...
  POSTHOG_API_HOST          https://us.posthog.com (default) or https://eu.posthog.com
  NEXT_PUBLIC_POSTHOG_KEY   phc_...  the project key the browser uses (also in website/.env.local)

Every function raises SystemExit with a plain sentence when something is missing, so a member
sees "POSTHOG_PROJECT_ID is missing from .env" and not a stack trace.
"""
import json
import os
import sys
import time

import requests
from dotenv import load_dotenv

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(ROOT, ".env"))
load_dotenv(os.path.join(ROOT, "website", ".env.local"))

API_HOST = os.environ.get("POSTHOG_API_HOST", "https://us.posthog.com").rstrip("/")
PERSONAL_KEY = os.environ.get("POSTHOG_PERSONAL_API_KEY", "")
PROJECT_ID = os.environ.get("POSTHOG_PROJECT_ID", "")
PROJECT_KEY = os.environ.get("NEXT_PUBLIC_POSTHOG_KEY", "")
CACHE = os.path.join(ROOT, "code", "cache")
os.makedirs(CACHE, exist_ok=True)


def need(*names):
    missing = [n for n in names if not os.environ.get(n)]
    if missing:
        sys.exit(f"{', '.join(missing)} missing from .env - `python3 code/setup_check.py` says what to do about it.")


def _headers():
    need("POSTHOG_PERSONAL_API_KEY")
    return {"Authorization": f"Bearer {PERSONAL_KEY}", "Content-Type": "application/json"}


def call(method, path, body=None, params=None, ok=(200, 201), soft=False):
    """One API call. `path` is absolute (/api/...) or project-relative (session_recordings/).
    soft=True returns (status, json_or_text) instead of exiting on an error."""
    if not path.startswith("/api/"):
        need("POSTHOG_PROJECT_ID")
        path = f"/api/projects/{PROJECT_ID}/{path.lstrip('/')}"
    url = API_HOST + path
    r, last = None, ""
    for attempt in range(3):
        try:
            r = requests.request(method, url, headers=_headers(), json=body, params=params, timeout=60)
        except requests.RequestException as e:
            # a dropped connection or a timeout is the commonest real failure; retry, then say it in a sentence
            last = f"{e.__class__.__name__}"
            time.sleep(1 + attempt * 2)
            continue
        if r.status_code == 429 or r.status_code >= 500:
            time.sleep(2 + attempt * 3)
            continue
        break
    if r is None:
        msg = f"PostHog did not answer at {API_HOST} ({last}). Check the connection, then run the command again."
        if soft:
            return 0, msg
        sys.exit(msg)
    if soft:
        try:
            return r.status_code, (r.json() if r.text else {})
        except ValueError:
            return r.status_code, r.text[:400]
    if r.status_code not in ok:
        detail = r.text[:400]
        sys.exit(f"PostHog {method} {path} answered {r.status_code}: {detail}")
    return r.json() if r.text else {}


def get(path, **params):
    return call("GET", path, params=params or None)


def post(path, body):
    return call("POST", path, body)


def patch(path, body):
    return call("PATCH", path, body)


def hogql(query, name="query"):
    """Run a HogQL query, return (columns, rows). Cached copies land in code/cache for debugging."""
    out = post("query/", {"query": {"kind": "HogQLQuery", "query": query}})
    cols = out.get("columns") or []
    rows = out.get("results") or []
    with open(os.path.join(CACHE, f"hogql-{name}.json"), "w") as f:
        json.dump({"query": query, "columns": cols, "rows": rows[:2000]}, f, indent=1, default=str)
    return cols, rows


def rows_as_dicts(cols, rows):
    return [dict(zip(cols, r)) for r in rows]


def ui(path=""):
    """A clickable PostHog URL for the project."""
    need("POSTHOG_PROJECT_ID")
    return f"{API_HOST}/project/{PROJECT_ID}/{path.lstrip('/')}"


def sql_str(s):
    return "'" + str(s).replace("\\", "\\\\").replace("'", "\\'") + "'"
