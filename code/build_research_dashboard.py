"""Draw the research dashboard: what buyers say, what the competitors sell, and the copy the buyers judged.

    python3 code/build_research_dashboard.py                      # context/voc -> context/voc/research.html
    python3 code/build_research_dashboard.py --out <file.html>

It reads what /personas wrote in context/voc/ - reasons.md, reddit.md, reviews.md, rivals.md - and, when it
exists, options-judged.json (every copy option, what was cut and each buyer's verdict). Missing files are
skipped, never invented. The page borrows the persona dashboard's own stylesheet, so the two look like one set.

Every buyer counts the same (Jono, 29 September 2026): a result reads "5 of 7 stay", never a weighted share.
One thing at a time (Jono, 2 October 2026: "aesthetic, beautiful, presentable"): tabs and arrow keys, like the
buyer cards, with the rest folded away.
"""
import argparse
import html
import json
import os
import re
import sys
from datetime import date

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build_persona_dashboard as bpd  # noqa: E402  the business name, the reasons parser, the shared template

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VOC = os.path.join(ROOT, "context", "voc")
COL = ["#c96442", "#3b6ea5", "#3d7a4a", "#8a6a0c", "#7a4a8a", "#2f7f86", "#a8456b", "#5b6b2f"]
e = lambda t: html.escape(str(t if t is not None else ""))
QUOTE = re.compile(r'^\s*-\s*["“](.+)["”]\s*(.*)$')
SUMMARY = ("what almost all", "what almost none", "offers and guarantees", "the 10 headlines", "the ten headlines")
SECTION_NAMES = {"hero": "The first screen", "trust": "The numbers strip", "problem": "The problem", "get": "What you get",
                 "featured": "The featured quote", "wall": "The reviews heading", "how": "How it works",
                 "cases": "The case studies heading", "why": "Why us", "guarantee": "The guarantee", "cost": "What it costs",
                 "faq": "The questions", "faqhead": "The questions heading", "close": "The form section"}


def read(name):
    p = os.path.join(VOC, name)
    return open(p, encoding="utf-8").read() if os.path.exists(p) else ""


def clean_src(s):
    s = re.sub(r"https?://\S+", "", s or "").strip().strip("-·() ").strip()
    return re.sub(r"[,\s]+$", "", s)


def buckets(text):
    """'## 1. Bucket' > '### Theme (58 posts)' > '- "quote" - source'. A count may sit in the heading or on a Count: line."""
    out, bucket, theme = [], None, None
    for line in text.splitlines():
        m = re.match(r"^##\s+\d+[.)]\s*(.+)$", line)
        if m:
            bucket = {"title": re.sub(r"\s*\(.*\)\s*$", "", m.group(1)).strip(), "themes": []}
            out.append(bucket); theme = None
            continue
        if re.match(r"^##\s+", line):
            bucket = theme = None
            continue
        m = re.match(r"^###\s+(.+)$", line)
        if m and bucket is not None:
            title = m.group(1).strip()
            c = re.search(r"\((\d[^)]*)\)\s*$", title)
            theme = {"title": re.sub(r"\s*\([^)]*\)\s*$", "", title).strip(), "count": c.group(1) if c else "", "quotes": []}
            bucket["themes"].append(theme)
            continue
        if theme is None:
            continue
        c = re.match(r"^\s*-\s*Count:\s*(.+)$", line, re.I)
        if c and not theme["count"]:
            theme["count"] = c.group(1).strip()
            continue
        q = QUOTE.match(line)
        if q:
            theme["quotes"].append({"text": q.group(1).strip(), "source": clean_src(q.group(2))})
    return [b for b in out if any(t["quotes"] for t in b["themes"])]


