"""The page itself, marked up - every change the owner should make, drawn on their own screenshot.

Four sources feed the pins, all of them already measured elsewhere:
  1. copy_check   - the bullets, paragraphs, testimonials and headline, each with its box
  2. the capture  - placeholders still on the page, stock photos, play buttons with no video,
                    sections with no button, the form, tiny taps
  3. the 18       - a component that is missing gets pinned where it should go
  4. the rubric   - anything else failing that knows where it lives

Positions come from the desktop capture, which records every element's pixel box, and the
screenshot is that same run's full-page shot, so the two line up exactly.
"""
import os
import re

SEV = {"high": "bad", "medium": "warn", "low": "muted", "good": "good"}
ORDER = {"high": 0, "medium": 1, "low": 2, "good": 3}


def _fmt(t, n=52):
    t = re.sub(r"\s+", " ", t or "").strip()
    return (t[:n] + "...") if len(t) > n else t


# Where each judged verdict belongs on the page. A verdict with no anchor here never
# appears on the marked-up view - it goes to the list instead (Jono, 26 September 2026).
#   fold      the first screen          quotes   the written testimonials
#   videos    the testimonial videos    faq      the FAQ section
#   images    the photo the call is about
JUDGED_ANCHOR = {
    "M1": "h1", "M2": "subhead", "M3": "subhead", "M4": "subhead", "D2": "fold", "P2": "video-frame",
    "P4": "videos", "P6": "quotes", "P8": "images",
    "W5": "faq", "F3": "faq",
    "W3": "sections", "W4": "sections",   # said per section, never once for the page
    "D1": None, "D7": None,               # no single place: the list page carries them
}



def _place_name(box, facts, keep=""):
    """What to call a spot that carries more than one note.

    The exact element wins. Otherwise keep the title the pin already had - it describes the
    message - and only fall back to a place name when there is nothing better. A section's
    own heading is never used for the hero, because there the heading is the page's H1.
    """
    for key, name in (("h1Box", "The headline"), ("subBox", "The line under the headline")):
        el = facts.get(key)
        if el and abs(el["top"] - box["top"]) < 6 and abs(el["h"] - box["h"]) < 6:
            return name
    if keep:
        h1t = ((facts.get("h1Box") or {}).get("text") or "").strip()
        if not (h1t and keep[:28] == h1t[:28]):
            return keep
    vph = (facts.get("viewport") or {}).get("h", 800)
    secs = facts.get("sections") or []
    if secs and box["top"] <= secs[0]["top"] + vph:
        return "The first screen"
    for sec in secs:
        if sec["top"] <= box["top"] < sec["top"] + sec["h"]:
            head = (sec.get("heading") or "").strip()
            h1t = ((facts.get("h1Box") or {}).get("text") or "").strip()
            if head and not (h1t and head[:28] == h1t[:28]):
                return head
            return "This section"
    return "This part of the page"


def _is_bar(box, facts):
    """Is this box really the navigation bar? A finding about page CONTENT never belongs there."""
    bar = facts.get("topBar") or {}
    if not box or not bar or bar.get("top") is None:
        return False
    return abs((box.get("top") or 0) - bar["top"]) < 8 and (box.get("h") or 0) <= (bar.get("h") or 0) + 8


def _same_spot(a, b):
    over_v = min(a["top"] + a["h"], b["top"] + b["h"]) - max(a["top"], b["top"])
    over_h = min(a["left"] + a["w"], b["left"] + b["w"]) - max(a["left"], b["left"])
    if over_v <= 0 or over_h <= 0:
        return False
    a1, a2 = a["w"] * a["h"], b["w"] * b["h"]
    return (over_v * over_h) / (min(a1, a2) or 1) > 0.6 and min(a1, a2) / (max(a1, a2) or 1) > 0.5


