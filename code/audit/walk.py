"""The report's spine: the page cut into bands, top to bottom, one card per band.

Why (Jono, 27 September 2026, after three bad rounds): the old audit was 41 separate rules
each hunting for a spot to draw a box. When a rule found nothing it guessed, which is how
"The offer" was drawn on a B2B site's navigation bar. The code was being asked for
MEANING - is this the founder video, is this a gallery - which it cannot read reliably on
the infinite ways pages get built.

So the work is split. The code MEASURES: where each band starts and ends, and what sits
inside it (buttons, phone links, forms, videos and their transcripts, reviews, questions
and their answers, the words). Claude READS each band from its own screenshot: what it is,
which of the 21 components it holds, and whether to keep it, fix it or cut it. The code's
guesses go on the judging sheet as suggestions and nothing more.

Guarantees, checked by `check()`:
  - the bands tile the page: no gaps, no overlaps, top of the page to the bottom
  - every band gets one card, and every card one box
  - each of the 21 components is spoken about exactly once
  - nothing is boxed from a guess: a box is a band, or the headline or subheadline
"""

import os
import re

from .eighteen import EIGHTEEN, GROUP_OF, HOME, PAGE, STATUS_WORD, WEIGHT, WHERE_TO_ADD
from .plain import MAX_GRADE, chain_mix, grade as read_grade, hard_lines, section_grade, too_long
from .sections import TYPES, checklist, classify

SPLIT_SCREENS = 2.5   # a band taller than this is split at the sections inside it
MIN_BAND = 70         # anything thinner joins the band above it
GAP_BAND = 160        # uncovered page taller than this becomes its own band

# Headings that name a section a landing page does not need. A SUGGESTION to cut, which
# Claude confirms from the screenshot; never a verdict on its own.
NOT_ON_BLUEPRINT = re.compile(
    r"\b(?:about us|our story|who we are|our team|meet the team|news|insights|blog|careers|"
    r"jobs|our model|our mission|our values|offices|locations|resources|partners|investors|"
    r"press|media|latest posts)\b", re.I)

NAMES = {n: name for n, name, _, _ in EIGHTEEN}
NAMES[2] = "The proof in the first screen"      # never "above the fold" in front of the owner
VERDICTS = ("keep", "fix", "cut")
# "unchecked": the audit could not see it from outside (a thank-you page behind the form). It is
# listed as not checked and left out of the count - never silently dropped, never called missing.
STATUSES = ("ok", "weak", "missing", "n/a", "unchecked")
FOOTER_TEXT = re.compile(r"©|\bcopyright\b|all rights reserved|privacy policy|terms of (?:use|service)", re.I)


# --------------------------------------------------------------------------- bands

def _iv(x, src):
    top = int(x.get("top") or 0)
    return {"top": top, "bot": top + int(x.get("h") or 0),
            "heading": (x.get("heading") or "").strip(), "src": src}


def _contains(outer, inner, slack=8):
    return inner["top"] >= outer["top"] - slack and inner["bot"] <= outer["bot"] + slack


def _outermost(cands, floor=None):
    """Greedy, top to bottom: keep a candidate unless one already kept holds it."""
    kept = []
    for c in sorted(cands, key=lambda c: (c["top"], -(c["bot"] - c["top"]))):
        if any(_contains(k, c) for k in kept):
            continue
        c = dict(c)
        if kept and c["top"] < kept[-1]["bot"]:
            c["top"] = kept[-1]["bot"]          # a partial overlap is clipped, never doubled
        if c["bot"] - c["top"] < 60:
            continue
        kept.append(c)
    return kept


def _split(chosen, cands, vh):
    """A band taller than SPLIT_SCREENS is really several sections. Cut it at the ones inside."""
    for _ in range(4):
        out, changed = [], False
        for k in chosen:
            h = k["bot"] - k["top"]
            if h <= SPLIT_SCREENS * vh:
                out.append(k)
                continue
            kids = [c for c in cands if _contains(k, c) and (c["bot"] - c["top"]) < h - 40
                    and (c["bot"] - c["top"]) >= 120]
            sel = _outermost(kids)
            if len(sel) < 2:
                out.append(k)
                continue
            if sel[0]["top"] - k["top"] >= 150:
                out.append({"top": k["top"], "bot": sel[0]["top"], "heading": k["heading"], "src": "head"})
            else:
                sel[0]["top"] = k["top"]
                sel[0]["heading"] = sel[0]["heading"] or k["heading"]
            out.extend(sel)
            if k["bot"] - sel[-1]["bot"] >= 150:
                out.append({"top": sel[-1]["bot"], "bot": k["bot"], "heading": "", "src": "tail"})
            else:
                out[-1]["bot"] = k["bot"]
            changed = True
        chosen = sorted(out, key=lambda c: c["top"])
        if not changed:
            break
    return chosen


def _once(lines):
    """Each line of four or more words once. A review wall that loops prints every card twice, and a
    banner is often in the page twice; the visitor reads it once (one audited site, 2 Oct 2026)."""
    seen, out = set(), []
    for t in lines:
        k = " ".join((t or "").split()).lower()
        if len(k.split()) >= 4 and k in seen:
            continue
        seen.add(k)
        out.append(t)
    return out


_SLOT_NOTE = re.compile(r"^Until it is filled, visitors see", re.I)
_SLOT_TAG = re.compile(r"^(?:Placeholder ·|IDEAL · NEEDS PROOF|Needs: )", re.I)


def _without_slot_labels(lines):
    """A draft on the dev server draws every empty slot as a frame with a label, a hint and "Until it is
    filled, visitors see...". Visitors never read those words, so they are not counted (2 Oct 2026)."""
    out = list(lines)
    for i, t in enumerate(lines):
        if _SLOT_NOTE.match((t or "").strip()):
            for j in (i - 2, i - 1, i):
                if j >= 0:
                    out[j] = None
        elif _SLOT_TAG.match((t or "").strip()):
            out[i] = None
    return [t for t in out if t is not None]


def _heading_for(band, facts):
    """The band's own title: the biggest heading in its top half, else the first one in it."""
    hs = [h for h in (facts.get("headingsAt") or [])
          if h.get("top") is not None and band["top"] <= h["top"] < band["bot"]]
    # a reviewer's name inside a review card is not the section's title (one audited site: the wall
    # of reviews was titled "Julian Bradley")
    quotes = [q for q in (facts.get("quoteBlocks") or []) if q.get("top") is not None]
    own = [h for h in hs if not any(q["top"] - 4 <= h["top"] <= q["top"] + (q.get("h") or 0) + 4
                                    and (q.get("left") or 0) - 4 <= (h.get("left") or 0) <= (q.get("left") or 0) + (q.get("w") or 0) + 4
                                    for q in quotes)]
    if hs and not own:
        return ""
    hs = own
    if not hs:
        fb = band.get("heading") or ""
        if fb and any(fb in (q.get("text") or "") for q in quotes if band["top"] <= q["top"] < band["bot"]):
            return ""
        return fb
    top_half = [h for h in hs if h["top"] < band["top"] + max(260, (band["bot"] - band["top"]) * 0.5)]
    pool = top_half or hs
    # A title is words, not a stat: on mobiloud.com the biggest text in a section was "Instant" or
    # "↑10x", and the section got named after it. Heading tags are no guide either - a B2B site puts
    # them on its small eyebrow lines. So: the biggest line of two or more words.
    worded = [h for h in pool if re.search(r"[A-Za-z]{3,}", h["text"]) and len(h["text"].split()) >= 2]
    pool = worded or pool
    big = max(h.get("size") or 0 for h in pool)
    # a two-tone heading is several pieces the same size: the whole line wins over its coloured half
    same = [h for h in (hs if worded else pool) if (h.get("size") or 0) >= big - 3
            and h["top"] < band["top"] + max(260, (band["bot"] - band["top"]) * 0.5)]
    best = max(same or pool, key=lambda h: (len(h["text"]), -h["top"]))
    return best["text"].strip()


