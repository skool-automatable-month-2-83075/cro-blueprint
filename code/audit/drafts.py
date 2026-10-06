"""Draft three, build one: three big ideas, each with its message map. The structure follows. The words come last.

    python3 code/audit/drafts.py check   context/pages/<slug>/drafts    # each map, its structure, and the three apart
    python3 code/audit/drafts.py show    context/pages/<slug>/drafts    # drafts.html: the maps and their structures
    python3 code/audit/drafts.py prepare context/pages/<slug>/drafts    # shuffle them into blind outlines for the panel
    python3 code/audit/drafts.py results context/pages/<slug>/drafts    # weigh the reads, write results.md
    python3 code/audit/drafts.py needed  context/pages/<slug>/drafts    # options-needed.json: the writers' brief

⛔ THE ORDER (Jono, 28 September 2026).
  1. The big idea and the message map decide what the page must say, and in what order: the offer, the
     guarantee, the three benefits, the proof, the objections. Each is a point from the pool.
  2. The structure follows from that map, with the blueprint's skeleton as the default. `structure()` builds it.
  3. The final words fill it, after the owner picks one draft.

⛔ WHY THREE (Jono, 28 September 2026). Only one challenger can run: three live pages need about three times
the traffic (STEP 1b). A map costs minutes and a build costs a day, so three are drafted and one is built.

⛔ THREE REAL SWINGS, NOT THREE ORDERS (Jono, 28 September 2026: "should they be much more different?"). A visitor
notices the first screen, the length and where the form sits, not the order of the middle. So the three differ in
all of those, and in the look: each takes its own look from the kit (paper, the blue field, ink), and the checks
refuse three pages that share a look or a length.

⛔ THE SAME FACTS, DIFFERENT PAGES. The three share one pool of talking points, so none can invent a claim.
Each has its own big idea and picks which points it makes, in its own order. Every point lives in one section,
a second mention only at the close (the page that said "live in 8 weeks" 13 times scored 3 of 10).

The folder holds:
  points.json   {"budget": [350, 850], "not_here": {"5": "why this component does not apply"},
                 "points": [{"id": "guarantee", "point": "Live in 8 weeks, or we keep working free",
                             "source": "proof.md", "match": "8 weeks", "component": 20}]}
                A source of "ask the owner" marks a promise not on file: it ships only with their yes.
                "reason": 1, 2 or 3 marks one of the three reasons people buy, from context/voc/reasons.md.
                "component" is the blueprint number the point carries: its section then holds it.
  draft-A.json  {"big_idea": "...", "motivation": "reduce_risk", "ask": "call" | "form",
  draft-B.json   "look": "paper" | "field" | "ink", "form": "hero" | "end", "length": "short" | "medium" | "long",
                 "order": [optional: the section types top to bottom, when the skeleton's default order is not the idea],
                 "message_map": [{"point": "agency_burn", "section": "hero"}, {"point": "price", "section": "hero"}, ...]}
  draft-C.json  The map runs top to bottom. Its sections are skeleton names or new ones: hero, problem, audit,
                steps, benefit-1, benefit-2, benefit-3, terms, videos, reviews, faq, close.
  today.json    optional: the control as it is, {"structure": [{"type", "layout", "says", "holds"}]}
  words/        the words, written after the pick
  reads/        one sheet per buyer, plus craft.json, filled by the panel after `prepare`
"""
import argparse
import difflib
import glob
import json
import os
import random
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))

from audit.eighteen import EIGHTEEN, PAGE  # noqa: E402
from audit.motivations import MOTIVATIONS  # noqa: E402

NAMES = {n: name for n, name, *_ in EIGHTEEN}
REASONS = os.path.join(os.path.dirname(os.path.dirname(HERE)), "context", "voc", "reasons.md")
ASK_OWNER = "ask the owner"
ALIKE = 0.6

