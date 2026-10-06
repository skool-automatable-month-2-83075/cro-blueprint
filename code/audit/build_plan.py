"""From the audit to the build: what goes where, in what words, and what only the owner can supply.

Jono, 28 September 2026: "let's update this skill so that we can actually update their page - or
create a new one." The audit says keep, fix, cut and add for every section. This turns that into the
work, two ways:

  ads  - a NEW landing page from the course template (website/app/lp/_template). Each template
         section says which of their sections feeds it, the words to use (their kept words, the
         rewrites applied), and the placeholders only the owner can fill. Cut sections are left out.
         Their live page is never touched. Works whatever their site is built on.
  seo  - their EXISTING page, as a to-do list in page order: what to keep, what to rewrite, what to
         move under a Read more, what to add. The menu and footer stay; nothing is deleted that
         search needs.
  both - both of the above.

Every fact only the owner has - a number, the guarantee terms, the price, a review count, a video,
a photo - becomes one plain question. Nothing is invented; the page cannot go live with a placeholder.

    python3 code/audit/build_plan.py context/pages/<slug> --mode ads|seo|both
    -> context/pages/<slug>/build-plan.md and build-plan.json
"""
import argparse
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))

from audit import walk as W  # noqa: E402
from audit.eighteen import EIGHTEEN  # noqa: E402

NAMES = {n: name for n, name, _, _ in EIGHTEEN}
NAMES[2] = "The proof in the first screen"

# The course template's sections, in its fixed order, and the audit section kinds that feed each.
TEMPLATE = [
    ("Top line: name and phone", ["nav"], "Business name and a tappable phone number. No menu - this is an ad page."),
    ("First screen", ["hero"], "Pain line, headline with the service and the city, the offer and guarantee line, three proof ticks, the form button and the phone, then the founder video."),
    ("Founder video", ["founder_video"], "You on camera, about 45 seconds: who you are, why, the promise."),
    ("Client logos", ["proof_logos"], "Five to eight logos of clients people know, with a line saying what they are."),
    ("Selected work", ["gallery"], "Real finished work, one line on each."),
    ("Video testimonials", ["proof_video"], "Clients on camera: what was broken, what happened, what changed."),
    ("Process", ["steps"], "Three or four steps, each a title and one short line, ending on what they get."),
    ("What you get - three benefits", ["body"], "The three strongest benefits, each: headline, one short paragraph, bullets in the chain, both buttons, the reply time, a touch of proof - picture on the other side."),
    ("Kind words - written reviews", ["proof_quotes"], "Every review with a name and a face, the long ones cut to their best line with a Read more, and a total rating with the stars at the top."),
    ("Real results", ["stats", "pricing"], "Results with numbers, or the price."),
    ("The form", ["form"], "Title, a short paragraph, three bullets, the form, the reply time, the guarantee, review badges, and the phone."),
    ("Questions", ["faq"], "Six or more questions people ask BEFORE they enquire, each answered in a line or two."),
    ("Legal line", ["footer"], "One line: the business name, the year, privacy. Nothing after it."),
]

# The one question to ask the owner for each component that is missing or waiting on a fact.
ASK = {
    1: "Can you record about 45 seconds on your phone: who you are, why you do this, and the promise this page makes?",
    2: "What rating and review count can we show, from which platform? And can we use three client photos?",
    4: "What exactly do they get, and by when? Say it the way you would on the phone.",
    6: "Which two or three happy clients would record a short phone video: what was broken, what happened, what changed?",
    9: "How fast do you reply to a new enquiry, honestly - in minutes or hours?",
    10: "Can we use six or more written reviews, each with the client's name and a photo?",
    11: "Which fields do you need to call someone back? First name, last name, phone, email and one qualifying question is the default.",
    12: "Is there something useful you can give them for enquiring - a price guide, a checklist, a preview - with a picture of it?",
    13: "Which review platforms are you on (Google, Facebook, Yelp, Trustpilot, TrustIndex, Capterra, G2, Bark), and what are your scores and counts?",
    15: "Which three or four pieces of finished work are you proudest of, and what was the result of each?",
    20: "What will you promise if it does not work - money back, a redo, you stop paying? Only what you would honour.",
    21: "Where do people land after the form, and when do you call them?",
    22: "Which phone number should the page show, and who answers it?",
    23: "Which three or four numbers can we show: years in business, jobs or clients, the rating, anything else you can prove?",
    24: "Which five to eight clients' logos can we show?",
}