def rivals(text):
    """'## Name' blocks of 'Key: value' lines, then the summary sections under '#' or '##' headings."""
    out = {"list": [], "all": [], "none": [], "offers": [], "headlines": []}
    cur, mode = None, None
    for line in text.splitlines():
        h = re.match(r"^#{1,2}\s+(.+)$", line)
        if h:
            t = h.group(1).strip(); low = t.lower()
            hit = next((k for k in SUMMARY if low.startswith(k)), None)
            if hit:
                mode = {"what almost all": "all", "what almost none": "none", "offers and guarantees": "offers"}.get(hit, "headlines")
                cur = None
            elif line.startswith("## "):
                cur = {"name": t, "fields": {}}; out["list"].append(cur); mode = None
            continue
        s = line.strip().lstrip("-").strip()
        if not s:
            continue
        if mode:
            out[mode].append(s)
        elif cur is not None:
            m = re.match(r"^([A-Za-z][A-Za-z ,'/]{1,40}):\s*(.+)$", s)
            if m:
                cur["fields"][m.group(1).strip().lower()] = m.group(2).strip()
    return out


def field(r, *keys):
    for k in keys:
        for name, v in r["fields"].items():
            if name == k or name.startswith(k):
                return v
    return ""


def how_many(text, pats, fallback=""):
    for p in pats:
        m = re.search(p, text, re.I)
        if m:
            return m.group(1)
    return fallback


# ----------------------------------------------------------------------------- the copy options

def main_line(sid, f):
    if "h1" in f: return f["h1"]
    if "stats" in f: return "  ·  ".join(f"{x.get('value', '')} {x.get('label', '')}" for x in f["stats"])
    if "quote" in f: return f"“{f['quote']}” - {f.get('name', '')}"
    if "q" in f: return f["q"]
    return f.get("heading", "")


def words(sid, f):
    """One option, drawn the way it would read on the page - never as field names."""
    out = []
    if f.get("eyebrow"): out.append(f'<p class="eyebrow">{e(f["eyebrow"])}</p>')
    if f.get("label") and "stats" not in f: out.append(f'<p class="eyebrow">{e(f["label"])}</p>')
    if "stats" in f:
        out.append('<div class="wstats">' + "".join(f'<div><b>{e(x.get("value"))}</b><span>{e(x.get("label"))}</span></div>' for x in f["stats"]) + "</div>")
    else:
        out.append(f'<p class="whead display">{e(main_line(sid, f))}</p>')
    for k in ("sub", "intro", "body", "a"):
        if f.get(k): out.append(f"<p>{e(f[k])}</p>")
    for k in ("ticks", "bullets", "checklist"):
        if f.get(k): out.append("<ul>" + "".join(f"<li>{e(x)}</li>" for x in f[k]) + "</ul>")
    for k in ("steps", "points"):
        if f.get(k): out.append("<ol>" + "".join(f"<li><b>{e(x.get('title'))}</b> {e(x.get('body') or x.get('proof') or '')}</li>" for x in f[k]) + "</ol>")
    if f.get("cta") or f.get("button"): out.append(f'<p><span class="wbtn">{e(f.get("cta") or f.get("button"))}</span></p>')
    return "".join(out)


def recount(secs):
    """Every buyer counts the same: stay and leave become head counts, and each section is ranked again."""
    for s in secs:
        for o in s["options"]:
            panel = o.get("panel") or []
            o["n"], o["stay_n"] = len(panel), sum(1 for p in panel if p["v"] == "STAY")
            o["leave_n"] = sum(1 for p in panel if p["v"] == "LEAVE")
        live = sorted([o for o in s["options"] if o["verdict"] != "CUT"],
                      key=lambda o: (-(o["stay_n"] - o["leave_n"]), -o["stay_n"], o["leave_n"], o["id"]))
        s["live"], s["cut"] = live, [o for o in s["options"] if o["verdict"] == "CUT"]
        s["winners"] = live[:6] if s["section"] == "faq" else live[:1]
    return secs


def outcome(o):
    if o["verdict"] == "CUT":
        why = (o.get("why_cut") or [""])[0].replace("editor: ", "")
        return f'<span class="st leave">Cut</span> <span class="k">{e(why.split(":")[0])}</span>'
    return f'<span class="st ok">{o["stay_n"]} of {o["n"]} stay</span>' + (f' <span class="st nonbuyer">{o["leave_n"]} leave</span>' if o["leave_n"] else "")


