"""Does the picker work? Run it before the owner gets the link, every time.

    python3 code/audit/picker_check.py context/pages/<slug>/drafts     # the real run: the words and the behaviour
    python3 code/audit/picker_check.py --selftest                      # the code alone, on a made-up page

⛔ WHY (Jono, 28 September 2026: "make sure it works properly every time"). The picker is the owner's whole
experience of the split test. A headline that wraps to seven lines, a point said twice, a button that does
nothing, a download that drops the stats: each one was found by hand once. This finds them every time.

The words (the real run only):
  - drafts.py check passes: three maps, their own looks and lengths, every component placed
  - every section the pages use has at least three options that sell: the three the owner sees
  - every section has an ideal option that sells: the line worth working toward, shown in the top three
  - every paying buyer scored every option of every section the pages use
What it does, headless, every page type, computer and phone:
  - no script errors; the page types rotate; lock and unlock work
  - once locked: nothing said twice, every text section filled, every headline three lines or fewer
  - nothing scrolls sideways
  - a section shows its top three, "show more" opens the rest, the arrows move, clicking an option applies it
  - "write your own" applies
  - the numbers strip: four ticked, a fifth refused, the strip changes
  - the promises show as yes or not yet, when the page has any
  - a first name typed in the form reaches the thank-you page
  - verify, then download: picks.json holds the page, every section, the stats, the promises, verified
The self-test also proves the code carries no business of its own: its made-up business's page must show
its own name and none of another business's proof.
Prints PASS, or FAIL and every line that broke. Exits 1 on any failure.
"""
import glob
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
CODE = os.path.dirname(HERE)
PY = sys.executable
LINES = """() => Math.max(0, ...[...document.querySelectorAll('.page:not([hidden]) h1.cs-hero, .page:not([hidden]) h2.cs-title')]
  .filter(h => h.textContent).map(h => Math.round(h.offsetHeight / parseFloat(getComputedStyle(h).lineHeight))))"""
EMPTY = """() => [...document.querySelectorAll('.page:not([hidden]) .sec[data-key]:not([data-key=""]):not([data-key="stats:bar"])')]
  .filter(s => !(s.querySelector('h1,h2')||{}).textContent).map(s => s.dataset.type)"""


def run(args):
    r = subprocess.run([PY] + args, capture_output=True, text=True, cwd=os.path.dirname(CODE))
    return r.returncode, r.stdout + r.stderr


def data_of(folder):
    h = open(os.path.join(folder, "picker.html"), encoding="utf-8").read()
    raw = re.search(r'id="picker-data">(.*?)</script>', h, re.S).group(1).replace("<\\/", "</")
    return json.loads(raw)


def words(folder, D, fails):
    code, out = run([os.path.join(HERE, "drafts.py"), "check", folder])
    if code:
        fails.append("drafts.py check: " + " | ".join(l for l in out.splitlines() if l.startswith("-"))[:400])
    used = {s["key"] for p in D["pages"].values() for s in p["sections"] if s["key"] and not s.get("special")}
    for k in sorted(used):
        n = len(D["options"].get(k) or [])
        if n < 3:
            fails.append(f"{k}: {n} option(s) sell - the owner sees three. Rewrite until three pass (sell_filter.py says why)")
        if not any(o.get("ideal") for o in D["options"].get(k) or []):
            fails.append(f"{k}: no ideal option - write one: the best thing to say, [bracketed] numbers, and what it needs")
    files = {}
    for p in glob.glob(os.path.join(folder, "options-[0-9]*.json")):
        files.update({k: len(v) for k, v in json.load(open(p, encoding="utf-8")).items()})
    paying = [b for b in D["buyers"]]
    for b in paying:
        sp = os.path.join(folder, f"scores-{b['slug']}.json")
        if not os.path.exists(sp):
            fails.append(f"{b['name']} has not scored the options: no {os.path.basename(sp)}")
            continue
        sc = json.load(open(sp, encoding="utf-8"))
        short = [k for k in used if len(sc.get(k) or []) != files.get(k, -1)]
        if short:
            fails.append(f"{b['name']}'s scores do not match the options in: {', '.join(sorted(short))}")


