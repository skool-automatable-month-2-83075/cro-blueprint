"""Read the control page and derive the OPPOSITE page - what it SAYS first, then how it is built.

⛔ THE ORDER MATTERS (Jono, 25 September 2026). The first version of this file flipped seven
geometry axes and froze everything else as "substance". That was backwards. Across 2,288 audited
tests copy won 60% and layout 43%: the benefit the page leads on, the offer, the guarantee and the
proof are the things that move a number, and they are all legitimately testable. "30 leads in 30
days or your money back" against "we work free until you get them" is the same business making the
same promise with different risk framing, not a different company.

So the axes are ranked. The benefit rotates first, then the features under it, the offer, the
guarantee, the images, the form, the length, the FAQ, the layout, and the page style. The page
style flips too (Jono, 28 September 2026): two pages with the same look read as one page to a visitor.

⛔ SOCIAL PROOF NEVER ROTATES (Jono, 28 September 2026). Both arms carry the same testimonials,
reviews, case studies, client logos and client videos. Taking proof off one arm is not a test, it
handicaps that arm and teaches nothing. Its position can move with the order; its content cannot.

The only other things frozen: a claim that is not in context/proof.md, the form handler, the
thank-you page and the tracking.

    python3 code/audit/invert.py <url-or-capture.json>          # the brief, printed
    python3 code/audit/invert.py <url> --out context/pages/<slug>/challenger-brief.md

Why this exists (Jono, 25 September 2026): handing the challenger to /audit makes both arms
converge on the same "best practice" page, and a test between two similar pages needs traffic nobody
at this level has. A challenger earns its place by being STRUCTURALLY opposite, so the test answers
"which shape works" rather than "which shade of the same shape". The axes below are read from the
capture, not chosen by taste: length, where the form sits, hero shape, proof placement, section
order, CTA pattern, the ask. Each one is measured on the control and flipped.

What it never flips: the social proof, an unproven claim, the phone number's placement, the tracking.
"""
import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))

from audit.common import ROOT, out_dir_for  # noqa: E402

# Which section a heading belongs to, so the order can be compared and reversed.
# Social proof: what other people say and did. Held identical on both arms, never an axis.
# The portfolio is the business's own work, not social proof, so it can still rotate.
SOCIAL_PROOF_KINDS = ("proof_logos", "testimonials", "cases", "video")

KINDS = [
    ("faq", r"question|before you (enquire|book|call)|faq|\bask\b|answers"),
    ("proof_logos", r"trusted|clients|brands|as seen|logos|partners"),
    ("portfolio", r"work|gallery|portfolio|projects|rebuilt|before|after"),
    ("video", r"unscripted|watch|video|say it|on camera"),
    ("process", r"how it works|steps?|four|three|process|what happens"),
    ("offer", r"everything|what you get|included|the build|package|pricing|cost|price"),
    ("testimonials", r"said|kind words|reviews|testimonial|clients say"),
    ("cases", r"case stud|two builds|saved|results|outcomes"),
    ("form", r"see what|get (my|your)|enquire|quote|audit|start|contact|book"),
]


def classify(heading, has_form=False, is_first=False):
    """The first section is always the hero; a section holding the form is the form. Otherwise the
    heading names it, and the FAQ is tested before the portfolio so "Before you enquire" is an FAQ."""
    import re
    if is_first:
        return "hero"
    if has_form:
        return "form"
    h = (heading or "").strip().lower()
    for kind, pat in KINDS:
        if re.search(pat, h):
            return kind
    return "copy"


def motivation_read(text, model=None):
    """Which buying motivation the page currently leads on, and which strong ones it ignores.
    The nine and their per-model weights come from code/audit/motivations.py (12 sources)."""
    try:
        from audit.motivations import MOTIVATIONS
    except Exception:
        return {"leads_on": None, "present": [], "missing": []}
    low = (text or "").lower()
    head = low[:1200]          # roughly the hero: what the page leads on
    present, leading = [], []
    for key, m in MOTIVATIONS.items():
        hits = sum(1 for t in m["triggers"] if t in low)
        if hits:
            present.append((key, m["label"], hits))
        if any(t in head for t in m["triggers"]):
            leading.append((key, m["label"]))
    w = lambda k: (MOTIVATIONS[k]["weight"].get(model or "trade", 0.5))
    present.sort(key=lambda x: -x[2])
    missing = sorted([(k, m["label"], w(k)) for k, m in MOTIVATIONS.items()
                      if k not in {p[0] for p in present} and w(k) >= 0.7], key=lambda x: -x[2])
    return {"leads_on": leading[0] if leading else (present[0][:2] if present else None),
            "present": present, "missing": missing}