def build_bands(facts):
    """The page cut into contiguous bands. Every pixel of the page is in exactly one band."""
    vh = (facts.get("viewport") or {}).get("h") or 800
    page_h = int(facts.get("scrollHeight") or 0)
    cands = [_iv(s, "section") for s in (facts.get("sections") or []) if (s.get("h") or 0) >= 60]
    cands += [_iv(c, "block") for c in (facts.get("bandCandidates") or [])]
    if not page_h:
        page_h = max((c["bot"] for c in cands), default=0)
    for c in cands:
        c["top"], c["bot"] = max(0, c["top"]), min(page_h, c["bot"])
    cands = [c for c in cands if c["bot"] - c["top"] >= 60]

    chosen = _split(_outermost(cands), cands, vh)

    # fill what no candidate covered, so nothing on the page goes unspoken
    bands, cursor = [], 0
    for c in chosen:
        c = dict(c)
        if c["top"] - cursor >= GAP_BAND:
            bands.append({"top": cursor, "bot": c["top"], "heading": "", "src": "gap"})
        elif bands:
            bands[-1]["bot"] = c["top"]
        else:
            c["top"] = 0
        bands.append(c)
        cursor = c["bot"]
    if page_h - cursor >= GAP_BAND or not bands:
        bands.append({"top": cursor, "bot": page_h, "heading": "", "src": "gap"})
    else:
        bands[-1]["bot"] = page_h

    # the bar at the top is its own band when the page has one
    bar = facts.get("topBar") or {}
    if bar.get("top") is not None and bar["top"] < 8 and 24 <= (bar.get("h") or 0) <= vh * 0.3 and bands:
        bh = bar["top"] + bar["h"]
        first = bands[0]
        if abs((first["bot"] - first["top"]) - bh) <= 30:
            first["src"] = "nav"
        elif first["bot"] - bh >= 100:
            bands.insert(0, {"top": 0, "bot": bh, "heading": "", "src": "nav"})
            bands[1]["top"] = bh

    # the footer is one band, from where it starts to the end of the page
    foot = facts.get("footerBox") or {}
    if foot.get("top") is not None and page_h and (foot.get("h") or 0) <= page_h * 0.5 \
            and foot["top"] >= page_h * 0.5:
        ft = foot["top"]
        keep = []
        for b in bands:
            if b["bot"] <= ft + 20:
                keep.append(b)
            elif b["top"] < ft - 150:
                keep.append({**b, "bot": ft})
            else:
                ft = min(ft, b["top"])
        if keep:
            keep[-1]["bot"] = ft
        keep.append({"top": ft, "bot": page_h, "heading": "", "src": "footer"})
        bands = keep

    # slivers join the band above
    tidy = []
    for b in bands:
        if tidy and b["bot"] - b["top"] < MIN_BAND and b["src"] != "nav":
            tidy[-1]["bot"] = b["bot"]
            continue
        tidy.append(b)
    # No footer element found: the last band that carries the copyright or privacy line is the
    # footer. a photography site's footer typed as a selling section without this.
    if tidy and not any(b["src"] == "footer" for b in tidy):
        last = tidy[-1]
        words = " ".join(t["text"] for t in (facts.get("textAt") or [])
                         if t.get("top") is not None and last["top"] <= t["top"] < last["bot"])
        if FOOTER_TEXT.search(words) and (last["bot"] - last["top"]) <= vh * 1.2:
            last["src"] = "footer"

    for i, b in enumerate(tidy):
        b["n"] = i + 1
        b["id"] = f"b{i + 1:02d}"
        b["h"] = b["bot"] - b["top"]
        b["heading"] = "" if b["src"] in ("nav", "footer") else _heading_for(b, facts)
    return tidy


# --------------------------------------------------------------------------- evidence

def _in(x, b):
    t = x.get("top")
    return t is not None and b["top"] <= t < b["bot"]


def _vid_kinds(assets):
    from .copy_check import classify_video
    out = []
    for v in ((assets or {}).get("videos") or {}).get("items", []):
        kind, why = classify_video(v.get("transcript"))
        w = v.get("watched") or {}
        if kind in ("unknown", "explainer") and w.get("who") and not w.get("error"):
            kind, why = w["who"], f'watched: {w.get("who_because", "")}'
        out.append({"top": v.get("top"), "kind": kind, "why": why, "provider": v.get("kind"),
                    "words": v.get("transcript_words") or 0,
                    "transcript": (v.get("transcript") or "")[:1400],
                    "watched": ({k: w.get(k) for k in ("seconds", "length_says", "smiles", "expression", "eye_contact",
                                                       "broll_share", "cuts", "captions", "opens_with", "says", "moments")}
                                if w and not w.get("error") else ({"not_watched": w.get("error", "")[:120]} if w else {})),
                    "frames": v.get("frames") or ""})
    return out


def _goes(href, page_url=""):
    h = (href or "").strip()
    if not h or h.startswith("#") or h.lower().startswith("javascript"):
        return "this page"
    if h.lower().startswith("mailto:"):
        return "opens an email app"
    if h.lower().startswith(("tel:", "sms:")):
        return "calls or texts"
    from urllib.parse import urlparse
    u, p = urlparse(h), urlparse(page_url or "")
    if u.netloc and p.netloc and u.netloc.replace("www.", "") != p.netloc.replace("www.", ""):
        return "another site"
    if (u.path or "/").rstrip("/") == (p.path or "/").rstrip("/") and not u.query:
        return "this page"
    return "another page"


def evidence(b, facts, assets, pins=None, vkinds=None, page_url=""):
    """What the code can MEASURE inside one band. Suggestions for Claude, never verdicts."""
    text = _once([t["text"] for t in (facts.get("textAt") or []) if _in(t, b)])
    words = sum(len(t.split()) for t in text)
    ctas = [c for c in (facts.get("ctas") or []) if _in(c, b) and not c.get("fixed")]
    tel = [t for t in (facts.get("tel") or []) if _in(t, b) and t.get("visible", True)]
    forms = [f for f in (facts.get("forms") or []) if _in(f, b)]
    vids = [v for v in (vkinds or []) if _in(v, b)]
    frames = [f for f in (facts.get("iframes") or []) + (facts.get("videos") or []) + (facts.get("videoWidgets") or [])
              if _in(f, b) and (f.get("provider") in ("youtube", "vimeo", "wistia", "loom") or f.get("kind") == "video")]
    imgs = [i for i in (facts.get("images") or []) if _in(i, b) and (i.get("w") or 0) * (i.get("h") or 0) >= 4000]
    # a scrolling review wall prints every card twice so the row can loop: count each review once
    # (one audited site, 2 Oct 2026: 61 reviews were reported as 122)
    quotes = list({(q.get("text") or "")[:80]: q for q in (facts.get("quoteBlocks") or []) if _in(q, b)}.values())
    faq = [q for q in (facts.get("faq") or []) if _in(q, b) and (q.get("q") or "").strip().endswith("?")]
    bullets = [x["text"] for x in (facts.get("blocks") or []) if _in(x, b) and x.get("kind") == "bullet"]
    noticed = []
    for p in pins or []:
        if _in(p.get("box") or {}, b):
            noticed.append(f'{p["title"]}: {(p.get("says") or "")[:140]}')
    return {
        "heading": b.get("heading", ""),
        "words": words,
        "text": text[:60],
        "buttons": [f'{c.get("text", "")[:40]} ({_goes(c.get("href"), page_url)})' for c in ctas][:8],
        "buttons_off_the_page": [c.get("text", "")[:40] for c in ctas
                                 if _goes(c.get("href"), page_url) in ("another page", "another site", "opens an email app")][:8],
        "phone": [t.get("text", "")[:30] for t in tel][:3],
        "forms": [{"fields": len(f.get("fields") or []) if isinstance(f.get("fields"), list) else f.get("fields"),
                   "button": f.get("button", "")} for f in forms],
        "videos": [{"the_transcript_says": v["kind"], "why": v["why"], "words": v["words"],
                    "transcript": v["transcript"], "watched": v.get("watched") or {},
                    "frames": v.get("frames") or ""} for v in vids],
        "video_frames": len(frames),
        "pictures": len(imgs),
        "stock_suspects": sum(1 for i in imgs if i.get("stock_suspect")),
        "reviews": len(quotes),
        "reviews_with_a_face": sum(1 for q in quotes if q.get("hasPhoto")),
        "questions": [{"q": q.get("q", "")[:160], "a": (q.get("a") or "")[:400],
                       "answer_read": bool((q.get("a") or "").strip()),
                       "asked": question_timing(q.get("q"))} for q in faq],
        "bullets": bullets[:12],
        "code_noticed": noticed[:6],
        # how hard the words are to read: grade 10 is the ceiling, abstract words need a thing
        # the visitor can picture in their place (Jono, 28 Sep 2026)
        "reading_grade": section_grade(text),
        "hard_lines": hard_lines(text),
        "about_you": _self_talk(text, facts),
        # proof without a number is a claim: every figure in the section, so a case study or a
        # review block with none is caught (Jono, 28 Sep 2026: "not a single outcome, stat, number")
        "numbers": _numbers(text),
        # pictures that do not load: the visitor sees a name or an empty box where a face should be
        "broken_images": [(i.get("alt") or i.get("src", "").rsplit("/", 1)[-1])[:50]
                          for i in (facts.get("brokenImages") or []) if _in(i, b)],
        # every photo searched on TinEye: a face found on Unsplash is a stock photo, whatever the name beside it
        "reverse_search": [{"what": r.get("why"), "file": (r.get("src") or "").split("?")[0].rsplit("/", 1)[-1][:60],
                            "verdict": r.get("verdict") or ("not searched: " + (r.get("error") or "")),
                            "stock_sites": r.get("stock_domains") or [], "also_on": r.get("elsewhere") or []}
                           for r in (facts.get("reverseSearch") or []) if _in(r, b)][:12],
        "echoes": _echoes(b, facts),
        # faces from stand-in portrait sites: a fabricated person, whatever name sits beside it
        "stand_in_faces": sum(1 for i in (facts.get("images") or []) if _in(i, b) and STAND_IN.search(i.get("src") or "")),
        "image_facts": _image_facts(b, facts, assets),
        "aggregate_rating": _aggregate(text),
        "badges": _badges(facts, b),
    }


# a line that says its title again: "Build & integrate / We build and configure your app... every
# integration" - the box says one thing twice (Jono, 28 Sep 2026: "the subtext repeats the headline")
def _stems(t):
    return {w[:5] for w in re.findall(r"[a-z]{4,}", (t or "").lower())} - {"about", "their", "there", "these", "which", "with", "your", "yours", "from", "that", "this", "will", "have"}


