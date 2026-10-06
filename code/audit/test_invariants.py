"""The rules the audit report may never break, checked against saved pages.

    python3 code/audit/test_invariants.py            # every saved page under context/pages/
    python3 code/audit/test_invariants.py dj-site-home b2b-site-home

Each check is a complaint Jono made that must never come back (27 September 2026):
  - "the offer is drawn on the navigation bar"        -> the nav is its own band, nothing else is boxed there
  - "it skips over major parts of the page"            -> the bands tile the page, top to bottom, no gaps
  - "61 boxes and I can only see 12 in the sidebar"    -> one box per card, same number, same order
  - "the same thing said five times"                   -> each of the 21 components is spoken about once
  - "the founder video called a testimonial"           -> the transcript decides what a video is
  - "a report I could not show anyone"                 -> no report until every section has a verdict
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))

from audit import walk as W  # noqa: E402
from audit.copy_check import classify_video  # noqa: E402
from audit.eighteen import EIGHTEEN, HOME, PAGE  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(HERE))
PAGES = os.path.join(ROOT, "context", "pages")
FAILS = []


def ok(cond, msg):
    if not cond:
        FAILS.append(msg)
    return cond


def tiles(slug, facts):
    bands = W.build_bands(facts)
    page_h = facts.get("scrollHeight") or 0
    ok(bands, f"{slug}: no bands at all")
    prev = 0
    for b in bands:
        ok(b["top"] == prev, f"{slug}: gap or overlap before {b['id']} ({prev} -> {b['top']})")
        ok(b["h"] > 0, f"{slug}: {b['id']} has no height")
        prev = b["bot"]
    ok(prev == page_h, f"{slug}: bands stop at {prev}, page is {page_h}")
    bar = facts.get("topBar") or {}
    if bar.get("top") is not None and bar["top"] < 8 and 24 <= (bar.get("h") or 0) <= 300:
        ok(bands[0]["src"] == "nav", f"{slug}: the top bar is not its own band")
        ok(bands[0]["bot"] <= bar["top"] + bar["h"] + 30, f"{slug}: the nav band swallows the hero")
    return bands


def full_judgment(bands, facts, roll_result):
    """A complete, well-formed sheet: the shape a finished judgment has."""
    need = W.sheet(facts, {}, bands, roll_result)
    cards = []
    for c in need["cards"]:
        holds = {k: {"status": "ok", "note": "zz-card-note"} for k in c["holds"]}
        # a complete judgment rewrites every hard line, in words a visitor reads first time
        rewrites = [{"before": h["line"], "after": "We fix it fast, so you save time and get back to work."}
                    for h in c["code_sees"]["hard_lines"]]
        extra = ({"eyebrow": {"verdict": "weak", "says": "test"}} if c["kind"] == "hero" else {})
        cards.append({**extra, "id": c["id"], "top": c["top"], "is": "x", "kind": c["kind"], "verdict": "keep",
                      "why": "test", "holds": holds, "notes": [], "rewrites": rewrites, "drop_off": 10 if c["code_sees"].get("stand_in_faces") else 3, "drop_off_why": "test",
                      "image_grade": 7, "image_why": "test"})
    items = {k: {"status": "weak", "note": "zz-card-note"} for k in need["page"]["items"]}
    return {"cards": cards, "page": {"mode": "landing", "items": items}}


def contract(slug, bands, facts):
    roll_result = {"checks": [{"n": n, "status": "TO DO", "says": ""} for n, *_ in EIGHTEEN]}
    j = full_judgment(bands, facts, roll_result)
    model, problems = W.finish(bands, j, facts, roll_result)
    ok(not problems, f"{slug}: a complete judgment still has problems: {problems[:3]}")
    card_boxes = [b for b in model["boxes"] if b["left"] is None]
    ok(len(card_boxes) == len(model["cards"]) == len(bands), f"{slug}: boxes, cards and bands differ")
    # every component exactly once
    seen = []
    for c in model["cards"]:
        seen += list(c["holds"])
    # the Add list also indexes missing items that live in a card or across the page; those
    # entries point elsewhere and are not a second telling
    seen += [c["n"] for c in model["across"]] + [c["n"] for c in model["add"] if not c.get("in_card")]
    ok(sorted(seen) == sorted(n for n, *_ in EIGHTEEN), f"{slug}: components not said exactly once: {sorted(seen)}")
    # nothing about content on the nav band
    if bands[0]["src"] == "nav":
        nav_holds = set(model["cards"][0]["holds"])
        ok(nav_holds <= {14}, f"{slug}: the nav band holds {nav_holds}, only 14 belongs there")

    # "not checked" is shown across the page and left out of the count
    j5 = json.loads(json.dumps(j))
    if "21" in j5["page"]["items"]:
        j5["page"]["items"]["21"] = {"status": "unchecked", "note": "could not reach it"}
        m5, p5 = W.finish(bands, j5, facts, roll_result)
        ok(not p5 and any(c["n"] == 21 and c["status"] == "unchecked" for c in m5["across"]),
           f"{slug}: a not-checked thank-you page was dropped from the report")
        ok(m5["tally"]["of"] == model["tally"]["of"] - 1, f"{slug}: a not-checked item was counted")
    for line in model["do_first"]:
        ok(len(line) < 90 and "zz-card-note" not in line, f"{slug}: 'Do these first' repeats a card note: {line!r}")

    # a rewrite above grade 10, and a repeat that is kept, both stop the report
    j6 = json.loads(json.dumps(j))
    j6["cards"][-1]["rewrites"] = [{"before": "x", "after": "Our comprehensive multidisciplinary methodology facilitates transformational organizational capabilities across heterogeneous environments."}]
    ok(W.finish(bands, j6, facts, roll_result)[1], f"{slug}: a rewrite above grade 10 did not stop the report")
    j7 = json.loads(json.dumps(j))
    j7["cards"][-1]["repeats"] = 1
    ok(W.finish(bands, j7, facts, roll_result)[1], f"{slug}: a kept repeat did not stop the report")

    # a draft scores stand-in slots as filled: no 10/10 forced, and every slot listed to fill
    faces = [c for c in j["cards"] if c.get("drop_off") == 10]
    if faces:
        j9 = json.loads(json.dumps(j))
        j9["page"]["status"] = "draft"
        for c in j9["cards"]:
            c["drop_off"] = 3
        m9, p9 = W.finish(bands, j9, facts, roll_result)
        ok(not p9, f"{slug}: a draft still forced 10/10 on stand-in slots: {p9[:2]}")
        ok(any("stand-in face" in x["what"] for x in m9["fill"]), f"{slug}: a draft did not list its stand-in faces to fill")

    # a section's checklist is about THAT section: a body section with no bullets never shows bullets ticked
    for c in model["cards"]:
        an = dict(c.get("anatomy") or [])
        if "bullets" in an and c.get("few_bullets") is not None:
            ok(an["bullets"] == (not c["few_bullets"]), f"{slug}: section {c['n']} checklist disagrees with its own bullet count")

    j8 = json.loads(json.dumps(j))
    j8["cards"][0].pop("drop_off")
    ok(W.finish(bands, j8, facts, roll_result)[1], f"{slug}: a section with no drop-off score did not stop the report")

    # breaking a rule has to stop the report
    j2 = json.loads(json.dumps(j))
    j2["cards"][0]["verdict"] = None
    ok(W.finish(bands, j2, facts, roll_result)[1], f"{slug}: a missing verdict did not stop the report")
    j3 = json.loads(json.dumps(j))
    if len(j3["cards"]) > 1:
        j3["cards"][1]["holds"]["20"] = {"status": "ok", "note": "twice"}
        j3["cards"][0]["holds"]["20"] = {"status": "ok", "note": "twice"}
        ok(W.finish(bands, j3, facts, roll_result)[1], f"{slug}: a component said twice did not stop the report")
    j9 = json.loads(json.dumps(j))
    menus = [c for c in j9["cards"] if c["kind"] in ("nav", "footer")]
    if menus:
        menus[0]["verdict"] = "fix"
        ok(W.finish(bands, j9, facts, roll_result)[1], f"{slug}: a menu or footer marked fix did not stop the report")
    j4 = json.loads(json.dumps(j))
    j4["cards"][-1].update({"verdict": "cut", "why": "", "notes": [{"says": "a fix note"}]})
    ok(W.finish(bands, j4, facts, roll_result)[1], f"{slug}: a cut with no reason and fix notes did not stop the report")


def regressions():
    # the founder video is known by what it says, not where it sits
    ok(classify_video("Hi, my name is Alex, the owner of Northside DJs. Today we're going to talk about "
                      "the three main reasons why our customers love us.")[0] == "founder",
       "the Northside DJs founder video was not read as a founder video")
    ok(classify_video("We hired them for our wedding and honestly it was the best decision. Would recommend.")[0]
       == "client", "a client video was not read as a client video")
    ok(classify_video("")[0] == "unknown", "a video with no transcript was given a kind")
    # owning a business does not make you the founder of THIS one: Dana owns Ridgeline Design and
    # is the agency's client; Jono welcoming visitors to his own site is the founder
    ok(classify_video("Hey, my name is Dana and I'm one of the owners of Ridgeline Design. We have automated a lot of our "
                      "business thanks to Acme Marketing.")[0] == "client", "a client who owns a business was read as the founder")
    ok(classify_video("Hey, so if you're watching this, you probably already know who I am from YouTube. First of all, thanks "
                      "for visiting the website.")[0] == "founder", "the owner welcoming visitors was read as a client")
    ok(classify_video("Hi, my name is Alex, the owner of Northside Photo. We have worked with thousands of photographers and "
                      "kept the top 1%.")[0] == "founder", "an owner describing their own hiring was read as a client")
    # every component has one home
    placed = sorted(list(HOME) + PAGE)
    ok(placed == sorted(n for n, *_ in EIGHTEEN), f"components placed wrongly: {placed}")


def page_facts(slug):
    """Jono's specific complaints about specific pages, where the saved capture is fresh enough."""
    path = os.path.join(PAGES, slug, "capture.json")
    f = json.load(open(path))["viewports"]["desktop"]["facts"]
    if slug == "b2b-site-home" and f.get("textAt") is not None:
        bands = W.build_bands(f)
        ok(bands[0]["src"] == "nav" and bands[0]["bot"] <= 140, "a B2B site: the nav is not the first band")
        ok(any(abs(b["top"] - 129) <= 12 for b in bands), "a B2B site: no band starts where the hero does")
        ok(not f.get("forms"), "a B2B site: a form was found where there is none")
    if slug == "dj-site-home" and f.get("textAt") is not None:
        answered = [q for q in f.get("faq") or [] if (q.get("q") or "").endswith("?") and (q.get("a") or "").strip()]
        ok(len(answered) >= 6, f"dj site: only {len(answered)} FAQ answers read, there are six")
    if slug == "photo-site-home" and f.get("textAt") is not None:
        bands = W.build_bands(f)
        ok(any(any(fm.get("top") is not None and b["top"] <= fm["top"] < b["bot"] for fm in f.get("forms") or [])
               for b in bands), "a photography site: no band holds the quote form")
        if f.get("videoWidgets") is not None:
            ok(len(f["videoWidgets"]) >= 10, f"a photography site: {len(f['videoWidgets'])} video widgets found, the page has a founder video and nine client videos")
            ok(bands[-1]["src"] == "footer", "a photography site: the footer was not found")
            hero = next((b for b in bands if b["src"] != "nav"), None)
            head, sub = W.hero_lines(f, hero)
            ok("1,000" in (head.get("text") or ""), f"a photography site: the headline was read as {head.get('text')!r}, not the big line")
            ok("top 1%" in (sub.get("text") or ""), f"a photography site: the line under the headline was read as {sub.get('text')!r}")


