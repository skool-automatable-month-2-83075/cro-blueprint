"""Start, stop or restart the website's dev server, and say who holds the port. Never opens a window.

    python3 code/dev_server.py --status     # running or not, whose it is, whether website/.env.local changed since it started
    python3 code/dev_server.py --start      # `npm run dev` in website/, in the background, waits until the site answers
    python3 code/dev_server.py --restart    # after a change to website/.env.local (Next reads NEXT_PUBLIC_* once, at start)
    python3 code/dev_server.py --stop

Only ever stops a server whose working directory is THIS repo's website/. The port held by anything
else is reported, never killed. Port: DEV_PORT in .env, default 3000. Log: code/cache/dev-server.log.
Importable: holder(), is_ours(), env_newer_than_server(). Exit 0 = the state asked for is true.
"""
import os
import signal
import subprocess
import sys
import time
from datetime import datetime

import requests

import _posthog as ph  # ROOT and CACHE, and it loads .env

WEBSITE = os.path.join(ph.ROOT, "website")
PORT = int(os.environ.get("DEV_PORT", "3000") or "3000")
URL = f"http://localhost:{PORT}"
LOG = os.path.join(ph.CACHE, "dev-server.log")
ENV_LOCAL = os.path.join(WEBSITE, ".env.local")


def _ps(pid, cols):
    try:
        return subprocess.run(["ps", "-o", cols, "-p", str(pid)], capture_output=True, text=True).stdout.strip()
    except OSError:
        return ""


def _cwd(pid):
    out = subprocess.run(["lsof", "-a", "-p", str(pid), "-d", "cwd", "-Fn"], capture_output=True, text=True).stdout
    for line in out.splitlines():
        if line.startswith("n"):
            return line[1:]
    return ""


def _started(pid):
    try:
        return datetime.strptime(_ps(pid, "lstart="), "%a %b %d %H:%M:%S %Y")
    except ValueError:
        return None


def _same(a, b):
    return os.path.realpath(a or "/nonexistent") == os.path.realpath(b)


def holder():
    """The process listening on the port: {pid, cwd, command, started}, or None."""
    out = subprocess.run(["lsof", "-nP", f"-iTCP:{PORT}", "-sTCP:LISTEN", "-Fp"], capture_output=True, text=True).stdout
    pids = [int(l[1:]) for l in out.splitlines() if l.startswith("p") and l[1:].isdigit()]
    if not pids:
        return None
    pid = pids[0]
    return {"pid": pid, "cwd": _cwd(pid), "command": _ps(pid, "command="), "started": _started(pid)}


def is_ours(h):
    return bool(h) and _same(h["cwd"], WEBSITE)


def _child_env():
    """This process loaded the root .env (via _posthog). Next lets an inherited variable beat website/.env.local,
    so a blank placeholder there (LEAD_WEBHOOK_URL=   # GHL: ...) hid the real webhook and every lead got a 503
    (found 25 September 2026). Drop every key website/.env.local defines, so the website's own file wins."""
    env = dict(os.environ)
    if os.path.exists(ENV_LOCAL):
        for line in open(ENV_LOCAL).read().splitlines():
            key = line.split("=", 1)[0].strip()
            if "=" in line and key and not key.startswith("#"):
                env.pop(key, None)
    return env


def env_newer_than_server(h):
    """True when website/.env.local was written after the server started - it is running with stale keys."""
    if not h or not h.get("started") or not os.path.exists(ENV_LOCAL):
        return False
    return datetime.fromtimestamp(os.path.getmtime(ENV_LOCAL)) > h["started"]


def _chain(pid):
    """The listener plus its parents, while they are node / npm / next processes working in website/."""
    pids, seen = [], set()
    while pid and pid > 1 and pid not in seen:
        seen.add(pid)
        cmd = _ps(pid, "command=")
        if not any(w in cmd for w in ("node", "npm", "next")) or not _same(_cwd(pid), WEBSITE):
            break
        pids.append(pid)
        ppid = _ps(pid, "ppid=")
        pid = int(ppid) if ppid.isdigit() else 0
    return pids


def _answers():
    try:
        return requests.get(URL + "/", timeout=10).status_code < 500
    except requests.RequestException:
        return False


def status():
    h = holder()
    if not h:
        print(f"Not running. Nothing listens on port {PORT}.")
        return False
    who = "this repo's website/" if is_ours(h) else f"another folder: {h['cwd'] or 'unknown'}"
    when = h["started"].strftime("%-d %B %Y %H:%M") if h["started"] else "an unknown time"
    print(f"Running · pid {h['pid']} · {who} · since {when} · {URL}")
    if is_ours(h) and env_newer_than_server(h):
        print("website/.env.local changed after the server started - it runs with stale keys. `python3 code/dev_server.py --restart`.")
        return False
    return is_ours(h)


def stop():
    h = holder()
    if not h:
        print(f"Nothing listens on port {PORT}.")
        return True
    if not is_ours(h):
        print(f"Port {PORT} is held by another folder ({h['cwd'] or 'unknown'}, pid {h['pid']}). Not touching it - stop it yourself, or set DEV_PORT in .env.")
        return False
    pids = _chain(h["pid"])
    for sig in (signal.SIGTERM, signal.SIGKILL):
        for pid in pids:
            try:
                os.kill(pid, sig)
            except ProcessLookupError:
                pass
        for _ in range(20):
            if not holder():
                print(f"Stopped pid {', '.join(map(str, pids))}.")
                return True
            time.sleep(0.5)
    print(f"Could not free port {PORT}.")
    return False


def start():
    h = holder()
    if h and is_ours(h):
        if env_newer_than_server(h):
            print("Already running, but website/.env.local changed after it started. Restarting.")
            return stop() and start()
        print(f"Already running · pid {h['pid']} · {URL}")
        return True
    if h:
        print(f"Port {PORT} is held by another folder ({h['cwd'] or 'unknown'}, pid {h['pid']}). Stop it, or set DEV_PORT in .env and use that port.")
        return False
    if not os.path.exists(os.path.join(WEBSITE, "node_modules", "next")):
        print("website/node_modules is missing. Running `npm install` first.")
        if subprocess.run(["npm", "install"], cwd=WEBSITE).returncode != 0:
            print("npm install failed - read the lines above.")
            return False
    log = open(LOG, "a")
    log.write(f"\n--- start {datetime.now():%Y-%m-%d %H:%M:%S} ---\n")
    log.flush()
    p = subprocess.Popen(["npm", "run", "dev", "--", "-p", str(PORT)], cwd=WEBSITE, stdout=log, stderr=subprocess.STDOUT,
                         stdin=subprocess.DEVNULL, start_new_session=True, env=_child_env())
    for _ in range(90):
        if _answers():
            h = holder()
            print(f"Running · pid {h['pid'] if h else p.pid} · {URL} · log code/cache/dev-server.log")
            return True
        if p.poll() is not None:
            break
        time.sleep(1)
    print(f"The dev server did not answer on {URL} within 90 seconds. Last lines of the log:")
    print(subprocess.run(["tail", "-20", LOG], capture_output=True, text=True).stdout)
    return False


def restart():
    return stop() and start()


if __name__ == "__main__":
    a = sys.argv[1:] or ["--status"]
    fn = {"--status": status, "--start": start, "--stop": stop, "--restart": restart}.get(a[0])
    if not fn:
        sys.exit(__doc__)
    sys.exit(0 if fn() else 1)
