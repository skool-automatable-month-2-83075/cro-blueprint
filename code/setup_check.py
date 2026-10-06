"""The one gate every PostHog command runs first. What is wired and what is not, one line each, on one screen.

    python3 code/setup_check.py --page /lp/<slug>     # every check; exit 0 = go, exit 1 = something to do first (a manual stop is printed in full)
    python3 code/setup_check.py --write-setup         # rewrite only the lines this script owns in CLAUDE.md "## My setup", from code/cache/setup.json
    python3 code/setup_check.py --stamp tracking_verified_at today --page /lp/<slug>   # what check_tracking.py does on ALL PASS

Reads .env, website/.env.local and code/cache/setup.json. Asks nothing itself. When something only a human can do is
missing it prints the PostHog manual stop block from references/posthog-setup.md and
exits 1. The command shows the block, waits, and runs this again when the keys land. A line marked FIX is code's job
and names the script to run. CLAUDE.md "## My setup" is rewritten from setup.json every run, so Claude never edits it by hand.

setup.json: connected_at, project_id, region, dashboard_url, site, masking_enabled_at,
tracking_verified_at, tracking_page. Dates are YYYY-MM-DD. Never a key value.
"""
import argparse
import hashlib
import json
import os
import sys
from datetime import date, timedelta

import requests

import _posthog as ph

SETUP = os.path.join(ph.CACHE, "setup.json")
CLAUDE_MD = os.path.join(ph.ROOT, "CLAUDE.md")
REFERENCE = os.path.join(ph.ROOT, "references", "posthog-setup.md")
ENV_LOCAL = os.path.join(ph.ROOT, "website", ".env.local")
FRESH_DAYS = 30
OWNED = ("PostHog:", "Dashboard:", "Gemini:", "Site:", "Replay masking:", "TRACKING VERIFIED:")  # Gemini: /audit video transcripts only

POSTHOG_STOP = """⛔ MANUAL STOP · PostHog account and key · about three minutes, once
1. Go to posthog.com and sign up. Free. Google login is fastest.
2. Name the project after your site when it asks. US or EU cloud, either works.
3. Settings, Personal API keys, Create personal API key. Name it cro-blueprint. Scopes: All access. Copy it, it starts with phx_ and PostHog shows it once.
4. Paste it here.
The moment it lands I do the rest: the project id and key, the region, replay and heat maps on, the scripts on every page, the tracking test, the dashboard. You never open PostHog again."""

def load():
    try:
        return json.load(open(SETUP))
    except (OSError, ValueError):
        return {}


def save(d):
    os.makedirs(os.path.dirname(SETUP), exist_ok=True)
    json.dump(d, open(SETUP, "w"), indent=1, sort_keys=True)
    return d


def stamp(key, value="today"):
    d = load()
    d[key] = date.today().isoformat() if value == "today" else value
    return save(d)


def fresh(iso, days=FRESH_DAYS):
    try:
        return date.today() - date.fromisoformat(str(iso)[:10]) <= timedelta(days=days)
    except (TypeError, ValueError):
        return False


def pretty(iso):
    try:
        return date.fromisoformat(str(iso)[:10]).strftime("%-d %B %Y")
    except (TypeError, ValueError):
        return str(iso)


def env_value(path, key):
    if not os.path.exists(path):
        return ""
    for line in open(path).read().splitlines():
        if line.startswith(key + "="):
            return line.split("=", 1)[1].split(" #")[0].strip().strip('"')
    return ""


def block(which):
    """The manual stop block in the reference file's own words; the copy above when the file is missing."""
    fallback, marker = POSTHOG_STOP, "⛔ MANUAL STOP · PostHog"
    try:
        lines = open(REFERENCE).read().splitlines()
    except OSError:
        return fallback
    for i, line in enumerate(lines):
        if line.startswith(marker):
            out = []
            for m in lines[i:]:
                if not m.strip():
                    break
                out.append(m)
            return "\n".join(out)
    return fallback


# ---- the checks: each returns (state, text). PASS · FIX (a script fixes it) · STOP (a human) · INFO