def verdict_rows(o):
    rows = []
    for p in sorted(o.get("panel") or [], key=lambda p: ({"LEAVE": 0, "STAY": 1}.get(p["v"], 2), p["buyer"])):
        cls = "leave" if p["v"] == "LEAVE" else "stay"
        tag = {"LEAVE": "st leave", "STAY": "st ok"}.get(p["v"], "st nonbuyer")
        rows.append(f'<div class="vrow v3 {cls}"><span class="vwho"><b>{e(p["buyer"])}</b></span>'
                    f'<span class="{tag}">{e(p["v"].lower())}</span><span class="el">{e(p["why"])}</span></div>')
    return "".join(rows)


# ----------------------------------------------------------------------------- the page

def tabs(group, labels, panels, nav=True):
    b = "".join(f'<button class="btab" style="--pc:{COL[i % len(COL)]}"><span class="dot"></span><b>{e(l)}</b></button>' for i, l in enumerate(labels))
    arrows = '<span class="bnav"><button data-step="-1" aria-label="Previous">&lsaquo;</button><button data-step="1" aria-label="Next">&rsaquo;</button></span>' if nav else ""
    return f'<div data-tabs="{group}"><div class="btabs">{b}{arrows}</div>{"".join(panels)}</div>'


def panel(i, kicker, title, label, body, score=""):
    return (f'<div class="card bp" data-panel style="--pc:{COL[i % len(COL)]}"><div class="top"><div>'
            f'<div class="kicker" style="color:var(--pc)">{e(kicker)}</div><h3 class="display">{e(title)}</h3>'
            f'{f"<div class=lbl>{e(label)}</div>" if label else ""}</div>{score}</div>{body}</div>')


def says_section(source, bs, n0):
    panels, labels = [], []
    for i, b in enumerate(bs):
        themes = [t for t in b["themes"] if t["quotes"]]
        top = themes[0]
        body = [f'<blockquote class="say">&ldquo;{e(top["quotes"][0]["text"])}&rdquo;<span class="src">{e(top["quotes"][0]["source"])}</span></blockquote>',
                '<div class="themes">']
        for t in themes[:5]:
            q = t["quotes"][1] if t is top and len(t["quotes"]) > 1 else t["quotes"][0]
            c = re.match(r"\s*(\d+(?:\s+of\s+\d+)?)", t["count"] or "")
            count = (c.group(1) if " of " in c.group(1) else c.group(1) + " mentions") if c else ""
            body.append(f'<div class="trow"><span class="tcount">{e(count)}</span><div><b class="display">{e(t["title"])}</b>'
                        f'<p>&ldquo;{e(q["text"])}&rdquo;</p><span class="src">{e(q["source"])}</span></div></div>')
        body.append("</div>")
        more = [(t, q) for t in themes for q in t["quotes"][1:4]]
        if more:
            body.append('<details class="fold"><summary>More of what they said</summary><div class="in"><ul class="qlist">'
                        + "".join(f'<li>&ldquo;{e(q["text"])}&rdquo; <span class="k">{e(t["title"])} · {e(q["source"])}</span></li>' for t, q in more[:14])
                        + "</ul></div></details>")
        labels.append(b["title"].split(",")[0].split("(")[0].strip()[:34])
        panels.append(panel(i, f"{source} · {i + 1} of {len(bs)}", b["title"], f"{len(themes)} themes, most repeated first", "".join(body)))
    return tabs(f"says-{n0}", labels, panels)


def rivals_section(R):
    out = []
    if R["none"] or R["all"]:
        out.append('<div class="two">'
                   + (f'<div class="card pad good"><div class="kicker">What none of them say · your opening</div><ul>{"".join(f"<li>{e(x)}</li>" for x in R["none"][:8])}</ul></div>' if R["none"] else "")
                   + (f'<div class="card pad"><div class="kicker">What all of them say · table stakes</div><ul>{"".join(f"<li>{e(x)}</li>" for x in R["all"][:8])}</ul></div>' if R["all"] else "")
                   + "</div>")
    panels, labels = [], []
    for i, r in enumerate(R["list"]):
        name = re.split(r"\s[·(-]\s?|\s\(", r["name"])[0].strip()
        head = field(r, "headline").strip('"“”')
        under = field(r, "under it", "line under it").strip('"“”')
        cells = [("Offer", "q", field(r, "offer")), ("Guarantee", "y", field(r, "guarantee")), ("Price", "n", field(r, "price"))]
        body = [f'<blockquote class="say">&ldquo;{e(head)}&rdquo;{f"<span class=src>{e(under)}</span>" if under else ""}</blockquote>' if head else "",
                '<div class="three">' + "".join(f'<div><span class="ml {c}">{k}</span><p>{e(v) or "<span class=k>not on the page</span>"}</p></div>' for k, c, v in cells) + "</div>"]
        rest = [(k, v) for k, v in r["fields"].items() if not k.startswith(("headline", "under it", "line under it", "offer", "guarantee", "price"))]
        if rest:
            body.append('<details class="fold"><summary>Proof, fears answered and why it was picked</summary><div class="in"><dl class="facts">'
                        + "".join(f"<dt>{e(k.capitalize())}</dt><dd>{e(v)}</dd>" for k, v in rest) + "</dl></div></details>")
        labels.append(name[:28])
        panels.append(panel(i, f"{i + 1} of {len(R['list'])}", name, r["name"][len(name):].strip(" ·-()"), "".join(body)))
    if panels:
        out.append(tabs("rivals", labels, panels))
    return "".join(out)


