"""Draw the persona dashboard: every buyer file in context/personas/ plus every logged panel round, on one page.

    python3 code/build_persona_dashboard.py                       # context/personas/*.md -> context/personas/dashboard.html
    python3 code/build_persona_dashboard.py --dir references/examples/personas --out /tmp/example.html --business "Dave's Plumbing"

Same shell as the Google Ads and SEO audit dashboards. Copies references/persona-dashboard-template.html and
replaces ONLY the JSON inside <script id="persona-data">. Never edits the template itself.

Reads the persona files in the shape references/persona-panel.md describes: an H1 "Name · label", then
"- Field:" bullets with the value on the line or as sub-bullets. A field the file leaves blank is DROPPED
from the card, never printed as an empty row and never invented. persona_panel.py calls build() after every
logged run so the page is always the current picture.

Two rules the drawing enforces, because a picture is where a wrong weight gets believed:
  - A pattern with no revenue on record is a NON-BUYER. It gets its own section, never a slice of the
    revenue bar and never a vote in the panel's call.
  - When the primary is not the biggest payer, context/personas/why-primary.md must say why in one
    sentence, and it prints beside the revenue bar. No file, and the build says so.
"""
import argparse
import glob
import json
import os
import re
import shutil
import sys
from datetime import date

import _posthog as ph  # only for ROOT

TEMPLATE = os.path.join(ph.ROOT, "references", "persona-dashboard-template.html")
DEFAULT_DIR = os.path.join(ph.ROOT, "context", "personas")
DEFAULT_OUT = os.path.join(DEFAULT_DIR, "dashboard.html")
NOT_A_PERSONA = ("readme.md", "runs.md", "why-primary.md", "evidence.md")   # why-primary.md is from before buyers counted the same   # files in the folder that are not buyers
CONVO_WORDS = r"(?:calls?|phone calls?|dm threads?|dms?|messages?|message threads?|conversations?|interviews?|chats?)"


def norm(label):
    return re.sub(r"\s+", " ", label.replace("’", "'").strip().lower())


def parse_persona(path):
    """One persona file -> dict. Fields keyed by their lowercased label, values as a list of lines."""
    text = open(path, encoding="utf-8").read()
    lines = text.splitlines()
    name, label = os.path.splitext(os.path.basename(path))[0].replace("-", " ").title(), ""
    for line in lines:
        m = re.match(r"^#\s+(.+)$", line)
        if m:
            head = m.group(1).strip()
            parts = re.split(r"\s+·\s+|\s+-\s+|,\s+", head, maxsplit=1)
            name = parts[0].strip()
            label = parts[1].strip() if len(parts) > 1 else ""
            break
    fields, cur = {}, None
    for line in lines:
        top = re.match(r"^- (.+)$", line)
        sub = re.match(r"^\s{2,}[-*] (.+)$", line)
        if top:
            m = re.match(r"^([^:]{1,60}):\s*(.*)$", top.group(1).strip())
            if m:
                cur = norm(m.group(1))
                val = m.group(2).strip()
                fields[cur] = [val] if val else []
            else:
                cur = None
        elif sub and cur is not None:
            fields[cur].append(sub.group(1).strip())

    def sources_raw(f):
        for k in f:
            if k.startswith("sources"):
                return " ".join(f[k])
        return ""

    def field(*keys):
        for k in fields:
            if any(k.startswith(x) for x in keys):
                return fields[k]
        return []

    # Every buyer counts the same (Jono, 29 September 2026: "7 equal buyers" - a share was a guess).
    # A file marked "Non-buyer: yes", a pattern that never paid, is shown and never counted.
    rev_vals = " ".join(field("share of revenue") + field("share of buyers"))
    nonbuyer = " ".join(field("non-buyer")).strip().lower().startswith("yes")
    share = 0 if nonbuyer else 1
    m = re.search(r"from\s+(\d+)\s+(?:jobs?|clients?|sales?|deals?)", rev_vals, re.I)
    jobs = int(m.group(1)) if m else None
    m = re.search(r"(\d+)\s+(?:organisations?|organizations?|businesses|companies|firms)", sources_raw(fields), re.I)
    orgs = int(m.group(1)) if m else None
    primary = False   # no buyer outranks another, so none is primary
    sources = " ".join(field("sources"))
    conversations = sum(int(n) for n, _ in re.findall(r"(\d+)\s+(" + CONVO_WORDS + r")\b", sources, re.I))
    approved = " ".join(field("approved")).strip() or None
    quotes = []
    for q in field("verbatim"):
        if " · " in q:
            t, src = q.rsplit(" · ", 1)
            quotes.append({"text": t.strip(), "source": src.strip()})
        else:
            quotes.append({"text": q.strip(), "source": ""})
    # A line sourced to this business's own buyer is evidence. Anything researched is an assumption,
    # and says so on its own source tag. The two are never totalled together.
    for q in quotes:
        q["assumed"] = bool(re.match(r"^(assumption|assumed|research)", q["source"], re.I))
    assumed_quotes = sum(1 for q in quotes if q["assumed"])
    urgency = []
    for u in field("urgency"):
        m = re.match(r"^(same-hour|same hour|this-week|this week|researching)\s*[:·-]?\s*(\d+)\s*%", u.strip(), re.I)
        if m:
            urgency.append({"kind": m.group(1).lower().replace(" ", "-"), "pct": int(m.group(2))})
    moves, bad_moves = motivations_of(field("moves them"))
    slug = re.sub(r"[^a-z0-9]+", "-", os.path.splitext(os.path.basename(path))[0].lower()).strip("-")
    return {
        "id": "p-" + slug, "file": os.path.basename(path), "name": name, "label": label,
        "primary": primary, "share": share, "jobs": jobs, "conversations": conversations,
        "proto": conversations < 6, "approved": approved, "orgs": orgs, "quotes": quotes, "urgency": urgency,
        "assumed_quotes": assumed_quotes, "evidence_quotes": len(quotes) - assumed_quotes, "fields": fields,
        "moves": moves, "moves_labels": [label_of(m) for m in moves], "bad_moves": bad_moves,
        "personality": personality_of(field("personality")),
    }


