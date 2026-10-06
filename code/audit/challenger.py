"""The fifteen axes: what the page does now, and the options per decision. Raw material for the three drafts.

    python3 code/audit/challenger.py <url>                   # the axes sheet, from the audit
    python3 code/audit/challenger.py <url> --answers a.json  # the picked draft's choices -> the build brief

⛔ THE AXES ARE NO LONGER ASKED (Jono, 28 September 2026: "we shouldn't ask questions that are going to be
overridden by that anyways"). The visitors, the buyers and the panel answer the taste questions, so the owner
is asked only the facts. Three whole drafts are written from these axes, read blind by the panel, and the
owner picks one (code/audit/drafts.py). Picking winners by taste is near-chance (kappa 0.141 against 330 real
tests), so the owner picks among whole pages the panel has read, with reasons, never line by line.

The structure is still derived: the opposite of what the control measurably does, because a machine can
compute that and a human guessing at it lands on the page they already have.

Nothing here invents a claim. Options that carry a number are drafted from context/proof.md only,
and an axis with no proof behind it says so instead of guessing.
"""
import argparse
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))

from audit.common import ROOT, out_dir_for, rel  # noqa: E402
from audit import evidence as EV  # noqa: E402
from audit import visitor_fixes as VF  # noqa: E402
from audit.invert import motivation_read, shape  # noqa: E402

try:
    from audit.motivations import MOTIVATIONS
except Exception:
    MOTIVATIONS = {}


# proof.md is written in sections, and only some of them hold claims you may print. Reading it line
# by line was a mistake: the first version offered dates, audit notes, a "this number is wrong" warning
# and finally an item from the NEVER SAY list as things to put on a landing page. So the section
# heading decides, and anything outside an allowed section is invisible to this file.
_SAFE_SECTION = re.compile(r"measured|safe to use|results you can use|promises you can print|proof you can|approved", re.I)
_BANNED_SECTION = re.compile(r"never say|⛔|hold|too weak|empty slot|do not|wrong|gap|still do not have", re.I)


def proof_lines(limit=14):
    """Claims from the ALLOWED sections of context/proof.md, and nowhere else.

    A landing page may only print what this returns. Sections marked never-say, hold, wrong or empty
    are skipped entirely, headings are skipped, and a line has to carry a number next to a word that
    says what the number means. When in doubt the line is dropped: a missing option is a small
    problem, an option that quotes a banned claim is a live one."""
    p = os.path.join(ROOT, "context", "proof.md")
    if not os.path.exists(p):
        return []
    out, allowed = [], False
    for raw in open(p, encoding="utf-8", errors="ignore"):
        line = raw.rstrip()
        if re.match(r"^#{1,2}\s", line):
            heading = line.lstrip("# ").strip()
            if re.match(r"^\d+\.", heading):          # "## 1. Psychotherapy clinic" - stays in its parent
                continue
            allowed = bool(_SAFE_SECTION.search(heading)) and not _BANNED_SECTION.search(heading)
            continue
        if not allowed:
            continue
        line = re.sub(r"\*\*|`", "", line).lstrip("-· ").strip()
        line = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", line)        # markdown links to their text
        if not line or line.startswith((">", "|", "<!--")) or len(line) > 200:
            continue
        if not re.search(r"\d", line) or len(re.findall(r"[A-Za-z]{3,}", line)) < 3:
            continue
        if re.search(r"\b(verified|as of|source|publish once|see above|quote bank|tagged by)\b", line, re.I):
            continue
        # an inline warning overrides the section: "weak, do not publish" is a no wherever it appears
        if re.search(r"\b(do not publish|weak|hold list|not typical|unnamed|undated|never blur|fix or remove)\b", line, re.I):
            continue
        if not re.search(r"\b(saved?|cut|earned?|made|leads?|clients?|customers?|jobs?|years?|months?|weeks?"
                         r"|reviews?|rating|stars?|members?|subscribers?|views?|videos?|rate|close|show|booked?"
                         r"|weeks|guarantee|free|%)\b", line, re.I):
            continue
        out.append(line)
    return out[:limit]


# ⛔ Held identical on both arms, never asked (Jono, 28 September 2026). Removing social proof
# from one arm does not test anything, it just handicaps that arm.
FROZEN = [
    "The social proof: the same testimonials, reviews, case studies, client logos and client videos. Its position can move with the order; its content does not.",
    "The form handler, the thank-you page and the tracking.",
    "The brand: the same colours and fonts. The page STYLE flips - calm to bold or bold to calm - so page B looks like a different page.",
]

