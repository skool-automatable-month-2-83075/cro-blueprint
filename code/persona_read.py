"""Your buyers read the page, section by section, drawn on the page itself - the same look as the audit.

    python3 code/persona_read.py prepare context/pages/<slug>          # one answer sheet per approved buyer
    python3 code/persona_read.py write context/pages/<slug>            # check every sheet, draw personas.html, log the round

The audit cuts the page into sections and screenshots each one (`code/audit/page_audit.py <url>`).
This reads those same sections through each buyer's eyes: where they keep reading, what each
section answers for them, what it leaves open, where they close the tab, and the words that would
keep them. One subagent per buyer fills one sheet in `<page>/persona-read/`; this script checks the
sheets and draws `<page>/personas.html`.

What the check refuses, because every rewrite is a line the owner is about to publish:
  - a section with no reaction (reads on | leaves) or no tone (answers | misses | neutral)
  - a rewrite whose "before" is not really on the page - quoted, never paraphrased
  - a rewrite that adds a number not in context/proof.md, unless it sits in [brackets]
  - a rewrite with no buying motivation, or not resting on a line from the buyer's own file
  - a rewrite of a client's own words

Non-buyers read the page too. Their notes are shown; they never vote and never reach "Do these first".
"""
import argparse
import hashlib
import json
import os
import re
import sys
from datetime import date

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import _posthog as ph  # noqa: E402  only for ROOT
import build_persona_dashboard as bpd  # noqa: E402
from audit import report_html as RH  # noqa: E402  the audit's own styles, so both pages look the same
from audit.motivations import MOTIVATIONS  # noqa: E402
from audit.plain import chain_line  # noqa: E402  the audit's own feature / benefit / outcome test
from audit.sections import TYPES  # noqa: E402

ROOT = ph.ROOT
PROOF = os.path.join(ROOT, "context", "proof.md")
SHEETS = "persona-read"
OUT = "personas.html"
REACTIONS = ("reads on", "leaves")
TONES = ("answers", "misses", "neutral")
QUOTE_KINDS = ("proof_quotes", "proof_video")      # a client's own words are never rewritten
# the same order and colours as the persona dashboard, so a buyer is one colour everywhere
COL = ["#c96442", "#3b6ea5", "#3d7a4a", "#8a6a0c", "#7a4a8a", "#2f7f86", "#a14a6b", "#5b6b2f", "#6e6d66"]  # last = non-buyers

PROMPT = """You are reading a landing page on behalf of one specific buyer, described in the attached persona file. Answer in the third person about that buyer. Do not answer as yourself and do not be helpful to the page owner.

The buyer is on the device named in the file, has one tab open and has been burned before. They do not want the page to succeed. They read top to bottom and stop the moment a section gives them a reason to.

Read only the persona file, the proof file, the section screenshots in order and the words listed for each section. A phone buyer judges the first screen from the phone screenshot, not the desktop one. Quote the buyer's own lines from the file when you reason about them. If the file has no evidence for a reaction, say "no evidence in file" rather than inventing one.

Fill the answer sheet, one entry per section, in order:
- reaction: "leaves" if this is where the buyer closes the tab, otherwise "reads on". Keep going after a "leaves" and judge the rest as if an earlier fix had kept them - the owner needs every section read.
- tone: "answers" if the section answers something the file says they need, "misses" if they needed something here and did not get it, "neutral" if there is nothing here for them either way.
- quote: the exact words on the page this is about, copied, never paraphrased. Empty when neutral.
- says: one sentence, third person, what the buyer thinks here and which line of their file it comes from.
- rewrite, only when tone is "misses" or reaction is "leaves": before (the exact page words), after (the one line that would keep this buyer, in their language, under grade 10: lead with what it means for them, and never stop at a feature - the thing, so they get the benefit, which means something they can picture: a call, a job, money, hours back), moves (one of the two or three motivations the file lists under "Moves them" - never another), because (the verbatim line from their file it rests on). Never add a number that is not in the proof file - write [number] instead. Never rewrite a client's own words. Change words only: never remove or add a picture, a video, a section, a heading or a paragraph. A rewrite keeps the shape of what it replaces - a label stays a label, a heading stays a heading, a paragraph stays a paragraph, and it is never longer than it needs to be. If what the buyer needs here is a real thing only the owner can supply - a photo of finished work, a review count, a recorded video - write it in needs, in plain words, and change nothing on the page for it.

Then at the end: unanswered (the one question the whole page never answers for this buyer, in their words, or "none"), acts (yes only if, with no section making them leave, this buyer would fill in the form or call on this visit), acts_why (one sentence: what makes them act, or what stops them), out_of_control (yes if the reason they leave is price, area, hours or availability as the file lists it), confirmed_by (the call, email or search term in their file that confirms the leave reason, or "none")."""


# --------------------------------------------------------------------------- the page

def _load(path, what):
    if not os.path.exists(path):
        sys.exit(f"{os.path.relpath(path, ROOT)} is missing. {what}")
    return json.load(open(path, encoding="utf-8"))


