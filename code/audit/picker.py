"""The page picker: three page types to rotate and lock, then ten options per section to rotate, scored.

    python3 code/audit/picker.py context/pages/<slug>/drafts     # writes picker.html beside the drafts

⛔ WHAT IT IS (Jono, 28 September 2026). A dashboard like the audit report: the page on the left, a sidebar on
the right. The owner rotates between the three page types (drafts.py maps, drawn in the design kit with generic
words), locks one in, then clicks a section and rotates its ten options. Each option shows five scores out of
ten, the same measures as /audit: will they stay (the buyers), the reading grade, the length, benefits and
outcomes over features, and how clear it is. There is always a "write your own". The owner decides; the scores
are there for feedback. 1 to 3 options per section are marked ideal: the best thing to say, even before the
proof is on file, labelled with what it needs. Everything the owner supplies is a placeholder.

⛔ THE BIG PICTURE STAYS ON TOP. The big idea and its message map head the sidebar, and a live check counts every
talking point across the whole assembled page: each point once, a second time only at the close.

⛔ THE FORM CARRIES INTO THE THANK-YOU PAGE, AND SOMEONE VERIFIES IT. The thank-you page is drawn at the end with
the form's answers in it, and the picks cannot be downloaded as done until the owner ticks that a real test lead
went through: it arrived, and they landed on the thank-you page.

Reads the drafts folder: points.json, draft-*.json, options-*.json (the words), scores-*.json (one per buyer,
{"<option key>": [ten leave risks, 0 to 10]}). Writes picker.html. Choices live in the browser and download as
picks.json, which the build reads.
"""
import glob
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))

from audit import picker_page as PG  # noqa: E402
from audit import picker_ui as UI  # noqa: E402
from audit.drafts import ASK_OWNER, NAMES, STRIPS, load, structure  # noqa: E402
from audit.eighteen import PAGE  # noqa: E402
from audit.motivations import MOTIVATIONS  # noqa: E402
from audit.plain import ABSTRACT, chain_mix, section_grade  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(HERE))
# How each component is drawn in the picker, and the line that says so.
HOW = {1: "slot", 2: "slot", 9: "slot", 13: "sample", 24: "slot", 12: "slot", 6: "slot", 10: "slot"}
NOTE = {1: "A placeholder beside the headline until you film it.",
        9: "A placeholder under the form button and on the thank-you page, until your call-back time is real.", 2: "Three real faces; the rating line and two ticks are placeholders.",
        13: "Sample scores on Google, Trustpilot, G2 and Trustindex, until you add your real ones.",
        24: "Six placeholders under the first screen.", 23: "You pick up to four: the numbers on file, or the blueprint's own as placeholders.", 12: "What they get for filling in the form, with a placeholder picture beside it.",
        6: "2 real client videos, with placeholders up to this page's count: 3 short, 6 medium, 9 long.",
        10: "3 real reviews, with placeholders up to this page's count: 6 short, 9 medium or long.",
        3: "Both buttons in every section.", 17: "Shows in the phone view.", 21: "Drawn after the form, with the form's answers in it.",
        7: "Three benefit sections.", 8: "Scored as Length on every option.", 18: "Scored as Benefits and Clarity on every option.",
        16: "Every picture is a placeholder until you add your own.", 19: "Measured once the page is built."}
LIMIT = {"hero": 60, "faq": 250, "videos": 60, "reviews": 40, "steps": 80, "close": 80}
# Phrases that sound like something and promise nothing a visitor can check.
VAGUE = ["help you", "grow your business", "next level", "online presence", "digital presence", "boost your", "elevate",
         "maximize", "take your business", "get results", "real results", "the right people", "more visibility",
         "stand out", "dominate", "skyrocket", "success", "peace of mind", "hassle", "game plan"]
# What any buyer can check; the business's own nouns come from the pool's vocabulary (sell_filter.vocabulary).
CONCRETE = re.compile(r"\d|\$|\[|\b(?:week|weeks|minute|minutes|hour|hours|day|days|month|months|date|call|calls|phone|email|"
                      r"review|reviews|form)\b", re.I)


def key_of(s):
    return f"{'benefit' if s['type'].startswith('benefit') else s['type']}:{'+'.join(s['says'])}"


def lines_of(f):
    out = []
    for k in ("eyebrow", "h1", "heading", "sub", "body", "button"):
        if f.get(k):
            out.append(f[k])
    out += list(f.get("bullets") or []) + list(f.get("rows") or [])
    for qa in f.get("items") or []:
        out += list(qa)
    return out