# The blueprint's skeleton. The first screen, then logos and numbers right under it; the form, then one legal line, last.
TOP, END = ["hero", "logos", "stats"], ["faq", "close", "legal"]
PROOF = ["videos", "reviews"]          # placed where the map puts them, else after the selling sections
STRIPS = {"logos", "stats", "legal", "founder"}  # a row, not a section with words to choose: no talking point
HOLDS = {"hero": {1, 2, 4, 13, 22}, "logos": {24}, "stats": {23}, "videos": {6, 15}, "reviews": {10},
         "close": {9, 11, 12, 13}, "legal": {14}, "founder": {1}}
LOOKS = ("paper", "field", "ink")      # the kit's three looks: white, the brand-blue field, dark ink
# The first screen follows the form's place and the look: the form beside the headline, the founder video beside
# it, or everything centred over a wide video. A form in the first screen moves the founder video to its own band.
HERO_HOLDS = {"hero-form": {2, 4, 11, 12, 13, 22}, "hero-video": {1, 2, 4, 13, 22}, "hero-center": {1, 2, 4, 13, 22}}
BENEFIT_LAYOUT = {"paper": "benefit-compact", "ink": "benefit-row"}  # the field look alternates two-ups
LAYOUT = {"hero": "hero-video", "logos": "logo-row", "stats": "stat-row", "problem": "tint-card", "terms": "tint-card",
          "steps": "rows", "videos": "video-grid", "reviews": "quote-wall", "faq": "faq-list", "close": "form-split",
          "legal": "legal-line", "founder": "founder-band"}
ALWAYS = [3, 17, 21]                  # every page: a button in every section, the mobile call bar, the thank-you page


def load(folder):
    pool = json.load(open(os.path.join(folder, "points.json"), encoding="utf-8"))
    drafts = {os.path.basename(p)[6:-5]: json.load(open(p, encoding="utf-8"))
              for p in sorted(glob.glob(os.path.join(folder, "draft-*.json")))}
    tp = os.path.join(folder, "today.json")
    today = json.load(open(tp, encoding="utf-8")) if os.path.exists(tp) else None
    return pool, drafts, today


def hero_layout(d):
    if d.get("form") == "hero":
        return "hero-form"
    return "hero-center" if d.get("look") == "ink" else "hero-video"


def structure(d, pool):
    """The page the map implies: skeleton sections pinned, the map's own sections in the map's order - or the
    draft's own order when it gives one. Layouts follow the look and where the form sits."""
    if d.get("structure"):
        return d["structure"]
    comp = {p["id"]: p.get("component") for p in pool["points"]}
    if d.get("order"):
        types = list(d["order"])
    else:
        order = []
        for m in d.get("message_map") or []:
            if m.get("section") not in order:
                order.append(m.get("section"))
        middle = [s for s in order if s not in TOP + END]
        middle += [p for p in PROOF if p not in middle]
        types = TOP + middle + END
    if d.get("form") == "hero" and "founder" not in types:
        types.insert(1, "founder")
    out, bn = [], 0
    for t in types:
        says = [m["point"] for m in d.get("message_map") or [] if m.get("section") == t]
        if t == "hero":
            layout = hero_layout(d)
        elif t.startswith("benefit"):
            bn += 1
            layout = BENEFIT_LAYOUT.get(d.get("look"), "two-up-right" if bn % 2 else "two-up-left")
        else:
            layout = LAYOUT.get(t, "two-up-right")
        holds = set(HERO_HOLDS[layout] if t == "hero" else HOLDS.get(t, set())) | {comp[p] for p in says if comp.get(p)}
        out.append({"type": t, "layout": layout, "says": says, "holds": sorted(holds), "button": t not in STRIPS})
    return out


def outline(d, pool):
    """(type, words) per section: the talking points in plain words, for the blind panel and the pulled-by check."""
    text = {p["id"]: p["point"] for p in pool["points"]}
    return [(s["type"], ". ".join(text.get(p, p) for p in s.get("says") or [])) for s in structure(d, pool)]


def alike(a, b):
    return bool(a and b) and difflib.SequenceMatcher(None, a.lower(), b.lower()).ratio() > ALIKE


