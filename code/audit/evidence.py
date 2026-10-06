"""What real people said and did on the control, sorted by the challenger axis it bears on.

    python3 code/audit/evidence.py <url>            # every axis, with its evidence
    python3 code/audit/evidence.py <url> --json     # the same, for challenger.py

⛔ WHY THIS EXISTS (Jono, 28 September 2026). The challenger interview first read only the audit, so
every recommendation was a heuristic. Three better sources already sit in the repo:
- the buyers: context/personas/, lines from real calls, emails and quotes
- the panel's read of this page: a simulation, and labelled as one
- the visitors: the heat map, the scroll map, the form drop-off and the ten recordings, from /analytics
This file gathers all three and routes each line to the axes it bears on, so a recommendation can say
"7 of 10 recordings stopped at the office photo" instead of "best practice says".

Weight, highest first: what visitors did · what buyers said on real calls · how the panel reacted. The
panel catches confusion; it cannot predict conversion. Nothing here invents a line: an axis with no
evidence says so, and the interview says its pick is a heuristic.
"""
import argparse
import glob
import json
import os
import re
import sys
from datetime import date, datetime
from urllib.parse import urlparse

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))

from audit.common import ROOT, out_dir_for  # noqa: E402

VISITORS, SAID, PANEL = 3, 2, 1
LABEL = {VISITORS: "visitors", SAID: "buyer said", PANEL: "panel (simulated)"}
PER_AXIS = 6
PER_BUYER = 2   # per axis, so one talkative buyer cannot crowd the others out
STALE_DAYS = 30
NOT_PERSONAS = {"README.md", "why-primary.md", "evidence.md", "runs.md"}

# Which evidence bears on which axis. `kinds` routes by what the line is; `words` by what it says.
RISK = r"risk|up ?front|prior to|lock|minimum|refund|money back|guarantee|zero|fired|burn|contract|trust"
ROUTES = {
    "benefit": {"kinds": {"silent", "buys_on", "trigger", "moves"}, "words": r"hero|first screen|headline|benefit"},
    "headline": {"kinds": {"silent", "trigger"}, "words": r"hero|first screen|headline|top of|0% down|25% down"},
    "offer": {"kinds": {"buys_on", "acts"}, "words": r"price|cost|pay|month|deliver|build|own|mine|yours|offer|what you get"},
    "guarantee": {"kinds": set(), "words": RISK},
    "response_time": {"kinds": set(), "words": r"phone number|repl(y|ies)|respond|call(ed)? back|waiting|speed|minutes?\b|seconds?\b|same (day|night|hour)"},
    "three_benefits": {"kinds": {"moves", "buys_on", "silent"}, "words": r"three reasons|why us|benefit"},
    "features": {"kinds": {"buys_on"}, "words": r"what (you|they)('re| are)? doing|transparen|mine|yours|own it|report|built|included"},
    "proof_bullets": {"kinds": set(), "words": r"\b(roi|proof|results?|reported|impressions|leads|case stud(y|ies)|stats?)\b"},
    "images": {"kinds": set(), "words": r"\b(images?|photos?|photographs?|pictures? of|gallery|portfolio|rebuilt|selected work)\b|\(img\)"},
    "cta_text": {"kinds": {"click", "dead", "rage", "acts"}, "words": r"\b(button|book(ing)?|get my|get a|find the)\b"},
    "form": {"kinds": {"form"}, "words": r"form|field|started the|submit|enquir"},
    "sections": {"kinds": {"scroll", "panel_exit"}, "words": r"\b(section|how it works|process|skip(s|ped)?|placeholder)\b|stopped at|leaves? at|left at"},
    "faq": {"kinds": {"leave", "anxiety"}, "words": r"faq|question|objection|what happens"},
    "order": {"kinds": {"scroll", "panel_exit"}, "words": r"before (reaching|the form)|\b(below|above)\b|order of|stopped at|leaves? at|left at"},
    "length": {"kinds": {"scroll"}, "words": r"scrolled|halfway|% down|long|short|skim"},
}