def _echoes(b, facts):
    """Box titles whose line underneath says the title again. Matched by COLUMN: step boxes sit side by
    side, so the next line in reading order is the next box's title, not this box's text."""
    def is_title(t):
        x = t["text"].strip()
        n = len(x.split())
        return (2 <= n <= 8 and not x.endswith("?") and not x.startswith("©")
                and not (x.isupper() and n <= 3))
    allh = [h for h in (facts.get("headingsAt") or []) if _in(h, b)]
    lines = [t for t in (facts.get("textAt") or []) if _in(t, b) and t.get("tag") not in ("a", "button")]
    titles = [h for h in allh if is_title(h)
              and not any(h is not g and h["text"] in g["text"] and len(g["text"]) > len(h["text"]) for g in allh)]
    titles += [t for t in lines if is_title(t) and t.get("tag") in ("h2", "h3", "h4", "h5", "h6", "strong", "b", "dt")
               and not any(abs(t["top"] - h["top"]) < 6 and abs((t.get("left") or 0) - (h.get("left") or 0)) < 20 for h in titles)]
    out, seen = [], set()
    for h in titles:
        hs = _stems(h["text"])
        if len(hs) < 2 or h["text"] in seen:
            continue
        below = [t for t in lines if 0 < t["top"] - h["top"] <= 120 and abs((t.get("left") or 0) - (h.get("left") or 0)) <= 40
                 and len(t["text"].split()) >= 5 and not t["text"].startswith(h["text"][:20])]
        if not below:
            continue
        nxt = min(below, key=lambda t: t["top"])
        if len(hs & _stems(nxt["text"])) / len(hs) >= 0.5:
            seen.add(h["text"])
            out.append({"title": h["text"][:60], "line": nxt["text"][:120]})
    return out[:6]


_AGG = re.compile(r"\b[1-5](?:\.\d)?\s*(?:/\s*5|out of 5|stars?)\b[^.]{0,40}?\b\d[\d,.]*\s*[kK]?\+?\s*(?:reviews|ratings)"
                  r"|\b\d[\d,.]*\s*[kK]?\+?\s*(?:reviews|ratings)\b[^.]{0,30}?\b[1-5]\.\d", re.I)


def _aggregate(text):
    for t in text:
        m = _AGG.search(t)
        if m:
            return m.group(0)[:80]
    return ""


_BADGE = re.compile(r"capterra|\bg2\b|g2crowd|trustpilot|product.?hunt|google.?review|clutch|\bbbb\b|yelp|homestars|"
                    r"houzz|trustindex|reviews\.io|feefo|getapp|software.?advice|best.?of|award|users.?love|\bbark\b|"
                    r"facebook.{0,20}(?:review|recommend|rating)|review.?badge", re.I)


def _badges(facts, b):
    out = []
    for i in facts.get("images") or []:
        if _in(i, b):
            m = _BADGE.search(f'{i.get("alt", "")} {i.get("src", "")}')
            if m and m.group(0).lower() not in out:
                out.append(m.group(0).lower())
    return out[:6]


# "how long after the wedding will we get the photos" is asked BEFORE booking - delivery time is a
# reason to choose; after-sale means support once they are a customer
_AFTER = re.compile(r"after (?:launch|we launch|go.?live|you launch)|long.?term|keep using|"
                    r"ongoing|maintenance|once (?:it|the app) is live|renew|upgrade my plan", re.I)
_BEFORE = re.compile(r"cost|price|pricing|how much|how long|how fast|how soon|guarantee|refund|contract|cancel|work with|"
                     r"compatible|right for|different from|vs\.?|compare|what happens|own|secure|security|data|deposit|"
                     r"book|available|area|insur|licen|who will|backup|free", re.I)


def question_timing(q):
    """before | after | unclear - whether a question is asked before someone enquires. A hint; the judge decides."""
    if _AFTER.search(q or ""):
        return "after"
    if _BEFORE.search(q or ""):
        return "before"
    return "unclear"


# Stand-in portrait sites. A face from one of these is not a client, and one of them on a page is
# enough to make a visitor doubt every real review beside it (Jono, 28 Sep 2026: "risk should be 10/10").
STAND_IN = re.compile(r"randomuser\.me|pravatar|thispersondoesnotexist|uifaces|generated\.photos|placeholder\.com|picsum", re.I)

# Slots the course template ships filled with stand-ins, waiting for the real thing: portraits from
# stand-in sites, topical photos fetched into public/photos/, the template's own placeholder brand names,
# and [bracket] copy. On a DRAFT these are slots to fill, scored as if filled; on a live page a visitor
# cannot tell them from the real thing, so they are fabrications (Jono, 28 Sep 2026).
LOCAL_STOCK = re.compile(r"/photos/[a-z0-9-]+\.(?:jpe?g|png|webp)(?:\?|$)", re.I)
TEMPLATE_NAMES = ("Northline", "Harbour & Co", "Vantage", "Ridgeway", "Copperfield", "Meridian")
BRACKET = re.compile(r"\[[A-Za-z][^\]\n]{2,80}\]")


def placeholders_in(b, facts):
    """Every stand-in slot in one band, in plain words."""
    imgs = [i for i in (facts.get("images") or []) if _in(i, b)]
    faces = sum(1 for i in imgs if STAND_IN.search(i.get("src") or ""))
    photos = sum(1 for i in imgs if LOCAL_STOCK.search(i.get("src") or ""))
    text = " ".join(t["text"] for t in (facts.get("textAt") or []) if _in(t, b))
    out = []
    if faces:
        out.append(f"{faces} stand-in face{'s' if faces != 1 else ''} - replace with the real person's photo or video")
    if photos:
        out.append(f"{photos} stand-in photo{'s' if photos != 1 else ''} - replace with your own")
    names = [n for n in TEMPLATE_NAMES if n in text]
    if len(names) >= 3:
        out.append(f"{len(names)} placeholder brand names ({', '.join(names[:3])}...) - replace with real client logos")
    for m in sorted(set(BRACKET.findall(text)))[:6]:
        out.append(f"{m} - waiting for your words")
    return out

_NUM = re.compile(r"(?:\$\s?\d[\d,.]*\s?[kKmM]?|\d[\d,.]*\s?(?:%|x\b|\+|k\b|m\b|weeks?|days?|months?|hours?|"
                  r"minutes?|years?|units|leads|calls|clients|customers|events|reviews|stars?)|\b\d{2,}[\d,]*\b)", re.I)


def _numbers(text):
    seen = []
    for t in text:
        for m in _NUM.findall(t):
            m = m.strip()
            if m and m not in seen and not re.fullmatch(r"(?:19|20)\d\d", m):
                seen.append(m)
    return seen[:12]


def _self_talk(text, facts):
    """(lines about the business, lines about the visitor). Two long sections that both talk
    about the business are the repeat Jono spotted on a B2B site (28 Sep 2026)."""
    brand = set()
    for w in re.findall(r"[a-z]{4,}", (facts.get("title") or "").lower())[:3]:
        brand.add(w)
    me = you = 0
    for t in text:
        low = t.lower()
        words = set(re.findall(r"[a-z']+", low))
        if words & {"we", "our", "us", "we're", "we've", "ours"} or any(b in low for b in brand if len(b) > 4):
            me += 1
        if words & {"you", "your", "you're", "yours"}:
            you += 1
    return {"about_the_business": me, "about_the_visitor": you}


def _image_facts(b, facts, assets):
    """Each picture in the band, with what the code knows about it, so the judge grades the images and
    not just their presence (Jono, 28 Sep 2026: "are they actually good images?")."""
    by_src = {(i.get("src") or "").split("?")[0]: i for i in ((assets or {}).get("images") or {}).get("items", [])}
    rev = {(r.get("src") or "").split("?")[0]: r for r in (facts.get("reverseSearch") or [])}
    out = []
    for i in facts.get("images") or []:
        if not _in(i, b) or (i.get("w") or 0) * (i.get("h") or 0) < 6000:
            continue
        src = (i.get("src") or "").split("?")[0]
        a, r = by_src.get(src, {}), rev.get(src, {})
        out.append({"file": src.rsplit("/", 1)[-1][:60], "shown": f'{i.get("w")}x{i.get("h")}',
                    "real_size": f'{i.get("naturalW")}x{i.get("naturalH")}',
                    "stretched": bool(a.get("upscaled")) or ((i.get("naturalW") or 0) and (i.get("w") or 0) > (i.get("naturalW") or 0) * 1.3),
                    "stock_name": bool(a.get("stock_suspect")), "on_stock_sites": r.get("stock_domains") or [],
                    "alt": (i.get("alt") or "")[:60]})
    return out[:12]


def _stacked(b, facts):
    """Bullets built from icons and text rather than list tags: three or more short lines stacked in one
    column, close together. a photography site's ticked "All In One Solution" list read as no bullets without this."""
    rows = sorted([t for t in (facts.get("textAt") or []) if _in(t, b) and 1 <= len(t["text"].split()) <= 12
                   and t.get("tag") not in ("a", "button", "h1", "h2")], key=lambda t: t["top"])
    best = 0
    for col in {round((t.get("left") or 0) / 8) for t in rows}:
        col_rows = [t for t in rows if abs(round((t.get("left") or 0) / 8) - col) <= 1]
        run = 1
        for a, c in zip(col_rows, col_rows[1:]):
            run = run + 1 if 0 < c["top"] - a["top"] <= 48 else 1
            best = max(best, run)
    return best if best >= 3 else 0