def check_map(d, pool):
    P, ids = [], {p["id"] for p in pool["points"]}
    if not (d.get("big_idea") or "").strip():
        P.append("no big_idea: the one idea the whole page sells")
    if d.get("motivation") not in MOTIVATIONS:
        P.append(f"motivation must be one of: {', '.join(MOTIVATIONS)}")
    if d.get("ask") not in ("call", "form"):
        P.append('ask must be "call" or "form": which one the first screen leads with')
    if d.get("look") not in LOOKS:
        P.append(f"look must be one of: {', '.join(LOOKS)}")
    if d.get("form") not in ("hero", "end"):
        P.append('form must be "hero" or "end": where the form sits')
    mm = d.get("message_map") or []
    if d.get("order"):
        missing = sorted({m.get("section") for m in mm} - set(d["order"]))
        if missing:
            P.append(f"the map uses sections the order leaves out: {', '.join(missing)}")
        if d["order"][0] != "hero" or d["order"][-1] != "legal" or "close" not in d["order"]:
            P.append("the order starts with the hero and ends with the form (close) and the legal line")
    if not mm or mm[0].get("section") != "hero":
        P.append("the map starts in the hero: the first thing it says is the first screen")
    homes = {}
    for m in mm:
        if m.get("point") not in ids:
            P.append(f"\"{m.get('point')}\" is not in points.json - add it to the pool with its source")
        homes.setdefault(m.get("point"), []).append(m.get("section"))
    for pid, where in homes.items():
        if len(where) > 2 or (len(where) == 2 and "close" not in where):
            P.append(f"\"{pid}\" lives in {', '.join(where)} - one section, a second mention only at the close")
    # A point that names another point's words says it twice on the page: "what is included ... and a backup DJ"
    # beside a first screen that already promises the backup DJ. Found on the first cold run, 1 October 2026.
    by_id = {p["id"]: p for p in pool["points"]}
    for m in mm:
        p = by_id.get(m.get("point")) or {}
        if not p.get("match"):
            continue
        for o in mm:
            q = by_id.get(o.get("point")) or {}
            if q and q is not p and o.get("section") != m.get("section") and "close" not in (o.get("section"), m.get("section")) \
                    and re.search(p["match"], q.get("point", ""), re.I):
                P.append(f"\"{q['id']}\" in {o.get('section')} already says \"{p['id']}\", which lives in {m.get('section')} - reword one, or put them in one section")
    comp = {p["id"]: p.get("component") for p in pool["points"]}
    if not any(comp.get(m.get("point")) == 4 and m.get("section") == "hero" for m in mm):
        P.append("no offer in the hero: map a point with \"component\": 4 to the hero - what they get, by when")
    if not any(comp.get(m.get("point")) == 20 for m in mm):
        P.append("no guarantee: map a point with \"component\": 20 - what happens if it does not work")
    st = structure(d, pool)
    benefits = [s["type"] for s in st if s["type"].startswith("benefit")]
    if len(benefits) != 3:
        P.append(f"{len(benefits)} benefit sections - the blueprint wants three, each its own section")
    # the three reasons people buy (context/voc/reasons.md, from /personas) are the three benefits on every page type
    if os.path.exists(REASONS):
        why = {p.get("reason"): p["id"] for p in pool["points"] if p.get("reason") in (1, 2, 3)}
        if len(why) < 3:
            P.append("points.json needs the three reasons from context/voc/reasons.md: one point each with \"reason\": 1, 2 or 3")
        told = {pid for s in st if s["type"].startswith("benefit") for pid in s["says"]}
        for n, pid in sorted(why.items()):
            if pid not in told:
                P.append(f"reason {n}, \"{pid}\", has no benefit section - each of the three reasons people buy gets its own")
    empty = [s["type"] for s in st if not s["says"] and s["type"] not in STRIPS | set(PROOF)]
    if empty:
        P.append(f"sections with nothing to say: {', '.join(empty)} - give each one a point from the pool")
    held = {n for s in st for n in s["holds"]}
    skip = {int(k) for k in (pool.get("not_here") or {})}
    need = [n for n in NAMES if n not in PAGE and n not in skip and n not in held]
    if need:
        P.append("components with no home: " + ", ".join(f"{n} {NAMES[n]}" for n in need))
    return P, st