# Each axis: what to ask, how to read the control, and three things to react to.
# `options` is a function of (shape, proof) so an option can quote a real number.
AXES = [
    {"key": "benefit", "title": "The benefit the page leads on",
     "ask": "Everything else argues for this. Which reason to buy does the challenger lead on?",
     "read": lambda sh: (f"leads on \"{sh['motivation']['leads_on'][1]}\"" if (sh.get("motivation") or {}).get("leads_on") else "no clear motivation in the first screen"),
     "options": lambda sh, pr: _benefit_options(sh)},
    # ⛔ The headline itself keeps the service and the city: it is what the ad matches, and it keeps the
    # clicks cheap (/audit, 28 September 2026). What rotates is the line above it and the line under it.
    {"key": "headline", "title": "The lines around the headline",
     "ask": "The headline stays the service and the city. Which pain goes above it, and which offer goes under it?",
     "read": lambda sh: f"H1: \"{sh.get('h1','')[:90]}\"",
     "options": lambda sh, pr: [
         "The pain above, the offer under: \"[the cost they feel]?\" then \"[what you do], [by when], or [the guarantee].\"",
         "Who it is for above, the outcome under: \"For [the exact buyer]\" then \"[outcome] in [timeframe].\"",
         "The symptom above, the process under: \"[the thing that is broken]?\" then \"[first step], then [what follows].\"",
     ]},
    {"key": "offer", "title": "The offer",
     "ask": "The same service, stated as a different promise. What is the challenger promising?",
     "read": lambda sh: "the offer as written in the hero",
     "options": lambda sh, pr: [
         "A number and a deadline: \"[N] [things] in [N] days.\"",
         "An outcome and a feeling: \"[the result], without [the pain they expect].\"",
         "A first step that costs nothing: \"[the free thing], yours whether or not we work together.\"",
     ]},
    {"key": "guarantee", "title": "The guarantee",
     "ask": "How the risk is reversed. It must be true and deliverable.",
     "read": lambda sh: "the risk reversal as written",
     "options": lambda sh, pr: [
         "Money back: \"[the promise] or your money back.\"",
         "We keep working: \"[the promise] or we keep working free until it is.\"",
         "No guarantee at all - test whether the page needs one, if that is honest for this business.",
     ]},
    {"key": "response_time", "title": "The response-time claim",
     "ask": "Say it, change it, or drop it. A fast promise can read as pressure, and it only stays if the machine behind it actually delivers.",
     "read": lambda sh: ("states a response time" if sh.get("response_time") else "no response time on the page"),
     "options": lambda sh, pr: [
         "Keep a specific time: \"We call back within [N] minutes.\"",
         "Soften it to a window: \"Same day, every day.\"",
         "Remove it entirely - the page never mentions speed.",
     ]},
    {"key": "three_benefits", "title": "The three-benefit block",
     "ask": "Three reasons to pick you, each ending in the outcome it buys. Which three motivations?",
     "read": lambda sh: "the current three reasons",
     "options": lambda sh, pr: _three_benefit_options(sh)},
    {"key": "features", "title": "The features under the benefit",
     "ask": "The deliverables, rewritten so each one proves the new benefit.",
     "read": lambda sh: "the what-you-get list as written",
     "options": lambda sh, pr: [
         "Each line finishes the chain: \"we do X, which gives you Y, meaning Z.\"",
         "Group them into three named stages so the scope feels handled.",
         "Cut to the three that matter and delete the rest.",
     ]},
    {"key": "proof_bullets", "title": "The proof numbers",
     "ask": "Which numbers the page leads with. Only what is in proof.md.",
     "read": lambda sh: "the current tick strip and stat row",
     "options": lambda sh, pr: ([f"Lead with: {x}" for x in pr[:3]] if pr else
                                ["No usable claims in context/proof.md yet - fill it before this axis can move."])},
    {"key": "images", "title": "The images",
     "ask": "What the photography argues. Stock says nothing.",
     "read": lambda sh: f"{sh.get('images',0)} images on the page",
     "options": lambda sh, pr: [
         "The work: finished jobs, before and after, the real site.",
         "The people: the crew, the van, the owner on camera.",
         "The artefact: the actual report, dashboard or deliverable they receive.",
     ]},
    {"key": "cta_text", "title": "The button text",
     "ask": "The words on every button. One phrase, used everywhere.",
     "read": lambda sh: f"\"{sh.get('cta_text','')}\"" if sh.get("cta_text") else "the current button text",
     "options": lambda sh, pr: [
         "Name the thing they get: \"Get my free [deliverable]\".",
         "Name the next step: \"See what's missing\" or \"Check my [thing]\".",
         "Name the speed: \"Get a quote today\".",
     ]},
    # ⛔ Every option keeps the four: first name, last name, email, phone (Jono, 28 September 2026).
    # The axis moves the form and changes what comes AFTER the four - never the four themselves.
    {"key": "form", "title": "The form",
     "ask": "Where it sits, and what it asks after the four it always asks: first name, last name, email, phone.",
     "read": lambda sh: (f"{sh.get('form_fields',0)} fields, {sh.get('form_depth_pct')}% down the page" if sh.get("form_depth_pct") is not None else "no form on the page"),
     "options": lambda sh, pr: [
         "The four and nothing else, in the first screen: the website and the qualifying question move to the call.",
         "The four plus one qualifying chip, after the proof, so the lead arrives sorted.",
         "Keep the fields, move the form: same ask, opposite end of the page.",
     ]},
    {"key": "sections", "title": "Which sections exist",
     "ask": "Add or remove whole blocks. This is where a page changes shape.",
     "read": lambda sh: " → ".join(s["kind"] for s in sh["sections"]),
     "options": lambda sh, pr: _section_options(sh)},
    {"key": "faq", "title": "The FAQ",
     "ask": "Which objection gets answered. These are the reasons people do not enquire.",
     "read": lambda sh: "the questions currently answered",
     "options": lambda sh, pr: [
         "Money first: what it costs, what changes the price, whether the quote is fixed.",
         "Risk first: what happens if it goes wrong, who does the work, what the guarantee covers.",
         "Fit first: who this is not for, and what happens after they enquire.",
     ]},
    {"key": "order", "title": "The order of the page",
     "ask": "What the buyer meets first, second, third.",
     "read": lambda sh: " → ".join(s["kind"] for s in sh["sections"]),
     "options": lambda sh, pr: [
         "Proof first: reviews and faces directly under the headline, before any explanation.",
         "Offer first: what they get and what it costs, then the proof behind it.",
         "Story first: the problem, the process, then the proof.",
     ]},
    {"key": "length", "title": "The length",
     "ask": "Not long against squeeze - a service page needs room for proof. Tighter or fuller than the control.",
     "read": lambda sh: f"{sh['words']} words across {sh['section_count']} sections",
     "options": lambda sh, pr: [
         "Tighter: same sections, half the words in each.",
         "Fuller: the same shape with the objections and the process answered properly.",
         "About the same - length is not this test's question.",
     ]},
]


