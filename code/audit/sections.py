"""What KIND of section is this, and what does that kind have to answer for?

Why this exists (Jono, 27 September 2026): the audit only spoke about a section when
something tripped a rule, so whole bands of a page went uncommented and the owner could
not tell "nothing wrong here" from "not looked at". Every section now gets a type, and
each type carries a fixed checklist. A body section is always asked whether you can call
from it, whether there is a picture, whether there is proof, and whether the copy reaches
an outcome - whether or not anything looked broken.

The checklist is a prompt, not a score. Claude answers it from the section screenshot and
writes one verdict per section. Nothing is skipped because nothing looked broken.
"""

import re

# Every type, in the order they usually appear, with what that kind of band must answer for.
# "ask" is what the judgement has to cover. "not_expected" keeps a checklist honest - asking
# a logo carousel for bullet points is the kind of noise that made the report feel generic.
TYPES = {
    "hero": {
        "label": "the first screen",
        "want": ["a line above the headline naming the pain - 'Tired of waiting days for a call back?'",
                 "a headline with the service and the city, or the solution",
                 "a subheadline carrying the offer and the guarantee",
                 "outside trust - two or three review badges (Google, Facebook, Trustpilot, TrustIndex) with the stars and the count, and real faces",
                 "three bullets",
                 "a form button AND a phone number, so either way is one tap"],
        "ask": ["Is there a line above the headline that names the worry they arrived with?",
                "Does the headline say the service and the place, or what they get?",
                "Does the subheadline carry the offer and the guarantee?",
                "Is there proof in this screen - a rating with its count, real faces, a number?",
                "Are there three bullets, and do they reach an outcome?",
                "Can they submit the form AND call from here?",
                "Is the picture or video of the real thing, not a stock shot?"],
        "not_expected": [],
    },
    "body": {
        # Jono, 28 Sep 2026: one side carries the words and the ask, the other side shows something
        "label": "a selling section",
        "want": ["a headline that says what they get",
                 "one short paragraph",
                 "three to five bullets: feature, so you get the benefit, which means the outcome",
                 "both buttons: the form and a phone number to tap",
                 "a line on how fast you reply: 'We reply in 75 seconds'",
                 "a touch of proof: a review badge, a one-line client quote with a face, or a number",
                 "on the other side: a picture, a video, or social proof"],
        "ask": ["Does the headline say what they get, rather than label the section?",
                "Is there one short paragraph, not three?",
                "Are the points bullets, and does each run feature, benefit, outcome?",
                "Can they act from here - the form button AND a phone number?",
                "Does it say how fast you reply?",
                "Is there proof beside the words: a badge, a quote with a face, a number?",
                "Is there a picture, video or proof on the other side, or is it a wall of words?",
                "Would anything be lost if this section went?"],
        "not_expected": [],
    },
    "proof_logos": {
        "label": "a logo strip",
        "want": ["a heading saying what the logos mean", "the logos themselves"],
        "ask": ["Are these brands people recognise?",
                "Does a line above it say what the logos mean - worked with, trusted by, supplied to?",
                "Does it loop its own slides, so someone sees two of fifteen and moves on?"],
        "not_expected": ["bullets", "button"],
    },
    "proof_quotes": {
        "label": "written reviews",
        "want": ["a title", "about nine written reviews, each with a name and a face"],
        "ask": ["Does each review carry a name and a real face, not initials in a circle?",
                "Do they name the job, the event or the result, or are they 'great service, thanks'?",
                "Is the platform shown with the stars drawn and the score - '4.9 from 214'?",
                "Is there a button at the end of the block, once, for the section?"],
        "not_expected": ["bullets"],
    },
    "proof_video": {
        "label": "clients on camera",
        "want": ["a title", "up to nine client videos"],
        "ask": ["Is it a client speaking, or is it the owner? The transcript says which.",
                "Does each one say what was broken, what happened, and what changed?",
                "Is it self-hosted with a poster frame, or does a YouTube embed offer its own exits?",
                "Three is plenty and nine stops helping - how many are here?"],
        "not_expected": ["bullets"],
    },
    "founder_video": {
        "label": "you on camera",
        "want": ["a title", "the video, under about 60 seconds", "a real poster frame of you"],
        "ask": ["Does it say who you are, why you do this, and the promise this page makes?",
                "Is it under about sixty seconds?",
                "Is the still behind the play button you, looking at the camera?"],
        "not_expected": ["bullets", "button"],
    },
    "stats": {
        "label": "a stats bar",
        "want": ["three or four numbers: years in business, reviews and the score, jobs completed, clients served",
                 "a short label under each number"],
        "ask": ["Are there three or four numbers, each one something a buyer can check?",
                "Is each number labelled in plain words, not a bare figure?",
                "Does it sit near the top, where it helps the decision?"],
        "not_expected": ["bullets", "button"],
    },
    "form": {
        "label": "the form",
        "want": ["a title", "a short body paragraph", "bullets", "the form itself",
                 "a lead magnet with a picture of it", "a risk reversal or guarantee",
                 "review badges beside it - Google, Facebook, Trustpilot or TrustIndex, with the stars and the count",
                 "a phone number as well as the button"],
        "ask": ["How many fields, and is every one of them needed to call someone back?",
                "Are first and last name separate, so your emails and texts work?",
                "Is the phone field a phone input, so the number pad comes up on a mobile?",
                "Is there a line under the button saying how fast you answer and that it costs nothing?",
                "Can they call instead of filling it in?",
                "Is there anything beside the form that makes it worth the trouble?"],
        "not_expected": [],
    },
    "faq": {
        "label": "the questions",
        "want": ["a title", "at least six questions, each answering a reason someone would not enquire"],
        "ask": ["Are these the worries people have BEFORE they enquire - price, timing, risk, what happens next?",
                "Does every answer actually open and show on the page?",
                "Does each answer remove the doubt, or repeat it back?",
                "Is there one button, or a phone number, at the end of the block?",
                "Which obvious question is missing?"],
        "not_expected": ["bullets", "image"],
    },
    "steps": {
        "label": "how it works",
        "ask": ["Is it three or four steps, and does the last one say what they get?",
                "Does it say what happens after they enquire, and how fast?",
                "Is there a button at the end of it?"],
        "not_expected": [],
    },
    "pricing": {
        "label": "prices",
        "ask": ["Is there a real number, or does it say 'contact us for pricing'?",
                "Is what is included spelled out, so nobody has to ask?",
                "Is there a guarantee beside it - what happens if it does not work?"],
        "not_expected": [],
    },
    "nav": {
        "label": "the bar at the top",
        "ask": ["Is the phone number in it, tappable?",
                "How many links lead away from this page?"],
        "not_expected": ["bullets", "image", "proof"],
    },
    "footer": {
        "label": "the footer",
        "ask": ["Is it one legal line, or a second menu offering ways out?"],
        "not_expected": ["bullets", "image", "proof"],
    },
    "gallery": {
        "label": "the work",
        "ask": ["Is this your own work, or stock?",
                "Does a caption say what it was - the venue, the job, the result?",
                "Is there a button under it?"],
        "not_expected": ["bullets"],
    },
    "other": {
        "label": "this band",
        "ask": ["What is this section for, and would anything be lost if it went?",
                "Is there a way to act from it?",
                "Is there a picture or a number in it, or only words?"],
        "not_expected": [],
    },
}