def shape(cap):
    """The control's structure, measured."""
    d = cap["viewports"]["desktop"]["facts"]
    m = cap["viewports"]["mobile"]["facts"]
    height = d["scrollHeight"] or 1
    form_top = d["forms"][0]["top"] if d["forms"] else None
    secs = []
    for s in d["sections"]:
        in_form = bool(form_top is not None and s["top"] <= form_top <= s["top"] + max(s["h"], 1))
        secs.append({"i": s["i"], "heading": s["heading"], "words": s["words"], "ctas": s["ctas"],
                     "top": s["top"], "depth_pct": round(100 * s["top"] / height),
                     "kind": classify(s["heading"], in_form, is_first=(s is d["sections"][0]))})
    text = d.get("text", "")
    import re as _re
    return {
        "motivation": motivation_read(text),
        "lead_magnet": bool(_re.search(r"free (guide|checklist|pdf|report|audit|estimate|inspection|template|calculator)", text, _re.I)),
        "video_proof": sum(1 for v in d["videos"]) + sum(1 for f in d["iframes"] if f["provider"] in ("youtube", "vimeo", "wistia", "loom")),
        "written_proof": d.get("quotes", 0),
        "images": len(d.get("images", [])),
        "words": d["words"],
        "sections": secs,
        "section_count": len(secs),
        "page_height": height,
        "form_fields": len(d["forms"][0]["fields"]) if d["forms"] else 0,
        "form_depth_pct": round(100 * form_top / height) if form_top is not None else None,
        "hero_words": secs[0]["words"] if secs else 0,
        "hero_has_video": bool([v for v in d["videos"] if v["top"] < 900]) or bool([f for f in d["iframes"] if f["top"] < 900 and f["provider"] in ("youtube", "vimeo", "wistia", "loom")]),
        "videos": len(d["videos"]) + sum(1 for f in d["iframes"] if f["provider"] in ("youtube", "vimeo", "wistia", "loom")),
        "cta_count": d["ctasTotal"],
        "mobile_bar": bool([b for b in m["fixedBottom"] if b["hasTel"]]),
        "first_proof_depth_pct": next((s["depth_pct"] for s in secs if s["kind"] in ("proof_logos", "testimonials", "cases", "video", "portfolio")), None),
    }


