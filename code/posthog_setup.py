"""Connect PostHog from ONE personal key, switch on what the commands need, and read it back.

    python3 code/posthog_setup.py --connect --key phx_...   # one key in: finds the region, the project, its id and project key; writes .env and website/.env.local
    python3 code/posthog_setup.py --connect --project 123   # more than one project on the account: pick it by id
    python3 code/posthog_setup.py --list            # who am I, and every project this key can see: name · id · key
    python3 code/posthog_setup.py --show            # what is on right now
    python3 code/posthog_setup.py --enable          # replay (all sessions, inputs masked), heat maps, dead clicks, console logs
    python3 code/posthog_setup.py --dashboard       # one dashboard: leads by day, the form funnel, calls by source. Made once, found after.
    python3 code/posthog_setup.py --check-dupes     # any event fired twice in one session in the last 30 minutes = a bug
    python3 code/posthog_setup.py --write-env       # put the project key into website/.env.local (--connect does this too)

Flags run in that order when combined: `--connect --key phx_... --enable --dashboard` is step 0 in one line.
Every flag that changes something stamps code/cache/setup.json and rewrites CLAUDE.md "## My setup" through setup_check.py,
so the block is never hand-edited and the 30-day skip gate reads a date code wrote.
Nothing here touches the website's code. The snippet is in website/components/posthog/PostHogProvider.tsx; this
flips the project-side toggles so recordings and heat maps are accepted and stored.
Endpoints: settings are PATCHed at /api/organizations/<org>/projects/<id>/ (the documented path) with the
legacy /api/projects/<id>/ tried first. Field names and types are PostHog's OpenAPI schema, September 2026.
Personal key scopes: user:read project:read project:write action:write insight:write dashboard:write query:read
feature_flag:write experiment:write session_recording:read session_recording_playlist:write - or "All access".
"""
import os
import re
import shutil
import sys

import requests

import _posthog as ph
import setup_check as sc

HOSTS = ("https://us.posthog.com", "https://eu.posthog.com")
ENV = os.path.join(ph.ROOT, ".env")
ENV_LOCAL = os.path.join(ph.ROOT, "website", ".env.local")

WANT = {
    "session_recording_opt_in": True,
    "session_recording_sample_rate": "1.00",
    "session_recording_minimum_duration_milliseconds": 2000,
    "session_recording_masking_config": {"maskAllInputs": True, "maskTextSelector": "a[href^='tel:'], .phone, [data-ph-mask]"},
    "session_replay_config": {"record_canvas": False},
    "heatmaps_opt_in": True,
    "capture_dead_clicks": True,
    "autocapture_opt_out": False,
    "capture_console_log_opt_in": True,
    "capture_performance_opt_in": True,
}
SHOW = list(WANT) + ["recording_domains", "session_recording_url_trigger_config", "autocapture_exceptions_opt_in", "timezone"]


def set_env(path, values, example=None):
    """Write key=value lines into an env file, keeping every other line. Made from its example when missing."""
    if not os.path.exists(path) and example and os.path.exists(example):
        shutil.copy(example, path)
    lines = open(path).read().splitlines() if os.path.exists(path) else []
    out, done = [], set()
    for line in lines:
        key = line.split("=", 1)[0].strip() if "=" in line and not line.lstrip().startswith("#") else None
        if key in values:
            out.append(f"{key}={values[key]}")
            done.add(key)
        else:
            out.append(line)
    out += [f"{k}={v}" for k, v in values.items() if k not in done]
    open(path, "w").write("\n".join(out).rstrip("\n") + "\n")


def whoami(key):
    """Try POSTHOG_API_HOST if set, then the US cloud, then the EU cloud. Returns (host, /api/users/@me/)."""
    first = os.environ.get("POSTHOG_API_HOST", "").rstrip("/")
    hosts = ([first] if first else []) + [h for h in HOSTS if h != first]
    last = ""
    for host in hosts:
        try:
            r = requests.get(f"{host}/api/users/@me/", headers={"Authorization": f"Bearer {key}"}, timeout=30)
        except requests.RequestException as e:
            last = f"{host}: {e}"
            continue
        if r.status_code == 200:
            return host, r.json()
        last = f"{host}: {r.status_code} {r.text[:120]}"
    sys.exit(f"PostHog did not accept the key ({last}). It has to be a personal API key (phx_...), copied whole, with user:read at least.")