def copy_section(secs):
    panels, labels = [], []
    for i, s in enumerate(secs):
        sid = s["section"]; name = SECTION_NAMES.get(sid, sid.capitalize())
        win = s["winners"]
        if not win:
            continue
        body = []
        for o in win:
            qs = list(dict.fromkeys(o.get("ask") or []))
            ask = (f'<details class="asks"><summary>Needs your yes on {len(qs)} thing{"s" if len(qs) != 1 else ""} before this line goes live</summary>'
                   f'<ul>{"".join(f"<li>{e(a)}</li>" for a in qs)}</ul></details>') if qs else ""
            body.append(f'<div class="winner">{words(sid, o["fields"])}<div class="wout">{outcome(o)}</div>{ask}</div>')
        if len(win) == 1:
            body.append(f'<div class="vrows">{verdict_rows(win[0])}</div>')
        rest = [o for o in s["live"] if o not in win] + s["cut"]
        if rest:
            rows = []
            for o in rest:
                reads_html = f'<div class="vrows">{verdict_rows(o)}</div>' if o.get("panel") else ""
                cut_why = (o.get("why_cut") or [""])[0].replace("editor: ", "")
                cut_html = f'<p class="askq">Cut: {e(cut_why)}</p>' if o["verdict"] == "CUT" and cut_why else ""
                rows.append(f'<details class="orow"><summary><span class="line">{e(main_line(sid, o["fields"]))}</span>'
                            f'<span class="oout">{outcome(o)}</span></summary>'
                            f'<div class="obody">{words(sid, o["fields"])}{cut_html}{reads_html}</div></details>')
            rows = "".join(rows)
            body.append(f'<details class="fold"><summary>The other {len(rest)} options</summary><div class="in">{rows}</div></details>')
        w = win[0]
        score = f'<div class="score"><span class="v">{w["stay_n"]} of {w["n"]}</span><span class="u">buyers stay</span></div>' if len(win) == 1 else ""
        label = f'{len(s["options"])} written · {len(s["cut"])} cut · {len(s["live"])} judged by the buyers' + (" · the six they needed most" if sid == "faq" else "")
        labels.append(name.replace("The ", "").capitalize()[:24])
        panels.append(panel(0, f"{i + 1} of {len(secs)}", name, label, "".join(body), score))
    return tabs("copy", labels, panels)