def _benefit_options(sh):
    """Three DIFFERENT motivations, each with its own reason for being offered. The first version
    printed "the strongest motivation this page never mentions" twice, which is not a choice."""
    mot = sh.get("motivation") or {}
    missing = list(mot.get("missing") or [])
    leads = (mot.get("leads_on") or [None, None])[1]
    out, used = [], {leads}
    for i, (key, label, _w) in enumerate(missing[:2]):
        if label in used:
            continue
        used.add(label)
        out.append(f"{label} - " + ("the strongest reason this page never mentions." if i == 0
                                    else "also missing, and worth more to this buyer than the current lead."))
    for m in MOTIVATIONS.values():
        if len(out) >= 3:
            break
        if m["label"] not in used:
            used.add(m["label"])
            out.append(f"{m['label']} - mentioned on the page, but never the thing it leads with.")
    return out[:3] or ["No motivation data - fill context/business.md so the model is known."]


def _three_benefit_options(sh):
    labels = [m["label"] for m in MOTIVATIONS.values()] if MOTIVATIONS else []
    if len(labels) < 6:
        return ["Pick any three reasons people buy and give each its own block."]
    return [
        f"{labels[4]}, {labels[5]}, {labels[2]} - the safety set: risk, certainty, speed.",
        f"{labels[0]}, {labels[1]}, {labels[3]} - the money set: earn, save, less effort.",
        f"{labels[6]}, {labels[7]}, {labels[8]} - the relief set: end the pain, get your life back, look good.",
    ]