def _texts(facts, band):
    return [t["text"] for t in sorted((facts.get("textAt") or []), key=lambda t: t.get("top") or 0)
            if t.get("top") is not None and band["top"] <= t["top"] < band["bot"]]


def _brackets(s):
    return re.findall(r"\[([^\]\n]{2,60})\]", s or "")


def plan(page_dir, mode="ads"):
    j = json.load(open(os.path.join(page_dir, "judgments.json")))
    a = json.load(open(os.path.join(page_dir, "audit.json")))
    facts = a["capture"]["viewports"]["desktop"]["facts"]
    bands = {b["id"]: b for b in W.build_bands(facts)}
    cards = j.get("cards") or []
    items = {int(k): v for k, v in ((j.get("page") or {}).get("items") or {}).items()}
    comp = {}
    for c in cards:
        for k, v in (c.get("holds") or {}).items():
            comp[int(k)] = {**v, "section": c["id"]}
    for k, v in items.items():
        comp.setdefault(k, {**v, "section": None})
    num = {c["id"]: i + 1 for i, c in enumerate(cards)}

    questions, seen_q = [], set()

    def ask(n=None, text=None, why=""):
        q = text or ASK.get(n)
        if q and q not in seen_q:
            seen_q.add(q)
            questions.append({"ask": q, "for": why or (NAMES.get(n) if n else "")})

    for n, v in sorted(comp.items()):
        if (v.get("status") or "") in ("missing", "weak", "unchecked") and n in ASK:
            ask(n, why=NAMES.get(n, ""))
    for c in cards:
        for r in c.get("rewrites") or []:
            for b in _brackets(r.get("after") or ""):
                ask(text=f'What goes in "[{b}]"? ("{r["after"][:80]}")', why=f'section {num[c["id"]]}, {c.get("is", "")}')
        for key in ("eyebrow", "headline", "subheadline"):
            for b in _brackets((c.get(key) or {}).get("says")):
                ask(text=f'What goes in "[{b}]" in the {key}?', why="the first screen")

    out = {"mode": mode, "url": a.get("url"), "do_first": (j.get("page") or {}).get("do_first") or [],
           "owner_questions": questions}

    if mode in ("ads", "both"):
        sections = []
        phones = [t.get("text") for t in (facts.get("tel") or []) if t.get("text")]
        moved = []   # words that sat beside a founder video belong with the benefits, not in the video slot
        for name, kinds, spec in TEMPLATE:
            feeders = [c for c in cards if c.get("kind") in kinds and c.get("verdict") in ("keep", "fix")]
            if name.startswith("Top line"):
                entry = {"template_section": name, "spec": spec, "from": ["their logo, from the page's menu bar"],
                         "words": [], "apply": [f"phone: {phones[0]}" if phones else "phone: none on the page - ask the owner"],
                         "placeholders": [] if phones else ["A phone number people can tap"]}
                sections.append(entry)
                continue
            entry = {"template_section": name, "spec": spec, "from": [], "words": [], "apply": [], "placeholders": []}
            for c in feeders:
                b = bands.get(c["id"])
                entry["from"].append(f'section {num[c["id"]]}: {c.get("is", "")} ({c["verdict"]})')
                if b:
                    entry["words"] += [t for t in _texts(facts, b) if len(t.split()) >= 2][:30]
                for key in ("eyebrow", "headline", "subheadline"):
                    x = c.get(key) or {}
                    if (x.get("says") or "").strip():
                        entry["apply"].append(f'{key}: {x["says"]}')
                rw = [f'rewrite "{r["before"][:90]}" as "{r["after"]}"' for r in c.get("rewrites") or [] if r.get("after")]
                nt = [f'{n_.get("tag", "Fix")}: {n_["says"]}' for n_ in c.get("notes") or []]
                if c.get("kind") == "founder_video":
                    video = [x for x in nt if re.search(r"video|seconds|thumbnail|camera", x, re.I)]
                    moved += [f'(from section {num[c["id"]]}) {x}' for x in rw + [x for x in nt if x not in video]]
                    entry["apply"] += video + [f'{NAMES[1]}: {(c.get("holds") or {}).get("1", {}).get("note", "")}']
                else:
                    entry["apply"] += rw + nt
            if name.startswith("What you get") and moved:
                entry["apply"] += moved
            # components that belong in this template section and are missing
            for n, v in sorted(comp.items()):
                sec = v.get("section")
                owner_kind = next((c.get("kind") for c in cards if c["id"] == sec), None) if sec else None
                if (v.get("status") in ("missing",)) and (owner_kind in kinds or (not sec and _home_matches(n, kinds))):
                    entry["placeholders"].append(f'{NAMES.get(n, n)}: {v.get("note") or ""}'.strip())
            if not feeders and not entry["placeholders"]:
                entry["placeholders"].append("Nothing on the current page feeds this section - build it from the template with placeholders.")
            sections.append(entry)
        out["new_page"] = sections
        out["left_out"] = [f'section {num[c["id"]]}: {c.get("is", "")} - {c.get("why", "")}' for c in cards if c.get("verdict") == "cut"]

    if mode in ("seo", "both"):
        todo = []
        for c in cards:
            v = c.get("verdict")
            line = {"section": f'section {num[c["id"]]}: {c.get("is", "")}', "verdict": v}
            if v == "keep":
                line["do"] = ["Leave it."]
            elif v == "fix":
                line["do"] = ([f'Rewrite "{r["before"][:90]}" as "{r["after"]}"' for r in c.get("rewrites") or [] if r.get("after")]
                              + [f'{n_.get("tag", "Fix")}: {n_["says"]}' for n_ in c.get("notes") or []]
                              + [f'{k}: {(c.get(k) or {}).get("says")}' for k in ("eyebrow", "headline", "subheadline") if (c.get(k) or {}).get("says")])
            else:
                # for search the words stay on the page: a repeat is merged, the rest goes under a Read more
                if c.get("kind") in ("nav", "footer"):
                    line["do"] = ["Keep it on the SEO page - people and Google use it to move around the site."]
                elif c.get("repeats"):
                    line["do"] = [f'Merge its words into section {c["repeats"]}, under a Read more.']
                else:
                    line["do"] = ["Move it lower, under a Read more, or delete it if it adds nothing for search."]
            todo.append(line)
        out["seo_todo"] = todo
    return out