EXTRA_CSS = """
  [data-panel][hidden] { display:none; }
  .card.pad { padding:24px 28px; } .card.pad ul { margin:12px 0 0; padding-left:18px; font-size:14.5px; line-height:1.6; color:var(--body); }
  .card.pad li { margin:6px 0; } .card.good { background:var(--good-bg); border-color:var(--good-ring); } .card.good li { color:var(--ink); }
  .two { display:grid; grid-template-columns:1fr 1fr; gap:16px; margin-bottom:18px; }
  .themes { margin-top:22px; border-top:1px solid var(--hairline); }
  .trow { display:grid; grid-template-columns:150px 1fr; gap:18px; padding:16px 28px; border-bottom:1px solid var(--hairline); align-items:start; }
  .trow:last-child { border-bottom:0; } .trow b { font-size:18px; letter-spacing:-.3px; display:block; } .trow p { font-size:14.5px; line-height:1.5; color:var(--body); margin-top:5px; }
  .trow .src, .qlist .k { font-family:"JetBrains Mono",ui-monospace,monospace; font-size:10.5px; color:var(--muted); }
  .tcount { font-family:"JetBrains Mono",ui-monospace,monospace; font-size:11px; text-transform:uppercase; letter-spacing:1px; color:var(--pc); padding-top:4px; }
  .qlist { padding-left:18px; font-size:14px; line-height:1.6; color:var(--body); } .qlist li { margin:6px 0; }
  dl.facts dt { font-family:"JetBrains Mono",ui-monospace,monospace; font-size:10px; text-transform:uppercase; letter-spacing:1.2px; color:#6e6d66; margin-top:12px; }
  dl.facts dd { font-size:14px; line-height:1.5; color:var(--ink); margin-top:3px; }
  .winner { margin:20px 28px 0; padding:24px 26px; border-radius:16px; background:#fff; border:1px solid var(--hairline); }
  .winner + .winner { margin-top:12px; }
  .eyebrow { font-size:13px; color:var(--muted); margin-bottom:8px; }
  .whead { font-size:30px; line-height:1.15; letter-spacing:-.7px; margin-bottom:12px; }
  .winner p, .obody p { font-size:15px; line-height:1.6; color:var(--body); margin-bottom:10px; }
  .winner p.whead { color:var(--ink); font-size:32px; line-height:1.15; letter-spacing:-.8px; margin-bottom:14px; }
  .obody p.whead { color:var(--ink); font-size:21px; line-height:1.25; letter-spacing:-.4px; }
  details.asks { margin-top:12px; font-size:13.5px; color:#8a6a0c; } details.asks summary { cursor:pointer; font-weight:600; }
  details.asks ul { margin:8px 0 0; padding-left:18px; line-height:1.55; } details.asks li { margin:4px 0; }
  details.askbox summary { cursor:pointer; list-style:none; } details.askbox summary::-webkit-details-marker { display:none; }
  details.askbox ul { margin:10px 0 0; padding-left:18px; line-height:1.6; } details.askbox li { margin:5px 0; }
  .winner ul, .winner ol, .obody ul, .obody ol { padding-left:20px; font-size:15px; line-height:1.6; color:var(--body); margin-bottom:10px; }
  .wbtn { display:inline-block; padding:8px 14px; border-radius:10px; background:var(--terracotta); color:#faf9f5; font-size:13.5px; font-weight:500; }
  .wstats { display:grid; grid-template-columns:repeat(auto-fit,minmax(150px,1fr)); gap:14px; }
  .wstats b { display:block; font-family:"Tiempos Text",Georgia,serif; font-weight:500; font-size:30px; letter-spacing:-.8px; } .wstats span { font-size:13px; color:var(--body); }
  .wout { display:flex; gap:8px; align-items:center; flex-wrap:wrap; margin-top:14px; }
  .askq { font-size:13px; color:#8a6a0c; margin-top:10px; }
  .vrows { margin-top:20px; } .vrow.v3 { grid-template-columns:120px 76px 1fr; } .vrow.v3 .el { color:var(--body); }
  .orow { border-top:1px solid var(--hairline); } .orow:first-child { border-top:0; }
  .orow summary { list-style:none; cursor:pointer; display:flex; justify-content:space-between; gap:16px; align-items:center; padding:13px 0; font-size:15px; }
  .orow summary::-webkit-details-marker { display:none; } .orow .line { flex:1; min-width:0; overflow-wrap:anywhere; } .orow .oout { flex-shrink:0; display:flex; gap:6px; align-items:center; }
  .obody { padding:4px 0 18px; }
  .stats.four { grid-template-columns:repeat(4,1fr); } .askbox { margin:0 30px 22px; }
  @media (max-width:960px) { .two { grid-template-columns:1fr; } .stats.four { grid-template-columns:1fr 1fr; } .trow { grid-template-columns:1fr; gap:4px; padding:14px 20px; }
    .winner { margin:16px 16px 0; padding:18px; } .whead { font-size:24px; } .vrow.v3 { grid-template-columns:1fr 76px; } .vrow.v3 .el { grid-column:1 / -1; }
    .orow summary { flex-direction:column; align-items:flex-start; gap:6px; } }
"""