def _pins(copy_findings, facts, sc, eighteen, assets=None):
    pins = []
    unlocated = []
    # Every video classified from its TRANSCRIPT, once, before any pin is written. Empty
    # when no assets were passed, and every guard below falls back to the old behaviour
    # rather than inventing a kind.
    from .copy_check import video_kinds as _vk
    _kinds = _vk(assets) if assets else []

    def add(sev, title, says, box, quote="", part="", lead=2):
        """lead: 0 the component is missing · 1 it is there but broken · 2 a detail about it.

        A pin needs a REAL box. No box, or a zero-size box, means the thing was found but
        never located - that goes to the list, never to the corner of the page.
        """
        if not box:
            return
        top, left = box.get("top"), box.get("left")
        w, h = box.get("w") or 0, box.get("h") or 0
        if top is None or left is None or w <= 0 or h <= 0:
            unlocated.append({"title": title, "says": says, "severity": sev, "part": part})
            return
        # THE NAVIGATION BAR IS NOT THE PAGE. A finding about the offer, the proof block, the
        # form or any other content cannot be drawn on the header, whatever fallback produced
        # the box. This is the fail-safe: it does not matter which of the 41 rules went wrong,
        # nothing about content gets drawn up there (Jono, 27 Sep 2026).
        if part not in ("14. No header, no footer", "Navigation") and _is_bar(box, facts):
            unlocated.append({"title": title, "says": says, "severity": sev, "part": part,
                              "why": "the box landed on the navigation bar"})
            return
        # Impossible geometry means the element was mis-identified. Report it in the list
        # rather than drawing a box somewhere wrong (Jono, 27 September 2026).
        page_h = facts.get("scrollHeight") or 0
        page_w = (facts.get("viewport") or {}).get("w") or 0
        if top < 0 or left < 0 or (page_h and h > page_h) or (page_w and w > page_w * 1.5):
            unlocated.append({"title": title, "says": says, "severity": sev, "part": part})
            return
        pins.append({"severity": sev, "title": title, "says": says, "quote": quote, "part": part,
                     "lead": lead, "box": {k: box[k] for k in ("top", "left", "w", "h")}})

    # 1. copy findings already carry their box. Two notes on the same card become one.
    at = {}
    for f in copy_findings:
        if not f.get("box"):
            continue
        k = (f["box"]["top"], f["box"]["left"])
        if k in at:
            prev = at[k]
            prev["says"] = prev["says"].rstrip(".") + ". " + f["says"]
            if ORDER[f["severity"]] < ORDER[prev["severity"]]:
                prev["severity"] = f["severity"]
            continue
        at[k] = {"severity": f["severity"], "title": f["title"], "says": f["says"],
                 "quote": f.get("quote", ""), "box": f["box"], "rule": f.get("rule", "")}
    for v in at.values():
        add(v["severity"], v["title"], v["says"], v["box"], v["quote"])
        pins[-1]["rule"] = v["rule"]

    # 2. placeholders the owner left on the page - the most obvious thing a visitor sees.
    # A row of them (six logo slots) is ONE problem, so they group into one box.
    rows = {}
    for h in (facts.get("holders") or []):
        rows.setdefault((h.get("kind") == "image", round(h["top"] / 40)), []).append(h)
    for (is_img, _), group in rows.items():
        group.sort(key=lambda g: g["left"])
        box = {"top": min(g["top"] for g in group), "left": min(g["left"] for g in group),
               "w": max(g["left"] + g["w"] for g in group) - min(g["left"] for g in group),
               "h": max(g["h"] for g in group)}
        n = len(group)
        if is_img:
            add("high", "This photo is a placeholder" if n == 1 else f"{n} placeholder photos",
                "Put a real photo here, or take the frame out until you have one.", box, _fmt(group[0].get("text", "")))
        else:
            add("high", "Placeholder still on the page" if n == 1 else f"{n} placeholders in this row",
                "Fill these in or delete the section. A visitor reads this as an unfinished business.",
                box, _fmt(" · ".join(g["text"] for g in group), 70))

    # 3. a play button with nothing behind it. The topmost one is the founder video slot;
    #    anything below it is a testimonial slot. One component each, never both.
    fakes = sorted(facts.get("fakeVideo") or [], key=lambda v: v["top"])
    fold_h = (facts.get("viewport") or {}).get("h", 800) * 2
    for i, v in enumerate(fakes):
        # topmost-is-the-founder was the old guess. If a transcript says otherwise, believe it.
        _fk = next((x for x in _kinds if x["kind"] == "founder"), None)
        founder = (v["top"] < fold_h) if _fk is None else False
        add("high",
            "The founder video is missing" if founder else "This testimonial video does not play",
            ("Film 45 seconds on your phone: who you are, why you do this, the promise. The still "
             "behind the play button should be you, smiling, looking at the camera." if founder
             else "Put the client's clip here, or take the frame out until you have it."), v,
            part="1. Founder video" if founder else "6. Video testimonials", lead=0)

    # 4. stock photography
    for i in (facts.get("images") or []):
        if i.get("stock_suspect") and i.get("top") is not None:
            add("medium", "This photo is not of your business",
                "Replace it with your team, your work, your place.", i, _fmt(i.get("alt", "")),
                part="16. Real photos of this business")

    # 5. sections that argue but never ask
    _f0 = (facts.get("forms") or [{}])[0]
    form_top = _f0.get("top")

    def _is_row(sec, all_secs):
        """True when this block sits inside a bigger one - a row, not a section."""
        return any(o is not sec and o["top"] <= sec["top"]
                   and o["top"] + o["h"] >= sec["top"] + sec["h"]
                   and o["h"] > sec["h"] * 1.3 for o in all_secs)

    all_secs = facts.get("sections") or []
    for s in all_secs:
        if _is_row(s, all_secs):
            continue  # a row inside a section: the section carries the button
        if form_top is not None and s["top"] <= form_top < s["top"] + s["h"]:
            continue  # the form is here: nothing to point at it with
        if s.get("words", 0) > 60 and s.get("ctas", 0) == 0:
            add("low", "No button in this section",
                "Someone convinced here has to scroll to act. Add a button that goes to the form.",
                s, _fmt(s.get("heading", "")))

    # 6. the 18, pinned where the component belongs
    secs = facts.get("sections") or []
    hero = secs[0] if secs else None
    form = (facts.get("forms") or [{}])[0]
    quotes = facts.get("quoteBlocks") or []
    # the fold: the first screen only, not the whole hero section
    vph = (facts.get("viewport") or {}).get("h", 800)
    fold = {"top": hero["top"], "left": hero["left"], "w": hero["w"], "h": min(vph, hero["h"])} if hero else None
    quote_box = None
    if quotes:
        quote_box = {"top": min(q["top"] for q in quotes), "left": min(q["left"] for q in quotes),
                     "w": max(q["left"] + q["w"] for q in quotes) - min(q["left"] for q in quotes),
                     "h": max(q["top"] + q["h"] for q in quotes) - min(q["top"] for q in quotes)}
    # where each of the 18 belongs. A component missing from this map has no place on the
    # page, so it is NOT drawn - `unplaced` hands it to the list view (Jono, 26 Sep 2026).
    photo_box = None
    real_imgs = [i for i in (facts.get("images") or []) if i.get("top") is not None]
    if real_imgs:
        photo_box = max(real_imgs, key=lambda i: i["w"] * i["h"])
    portfolio = next((x for x in secs if re.search(r"work|portfolio|gallery|rebuil|project|before", (x.get("heading") or ""), re.I)), None)
    trust_strip = None
    h1_top = (facts.get("h1Box") or {}).get("top", 0)
    strip_bullets = [b for b in (facts.get("blocks") or [])
                     if b["kind"] == "bullet" and hero
                     and h1_top < b["top"] < hero["top"] + min(vph, hero["h"]) + 120]
    if strip_bullets:
        trust_strip = {"top": min(b["top"] for b in strip_bullets), "left": min(b["left"] for b in strip_bullets),
                       "w": max(b["left"] + b["w"] for b in strip_bullets) - min(b["left"] for b in strip_bullets),
                       "h": max(b["h"] for b in strip_bullets)}
    avatars = (facts.get("initialsClusters") or [None])[0]
    # sections we can point at by what they contain
    def _sec_with(rx):
        return next((x for x in secs if re.search(rx, (x.get("heading") or ""), re.I)), None)
    tst_sec = _sec_with(r"say|testimonial|review|words|client")
    res_sec = _sec_with(r"result|case stud|what changed|built")
    foot = next((x for x in reversed(secs) if x.get("top", 0) > 0), None)
    # under the main button in the first screen: where the proof block belongs when there
    # is not one yet
    main_cta = None
    for c in (facts.get("ctas") or []):
        if c.get("top") is None or not hero:
            continue
        if hero["top"] <= c["top"] < hero["top"] + min(vph, hero["h"]) and c.get("w", 0) >= 120:
            main_cta = c
            break
    under_cta = ({"top": main_cta["top"] + main_cta["h"] + 6, "left": main_cta["left"],
                  "w": max(main_cta["w"], 280), "h": 44} if main_cta else None)
    _frames = [x for x in (facts.get("iframes") or []) + (facts.get("videos") or [])
               if x.get("top") is not None and x.get("h")]
    _frames.sort(key=lambda x: x["top"])

    def _span(fr):
        if not fr:
            return None
        return {"top": min(x["top"] for x in fr), "left": min(x["left"] for x in fr),
                "w": max(x["left"] + x["w"] for x in fr) - min(x["left"] for x in fr),
                "h": max(x["top"] + x["h"] for x in fr) - min(x["top"] for x in fr)}

    # Split the frames by what their transcripts say. Component 6 is CLIENT videos only -
    # boxing the founder video as a testimonial is the error this removes.
    _cl_idx = {k["index"] for k in _kinds if k["kind"] == "client"}
    _fo_idx = {k["index"] for k in _kinds if k["kind"] == "founder"}
    _client_frames = [f for i, f in enumerate(_frames) if i in _cl_idx] if _cl_idx else []
    _founder_frame = next((f for i, f in enumerate(_frames) if i in _fo_idx), None)
    _vid_box = _span(_client_frames) if _client_frames else (None if _kinds else _span(_frames))
    _founder_box = _founder_frame or (_frames[0] if (_frames and not _kinds) else None)
    _stock = [i for i in (facts.get("images") or []) if i.get("stock_suspect") and i.get("top") is not None]
    # A MISSING component gets a box only where the page really shows the thing it is about.
    # No fallback to the fold, the hero or "the first thing near the top": that is how "The
    # offer" was drawn on a B2B site's navigation bar and how "the proof block above the
    # fold" landed on a 40px line of nav text (Jono, 27 Sep 2026). None means "say it in the
    # component list, draw nothing" - an honest silence beats a box in the wrong place.
    #
    # `fold` is deliberately absent from this table. It is the first screen of whatever
    # section happens to sit at the top, which on a page with a tall sticky header IS the
    # header, and nothing about an offer or a proof block belongs there.
    WHERE = {16: (_stock[0] if _stock else photo_box), 2: avatars or trust_strip, 5: trust_strip,
             4: facts.get("subBox"),
             12: form, 11: form, 15: portfolio or res_sec,
             # 6 is VIDEO testimonials: only pin it where videos actually are
             6: _vid_box, 10: quote_box or tst_sec, 13: tst_sec,
             17: None, 3: None, 7: None, 8: None, 9: None, 14: None, 18: None,
             1: _founder_box}
    if fakes:
        WHERE[1] = None
        WHERE[6] = None
    # already said elsewhere on the page, so neither pinned again nor listed
    covered = {18}
    if fakes:
        covered |= {1, 6}
    if (facts.get("_judgments") or {}).get("sections"):
        covered.add(18)
    unplaced = []
    for c in eighteen["checks"]:
        if c["status"] not in ("TO DO", "PARTIAL"):
            continue
        box = WHERE.get(c["n"], "unset")
        if box == "unset":
            box = None
        if box and box.get("top") is not None:
            add("high" if c["status"] == "TO DO" else "medium",
                c["name"], c["says"], box, part=f'{c["n"]}. {c["name"]}')
        elif c["n"] not in covered:
            unplaced.append(c)
    facts["_unplaced"] = [{"n": c["n"], "name": c["name"], "says": c["says"], "status": c["status"]} for c in unplaced]

    # 6b. The three above-the-fold judgements Jono makes every time.
    eb = facts.get("eyebrow")
    if eb:
        # the consequence they actually feel, never the framing ("tired of", "sick of")
        PAIN = re.compile(r"\b(?:wast(?:ed|ing)|burn(?:ed|ing) (?:money|cash|budget)|bleed\w*|"
                          r"losing (?:money|jobs|calls|leads|work|customers)|lost (?:money|jobs|calls|leads)|"
                          r"competitor\w*|rival\w*|someone else|the (?:shop|guy|business) (?:above|down the road)|"
                          r"another agency|promised|let down|ripped off|nothing to show|"
                          r"paying for|month after month|year after year|again and again|"
                          r"third time|tried \w+ (?:twice|before|already))\b", re.I)
        deep = PAIN.search(eb.get("text", ""))
        if not eb.get("asks") and not deep:
            add("medium", "The line above the headline says nothing",
                "This is the one line that makes them feel the problem before you pitch. Name the "
                "thing that actually bothers them - a competitor taking the calls, money going out "
                "with nothing back, another agency that promised and did not deliver.",
                eb, _fmt(eb.get("text", "")))
        elif not deep:
            add("low", "The line above the headline is surface-level",
                "It names a symptom. Go one level down to what it costs them: the competitor "
                "getting the call, the money spent with nothing to show, the last agency that "
                "wasted a year. That is what they are actually trying to escape.",
                eb, _fmt(eb.get("text", "")))
    # the tick strip under the buttons: terms, or proof?
    TERMS = re.compile(r"month to month|no lock|you keep|fixed price|no contract|cancel any|from \$|per month", re.I)
    PROOF = re.compile(r"\d[\d,]*\+?\s*(?:jobs|clients|customers|reviews|years|homes|projects)|\d\.\d\s*(?:stars|out of)|since \d{4}", re.I)
    if hero:
        strip = [b for b in (facts.get("blocks") or [])
                 if b["kind"] == "bullet"
                 and (facts.get("h1Box") or {}).get("top", 0) < b["top"] < hero["top"] + min(vph, hero["h"]) + 120]
        if strip and not any(PROOF.search(b["text"]) for b in strip) and any(TERMS.search(b["text"]) for b in strip):
            box = {"top": min(b["top"] for b in strip), "left": min(b["left"] for b in strip),
                   "w": max(b["left"] + b["w"] for b in strip) - min(b["left"] for b in strip),
                   "h": max(b["h"] for b in strip)}
            add("medium", "These three should be proof, not terms",
                "Month to month and no lock-in are terms. The best use of this line is proof: jobs done, "
                "years in business, reviews, money made for clients.", box,
                _fmt(" · ".join(b["text"] for b in strip), 70))
    for c in (facts.get("initialsClusters") or []):
        add("medium", "Initials instead of faces",
            f'These {c["count"]} circles are initials. Real client photos are believed; initials read as a placeholder.',
            c, _fmt(c.get("text", "")))

    # 6c. The judged verdicts, each on the element it is about. Anything with no anchor
    #     is not drawn here at all - `verdicts()` hands it to the list view instead.
    faq_sec = None
    for sec in secs:
        if re.search(r"question|faq|before you (?:enquire|ask)|answers", (sec.get("heading") or ""), re.I):
            faq_sec = sec
            break
    vid_box = None
    if fakes:
        below = [v for v in fakes if v["top"] >= fold_h] or fakes
        vid_box = {"top": min(v["top"] for v in below), "left": min(v["left"] for v in below),
                   "w": max(v["left"] + v["w"] for v in below) - min(v["left"] for v in below),
                   "h": max(v["top"] + v["h"] for v in below) - min(v["top"] for v in below)}
    stock = [i for i in (facts.get("images") or []) if i.get("stock_suspect") and i.get("top") is not None]
    ANCHOR_BOX = {"fold": (fold if (fold and not _is_bar(fold, facts)) else None), "quotes": quote_box, "videos": vid_box, "faq": faq_sec,
                  "images": stock[0] if stock else None,
                  "h1": facts.get("h1Box"), "subhead": facts.get("subBox"),
                  "video-frame": fakes[0] if fakes else None}
    grouped = {}
    for row in (sc.get("rows") or []):
        if row["kind"] != "JUDGED" or row["status"] in ("PASS", "PENDING", "N/A"):
            continue
        where = JUDGED_ANCHOR.get(row["id"], "unset")
        if where in (None, "unset", "sections", "images"):
            continue  # no place, or already said per section / per photo
        if not ANCHOR_BOX.get(where):
            continue
        grouped.setdefault(where, []).append(row)
    TITLE = {"fold": "The first screen", "quotes": "The written reviews",
             "videos": "The video testimonials", "faq": "The FAQ",
             "portfolio": "The work on show", "h1": "The headline",
             "subhead": "The line under the headline", "video-frame": "The founder video"}
    h1_text = ((facts.get("h1Box") or {}).get("text") or "").strip()
    for where, rows_here in grouped.items():
        worst = "high" if any(x["status"] == "FAIL" for x in rows_here) else "medium"
        if len(rows_here) == 1:
            add(worst, rows_here[0]["name"], rows_here[0]["fix"],
                ANCHOR_BOX[where], _fmt(rows_here[0]["reason"], 90))
        else:
            says = " ".join(x["fix"].rstrip(".") + "." for x in rows_here)
            add(worst, TITLE.get(where, "This part of the page"), says, ANCHOR_BOX[where],
                _fmt(" · ".join(x["name"] for x in rows_here), 90))

    # 6b-ii. The line under the headline is a sentence, not a list. Bullets there make the
    #        reader do the assembling before they have been sold anything.
    sub = facts.get("subBox")
    if sub and hero:
        sub_bullets = [b for b in (facts.get("blocks") or [])
                       if b["kind"] == "bullet" and sub["top"] - 20 <= b["top"] <= sub["top"] + sub["h"] + 90]
        if len(sub_bullets) >= 2:
            add("medium", "The line under the headline is bullets",
                "This should be one sentence carrying the offer. Bullets here make them assemble "
                "the pitch themselves. Move the list further down and write the promise as a line.",
                sub, _fmt(" · ".join(b["text"] for b in sub_bullets), 70))

    # 6c-i. The nav and the footer. On a page you are paying for clicks to, every link in
    #       them is a way out that is not the call or the form (Jono, 26 September 2026).
    nav_links = facts.get("navLinks") or []
    top_bar = facts.get("topBar")
    if nav_links and top_bar:
        add("high", f"The menu has {len(nav_links)} ways off this page",
            "On a page you are paying for clicks to, the menu is the biggest leak there is. "
            "Keep the name and the phone number, drop the rest. Anyone who came from an ad "
            "should have two choices: call, or fill the form.", top_bar,
            _fmt(" · ".join(l.get("text", "") for l in nav_links), 70))
    foot_links = facts.get("footerLinks") or []
    foot_box = facts.get("footerBox")
    if len(foot_links) > 2 and not foot_box and secs:
        last = secs[-1]
        foot_box = {"top": last["top"] + last["h"] - 120, "left": last["left"], "w": last["w"], "h": 120}
    if len(foot_links) > 2 and foot_box:
        social = [l for l in foot_links if re.search(r"youtube|instagram|tiktok|linkedin|facebook|twitter|x\.com", (l.get("href", "") + l.get("text", "")), re.I)]
        add("high", f"The footer has {len(foot_links)} more ways off this page",
            ("Social links send people to a feed they will not come back from. " if social else "")
            + "Leave one legal line - terms, privacy, and your phone number. Nothing else.",
            foot_box, _fmt(" · ".join(l.get("text", "") for l in foot_links), 70))

    # 6c-ii. A video hosted on YouTube keeps its own exits: the logo, the channel, related
    #        videos at the end. On a lead-gen page, host it yourself.
    yt = [i for i in (facts.get("iframes") or []) if i.get("provider") in ("youtube", "vimeo") and i.get("top") is not None]
    if yt:
        add("medium", f"{len(yt)} video{'s' if len(yt) > 1 else ''} played from YouTube",
            "A YouTube embed carries its own exits - the logo, the channel name, related videos "
            "when it ends. Host the file yourself with a poster frame so the only way out is "
            "your form.", yt[0], _fmt(yt[0].get("src", "")))

    # 6c-iii-a. Stat tiles, read one by one. A figure someone could go and check is the
    #           cheapest proof on a page, and it deserves to be named as good.
    stats = [b for b in (facts.get("blocks") or []) if b["kind"] == "stat"]
    if stats:
        box = {"top": min(b["top"] for b in stats), "left": min(b["left"] for b in stats),
               "w": max(b["left"] + b["w"] for b in stats) - min(b["left"] for b in stats),
               "h": max(b["top"] + b["h"] for b in stats) - min(b["top"] for b in stats)}
        checkable = [b for b in stats if re.search(r"subscriber|member|client|customer|job|review|year|"
                                                   r"business|coached|built|sold|lead|follower", b["text"], re.I)]
        if len(checkable) >= max(2, len(stats) // 2):
            add("good", f"{len(stats)} numbers anyone could check",
                "This is the cheapest proof on the page: each one is a figure someone can verify, "
                "and together they say you have done it yourself. Keep them where they are.",
                box, _fmt(" · ".join(b["text"] for b in stats), 80), lead=1)
        elif len(stats) >= 2:
            # only worth raising when SEVERAL figures are unlabelled - a single one that
            # read as bare is far more likely to be a reading failure than a page failure
            add("low", f"{len(stats)} numbers without a label showing",
                "A figure proves something when it says what it counts. Check these read as "
                "'1,000+ events a year' rather than just the number - if they already do, "
                "ignore this.", box, _fmt(" · ".join(b["text"] for b in stats), 80))

    # 6c-iv. Both ways to get in touch, judged SECTION BY SECTION. Someone reading a section
    #        should be able to call or enquire from where they are - but a number in the
    #        subhead counts, it does not have to sit against the button (Jono, 27 Sep 2026).
    tel_tops = [t["top"] for t in (facts.get("tel") or []) if t.get("top") is not None]
    for sec in secs:
        if _is_row(sec, secs):
            continue  # judge the section, not each row inside it
        sec_ctas = [c for c in (facts.get("ctas") or [])
                    if c.get("top") is not None and sec["top"] <= c["top"] < sec["top"] + sec["h"]]
        if not sec_ctas:
            continue
        has_tel = any(sec["top"] <= t < sec["top"] + sec["h"] for t in tel_tops)
        if not has_tel:
            add("medium", "No way to call from this section",
                "There is a button here but no phone number. Some people will never fill a form "
                "and some will never ring - put the number somewhere in this section so both are "
                "one tap away.", sec, _fmt(sec.get("heading", "")))

    # 6c-v. The proof that is already there, named as good.
    logo_sec = next((x for x in secs if re.search(r"trusted|as seen|featured|clients|partners|brands", (x.get("heading") or ""), re.I)), None)
    if logo_sec:
        logos = [i for i in (facts.get("images") or [])
                 if i.get("top") is not None and logo_sec["top"] <= i["top"] < logo_sec["top"] + logo_sec["h"]]
        if len(logos) >= 4:
            add("good", f"{len(logos)} recognisable logos", 
                "A wall of brands people already know does the arguing for you - it borrows their "
                "credibility before you have said a word. Keep it high on the page.", logo_sec, lead=1)

    vids = [v for v in (facts.get("iframes") or []) + (facts.get("videos") or [])
            if v.get("top") is not None and (v.get("provider") in ("youtube", "vimeo") or v.get("kind") == "video")]
    # Only videos whose TRANSCRIPT shows a customer speaking count as testimonials. A founder
    # video is not a testimonial however high it sits, and two frames on a page prove nothing.
    _client_n = sum(1 for k in _kinds if k["kind"] == "client")
    _founder_n = sum(1 for k in _kinds if k["kind"] == "founder")
    if _kinds and _client_n >= 2:
        vids = vids[:_client_n] if len(vids) > _client_n else vids
    elif _kinds:
        vids = []
    if len(vids) >= 2:
        box = {"top": min(v["top"] for v in vids), "left": min(v["left"] for v in vids),
               "w": max(v["left"] + v["w"] for v in vids) - min(v["left"] for v in vids),
               "h": max(v["top"] + v["h"] for v in vids) - min(v["top"] for v in vids)}
        add("good", f"{len(vids)} clients on camera",
            "Video testimonials are the single strongest proof you can put on a page - a face and "
            "a voice are believed in a way written words are not. Most businesses never get these. "
            "Keep them.", box, lead=1)

    # ALWAYS speak to both video slots. Present, and it is called out as a strength. Absent,
    # and it is called out as the gap it is. Silence on either one is not an option - the two
    # highest-trust assets on any page do not get skipped because nothing tripped a rule.
    if _kinds:
        if _founder_n and _founder_box:
            _fk = next((x for x in _kinds if x["kind"] == "founder"), {})
            add("good", "You are on camera",
                "A founder video is the fastest trust you can buy and almost nobody makes one - "
                f"{_fk.get('why', 'the transcript shows you speaking for the business')}. "
                "Keep it above the fold and under about sixty seconds.", _founder_box, lead=1)
        elif not _founder_n:
            add("high", "No founder video",
                "Nobody has seen your face. Thirty to sixty seconds on a phone - who you are, why "
                "you do this, and the promise this page makes - outperforms any amount of copy "
                "about how much you care.", None, part="1. Founder video", lead=0)
        if not _client_n:
            add("high", "No client on camera",
                "Written reviews are read as marketing. A face and a voice are not. Ask three happy "
                "clients for a phone video: what was broken, what happened, what changed.",
                tst_sec or quote_box, part="6. Video testimonials", lead=0)

    qb = facts.get("quoteBlocks") or []
    if len(qb) >= 6:
        box = {"top": min(q["top"] for q in qb), "left": min(q["left"] for q in qb),
               "w": max(q["left"] + q["w"] for q in qb) - min(q["left"] for q in qb),
               "h": max(q["top"] + q["h"] for q in qb) - min(q["top"] for q in qb)}
        add("good", f"{len(qb)} written reviews",
            "Volume is its own argument here - nobody fakes this many. Keep them, and make sure "
            "each one names the person and what actually happened.", box, lead=1)

    # 6d. Under each CTA: how fast you answer, and that it costs nothing. Said once, on the
    #     first bare button, because the fix is the same everywhere.
    REASSURE = re.compile(r"\b(?:\d+\s*(?:second|minute|hour|min)|same day|within|free|no card|no obligation|today|straight away|right away)\b", re.I)
    ctas = facts.get("ctaReassure") or []
    first_screen = (hero["top"] + min(vph, hero["h"])) if hero else vph
    below = [c for c in ctas if c["top"] >= first_screen]
    bare = [c for c in below if not REASSURE.search(c.get("under", "") or "")]
    if bare and len(bare) >= max(2, len(below) // 2):
        add("medium", f"Nothing under {len(bare)} of your buttons",
            "Put one line under each of these: how fast you answer and that it costs nothing. "
            "'We answer in about 60 seconds. Free, and yours to keep.' Leave the buttons in the "
            "first screen alone - there is already enough competing for attention up there.",
            bare[0], _fmt(bare[0].get("text", "")))

    # 6e-i. A framed slot with nothing in it.
    for sl in (facts.get("emptySlots") or []):
        label = re.sub(r"[\[\]]", "", (sl.get("text") or "")).strip()
        what = label.lower() if label else "this slot"
        title = f"Empty slot: {label}" if label else "This slot is empty"
        add("high", title,
            f"Nothing is in it. Either fill {what} or take the frame out - "
            "a gap in a row of three reads as a job half done.", sl, _fmt(sl.get("text", "")))

    # 6e. The same picture used more than once. Grouped into ONE pin per area - seven pins
    #     saying the same sentence is not seven findings (Jono, 27 September 2026). A
    #     carousel repeating its own slides is normal and is not reported at all.
    reps = [r for r in (facts.get("repeatedImages") or []) if r.get("top") is not None]
    if reps:
        # which section each repeat lives in
        def _sec_of(top):
            for x in secs:
                if x["top"] <= top < x["top"] + x["h"]:
                    return x["i"]
            return -1

        by_sec = {}
        for r in reps:
            spans = {_sec_of(t) for t in (r.get("tops") or [r["top"]])}
            r["_spans"] = len(spans)
            by_sec.setdefault(_sec_of(r["top"]), []).append(r)
        for sec_i, group in by_sec.items():
            # a carousel loops its own slides inside one block, so only its own images
            # repeat. Anything appearing in more than one section is a real repeat.
            spanning = [r for r in group if r.get("_spans", 1) >= 2]
            if not spanning:
                continue  # everything here loops inside this block: a carousel
            group = spanning
            host = next((x for x in secs if x["i"] == sec_i), None)
            box = host or group[0]
            n = len(group)
            times = max((r.get("count") or 2) for r in group)
            add("low",
                "The same picture is used twice" if n == 1 else f"{n} pictures are used more than once",
                f"One of these appears {times} times on the page. Repeating a picture makes the page "
                "feel thinner than it is - if it is a logo or an icon that is fine, but a photo of "
                "work or a person should only appear once.", box,
                _fmt(" · ".join(r["src"].rsplit("/", 1)[-1] for r in group), 70))

    # 6f. A bar at the top eating the first screen.
    tb = facts.get("topBar")
    if tb and tb.get("share", 0) >= 12:
        add("medium", f"The top bar takes {tb['share']}% of the first screen",
            "On an ad page the bar only needs the name and the phone number. "
            "Every pixel it takes is a pixel the promise does not get.", tb, _fmt(tb.get("text", "")))

    # 7. Claude's own per-section and per-image calls. These are the ones that need a human
    #    eye: whether the copy sells, whether a photo is really theirs. Good ones are pinned
    #    too, in green, so the owner knows what to keep.
    j = facts.get("_judgments") or {}
    # a machine heading note is dropped when the section it sits in already carries a
    # judged verdict - that verdict names the actual replacement line.
    judged_secs = {str(k) for k, v in ((j.get("sections") or {}).items()) if v.get("verdict")}
    # a section judged good never carries a machine complaint about its own heading
    good_secs = {str(k) for k, v in ((j.get("sections") or {}).items()) if v.get("verdict") == "good"}
    if good_secs:
        drop_good = []
        for p in pins:
            if p["severity"] == "good":
                continue
            for sec in secs:
                if str(sec["i"]) in good_secs and sec["top"] <= p["box"]["top"] < sec["top"] + sec["h"] \
                        and "earn a click" in p["title"]:
                    drop_good.append(id(p))
                    break
        pins = [p for p in pins if id(p) not in drop_good]
    if judged_secs:
        drop = []
        for p in pins:
            rule = p.get("rule") or ""
            if not rule.startswith("heading-"):
                continue  # any heading rule, whatever it is called
            for sec in secs:
                if sec["top"] <= p["box"]["top"] < sec["top"] + sec["h"] and str(sec["i"]) in judged_secs:
                    drop.append(id(p))
                    break
        pins = [p for p in pins if id(p) not in drop]

    SEV_OF = {"bad": "high", "weak": "medium", "good": "good"}
    ELEMENT = {"headline": facts.get("h1Box"), "h1": facts.get("h1Box"),
               "subhead": facts.get("subBox"), "subheadline": facts.get("subBox")}
    for key, v in (j.get("sections") or {}).items():
        if not v.get("verdict") or not v.get("says"):
            continue
        sec = next((x for x in secs if str(x["i"]) == str(key)), None)
        if not sec:
            continue
        # a verdict about one element boxes that element, never the section around it
        el = ELEMENT.get((v.get("about") or "").lower().strip())
        if el and el.get("top") is not None:
            add(SEV_OF.get(v["verdict"], "medium"),
                "The headline" if el is facts.get("h1Box") else "The line under the headline",
                v["says"], el, part="18. Copy")
            continue
        title = (sec.get("heading") or "").strip() or v.get("heading", "").strip()
        h1t = ((facts.get("h1Box") or {}).get("text") or "").strip()
        if not title or (h1t and title[:28] == h1t[:28]):
            title = "The copy in the first screen" if sec.get("top", 1) < 400 else "The copy in this section"
        else:
            title = "The copy: " + title
        add(SEV_OF.get(v["verdict"], "medium"), title, v["says"], sec, part="18. Copy")
    # per-question verdicts, pinned to the question itself
    faq_qs = facts.get("faq") or []
    for key, v in (j.get("faq") or {}).items():
        if not v.get("verdict") or not v.get("says"):
            continue
        try:
            idx = int(key.split("-")[1])
        except (ValueError, IndexError):
            continue
        if idx >= len(faq_qs):
            continue
        add(SEV_OF.get(v["verdict"], "medium"), _fmt(faq_qs[idx].get("q", "This question"), 46),
            v["says"], faq_qs[idx], part="FAQ", lead=2)

    # per-video verdicts, pinned to the embed they are about
    frames = [x for x in (facts.get("iframes") or []) + (facts.get("videos") or []) if x.get("top") is not None]
    frames.sort(key=lambda x: x["top"])
    for key, v in (j.get("videos") or {}).items():
        if not v.get("verdict") or not v.get("says"):
            continue
        try:
            idx = int(key.split("-")[1])
        except (ValueError, IndexError):
            continue
        if idx >= len(frames):
            continue
        secs_txt = f' ({v["seconds"]}s)' if v.get("seconds") else ""
        # WHICH video this is comes from its transcript. Position is not evidence.
        _k = next((x for x in _kinds if x["index"] == idx), None)
        _kind = (_k or {}).get("kind") or "unknown"
        _title = {"founder": "The founder video", "client": "This client video",
                  "explainer": "This explainer video",
                  "unknown": "This video (transcript unread)"}[_kind]
        _part = {"founder": "1. Founder video", "client": "6. Video testimonials",
                 "explainer": "6. Video testimonials",
                 "unknown": "6. Video testimonials"}[_kind]
        add(SEV_OF.get(v["verdict"], "medium"), _title + secs_txt,
            v["says"], frames[idx], part=_part, lead=1)

    imgs = facts.get("images") or []
    by_src = {}
    for im in imgs:
        by_src.setdefault((im.get("src") or "").split("?")[0], []).append(im)
    for key, v in (j.get("images") or {}).items():
        if not v.get("verdict") or not v.get("says"):
            continue
        targets = by_src.get((v.get("src") or "").split("?")[0], [])
        if not targets:
            # no src recorded (an older judgments file): fall back to position, but only
            # when the two lists are the same length, so a verdict never lands on the wrong photo
            try:
                idx = int(key.split("-")[1])
            except (ValueError, IndexError):
                continue
            if len(imgs) != len(j.get("images") or {}) or idx >= len(imgs):
                continue
            targets = [imgs[idx]]
        for im in targets:
            add(SEV_OF.get(v["verdict"], "medium"), "This photo", v["says"], im, part="16. Real photos")

    # 8. the form, if it is asking too much or asking the wrong things
    if form.get("top") is not None:
        fields = [f for f in (form.get("fields") or []) if f.get("visible")]
        hard = [f for f in fields if re.search(r"zip|postcode|postal|account|policy|reference", (f.get("name", "") + f.get("label", "")), re.I)]
        if len(fields) > 6:
            add("medium", f"The form asks {len(fields)} things",
                "Cut it to name, phone, email and one question. Every extra field loses people.", form)
    if form.get("top") is not None:
        for uf in (form.get("urlFields") or []):
            ph_ = (uf.get("placeholder") or "").strip()
            if uf.get("demandsProtocol") or ph_.startswith(("http://", "https://")):
                add("medium", "The website field makes them type https://",
                    "Accept 'example.com' and add the https:// yourself. Nobody should have to "
                    "type boilerplate to enquire.", form, _fmt(ph_ or uf.get("name", "")))
        fields = [x for x in (form.get("fields") or []) if x.get("visible")]
        hard = [x for x in fields if re.search(r"zip|postcode|postal|account|policy|reference", (x.get("name", "") + x.get("label", "")), re.I)]
        for f in hard:
            add("medium", f'"{_fmt(f.get("label") or f.get("name"), 30)}" is hard to answer',
                "People do not always know it off the top of their head. Ask on the call instead.", form)

    # A group box that only repeats the pins inside it is dropped: a row of four placeholder
    # photos with a verdict on each photo does not also need a box round the row.
    judged_boxes = [p["box"] for p in pins if p.get("part") == "16. Real photos"]
    if judged_boxes:
        # a label sitting inside a judged photo says nothing the photo's own verdict does not
        pins = [p for p in pins
                if p.get("part") == "16. Real photos" or p.get("lead", 2) < 2
                or not any(p["box"]["top"] >= k["top"] - 4 and p["box"]["top"] + p["box"]["h"] <= k["top"] + k["h"] + 4
                           and p["box"]["left"] >= k["left"] - 4 and p["box"]["left"] + p["box"]["w"] <= k["left"] + k["w"] + 4
                           for k in judged_boxes)]
        judged_boxes = [p["box"] for p in pins if p.get("part") == "16. Real photos"]
        kept = []
        for p in pins:
            b = p["box"]
            inside = [k for k in judged_boxes
                      if k["top"] >= b["top"] - 8 and k["top"] + k["h"] <= b["top"] + b["h"] + 8
                      and k["left"] >= b["left"] - 8 and k["left"] + k["w"] <= b["left"] + b["w"] + 8]
            if p.get("part") in ("16. Real photos", "18. Copy"):
                kept.append(p)
                continue
            # a box that only repeats the judged photos it spans. Either it wraps them, or
            # it is a thin label row drawn across the same columns.
            spans = [k for k in judged_boxes
                     if k["left"] < b["left"] + b["w"] and k["left"] + k["w"] > b["left"]
                     and k["top"] < b["top"] + b["h"] + 400 and k["top"] + k["h"] + 400 > b["top"]]
            if len(spans) >= 2 and max(k["top"] for k in spans) - min(k["top"] for k in spans) < 40:
                cols = sorted(k["left"] for k in spans)
                wide_enough = (max(cols) + 40) >= (b["left"] + b["w"]) * 0.75
                if wide_enough:
                    continue
            kept.append(p)
        pins = kept

    # One box, one problem. A pin that sits inside a pin already kept is dropped, so a
    # placeholder frame with a play button drawn on it does not get marked twice.
    pins.sort(key=lambda p: (p.get("lead", 2), ORDER[p["severity"]], p["box"]["top"]))
    keep = []
    for p in pins:
        b = p["box"]
        clash = False
        for k in keep:
            kb = k["box"]
            over_v = min(b["top"] + b["h"], kb["top"] + kb["h"]) - max(b["top"], kb["top"])
            over_h = min(b["left"] + b["w"], kb["left"] + kb["w"]) - max(b["left"], kb["left"])
            if over_v > 0 and over_h > 0:
                # only merge boxes that are essentially the SAME element. A big section box
                # (a missing component pinned to the hero) must never swallow the small
                # findings that sit inside it - those are separate jobs.
                if (p["severity"] == "good") != (k["severity"] == "good") and not (
                    b["top"] == kb["top"] and b["left"] == kb["left"]
                    and b["w"] == kb["w"] and b["h"] == kb["h"]):
                    continue  # a verdict and a fix on different spots are different messages
                a1, a2 = b["w"] * b["h"], kb["w"] * kb["h"]
                overlap = over_v * over_h
                if overlap / (min(a1, a2) or 1) > 0.6 and min(a1, a2) / (max(a1, a2) or 1) > 0.5:
                    clash = True
                    break
        if not clash:
            keep.append(p)
        else:
            # same spot: fold the dropped message into the one already there
            host = next((k for k in keep if _same_spot(k["box"], b)), None)
            # A COPY verdict always leads its own section. "No phone number here" is a detail
            # inside the section; letting it take the title buried the single best line on
            # a DJ site ("50 DJs out of 5,000+") as sub-text (Jono, 27 Sep 2026).
            if host and p.get("part") == "18. Copy" and host.get("part") != "18. Copy":
                host["says"], p["says"] = p["says"], host["says"]
                host["title"], p["title"] = p["title"], host["title"]
                host["severity"], host["part"] = p["severity"], "18. Copy"
                if p["says"]:
                    host.setdefault("more", []).append(p["says"])
                continue
            if host and host.get("part") == "18. Copy" and p.get("part") != "18. Copy":
                if p["says"] and p["says"].lower()[:40] not in (host["says"] or "").lower():
                    host.setdefault("more", []).append(p["says"])
                continue
            # the bigger finding leads. A missing component outranks a note about the
            # picture standing in for it.
            if host and (p.get("lead", 2), ORDER[p["severity"]]) < (host.get("lead", 2), ORDER[host["severity"]]):
                host["says"], p["says"] = p["says"], host["says"]
                host["title"], p["title"] = p["title"], host["title"]
                host["severity"] = p["severity"]
            said = (host["says"] + " " + " ".join(host.get("more", []))).lower() if host else ""
            if host and p["says"] and p["says"].lower()[:40] not in said:
                host.setdefault("more", []).append(p["says"])
                host["title"] = _place_name(host["box"], facts, host["title"])
                if host.get("part") != "18. Copy":
                    host["part"] = ""  # the label belonged to one message, not the merged pin
                if ORDER[p["severity"]] < ORDER[host["severity"]] and host["severity"] != "good":
                    host["severity"] = p["severity"]
    # Two pins about the same thing in the same place are one finding. Compare the words
    # of the advice, not the titles - the same sentence twice is the tell.
    def _words(x):
        return set(re.findall(r"[a-z]{5,}", (x.get("says") or "").lower()))

    # Same message in several places: every box stays, and they share one entry in the list.
    # "sections 8, 9, 10 say the same thing" is the useful form of this - deleting four of
    # them was not (Jono, 27 Sep 2026).
    groups = []
    for p in keep:
        lead_of = None
        for g in groups:
            q = g[0]
            a, b_ = _words(p), _words(q)
            if not a or not b_:
                continue
            if len(a & b_) / max(1, min(len(a), len(b_))) > 0.8 and p.get("part") == q.get("part"):
                lead_of = g
                break
        if lead_of is None:
            groups.append([p])
        else:
            lead_of.append(p)
    for g in groups:
        if len(g) < 2:
            continue
        head, rest = g[0], g[1:]
        # name each PLACE once. "What we do, What we do, What we do" is noise; the useful
        # form is the list of distinct sections plus a count (Jono, 27 Sep 2026).
        seen_spot, spots = set(), []
        for x in g[1:]:
            nm = _place_name(x["box"], facts, "") or ""
            if not nm or nm in seen_spot:
                continue
            seen_spot.add(nm)
            spots.append(nm)
        head["also_at"] = spots[:5]
        head["also_more"] = max(0, len(g) - 1 - len(spots[:5]))
        head["group_n"] = len(g)
        for x in rest:            # still boxed, still numbered, but listed with the first
            x["grouped_into"] = id(head)
            x["says"] = ""        # the words are said once, on the entry that leads

    # No deletion pass here any more. Grouping above is the whole dedupe: a repeated message
    # is said once in the list and every one of its boxes stays on the page.
    keep.sort(key=lambda p: p["box"]["top"])
    facts["_unlocated"] = unlocated
    return keep