def _home_matches(n, kinds):
    from audit.eighteen import HOME
    return any(k in kinds for k in HOME.get(n, []))


def write_md(p, path):
    L = [f"# Build plan: {p.get('url')}", "", f"Mode: **{p['mode']}**.", ""]
    if p.get("do_first"):
        L += ["## Do these first", ""] + [f"{i}. {x}" for i, x in enumerate(p["do_first"], 1)] + [""]
    if p.get("owner_questions"):
        L += ["## Questions for the owner", "", "Every placeholder on the page waits on one of these. Nothing is invented.", ""]
        L += [f"{i}. {q['ask']} *({q['for']})*" for i, q in enumerate(p["owner_questions"], 1)] + [""]
    if p.get("new_page"):
        L += ["## The new ad page, section by section", "", "Built from `website/app/lp/_template`. Their live page is not touched.", ""]
        for s in p["new_page"]:
            L += [f"### {s['template_section']}", "", f"**What it holds:** {s['spec']}", ""]
            if s["from"]:
                L += ["**Fed by:** " + "; ".join(s["from"]), ""]
            if s["apply"]:
                L += ["**Apply:**", ""] + [f"- {x}" for x in s["apply"]] + [""]
            if s["placeholders"]:
                L += ["**Placeholders:**", ""] + [f"- {x}" for x in s["placeholders"]] + [""]
        if p.get("left_out"):
            L += ["## Left out of the ad page", ""] + [f"- {x}" for x in p["left_out"]] + [""]
    if p.get("seo_todo"):
        L += ["## Their existing page, for search", "", "In page order. The menu and footer stay.", ""]
        for t in p["seo_todo"]:
            L += [f"### {t['section']} ({t['verdict']})", ""] + [f"- {x}" for x in t["do"]] + [""]
    open(path, "w").write("\n".join(L))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("page_dir")
    ap.add_argument("--mode", choices=["ads", "seo", "both"], default="ads")
    x = ap.parse_args()
    p = plan(x.page_dir, x.mode)
    json.dump(p, open(os.path.join(x.page_dir, "build-plan.json"), "w"), indent=1)
    write_md(p, os.path.join(x.page_dir, "build-plan.md"))
    n_ph = sum(len(s["placeholders"]) for s in p.get("new_page", []))
    print(f"build plan written: {len(p.get('new_page', []))} template sections, {n_ph} placeholders, "
          f"{len(p['owner_questions'])} questions for the owner, {len(p.get('left_out', []))} sections left out")
    print(os.path.join(x.page_dir, "build-plan.md"))