JS = """
document.querySelectorAll('[data-tabs]').forEach(function(g){
  var t = g.querySelectorAll('.btab'), p = g.querySelectorAll(':scope > [data-panel]'), cur = 0;
  function show(i){ cur = (i + t.length) % t.length; t.forEach(function(b,k){ b.classList.toggle('on', k===cur); }); p.forEach(function(x,k){ x.hidden = k!==cur; }); }
  t.forEach(function(b,k){ b.addEventListener('click', function(){ show(k); }); });
  g.querySelectorAll('[data-step]').forEach(function(b){ b.addEventListener('click', function(){ show(cur + (+b.dataset.step)); }); });
  g._step = function(d){ show(cur + d); }; show(0);
});
document.addEventListener('keydown', function(ev){
  if (ev.key !== 'ArrowLeft' && ev.key !== 'ArrowRight') return;
  var mid = innerHeight / 2, best = null, d = 1e9;
  document.querySelectorAll('[data-tabs]').forEach(function(g){ var r = g.getBoundingClientRect(), x = Math.abs((r.top + r.bottom) / 2 - mid); if (r.bottom > 0 && r.top < innerHeight && x < d) { d = x; best = g; } });
  if (best) best._step(ev.key === 'ArrowRight' ? 1 : -1);
});
"""


def build(out, business=None):
    tpl = open(bpd.TEMPLATE, encoding="utf-8").read()
    css = re.search(r"<style>(.*?)</style>", tpl, re.S).group(1)
    name = bpd.business_name(business)
    reddit_txt, reviews_txt, rivals_txt = read("reddit.md"), read("reviews.md"), read("rivals.md")
    reddit, reviews, R = buckets(reddit_txt), buckets(reviews_txt), rivals(rivals_txt)
    reasons = bpd.load_reasons(os.path.join(ROOT, "context", "personas"))
    jp = os.path.join(VOC, "options-judged.json")
    secs = recount(json.load(open(jp, encoding="utf-8"))) if os.path.exists(jp) else []
    n_reddit = how_many(reddit_txt, [r"\((\d+) items\)", r"(\d+) posts and comments", r"(\d+) items"], str(sum(len(t["quotes"]) for b in reddit for t in b["themes"])))
    n_reviews = how_many(reviews_txt, [r"Reviews read:\s*(\d+)", r"(\d+)\s+(?:Google Maps |Trustpilot )?reviews"], str(sum(len(t["quotes"]) for b in reviews for t in b["themes"])))
    n_opts, n_cut = sum(len(s["options"]) for s in secs), sum(len(s["cut"]) for s in secs)
    stats = [(n_reddit, "Reddit posts and comments", "owners describing the problem in their own words") if reddit else None,
             (n_reviews, "Competitor reviews", "what buyers praised, and what let them down") if reviews else None,
             (str(len(R["list"])), "Competitors", "picked by how long their ads have run, then size") if R["list"] else None,
             (str(n_opts), "Copy options", f"{n_cut} cut as vague, {n_opts - n_cut} judged by the buyers") if secs else None]
    stats = [s for s in stats if s]
    asks = list(dict.fromkeys(a for s in secs for o in s["winners"] for a in (o.get("ask") or [])))
    if asks and any("retainer" in a.lower() for a in asks):
        asks = [a for a in asks if "retainer" not in a.lower()] + ["If a client stops the retainer, do the site, the CRM and the automations keep running in their name?"]
    H, jump, n = [], [], 0
    top = ['<div class="card">']
    if reasons:
        cards = []
        for i, r in enumerate(reasons):
            chip = (f'<span class="st ok">{e(r["buyers"])}</span>' if r.get("buyers") else "") + \
                   (f'<span class="mchip" style="--pc:var(--terracotta)">{e(r["moves"])}</span>' if r.get("moves") else "")
            quote = f'<blockquote class="say">&ldquo;{e(r["quotes"][0]["text"])}&rdquo;</blockquote>' if r.get("quotes") else ""
            cards.append(f'<div class="reason"><div class="rn">{i + 1}</div><div class="rb"><h3 class="display">{e(r["title"])}</h3>'
                         f'<div class="rmeta">{chip}</div>{quote}</div></div>')
        top.append('<div class="who"><div class="kicker">Why people buy · the three reasons every page writes to</div>'
                   f'<div class="reasons">{"".join(cards)}</div></div>')
    if asks:
        top.append(f'<details class="whybox askbox"><summary><b>{len(asks)} promises in the winning lines need your yes before they go live</b> · open the list</summary>'
                   f'<ul>{"".join(f"<li>{e(a)}</li>" for a in asks)}</ul></details>')
    top.append(f'<div class="stats{" four" if len(stats) == 4 else ""}">' + "".join(f'<div class="stat"><div class="v">{e(v)}</div><div class="k">{e(k)}</div><div class="sub">{e(s)}</div></div>' for v, k, s in stats) + "</div></div>")
    H.append(f'<section id="top"><div class="rail">{"".join(top)}</div></section>')

    def sec(sid, title, lead, body, band):
        nonlocal n
        n += 1
        jump.append((sid, title))
        H.append(f'<section id="{sid}"{" class=band" if band else ""}><div class="rail"><div class="sh"><span class="kicker">Section {n}</span>'
                 f'<h2 class="display">{e(title)}</h2>{f"<p class=lead>{e(lead)}</p>" if lead else ""}</div>{body}</div></section>')
    if reddit:
        sec("reddit", "What buyers say", "Their own words, before they ever buy. Most repeated first.", says_section("Reddit", reddit, 1), True)
    if reviews:
        sec("reviews", "What buyers say about competitors", "Reviews come from people who bought: the result they wanted, and what let them down.", says_section("Reviews", reviews, 2), False)
    if R["list"]:
        sec("rivals", "The competitors", "The best-run rivals, not the nearest ones. What nobody says is where your page can stand alone.", rivals_section(R), True)
    if secs:
        sec("copy", "The copy, section by section", "Ten options for each section. The vague ones were cut, then every buyer read the rest. Arrow keys move between sections.", copy_section(secs), False)
    spark = '<svg viewBox="0 0 24 24" width="19" height="19" fill="currentColor" aria-hidden="true"><path d="M12 2 L13.4 10.6 L22 12 L13.4 13.4 L12 22 L10.6 13.4 L2 12 L10.6 10.6 Z"/></svg>'
    stamp = " · ".join(x for x in [date.today().strftime("%-d %B %Y"), f"{n_reddit} posts and comments" if reddit else "", f"{n_reviews} reviews" if reviews else "",
                                   f"{len(R['list'])} competitors" if R["list"] else "", f"{n_opts} copy options" if secs else ""] if x)
    page = f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{e(name)} - research and copy</title><style>{css}{EXTRA_CSS}</style></head><body>