def _section_options(sh):
    kinds = {s["kind"] for s in sh["sections"]}
    # social proof blocks are frozen, so this axis never offers to add or remove one
    add = [k for k in ("process", "faq", "portfolio") if k not in kinds]
    drop = [k for k in ("process", "portfolio") if k in kinds]
    out = []
    if add:
        out.append("Add: " + ", ".join(add[:2]) + " - blocks the control does not have.")
    if drop:
        out.append("Remove: " + drop[0] + " - test whether the page needs it at all.")
    out.append("Same sections, different order - nothing added, nothing cut.")
    return out[:3]


def _evidence_head(ev):
    """What the interview knows about real people, and what it is missing, before any axis is asked."""
    c = ev["counts"]
    L = ["## What real people said and did", "",
         f"- Visitors: {c['visitors']} lines" + (f", from the {ev['session_read']} session read" if ev["session_read"] else ""),
         f"- Buyers: {c['buyer said']} lines from real calls and emails"]
    L += [f"  - {n}" for n in ev["buyers"]] or ["  - none approved"]
    L += [f"- Panel: {c['panel (simulated)']} reactions, simulated"]
    L += [f"  - {n}" for n in ev["panel_read"]] or ["  - no read of this page"]
    L += [f"- Missing: {m}" for m in ev["missing"]]
    return L + ["- Weight: visitors beat what buyers said, which beats the panel. None of it beats a real test.", ""]


def sheet(url, sh, out=None):
    pr = proof_lines()
    ev = EV.gather(url)
    L = [f"# Challenger interview · {url}",
         f"Your page: {sh['words']} words · {sh['section_count']} sections · form {sh.get('form_depth_pct')}% down",
         "Raw material for the three drafts, and after the pick for the sidebar. None of it is asked of the owner.", "",
         "## How the drafts use it", "",
         "- Each draft takes a different option on the axes that carry its big idea.",
         "- Every number must already be in context/proof.md. Nothing here invents a claim.",
         "- An axis a draft does not change stays as the control has it.", "",
         "## Held identical on both arms, never asked", ""] + [f"- {x}" for x in FROZEN] + [""] + _evidence_head(ev)
    for i, ax in enumerate(AXES, 1):
        try:
            control = ax["read"](sh)
        except Exception:
            control = "not measured"
        L += [f"## {i}. {ax['title']}", "", f"- Now: {control}", f"- {ax['ask']}"]
        lines = ev["axes"].get(ax["key"]) or []
        L += (["- Evidence:"] + [f"  - {e['source']}: {e['text']}" for e in lines] if lines
              else ["- Evidence: none on file for this axis, so any recommendation is a heuristic."])
        L.append("")
        for j, opt in enumerate(ax["options"](sh, pr), 1):
            L.append(f"  {chr(64+j)}. {opt}")
        L.append("")
    L += ["## After the owner picks a draft", "",
          "- Its choices go into answers.json, keyed by axis, and --answers writes the build brief.",
          "- Anything the draft does not change stays as the control has it, and the brief says which.",
          "- If the choices conflict - much tighter AND three new sections - flag it once, before building.", ""]
    text = "\n".join(L)
    if out:
        os.makedirs(os.path.dirname(out), exist_ok=True)
        open(out, "w").write(text)
    return text


def _analysis_block(an):
    """The /analytics analysis, finding by finding, with the change each one asks for."""
    if not an:
        return ["## What the visitor analysis says", "", "- No /analytics analysis of this page yet.", ""]
    n = int(an.get("sessions") or 0)
    L = ["## What the visitor analysis says", "", f"- From: {n} sessions, read {an.get('date', '')}"]
    if n < EV.MIN_ANALYSIS_SESSIONS:
        L.append(f"- Under {EV.MIN_ANALYSIS_SESSIONS} sessions: a hint, not a rule. Check they are real visitors, not our own checks.")
    for f in an.get("findings") or []:
        L.append(f"- {f.get('verdict', '')}: {f.get('title', '')}")
        if f.get("change"):
            L.append(f"  - Change: {f['change']}")
    return L + [""]


def _visitor_block(vf):
    """The changes the visitors force. Not asked in the interview: the data already answered them."""
    L = ["## Fixed because of what visitors did", ""]
    if vf.get("note"):
        L.append(f"- Note: {vf['note']}")
    for x in vf["fixes"]:
        L += [f"- Rule {x['rule']}: {x['change']}", f"  - Evidence: {x['evidence']}", f"  - Applies to: {x['applies']}"]
    if not vf["fixes"]:
        L.append("- Nothing to fix from the visitor data yet.")
    return L + [""]