def _item(weight, kind, text, where="", who="", primary=False):
    text = re.sub(r"\s+", " ", text).strip()
    # route on the words themselves, never on the source tag after " · " ("photo booth company", "fit call")
    return {"weight": weight, "source": LABEL[weight], "kind": kind, "where": where, "who": who, "primary": primary,
            "match": text.split(" · ")[0],
            "text": text if len(text) <= 170 else text[:167].rstrip() + "..."}


def _fields(path):
    """A persona file as {field: value or [sub-bullets]}. Top-level '- Key: value', then '  - sub'."""
    out, key = {}, None
    for line in open(path, encoding="utf-8").read().splitlines():
        top = re.match(r"^- ([^:]+):\s*(.*)$", line)
        sub = re.match(r"^\s{2,}- (.+)$", line)
        if top:
            key = top.group(1).strip().lower()
            out[key] = top.group(2).strip() or []
        elif sub and key is not None and isinstance(out.get(key), list):
            out[key].append(sub.group(1).strip())
    return out


def buyer_files():
    """(name, primary, fields) per APPROVED buyer, primary first. An unapproved file is a draft and never votes."""
    out = []
    for p in sorted(glob.glob(os.path.join(ROOT, "context", "personas", "*.md"))):
        if os.path.basename(p) in NOT_PERSONAS:
            continue
        f = _fields(p)
        if not f.get("approved") or isinstance(f.get("approved"), list):
            continue
        head = open(p, encoding="utf-8").readline()
        name = head.lstrip("# ").split("·")[0].strip() or os.path.basename(p)[:-3]
        out.append((name, str(f.get("primary", "")).lower().startswith("yes"), f))
    return sorted(out, key=lambda b: not b[1])


def buyers():
    items, names = [], []
    for name, primary, f in buyer_files():
        names.append(name + (" (primary)" if primary else ""))
        for key, kind in (("silent question", "silent"), ("what they buy on", "buys_on"), ("trigger", "trigger")):
            if isinstance(f.get(key), str) and f[key]:
                items.append(_item(SAID, kind, f"{name}, {key}: {f[key]}", who=name, primary=primary))
        for key, kind in (("leave moment", "leave"), ("anxiety and habit", "anxiety"), ("verbatim lines", "verbatim")):
            for line in f.get(key) or []:
                text = f"{name}: {line}" if kind == "verbatim" else f"{name}, {key}: {line}"
                items.append(_item(SAID, kind, text, who=name, primary=primary))
    return items, names


def _quote(line):
    """A verbatim line without its source tag - the words to borrow, not the citation."""
    return line.split(" · ")[0].strip()


def buyer_brief(verbatim=3):
    """⛔ THE BUYERS WRITE THE PAGE (Jono, 28 September 2026). The visitors decide what gets fixed or cut; the
    buyers decide the words and the emotion. This is the copy guide the challenger is written to, in the
    order the page sells: the moment they started looking, the question they will not ask out loud, what
    they buy on, and every moment they leave - each one answered before the form. See references/persuasion.md
    sections 4, 5 and 10: objections, their words, grade 7."""
    files = buyer_files()
    if not files:
        return ["## Written for the buyers", "",
                "- No approved buyers in context/personas/, so the words rest on the audit alone. /personas builds them.", ""]
    L = ["## Written for the buyers - the words and the emotion", "",
         "- Every headline, benefit, FAQ answer and button rests on one line below. Their words, not ours.",
         "- The page sells in this order: the moment, the unasked question, what they buy on, then every leave moment.",
         "- Borrowed words are phrasing only. Never print them as a quote or a testimonial.",
         "- Grade 7 or under. Each line ends on something they can picture: a call, a job, money, hours back.", ""]
    for name, primary, f in files:
        L += [f"### {name}" + (" · primary, the page is written to them first" if primary else ""), ""]
        for key, use in (("trigger", "The first screen names this moment, in these words"),
                         ("silent question", "Answered above the fold, without being asked"),
                         ("what they buy on", "The three benefits prove this")):
            if isinstance(f.get(key), str) and f[key]:
                L += [f"- {use}:", f"  - {f[key]}"]
        leaves = f.get("leave moment") or []
        if leaves:
            # ⛔ Only the worries a stranger would share. "Is it mine or yours?" came from a real call and
            # still sold nothing on the page (Jono, 28 September 2026): the obvious is left unsaid.
            L += ["- Where they leave - answer the ones a stranger would share, never the obvious:"] + [f"  - {x}" for x in leaves]
        lines = [_quote(x) for x in (f.get("verbatim lines") or [])[:verbatim]]
        if lines:
            L += ["- Words to borrow:"] + [f"  - {x}" for x in lines]
        L.append("")
    return L