def _drop_guess(ev, kind, long_, cut_hint):
    """How likely this section is to lose the reader, 0 to 10, from what the code can measure. A starting
    point for the judge, who reads the section and sets the real number (Jono, 28 Sep 2026: "would it win
    the lead, or would it likely lose someone")."""
    if kind in ("nav", "footer"):
        return 3
    if ev.get("stand_in_faces"):
        return 10          # a fabricated person loses the reader, and the page's trust with them
    g = 2
    g += 2 if long_ else 0
    g += 1 if (ev.get("reading_grade") or 0) > 10 else 0
    g += 1 if not ev.get("pictures") and not ev.get("video_frames") and kind in ("body", "steps") else 0
    g += 1 if not (ev.get("numbers") or ev.get("reviews") or ev.get("badges")) and kind in ("body", "steps") else 0
    g += 1 if not ev.get("buttons") and not ev.get("forms") and kind not in ("proof_logos", "stats") else 0
    g += 1 if ev.get("echoes") else 0
    g += 2 if cut_hint else 0
    g -= 1 if ev.get("numbers") and kind in ("gallery", "proof_quotes", "stats") else 0
    return max(0, min(10, g))


def guess_kind(b, idx, facts, vkinds, nav_bottom):
    """A SUGGESTION for the section kind. Claude overrides it from the screenshot."""
    if b["src"] == "nav":
        return "nav"
    if b["src"] == "footer":
        return "footer"
    vh = (facts.get("viewport") or {}).get("h") or 800
    if b["top"] <= nav_bottom + 12 and b["top"] < vh:
        return "hero"
    sec = {"top": b["top"], "h": b["h"], "heading": b.get("heading", ""),
           "words": sum(len(t["text"].split()) for t in (facts.get("textAt") or []) if _in(t, b))}
    kinds = [{"kind": v["kind"], "top": v["top"]} for v in vkinds or []]
    k = classify(sec, facts, max(idx, 1), kinds)
    return "other" if k in ("nav", "hero") else k


def cut_hint(b, ev, earlier_words):
    head = b.get("heading") or ""
    if NOT_ON_BLUEPRINT.search(head):
        return f'"{head}" is not a section a landing page needs. Cut it unless the screenshot says otherwise.'
    mine = set(w.lower() for w in re.findall(r"[A-Za-z]{5,}", " ".join(ev["text"])))
    if len(mine) >= 12:
        overlap = len(mine & earlier_words) / len(mine)
        if overlap > 0.6:
            return f"{round(overlap * 100)}% of its words already appear higher up the page. It may repeat a section above."
    return ""


# --------------------------------------------------------------------------- the first screen

def hero_lines(facts, band):
    """The headline and the line under it, as a visitor sees them - not as the tags say.

    a photography site puts its <h1> on the small "WEDDING PHOTOGRAPHY" label, so the H1 box drew the
    headline box on the eyebrow. The headline is the BIGGEST heading in the first screen; when
    several pieces share that size (a two-colour headline split into spans), the one holding
    the others wins. The subheadline is the first line of body text under it.
    """
    if not band:
        return {}, {}
    hs = [h for h in (facts.get("headingsAt") or []) if h.get("top") is not None
          and band["top"] <= h["top"] < band["bot"] and (h.get("w") or 0) > 0 and (h.get("h") or 0) > 0]
    if not hs:
        h1, sub = facts.get("h1Box") or {}, facts.get("subBox") or {}
        head = h1 if h1.get("top") is not None and band["top"] <= h1["top"] < band["bot"] else {}
        return head, (sub if head and sub.get("top") is not None else {})
    big = max(h.get("size") or 0 for h in hs)
    tops = [h for h in hs if (h.get("size") or 0) >= big - 2]
    head = max(tops, key=lambda h: ((h.get("w") or 0) * (h.get("h") or 0), -h["top"]))
    head = {k: head[k] for k in ("text", "top", "left", "w", "h")}
    below = head["top"] + head["h"]
    sub = {}
    for t in sorted((facts.get("textAt") or []), key=lambda t: t.get("top") or 0):
        if t.get("top") is None or t["top"] < below - 4 or t["top"] > below + 260 or t["top"] >= band["bot"]:
            continue
        if t.get("tag") in ("a", "button") or len(t["text"].split()) < 5 or t["text"] in head["text"]:
            continue
        sub = {k: t[k] for k in ("text", "top", "left", "w", "h")}
        break
    return head, sub


def hero_eyebrow(facts, band, head):
    """The short line just above the headline - where the deepest pain point belongs (Jono: "you didn't
    mention the pain point: 'Website To App Service For Ecommerce Brands'")."""
    if not band or not head or head.get("top") is None:
        return {}
    above = [t for t in (facts.get("textAt") or []) if t.get("top") is not None and band["top"] <= t["top"] < head["top"]
             and head["top"] - (t["top"] + (t.get("h") or 0)) <= 110 and 1 <= len(t["text"].split()) <= 14
             and t.get("tag") not in ("a", "button") and t["text"] not in head.get("text", "")]
    if not above:
        return {}
    t = max(above, key=lambda t: t["top"])
    return {k: t[k] for k in ("text", "top", "left", "w", "h")}


# --------------------------------------------------------------------------- homes

def _status_of(c):
    return {"DONE": "ok", "PARTIAL": "weak", "TO DO": "missing", "N/A": "n/a"}.get(c["status"])


def _secs(cards):
    ns = [str(c["n"]) for c in cards]
    if len(ns) == 1:
        return f"Section {ns[0]}"
    return "Sections " + ", ".join(ns[:-1]) + " and " + ns[-1]


def _bullets_part(cards):
    """Part 25, measured: does every text section carry three or more bullets?"""
    text = [c for c in cards if c["verdict"] in ("keep", "fix") and c["kind"] in ("body", "form", "pricing")]
    short = [c for c in text if c.get("few_bullets")]
    if not text:
        return {"status": "missing", "note": "No section says what the visitor gets, so nothing is in bullets. "
                                             "Each benefit section needs three to five."}
    if not short:
        return {"status": "ok", "note": f"{_secs(text)} {'carries' if len(text) == 1 else 'each carry'} three or more bullets."}
    return {"status": "weak", "note": f"{_secs(short)} {'has' if len(short) == 1 else 'have'} fewer than three bullets. "
                                      "Turn each paragraph into three to five."}


def _reading_part(cards):
    """Part 26, measured: is every line the business wrote at the grade limit or below? Client quotes
    are never graded. One line above the limit is enough to say so - the limit is the limit."""
    copy = [c for c in cards if c["verdict"] in ("keep", "fix") and c["kind"] in ("hero", "body", "steps", "form", "pricing")]
    hard = [(c, h) for c in copy for h in (c.get("hard") or [])]
    if not hard:
        graded = [c for c in copy if c.get("grade") is not None]
        if not graded:
            return {"status": "ok", "note": "Too little text of your own to measure. Client quotes are never graded."}
        top = max(graded, key=lambda c: c["grade"])
        return {"status": "ok", "note": f"No line of yours reads above grade {MAX_GRADE}. "
                                        f"The hardest section is {top['n']}, at grade {top['grade']:g}."}
    secs = []
    for c, _ in hard:
        if c not in secs:
            secs.append(c)
    worst = max(hard, key=lambda x: x[1]["grade"])
    n = len(hard)
    return {"status": "weak", "note": f"{'One line reads' if n == 1 else f'{n} lines read'} above grade {MAX_GRADE}, in "
                                      f"{_secs(secs).lower()}. The hardest is grade {worst[1]['grade']:g}. "
                                      "Shorter sentences, shorter words, one idea a line."}


MEASURED_PARTS = {25: _bullets_part, 26: _reading_part}


def place(cards_kinds, roll_checks):
    """Where each of the 21 is spoken about: {n: ("card", id) | ("page", None)}. Once each."""
    where = {}
    for n in sorted(NAMES):
        home = None
        for kind in HOME.get(n, []):
            hit = next((cid for cid, k in cards_kinds if k == kind), None)
            if hit:
                home = ("card", hit)
                break
        where[n] = home or ("page", None)
    return where