# How a buyer reads a page (Jono, 28 September 2026: "different personality type, different buyer").
# Four plain-English styles - the DISC lens his own /personas files already use. A panel should cover all four.
PERSONALITIES = {
    "driver": "decides fast, wants the result and the bottom line",
    "analyst": "wants the detail, the proof and the method",
    "steady": "wants safety, a person to trust and no surprises",
    "expressive": "buys on people, stories and how it will feel",
}


def personality_of(vals):
    word = re.split(r"[\s(,-]", (" ".join(vals or [])).strip().lower() + " ", maxsplit=1)[0]
    return word if word in PERSONALITIES else ""


def _nine():
    from audit.motivations import MOTIVATIONS
    return MOTIVATIONS


def label_of(key):
    return _nine()[key]["label"]


def motivations_of(vals):
    """"Moves them" names two or three of the nine, by key or by label. Returns (keys, unrecognised)."""
    nine = _nine()
    by_label = {re.sub(r"[^a-z ]", "", v["label"].lower()).strip(): k for k, v in nine.items()}
    keys, bad = [], []
    for raw in re.split(r"\s*·\s*|\s*,\s*|\n", " · ".join(vals or [])):
        t = raw.strip().strip("-").strip()
        if not t:
            continue
        k = t if t in nine else by_label.get(re.sub(r"[^a-z ]", "", t.lower()).strip())
        (keys if k else bad).append(k or t)
    return list(dict.fromkeys(keys)), bad


def load_runs(path):
    if not path or not os.path.exists(path):
        return []
    runs = json.load(open(path, encoding="utf-8"))
    try:
        from persona_panel import call_lines
    except Exception:  # the panel script is optional here; the grid still draws
        call_lines = None
    for r in runs:
        if call_lines and "call" not in r:
            r["call"] = call_lines(r)
    return runs


def confidence(personas, extra=None):
    """How much this panel is worth, 0 to 100, decided before anything is built.

    Conversations carry almost all of it, because first-person buyer language is the only thing that
    makes a persona better than a guess. It SATURATES: code saturation lands near twelve conversations
    and meaning saturation near twenty, so forty scores the same as four hundred. Nothing ever reports
    above 95 - a panel simulation does not predict behaviour, however much data went in.
    """
    extra = extra or {}
    conv = sum(p.get("conversations") or 0 for p in personas)
    # (conversations, points) - flat past 40 on purpose
    curve = [(0, 0), (2, 8), (6, 28), (12, 51), (20, 64), (40, 70)]
    pts = curve[-1][1]
    for i, (n, v) in enumerate(curve):
        if conv <= n:
            if i == 0:
                pts = v
            else:
                pn, pv = curve[i - 1]
                pts = pv + (v - pv) * (conv - pn) / (n - pn)   # straight line between the marks
            break
    # Two parts only (Jono, 2 October 2026). The books check went when every buyer began to count the same, and
    # "lost deals" read on camera as deals the owner lost.
    parts = [("conversations", round(pts), 70, f"{conv} real conversation{'' if conv == 1 else 's'} behind the buyers")]
    parts.append(("search terms", 30 if extra.get("search_terms") else 0, 30,
                  "90 days of what people typed into Google" if extra.get("search_terms") else "not added yet: what people typed into Google before they clicked"))
    score = min(95, round(sum(p[1] for p in parts)))
    if score < 20:
        band, means = "guesses", "Useful for catching an unclear page. Useless for deciding who the page is for."
    elif score < 45:
        band, means = "a working hypothesis", "The panel's LEAVE verdicts are notes, never a FIX NOW on their own."
    elif score < 70:
        band, means = "solid", "Every buyer's LEAVE counts the same."
    else:
        band, means = "strong", "Still a simulation. Real visitors remain the only authority."
    return {"score": score, "band": band, "means": means, "conversations": conv,
            "parts": [{"name": n, "got": g, "max": m, "why": w} for n, g, m, w in parts]}


