"""What the visitors force on the rebuild, before anyone's opinion is asked.

    python3 code/audit/visitor_fixes.py <url>           # the fixes, as a list
    python3 code/audit/visitor_fixes.py <url> --json    # the same, for challenger.py

⛔ FOUR RULES (Jono, 28 September 2026). The heat map and the recordings are not background reading. Each
one turns into a change, and none of them is a question for the interview:
1. A click on something that is not a link: make it a link to the form, or stop it looking clickable.
2. A form field people quit on: remove it. Name, phone and email are how the lead is reached, so those
   are fixed (type, format, error message) instead of removed.
3. A section that loses far more people than the rest: cut it or shrink it. Social proof is moved higher
   instead, never removed or rewritten - it is identical on both arms.
4. A link that takes people off the page: remove it. Privacy and terms stay, small, in the footer.

Rules 1 and 4 are bugs: they are fixed on BOTH arms before the test starts, because a bug is not a test
variable. So is a broken contact field under rule 2. Removing a field and cutting a section change the
page's shape, so those go on the challenger.

It reads context/sessions/<date>.json (written by code/read_sessions.py) for the visitor numbers, and the
page's audit for links that leak even when nobody has clicked them yet. Under MIN_SESSIONS the numbers are
reported as early and nothing is forced - except the audit's leaks, which need no traffic to be wrong.
"""
import argparse
import glob
import json
import os
import re
import statistics
import sys
from urllib.parse import urlparse

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))

from audit.common import ROOT, out_dir_for  # noqa: E402
from audit.invert import SOCIAL_PROOF_KINDS, classify  # noqa: E402

MIN_SESSIONS = 50            # below this, a click map is a handful of people
NONLINK_MIN = (5, 3)         # clicks, people - on something that is not a link
DEAD_MIN = 5                 # clicks that changed nothing
FIELD_EXIT_MIN = (3, 0.15)   # sessions, share of form starters whose last field was this one
SECTION_MIN_REACHED = 30     # a section needs this many viewers before its loss means anything
SECTION_LOSS_FLOOR = 25      # % who never reach the next section, before it is a candidate
SECTION_LOSS_RATIO = 1.5     # and this many times the page's median loss
CONTACT_FIELD = re.compile(r"^(first_?name|last_?name|full_?name|name|phone|tel|mobile|email)$", re.I)
CLICKABLE_TAGS = ("a", "button", "input", "label", "select", "textarea")
BOTH, CHALLENGER = "both arms, before the test starts", "the challenger"


def newest_read(path):
    """The newest session read of this page, as data. None when /analytics has not read it."""
    reads = []
    for p in glob.glob(os.path.join(ROOT, "context", "sessions", "20*.json")):
        try:
            d = json.load(open(p))
        except (OSError, ValueError):
            continue
        if (d.get("url") or "").rstrip("/") == path.rstrip("/") and not d.get("include_dev"):
            reads.append((d.get("date", ""), d))
    return max(reads, key=lambda r: r[0])[1] if reads else None


def _fix(rule, change, evidence, applies):
    return {"rule": rule, "change": change, "evidence": evidence, "applies": applies}


def clicks(read):
    out = []
    for r in read.get("clicks") or []:
        tag = (r.get("tag") or "").split(":")[0].lower()
        if tag in CLICKABLE_TAGS or int(r.get("n") or 0) < NONLINK_MIN[0] or int(r.get("people") or 0) < NONLINK_MIN[1]:
            continue
        what = r.get("el") or f"a <{tag}> with no text"
        out.append(_fix(1, f"\"{what[:50]}\" is clicked like a link: make it scroll to the form, or stop it looking clickable",
                        f"{r['n']} clicks by {r['people']} people on a <{tag}>", BOTH))
    for r in read.get("dead") or []:
        if int(r.get("n") or 0) >= DEAD_MIN:
            out.append(_fix(1, f"\"{(r.get('el') or 'no text')[:50]}\" does nothing when clicked: make it work, or make it plain",
                            f"{r['n']} dead clicks", BOTH))
    return out