def sheet(facts, assets, bands, roll_result, pins=None, page_url=""):
    """The judging sheet Claude fills in, one entry per band plus the page-wide items."""
    vkinds = _vid_kinds(assets)
    nav_bottom = next((b["bot"] for b in bands if b["src"] == "nav"), 0)
    # the course template opens on a plain top line - business name and phone, no menu. A short band
    # at the very top with few words is that line, not the first screen (localhost GBP page, 28 Sep 2026)
    if not nav_bottom and bands:
        b0 = bands[0]
        w0 = sum(len(t["text"].split()) for t in (facts.get("textAt") or []) if _in(t, b0))
        if b0["top"] == 0 and b0["h"] <= 180 and w0 <= 20:
            b0["src"] = "nav"
            nav_bottom = b0["bot"]
    checks = {c["n"]: c for c in roll_result["checks"]}
    cards, seen_words = [], set()
    for i, b in enumerate(bands):
        ev = evidence(b, facts, assets, pins, vkinds, page_url)
        kind = guess_kind(b, i, facts, vkinds, nav_bottom)
        ask, label, _, want = checklist(kind)
        card = {"id": b["id"], "n": b["n"], "top": b["top"], "h": b["h"],
                "screenshot": f"assets/band-{b['n']:02d}.png",
                "code_sees": ev, "kind_guess": kind,
                "cut_hint": cut_hint(b, ev, seen_words) if kind not in ("hero", "nav", "form") else "",
                "is": "", "kind": kind, "verdict": None, "why": "",
                "holds": {}, "notes": [], "rewrites": [], "repeats": None, "drop_off": None, "drop_off_why": "",
                "image_grade": None, "image_why": "",
                "_ask": ask, "_a_section_like_this_has": want}
        if kind in ("gallery", "proof_quotes", "proof_logos", "proof_video") and ev["words"] >= 40 and not ev["numbers"]:
            ev["no_numbers"] = ("Not one number in this proof section: no result, no time saved, no count. "
                                "Proof without a number is a claim.")
        # A section that is only a line and a button, below the first screen. The form section is the
        # ask; a stray "Start a conversation" band is one more thing between the reader and the form.
        if kind not in ("hero", "nav", "footer", "form") and ev["buttons"] and not ev["forms"] and ev["words"] <= 45 \
                and not ev["pictures"] and not ev["video_frames"] and not card["cut_hint"]:
            card["cut_hint"] = ("Only a line and a button. The form section is the ask; a separate call-to-action band "
                                "is one more thing between the reader and the form. Cut it, or make it the form.")
        long_, limit = too_long(ev["words"], kind)
        ev["too_many_words"] = (f'{ev["words"]} words; a section like this should carry under {limit}. '
                                'No one reads that much.') if long_ else ""
        card["drop_off"] = None
        card["drop_off_code_guess"] = _drop_guess(ev, kind, long_, bool(card["cut_hint"]))
        seen_words |= set(w.lower() for w in re.findall(r"[A-Za-z]{5,}", " ".join(ev["text"])))
        cards.append(card)
    # Word overlap cannot see this - a B2B site's sections 4 and 5 share a fifth of their words
    # and make the same point. The measurable shape is two long sections that both talk about
    # the business. Claude confirms it from the screenshots.
    dense = []
    for card in cards:
        ev = card["code_sees"]
        at = ev["about_you"]
        if card["kind_guess"] in ("body", "other") and ev["too_many_words"] and at["about_the_business"] > at["about_the_visitor"]:
            if dense and not card["cut_hint"]:
                first = dense[0]
                card["cut_hint"] = (f'Section {first["n"]} already describes the business at length ({first["code_sees"]["words"]} words), '
                                    f'and this is another {ev["words"]} words about it. Likely a repeat: keep the stronger one, cut or merge the other.')
            dense.append(card)
    where = place([(c["id"], c["kind"]) for c in cards], roll_result["checks"])
    # measured facts for the page-wide items, so "mostly bullets" can never be said of a page
    # whose sections run to 150 words (a B2B site, 28 Sep 2026)
    over = [f'{c["n"]} ({c["code_sees"]["words"]} words)' for c in cards if c["code_sees"].get("too_many_words")]
    tel_at = [f'section {c["n"]}' for c in cards if c["code_sees"]["phone"]]
    off = sorted({t for c in cards for t in c["code_sees"]["buttons_off_the_page"]})
    badges = sorted({x for c in cards for x in c["code_sees"]["badges"]})
    selling = [c["n"] for c in cards if c["kind_guess"] in ("body", "steps")]
    sticky = facts.get("stickyForm")
    broken = [i.get("alt") or i.get("src", "").rsplit("/", 1)[-1] for i in (facts.get("brokenImages") or [])]
    mob = facts.get("_mobile") or {}
    top_bar = (mob.get("fixedTop") or [])
    bottom_bar = [x for x in (mob.get("fixedBottom") or []) if x.get("hasTel") or x.get("hasFormLink")]
    measured = {
        17: ("two fixed bars on a phone: one at the top" + (f' ("{top_bar[0].get("text", "")[:30]}")' if top_bar[0].get("text") else "")
             + " and one at the bottom - keep the bottom one only" if top_bar and bottom_bar else
             ("a bar fixed at the top on a phone and none at the bottom - move it to the bottom, with the form button" if top_bar else "")),
        8: (f'sections over the word limit: {", ".join(over)}' if over else "every section is under its word limit"),
        11: ("the form is sticky: on a computer it follows the visitor down the whole page" if sticky else ""),
        16: "; ".join(x for x in [
            f'{len(broken)} picture(s) do not load: {", ".join(sorted(set(broken))[:8])}' if broken else "",
            (lambda st: f'{len(st)} photo(s) found on stock sites: ' + ", ".join(f'{r.get("src", "").rsplit("/", 1)[-1][:40]} ({", ".join(r.get("stock_domains") or ["stock"])})' for r in st[:5]) if st else "")(
                [r for r in (facts.get("reverseSearch") or []) if r.get("verdict") == "stock"])] if x),
        10: (lambda bare: f'selling sections with no proof beside them: {", ".join(map(str, bare))} - sprinkle quotes there'
                           if bare else "")([c["n"] for c in cards if c["kind_guess"] in ("body", "steps")
                                             and not (c["code_sees"]["reviews"] or c["code_sees"]["numbers"] or c["code_sees"]["badges"])]),
        13: (f'review and award badges on the page: {", ".join(badges)}' if badges else
             "no review or award badges anywhere - grab the graphics from Capterra, G2, Google, Trustpilot or Product Hunt"),
        7: (f'{len(selling)} selling sections ({", ".join(map(str, selling))}). Pick the three strongest benefits, fold the rest in, cut what is left'
            if len(selling) > 3 else ""),
        22: (f'a tappable number in: {", ".join(tel_at)}' if tel_at else "no tappable phone number anywhere"),
        3: ((f'buttons that leave the page: {", ".join(off)}' if off else "every button stays on this page")
            + ("; the form follows the visitor down the page, so every section has a way to act" if sticky else "")),
    }
    page_items = {}
    for n, (kind, cid) in where.items():
        c = checks.get(n) or {}
        slot = {"name": NAMES[n], "status": None, "note": "",
                **({"_measured": "leave status empty and the code fills this in from the sections once they are judged"}
                   if n in MEASURED_PARTS else {}),
                "code_thinks": _status_of(c) if c else None,
                "code_says": (c.get("says") or "")[:200] if c else "",
                **({"code_measured": measured[n]} if measured.get(n) else {})}
        if kind == "card":
            next(x for x in cards if x["id"] == cid)["holds"][str(n)] = slot
        else:
            page_items[str(n)] = slot
    hero = next((c for c in cards if c["kind"] == "hero"), None)
    if hero:
        band = next(b for b in bands if b["id"] == hero["id"])
        head, sub = hero_lines(facts, band)
        eb = hero_eyebrow(facts, band, head)
        hero["eyebrow"] = {"text": (eb.get("text") or "")[:160], "verdict": None, "says": "",
                           "_how": "The line above the headline names the deepest pain, not a label. If there is none, say so and write one."}
        hero["headline"] = {"text": (head.get("text") or "")[:200], "verdict": None, "says": ""}
        hero["subheadline"] = {"text": (sub.get("text") or "")[:240], "verdict": None, "says": "",
                               **({} if sub else {"_note": "no line under the headline was found; say so if there is none"})}
    no_form = not (facts.get("forms") or [])
    mode = "homepage" if no_form and (len(bands) >= 10 or len(facts.get("navLinks") or []) >= 4) else "landing"
    return {
        "_how": ("One card per band of the page, top to bottom. Open each screenshot and READ it - the "
                 "code_sees block is measurement and guesses, the picture is the truth. For every card set: "
                 "is (what the section is, in plain words the owner would use), kind (one of: "
                 + ", ".join(TYPES) + "), verdict (keep | fix | cut), why (one line). For every component "
                 "in holds set status (ok | weak | missing | n/a | unchecked) and a one-line note. unchecked means the audit could not see it from outside, never that it is missing. A component can move "
                 "to the card it really lives in - one card only, never two. notes: up to three "
                 "{tag, quote, says} about the exact words; tag is one of Swap, Cut, Add, Rewrite, Move, Typo, Fix, Keep. rewrites: the three hardest lines in code_sees.hard_lines (above grade 10) MUST each get one, and so does EVERY other weak selling line in the section (a bullet, a tick, a benefit heading) as {before, after}, the after written as the chain - the feature, so you get the benefit, which means the outcome. Show the fix, not just the fault. Never invent a fact: use a [placeholder] where a number is needed. A hard line that is a client's own words is never rewritten: list it as {before, leave: 'the client quote'}. repeats: the number of an earlier section that already makes this section's point, or null - compare every section with every one above it, by what it SAYS, not by its words. A section that repeats an earlier one is cut or merged, never rewritten. drop_off: 0 to 10, how likely this section is to LOSE the reader - boring, text heavy, irrelevant, never tied back to a benefit - with drop_off_why in one line; anything fabricated - a stand-in face, a made-up brand, an unsourced rating, a play button with nothing behind it - is 10; drop_off_code_guess is the code's starting point from what it measured. EVERY card gets one, cut cards included. image_grade: 0 to 10 for how GOOD the pictures in the section are, not whether there are any - real or stock or AI, relevant to what the section says, sharp or stretched, showing people or the result - with image_why in one line; open the screenshot and use code_sees.image_facts. Every kept section with pictures gets one. A cut card gets a why and nothing else. Cut only on "
                 "positive evidence you can see; never because the code found nothing in a band."),
        "cards": cards,
        "page": {"mode": mode, "status": "live", "items": page_items, "do_first": [],
                 "_how": "status: live | draft - ask the owner. A draft is scored as if every placeholder is filled with the real thing, and the placeholders are listed as what blocks launch; on a live page a stand-in is a fabrication. mode: landing | homepage. items: status + note for each. A missing item the page has no "
                 "section for lands in the Add list, so its note must say WHERE it goes ('after the client "
                 "videos', 'beside the form') - never 'here'. do_first: optional, "
                         "the three moves that matter most, each one line. Left empty, they are worked "
                         "out from the weights."},
    }