def check_posthog(setup):
    key = os.environ.get("POSTHOG_PERSONAL_API_KEY", "")
    if not key:
        return "STOP", "PostHog: no personal API key in .env"
    try:
        r = requests.get(f"{ph.API_HOST}/api/users/@me/", headers={"Authorization": f"Bearer {key}"}, timeout=30)
    except requests.RequestException as e:
        return "FIX", f"PostHog: {ph.API_HOST} did not answer ({e.__class__.__name__}). Check the connection and run this again"
    if r.status_code != 200:
        return "STOP", f"PostHog: the key in .env was refused ({r.status_code}). A new personal key is needed"
    email = (r.json() or {}).get("email", "")
    pid = os.environ.get("POSTHOG_PROJECT_ID", "")
    if not pid or not os.environ.get("NEXT_PUBLIC_POSTHOG_KEY", ""):
        return "FIX", f"PostHog: the key works ({email}) but the project is not written. `python3 code/posthog_setup.py --connect --enable --dashboard`"
    if not env_value(ENV_LOCAL, "NEXT_PUBLIC_POSTHOG_KEY").startswith("phc_"):
        return "FIX", "PostHog: website/.env.local has no project key. `python3 code/posthog_setup.py --connect --enable --dashboard`"
    changed = False
    if not setup.get("connected_at"):
        setup["connected_at"] = date.today().isoformat(); changed = True
    if setup.get("project_id") != pid:
        setup["project_id"] = pid; changed = True
    region = "EU" if "eu.posthog.com" in ph.API_HOST else "US"
    if setup.get("region") != region:
        setup["region"] = region; changed = True
    if changed:
        save(setup)
    return "PASS", f"PostHog: connected as {email}, project {pid} on the {region} cloud"


def check_settings(setup):
    from posthog_setup import WANT
    project = None
    st, out = ph.call("GET", f"/api/projects/{ph.PROJECT_ID}/", soft=True)
    if st == 200 and isinstance(out, dict):
        project = out
    else:
        st2, me = ph.call("GET", "/api/users/@me/", soft=True)
        org = ((me or {}).get("organization") or {}).get("id") if isinstance(me, dict) else None
        if org:
            st, out = ph.call("GET", f"/api/organizations/{org}/projects/{ph.PROJECT_ID}/", soft=True)
            if st == 200 and isinstance(out, dict):
                project = out
    if project is None:
        return "FIX", f"Replay and heat maps: could not read the project ({st}). The key needs project:read. `python3 code/posthog_setup.py --show`"
    off = [k for k, v in WANT.items() if project.get(k) != v]
    if off:
        return "FIX", f"Replay and heat maps: {len(off)} setting(s) off ({', '.join(off[:3])}). `python3 code/posthog_setup.py --enable`"
    if not setup.get("masking_enabled_at"):
        setup["masking_enabled_at"] = date.today().isoformat()
        save(setup)
    site = os.environ.get("SITE_BASE_URL", "").strip().rstrip("/")
    local = f"http://localhost:{os.environ.get('DEV_PORT', '3000') or '3000'}"
    allowed = project.get("app_urls") or []
    missing = [u for u in (local, site) if u and u not in allowed]
    if missing:
        return "FIX", ("Heat map viewer: " + ", ".join(missing) + " is not on PostHog's toolbar allow-list, so the heat map "
                       "page loads blank however much data there is. `python3 code/posthog_setup.py --enable`")
    return "PASS", f"Replay, heat maps, dead clicks and input masking: on since {pretty(setup['masking_enabled_at'])}"


def check_dashboard(setup):
    st, found = ph.call("GET", "dashboards/", params={"search": "See your visitors", "limit": 20}, soft=True)
    if st == 200 and isinstance(found, dict):
        for d in found.get("results", []):
            if d.get("name") == "See your visitors" and not d.get("deleted"):
                url = ph.ui("dashboard/" + str(d["id"]))
                if setup.get("dashboard_url") != url:
                    setup["dashboard_url"] = url
                    save(setup)
                return "PASS", f"Dashboard: {url}"
        return "FIX", "Dashboard: not made yet. `python3 code/posthog_setup.py --dashboard`"
    if st in (401, 403):
        return "FIX", "Dashboard: the key cannot read dashboards (dashboard:read). Make the key All access and run --connect again"
    return "FIX", f"Dashboard: PostHog answered {st}. `python3 code/posthog_setup.py --dashboard`"


def check_site(setup):
    site = os.environ.get("SITE_BASE_URL", "").strip().rstrip("/")
    if not site:
        return "INFO", "Site: SITE_BASE_URL not set. Recordings are limited to nothing yet; set it in .env before the live deploy"
    if setup.get("site") != site:
        setup["site"] = site
        save(setup)
    return "PASS", f"Site: {site}"


def check_tracking(setup, page):
    iso = setup.get("tracking_verified_at")
    if iso and fresh(iso):
        return "PASS", f"TRACKING VERIFIED: {pretty(iso)} on {setup.get('tracking_page') or 'the page'}"
    port = os.environ.get("DEV_PORT", "3000") or "3000"
    target = f"http://localhost:{port}{page}" if page else f"http://localhost:{port}/lp/<slug>"
    when = "never" if not iso else f"last {pretty(iso)}, more than {FRESH_DAYS} days ago"
    return "FIX", f"TRACKING VERIFIED: {when}. `python3 code/check_tracking.py {target}`"