def behaviour(folder, D, fails, selftest):
    from playwright.sync_api import sync_playwright
    url = "file://" + os.path.abspath(os.path.join(folder, "picker.html")).replace(" ", "%20")
    with sync_playwright() as p:
        b = p.chromium.launch(headless=True)
        ctx = b.new_context(viewport={"width": 1600, "height": 1000}, accept_downloads=True)
        pg = ctx.new_page()
        errs = []
        pg.on("pageerror", lambda e: errs.append(str(e)))
        pg.goto(url, wait_until="networkidle")
        pg.evaluate("localStorage.clear()")
        pg.reload(wait_until="networkidle")
        names = list(D["pages"])
        for i, k in enumerate(names):
            shown = pg.evaluate("document.querySelector('.page:not([hidden])').dataset.page")
            if shown != k:
                fails.append(f"page type {k}: the rotator shows {shown}")
            pg.click("[data-act=lock]")
            pg.wait_for_timeout(250)
            chips = pg.inner_text(".sum .chips")
            if "repeated" in chips and "Nothing repeated" not in chips:
                fails.append(f"page {k}: something is said twice once locked - " + pg.inner_text(".rep").replace("\n", " / ")[:200])
            empty = pg.evaluate(EMPTY)
            if empty:
                fails.append(f"page {k}: text sections with no heading: {', '.join(empty)}")
            for view in ("desktop", "phone"):
                pg.click(f"[data-view={view}]")
                pg.wait_for_timeout(250)
                if pg.evaluate(LINES) > 3:
                    fails.append(f"page {k}, {view}: a headline runs past three lines")
                wide = pg.evaluate("() => { const s = document.querySelector('.page:not([hidden]) .scaler'); return s.scrollWidth - s.clientWidth }")
                if wide > 2:
                    fails.append(f"page {k}, {view}: the page scrolls sideways by {wide}px")
            pg.click("[data-view=desktop]")
            if k == names[0]:
                exercise(pg, D, k, fails, selftest)
            pg.click("[data-act=unlock]")
            pg.click("[data-act=next]")
            pg.wait_for_timeout(250)
        if pg.evaluate("document.querySelector('.page:not([hidden])').dataset.page") != names[0]:
            fails.append("the rotator does not come back round to the first page type")
        fails += [f"script error: {e}" for e in errs]
        b.close()


def exercise(pg, D, k, fails, selftest):
    """Every control once, on the first page type."""
    secs = [s for s in D["pages"][k]["sections"] if s["key"] and not s.get("special")]
    with_opts = [s for s in secs if D["options"].get(s["key"])]
    if with_opts:
        key = with_opts[0]["key"]
        pg.click(f'.secl[data-sel="{key}"]')
        pg.wait_for_timeout(300)
        n = len(D["options"][key])
        if any(o.get("ideal") for o in D["options"][key]) and not pg.locator(".opt .ideal").count():
            fails.append(f"{key}: the top three has no ideal line")
        if pg.locator(".opt").count() != min(3, n):
            fails.append(f"{key}: shows {pg.locator('.opt').count()} options, not the top three")
        if n > 3:
            pg.click("[data-act=more]")
            if pg.locator(".opt").count() != n:
                fails.append(f"{key}: show more did not open all {n}")
        before = pg.inner_text(".cur .rot .of")
        pg.click("[data-act=onext]")
        if pg.inner_text(".cur .rot .of") == before:
            fails.append(f"{key}: the arrow did not move")
        pg.locator(".opt").last.click()
        if "on" not in (pg.locator(".opt").last.get_attribute("class") or ""):
            fails.append(f"{key}: clicking an option did not apply it")
    elif not selftest:
        fails.append(f"page {k}: no section has options")
    if secs:
        pg.click(f'.secl[data-sel="{secs[0]["key"]}"]')
        pg.wait_for_timeout(200)
        field = pg.locator("[data-own]").first
        field.fill("You get a test line from write your own.")
        pg.click("[data-act=own]")
        pg.wait_for_timeout(200)
        if "test line" not in pg.inner_text(f'.page:not([hidden]) .sec[data-key="{secs[0]["key"]}"]').lower():
            fails.append("write your own did not reach the page")
    if pg.locator('.secl[data-sel="stats:bar"]').count():
        pg.click('.secl[data-sel="stats:bar"]')
        pg.wait_for_timeout(200)
        strip = pg.inner_text(".page:not([hidden]) [data-stats]")
        if pg.locator(".statpick input:checked").count() != min(4, len(D["stats"])):
            fails.append("the numbers strip does not start with four ticked")
        unticked = pg.locator(".statpick input:not(:checked)")
        if unticked.count():
            unticked.first.click()
            if pg.locator(".statpick input:checked").count() > 4:
                fails.append("the numbers strip took a fifth number")
            pg.locator(".statpick input:checked").first.click()
            unticked.first.click() if pg.locator(".statpick input:not(:checked)").count() else None
            if pg.inner_text(".page:not([hidden]) [data-stats]") == strip:
                fails.append("ticking a number did not change the strip")
    else:
        fails.append("the numbers strip has no picker")
    if D["pages"][k]["needs"] and not pg.locator("[data-prom]").count():
        fails.append(f"page {k}: its promises are not asked")
    pg.fill(".page:not([hidden]) [data-in=first]", "Testname")
    if "Testname" not in pg.inner_text(".page:not([hidden]) [data-sync=first]"):
        fails.append("the first name did not reach the thank-you page")
    pg.check("[data-act=verify]")
    with pg.expect_download() as dl:
        pg.click("#dl")
    picks = json.load(open(dl.value.path()))
    for need in ("page", "sections", "stats", "promises", "verified"):
        if need not in picks:
            fails.append(f"picks.json has no {need}")
    if picks.get("verified") is not True:
        fails.append("picks.json does not say the form was verified")
    if len(picks.get("sections") or []) != len(D["pages"][k]["sections"]):
        fails.append("picks.json is missing sections")