def invert(sh, business_model=None):
    """One decision per axis, ranked by what actually moves a number. Substance first, design last.
    Every 'control' line is a measurement, so a disagreement is with the page, not with an opinion."""
    axes = []
    mot = sh.get("motivation") or {}
    leads_on = mot.get("leads_on")
    missing = mot.get("missing") or []
    alt = missing[0] if missing else None

    # 1. THE BENEFIT - the biggest lever on the page
    axes.append({
        "axis": "1 · The benefit it leads on",
        "control": f"leads on \"{leads_on[1]}\"" if leads_on else "no clear buying motivation in the first screen",
        "challenger": (f"Lead on \"{alt[1]}\" instead - the strongest motivation this page never mentions."
                       if alt else "Lead on a different one of the nine motivations; the page currently covers most of them, so pick the one its buyer feels hardest."),
        "why": "People buy to save time, earn money, save money, save effort, remove risk, know exactly what happens, stop a pain, get their life back, or look good. The page can only lead on one. Which one is the single biggest thing to test, and copy beats layout 60% to 43% across 2,288 tests.",
    })
    # 2. THE FEATURES UNDER IT
    axes.append({
        "axis": "2 · The features backing it",
        "control": "the current three reasons and the what-you-get list",
        "challenger": "Rewrite every feature as the proof of the NEW benefit. Same deliverables, same truth, each one finished with the outcome it buys.",
        "why": "A feature with no benefit attached is a specification. When the benefit changes, the features must argue for the new one or the page contradicts its own headline.",
    })
    # 3. THE OFFER
    axes.append({
        "axis": "3 · The offer",
        "control": "the offer as written in the hero",
        "challenger": "State the same deliverable as a different promise: a number and a deadline against an outcome and a feeling. \"30 leads in 30 days\" against \"your phone rings by the end of the month\".",
        "why": "Same service, same truth, different thing being bought. This is a legitimate test, not a change of business - it only becomes one if you promise something you cannot deliver.",
    })
    # 4. THE GUARANTEE
    axes.append({
        "axis": "4 · The guarantee",
        "control": "the risk reversal as written",
        "challenger": "Flip how the risk is reversed: money back against we keep working free, or a named deadline against a named result. It must still be true and still in proof.md.",
        "why": "Risk reduction is the strongest motivation for a trade buyer and the thing the guarantee is really selling. Its FORM is testable even when the promise behind it does not move.",
    })
    # 5. IMAGES
    axes.append({
        "axis": "5 · The images",
        "control": f"{sh.get('images', 0)} images on the page",
        "challenger": "Swap the image language: real work and real faces where the control uses staged or stock shots, or the finished result where the control shows the process.",
        "why": "A photo is an argument about who you are. Stock says nothing; the van, the crew and the finished job say it in a second.",
    })
    # 6. THE FORM
    fd, ff = sh.get("form_depth_pct"), sh.get("form_fields", 0)
    axes.append({
        "axis": "6 · The form",
        "control": (f"{ff} fields, {fd}% down the page" if fd is not None else "no form on the page"),
        "challenger": ("The four and nothing else, in the first screen: first name, last name, email, phone. The rest is asked on the call."
                       if (fd is None or fd > 40 or ff > 4) else "The four plus one qualifying chip, placed after the proof so the page earns the ask first."),
        "why": "Where the ask sits and what it asks after the four is the one structural bet that changes who converts. The four - first name, last name, email, phone - are never cut.",
    })
    # 7. LENGTH
    long_page = sh["words"] > 550 or sh["section_count"] > 7
    axes.append({
        "axis": "7 · Length",
        "control": f"{sh['words']} words across {sh['section_count']} sections",
        "challenger": "Short: the promise, the form and every proof block the control has, with the words around them cut. Under 250 words of our own copy." if long_page
                      else "Long: problem, process, what you get, proof in depth, FAQ. 700+ words.",
        "why": "Long and short are the two real shapes. At this traffic only a difference this size is resolvable.",
    })
    # 8. THE FAQ
    axes.append({
        "axis": "8 · The FAQ",
        "control": "the questions currently answered",
        "challenger": "Answer the objections the control avoids - what it costs, what happens if it goes wrong, why you and not the cheaper quote - and drop the ones no buyer actually asks.",
        "why": "The FAQ is where the reasons people DON'T enquire get answered. Changing which objection is met changes who finishes the page.",
    })
    # 9. LAYOUT
    order = [x["kind"] for x in sh["sections"]]
    axes.append({
        "axis": "9 · Layout and order",
        "control": " → ".join(order),
        "challenger": " → ".join(["hero"] + [k for k in reversed(order[1:]) if k != "hero"]),
        "why": "The order is a claim about what the buyer needs next. Reversing it tests the claim - and it is the cheapest axis to move, which is why it ranks here and not first.",
    })
    # 10. DESIGN
    axes.append({
        "axis": "10 · Design",
        "control": "the control's page style",
        "challenger": "Flip the page style: the kit's calm style becomes the bold one, or the other way round. Same brand colours and fonts, different colour coverage, alignment and density.",
        "why": "Two pages in the same style read as one page to a visitor, and a difference nobody notices tests nothing (Jono, 28 September 2026).",
    })
    return axes


# PXL's operational test for "is this different enough to be resolvable at our sample". All three
# must pass before a challenger is built: a difference nobody notices reads flat at any affordable N.
GATE = [
    "Distinguishable in a 5-second side-by-side: show the control, then the challenger, for 5 seconds each - can a stranger say what changed?",
    "Adds or removes something, not only rearranges it.",
    "The difference is above the fold.",
]

# Where the hypothesis came from. Written into the test log every time, honestly.
TIERS = {
    1: "our own prior significant result on a comparable page, or a pattern replicated in significant tests",
    2: "session replay of non-converting sessions, form-field drop-off, or a sales-call objection",
    3: "user testing with 5 to 10 people, or an exit survey",
    4: "a heuristic read of the page's own shape - this file, with no outside evidence",
}

NEVER = ["The social proof: the same testimonials, reviews, case studies, logos and client videos on both arms. Removing proof handicaps an arm; it is not a test.",
         "Any claim, number or testimonial that is not in context/proof.md. Never invent proof.",
         "A promise the business cannot actually deliver. The offer and the guarantee may be reframed; they may not become fiction.",
         "The form handler, the thank-you page and the tracking - same events, same endpoint, both arms.",
         "The brand colours and fonts. The page style flips; the brand does not.",
         "The phone number's role (the digits differ per arm for call attribution; the placement does not)."]