def check(folder):
    pool, drafts, today = load(folder)
    failed = False
    for k, d in drafts.items():
        P, st = check_map(d, pool)
        failed |= bool(P)
        print(f"Draft {k} - {'PASS' if not P else 'FIX'} ({len(d.get('message_map') or [])} points, {len(st)} sections)")
        for p in P:
            print(f"- {p}")
    X = [] if len(drafts) == 3 else [f"{len(drafts)} drafts - write three"]
    ks = list(drafts)
    order = {k: [s["type"] for s in structure(drafts[k], pool)] for k in ks}
    for i, a in enumerate(ks):
        for b in ks[i + 1:]:
            A, B = drafts[a], drafts[b]
            if A.get("motivation") == B.get("motivation"):
                X.append(f"{a} and {b} lead on the same motivation: {A.get('motivation')}")
            if alike(A.get("big_idea", ""), B.get("big_idea", "")):
                X.append(f"{a} and {b} have nearly the same big idea")
            if order[a] == order[b]:
                X.append(f"{a} and {b} run their sections in the same order")
            lead = lambda D: [m["point"] for m in D.get("message_map") or [] if m.get("section") == "hero"]  # noqa: E731
            if lead(A) == lead(B):
                X.append(f"{a} and {b} open on the same points - the first screen has to differ")
        if today and order[a] == [s["type"] for s in structure(today, pool)]:
            X.append(f"{a} runs in the control's order - change the shape")
    looks = [drafts[k].get("look") for k in ks]
    if len(set(looks)) < len(looks):
        X.append(f"two or more share a look ({', '.join(str(x) for x in looks)}) - each takes its own: {', '.join(LOOKS)}")
    lengths = [drafts[k].get("length") for k in ks]
    if len(set(lengths)) < len(lengths):
        X.append(f"two or more share a length ({', '.join(str(x) for x in lengths)}) - one short, one medium, one long")
    if len({drafts[k].get("form") for k in ks}) < 2 and len({drafts[k].get("ask") for k in ks}) < 2:
        X.append("the form sits in the same place and the ask is the same on all three - move the form on one")
    print(f"Across the drafts - {'PASS' if not X else 'FIX'}")
    for x in X:
        print(f"- {x}")
    return 1 if failed or X else 0


def pages_of(folder):
    pool, drafts, today = load(folder)
    return pool, dict(drafts, **({"today": today} if today else {}))


def prepare(folder):
    pool, pages = pages_of(folder)
    order = list(pages)
    random.Random(len(order)).shuffle(order)
    out = os.path.join(folder, "panel")
    os.makedirs(out, exist_ok=True)
    key = {}
    for i, k in enumerate(order, 1):
        page = {"sections": [{"section": t, "says": w} for t, w in outline(pages[k], pool)]}  # no big idea, no label
        json.dump(page, open(os.path.join(out, f"page-{i}.json"), "w"), indent=1, ensure_ascii=False)
        key[f"page-{i}"] = k
    json.dump(key, open(os.path.join(out, "key.json"), "w"), indent=1)
    os.makedirs(os.path.join(folder, "reads"), exist_ok=True)
    print(f"{len(key)} blind outlines in {out}. Never hand a reader key.json.")
    print('Each buyer writes reads/<buyer>.json: {"buyer": "<name>", "pages": {"page-1": {"acts": "yes|no", '
          '"leaves_at": "<section, empty if they read to the end>", "pulled_by": "<words from that page>", "why": "..."}}}')
    print('The craft judge writes reads/craft.json: {"pages": {"page-1": {"score": 7, "why": "..."}}}')
    return 0