def read_extra(pdir):
    """Flags that cannot be counted from the buyer files, kept in <dir>/evidence.md as plain lines."""
    path = os.path.join(pdir, "evidence.md")
    if not os.path.exists(path):
        return {}
    txt = open(path, encoding="utf-8").read().lower()
    yes = lambda k: bool(re.search(k + r"\s*:\s*yes", txt))
    return {"search_terms": yes("search terms"), "revenue_from_books": yes("revenue split from the books"),
            "lost_deals": yes("lost deals")}


def load_reasons(pdir):
    """The three reasons people buy, from context/voc/reasons.md: '## 1. <reason>' blocks, each with a
    '- Moves them:' line, a '- Buyers: N of 7' line and quotes ending ' · <source>'. Written by /personas step 1c."""
    path = os.path.join(os.path.dirname(os.path.abspath(pdir)), "voc", "reasons.md")
    if not os.path.exists(path):
        return []
    out, cur = [], None
    for line in open(path, encoding="utf-8").read().splitlines():
        m = re.match(r"^##\s+(?:\d+[.)]\s*)?(.+)$", line.strip())
        if m:
            cur = {"title": m.group(1).strip(), "moves": "", "buyers": "", "quotes": []}
            out.append(cur)
            continue
        if cur is None:
            continue
        t = line.strip().lstrip("-").strip()
        low = t.lower()
        if low.startswith("moves them:"):
            cur["moves"] = t.split(":", 1)[1].strip()
        elif low.startswith("buyers:"):
            cur["buyers"] = t.split(":", 1)[1].strip()
        elif re.match(r'^["\u201c]', t):
            text, _, src = t.partition(" · ")
            cur["quotes"].append({"text": text.strip().strip('"\u201c\u201d'), "source": src.strip()})
    return out[:3]


def business_name(override=None):
    """The name on the wordmark. BUSINESS_NAME in .env wins. business.md's H1 is used only when it
    reads like a name - "# What Acme Marketing does" is a document title, not a business, and a heading
    that long on the wordmark is how a dashboard ends up titled after a file."""
    if override:
        return override
    try:
        import _business
        n = (_business.name() or "").strip()
        if looks_like_a_name(n):
            return n
        # business.md's H1 is a document title ("What Acme does"). The business name is usually
        # inside it - take the one capitalised word that is not a question word.
        for w in re.findall(r"\b[A-Z][A-Za-z0-9&'.-]{2,}", n):
            if w.lower() not in ("what", "who", "how", "the", "business", "does", "we"):
                return w
    except Exception:
        pass
    return "Your business"


def looks_like_a_name(n):
    """A wordmark is a name, not a sentence. Four words maximum and no question opener."""
    return bool(n) and len(n.split()) <= 4 and not n.lower().startswith(("what ", "who ", "how ", "the business"))