def selftest_folder():
    """A made-up page: three maps, no written options, so only the code is tested."""
    t = tempfile.mkdtemp(prefix="picker-selftest-")
    pts = [("pain", "Your calls go to the business above you on Google", None), ("offer", "A rebuilt Google profile in 8 weeks", 4),
           ("promise", "Live in 8 weeks, or we keep working", 20), ("b1", "Your profile filled in, so Google shows you nearby", None),
           ("b2", "Your listings match, so callers reach the right phone", None), ("b3", "Your calls tracked, so you see what the profile brings", None),
           ("proof", "Clients on camera", 15), ("words", "Paying clients in their own words", 10), ("audit", "A free graded audit by email", 12),
           ("q", "No result on file yet, and we say so", None), ("ask", "Money back if not in the map pack", 4)]
    pool = {"points": [dict({"id": i, "point": t_, "source": "selftest"}, **({"component": c} if c else {})) for i, t_, c in pts],
            "not_here": {"5": "selftest"},
            "stats": [{"id": "a", "value": "100+", "label": "a number on file", "source": "selftest"},
                      {"id": "b", "value": "2014", "label": "a year on file", "source": "selftest"},
                      {"id": "c", "value": "20+", "label": "another number", "source": "selftest"},
                      {"id": "d", "value": "9", "label": "one more", "source": "selftest"},
                      {"id": "e", "value": "[N]", "label": "years in business", "needs": "a number"}]}
    pool["points"][-1]["source"] = "ask the owner"
    json.dump(pool, open(os.path.join(t, "points.json"), "w"))
    M = lambda *pairs: [{"point": p, "section": s} for s, ps in pairs for p in ps]  # noqa: E731
    common = (("benefit-1", ["b1"]), ("benefit-2", ["b2"]), ("benefit-3", ["b3"]), ("videos", ["proof"]), ("reviews", ["words"]))
    drafts = {"A": dict(big_idea="Short page, form first", motivation="certainty", ask="form", look="paper", form="hero", length="short",
                        message_map=M(("hero", ["pain", "offer"]), *common, ("terms", ["promise"]), ("close", ["audit"]))),
              "B": dict(big_idea="Long page, call first", motivation="reduce_risk", ask="call", look="field", form="end", length="long",
                        message_map=M(("hero", ["pain", "offer", "promise"]), *common, ("faq", ["q"]), ("close", ["audit"]))),
              "C": dict(big_idea="Medium page, the money back", motivation="stop_the_pain", ask="call", look="ink", form="end", length="medium",
                        order=["hero", "reviews", "logos", "stats", "benefit-1", "benefit-2", "benefit-3", "videos", "terms", "close", "legal"],
                        message_map=M(("hero", ["pain", "ask"]), ("reviews", ["words"]), ("benefit-1", ["b1"]), ("benefit-2", ["b2"]),
                                      ("benefit-3", ["b3"]), ("videos", ["proof"]), ("terms", ["promise"]), ("close", ["audit"])))}
    for k, d in drafts.items():
        json.dump(d, open(os.path.join(t, f"draft-{k}.json"), "w"))
    json.dump({"business": "Selftest Co", "phone": "+1 555-010-0199",
               "reviews": [{"name": "Pat Example", "meta": "Selftest client", "quote": "A selftest review, word for word."}],
               "videos": [], "faces": [], "results_note": ""}, open(os.path.join(t, "proof.json"), "w"))
    return t


# Another business's proof must never appear on a page (Jono, 29 September 2026: "I don't want it built on my
# social proof"). The selftest page belongs to "Selftest Co", so none of these may show on it.
LEAKS = ("graded audit", "map pack", "Google profile")


def own_proof_only(folder, fails):
    h = open(os.path.join(folder, "picker.html"), encoding="utf-8").read()
    body = h.split('id="picker-data"')[0]
    for leak in LEAKS:
        if leak in body:
            fails.append(f"another business's proof shows on this page: {leak}")
    if "Selftest Co".upper() not in body and "Selftest Co" not in body:
        fails.append("the page does not carry its own business name")


def main():
    selftest = "--selftest" in sys.argv
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if not selftest and len(args) != 1:
        sys.exit(__doc__.split("\n\n")[1])
    folder = selftest_folder() if selftest else args[0]
    fails = []
    code, out = run([os.path.join(HERE, "picker.py"), folder])
    if code or not os.path.exists(os.path.join(folder, "picker.html")):
        print("FAIL\n- picker.py did not build: " + out[-400:])
        return 1
    D = data_of(folder)
    if not selftest:
        words(folder, D, fails)
    else:
        own_proof_only(folder, fails)
    behaviour(folder, D, fails, selftest)
    if selftest:
        shutil.rmtree(folder, ignore_errors=True)
    print("PASS" if not fails else "FAIL\n- " + "\n- ".join(fails))
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