def _sheets(folder, key, pages, pool, buyers):
    row, bad, read = {k: {"acts": [], "left": [], "pulled": []} for k in pages}, [], set()
    for f in sorted(glob.glob(os.path.join(folder, "reads", "*.json"))):
        if f.endswith("craft.json"):
            continue
        sh = json.load(open(f))
        b = buyers.get(str(sh.get("buyer", "")).lower())
        if not b:
            bad.append(f"{os.path.basename(f)}: \"{sh.get('buyer')}\" is not an approved paying buyer")
            continue
        read.add(b["name"].lower())
        gaps = sorted(set(key) - set(sh.get("pages") or {}))
        if gaps:
            bad.append(f"{b['name']} did not read {', '.join(gaps)}")
        for pid, r in (sh.get("pages") or {}).items():
            k = key.get(pid)
            if k is None:
                bad.append(f"{os.path.basename(f)}: no {pid}")
                continue
            words = " ".join(w for _, w in outline(pages[k], pool))
            if r.get("pulled_by") and r["pulled_by"].strip(' ."') not in words:
                bad.append(f"{b['name']} on {pid}: \"{r['pulled_by'][:60]}\" is not on that page word for word")
            if str(r.get("acts", "")).lower().startswith("y") and not r.get("leaves_at"):
                row[k]["acts"].append(b)
            else:
                row[k]["left"].append(f"{b['name']}: left at {r.get('leaves_at') or 'the end, without getting in touch'}")
            if r.get("pulled_by"):
                row[k]["pulled"].append(f"{b['name']}: \"{r['pulled_by']}\"")
    bad += [f"{b['name']} has no sheet - every paying buyer reads every page" for n, b in buyers.items() if n not in read]
    return row, bad


def results(folder):
    import persona_read as PR
    pool, pages = pages_of(folder)
    key = json.load(open(os.path.join(folder, "panel", "key.json")))
    buyers = {b["name"].lower(): b for b in PR.load_buyers() if b["weighted"]}
    total = len(buyers) or 1   # every buyer counts the same (Jono, 29 September 2026)
    cp = os.path.join(folder, "reads", "craft.json")
    craft = json.load(open(cp)).get("pages", {}) if os.path.exists(cp) else {}
    row, bad = _sheets(folder, key, pages, pool, buyers)
    if bad:
        print("FIX, send each sheet back to its reader:\n- " + "\n- ".join(bad))
        return 1
    asks = {p["id"] for p in pool["points"] if str(p.get("source", "")).lower() == ASK_OWNER}
    for k, r in row.items():
        r["share"] = len(r["acts"])
        c = craft.get(next((p for p, v in key.items() if v == k), ""), {})
        r["craft"], r["craft_why"] = c.get("score"), c.get("why", "")
    ranked = sorted(row, key=lambda k: (-row[k]["share"], -(row[k]["craft"] or 0)))
    best = next((k for k in ranked if k != "today"), ranked[0])
    L = [f"# {len(pages) - ('today' in pages)} drafts{', and today' if 'today' in pages else ''}, read blind as whole pages", "",
         f"**Next action:** pick one draft. The panel leans to {best}; it is a simulation, and your read outranks it.", ""]
    for k in ranked:
        r, d = row[k], pages[k]
        L += [f"## {'Today' if k == 'today' else 'Draft ' + k}", ""]
        if d.get("big_idea"):
            L.append(f"- Big idea: {d['big_idea']}")
        L.append(f"- Buyers who would get in touch: {r['share']} of {total} ({', '.join(b['name'] for b in r['acts']) or 'nobody'})")
        if r["craft"] is not None:
            L.append(f"- Craft judge: {r['craft']} of 10. {r['craft_why']}")
        need = sorted({m["point"] for m in d.get("message_map") or []} & asks)
        if need:
            L.append(f"- Needs your yes on {len(need)} promise(s) not on file: {', '.join(need)}")
        L += (["- What pulled them in:"] + [f"  - {x}" for x in r["pulled"]] if r["pulled"] else [])
        L += (["- Why the others did not:"] + [f"  - {x}" for x in r["left"]] if r["left"] else []) + [""]
    out = os.path.join(folder, "results.md")
    open(out, "w", encoding="utf-8").write("\n".join(L))
    for k in ranked:
        print(f"{'Today' if k == 'today' else 'Draft ' + k}: {row[k]['share']} of {total} buyers, craft {row[k]['craft']}")
    print(f"Wrote {out}")
    return 0