def build_brief(url, sh, answers, out=None):
    """Your answers, turned into the thing that gets built. Anything unanswered stays as the control
    has it and is listed as such, so nobody has to remember what was decided and what was skipped."""
    ev = EV.gather(url)
    chosen, kept = [], []
    for i, ax in enumerate(AXES, 1):
        a = (answers.get(ax["key"]) or "").strip()
        try:
            control = ax["read"](sh)
        except Exception:
            control = "not measured"
        (chosen if a and a.lower() not in ("same", "-", "skip") else kept).append((i, ax, control, a))
    L = [f"# Challenger build brief · {url}",
         f"{len(chosen)} axes change · {len(kept)} stay as the control has them",
         "Next: build VariantB.tsx to this, then /split-test step 3.", "",
         "## What changes", ""]
    for i, ax, control, a in chosen:
        L += [f"### {i}. {ax['title']}", f"- Now: {control}", f"- Becomes: {a}"]
        rests = (ev["axes"].get(ax["key"]) or [])[:2]
        L += (["- Rests on:"] + [f"  - {e['source']}: {e['text']}" for e in rests] if rests
              else ["- Rests on: no evidence on file, so this is a heuristic bet."])
        L.append("")
    if kept:
        L += ["## What stays as the control has it", ""]
        for i, ax, control, _a in kept:
            L.append(f"- {ax['title']}: {control}")
        L.append("")
    L += _analysis_block(ev.get("analysis")) + _visitor_block(VF.fixes(url)) + EV.buyer_brief()
    # the one conflict worth catching before anyone writes code
    length = (answers.get("length") or "").lower()
    sections = (answers.get("sections") or "").lower()
    if re.search(r"remove|cut|drop|delete|lose", sections) and re.search(r"testimonial|review|case|logo|proof|video", sections):
        L += ["## ⛔ Social proof cannot come off", "",
              "- The sections answer removes a proof block. Social proof is identical on both arms.",
              "- Keep the block, or move it with the order axis instead.", ""]
    if re.search(r"tighter|shorter|cut", length) and re.search(r"add", sections):
        L += ["## ⛔ One conflict to settle first", "",
              "- You asked for a tighter page AND for sections to be added. Both cannot win.",
              "- Say which: fewer words in the same blocks, or more blocks at the current length.", ""]
    L += ["## The rules this build follows", "",
          "- Every claim comes from context/proof.md. Nothing is invented to fill an option.",
          ] + [f"- Identical to the control. {x}" for x in FROZEN] + [
          "- The result is a claim about this page against the control, never about one axis.", ""]
    text = "\n".join(L)
    if out:
        os.makedirs(os.path.dirname(out), exist_ok=True)
        open(out, "w").write(text)
    return text


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("target", help="a URL already audited, or a path to capture.json")
    ap.add_argument("--out")
    ap.add_argument("--answers", help="a JSON file of {axis key: your answer} - writes the build brief instead")
    a = ap.parse_args()
    if a.target.endswith(".json"):
        cap = json.load(open(a.target)); url = cap.get("url", a.target)
    else:
        url = a.target
        p = os.path.join(out_dir_for(url), "capture.json")
        if not os.path.exists(p):
            sys.exit(f"No capture for {url}. Run: python3 code/audit/page_audit.py {url}")
        cap = json.load(open(p))
    sh = shape(cap)
    d = cap["viewports"]["desktop"]["facts"]
    sh["h1"] = d.get("h1", "")
    sh["response_time"] = bool(re.search(r"(within|in under|under)\s+\d+\s*(second|minute|hour)|same[- ]day|\d+\s*seconds?", d.get("text", ""), re.I))
    ctas = [c["text"] for c in d.get("ctas", []) if c.get("text")]
    sh["cta_text"] = ctas[0] if ctas else ""
    if a.answers:
        answers = json.load(open(a.answers))
        out = a.out or os.path.join(out_dir_for(url), "challenger-brief.md")
        print(build_brief(url, sh, answers, out))
        print(f"\nWrote {rel(out)}")
        return
    out = a.out or os.path.join(out_dir_for(url), "challenger-interview.md")
    print(sheet(url, sh, out))
    print(f"\nWrote {rel(out)}")
    print("\nDraft three from these (code/audit/drafts.py). After the pick: python3 code/audit/challenger.py <url> --answers <answers.json>")


if __name__ == "__main__":
    main()
