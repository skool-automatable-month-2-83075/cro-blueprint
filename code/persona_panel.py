"""The persona panel's memory: the verdict grid across runs, the call, the stop check.

    python3 code/persona_panel.py --log code/cache/panel-run.json     # append one run (Claude writes the JSON after the subagents answer)
    python3 code/persona_panel.py --grid                              # print + rewrite context/personas/runs.md
    python3 code/persona_panel.py --call                              # the call for the latest run: ship / fix / stop

A run JSON: {"page": "/lp/x", "page_hash": "...", "model": "claude-...", "verdicts": [
   {"persona": "Burst-pipe Brenda", "share": 1, "primary": false, "verdict": "LEAVE", "reason": "no phone number above the fold",
    "element": "hero", "out_of_control": false, "confirmed_by": "call 2026-08-14 / search term / human test / none"}]}

Rules it enforces (references/persona-panel.md): STAY counts for nothing, LEAVE counts; every buyer counts the
same; two personas hitting one element is ONE signal until something outside the model confirms it.

Every --log redraws context/personas/dashboard.html (code/build_persona_dashboard.py) so the page always shows the
latest round. call_lines() is shared with that script so the dashboard prints the same call this prints.
"""
import argparse
import json
import os
from datetime import date

import _posthog as ph

RUNS = os.path.join(ph.ROOT, "context", "personas", "runs.json")
GRID = os.path.join(ph.ROOT, "context", "personas", "runs.md")


def load():
    return json.load(open(RUNS)) if os.path.exists(RUNS) else []


def save(runs):
    os.makedirs(os.path.dirname(RUNS), exist_ok=True)
    json.dump(runs, open(RUNS, "w"), indent=1)


def log(path):
    run = json.load(open(path))
    run.setdefault("date", date.today().isoformat())
    runs = load()
    same_page = [r for r in runs if r.get("page") == run.get("page") and r.get("page_hash") == run.get("page_hash")]
    run["round"] = len(same_page) + 1
    runs.append(run)
    save(runs)
    print(f"Logged run {run['round']} on {run['page']} · {len(run['verdicts'])} verdicts")
    grid()
    call()
    redraw()


def redraw():
    """Rebuild the dashboard so the new round shows. Never fatal - the log is already saved."""
    try:
        import build_persona_dashboard as bpd
        out = bpd.build(quiet=True)
        print(f"\nDashboard redrawn: {out}")
    except SystemExit as e:
        print(f"\nDashboard not redrawn: {e}")
    except Exception as e:  # noqa: BLE001 - a broken dashboard must not lose a logged run
        print(f"\nDashboard not redrawn: {e}")


def grid():
    runs = load()
    L = ["# Persona panel · runs", f"{len(runs)} runs logged · latest {runs[-1]['date'] if runs else 'none'}",
         "Next: fix the blocker the primary buyer hit, run again.", ""]
    for r in runs[-12:]:
        L += [f"## {r['date']} · round {r.get('round', '?')} · {r['page']}", f"- Model: {r.get('model', '?')}"]
        for v in r["verdicts"]:
            tag = " · PRIMARY" if v.get("primary") else ""
            conf = (f" · confirmed by {v['confirmed_by'][:50].rsplit(' ', 1)[0]}"
                    if v.get("confirmed_by") and v["confirmed_by"] != "none" else "")
            L.append(f"- {v['persona']} · {v['verdict']}{tag}")
            if v["verdict"] == "LEAVE":
                L.append(f"  - at {v.get('element', '?')}: {v.get('reason', '')[:80].rsplit(' ', 1)[0]}{conf}")
        if r.get("fix_applied"):
            L.append(f"- Fix applied after this run: {r['fix_applied']}")
        L.append("")
    os.makedirs(os.path.dirname(GRID), exist_ok=True)
    open(GRID, "w").write("\n".join(L))
    print("\n".join(L[:40]))


def call_lines(r):
    """The call for one round: how many buyers get in touch, then every buyer who still leaves.
    Every buyer counts the same (Jono, 29 September 2026). Each exit is something the next page has to answer."""
    vs = r.get("verdicts", [])
    paying = [v for v in vs if v.get("share")]
    won = sum(1 for v in paying if v.get("verdict") == "STAY")
    L = [f"{won} of {len(paying)} buyers get in touch."]
    leaves = [v for v in paying if v.get("verdict") == "LEAVE"]
    if not leaves:
        L.append("Every buyer gets in touch. From a friendly model that is the default, not proof - put the page in front "
                 "of three real people before trusting it.")
    by_el = {}
    for v in leaves:
        who, el = v["persona"], v.get("element", "?")
        conf = f" · confirmed by {v['confirmed_by'][:50]}" if v.get("confirmed_by") not in (None, "", "none") else ""
        if v.get("out_of_control"):
            L.append(f"OUTSIDE THE PAGE: {who} leaves at {el} - price, area or hours.")
        else:
            L.append(f"TO ANSWER: {who} leaves at {el}{conf}")
            by_el.setdefault(el, []).append(v)
    for el, same in by_el.items():
        if len(same) >= 2 and not any(x.get("confirmed_by") not in (None, "", "none") for x in same):
            L.append(f"ONE SIGNAL, not {len(same)}: they all leave at {el}. Same model, same draw - a call, a search term "
                     "or a real person confirms it.")
    L += [f"NEVER PAID: {v['persona']} leaves at {v.get('element', '?')}. Worth answering; not counted."
          for v in vs if not v.get("share") and v.get("verdict") == "LEAVE"]
    return L


def call():
    runs = load()
    if not runs:
        print("No runs yet."); return
    r = runs[-1]
    print(f"\n# The call · round {r.get('round')} on {r['page']}")
    for line in call_lines(r):
        print(f"- {line}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--log"); ap.add_argument("--grid", action="store_true"); ap.add_argument("--call", action="store_true")
    a = ap.parse_args()
    if a.log: log(a.log)
    elif a.grid: grid()
    elif a.call: call()
    else: ap.print_help()