# --------------------------------------------------------------------------- the finished report

def finish(bands, judged, facts, roll_result):
    """Claude's sheet plus the bands, turned into the report. Returns (model, problems)."""
    problems = []
    jc = {c["id"]: c for c in (judged.get("cards") or [])} if isinstance(judged.get("cards"), list) \
        else dict(judged.get("cards") or {})
    page = judged.get("page") or {}
    checks = {c["n"]: c for c in roll_result["checks"]}
    cards = []
    for b in bands:
        j = jc.get(b["id"]) or {}
        if j.get("top") is not None and abs(int(j["top"]) - b["top"]) > 60:
            problems.append(f'{b["id"]} was judged at {j["top"]}px but now starts at {b["top"]}px - re-judge it')
            j = {}
        v = (j.get("verdict") or "").lower()
        if v not in VERDICTS:
            problems.append(f'{b["id"]} ({b.get("heading") or "no heading"}) has no verdict')
        if v == "cut" and not (j.get("why") or "").strip():
            problems.append(f'{b["id"]} is cut with no reason')
        if v == "cut" and j.get("notes"):
            problems.append(f'{b["id"]} is cut but still carries fix notes')
        # a menu or a footer with ways off the page is cut on an ad page, never "fix" (one audited site, 2 Oct 2026)
        if v == "fix" and (j.get("kind") or "") in ("nav", "footer"):
            problems.append(f'{b["id"]} is the {"menu bar" if j["kind"] == "nav" else "footer"} and is marked fix - '
                            f'it is keep (nothing to leave by) or cut (links off the page), with the SEO exception in the why')
        if j.get("repeats") and v != "cut":
            problems.append(f'{b["id"]} repeats section {j["repeats"]} but is kept - cut it, or merge it and say so in the why')
        cards.append({"id": b["id"], "n": b["n"], "top": b["top"], "h": b["h"], "src": b["src"],
                      "heading": b.get("heading", ""), "is": (j.get("is") or "").strip() or b.get("heading") or f"Section {b['n']}",
                      "kind": j.get("kind") or "other", "verdict": v or None, "why": (j.get("why") or "").strip(),
                      "holds": {int(k): x for k, x in (j.get("holds") or {}).items()},
                      "notes": [{**x, "tag": _tag(x)} for x in (j.get("notes") or []) if (x.get("says") or "").strip()][:3],
                      # every weak selling line, before and after, in the chain: feature, so you get
                      # the benefit, which means the outcome (Jono, 28 Sep 2026: show the fix, not just the fault)
                      "rewrites": [x for x in (j.get("rewrites") or []) if (x.get("before") or "").strip()
                                   and (x.get("after") or "").strip()][:8],
                      # {before, leave: "a client's own words"}: a hard line the judge chose not to rewrite,
                      # with the reason. Counts as handled; never shown as a rewrite.
                      "left_as_is": [x for x in (j.get("rewrites") or []) if (x.get("before") or "").strip()
                               and not (x.get("after") or "").strip() and (x.get("leave") or "").strip()],
                      "headline": j.get("headline"), "subheadline": j.get("subheadline"), "eyebrow": j.get("eyebrow"),
                      "repeats": j.get("repeats"),
                      "drop_off": j.get("drop_off"), "drop_off_why": (j.get("drop_off_why") or "").strip(),
                      "image_grade": j.get("image_grade"), "image_why": (j.get("image_why") or "").strip()})
        pics_here = [i for i in (facts.get("images") or []) if _in(i, b) and (i.get("w") or 0) * (i.get("h") or 0) >= 20000]
        if pics_here and v in ("keep", "fix") and not isinstance(j.get("image_grade"), (int, float)):
            problems.append(f'{b["id"]} ({b.get("heading") or "no heading"}) has pictures but no image grade out of 10')
        if not isinstance(j.get("drop_off"), (int, float)) or not 0 <= j["drop_off"] <= 10:
            problems.append(f'{b["id"]} ({b.get("heading") or "no heading"}) has no drop-off score out of 10')
        elif (page.get("status") or "live") != "draft" and j["drop_off"] < 10 \
                and any(_in(i, b) and STAND_IN.search(i.get("src") or "") for i in (facts.get("images") or [])):
            problems.append(f'{b["id"]} ({b.get("heading") or "no heading"}) shows a stand-in face, so its risk of losing '
                            f'them is 10/10, not {j["drop_off"]:g} - a fabricated person costs the whole page its trust')

    # The measures travel with the card, and the rewrites are held to the bar they enforce: an
    # "after" above grade 10 is not a fix, and the three hardest lines in every section that
    # stays get a rewrite (Jono, 28 Sep 2026: "you should measure if it's written at a grade 10 level").
    def _norm(t):
        return re.sub(r"\s+", " ", (t or "").lower()).strip()
    for c, b in zip(cards, bands):
        text = _once([t["text"] for t in (facts.get("textAt") or []) if _in(t, b)])
        if (page.get("status") or "") == "draft":
            text = _without_slot_labels(text)
        c["words"] = sum(len(t.split()) for t in text)
        c["has_read_more"] = any(re.fullmatch(r"(?:read|show|see) more", (t or "").strip(), re.I) for t in text)
        c["grade"] = section_grade(text)
        c["long"], c["limit"] = too_long(c["words"], c["kind"])
        c["chain"] = chain_mix(text) if c["kind"] in ("hero", "body", "steps", "form", "pricing") else {}
        _quoted = [_norm(q.get("text"))[:40] for q in (facts.get("quoteBlocks") or []) if _in(q, b)]
        c["hard"] = ([x for x in hard_lines(text) if (x["grade"] or 0) > MAX_GRADE and x["line"].lstrip()[:1] not in "\"“‘'"
                      and not any(q and (q in _norm(x["line"]) or _norm(x["line"])[:40] in q) for q in _quoted)]
                     if c["verdict"] in ("keep", "fix") and c["kind"] in ("hero", "body", "steps", "form", "pricing") else [])
        for r in c["rewrites"]:
            g = read_grade(r["after"])
            r["grade_before"], r["grade_after"] = read_grade(r["before"]), g
            if g is not None and g > MAX_GRADE:
                problems.append(f'{c["id"]}: the rewrite "{r["after"][:60]}..." reads at grade {g}; keep it at {MAX_GRADE} or below')
        if c["verdict"] in ("keep", "fix") and c["kind"] not in ("proof_quotes", "proof_video", "founder_video", "nav", "footer", "faq"):
            done = [_norm(r["before"]) for r in c["rewrites"] + c.get("left_as_is", [])]
            # the headline and the line under it have their own verdicts, with a replacement
            for key in ("headline", "subheadline"):
                done.append(_norm((c.get(key) or {}).get("text") or ""))
            if c["kind"] == "hero":
                done += [_norm(x) for x in hero_lines(facts, b)[0].get("text", "").split("\n")]
                done.append(_norm(hero_lines(facts, b)[1].get("text", "")))
            done = [d for d in done if d]
            # a customer's own words are evidence, never copy to rewrite (mobiloud.com, 28 Sep 2026)
            quoted = [_norm(q.get("text"))[:40] for q in (facts.get("quoteBlocks") or []) if _in(q, b)]
            for h in [x for x in hard_lines(text) if (x["grade"] or 0) > MAX_GRADE
                      and x["line"].lstrip()[:1] not in "\"“‘'"
                      and not any(q and (q in _norm(x["line"]) or _norm(x["line"])[:40] in q) for q in quoted)][:3]:
                key = _norm(h["line"])[:28]
                if not any(key in d or d[:28] in _norm(h["line"]) for d in done):
                    problems.append(f'{c["id"]}: "{h["line"][:70]}" reads at grade {h["grade"]} and has no rewrite')

    # what the videos in a section measured, in one line the owner can check
    for c in cards:
        c["video_facts"] = _video_facts([v for v in (judged.get("_videos") or []) if c["top"] <= (v.get("top") or -1) < c["top"] + c["h"]])

    # A section with no way to act gets the recommendation written for it, in the page's own words
    # (Jono, 28 Sep 2026: "there's no CTA recommendation here, even though there's none").
    from collections import Counter
    nav_bot = next((b["bot"] for b in bands if b["src"] == "nav"), 0)
    ctas = [c for c in (facts.get("ctas") or []) if not c.get("fixed") and (c.get("top") or 0) >= nav_bot]
    # the page's main ask is the first button in the first screen, not the most repeated one - mobiloud.com
    # repeats "Book a Demo" more often than its real ask, "Get Your Free App Preview"
    hero_b = next((b for b in bands if b["src"] != "nav"), None)
    first = [c for c in ctas if hero_b and _in(c, hero_b)]
    main_cta = re.sub(r"\s*[→>›]+\s*$", "", (first[0].get("text", "") if first else
               (Counter(c.get("text", "") for c in ctas).most_common(1) or [("", 0)])[0][0])).strip()
    sticky = facts.get("stickyForm")
    for c, b in zip(cards, bands):
        text = [t["text"] for t in (facts.get("textAt") or []) if _in(t, b)]
        has_btn = any(_in(x, b) for x in ctas) or any(_in(f, b) for f in (facts.get("forms") or []))
        # counted FIRST: the anatomy below reads them, and when they were counted after it each
        # section's pills showed the section before it (found 1 Oct 2026)
        # a wrapper around two ticks is not a third bullet: count the innermost ones only
        # (one audited site, 2 Oct 2026: two ticks were counted as five)
        _bl = [" ".join((x.get("text") or "").split()) for x in (facts.get("blocks") or []) if _in(x, b) and x.get("kind") == "bullet"]
        _leaf = {t for t in _bl if t and not any(o and o != t and o in t for o in _bl)}
        bullets = max(len([t for t in _leaf if len(t.split()) >= 3]), _stacked(b, facts))
        pics = sum(1 for i in (facts.get("images") or []) if _in(i, b) and (i.get("w") or 0) * (i.get("h") or 0) >= 12000)
        frames = sum(1 for f in (facts.get("iframes") or []) + (facts.get("videoWidgets") or []) if _in(f, b))
        c["needs_button"] = (c["verdict"] in ("keep", "fix") and not has_btn and not sticky
                             and c["kind"] in ("body", "steps", "gallery", "proof_quotes", "proof_video", "founder_video", "pricing"))
        # a selling section with no proof in it - no number, no review, no badge, no face - reads bland
        # (Jono, 28 Sep 2026: "it shouldn't feel bland")
        has_proof = (any(_in(q, b) for q in (facts.get("quoteBlocks") or [])) or _badges(facts, b)
                     or _numbers(text) or any(_in(r, b) for r in (facts.get("reverseSearch") or []) if r.get("why") == "reviewer photo"))
        c["bland"] = c["verdict"] in ("keep", "fix") and c["kind"] in ("body", "steps") and not has_proof
        c["page_has_phone"] = bool(facts.get("tel"))
        # the first screen's anatomy (Jono, 28 Sep 2026): the three ticks are PROOF - numbers - not features
        if c["kind"] == "hero":
            ticks = [x["text"] for x in (facts.get("blocks") or []) if _in(x, b) and x.get("kind") == "bullet"]
            joined = " ".join(text)
            c["anatomy"] = [
                ("pain line", bool((c.get("eyebrow") or {}).get("text") or hero_eyebrow(facts, b, hero_lines(facts, b)[0]))),
                ("headline", bool(c["heading"])),
                ("offer line", bool(hero_lines(facts, b)[1])),
                ("proof ticks", len(ticks) >= 2 and sum(1 for t in ticks if re.search(r"\d", t)) >= 2),
                ("badges", bool(_badges(facts, b))),
                ("form button", has_btn),
                ("phone", any(_in(t, b) for t in (facts.get("tel") or []))),
                ("reply time", bool(re.search(r"(?:reply|respond|answer|get back)[^.]{0,40}\b(?:second|minute|hour|same day|today)", joined, re.I))),
            ]
            c["feature_ticks"] = len(ticks) >= 2 and sum(1 for t in ticks if re.search(r"\d", t)) < 2
        # the anatomy of a selling section, measured part by part (Jono, 28 Sep 2026)
        if c["kind"] == "body" and c["verdict"] in ("keep", "fix"):
            joined = " ".join(text)
            c["anatomy"] = [
                ("headline", bool(c["heading"])),
                ("paragraph", any(len(t.split()) >= 12 for t in text)),
                ("bullets", bullets >= 3),
                ("form button", has_btn or bool(sticky)),
                ("phone", any(_in(t, b) for t in (facts.get("tel") or []))),
                ("reply time", bool(re.search(r"(?:reply|respond|answer|get back)[^.]{0,40}\b(?:second|minute|hour|same day|today)", joined, re.I))),
                ("proof", bool(has_proof)),
                ("picture or video", pics > 0 or frames > 0 or isinstance(c.get("image_grade"), (int, float))),
            ]
        c["main_cta"] = main_cta
        c["few_bullets"] = bullets < 3
        c["no_graphic"] = (c["verdict"] in ("keep", "fix") and c["kind"] in ("body", "steps") and pics == 0 and frames == 0
                           and not isinstance(c.get("image_grade"), (int, float))
                           and sum(len(t.split()) for t in text) >= 60)
        c["echoes"] = _echoes(b, facts)

    kept_selling = [c["n"] for c in cards if c["verdict"] in ("keep", "fix") and c["kind"] in ("body", "steps")]

    # each of the 21, exactly once
    spoken = {}
    for c in cards:
        for n in c["holds"]:
            if n in spoken:
                problems.append(f"component {n} ({NAMES.get(n)}) is spoken about in two places")
            spoken[n] = ("card", c["id"])
    items = {int(k): x for k, x in (page.get("items") or {}).items()}
    # 25 and 26 are measured, not judged: left empty, the code fills them in from the cards
    for n, measure in MEASURED_PARTS.items():
        if n not in spoken and not ((items.get(n) or {}).get("status") or "").strip():
            items[n] = measure(cards)
    for n in items:
        if n in spoken:
            problems.append(f"component {n} ({NAMES.get(n)}) is in a card AND across the page")
        else:
            spoken[n] = ("page", None)
    for n in NAMES:
        if n not in spoken:
            problems.append(f"component {n} ({NAMES[n]}) is not spoken about anywhere")

    def status(n):
        src = spoken.get(n)
        if not src:
            return None, ""
        x = (next(c for c in cards if c["id"] == src[1])["holds"][n] if src[0] == "card" else items[n])
        s = (x.get("status") or "").lower()
        if s not in STATUSES:
            problems.append(f"component {n} ({NAMES[n]}) has no status")
            s = None
        return s, (x.get("note") or "").strip()

    comp = {}
    for n in NAMES:
        s, note = status(n)
        comp[n] = {"n": n, "name": NAMES[n], "status": s, "note": note, "where": spoken.get(n, ("page", None)),
                   "group": GROUP_OF.get(n, "")}
    # a judged "in place" on a measured part has to survive the measurement
    for n, measure in MEASURED_PARTS.items():
        if comp[n]["status"] == "ok" and measure(cards)["status"] != "ok":
            problems.append(f"component {n} ({NAMES[n]}) is marked in place, but the sections measure otherwise: {measure(cards)['note']}")

    # "Add" lists EVERYTHING missing, wherever it is spoken about (Jono, 28 Sep 2026: "it's missing
    # offer, guarantee, form, response time, phone number, founder video - it's missing A LOT").
    # A missing item inside a card is listed by name and section; the reasoning stays in the card.
    num = {c["id"]: c for c in cards}
    add, across = [], []
    for n, c in comp.items():
        if c["status"] == "missing":
            if c["where"][0] == "card":
                sec = num[c["where"][1]]
                add.append({**c, "goes": f'In section {sec["n"]}, {sec["is"][0].lower() + sec["is"][1:]}.', "in_card": True})
            elif n in HOME:
                add.append({**c, "goes": c["note"] or WHERE_TO_ADD.get(n, "")})
            else:
                across.append(c)
                add.append({**c, "goes": "Across the page, see above.", "in_card": True})
            continue
        if c["where"][0] == "page":
            across.append(c)

    add.sort(key=lambda c: (-WEIGHT.get(c["n"], 1), c["n"]))

    # "In place" has to survive the numbers the code measured
    # More than three selling sections kept is not "three benefits": pick three, fold, cut. Less is more.
    if comp.get(7, {}).get("status") == "ok" and len(kept_selling) > 3:
        problems.append(f"component 7 (three benefits) is marked in place, but {len(kept_selling)} selling sections are kept "
                        f"({', '.join(map(str, kept_selling))}) - pick the three strongest, fold the rest in or cut them")
    over = [c for c, b in zip(cards, bands) if c["verdict"] in ("keep", "fix") and c.get("long")]
    if comp.get(8, {}).get("status") == "ok" and len(over) >= 2:
        problems.append("component 8 (little text) is marked in place, but sections "
                        + ", ".join(str(c["n"]) for c in over) + " are over their word limit")
    stock = sum(1 for i in (facts.get("images") or []) if i.get("stock_suspect"))
    mob = facts.get("_mobile") or {}
    if comp.get(17, {}).get("status") == "ok" and (mob.get("fixedTop") or []):
        problems.append("component 17 (the mobile bar) is marked in place, but a second bar is fixed at the top on a phone - one bar only, at the bottom")
    # mostly real photos passes (Jono's rule), but a stock one is always named, never skipped
    if comp.get(16, {}).get("status") == "ok" and stock and not re.search(r"stock|generated|ai-", comp[16]["note"], re.I):
        problems.append(f"component 16 (real photos) is marked in place, but the code found {stock} photo(s) that look like stock - "
                        "say which, or say why they are real")

    applies = [c for c in comp.values() if c["status"] and c["status"] not in ("n/a", "unchecked")]
    tally = {"ok": sum(1 for c in applies if c["status"] == "ok"),
             "weak": sum(1 for c in applies if c["status"] == "weak"),
             "missing": sum(1 for c in applies if c["status"] == "missing"),
             "of": len(applies), "cut": sum(1 for c in cards if c["verdict"] == "cut"),
             # what is left out of the count, by name, so "7 of 19" never needs explaining in chat
             "left_out": [(c["name"], c["status"]) for c in comp.values() if c["status"] in ("n/a", "unchecked")],
             "total": len(comp)}

    # "Do these first" names the move and WHERE it is, and nothing more: the reasons are in
    # the cards, and saying them twice is the repetition Jono kept cutting (27 Sep 2026).
    do_first = [x for x in (page.get("do_first") or []) if x][:3]
    if not do_first:
        num = {c["id"]: c["n"] for c in cards}

        def where(c):
            w = c["where"]
            return f' (section {num[w[1]]})' if w[0] == "card" else ""
        # one line per PLACE, so three fixes to the first screen read as one move, not three
        groups = {}
        for c in applies:
            if c["status"] not in ("weak", "missing"):
                continue
            key = c["where"][1] if c["where"][0] == "card" else f'page-{c["n"]}'
            verb = "add" if c["status"] == "missing" else "fix"
            nm = c["name"]
            if not re.match(r"(?:The|A|An)\b", nm) and not nm.endswith("s"):
                nm = ("a " if verb == "add" else "the ") + nm[0].lower() + nm[1:]
            g = groups.setdefault(key, {"w": 0, "parts": [], "where": where(c)})
            wt = WEIGHT.get(c["n"], 1) + (1 if c["status"] == "missing" else 0)
            g["w"] = max(g["w"], wt)
            g["parts"].append((wt, f'{verb} {nm[0].lower() + nm[1:]}'))
        moves = []
        for g in groups.values():
            # heaviest first inside the line too: the guarantee was being cut off the end
            line = ", ".join(p for _, p in sorted(g["parts"], key=lambda x: -x[0])[:3])
            moves.append((g["w"], f'{line[0].upper() + line[1:]}{g["where"]}.'))
        cuts = [c for c in cards if c["verdict"] == "cut"]
        if cuts:
            moves.append((2.5, f'{"Leave out" if (page.get("mode") or "") == "homepage" else "Cut"} '
                               f'section{"s" if len(cuts) > 1 else ""} {", ".join(str(c["n"]) for c in cuts)}.'))
        do_first = [m for _, m in sorted(moves, key=lambda m: -m[0])[:3]]

    # the boxes: one per card, plus the headline and subheadline inside the first screen
    boxes = [{"id": c["id"], "label": str(c["n"]), "top": c["top"], "h": c["h"], "left": None, "w": None,
              "tone": c["verdict"] or "none"} for c in cards]
    hero = next((c for c in cards if c["kind"] == "hero"), None)
    if hero:
        band = next(b for b in bands if b["id"] == hero["id"])
        seen = dict(zip(("headline", "subheadline"), hero_lines(facts, band)))
        seen["eyebrow"] = hero_eyebrow(facts, band, seen["headline"])
        if seen["headline"].get("text"):
            hero["heading"] = seen["headline"]["text"]
        # the pain point is judged on every page, present or not
        if not ((hero.get("eyebrow") or {}).get("says") or "").strip():
            problems.append(f'{hero["id"]}: no verdict on the line above the headline - the pain point. Judge it, or say there is none and write one')
        for key, tag in (("eyebrow", "a"), ("headline", "b"), ("subheadline", "c")):
            bx, jx = seen[key], hero.get(key) or {}
            hero[f"has_{key}_box"] = False
            if bx.get("top") is not None and (bx.get("h") or 0) > 0 and hero["top"] <= bx["top"] < hero["top"] + hero["h"] \
                    and (jx.get("says") or "").strip():
                hero[f"has_{key}_box"] = True
                boxes.append({"id": f'{hero["id"]}-{key}', "label": f'{hero["n"]}{tag}', "top": bx["top"], "h": bx["h"],
                              "left": bx.get("left"), "w": bx.get("w"),
                              "tone": {"good": "keep", "weak": "fix", "bad": "fix"}.get((jx.get("verdict") or "").lower(), "fix")})
    # chat widgets and popups: both cover the page and pull attention from the form (Jono, 28 Sep 2026).
    # Cookie banners are left alone - they are often the law.
    hidden = facts.get("overlays_hidden") if isinstance(facts.get("overlays_hidden"), list) else []
    remove = []
    if facts.get("chat") or "chat" in hidden:
        remove.append({"what": "The chat widget", "why": "It covers part of the page and pulls attention away from the form. "
                                                          "A visitor ready to talk should see a phone number, not a chatbot."})
    if facts.get("popup") or "popup" in hidden:
        remove.append({"what": "The popup", "why": "It interrupts people before the page has made its case. The offer belongs on "
                                                   "the page, beside the form."})
    draft = (page.get("status") or "live") == "draft"
    fill = []
    for c, b in zip(cards, bands):
        c["placeholders"] = placeholders_in(b, facts) if c["verdict"] != "cut" else []
        fill += [{"n": c["n"], "section": c["is"], "what": w} for w in c["placeholders"]]
    model = {"cards": cards, "components": comp, "add": add, "across": across, "tally": tally, "remove": remove,
             "draft": draft, "fill": fill,
             "do_first": do_first, "mode": (page.get("mode") or "landing").lower(), "boxes": boxes,
             "page_h": facts.get("scrollHeight") or 0, "page_w": (facts.get("viewport") or {}).get("w") or 1366}
    problems += check(model, bands)
    return model, problems