def measure(kind, f, concrete_words=()):
    """Four of the five scores, out of ten, by code. The fifth, will they stay, comes from the buyers."""
    lines = lines_of(f)
    text = " ".join(lines)
    words = len(re.findall(r"[\w$'+-]+", text))
    limit = LIMIT.get(kind, 80)
    r = words / limit
    length = 10 if r <= 0.8 else max(0.0, 10 - (r - 0.8) * 12.5)
    body = [x for x in lines if x not in (f.get("heading"), f.get("h1"), f.get("eyebrow"), f.get("button"))]
    g = section_grade(body)
    reading = 10 if g is None or g <= 7 else max(0.0, 10 - (g - 7) * 1.5)
    mix = chain_mix(body)
    benefits = 10 * (0.6 * mix["benefits"] + mix["outcomes"]) / mix["lines"] if mix["lines"] else 10
    low = text.lower()
    abstract = sorted({w for w in re.findall(r"[a-z][a-z-]*", low) if w in ABSTRACT})
    vague = [p for p in VAGUE if p in low]
    solid = lambda x: bool(CONCRETE.search(x)) or any(w in x.lower() for w in concrete_words)  # noqa: E731
    concrete = sum(1 for x in body if solid(x)) / len(body) if body else 1
    clarity = max(0.0, 10 - 2 * len(abstract) - 1.5 * len(vague)) * (0.6 + 0.4 * concrete)
    return {"reading": round(reading, 1), "length": round(length, 1), "benefits": round(min(10, benefits), 1),
            "clarity": round(clarity, 1),
            "raw": {"grade": g, "words": words, "limit": limit, "mix": mix["verdict"] or "-", "vague": abstract + vague}}


def buyers():
    import build_persona_dashboard as bpd
    pdir = bpd.DEFAULT_DIR
    out = []
    for f in sorted(os.listdir(pdir)):
        if f.endswith(".md") and f.lower() not in bpd.NOT_A_PERSONA:
            p = bpd.parse_persona(os.path.join(pdir, f))
            if (p.get("share") or 0) > 0:
                out.append({"name": p["name"].split("·")[0].strip(), "share": p["share"], "approved": bool(p["approved"]),
                            "slug": f[:-3]})
    return out


def stays(key, i, reads, people):
    got = [(p, reads[p["slug"]][key][i]) for p in people if key in reads.get(p["slug"], {}) and i < len(reads[p["slug"]][key])]
    if not got:
        return None, []
    total = sum(p["share"] for p, _ in got) or 1
    risk = sum(p["share"] * r for p, r in got) / total
    return round(10 - risk, 1), [{"name": p["name"], "risk": r} for p, r in got]


def options(folder, people):
    opts = {}
    for p in sorted(glob.glob(os.path.join(folder, "options-*.json"))):
        if not p.endswith("options-needed.json"):
            opts.update(json.load(open(p, encoding="utf-8")))
    reads = {}
    for p in glob.glob(os.path.join(folder, "scores-*.json")):
        reads[os.path.basename(p)[7:-5]] = json.load(open(p, encoding="utf-8"))
    from audit.sell_filter import gates, vocabulary
    from check_page_quality import proof_numbers
    pool = json.load(open(os.path.join(folder, "points.json"), encoding="utf-8"))
    vocab = vocabulary(pool)
    repeats = [{"label": p["point"], "match": p["match"]} for p in pool["points"] if p.get("match")]
    known, dropped = proof_numbers(), 0
    for key, lst in list(opts.items()):
        kind, keep = key.split(":")[0], []
        for i, o in enumerate(lst):
            sc = measure(kind, o["fields"], vocab["concrete"])
            sc["stays"], sc["buyers"] = stays(key, i, reads, people)
            got = [sc[k] for k in ("stays", "reading", "length", "benefits", "clarity") if sc[k] is not None]
            sc["overall"] = round(sum(got) / len(got), 1)
            o["scores"] = sc
            if gates(kind, o, sc, known, repeats, vocab)[0]:  # only options that sell reach the owner (sell_filter.py)
                keep.append(o)
            else:
                dropped += 1
        opts[key] = keep
    if dropped:
        print(f"{dropped} option(s) failed the sell filter and are hidden. Run sell_filter.py for why, and rewrite them.")
    return opts


def headline(t, cap=60):
    """A talking point cut to a heading that fits three lines: its first clause, the rest goes under it."""
    if len(t) <= cap:
        return t, ""
    for sep in (": ", ". ", ", so ", ", "):
        i = t.find(sep)
        if 12 <= i <= cap:
            return t[:i].rstrip(",.:"), t[i + len(sep):].strip()
    cut = t[:cap].rsplit(" ", 1)[0]
    return cut, t[len(cut):].strip()