def follows(slug):
    """A form that stays on screen while scrolling is found, and a phone gets one bar, not two."""
    path = os.path.join(PAGES, slug, "capture.json")
    if slug != "www-mobiloud-com-pages-shopify-mobile-app" or not os.path.exists(path):
        return
    cap = json.load(open(path))
    f = cap["viewports"]["desktop"]["facts"]
    if "stickyForm" in f:
        ok(bool(f.get("stickyForm")), "mobiloud shopify page: the form that follows the visitor was not found")
    m = cap["viewports"]["mobile"]["facts"]
    if "fixedTop" in m:
        ok(bool(m.get("fixedTop")) and bool(m.get("fixedBottom")), "mobiloud shopify page: the two phone bars were not both found")


def titles(slug):
    """Sections are named by their real title, never by a stat or half a two-tone heading."""
    want = {"www-mobiloud-com-home": ["A direct line to your best", "Get a free preview of your", "Tadashi Shoji achieves 18%"],
            "b2b-site-home": ["Innovation model", "Case studies"]}
    if slug not in want:
        return
    f = json.load(open(os.path.join(PAGES, slug, "capture.json")))["viewports"]["desktop"]["facts"]
    if f.get("headingsAt") is None:
        return
    got = [b["heading"] for b in W.build_bands(f)]
    for w in want[slug]:
        ok(any(g.startswith(w) for g in got), f"{slug}: no section titled {w!r} - got {[g[:24] for g in got]}")


def main(slugs):
    regressions()
    for slug in slugs:
        cap = os.path.join(PAGES, slug, "capture.json")
        if not os.path.exists(cap):
            continue
        facts = json.load(open(cap))["viewports"]["desktop"]["facts"]
        bands = tiles(slug, facts)
        if bands:
            contract(slug, bands, facts)
        page_facts(slug)
        titles(slug)
        follows(slug)
    if FAILS:
        print(f"{len(FAILS)} FAILED")
        for f in FAILS:
            print("  -", f)
        sys.exit(1)
    print(f"all rules hold on {len(slugs)} page(s)")


if __name__ == "__main__":
    args = sys.argv[1:] or sorted(d for d in os.listdir(PAGES) if os.path.isdir(os.path.join(PAGES, d)))
    main(args)