def panel(page_dir):
    """The panel's read of THIS page. A read of another page is not evidence about this one."""
    items, read = [], []
    for p in sorted(glob.glob(os.path.join(page_dir, "persona-read", "*.json"))):
        if os.path.basename(p) == "needed.json":
            continue
        try:
            sheet = json.load(open(p))
        except (OSError, ValueError):
            continue
        who = sheet.get("buyer") or os.path.basename(p)[:-5]
        read.append(who)
        if not sheet.get("acts") and sheet.get("acts_why"):
            items.append(_item(PANEL, "panel_exit", f"The panel's {who}: {sheet['acts_why']}"))
        for s in sheet.get("sections") or []:
            if s.get("reaction") != "leaves" and s.get("tone") != "misses":
                continue
            verb = "leaves at" if s.get("reaction") == "leaves" else "misses something at"
            items.append(_item(PANEL, "panel_miss", f"The panel's {who} {verb} {s.get('name')}: {s.get('says', '')}", s.get("name", "")))
            rw = s.get("rewrite") or {}
            if isinstance(rw, dict) and rw.get("after"):
                items.append(_item(PANEL, "moves", f"The panel's {who} would stay for: \"{rw['after']}\" ({rw.get('moves', '')})", s.get("name", "")))
    return items, read


_HEADINGS = {
    "the numbers": "numbers", "how far they scroll": "scroll", "where they click (": "click",
    "where they rage click": "rage", "where they click and nothing happens": "dead",
    "where the form dies": "form", "where they quit the form": "form", "how far each section gets": "scroll",
    "claude's read": "read", "gemini's read": "read",
    "test later": "test_later",
}


def visitors(path):
    """The newest session read of this page, section by section. Its age is reported, never hidden."""
    reads = []
    for p in glob.glob(os.path.join(ROOT, "context", "sessions", "20*.md")):
        lines = open(p, encoding="utf-8").read().splitlines()
        m = re.search(r"containing (\S+)", lines[1]) if len(lines) > 1 else None
        if m and path and m.group(1).rstrip("/") == path.rstrip("/"):
            reads.append((os.path.basename(p)[:10], p, lines))
    if not reads:
        return [], None
    day, _p, lines = max(reads)
    items, kind = [], None
    for line in lines:
        if line.startswith("## "):
            h = line[3:].lower()
            kind = next((v for k, v in _HEADINGS.items() if h.startswith(k)), None)
            continue
        m = re.match(r"^- (.+)$", line)
        if kind and m and not m.group(1).startswith("(filled by") and m.group(1).strip():
            items.append(_item(VISITORS, kind, f"{m.group(1)} (read {day})"))
    return items, day


MIN_ANALYSIS_SESSIONS = 50
_GROUP_KIND = (("form", "form"), ("where they leave", "scroll"), ("broken", "dead"),
               ("what happens to the ones who stay", "acts"), ("working", "working"), ("sessions", "read"))


def analysis(path):
    """The /analytics dashboard's own analysis of this page: each finding's verdict, what happens and
    the change it asks for. Read from the JSON the dashboard embeds in <script id="visitors-data"> - the
    builder refuses to render without that block, so it is the contract - never from the HTML around it."""
    best = None
    for p in glob.glob(os.path.join(ROOT, "context", "sessions", "*.html")):
        try:
            m = re.search(r'<script id="visitors-data" type="application/json">(.*?)</script>', open(p, encoding="utf-8").read(), re.S)
            d = json.loads(m.group(1).replace("<\\/", "</")) if m else None
        except (OSError, ValueError):
            continue
        if not d or not d.get("findings") or (d.get("page") or "").rstrip("/") != path.rstrip("/"):
            continue
        if best is None or os.path.getmtime(p) > best[0]:
            best = (os.path.getmtime(p), d)
    return best[1] if best else None