_H = {
    "faq": r"frequently asked|faqs?\b|common questions|questions",
    "form": r"get a quote|get a free|request a|book a|contact us|get in touch|enquir|inquir|"
            r"free quote|no risk|get started",
    "pricing": r"pricing|prices|packages|how much|rates|investment",
    "steps": r"how it works|how we work|the process|our process|what happens|three steps|step 1",
    "proof_video": r"video testimonial|watch (?:our|what)|on camera|in their own words",
    "proof_quotes": r"testimonial|reviews?|what (?:our|some of our) clients|clients (?:say|have said)|"
                    r"love us|hear from|kind words",
    "proof_logos": r"trusted by|as seen (?:in|on)|featured in|our clients|brands|partners|worked with",
    "gallery": r"gallery|portfolio|our work|recent (?:work|jobs|events)|case stud",
}


def classify(sec, facts, index_in_page=0, video_kinds=None):
    """The section's type, from its heading, its shape and what sits inside it."""
    head = (sec.get("heading") or "").strip()
    low = head.lower()
    top, h = sec.get("top") or 0, sec.get("h") or 0
    words = sec.get("words") or 0
    vp_h = ((facts.get("viewport") or {}).get("h")) or 844

    # The bar at the top is known by its BOX. This runs before the hero rule, because the
    # first section on the page is usually the header, not the hero - a B2B site's band 0
    # is a 128px nav bar that typed as "hero" and left the real hero at 129px unspoken
    # (Jono, 27 Sep 2026).
    bar = facts.get("topBar") or {}
    if bar and bar.get("top") is not None and h:
        same_top = abs(top - bar["top"]) < 8
        same_h = abs(h - (bar.get("h") or 0)) < 24
        if same_top and (same_h or h <= max(140, vp_h * 0.25)):
            return "nav"
    # a short band at the very top full of menu links is a header whatever its class names say
    if top < 8 and h and h <= max(160, vp_h * 0.22) and words < 40:
        return "nav"
    # A footerBox taller than half the page is a detection failure, not a footer. Trusting one
    # typed all 18 a B2B site sections as "footer" (Jono, 27 Sep 2026).
    foot = facts.get("footerBox") or {}
    page_h = facts.get("scrollHeight") or 0
    if foot and foot.get("top") is not None and (not page_h or (foot.get("h") or 0) <= page_h * 0.5) \
            and top >= foot["top"] - 4:
        return "footer"
    # The hero is the first real band of CONTENT. If a nav bar sits above it, the hero starts
    # where the bar ends - so "first section on the page" is the wrong test.
    bar_h = (bar.get("h") or 0) if (bar and bar.get("top") is not None and bar["top"] < 8) else 0
    if top <= bar_h + 12 and top < vp_h and words >= 8:
        return "hero"

    # The HEADING wins. It is what the owner sees and what the section announces itself as.
    # Content-sniffing only runs when there is no heading to go on.
    for kind, rx in _H.items():
        if low and re.search(rx, low):
            return kind
    # three or more figures in a short band with few words is a stats bar
    figs = re.findall(r"\d[\d,.]*\s?(?:%|\+|k\b|x\b)?", " ".join(t["text"] for t in (facts.get("textAt") or [])
                                                         if t.get("top") is not None and top <= t["top"] < top + max(h, 1)))
    if len(figs) >= 3 and words < 40 and h < 450:
        return "stats"
    # A form inside the band makes it the form section, whatever its heading says. The
    # a photography site quote section typed as "body" when this ran after the words rule.
    if any(f.get("top") is not None and top <= f["top"] < top + max(h, 1) for f in (facts.get("forms") or [])):
        return "form"

    # a video in this band: which kind depends on the transcript, never the position
    frames = [v for v in (facts.get("iframes") or []) + (facts.get("videos") or []) + (facts.get("videoWidgets") or [])
              if v.get("top") is not None and top <= v["top"] < top + max(h, 1)]
    if frames and words < 120:
        kinds = {k["kind"] for k in (video_kinds or []) if
                 any(abs((k.get("top") or -1) - f["top"]) < 4 for f in frames)}
        if "founder" in kinds:
            return "founder_video"
        if "client" in kinds:
            return "proof_video"
        # Several frames and almost no words is a testimonial wall. a photography site ships nine
        # of them as rows with no text at all, and they typed as "other" (Jono, 27 Sep 2026).
        if len(frames) >= 2:
            return "proof_video"
    pics = [i for i in (facts.get("images") or []) if i.get("top") is not None
            and top <= i["top"] < top + max(h, 1) and (i.get("w") or 0) * (i.get("h") or 0) >= 12000]
    if len(pics) >= 8 and h >= 600 and words < 90:
        return "gallery"
    # A heading that reads like a selling section IS one, even if a quote or a picture sits in
    # its box. "All In One Solution" typed as written-reviews because two quote blocks fell
    # inside it (Jono, 27 Sep 2026).
    if low and words >= 25:
        return "body"
    # a band of nothing but pictures, in a run of identical bands, is a grid of something -
    # judge it as work shown, not as an unknown.
    if words < 8 and h and h < 400:
        imgs_here = [i for i in (facts.get("images") or []) if i.get("top") is not None
                     and top <= i["top"] < top + max(h, 1)]
        if len(imgs_here) >= 3:
            return "gallery"

    # no heading to go on: read what is inside the band
    forms = [f for f in (facts.get("forms") or []) if f.get("top") is not None
             and top <= f["top"] < top + max(h, 1)]
    if forms:
        return "form"
    qb = [q for q in (facts.get("quoteBlocks") or []) if q.get("top") is not None
          and top <= q["top"] < top + max(h, 1)]
    if len(qb) >= 2:
        return "proof_quotes"
    imgs = [i for i in (facts.get("images") or []) if i.get("top") is not None
            and top <= i["top"] < top + max(h, 1)]
    if len(imgs) >= 5 and words < 40:
        return "proof_logos"
    if words >= 25:
        return "body"
    return "other"


def checklist(kind):
    """(questions, label, not_expected, want) - `want` is what this kind of section is
    made of, so a verdict can name the missing part rather than only judge what is there."""
    t = TYPES.get(kind) or TYPES["other"]
    return t["ask"], t["label"], t.get("not_expected", []), t.get("want", [])