def load_page(pdir):
    """The audit's bands, screenshots and page text. Nothing is re-measured here."""
    need = _load(os.path.join(pdir, "judgments-needed.json"),
                 "Run `python3 code/audit/page_audit.py <url>` first - it cuts the page into sections.")
    cards = need.get("cards") or []
    if not cards:
        sys.exit("This page's audit is from before sections existed. Re-run `python3 code/audit/page_audit.py <url>`.")
    cap = _load(os.path.join(pdir, "capture.json"), "Re-run the audit capture.")
    judged = {}
    jpath = os.path.join(pdir, "judgments.json")
    if os.path.exists(jpath):
        judged = {c["id"]: c for c in (json.load(open(jpath)).get("cards") or []) if c.get("id")}
    desk, mob = cap["viewports"]["desktop"], cap["viewports"]["mobile"]
    # names Claude set from the screenshots win over the code's guesses, and survive a re-run
    named = {}
    npath = os.path.join(pdir, SHEETS, "needed.json")
    if os.path.exists(npath):
        named = {x["id"]: x for x in json.load(open(npath, encoding="utf-8")).get("sections") or []}
    bands = [{"id": c["id"], "n": c["n"], "top": c["top"], "h": c["h"],
              "kind": (named.get(c["id"]) or {}).get("kind") or (judged.get(c["id"]) or {}).get("kind")
                      or c.get("kind_guess") or "other",
              "name": (named.get(c["id"]) or {}).get("name") or band_name(c, judged.get(c["id"])),
              "screenshot": c.get("screenshot", ""),
              "heading": ((c.get("code_sees") or {}).get("heading") or "").strip(),
              "words": (c.get("code_sees") or {}).get("text") or []} for c in cards]
    return {"url": cap.get("url") or "", "bands": bands,
            "page_h": int(desk["facts"].get("scrollHeight") or 0) or max(b["top"] + b["h"] for b in bands),
            "page_w": int((desk["facts"].get("viewport") or {}).get("w") or 1366),
            "full": desk["shots"].get("full") or "", "phone_fold": mob["shots"].get("fold") or "",
            "text": norm(cap.get("html_text") or " ".join(w for b in bands for w in b["words"]))}


def band_name(card, judged):
    """The owner's name for a section: the audit's judged name, else its heading, else its kind."""
    if judged and judged.get("is"):
        return judged["is"]
    head = ((card.get("code_sees") or {}).get("heading") or "").strip()
    if head and not re.match(r"^\[.*\]$", head) and len(head) <= 60:
        return head
    label = (TYPES.get(card.get("kind_guess") or "other") or TYPES["other"])["label"]
    return label[0].upper() + label[1:]


def norm(s):
    s = str(s or "").lower().replace("’", "'").replace("‘", "'").replace("“", '"').replace("”", '"')
    return re.sub(r"\s+", " ", re.sub(r"[^\w$%'\[\] ]+", " ", s)).strip()


# --------------------------------------------------------------------------- the buyers

def load_buyers():
    pdir = bpd.DEFAULT_DIR
    files = sorted(f for f in os.listdir(pdir) if f.endswith(".md") and f.lower() not in bpd.NOT_A_PERSONA)
    people = [bpd.parse_persona(os.path.join(pdir, f)) for f in files]
    if not people:
        sys.exit("No buyers yet. Run /personas research first.")
    waiting = [p["name"] for p in people if not p["approved"]]
    if waiting:
        sys.exit(f"Not approved yet: {', '.join(waiting)}. Nobody reads the page for a buyer the owner has not signed off.")
    buyers = sorted([p for p in people if (p["share"] or 0) > 0], key=lambda p: (not p["primary"], -(p["share"] or 0)))
    others = [p for p in people if not (p["share"] or 0) > 0]
    ci = 1
    for p in buyers:
        if p["primary"]:
            p["color"] = COL[0]
        else:
            p["color"], ci = COL[1 + (ci - 1) % (len(COL) - 2)], ci + 1
        p["weighted"] = True
    for p in others:
        p["color"], p["weighted"] = COL[-1], False
    for p in buyers + others:
        p["device"] = device_of(p)
        p["slug"] = p["id"].replace("p-", "", 1)
    return buyers + others


def device_of(p):
    """Whichever of phone or desktop the file names first. The subagent sees the matching first screen."""
    text = " ".join((p["fields"] or {}).get("device and moment") or []).lower()
    ph_at = min([i for i in (text.find("phone"), text.find("mobile")) if i >= 0] or [10 ** 6])
    dk_at = min([i for i in (text.find("desktop"), text.find("laptop"), text.find("computer")) if i >= 0] or [10 ** 6])
    return "phone" if ph_at < dk_at else "desktop"


# --------------------------------------------------------------------------- prepare