def fields(read):
    form = read.get("form") or {}
    started = int(form.get("started") or 0)
    out = []
    for r in form.get("exits") or []:
        n, name = int(r.get("sessions") or 0), (r.get("field") or "").strip()
        if not name or n < FIELD_EXIT_MIN[0] or (started and n / started < FIELD_EXIT_MIN[1]):
            continue
        share = f"{n} of {started} who started the form left at it" if started else f"{n} sessions left at it"
        if CONTACT_FIELD.match(name):
            out.append(_fix(2, f"Fix the {name} field, do not remove it: it is how the lead is reached. Check its type, its format and its error message",
                            share, BOTH))
        else:
            out.append(_fix(2, f"Remove the {name} field. Ask it on the call instead", share, CHALLENGER))
    return out


def sections(read):
    out = []
    for cls, d in (read.get("reach") or {}).items():
        secs = d.get("sections") or []
        # the hero's loss is the headline's job, the form's is rule 2's, and the last section has no next
        judged = [s for s in secs[1:-1] if s.get("lost_pct") is not None and s["name"].lower() != "form"
                  and int(s.get("reached") or 0) >= SECTION_MIN_REACHED]
        if len(judged) < 3:
            continue
        median = statistics.median(s["lost_pct"] for s in judged)
        for s in judged:
            if s["lost_pct"] < max(SECTION_LOSS_FLOOR, SECTION_LOSS_RATIO * median):
                continue
            ev = f"on {cls}, {s['lost_pct']}% of the {s['reached']} who reached it never reached the next · the page's median is {median:.0f}%"
            if classify(s.get("heading") or s["name"]) in SOCIAL_PROOF_KINDS:
                out.append(_fix(3, f"\"{s['name']}\" loses people, but it is social proof: move it higher, never remove or rewrite it", ev, CHALLENGER))
            else:
                out.append(_fix(3, f"Cut \"{s['name']}\", or shrink it to its one strongest line", ev, CHALLENGER))
    return out


def leaks(url, read):
    """Leaks the audit found on the page, with their clicks when the session read has them."""
    clicked = {r["href"]: r for r in (read or {}).get("links") or [] if r.get("kind") == "leak"}
    out, seen = [], set()
    p = os.path.join(out_dir_for(url), "audit.json")
    items = []
    if os.path.exists(p):
        try:
            items = ((json.load(open(p)).get("assets") or {}).get("links") or {}).get("items") or []
        except (OSError, ValueError):
            items = []
    for r in items:
        href = r.get("href") or ""
        if r.get("kind") == "legal" or href in seen:
            continue
        seen.add(href)
        c = clicked.pop(href, None)
        ev = f"{r.get('kind', 'link')} in the {r.get('where') or 'page'}" + (f" · {c['n']} clicks by {c['people']} people" if c else " · found by the audit")
        out.append(_fix(4, f"Remove the link \"{(r.get('text') or href)[:40]}\" ({href[:60]})", ev, BOTH))
    for href, c in clicked.items():   # clicked, but the audit never saw it - a link added since
        out.append(_fix(4, f"Remove the link {href[:60]}", f"{c['n']} clicks by {c['people']} people", BOTH))
    return out


def fixes(url):
    path = urlparse(url).path or url
    read = newest_read(path)
    sessions = int((read or {}).get("sessions") or 0)
    out = {"url": url, "read": (read or {}).get("date"), "sessions": sessions, "early": sessions < MIN_SESSIONS,
           "fixes": leaks(url, read)}
    if read and not out["early"]:
        out["fixes"] = clicks(read) + fields(read) + sections(read) + out["fixes"]
    if not read:
        out["note"] = f"No session read of {path}. Only the audit's leaks apply until /analytics reads it."
    elif out["early"]:
        out["note"] = f"{sessions} sessions, under {MIN_SESSIONS}. Clicks, fields and sections are too early to force a change."
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("url")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    f = fixes(a.url)
    if a.json:
        print(json.dumps(f, indent=1))
        return
    print(f"# Visitor fixes · {a.url}")
    print(f"{len(f['fixes'])} fixes · session read {f['read'] or 'none'} · {f['sessions']} sessions")
    if f.get("note"):
        print(f"- Note: {f['note']}")
    for x in f["fixes"]:
        print(f"- Rule {x['rule']}: {x['change']}")
        print(f"  - Evidence: {x['evidence']}")
        print(f"  - Applies to: {x['applies']}")


if __name__ == "__main__":
    main()