def site_url_from_config():
    path = os.path.join(ph.ROOT, "website", "lib", "site.config.ts")
    if not os.path.exists(path):
        return ""
    m = re.search(r'\burl:\s*"(https?://[^"]+)"', open(path).read())
    url = m.group(1).rstrip("/") if m else ""
    return "" if "example.com" in url else url


def connect(key="", project=""):
    """One key in, everything else out: region, project, ids, both env files. Prints what it found."""
    key = key or ph.PERSONAL_KEY
    if not key:
        sys.exit("No personal API key. `python3 code/posthog_setup.py --connect --key phx_...` - PostHog > Settings > Personal API keys, All access.")
    host, me = whoami(key)
    org = me.get("organization") or {}
    team = me.get("team") or {}
    headers = {"Authorization": f"Bearer {key}"}
    projects = []
    if org.get("id"):
        r = requests.get(f"{host}/api/organizations/{org['id']}/projects/", headers=headers, params={"limit": 100}, timeout=30)
        if r.status_code == 200:
            projects = r.json().get("results", [])
    chosen = next((p for p in projects if str(p.get("id")) == str(project)), None) if project else None
    if project and not chosen:
        sys.exit(f"No project with id {project} on this account. `--list` prints them.")
    chosen = chosen or next((p for p in projects if p.get("id") == team.get("id")), None) or team
    if chosen.get("id") and not chosen.get("api_token"):
        r = requests.get(f"{host}/api/projects/{chosen['id']}/", headers=headers, timeout=30)
        if r.status_code == 200:
            chosen = r.json()
    if not chosen.get("id") or not chosen.get("api_token"):
        sys.exit("The key logs in but cannot read a project. Give it project:read (or All access) and run --connect again.")
    region = "eu" if "eu.posthog.com" in host else "us"
    ingest = f"https://{region}.i.posthog.com"
    site = os.environ.get("SITE_BASE_URL", "").strip() or site_url_from_config()
    values = {"POSTHOG_PERSONAL_API_KEY": key, "POSTHOG_PROJECT_ID": str(chosen["id"]), "POSTHOG_API_HOST": host,
              "NEXT_PUBLIC_POSTHOG_KEY": chosen["api_token"], "NEXT_PUBLIC_POSTHOG_HOST": ingest}
    if site:
        values["SITE_BASE_URL"] = site
    set_env(ENV, values, example=os.path.join(ph.ROOT, ".env.example"))
    set_env(ENV_LOCAL, {"NEXT_PUBLIC_POSTHOG_KEY": chosen["api_token"], "NEXT_PUBLIC_POSTHOG_HOST": ingest},
            example=os.path.join(ph.ROOT, "website", ".env.local.example"))
    os.environ.update(values)
    ph.API_HOST, ph.PERSONAL_KEY, ph.PROJECT_ID, ph.PROJECT_KEY = host, key, str(chosen["id"]), chosen["api_token"]
    print(f"Connected · {me.get('email')} · project \"{chosen.get('name')}\" · id {chosen['id']} · {region.upper()} cloud")
    print(f"Wrote .env and website/.env.local · project key {chosen['api_token'][:8]}... · recordings limited to {site or 'nothing yet: set SITE_BASE_URL in .env'}")
    for p in [p for p in projects if p.get("id") != chosen.get("id")]:
        print(f"- also on this account: {p.get('name')} · id {p.get('id')} · `--connect --project {p.get('id')}` to use it instead")
    d = sc.load()
    d.update({"connected_at": __import__("datetime").date.today().isoformat(), "project_id": str(chosen["id"]),
              "region": region.upper(), "site": site or d.get("site", "")})
    sc.save(d)
    sc.write_setup()
    print("Next: `python3 code/dev_server.py --restart` so Next reads the key, then `python3 code/check_tracking.py <url>`.")


def me():
    return ph.get("/api/users/@me/")


def org_id():
    m = me()
    return (m.get("organization") or {}).get("id") or ""