def prepare(pdir, fresh=False):
    page, buyers = load_page(pdir), load_buyers()
    sdir = os.path.join(pdir, SHEETS)
    os.makedirs(sdir, exist_ok=True)
    rel = lambda p: os.path.relpath(p, ROOT) if p else ""
    npath = os.path.join(sdir, "needed.json")
    old_id = json.load(open(npath)).get("read_id") if os.path.exists(npath) else None
    fresh_any = fresh or any(not os.path.exists(os.path.join(sdir, f"{p['slug']}.json")) for p in buyers)
    read_id = date.today().isoformat() + "-" + hashlib.sha1(os.urandom(8)).hexdigest()[:6] if (fresh_any or not old_id) else old_id
    shared = {"url": page["url"], "proof": rel(PROOF), "prompt": PROMPT, "read_id": read_id,
              "phone_first_screen": rel(page["phone_fold"]),
              "sections": [{"id": b["id"], "n": b["n"], "name": b["name"], "kind": b["kind"],
                            "screenshot": rel(os.path.join(pdir, b["screenshot"])), "words": b["words"]}
                           for b in page["bands"]]}
    json.dump(shared, open(npath, "w"), indent=1, ensure_ascii=False)
    made = []
    for p in buyers:
        path = os.path.join(sdir, f"{p['slug']}.json")
        if os.path.exists(path) and not fresh:
            made.append((p, path, "kept"))
            continue
        sheet = {"buyer": p["name"], "file": f"context/personas/{p['file']}", "device": p["device"],
                 "weighted": p["weighted"], "model": "", "unanswered": "", "acts": None, "acts_why": "",
                 "out_of_control": None, "confirmed_by": "none",
                 "sections": [{"id": b["id"], "n": b["n"], "name": b["name"], "reaction": None, "tone": None,
                               "quote": "", "says": "", "rewrite": None, "needs": ""} for b in page["bands"]]}
        json.dump(sheet, open(path, "w"), indent=1, ensure_ascii=False)
        made.append((p, path, "new"))
    print(f"{len(page['bands'])} sections from the audit · {len(buyers)} readers")
    print(f"Shared: {rel(os.path.join(sdir, 'needed.json'))} (the prompt, the sections, the screenshots)")
    for p, path, st in made:
        who = "never paid, not counted" if not p["weighted"] else "one of the buyers"
        print(f"- {p['name']} · {p['device']} · {who} · {rel(path)} ({st})")
    print("Next: one subagent per sheet, in parallel, fresh context. Each gets its persona file, the proof file, "
          "needed.json and its own sheet - nothing from another buyer. Then `write`.")


# --------------------------------------------------------------------------- the check

NUM = re.compile(r"\$?\d[\d,.]*\+?%?")


def numbers(s):
    """Every number in the text, as bare digits, ignoring anything inside [brackets]."""
    raw = NUM.findall(re.sub(r"\[[^\]]*\]", " ", s or ""))
    return {re.sub(r"[.]$", "", n.replace(",", "").replace("$", "").replace("+", "")) for n in raw} - {""}


def check_sheet(sheet, page, proof_nums, quotes_of, moves_of=lambda who: []):
    """Every problem, in plain words. An empty list is the only pass."""
    P, who = [], sheet.get("buyer", "?")
    by_id = {b["id"]: b for b in page["bands"]}
    got = [s.get("id") for s in sheet.get("sections") or []]
    if got != [b["id"] for b in page["bands"]]:
        return [f"{who}: the sheet does not list the page's {len(page['bands'])} sections in order - re-run prepare with --fresh"]
    for s in sheet["sections"]:
        where = f"{who}, section {s['n']}"
        if s.get("reaction") not in REACTIONS:
            P.append(f"{where}: reaction must be one of {', '.join(REACTIONS)}")
        if s.get("tone") not in TONES:
            P.append(f"{where}: tone must be one of {', '.join(TONES)}")
        if s.get("tone") != "neutral" and not (s.get("says") or "").strip():
            P.append(f"{where}: says is empty")
        if s.get("quote") and norm(s["quote"]) not in page["text"]:
            P.append(f"{where}: the quote is not on the page, word for word: \"{s['quote'][:60]}\"")
        rw = s.get("rewrite")
        needs = s.get("tone") == "misses" or s.get("reaction") == "leaves"
        if needs and not rw and not (s.get("needs") or "").strip():
            P.append(f"{where}: a miss or a leave says what they needed - a rewrite, or one line in needs")
        if rw:
            P += check_rewrite(rw, where, by_id[s["id"]], page, proof_nums, quotes_of(who), moves_of(who))
    if sheet.get("out_of_control") not in (True, False, "yes", "no"):
        P.append(f"{who}: out_of_control must be yes or no")
    acts, ex = sheet.get("acts"), exit_of(sheet)
    if acts not in (True, False, "yes", "no"):
        P.append(f"{who}: acts must be yes or no - would they fill in the form or call on this visit")
    elif yes(acts) and ex:
        P.append(f"{who}: acts is yes but they leave at section {ex['n']} - a buyer who closed the tab does not act")
    elif not yes(acts) and not ex and not any(s.get("rewrite") for s in sheet["sections"]):
        P.append(f"{who}: reads to the end but does not act, so some section must say what stops them, with a rewrite")
    if acts in (True, False, "yes", "no") and not (sheet.get("acts_why") or "").strip():
        P.append(f"{who}: acts_why is empty")
    if not (sheet.get("unanswered") or "").strip():
        P.append(f"{who}: unanswered is empty - the one question the page never answers for them, or none")
    return P


def yes(v):
    return v in (True, "yes")


def shape(before, after, band, where):
    """A rewrite keeps the shape of what it replaces. On 28 September 2026 the first rebuild turned
    two-word labels and short headings into twenty-word sentences, and the page read as paragraphs."""
    wb, wa = len(before.split()), len(after.split())
    heading = overlaps(before, band.get("heading")) and wb <= 16
    if wb <= 4:
        cap, kind = max(6, wb + 3), "a label"
    elif heading or wb <= 12:
        cap, kind = max(12, round(wb * 1.4)), "a heading"
    else:
        cap, kind = round(wb * 1.3) + 5, "a paragraph"
    if wa > cap:
        return [f"{where}: {kind} of {wb} words became {wa} - keep it {kind}, {cap} words at most"]
    if kind == "a paragraph" and wa < wb * 0.4:
        return [f"{where}: a paragraph of {wb} words became {wa} - a paragraph stays a paragraph"]
    return []


PLACEHOLDER = re.compile(r"\[[^\]]+\]|placeholder|to add\b", re.I)