# Every note says what KIND of change it is, so the owner can scan the card for the work
# (Jono, 28 Sep 2026: "this stuff should have a tag, like Missing or Swap").
TAGS = ("Swap", "Cut", "Add", "Rewrite", "Move", "Typo", "Fix", "Keep")


def _tag(note):
    t = (note.get("tag") or "").strip().capitalize()
    if t in TAGS:
        return t
    says = (note.get("says") or "").lower()
    for tag, rx in (("Typo", r"\btypo\b|glued together|repeats on the next line"),
                    ("Swap", r"\bswap\b|\breplace (?:it|the photo|the image)|stock|ai-generated"),
                    ("Keep", r"\bkeep it\b|^keep\b|\bleave it\b"),
                    ("Cut", r"\bcut (?:it|this|the line)\b|\bfiller\b|\bremove\b"),
                    ("Move", r"\bmove (?:it|this)\b|\bput it in the first screen\b|\bpull it up\b"),
                    ("Add", r"^add\b|\badd (?:a|the|one)\b|\bthere is no\b|\bmissing\b"),
                    ("Rewrite", r"'[^']{12,}'|\"[^\"]{12,}\"|\ba label\b|says nothing")):
        if re.search(rx, says):
            return tag
    return "Fix"


def _video_facts(vids):
    """ "46 seconds, smiles often, lively, 20% b-roll, no captions" - or the range across a wall of videos."""
    w = [v["watched"] for v in vids if (v.get("watched") or {}).get("seconds")]
    if not w:
        return ""
    secs = sorted(int(round(x["seconds"])) for x in w)
    face = {"lively": "face changes with the words", "some": "face changes a little", "flat": "flat face"}
    if len(w) == 1:
        x = w[0]
        if x.get("smiles") == "no one on camera":
            bits = [f'{secs[0]} seconds', "no one on camera", f'{int(x.get("broll_share") or 0)}% b-roll',
                    "captions on" if x.get("captions") else "no captions"]
        else:
            bits = [f'{secs[0]} seconds', f'smiles {x.get("smiles")}', face.get(x.get("expression"), ""),
                    f'{int(x.get("broll_share") or 0)}% b-roll', "captions on" if x.get("captions") else "no captions"]
        return ", ".join(b for b in bits if b and "None" not in b)
    smile = {x.get("smiles") for x in w}
    return ", ".join([f'{len(w)} of {len(vids)} videos watched', f'{secs[0]} to {secs[-1]} seconds',
                      f'smiles {"/".join(sorted(smile))}',
                      f'{"no" if all(not (x.get("broll_share") or 0) for x in w) else "some"} b-roll',
                      f'{"no" if not any(x.get("captions") for x in w) else "some"} captions'])