def candidates(sh, axes):
    """Three ways to cut the same axis list. Generation is free and widens the search; SELECTION is
    the weak link - an LLM judge scored kappa 0.141 against 330 real A/B tests - so nothing here
    predicts a winner. Pick on what can be observed before the test runs. Build ONE: a third live
    arm costs 82% more leads, which is 21 months instead of 12 at 30 leads a month."""
    return [
        {"name": "A · say something else", "flips": ["1 · The benefit it leads on", "2 · The features backing it", "3 · The offer", "4 · The guarantee"],
         "summary": "Same page shape, a different reason to buy. The highest-value cut, because copy outperforms layout, and the easiest to read: only the argument moved.",
         "build": "medium"},
        {"name": "B · show something else", "flips": ["5 · The images", "8 · The FAQ"],
         "summary": "Same argument, same shape, same social proof - different pictures and different objections answered. Use when the promise is right but the page does not feel real.",
         "build": "low"},
        {"name": "C · the opposite page", "flips": [a["axis"] for a in axes],
         "summary": "Everything, the page style included. The biggest resolvable difference and the least diagnostic - it tells you which page wins, never which part. The default at low traffic.",
         "build": "highest"},
    ]


def brief(url, sh, axes, out=None):
    L = [f"# Challenger brief · {url}",
         f"Derived from the control's own shape · {sh['words']} words · {sh['section_count']} sections · form {sh['form_depth_pct']}% down",
         "Next: build VariantB.tsx to the decisions below, then /split-test step 2.", "",
         "## The bet, in one line", "",
         f"- {axes[0]['challenger'].rstrip('.')}.",
         f"- Then everything on the page argues for that instead: the features, the offer and the guarantee. The social proof stays exactly as it is.", "",
         "## Axis by axis", ""]
    import re as _re
    def _wrap(prefix, body, ind="  "):
        """One bullet, then sub-bullets - the house shape keeps every line readable on a phone."""
        body = body.strip()
        if len(f"- {prefix}: {body}") <= 195:
            return [f"- {prefix}: {body}"]
        parts = [x.strip() for x in _re.split(r'(?<=[.!?])\s+(?=[A-Z"\u201c])', body) if x.strip()]
        out, first = [f"- {prefix}:"], True
        for x in parts:
            while len(x) > 190:
                cut = x.rfind(" ", 0, 190)
                out.append(f"{ind}- {x[:cut]}"); x = x[cut + 1:]
            out.append(f"{ind}- {x}")
            first = False
        return out
    for a in axes:
        L += [f"### {a['axis']}"] + _wrap("Control", a["control"]) + _wrap("Challenger", a["challenger"]) + _wrap("Why it is worth testing", a["why"]) + [""]
    L += ["## The three candidates - build ONE", "",
          "Generating several widens the search and costs nothing.",
          "Picking between them is the weak step: judgement has almost no demonstrated accuracy here.",
          "So choose on what you can SEE before the test - the noticeability gate, then the evidence tier, then build cost.",
          "Never on which one you think will win.", ""]
    for c in candidates(sh, axes):
        L += [f"### {c['name']}", "- Flips:"] + [f"  - {x}" for x in c["flips"]] + _wrap("What it is", c["summary"]) + [f"- Build cost: {c['build']}", ""]
    L += ["## The gate, before a line of code", "",
          "All three must be yes, or the challenger is too close to the control and will read flat at any sample you can afford:", ""] + [f"- {g}" for g in GATE] + ["",
          "## Where this hypothesis came from", "",
          "Write the tier into the test log. Tier 4 is legitimate on a page that has never been tested - that is what a heuristic read is for - but it is never logged as though it were tier 1.", ""] + [f"- Tier {k}: {v}" for k, v in TIERS.items()] + ["",
          f"- This brief, on its own, is TIER 4. It rises to tier 2 when the queue item behind it came from a session read or a real objection.", "",
          "## What does NOT change", ""] + [f"- {n}" for n in NEVER] + ["",
          "## The rule", "",
          "- A challenger that shares the control's shape is not a challenger; it is the same page with different words.",
          "- Flip the structure, keep the substance. One test, one question.",
          "- The result is a claim about the SHAPE, never about one axis. Seven things moved; no single one gets the credit.",
          "- The whole page is flipped because that is the only effect size low traffic can resolve.",
          "  - Not because layout wins more: across 2,288 audited tests copy won 60% and layout 43%.",
          "  - That is why the benefit, the offer and the guarantee rank above the layout in this brief.", ""]
    text = "\n".join(L)
    if out:
        os.makedirs(os.path.dirname(out), exist_ok=True)
        open(out, "w").write(text)
    return text


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("target", help="a URL already audited, or a path to capture.json")
    ap.add_argument("--out")
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
    axes = invert(sh)
    out = a.out or os.path.join(out_dir_for(url), "challenger-brief.md")
    print(brief(url, sh, axes, out))
    print(f"\nWrote {os.path.relpath(out, ROOT)}")


if __name__ == "__main__":
    main()