def check_rewrite(rw, where, band, page, proof_nums, own_lines, own_moves=()):
    P = []
    before, after = rw.get("before") or "", rw.get("after") or ""
    if not before or norm(before) not in page["text"]:
        P.append(f"{where}: the rewrite's before is not on the page, word for word: \"{before[:60]}\"")
    if not after.strip():
        P.append(f"{where}: an empty after takes something off the page - change words only, and put what the "
                 "buyer needs from the owner in needs")
    # A rewrite is a note for the writer in /split-test, never words that go on the page as they are
    # (2 October 2026). So its length, and whether it finishes the benefit chain, no longer stop a read:
    # only what keeps it true does - the words it points at, the numbers, the buyer's own line behind it.
    new = numbers(after) - numbers(before) - proof_nums
    if new:
        P.append(f"{where}: the rewrite adds {', '.join(sorted(new))}, which is not in proof.md - use [number]")
    if rw.get("moves") not in MOTIVATIONS:
        P.append(f"{where}: moves must be one of {', '.join(MOTIVATIONS)}")
    elif own_moves and rw["moves"] not in own_moves:
        P.append(f"{where}: moves is {rw['moves']}, which is not one of what moves this buyer "
                 f"({', '.join(own_moves)}) - pull on their motivations, not the page's")
    because = norm(rw.get("because"))
    if len(because) < 12 or not any(because in q or q in because for q in own_lines if q):
        P.append(f"{where}: because must be copied from one of this buyer's Verbatim lines or their Trigger - "
                 "words they said, not a field of the file")
    return P


# --------------------------------------------------------------------------- one page, several buyers

def overlaps(a, b):
    a, b = norm(a), norm(b)
    return bool(a) and bool(b) and (a in b or b in a)


def classify(pairs, page, lost=()):
    """Which rewrites go on the page, and which need ONE line written for several buyers at once.

    No buyer wins at another's cost (Jono, 28 September 2026: "we don't fall into this trap where only one buyer
    wins and we marginalize the other five or six... keep having these personas argue back and forth... until there
    is consensus that the highest percentage of people would move forward"). Every buyer counts the same (29 September 2026):
      - a rewrite goes on wherever no other buyer reads on because of that section
      - where another buyer DOES read on because of it - anything in the first screen, or the words they quoted -
        it is a MERGE: one line that keeps their reason and brings this buyer in. It goes on the copy and every
        buyer reads it again. The read only marks it; /split-test answers it on a whole page
      - anywhere else another buyer reads on, the line goes on WATCHED: if they stop reading on there, it comes back off
      - two buyers needing the same words changed is one fix, the bigger share's line, serving both
    Buyers come in file order - none outranks another. `lost` is the buyers a read has proved this page cannot keep.
    """
    order = sorted(pairs, key=lambda x: (not x[0]["weighted"], -(x[0]["share"] or 0), not x[0]["primary"]))
    reads = {p["name"]: {x["id"]: x for x in sh["sections"]} for p, sh in pairs}
    share = {p["name"]: (p["share"] or 0) for p, _ in pairs}
    counted = [p["name"] for p, _ in pairs if p["weighted"] and p["name"] not in lost]
    hero = {b["id"] for b in page["bands"] if b["kind"] == "hero"}
    fix, merge, notes = [], [], []
    for p, sh in order:
        ex = exit_of(sh)
        for s in sh["sections"]:
            rw = s.get("rewrite")
            if not rw:
                continue
            item = {"buyer": p["name"], "share": p["share"] or 0, "primary": p["primary"], "weighted": p["weighted"],
                    "id": s["id"], "n": s["n"], "name": s["name"], "exit": bool(ex) and ex["id"] == s["id"], "also": [], **rw}
            if p["name"] in lost:
                notes.append({**item, "why": "a read proved this page cannot keep them"})
                continue
            if item["exit"] and yes(sh.get("out_of_control")):
                notes.append({**item, "why": "the reason they leave is outside the page's control"})
                continue
            keepers = [b for b in counted if b != p["name"] and reads[b][s["id"]]["tone"] == "answers"]
            touched = [b for b in keepers if s["id"] in hero or overlaps(rw["before"], reads[b][s["id"]].get("quote"))]
            if touched:
                merge.append({**item, "keep": [{"buyer": b, "quote": reads[b][s["id"]].get("quote") or ""} for b in touched],
                              "keeps": " / ".join(reads[b][s["id"]].get("quote") or "" for b in touched),
                              "keep_share": sum(share[b] for b in touched),
                              "why": "the first screen" if s["id"] in hero else "the words that keep them reading"})
                continue
            if keepers:
                item["watch"] = keepers       # it goes on; the next read checks each of them still reads on here
            same = next((f for f in fix if f["id"] == s["id"] and overlaps(f["before"], rw["before"])), None)
            if same:
                same["also"].append(p["name"])
                continue
            fix.append(item)
    fix.sort(key=lambda f: (not f["weighted"], not f["exit"], -f["share"], f["n"]))
    merge.sort(key=lambda m: (not m["weighted"], not m["exit"], -m["share"], m["n"]))
    return {"fix": fix, "merge": merge, "notes": notes, "clash": []}


# --------------------------------------------------------------------------- write

def said(p):
    """Words the buyer really said: the Verbatim lines, and the Trigger, which the file keeps in their words.
    The silent question is not one of them - it is the thing they never say out loud."""
    got = [norm(q["text"]) for q in p["quotes"]]
    got += [norm(t.split(" · ")[0]) for t in (p["fields"] or {}).get("trigger") or [] if '"' in t or "\u201c" in t]
    return [g for g in got if g]