<div class="nav"><div class="rail"><span class="wordmark display">{spark}{e(name)}</span>
<nav class="jump">{"".join(f'<a href="#{i}">{e(t)}</a>' for i, t in jump)}</nav><span class="chip">Research · simulation</span></div></div>
<main><header class="hero"><div class="rail"><div class="kicker">What buyers want · and the words that answer it</div>
<h1 class="display">{e(name)}</h1><div class="meta"><span class="stamp">{e(stamp)}</span></div></div></header>
{"".join(H)}</main>
<footer><div class="rail"><span class="wordmark display">{spark}{e(name)}</span><span>Buyers read by a model catch confusion and broken promises. Real visitors decide, in the split test.</span></div></footer>
<script>{JS}</script></body></html>"""
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    open(out, "w", encoding="utf-8").write(page)
    print(f"Research dashboard: {os.path.abspath(out)}")
    print(f"- {len(reddit)} Reddit buckets · {len(reviews)} review buckets · {len(R['list'])} competitors · {len(secs)} copy sections")
    for missing, what in [(not reddit_txt, "reddit.md"), (not reviews_txt, "reviews.md"), (not rivals_txt, "rivals.md"), (not reasons, "reasons.md")]:
        if missing:
            print(f"- Not on the page: context/voc/{what} is missing - /personas step 1c writes it.")
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", default=os.path.join(VOC, "research.html"))
    ap.add_argument("--business", default=None)
    a = ap.parse_args()
    build(a.out, a.business)