def build(pdir=DEFAULT_DIR, out=DEFAULT_OUT, runs=None, business=None, template=TEMPLATE, quiet=False):
    files = sorted(f for f in glob.glob(os.path.join(pdir, "*.md"))
                   if os.path.basename(f).lower() not in NOT_A_PERSONA)
    if not files:
        sys.exit(f"No persona files in {os.path.relpath(pdir, ph.ROOT)}/ yet. Run /personas research first - it writes one file per buyer.")
    if not os.path.exists(template):
        sys.exit(f"{os.path.relpath(template, ph.ROOT)} is missing. It ships with the repo - restore it from git before building.")
    personas = [parse_persona(f) for f in files]
    data = {
        "business": business_name(business),
        "date": date.today().strftime("%-d %B %Y"),
        "personas": personas,
        "runs": load_runs(runs if runs else os.path.join(pdir, "runs.json")),
        "reasons": load_reasons(pdir),
        "confidence": confidence(personas, read_extra(pdir)),
    }
    html = open(template, encoding="utf-8").read()
    payload = json.dumps(data, indent=1, ensure_ascii=False).replace("</", "<\\/")
    new, n = re.subn(r'(<script id="persona-data" type="application/json">).*?(</script>)',
                     lambda m: m.group(1) + payload + m.group(2), html, count=1, flags=re.S)
    if n != 1:
        sys.exit("The template has no <script id=\"persona-data\"> block - it has been edited. Restore it from git.")
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    if os.path.abspath(out) != os.path.abspath(template):
        shutil.copyfile(template, out)   # keep the template's bytes for anything the JSON swap does not touch
    open(out, "w", encoding="utf-8").write(new)
    if not quiet:
        report(personas, data["runs"], out, data["reasons"], data["confidence"])
    return out


def report(personas, runs, out, reasons=(), conf=None):
    unapproved = [p["name"] for p in personas if not p["approved"]]
    protos = [p["name"] for p in personas if p["proto"]]
    C = conf or {}
    if C:
        print(f"Confidence: {C['score']} out of 100 - {C['band']}. {C['means']}")
        for part in C["parts"]:
            print(f"    {part['got']:>2} / {part['max']}  {part['why']}")
    print(f"Dashboard: {os.path.abspath(out)}")
    print(f"- {len(personas)} buyer{'s' if len(personas) != 1 else ''} · {sum(p['conversations'] for p in personas)} conversations behind them · {len(runs)} panel round{'s' if len(runs) != 1 else ''} logged")
    buyers = [p for p in personas if p["share"]]
    nonbuyers = [p["name"] for p in personas if not p["share"]]
    if nonbuyers:
        print(f"- Shown separately, never counted (marked Non-buyer): {', '.join(nonbuyers)}.")
    tally = {}
    for p in buyers:
        for m in p["moves_labels"]:
            tally[m] = tally.get(m, 0) + 1
    if tally:
        top = sorted(tally.items(), key=lambda x: -x[1])
        print("- What moves them, counted across the buyers: " + " · ".join(f"{m} {n} of {len(buyers)}" for m, n in top[:5]))
    if not reasons:
        print("- ⛔ No context/voc/reasons.md. Rank the three reasons people buy from what paying buyers said, not from their fears.")
    if protos:
        print(f"- Proto-persona (fewer than six conversations): {', '.join(protos)}. Say so in every verdict.")
    types = {p["personality"] for p in buyers}
    missing = [t for t in PERSONALITIES if t not in types]
    if len(buyers) < 5:
        print(f"- Only {len(buyers)} buyers. A market usually holds about seven - research the ones who never called.")
    unset = [p["name"] for p in personas if not p["personality"]]
    if unset:
        print(f"- ⛔ No personality on: {', '.join(unset)}. Add one of: {', '.join(PERSONALITIES)}.")
    elif missing:
        print(f"- Nobody on the panel reads as: {', '.join(missing)} ({'; '.join(PERSONALITIES[t] for t in missing)}). "
              "Worth researching one.")
    for p in personas:
        if p["bad_moves"]:
            print(f"- ⛔ {p['name']}: 'Moves them' names something that is not one of the nine: {', '.join(p['bad_moves'])}")
        elif not 2 <= len(p["moves"]) <= 3:
            print(f"- ⛔ {p['name']}: 'Moves them' needs two or three of the nine, it has {len(p['moves'])}")
    if unapproved:
        print(f"- Awaiting approval: {', '.join(unapproved)}. The panel does not run until every file carries an Approved line.")
    else:
        print("- Every buyer approved." + ("" if runs else " Next: /personas panel <url>."))


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dir", default=DEFAULT_DIR, help="folder of persona .md files (default context/personas)")
    ap.add_argument("--out", default=None, help="where to write the HTML (default <dir>/dashboard.html)")
    ap.add_argument("--runs", default=None, help="runs.json to draw the panel from (default <dir>/runs.json)")
    ap.add_argument("--business", default=None, help="the name on the wordmark (default BUSINESS_NAME in .env, else business.md's H1)")
    ap.add_argument("--template", default=TEMPLATE)
    a = ap.parse_args()
    build(pdir=a.dir, out=a.out or os.path.join(a.dir, "dashboard.html"), runs=a.runs, business=a.business, template=a.template)