def load_sheets(pdir, buyers):
    sdir = os.path.join(pdir, SHEETS)
    out = []
    for p in buyers:
        path = os.path.join(sdir, f"{p['slug']}.json")
        if not os.path.exists(path):
            sys.exit(f"No sheet for {p['name']}. Run `python3 code/persona_read.py prepare {os.path.relpath(pdir, ROOT)}`.")
        out.append((p, json.load(open(path, encoding="utf-8"))))
    return out


def exit_of(sheet):
    return next((s for s in sheet["sections"] if s.get("reaction") == "leaves"), None)


def write(pdir):
    page, buyers = load_page(pdir), load_buyers()
    pairs = load_sheets(pdir, buyers)
    names = {b["id"]: b["name"] for b in page["bands"]}
    for _, sh in pairs:
        for x in sh.get("sections") or []:
            x["name"] = names.get(x.get("id"), x.get("name", ""))
    proof_nums = numbers(open(PROOF, encoding="utf-8").read()) if os.path.exists(PROOF) else set()
    lines = {p["name"]: said(p) for p in buyers}
    moves = {p["name"]: p.get("moves") or [] for p in buyers}
    problems = [x for _, sh in pairs for x in check_sheet(sh, page, proof_nums, lambda w: lines.get(w, []),
                                                        lambda w: moves.get(w, []))]
    out = os.path.join(pdir, OUT)
    if problems:
        open(out, "w").write(unfinished(page["url"], problems))
        print(f"⛔ NOT FINISHED - {len(problems)} thing(s) on the sheets break a rule, so no read was drawn:")
        print("\n".join(f"   - {x}" for x in problems[:40]))
        sys.exit(1)
    conf = bpd.confidence([p for p in buyers], bpd.read_extra(bpd.DEFAULT_DIR))
    open(out, "w").write(draw(page, pairs, conf, pdir, proven_lost(pdir)))
    npath = os.path.join(pdir, SHEETS, "needed.json")
    log_round(page, pairs, out, json.load(open(npath)).get("read_id") if os.path.exists(npath) else None)
    print(f"Read: {out}")
    for p, sh in pairs:
        ex = exit_of(sh)
        print(f"- {p['name']}: " + (f"leaves at section {ex['n']}, {ex['name']}" if ex else "reads to the end"))


def proven_lost(pdir):
    """Buyers a rebuild has PROVED this page cannot keep, from its persona-build.json. None for a first read."""
    path = os.path.join(pdir, "persona-build.json")
    return json.load(open(path)).get("dealbreakers", []) if os.path.exists(path) else []


def unfinished(url, problems):
    today = date.today().strftime("%d %B %Y")
    H = [RH._head("Persona read not finished"), topbar(url, today),
         '<div class="unfinished"><h1 class="display">Not finished yet</h1>'
         '<p>Every buyer has to read every section, and every rewrite has to pass the rules, before this is drawn. '
         'What is still open:</p><ul>']
    H += [f"<li>{RH.e(p)}</li>" for p in problems[:40]]
    return "\n".join(H + ["</ul></div></body></html>"])


def topbar(url, today):
    return (f'<div class="top"><span class="mark display">{RH.MARK}Your buyers read the page</span>'
            f'<span class="url">{RH.e(url)}</span><span class="date">{RH.e(today)}</span></div>')


def log_round(page, pairs, out, read_id=None):
    """One round in context/personas/runs.json per `prepare`. Drawing again - after a reader fixes a
    rejected entry - updates that round in place; it never counts the same read twice."""
    import persona_panel as pp
    verdicts = []
    for p, sh in pairs:
        ex = exit_of(sh)
        verdicts.append({"persona": p["name"], "share": p["share"] or 0, "primary": p["primary"],
                         "verdict": "STAY" if (yes(sh.get("acts")) and not ex) else "LEAVE",
                         "element": f"section {ex['n']}, {ex['name']}" if ex else ("" if yes(sh.get("acts")) else "reads it all, does not act"),
                         "reason": (ex or {}).get("says", "") or ("" if yes(sh.get("acts")) else sh.get("acts_why", "")),
                         "out_of_control": sh.get("out_of_control") in (True, "yes"),
                         "confirmed_by": sh.get("confirmed_by") or "none"})
    path_only = re.sub(r"^https?://[^/]+", "", page["url"]) or "/"
    if path_only in ('', '/'):
        path_only = re.sub(r"^https?://(www\.)?", "", page["url"]).split("/")[0] or path_only   # a homepage is named by its site, not '/'
    run = {"page": path_only, "page_hash": hashlib.sha1(page["text"].encode()).hexdigest(), "read_id": read_id,
           "model": next((sh.get("model") for _, sh in pairs if sh.get("model")), ""),
           "note": f"section-by-section read · {len(pairs)} separate readers, none saw another",
           "markup": os.path.relpath(out, ROOT), "verdicts": verdicts,
           "dealbreakers": sorted({d["buyer"] for d in proven_lost(os.path.dirname(out))}),
           "merges": sorted({m["buyer"] for m in classify(pairs, page)["merge"] if m["exit"] and m["weighted"]})}
    runs = pp.load()
    same = next((r for r in runs if read_id and r.get("read_id") == read_id), None)
    if same:
        same.update({k: v for k, v in run.items() if k != "date"})
        same.pop("call", None)
        pp.save(runs)
        print(f"Round {same.get('round')} updated in place - the same read, drawn again.")
        pp.grid(); pp.call(); pp.redraw()
        return
    tmp = os.path.join(ph.CACHE, "panel-run.json")
    json.dump(run, open(tmp, "w"), indent=1)
    pp.log(tmp)