def check_dev_server():
    try:
        import dev_server as ds
    except ImportError:
        return "INFO", "Dev server: code/dev_server.py is missing; start `npm run dev` in website/ yourself"
    h = ds.holder()
    if not h:
        return "INFO", f"Dev server: not running. `python3 code/dev_server.py --start` before the tracking check"
    if not ds.is_ours(h):
        return "INFO", f"Dev server: port {ds.PORT} is held by another folder ({h.get('cwd') or 'unknown'}). Set DEV_PORT in .env"
    if ds.env_newer_than_server(h):
        return "FIX", "Dev server: running with stale keys. `python3 code/dev_server.py --restart`"
    return "PASS", f"Dev server: running at {ds.URL}"


# ---- CLAUDE.md "## My setup", the lines this script owns

def setup_lines(s):
    L = []
    if s.get("connected_at"):
        L.append(f"- PostHog: connected {pretty(s['connected_at'])}")
        if s.get("project_id"):
            L.append(f"  - Project {s['project_id']} on the {s.get('region', 'US')} cloud")
    else:
        L.append("- PostHog: not connected yet")
    L.append(f"- Dashboard: {s['dashboard_url']}" if s.get("dashboard_url") else "- Dashboard: not made yet")
    L.append(f"- Site: {s['site']}" if s.get("site") else "- Site: not set")
    L.append(f"- Replay masking: on since {pretty(s['masking_enabled_at'])}" if s.get("masking_enabled_at") else "- Replay masking: not proven yet")
    tv = s.get("tracking_verified_at")
    L.append(f"- TRACKING VERIFIED: {pretty(tv)} on {s.get('tracking_page') or 'the page'}" if tv else "- TRACKING VERIFIED: never")
    return L


def write_setup():
    s = load()
    text = open(CLAUDE_MD).read() if os.path.exists(CLAUDE_MD) else "# CRO Blueprint Pro\n"
    lines = text.splitlines()
    start = next((i for i, l in enumerate(lines) if l.strip() == "## My setup"), None)
    if start is None:
        lines += ["", "## My setup", "", "Filled by the commands as they run. Nothing here gets asked twice.", ""]
        start = len(lines) - 3
    end = next((i for i in range(start + 1, len(lines)) if lines[i].startswith("## ")), len(lines))
    kept, skip_sub = [], False
    for l in lines[start + 1:end]:
        if l.startswith("- ") and any(l[2:].startswith(o) for o in OWNED):
            skip_sub = True
            continue
        if skip_sub and l.startswith("  "):
            continue
        skip_sub = False
        kept.append(l)
    new = setup_lines(s)
    first_bullet = next((i for i, l in enumerate(kept) if l.startswith("- ")), None)
    if first_bullet is None:
        while kept and not kept[-1].strip():
            kept.pop()
        kept += [""] + new
    else:
        kept = kept[:first_bullet] + new + kept[first_bullet:]
    while kept and not kept[-1].strip():
        kept.pop()
    kept.append("")
    out = lines[:start + 1] + kept + lines[end:]
    open(CLAUDE_MD, "w").write("\n".join(out).rstrip("\n") + "\n")
    return new


def run(page):
    setup = load()
    results = []
    st, text = check_posthog(setup)
    results.append((st, text))
    if st == "PASS":
        results.append(check_settings(setup))
        results.append(check_dashboard(setup))
    results.append(check_site(setup))
    results.append(check_tracking(setup, page))
    results.append(check_dev_server())
    for st, text in results:
        print(f"{st:<5} {text}")
    write_setup()
    stops = [t for s, t in results if s == "STOP"]
    fixes = [t for s, t in results if s == "FIX"]
    if stops:
        print("\nNothing else runs until this lands. Show the member this, in these words, and wait:\n")
        if any(t.startswith("PostHog") for t in stops):
            print(block("posthog") + "\n")
    if fixes:
        print(f"{len(fixes)} thing(s) code fixes before any number is read - run the commands above, then this again.")
    if stops or fixes:
        return 1
    print("READY. Every PostHog command may run.\n")
    print("Where to look in PostHog, when you want to see it yourself:")
    for label, path in (("Heat maps", "heatmaps"), ("Session recordings", "replay/home"), ("Your dashboard", "")):
        print(f"- {label}: {setup.get('dashboard_url') if not path else ph.ui(path)}")
    print("You never have to open these - /analytics reads them for you and writes the answer to a file.")
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--page", default="", help="the page path the tracking check should name, e.g. /lp/drain-cleaning")
    ap.add_argument("--write-setup", action="store_true")
    ap.add_argument("--stamp", nargs=2, metavar=("KEY", "VALUE"), help="write one setup.json key; VALUE 'today' is today's date")
    a = ap.parse_args()
    if a.stamp:
        stamp(a.stamp[0], a.stamp[1])
        if a.stamp[0] == "tracking_verified_at" and a.page:
            stamp("tracking_page", a.page)
        write_setup()
        print(f"Stamped {a.stamp[0]} and rewrote CLAUDE.md \"## My setup\".")
        sys.exit(0)
    if a.write_setup:
        for l in write_setup():
            print(l)
        sys.exit(0)
    sys.exit(run(a.page))