def generic(kind, says, text, ask, short=None):
    """The words a page type shows before it is locked: its talking points, plainly, so the shape is judged, not the words."""
    short = short or {}
    t = [text.get(p, p) for p in says]
    if kind == "hero":
        h1 = short.get(says[1] if len(says) > 1 else says[0]) or (t[1] if len(t) > 1 else t[0])
        return {"eyebrow": t[0].rstrip(".") + "?", "h1": h1, "sub": ". ".join(t[1:])}
    if kind == "faq":
        return {"heading": "Questions", "items": [["[The question a buyer asks]", x] for x in t]}
    if kind == "close":
        return {"heading": "Get in touch", "body": ". ".join(t), "button": "Call me back" if ask == "call" else PG.form_button()}
    if kind in ("videos", "reviews"):
        return {"heading": {"videos": "Two owners, on camera", "reviews": "What paying clients say"}[kind], "sub": t[0] if kind == "videos" else ""}
    if kind in ("terms", "audit"):
        return {"heading": {"terms": "The terms", "audit": "What you get first"}[kind], "bullets": t}
    if kind == "steps":
        return {"heading": "How it works", "rows": t}
    head, rest = headline(t[0])
    return {"heading": head, "body": ". ".join(x for x in [rest] + t[1:] if x)}


LABEL = {"hero": "The first screen", "logos": "Client logos", "stats": "The numbers", "problem": "The problem", "audit": "What you get first",
         "steps": "How it works", "videos": "Client videos", "reviews": "Written reviews", "terms": "The terms", "faq": "Questions",
         "close": "The form", "legal": "The legal line", "founder": "The founder video"}
FIRST = {"hero-form": "the form beside the headline", "hero-video": "the founder video beside the headline",
         "hero-center": "centred, over a wide founder video"}
LOOK = {"paper": "paper, white with blue buttons", "field": "the brand-blue field", "ink": "dark ink"}


def differences(k, drafts, pool):
    """What this page type does that the other two do not: the structure, in plain lines."""
    st = {x: [s["type"] for s in structure(d, pool)] for x, d in drafts.items()}
    d, mine = drafts[k], st[k]
    others = [st[x] for x in st if x != k]
    hero = structure(d, pool)[0]["layout"]
    vids, revs = PG.COUNTS.get(d.get("length"), PG.COUNTS["long"])
    first_after = next((t for t in mine[1:] if t not in ("logos", "stats", "founder")), "")
    same = lambda t: t.startswith("benefit") or t == "founder"  # noqa: E731 - the founder video is on all three, only its place moves
    only = [t for t in dict.fromkeys(mine) if not same(t) and all(t not in o for o in others)]
    left = [t for t in dict.fromkeys(sum(others, [])) if not same(t) and t not in mine]
    lab = lambda t: LABEL.get(t) or ("Benefit " + t.split("-")[1] if t.startswith("benefit-") else t)  # noqa: E731
    lines = [f"First screen: {FIRST.get(hero, hero)}",
             f"Length: {d.get('length', '')}, {len(mine)} sections, {vids} client videos and {revs} reviews",
             "Form: in the first screen, and again at the end" if d.get("form") == "hero" else
             f"Form: at the end, {'the call first' if d.get('ask') == 'call' else 'the form first'}",
             f"After the first screen: {lab(first_after)}",
             f"Look: {LOOK.get(d.get('look'), '')}"]
    if only:
        lines.append("Only on this page: " + ", ".join(lab(t) for t in only))
    if left:
        lines.append("Left out: " + ", ".join(lab(t) for t in left))
    return lines


def vocabulary_words(pool):
    from audit.sell_filter import vocabulary
    return vocabulary(pool)["concrete"]


def business_proof(folder, stats):
    """The business this page is for: drafts/proof.json, written from its own proof.md, quote bank and
    business.md. Missing pieces stay empty, and the page shows a placeholder in their place.
      {"business", "phone", "reviews": [{"name", "meta", "quote", "photo"}], "videos": [{"id", "name", "who", "result"}],
       "faces": ["/images/..."], "results_note"}"""
    import _business
    p = os.path.join(folder, "proof.json")
    biz = json.load(open(p, encoding="utf-8")) if os.path.exists(p) else {}
    biz.setdefault("business", _business.name())
    biz["stats"] = [x for x in stats if not x.get("needs")] or [x for x in stats]
    return biz