# --------------------------------------------------------------------------- the drawing

CSS = """
.bx.lose { --c:var(--cut-line); }  /* red outline, never the audit's hatch: that means cut the section */
.lose .num { background:var(--cut-line); } .lose .vd { color:var(--cut); background:var(--cut-bg); }
.stage .rail { position:absolute; top:0; width:6px; border-radius:3px; z-index:3; box-shadow:0 0 0 1.5px rgba(255,255,255,.9); }
.stage .exit { position:absolute; left:0; right:0; border-top:3px dashed var(--bc); z-index:6; pointer-events:none; }
.stage .exitchip { position:absolute; z-index:7; transform:translateY(-50%); font-size:13px; font-weight:600; color:#fff;
  background:var(--bc); padding:5px 12px; border-radius:99px; white-space:nowrap; box-shadow:0 2px 8px rgba(0,0,0,.25); pointer-events:none; }
.stage .exit.nb { border-top-style:dotted; } .stage .exitchip.nb { opacity:.88; }
.stage .veil { position:absolute; left:0; right:0; bottom:0; background:rgba(245,244,237,.62); z-index:2; pointer-events:none; }
.stage .veil span { position:sticky; top:10px; display:block; margin:14px auto 0; width:fit-content; font-size:13px; font-weight:600;
  color:var(--ink); background:var(--ivory); padding:6px 12px; border-radius:8px; box-shadow:0 2px 10px rgba(0,0,0,.12); }
.who { margin-top:4px; }
.by { padding:12px 0; border-top:1px solid var(--hairline); } .by:first-child { border-top:0; padding-top:4px; }
.by .nm { display:flex; align-items:center; gap:8px; font-size:15px; } .by .nm b { font-weight:600; }
.by .k { font-size:11.5px; color:var(--muted); font-family:"JetBrains Mono",ui-monospace,monospace; }
.dot { width:11px; height:11px; border-radius:50%; flex-shrink:0; display:inline-block; }
.reach { height:8px; border-radius:4px; background:var(--sand); overflow:hidden; margin:8px 0 6px; } .reach i { display:block; height:100%; border-radius:4px; }
.by .out { font-size:13px; color:var(--body); line-height:1.45; } .by .out b { color:var(--ink); font-weight:600; }
.by.nb { opacity:.72; }
.conf { font-size:12.5px; color:var(--body); margin-top:14px; padding:9px 12px; border-radius:9px; background:rgba(20,20,19,.045); line-height:1.5; }
.conf b { color:var(--ink); }
.pr { margin:12px 0 0 36px; padding-top:10px; border-top:1px solid var(--hairline); }
.pr .prh { display:flex; align-items:center; gap:7px; font-size:13px; } .pr .prh b { font-weight:600; }
.rx { font-size:10px; letter-spacing:1px; text-transform:uppercase; font-weight:700; padding:2px 7px; border-radius:4px; margin-left:auto; white-space:nowrap; }
.rx.leave { color:#fff; background:var(--cut-line); } .rx.on { color:var(--keep); background:var(--keep-bg); }
.rx.miss { color:var(--fix); background:var(--fix-bg); } .rx.past { color:var(--muted); background:rgba(20,20,19,.05); }
.pr q { display:block; font-size:12.5px; color:var(--muted); font-style:italic; quotes:none; margin-top:5px; }
.pr p { font-size:13px; color:var(--body); line-height:1.45; margin-top:4px; }
.pr .rw { margin-left:0; } .pr.nb { opacity:.7; } .pr.past p, .pr.past q { color:var(--muted); }
.mv { display:inline-block; margin-top:6px; font-size:10.5px; letter-spacing:.8px; text-transform:uppercase; font-weight:700;
  color:var(--terracotta); background:rgba(201,100,66,.09); padding:2px 7px; border-radius:4px; }
.bc { font-size:12.5px; color:var(--body); margin-top:6px; line-height:1.45; } .bc i { color:var(--ink); }
.cant p { font-size:13.5px; line-height:1.5; color:var(--ink); margin-top:8px; padding:10px 12px; border-radius:9px; background:var(--cut-bg); }
.cant p b { font-weight:600; }
.both p { font-size:13.5px; line-height:1.5; color:var(--ink); margin-top:8px; padding:10px 12px; border-radius:9px; background:var(--fix-bg); }
.both p b { font-weight:600; }
.mvs { display:flex; flex-wrap:wrap; gap:5px; margin-top:7px; }
.mvh { font-size:10.5px; font-weight:600; padding:2px 8px; border-radius:99px; }
.mvh.hit { color:var(--keep); background:var(--keep-bg); } .mvh.hit::before { content:"\2713  "; }
.mvh.miss { color:var(--cut); background:var(--cut-bg); } .mvh.miss::before { content:"\2715  "; }
.by .ask { font-size:12.5px; color:var(--body); margin-top:5px; line-height:1.45; } .by .ask i { color:var(--ink); }
.needs { font-size:12.5px; line-height:1.45; margin-top:6px; padding:6px 9px; border-radius:7px; background:rgba(20,20,19,.05); color:var(--body); }
.needs b { color:var(--ink); font-weight:600; }
.pr .rw .af:empty::before { content:"(take it off the page)"; color:var(--muted); font-style:italic; }
"""