def project_paths():
    ph.need("POSTHOG_PROJECT_ID")
    return [f"/api/projects/{ph.PROJECT_ID}/", f"/api/organizations/{org_id()}/projects/{ph.PROJECT_ID}/"]


def read_project():
    for path in project_paths():
        st, out = ph.call("GET", path, soft=True)
        if st == 200 and isinstance(out, dict):
            return out, path
    sys.exit("Could not read the project. Check POSTHOG_PROJECT_ID and that the key has project:read.")


def patch_project(body):
    last = None
    for path in project_paths():
        st, out = ph.call("PATCH", path, body, soft=True)
        if st == 200:
            return out
        last = (st, out)
    sys.exit(f"PostHog rejected the settings change: {last}")


def list_projects():
    m = me()
    team = m.get("team") or {}
    print(f"You: {m.get('email')} · current project \"{team.get('name')}\" · id {team.get('id')} · key {str(team.get('api_token', ''))[:8]}...")
    org = m.get("organization") or {}
    out = ph.get(f"/api/organizations/{org.get('id')}/projects/", limit=100)
    for p in out.get("results", []):
        print(f"- {p.get('name')} · id {p.get('id')} · key {str(p.get('api_token', ''))[:8]}... · {p.get('timezone')}")
    print("\nPut the id in .env as POSTHOG_PROJECT_ID and the key in website/.env.local as NEXT_PUBLIC_POSTHOG_KEY.")


def show():
    p, _ = read_project()
    print(f"Project: {p.get('name')} · id {p.get('id')} · key {str(p.get('api_token', ''))[:8]}...")
    for k in SHOW:
        if k in p:
            print(f"- {k}: {p[k]}")
    print(f"\nOpen it: {ph.ui('settings/project')}")
    return p


def enable():
    before, _ = read_project()
    body = {k: v for k, v in WANT.items() if before.get(k) != v}
    site = os.environ.get("SITE_BASE_URL", "").rstrip("/")
    local = f"http://localhost:{os.environ.get('DEV_PORT', '3000') or '3000'}"
    if site and site not in (before.get("recording_domains") or []):
        body["recording_domains"] = sorted(set((before.get("recording_domains") or []) + [site]))
    # app_urls is the toolbar allow-list. PostHog's heat map viewer loads the page in an iframe and refuses
    # any URL that is not on it, so the screen stays blank however much data there is. Both URLs go on.
    want_urls = [u for u in (local, site) if u]
    have_urls = before.get("app_urls") or []
    if any(u not in have_urls for u in want_urls):
        body["app_urls"] = have_urls + [u for u in want_urls if u not in have_urls]
    if not body:
        if not sc.load().get("masking_enabled_at"):
            sc.stamp("masking_enabled_at")
            sc.write_setup()
        print("Already on. Nothing to change.")
        return
    patch_project(body)
    after, _ = read_project()
    stuck = [k for k, v in WANT.items() if after.get(k) != v]
    print("Switched on: " + ", ".join(k for k in body if k not in stuck))
    if stuck:
        print("Did not stick (a scope or a renamed field - read the message above): " + ", ".join(stuck))
        sys.exit(1)
    if not sc.load().get("masking_enabled_at"):
        sc.stamp("masking_enabled_at")
    sc.write_setup()
    if site:
        print(f"Recordings limited to {site} so localhost and staging do not burn the free 5,000 a month.")
    if body.get("app_urls"):
        print("Toolbar allow-list now covers: " + ", ".join(body["app_urls"]) + " (without this the heat map viewer shows a blank page)")
    print(f"Replay: {ph.ui('replay/home')}\nHeat maps: {ph.ui('heatmaps')} (about 2,000 pageviews per URL before the picture means anything)")