def check(model, bands):
    """The rules the report may never break. Any line returned stops the report being written."""
    out = []
    # the bands tile the page
    prev = 0
    for b in bands:
        if b["top"] != prev:
            out.append(f'gap or overlap before {b["id"]}: {prev}px to {b["top"]}px')
        if b["h"] <= 0:
            out.append(f'{b["id"]} has no height')
        prev = b["bot"]
    if bands and model["page_h"] and prev != model["page_h"]:
        out.append(f"the bands stop at {prev}px but the page is {model['page_h']}px tall")
    # one card per band, one box per card, and every sub-box belongs to a card line
    ids = [c["id"] for c in model["cards"]]
    if len(ids) != len(bands):
        out.append(f"{len(bands)} bands but {len(ids)} cards")
    card_boxes = [x for x in model["boxes"] if x["id"] in ids]
    if len(card_boxes) != len(ids):
        out.append(f"{len(ids)} cards but {len(card_boxes)} section boxes")
    for x in model["boxes"]:
        if x["id"] not in ids and not any(x["id"].startswith(i + "-") for i in ids):
            out.append(f'box {x["label"]} has no card')
        if x["top"] < 0 or (model["page_h"] and x["top"] >= model["page_h"]):
            out.append(f'box {x["label"]} sits outside the page')
    return out


# --------------------------------------------------------------------------- screenshots

def crop(bands, full_png, page_h, out_dir, max_w=1100):
    """One screenshot per band, cut from the full-page shot, so Claude reads exactly the band."""
    from PIL import Image
    Image.MAX_IMAGE_PIXELS = None
    img = Image.open(full_png)
    scale = img.height / page_h if page_h else 1
    paths = []
    for b in bands:
        top, bot = int(b["top"] * scale), int(min(b["bot"] * scale, img.height))
        if bot <= top:
            continue
        part = img.crop((0, top, img.width, bot))
        if part.width > max_w:
            part = part.resize((max_w, max(1, int(part.height * max_w / part.width))))
        p = os.path.join(out_dir, f"band-{b['n']:02d}.png")
        part.save(p)
        paths.append(p)
    return paths