def draw(page, pairs, conf, pdir, proven=()):
    today = date.today().strftime("%d %B %Y")
    ph_, pw = page["page_h"] or 1, page["page_w"] or 1366
    src = os.path.relpath(page["full"], pdir) if page["full"] else ""
    weighted = [(p, sh) for p, sh in pairs if p["weighted"]]
    tone = {b["id"]: band_tone(b["id"], weighted) for b in page["bands"]}

    H = [RH._head("Your buyers read the page").replace("</style>", CSS + "</style>"), topbar(page["url"], today),
         '<div class="grid"><div class="pane"><div class="stage">', f'<img src="{RH.e(src)}" alt="Your page">']
    for b in page["bands"]:
        t, hh = 100 * b["top"] / ph_, 100 * b["h"] / ph_
        H.append(f'<a class="bx {tone[b["id"]][0]}" id="box-{b["id"]}" href="#card-{b["id"]}" '
                 f'style="top:calc({t:.4f}% + 3px);height:calc({hh:.4f}% - 6px)"><span class="tag">{b["n"]}</span></a>')
    # how far each buyer reads: a rail down the right edge, a dashed line where they close the tab
    deepest = 0
    by_band = {}
    for i, (p, sh) in enumerate(pairs):
        ex = exit_of(sh)
        band = next(b for b in page["bands"] if b["id"] == ex["id"]) if ex else None
        stop = (band["top"] + band["h"]) if band else ph_
        if p["weighted"]:
            deepest = max(deepest, stop)
        H.append(f'<div class="rail" style="right:{10 + i * 11}px;height:{100 * stop / ph_:.4f}%;background:{p["color"]}"></div>')
        if band:
            by_band.setdefault(band["id"], []).append((p, stop))
    # every line first, then every label above all of them, so no line is ever drawn through a label
    chips = []
    for bid, ps in by_band.items():
        stop = ps[0][1]
        for k, (p, _) in enumerate(ps):
            label = f"{p['name'].split()[-1]} leaves here" + ("" if p["weighted"] else " · no weight")
            H.append(f'<div class="exit{"" if p["weighted"] else " nb"}" style="top:{100 * stop / ph_:.4f}%;--bc:{p["color"]}"></div>')
            chips.append(f'<span class="exitchip{"" if p["weighted"] else " nb"}" style="top:{100 * stop / ph_:.4f}%;'
                         f'right:{60 + k * 200}px;--bc:{p["color"]}">{RH.e(label)}</span>')
    H += chips
    if weighted and deepest < ph_ - 40:
        H.append(f'<div class="veil" style="top:{100 * deepest / ph_:.4f}%"><span>None of your buyers get this far</span></div>')
    H.append("</div></div>")

    H.append('<aside class="side"><div class="sum"><div class="who">')
    for p, sh in pairs:
        H.append(buyer_row(p, sh, page))
    H.append("</div>")
    H.append(f'<div class="conf"><b>Confidence {conf["score"]} of 100</b>, {RH.e(conf["band"])}. A panel simulation: '
             f'{len(pairs)} separate readers, none saw another. Real visitors are the only authority.</div>')
    plan = classify(pairs, page, {d["buyer"] for d in proven})
    todo = do_first(plan)
    if todo:
        H.append('<div class="first"><h3>Do these first</h3><ol>' + "".join(f"<li>{x}</li>" for x in todo) + "</ol></div>")
    both, lost = win_both(plan, pairs, proven)
    if both:
        H.append('<div class="first both"><h3>Where two buyers pull different ways</h3>' + "".join(f"<p>{x}</p>" for x in both) + "</div>")
    if lost:
        H.append('<div class="first cant"><h3>Proved: this page cannot keep them</h3>' + "".join(f"<p>{x}</p>" for x in lost) + "</div>")
    H.append('</div><div class="grp">Section by section</div>')
    for b in page["bands"]:
        H.append(card(b, tone[b["id"]], pairs))
    H.append('<div class="foot">Every section has a box and a card, in the same order. Hover a card to find its section.</div>')
    H.append("</aside></div>" + RH.JS + "</body></html>")
    return "\n".join(H)


def band_tone(bid, weighted):
    """Red where a paying buyer closes the tab, amber where one needed something, green where one was answered."""
    rows = [(next(s for s in sh["sections"] if s["id"] == bid), exit_of(sh)) for _, sh in weighted]
    if any(ex and ex["id"] == bid for _, ex in rows):
        return ("lose", "Loses a buyer")
    if any(s["tone"] == "misses" for s, _ in rows):
        return ("fix", "Fix")
    if any(s["tone"] == "answers" for s, _ in rows):
        return ("keep", "Works")
    return ("none", "")


def buyer_row(p, sh, page):
    ex = exit_of(sh)
    stop = next(b["top"] + b["h"] for b in page["bands"] if b["id"] == ex["id"]) if ex else page["page_h"]
    pct = max(3, round(100 * stop / (page["page_h"] or 1)))
    tag = "never paid, not counted" if not p["weighted"] else "buyer"
    ask = (sh.get("unanswered") or "").strip()
    ask = "" if ask.lower().strip(".") == "none" else ask
    if ex:
        out = f'Leaves at <b>section {ex["n"]}</b>, {RH.e(ex["name"])}. Reads {pct}% of the page.'
    elif yes(sh.get("acts")):
        out = "<b>Reads to the end and gets in touch.</b>"
    else:
        out = "<b>Reads to the end, but does not get in touch.</b> " + RH.e(sh.get("acts_why", ""))
    return (f'<div class="by{"" if p["weighted"] else " nb"}"><div class="nm"><span class="dot" style="background:{p["color"]}"></span>'
            f'<b>{RH.e(p["name"])}</b><span class="k">{RH.e(tag)}</span></div>'
            f'<div class="reach"><i style="width:{pct}%;background:{p["color"]}"></i></div><div class="out">{out}</div>'
            + (f'<div class="ask">Still asks: <i>{RH.e(ask)}</i></div>' if ask else "")
            + moves_line(p, page) + '</div>')