def dashboard():
    st, found = ph.call("GET", "dashboards/", params={"search": "See your visitors", "limit": 20}, soft=True)
    if st == 200 and isinstance(found, dict):
        for d in found.get("results", []):
            if d.get("name") == "See your visitors" and not d.get("deleted"):
                url = ph.ui("dashboard/" + str(d["id"]))
                sc.stamp("dashboard_url", url)
                sc.write_setup()
                print(f"Dashboard exists: {url}")
                return
    st, d = ph.call("POST", "dashboards/", {"name": "See your visitors", "description": "Made by /analytics", "pinned": True, "tags": ["cro"]}, soft=True)
    if st not in (200, 201):
        sys.exit(f"Could not create the dashboard: {st} {str(d)[:200]}")
    did = d["id"]
    insights = [
        ("Leads by day", {"kind": "TrendsQuery", "dateRange": {"date_from": "-30d"}, "interval": "day", "series": [
            {"kind": "EventsNode", "event": "lead_form_submitted", "math": "dau"},
            {"kind": "EventsNode", "event": "call_clicked", "math": "dau"},
            {"kind": "EventsNode", "event": "text_clicked", "math": "dau"},
            {"kind": "EventsNode", "event": "booking_made", "math": "dau"}]}),
        ("Page to form to lead", {"kind": "FunnelsQuery", "dateRange": {"date_from": "-30d"}, "series": [
            {"kind": "EventsNode", "event": "$pageview"},
            {"kind": "EventsNode", "event": "lead_form_started"},
            {"kind": "EventsNode", "event": "lead_form_submitted"}]}),
        ("Calls by button", {"kind": "TrendsQuery", "dateRange": {"date_from": "-30d"}, "interval": "week",
                             "series": [{"kind": "EventsNode", "event": "call_clicked", "math": "total"}],
                             "breakdownFilter": {"breakdown": "source", "breakdown_type": "event"}}),
        ("Rage and dead clicks", {"kind": "TrendsQuery", "dateRange": {"date_from": "-30d"}, "interval": "day", "series": [
            {"kind": "EventsNode", "event": "$rageclick", "math": "total"},
            {"kind": "EventsNode", "event": "$dead_click", "math": "total"}]}),
    ]
    for name, src in insights:
        st, out = ph.call("POST", "insights/", {"name": name, "dashboards": [did], "query": {"kind": "InsightVizNode", "source": src}}, soft=True)
        print(f"- {name}: {'ok' if st in (200, 201) else str(out)[:120]}")
    sc.stamp("dashboard_url", ph.ui("dashboard/" + str(did)))
    sc.write_setup()
    print(f"Dashboard: {ph.ui('dashboard/' + str(did))}")


def check_dupes():
    cols, rows = ph.hogql("""select event, $session_id as s, count() as c from events
        where timestamp > now() - interval 30 minute
          and event in ('lead_form_submitted', 'lead_received', 'call_clicked', 'text_clicked', 'booking_made')
        group by event, s having c > 1 limit 50""", "dupes")
    if rows:
        print("Fired more than once in one session (a double count):")
        for r in rows:
            print(f"- {r[0]} · session {str(r[1])[:8]} · {r[2]} times")
        sys.exit(1)
    print("No duplicates in the last 30 minutes.")


def write_env():
    ph.need("NEXT_PUBLIC_POSTHOG_KEY")
    path = os.path.join(ph.ROOT, "website", ".env.local")
    lines = []
    if os.path.exists(path):
        lines = [l for l in open(path).read().splitlines() if not l.startswith(("NEXT_PUBLIC_POSTHOG_KEY=", "NEXT_PUBLIC_POSTHOG_HOST="))]
    host = os.environ.get("NEXT_PUBLIC_POSTHOG_HOST", "https://us.i.posthog.com")
    lines += [f"NEXT_PUBLIC_POSTHOG_KEY={ph.PROJECT_KEY}", f"NEXT_PUBLIC_POSTHOG_HOST={host}"]
    open(path, "w").write("\n".join(lines) + "\n")
    print(f"Wrote website/.env.local · key {ph.PROJECT_KEY[:8]}... · host {host}. Restart `npm run dev`.")


if __name__ == "__main__":
    a = sys.argv[1:] or ["--show"]

    def val(flag):
        return a[a.index(flag) + 1] if flag in a and a.index(flag) + 1 < len(a) else ""

    if "--connect" in a: connect(val("--key"), val("--project"))
    if "--list" in a: list_projects()
    if "--enable" in a: enable()
    if "--show" in a: show()
    if "--dashboard" in a: dashboard()
    if "--check-dupes" in a: check_dupes()
    if "--write-env" in a: write_env()