def build(folder):
    pool, drafts, _ = load(folder)
    text = {p["id"]: p["point"] for p in pool["points"]}
    short = {p["id"]: p["short"] for p in pool["points"] if p.get("short")}  # a headline-length form of an offer
    asks = {p["id"] for p in pool["points"] if str(p.get("source", "")).lower() == ASK_OWNER}
    people = buyers()
    opts = options(folder, people)
    faces = ""   # the faces come from proof.json now; kept as an argument for the page functions
    stat_pool = pool.get("stats") or []
    PG.use(business_proof(folder, stat_pool), os.path.relpath(os.path.join(ROOT, "website", "public"), folder))
    pages, htmls = {}, []
    for k, d in drafts.items():
        ask = d.get("ask", "call")
        form_text = PG.form_button() if ask == "form" else "Get a call back"
        st, secs, white = structure(d, pool), [], False
        body = [PG.topline()]
        for n, s in enumerate(st, 1):
            kind = "benefit" if s["type"].startswith("benefit") else s["type"]
            key = key_of(s) if s["type"] not in STRIPS and s["says"] else ("stats:bar" if s["type"] == "stats" else "")
            white = not white if s["layout"] not in ("hero-video", "hero-form", "hero-center", "form-split", "legal-line", "logo-row", "stat-row", "founder-band") else white
            body.append(f'<div class="sec" data-n="{n}" data-key="{key}" data-type="{s["type"]}"><span class="n">{n}</span>'
                        f'{PG.section(s, ask, form_text, faces, white, d.get("look", "field"), d.get("length", "long"))}</div>')
            secs.append({"n": n, "type": s["type"], "kind": kind, "key": key, "ids": s["says"], "says": [text.get(p, p) for p in s["says"]],
                         "holds": s["holds"], "generic": generic(kind, s["says"], text, ask, short) if key and kind != "stats" else None,
                         "options": key in opts, "special": "stats" if kind == "stats" else ""})
        body.append(PG.mobile_bar(ask, form_text))
        htmls.append(f'<div class="page" data-page="{k}" hidden><div class="frame"><div class="scaler"><div class="cs">{"".join(body)}</div></div></div>'
                     f'{UI.thanks(PG, ask)}</div>')
        held = {n for s in st for n in s["holds"]}
        skip = {int(x): why for x, why in (pool.get("not_here") or {}).items()}
        comps = [{"n": n, "name": NAMES[n], "state": "page" if n in PAGE else "not" if n in skip else HOW.get(n, "here") if n in held else "missing",
                  "why": skip.get(n) or NOTE.get(n, "")} for n in NAMES]
        pages[k] = {"big_idea": d.get("big_idea", ""), "motivation": MOTIVATIONS.get(d.get("motivation"), {}).get("label", ""),
                    "ask": ask, "look": d.get("look", "field"), "form": d.get("form", "end"), "length": d.get("length", ""),
                    "sections": secs, "components": comps, "diff": differences(k, drafts, pool),
                    "map": [{"section": m["section"], "point": text.get(m["point"], m["point"])} for m in d.get("message_map") or []],
                    "needs": [text[m["point"]] for m in d.get("message_map") or [] if m["point"] in asks]}
    repeats = [{"id": p["id"], "label": p["point"], "match": p["match"], "cap": p.get("cap", 2)} for p in pool["points"] if p.get("match")]
    static = [{"type": "videos", "text": PG.BIZ["results_note"]}] if PG.BIZ["results_note"] else []
    data = {"static": static, "stats": stat_pool, "concrete": vocabulary_words(pool), "slug": os.path.basename(os.path.dirname(os.path.abspath(folder))), "pages": pages, "options": opts, "buyers": people,
            "approved": all(p["approved"] for p in people) if people else False, "repeats": repeats, "limits": LIMIT,
            "abstract": sorted(ABSTRACT), "vague": VAGUE}
    out = os.path.join(folder, "picker.html")
    kp = os.path.join(folder, "kit.json")   # the owner's own design kit, when the page has one
    kit = json.load(open(kp, encoding="utf-8")) if os.path.exists(kp) else None
    open(out, "w", encoding="utf-8").write(UI.document(data, "".join(htmls), kit))
    missing = [s["key"] for pg in pages.values() for s in pg["sections"] if s["key"] and not s["options"] and not s["special"]]
    print(f"Wrote {os.path.abspath(out)}")
    if missing:
        print(f"{len(set(missing))} section(s) have no options yet: " + ", ".join(sorted(set(missing))))
    return 0


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__.split("\n\n")[1])
    sys.exit(build(sys.argv[1]))