def moves_line(p, page):
    """What moves this buyer, and whether the page says it anywhere - measured with the audit's own trigger phrases."""
    if not p.get("moves"):
        return ""
    bits = []
    for m in p["moves"]:
        said_it = any(t in page["text"] for t in (norm(x) for x in MOTIVATIONS[m]["triggers"]))
        bits.append(f'<span class="mvh {"hit" if said_it else "miss"}">{RH.e(MOTIVATIONS[m]["label"])}</span>')
    return '<div class="mvs">' + "".join(bits) + "</div>"


def do_first(plan):
    """The sorted fixes: exits first, the primary's before anyone's, top of the page down.
    Fixing the earliest exit is the only change that lets anyone read the rest."""
    out = []
    for f in plan["fix"][:3]:
        who = " and ".join([f["buyer"]] + f["also"])
        what = (f'take off "{RH.e(clip(f["before"], 70))}"' if not f["after"].strip()
                else f'change "{RH.e(clip(f["before"], 70))}" to "{RH.e(f["after"])}"')
        out.append(f'<b>Section {f["n"]}, for {RH.e(who)}:</b> {what}')
    return out


def win_both(plan, pairs, proven):
    """Where one buyer leaves at something another reads on because of. Never a verdict: the read only
    marks it, and /split-test answers both on a whole page."""
    out = []
    for m in [m for m in plan["merge"] if m["weighted"] and m["exit"]]:
        first = m["buyer"].split()[-1]
        mv = MOTIVATIONS[m["moves"]]["label"] if m.get("moves") in MOTIVATIONS else ""
        who = " and ".join(k["buyer"].split()[-1] for k in m.get("keep", [])) or "another buyer"
        out.append(f'<b>{RH.e(m["buyer"])} leaves at section {m["n"]}, {RH.e(m["name"])}.</b> {RH.e(who)} read'
                   f'{"s" if len(m.get("keep", [])) == 1 else ""} on because of {RH.e(m["why"])}. The next page has to keep '
                   f'that and answer {RH.e(first)}' + (f': <i>{RH.e(mv.lower())}</i>.' if mv else "."))
    lost = [f'<b>{RH.e(d["buyer"])}</b> still left at {RH.e(d["section"])} on two reads. '
            f'{RH.e(d["buyer"].split()[-1])} may need a page of their own.' for d in proven]
    return out, lost


def clip(s, n):
    s = re.sub(r"\s+", " ", s or "").strip()
    return s if len(s) <= n else s[:n].rsplit(" ", 1)[0] + "..."


def card(b, tone, pairs):
    cls, word = tone
    H = [f'<article class="card {cls}" id="card-{b["id"]}" data-box="{b["id"]}"><header><span class="num">{b["n"]}</span>'
         f'<div class="is">{RH.e(b["name"])}</div><span class="vd">{RH.e(word)}</span></header>']
    for p, sh in pairs:
        s = next(x for x in sh["sections"] if x["id"] == b["id"])
        ex = exit_of(sh)
        past = bool(ex) and ex["n"] < b["n"]
        if s["tone"] == "neutral" and s["reaction"] != "leaves":
            continue
        if s["reaction"] == "leaves" and not past:
            rx = ('leave', "Leaves here")
        elif past:
            rx = ("past", "Never gets here")
        elif s["tone"] == "misses":
            rx = ("miss", "Needs more")
        else:
            rx = ("on", "Reads on")
        H.append(f'<div class="pr{"" if p["weighted"] else " nb"}{" past" if past else ""}">'
                 f'<div class="prh"><span class="dot" style="background:{p["color"]}"></span><b>{RH.e(p["name"])}</b>'
                 f'<span class="rx {rx[0]}">{rx[1]}</span></div>')
        if s.get("quote"):
            H.append(f'<q>"{RH.e(clip(s["quote"], 140))}"</q>')
        H.append(f'<p>{RH.e(s["says"])}</p>')
        if (s.get("needs") or "").strip():
            H.append(f'<div class="needs"><b>Needs from you:</b> {RH.e(s["needs"])}</div>')
        rw = s.get("rewrite")
        if rw:
            mv = MOTIVATIONS[rw["moves"]]["label"]
            H.append('<div class="rw"><div class="pair"><span class="lb b">Before</span>'
                     f'<span class="bf">{RH.e(rw["before"])}</span><span class="lb a">After</span>'
                     f'<span class="af">{RH.e(rw["after"])}</span></div></div>'
                     f'<span class="mv">{RH.e(mv)}</span>'
                     f'<div class="bc">Because {RH.e(p["name"].split()[-1])} said: <i>"{RH.e(rw["because"].strip(chr(34)))}"</i></div>')
        H.append("</div>")
    if len(H) == 1:
        H.append('<p class="why">Nothing here for any of your buyers, either way.</p>')
    H.append("</article>")
    return "".join(H)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("step", choices=("prepare", "write"))
    ap.add_argument("page", help="the audit folder, context/pages/<slug>")
    ap.add_argument("--fresh", action="store_true", help="prepare: overwrite sheets that already exist")
    a = ap.parse_args()
    pdir = a.page if os.path.isabs(a.page) else os.path.join(ROOT, a.page)
    prepare(pdir, a.fresh) if a.step == "prepare" else write(pdir)