SCHEMA = {
    "hero": {"eyebrow": "the pain line above the headline, a question, 14 words or fewer",
             "h1": "the offer as the headline: what they get, by when; 55 characters or fewer, so it fits three lines",
             "sub": "the line under it: one or two full sentences, 35 words or fewer"},
    "problem": {"heading": "8 words or fewer", "body": "explain the situation before the pitch, 60 words or fewer"},
    "audit": {"heading": "8 words or fewer", "bullets": "four full sentences, 16 words or fewer each"},
    "steps": {"heading": "10 words or fewer", "rows": "four rows, each 'Step name: one full sentence', 16 words or fewer"},
    "benefit": {"heading": "the benefit, 10 words or fewer", "body": "one full sentence, 25 words or fewer",
                "bullets": "three full sentences with a subject and a verb: the feature, so they get the benefit, which means an outcome they can picture; 20 words or fewer each"},
    "videos": {"heading": "8 words or fewer", "sub": "a reason to press play, 20 words or fewer, honest about what the videos show"},
    "reviews": {"heading": "8 words or fewer", "sub": "15 words or fewer"},
    "terms": {"heading": "10 words or fewer", "bullets": "one full sentence per talking point, 18 words or fewer each"},
    "faq": {"heading": "6 words or fewer", "items": "one [question, answer] pair per talking point, answer 35 words or fewer"},
    "close": {"heading": "8 words or fewer", "body": "30 words or fewer", "button": "4 words or fewer, says the outcome"},
}


def key_of(s):
    return f"{'benefit' if s['type'].startswith('benefit') else s['type']}:{'+'.join(s['says'])}"


def needed(folder):
    """Every section the three pages use, once: its talking points, its sources, its fields. The writers' brief."""
    pool, drafts, _ = load(folder)
    text = {p["id"]: p for p in pool["points"]}
    need = {}
    for k, d in drafts.items():
        for s in structure(d, pool):
            if s["type"] in STRIPS or not s["says"]:
                continue
            kind = "benefit" if s["type"].startswith("benefit") else s["type"]
            if kind not in SCHEMA:
                sys.exit(f"{s['type']}: no field schema - add one to SCHEMA in drafts.py")
            n = need.setdefault(key_of(s), {"kind": kind, "used_by": [], "fields": SCHEMA[kind],
                                            "points": [{"id": p, "point": text[p]["point"], "source": text[p].get("source", "")} for p in s["says"]]})
            n["used_by"].append(f"Draft {k}, {s['type']}")
    out = os.path.join(folder, "options-needed.json")
    json.dump(need, open(out, "w"), indent=1, ensure_ascii=False)
    print(f"{len(need)} sections to write, ten options each: {out}")
    return 0


def show(folder):
    from audit.drafts_show import render
    pool, drafts, today = load(folder)
    out = os.path.join(folder, "drafts.html")
    open(out, "w", encoding="utf-8").write(render(pool, drafts, today))
    print(f"Wrote {os.path.abspath(out)}")
    return 0


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("action", choices=("check", "show", "prepare", "results", "needed"))
    ap.add_argument("folder")
    a = ap.parse_args()
    if not os.path.exists(os.path.join(a.folder, "points.json")):
        sys.exit(f"No points.json in {a.folder}. Write the pool of talking points first.")
    return {"check": check, "show": show, "prepare": prepare, "results": results, "needed": needed}[a.action](a.folder)


if __name__ == "__main__":
    sys.exit(main())