def analysis_items(a):
    items = []
    for f in (a or {}).get("findings") or []:
        group = (f.get("group") or "").lower()
        kind = "leak" if "off the page" in (f.get("title") or "") else next((k for g, k in _GROUP_KIND if g in group), "finding")
        change = f" Change: {f['change']}" if f.get("change") else ""
        item = _item(VISITORS, kind, f"{f.get('title', '')} ({f.get('verdict', '')}).{change}", f.get("where") or "")
        item["match"] = f.get("title") or ""   # route on what happened, never on the words of the advice
        items.append(item)
    return items


def findings():
    """Open findings and queued tests from /analytics. Fixed, won and lost ones are history."""
    items = []
    p = os.path.join(ROOT, "context", "visitor-findings.md")
    if os.path.exists(p):
        head, status = None, ""
        for line in open(p, encoding="utf-8").read().splitlines() + ["## end"]:
            if line.startswith("## "):
                if head and not re.search(r"fixed|won|lost", status, re.I):
                    items.append(_item(VISITORS, "finding", head))
                head = None if line.lower().startswith(("## how a block", "## end")) else line[3:]
                status = ""
            elif line.lower().startswith("- status:"):
                status = line
            elif head and line.lower().startswith("- change:"):
                head = f"{head} - change: {line.split(':', 1)[1].strip()}"
    q = os.path.join(ROOT, "context", "test-queue.md")
    if os.path.exists(q):
        example = False
        for line in open(q, encoding="utf-8").read().splitlines():
            if line.startswith("## "):
                example = line.lower().startswith("## how an item")
            m = re.match(r"^- We believe:\s*(.+)$", line)
            if m and not example:
                items.append(_item(VISITORS, "test_later", "Queued test: " + m.group(1)))
    return items


def route(items):
    axes = {}
    for key, r in ROUTES.items():
        hit = [i for i in items if i["kind"] in r["kinds"] or re.search(r["words"], i["match"] + " " + i["where"], re.I)]
        hit.sort(key=lambda i: (-i["weight"], not i["primary"]))  # stable, so file order holds within a tier
        kept, per = [], {}
        for i in hit:
            if i["who"] and per.get(i["who"], 0) >= PER_BUYER:
                continue
            per[i["who"]] = per.get(i["who"], 0) + 1
            kept.append(i)
        axes[key] = kept[:PER_AXIS]
    return axes


def gather(url):
    page_dir = out_dir_for(url)
    path = urlparse(url).path or url
    b, names = buyers()
    pn, read = panel(page_dir)
    v, day = visitors(path)
    an = analysis(path)
    f = findings() + analysis_items(an)
    missing = []
    if not names:
        missing.append("No approved buyers in context/personas/. /personas builds them.")
    elif not read:
        missing.append("No panel read of this page. Run the /personas read on the control first.")
    if not day:
        missing.append(f"No session read of {path} in context/sessions/. /analytics reads it once it has 50 sessions.")
    elif (date.today() - datetime.strptime(day, "%Y-%m-%d").date()).days > STALE_DAYS:
        missing.append(f"The newest session read is from {day}, over {STALE_DAYS} days old. /analytics refreshes it.")
    if an and int(an.get("sessions") or 0) < MIN_ANALYSIS_SESSIONS:
        missing.append(f"The visitor analysis of {path} rests on {an.get('sessions') or 0} sessions. Under "
                       f"{MIN_ANALYSIS_SESSIONS} it is a hint, not a rule - check they are real visitors, not our own checks.")
    return {"url": url, "buyers": names, "panel_read": read, "session_read": day, "analysis": an,
            "counts": {"visitors": len(v) + len(f), "buyer said": len(b), "panel (simulated)": len(pn)},
            "missing": missing, "axes": route(v + f + b + pn)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("url")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    ev = gather(a.url)
    if a.json:
        print(json.dumps(ev, indent=1))
        return
    print(f"# Evidence · {a.url}")
    print(" · ".join(f"{n} {k}" for k, n in ev["counts"].items()))
    for m in ev["missing"]:
        print(f"- Missing: {m}")
    for key, lines in ev["axes"].items():
        print(f"\n## {key}")
        for e in lines or [{"source": "none", "text": "no evidence on file - a pick here is a heuristic"}]:
            print(f"- {e['source']}: {e['text']}")


if __name__ == "__main__":
    main()
