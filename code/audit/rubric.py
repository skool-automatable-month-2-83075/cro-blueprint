"""The rubric: 100 points, a grade out of 10, every item with a measure and a fix.

Three kinds of item. MACHINE is scored here from the capture, assets, speed and tracking data. JUDGED is scored by
Claude (0, 1 or 2) from the screenshots, contact sheets and transcripts, handed in as judgments.json. BUSINESS
items apply or not, or weigh differently, by the business model in context/business.md. Items that do not apply
leave the denominator, so a SaaS page is never docked for a missing licence line.

    python3 -m audit.rubric --write-reference     # regenerates references/audit-rubric.md from ITEMS, so the two never drift

Grade: 90 or more is a 10-out-of-10 candidate, and only when no Proof, Conversion path or Tracking item is a FAIL.
"""
import json
import os
import re
import sys

from .common import ROOT

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

AREAS = [("message", "Message and offer", 15), ("proof", "Proof", 25), ("path", "Conversion path", 20), ("tracking", "Tracking", 10),
         ("copy", "Copy", 10), ("design", "Design and layout", 10), ("speed", "Speed and technical", 5), ("fit", "Business fit", 5)]

# id, area, name, points, kind, what is measured, the fix when it fails, models it applies to (None = all)
ITEMS = [
    ("M1", "message", "Headline names the service and the place", 4, "JUDGED", "H1 carries what they searched and where, with continuity of meaning, not a keyword string. The keyword and the city STAY - that is the message match the ad is paying for", "Rewrite the H1 as proof word + city + service, in the buyer's words. Keep the keyword and the city whatever else changes", None),
    ("M2", "message", "The offer above the fold", 5, "JUDGED", "An 'X in Y or Z' promise sits above the fold. On an ad page it belongs in the SUBHEADLINE, because the H1 has to carry the keyword and the city for Quality Score", "Write the offer into the line under the headline: what they get, by when, or what you do if you miss. Leave the H1 to the keyword and the city", None),
    ("M3", "message", "H1 plus subhead is the whole pitch", 3, "JUDGED", "Reading only those two lines, a stranger knows what you do, for whom, and why to call", "Cut the subhead to the offer plus one proof number", None),
    ("M6", "message", "A guarantee, stated in words anyone can hold you to", 3, "JUDGED",
     "The page says what happens if it does not work - money back, a redo, you stop paying, we keep going free. Named, specific, and easy to find",
     "Write the one you would actually honour and put it beside the button: 'if you are not happy with the work, we refund the deposit'. Vague confidence is not a guarantee", None),
    ("M4", "message", "One promise, not three", 2, "JUDGED", "The fold makes one promise; competing promises or slogans are absent", "Keep the promise the ad made, move the rest below the proof", None),
    ("M5", "message", "H1 exists, short, in the first screen", 1, "MACHINE", "An H1 of 4 to 14 words whose top is inside the phone's first screen. Shorter is better, but never at the cost of the keyword or the city", "Add a real H1 above the fold. Tighten the words around the keyword and the city, never remove them", None),
    ("P1", "proof", "Founder video in the first two screens", 2, "MACHINE", "A video or provider embed within the first two phone screens", "Record 30 to 60 seconds, face to camera, why you started and the promise. Self-host it, and make the still behind the play button you, smiling, looking at the camera - never a stock photo standing in", None),
    ("P2", "proof", "The founder video says why and the promise", 2, "JUDGED", "Its transcript names the person, why they do this, and the promise the page makes", "Re-record to the script: who you are, why, the promise, one line on what happens after they call", None),
    ("P3", "proof", "Video testimonials, three or more, click to play", 3, "MACHINE", "At least three videos beyond the founder's, self-hosted, poster, no autoplay", "Ask three happy clients for a phone video; self-host with posters", None),
    ("P4", "proof", "Testimonial transcripts name a real outcome", 2, "JUDGED", "Each transcript names the job, the result and something specific, not 'great service'", "Prompt clients: what was broken, what happened, what changed - in that order", None),
    ("P5", "proof", "Written testimonials, five or more, with names", 2, "MACHINE", "Five or more review blocks with a first name", "Pull the real reviews from the profile with names and dates", None),
    ("P6", "proof", "Written testimonials are specific", 1, "JUDGED", "They name staff, jobs, numbers, dates; nothing reads generic or invented", "Swap generic quotes for ones that name the job and the result", None),
    ("P7", "proof", "Real photos, no stock, no generated faces", 2, "MACHINE", "No image from a stock or avatar host, no upscaled or generated-looking file beside a real name", "Replace every flagged image with a real photo of the team, the work, the client", None),
    ("P8", "proof", "The photos show this business", 1, "JUDGED", "From the contact sheets: the images show this team, this work, this place - not lifestyle stock", "Shoot the van, the crew, the finished job; nothing else", None),
    ("P9", "proof", "A real review score with its count", 3, "MACHINE", "A star average with the number of reviews it comes from, in the first screen. On an ad page it is NOT linked out: the only ways off the page are the call, the form, or leaving", "Show the real score and the count it comes from - '4.9 from 214 Google reviews' - with the platform named so it can be checked. No link away from the page", None),
    ("P10", "proof", "Proof badges showing the stars and the count", 1, "MACHINE", "The platform's mark with the stars drawn and the number of reviews beside it - not a bare logo", "Show the badge as people expect to see it: the platform mark, the stars filled in, the score and how many reviews it comes from", None),
    ("P11", "proof", "Licence, insurance and bond with the number", 2, "BUSINESS", "For a trade or professional: licence or insurance named with a number in the hero", "Put 'Licensed #XXXXX, insured to $Xm' in the hero tick strip", ["trade", "professional"]),
    ("P12", "proof", "Real work on show - portfolio or case studies, whichever this buyer judges on", 2, "BUSINESS", "A business judged by looking (photography, events, trades, renovation, landscaping) shows real finished work as photos or video; a business judged on outcomes shows case studies with numbers. Either way it has to be work the owner is proud of - if they would not want it seen, it will not sell", "Show the work: photos or video of real finished jobs, or two case studies with a number and a timeframe. Nothing you would not want a client to see", ["trade", "professional", "agency", "saas"]),
    ("P13", "proof", "Every number on the page has a source", 2, "MACHINE", "Every figure on the page appears in context/proof.md (our pages) - or is flagged for the owner to source", "Source it in proof.md or take it off", None),
    ("C1", "path", "A CTA above the fold on every viewport", 3, "MACHINE", "At least one call or form CTA visible in the first screen on mobile, tablet and desktop", "Put the call button and the form button in the hero, above the fold, on every screen size", None),
    ("C2", "path", "A CTA on every section on desktop", 2, "MACHINE", "On desktop, most sections with real copy carry a CTA, or four or more CTAs total", "Add a CTA band after each proof block; every one scrolls to the form", None),
    ("C3", "path", "One fixed bottom bar on mobile with call and form", 3, "MACHINE", "Exactly one fixed bar at the bottom on mobile with a tel: link and a form button; none on desktop", "Add the mobile bar; remove any second sticky element", None),
    ("C4", "path", "Every CTA dials or scrolls to the form", 1, "MACHINE", "No CTA leads to another page", "Point every button at #lead-form or tel:", None),
    ("C5", "path", "The form asks the four - first name, last name, email, phone - and little else", 3, "MACHINE", "First name, last name, email and phone all asked (half the points), 3 to 6 fields, no select, no textarea, qualifying questions as chips", "Ask all four - first name, last name, email, phone - then at most one qualifying question as chips", None),
    ("C6", "path", "Form hygiene - labels, autofill, required, phone reason, consent, honeypot, privacy", 3, "MACHINE", "Seven checks: real labels, autocomplete tokens, required marking, the line under the phone field, the consent line with 'not a condition' and STOP, a honeypot, a privacy link", "Fix each missing check; the template form has all seven", None),
    ("C7", "path", "Nothing they must look up", 1, "MACHINE", "No ZIP, postcode or account fields", "Remove the ZIP field; ask for the city in the call", None),
    ("C8", "path", "The button says the outcome", 1, "MACHINE", "Button text is an outcome, never 'Submit'", "Change it to 'Get my free quote' or the real outcome", None),
    ("C9", "path", "The thank-you page does its job", 2, "MACHINE", "/thank-you exists, noindex, no nav, a tel link, a callback time, the calendar where the model books", "Build the thank-you page from the template; put the calendar there, not on the landing page", None),
    ("C10", "path", "Three exits only", 1, "MACHINE", "No link leaves the page except privacy and terms; every other link is a leak, named in the report", "Remove the nav, the footer links and every outbound link; keep one legal line", None),
    ("T1", "tracking", "One phone number", 2, "MACHINE", "Every tel: link carries the same digits", "One number everywhere; Google's snippet or a tracking number swaps it", None),
    ("T2", "tracking", "Calls are tracked", 2, "MACHINE", "Google's phone snippet or a call-tracking script (CallRail, CTM, WhatConverts, Invoca) is on the page", "Install the Google phone snippet or a call-tracking number with dynamic insertion", None),
    ("T3", "tracking", "Taps and fields are measurable", 1, "MACHINE", "An analytics or replay tool is present so tel taps and form fields can be counted", "Add PostHog (this repo wires it) so every tap and field is measured", None),
    ("T4", "tracking", "A conversion fires once on the lead", 2, "MACHINE", "A conversion script is present; on our pages check_tracking.py proves it fires exactly once", "Fire the lead event on the form's success, never on load; verify with check_tracking.py", None),
    ("T5", "tracking", "Click ids and UTMs survive to the form", 2, "MACHINE", "After ?gclid=test the id is in a hidden field or storage, and UTMs with it", "Capture gclid and utm_* on first touch and ride them on the form as hidden fields", None),
    ("T6", "tracking", "Replay and heat maps are on", 1, "MACHINE", "PostHog, Clarity or Hotjar present", "Turn on PostHog replay and heat maps (step 0 of /analytics)", None),
    ("W1", "copy", "Word count fits the buyer", 2, "MACHINE", "Under 600 words for a trade or local service, under 900 for an outcome service", "Cut to bullets; visitors read a tenth of it", None),
    ("W2", "copy", "Bullets over paragraphs", 1, "MACHINE", "More list items than paragraphs, or a short page", "Turn each paragraph into three bullets", None),
    ("W3", "copy", "Every line is proof, a result or a benefit", 3, "JUDGED", "Section by section, nothing is filler, a feature without its outcome, or repeated", "Delete the line or finish its chain: feature, benefit, outcome", None),
    ("W4", "copy", "The feature-benefit-outcome chain is visible", 1, "JUDGED", "The copy runs 'we do X, which gives you Y, meaning Z' at least in the key sections", "Rewrite the three reasons and the what-you-get bullets as chains", None),
    ("W5", "copy", "The FAQ answers why people do not enquire", 1, "JUDGED", "FAQ questions are the real objections before the form (price, timing, guarantee, what happens next); nothing after the form", "Ask the owner what people say when they do not go ahead; those sentences are the FAQ", None),
    ("W6", "copy", "No banned phrases", 1, "MACHINE", "No 'no spam', 'no obligation', 'no pressure', 'we strive', 'look no further', filler", "Delete them; reframe positively", None),
    ("W7", "copy", "Reads at grade 7 or under", 1, "MACHINE", "Flesch-Kincaid grade of the visible copy is 7 or under", "Shorter sentences, shorter words, one idea a line", None),
    ("D1", "design", "Hierarchy and whitespace", 2, "JUDGED", "From the full-page screenshots on each viewport: one clear reading order, air between blocks, nothing cramped", "Increase section spacing, one heading size per level, cut the boxes", None),
    ("D2", "design", "The first screen does its job", 2, "JUDGED", "From the fold screenshots: a stranger sees what this is, why to trust it and what to do next, without scrolling. Five or six things is the ceiling - the styled line above the headline, the headline, the line under it, the buttons, the three ticks, the review score. A seventh is one too many and something has to go. Order is the designer's choice; proof above or below the buttons is taste, not a fault. Judge what is MISSING, unreadable, or one thing too many - never where a working element sits", "Name the one thing missing from the first screen and put it there. Never prescribe an order that already works. Plain words - never say fold, CTA, message match or Quality Score", None),
    ("D3", "design", "Consistent type and palette", 1, "MACHINE", "Two font families or fewer, six text colours or fewer", "Pick one display and one body font; one accent colour", None),
    ("D4", "design", "Nothing overflows, no tiny text, no tiny taps", 2, "MACHINE", "No horizontal scroll on any viewport, under 6 text nodes below 12px on mobile, under 4 tap targets below 44px", "Fix the overflowing element, raise the small text, enlarge the taps", None),
    ("D5", "design", "Images crisp and light", 1, "MACHINE", "No image upscaled past 1.3x, none over 300 KB", "Export at 2x the rendered width as WebP", None),
    ("D6", "design", "The CTA pattern fits each viewport", 1, "MACHINE", "Mobile has the fixed bar and no per-section clutter; desktop has per-section CTAs and no fixed bar", "Mobile bar plus per-section CTAs on desktop, as the template does", None),
    ("D7", "design", "Looks like a business you would pay", 1, "JUDGED", "Overall, 0 to 10 with three specific reasons: would a stranger with three tabs open trust this one", "Take the three reasons and fix them in order", None),
    ("S1", "speed", "LCP under 2.5 seconds on mobile", 1.5, "MACHINE", "Lighthouse mobile LCP 2.5s or under (aim 1.8); 4s is half marks", "Preload the hero poster, self-host fonts, no video autoplay, compress the hero image", None),
    ("S2", "speed", "No layout shift, no blocking", 1, "MACHINE", "CLS 0.1 or under and TBT 200ms or under", "Set width and height on every image and video; defer scripts", None),
    ("S3", "speed", "Lighthouse performance 90 or over on mobile", 1, "MACHINE", "Performance score 90 or over; 70 is half marks", "Work the top opportunities in the speed section", None),
    ("S4", "speed", "Light third parties, clean head", 0.5, "MACHINE", "Under 300 KB of third-party weight, no synchronous script in the head except the Google tag", "Remove or defer the third-party scripts listed", None),
    ("S5", "speed", "Technical hygiene", 1, "MACHINE", "Seven checks: noindex on an ad page, no popup, no chat widget, no countdown, no autoplay, a poster on every video, no third-party video iframe", "Fix each failed check", None),
    ("P14", "proof", "A lead magnet beside the form, framed as an extra", 1, "MACHINE", "Something they keep named near the form - an audit, a checklist, a calculator - with a picture of it, and framed as an add-on rather than the reason to enquire", "Put it to the left of the form with a picture of it. Say what they are really getting - help with the job - and that the audit arrives on the way. Never sell the magnet as the offer", None),
    ("F1", "fit", "Nothing on the page is wrong for this business model", 2, "BUSINESS", "The layers that read as off for this model are absent (portfolio grid on e-commerce, calendar on a product page, licence line on SaaS, commercial logos on a residential trade)", "Remove the layer the report names", None),
    ("F2", "fit", "The layers this model needs are present", 2, "BUSINESS", "The proof form, the conversion action and the price treatment this model needs are on the page", "Add the layer the report names, from references/cro-by-business-model.md", None),
    ("F3", "fit", "The question they will not ask is answered before they scroll", 1, "JUDGED", "Against the primary persona (or the model's typical buyer), the first screen answers the question they will not type", "Put the answer in the subhead or the tick strip", None),
]

MODELS = {
    "trade": {"label": "local trade or home service", "words_max": 600, "bench": "plumbing 7.63%, HVAC 6.56 to 7.48%, electricians 9.08%, roofing 3.70%, cleaning 17.65% (LocaliQ 2026, paid search)",
              "bar": "Call left, Get a quote right",
              "required": ["phone_above_fold", "licence", "rating_count", "price_statement", "mobile_bar", "form"],
              "wrong": ["logo_wall_commercial", "calendar", "chat", "cart", "trial_cta", "security_badges", "countdown"]},
    "professional": {"label": "local professional service", "words_max": 800, "bench": "legal 5.55%, dentists 10.67%, orthodontics 14.21% (LocaliQ 2026); 56% of legal conversions are calls",
                     "bar": "Call left, Free case review or Book online right",
                     "required": ["credentials", "rating_count", "price_statement", "booking_or_call", "form"],
                     "wrong": ["portfolio_grid", "cart", "trial_cta", "security_badges", "chat", "countdown", "logo_wall_commercial"]},
    "agency": {"label": "agency or B2B service", "words_max": 900, "bench": "business services 4.85% (LocaliQ 2026), professional services 6.1% (Unbounce, Ruler); 95% of agency conversions are forms",
               "bar": "Book a call left, See results right",
               "required": ["case_studies", "review_profile_link", "price_statement", "form", "booking_or_form"],
               "wrong": ["licence", "portfolio_grid", "cart", "trial_cta", "phone_first", "textarea", "countdown", "yelp_bbb"]},
    "ecommerce": {"label": "e-commerce or physical product", "words_max": 700, "bench": "e-commerce page action 4.2% (Unbounce); purchase 1.4% average, 3.2% top 20% (Shopify); add-to-cart 4.6% median",
                  "bar": "Add to cart with price and variant, one button",
                  "required": ["product_images", "price", "buy_cta", "rating_count", "shipping_returns"],
                  "wrong": ["portfolio_grid", "case_studies", "calendar", "lead_form_primary", "licence", "phone_first", "logo_wall_commercial"]},
    "saas": {"label": "SaaS, app, course or community", "words_max": 900, "bench": "SaaS 3.8%, online courses 18.3% (Unbounce); education 13.14% (LocaliQ 2026); software 7.6% (Ruler)",
             "bar": "Start free trial or Book a demo left, See it work right",
             "required": ["trial_or_demo_cta", "product_visual", "pricing_or_link", "rating_count", "logos_or_cases"],
             "wrong": ["licence", "phone_first", "portfolio_grid", "yelp_bbb", "countdown"]},
}
MODEL_ALIASES = {"trade": ["trade", "home service", "plumb", "roof", "hvac", "electric", "clean", "landscap", "contractor", "handyman", "pest", "mov"],
                 "professional": ["professional", "lawyer", "law", "dent", "clinic", "account", "chiro", "physio", "vet", "medical", "insurance broker", "realtor"],
                 "agency": ["agency", "b2b", "consult", "marketing", "software dev", "studio", "freelanc"],
                 "ecommerce": ["e-commerce", "ecommerce", "product", "shop", "store", "retail"],
                 "saas": ["saas", "app", "software", "course", "community", "membership", "platform"]}

BANNED = re.compile(r"\bno spam\b|never spam|no obligation|no pressure|no hidden fees|we strive|look no further|in today's|fast-paced|rest assured|passionate about|second to none|one[- ]stop shop", re.I)


def model_key(text):
    t = (text or "").lower()
    for k, words in MODEL_ALIASES.items():
        if any(w in t for w in words):
            return k
    return None


def fk_grade(text):
    sents = max(1, len(re.findall(r"[.!?]+", text)))
    words = re.findall(r"[A-Za-z']+", text)
    if len(words) < 30:
        return None
    def syl(w):
        w = w.lower(); c = len(re.findall(r"[aeiouy]+", w))
        if w.endswith("e") and c > 1: c -= 1
        return max(1, c)
    syls = sum(syl(w) for w in words)
    return round(0.39 * len(words) / sents + 11.8 * syls / len(words) - 15.59, 1)


def layers(cap, assets, tracking):
    """What is on the page, as named layers the business-fit items reason about."""
    m = cap["viewports"]["mobile"]["facts"]; d = cap["viewports"]["desktop"]["facts"]
    text = m["text"]; low = text.lower()
    cta_text = " ".join(c["text"].lower() for c in d["ctas"])
    imgs = assets["images"]["items"]
    by_section = {}
    for im in imgs:
        if im["big"]:
            by_section[im["section"]] = by_section.get(im["section"], 0) + 1
    small_logo_like = sum(1 for im in imgs if im["naturalW"] and im["naturalH"] and im["naturalW"] / max(im["naturalH"], 1) > 1.8 and max(v["h"] for v in im["rendered"].values()) < 90)
    L = {
        "phone_above_fold": tracking["tel_above_fold_mobile"],
        "mobile_bar": any(b["hasTel"] for b in m["fixedBottom"]),
        "licence": bool(re.search(r"licen[sc]e|insured|bonded|wsib|certified", low)),
        "credentials": bool(re.search(r"licen[sc]e|certified|accredited|registered|bar association|college of|member of|award", low)),
        "portfolio_grid": any(v >= 6 for v in by_section.values()) or bool(re.search(r"our work|gallery|portfolio|recent projects|before (&|and) after", low)),
        "case_studies": bool(re.search(r"case stud|results? for|what changed|before (&|and) after|\d+%\s+(more|increase|lift)", low)),
        "rating_count": bool(re.search(r"\d\.\d\s*(stars?|/\s*5|out of 5).{0,80}\d{2,}|\d{2,}\+?\s*(google\s+)?reviews", text, re.I | re.S)),
        "logo_wall_commercial": small_logo_like >= 4,
        "price_statement": bool(re.search(r"\$\s?\d|(from|starting at)\s+\$|free (quote|estimate)|call[- ]out fee|diagnostic fee|per (hour|sq)", low)),
        "price": bool(re.search(r"\$\s?\d", text)),
        "cart": bool(re.search(r"add to cart|add to bag|checkout|buy now|shop now", cta_text + " " + low)),
        "buy_cta": bool(re.search(r"buy|add to cart|order|shop now|checkout", cta_text)),
        "trial_cta": bool(re.search(r"free trial|start (your )?trial|try (it )?free|sign ?up free|book a demo|get a demo|start free", cta_text + " " + low)),
        "trial_or_demo_cta": bool(re.search(r"trial|demo|sign ?up|get started|start free", cta_text)),
        "calendar": any(f["provider"] == "calendar" for f in d["iframes"]) or bool(re.search(r"calendly|leadconnector|msgsndr|acuity|cal\.com", low)),
        "booking_or_call": bool(m["tel"]) or any(f["provider"] == "calendar" for f in d["iframes"]) or bool(re.search(r"book (a|your|an|now)|schedule", cta_text)),
        "booking_or_form": bool(m["forms"]) or bool(re.search(r"book|schedule|apply|talk", cta_text)),
        "lead_form_primary": bool(m["forms"]) and not bool(re.search(r"buy|add to cart|checkout", cta_text)),
        "product_images": sum(1 for im in imgs if im["big"]) >= 3,
        "product_visual": (sum(1 for im in imgs if im["big"]) >= 2) or bool(d["videos"]) or bool(d["iframes"]),
        "shipping_returns": bool(re.search(r"shipping|delivery|returns?|refund", low)),
        "pricing_or_link": bool(re.search(r"\$\s?\d|pricing|per month|/mo\b", low)),
        "logos_or_cases": small_logo_like >= 3 or bool(re.search(r"case stud|trusted by|used by|clients include", low)),
        "rating_or_logos": small_logo_like >= 3 or bool(re.search(r"\d{2,}\+?\s*reviews|\d\.\d\s*(stars?|/5)", low)),
        "cases_or_results": bool(re.search(r"case stud|results|won|recovered|saved|settled|\d+%", low)),
        "portfolio_or_cases": any(v >= 6 for v in by_section.values()) or bool(re.search(r"our work|gallery|portfolio|projects|case stud|before (&|and) after", low)),
        "phone_first": bool(m["tel"]) and not bool(m["forms"]),
        "form": bool(m["forms"]),
        "mobile_bar": any(b["hasTel"] for b in m["fixedBottom"]),
        "chat": bool(m["chat"]),
        "countdown": bool(m["countdown"]),
        "textarea": any(f["textareas"] > 0 for f in m["forms"]),
        "security_badges": bool(re.search(r"soc ?2|iso ?27001|gdpr compliant|hipaa compliant|pci dss", low)),
        "yelp_bbb": bool(re.search(r"\byelp\b|\bbbb\b|better business bureau|\bangi\b", low)),
        "review_profile_link": any(l["kind"] == "review-profile" for l in assets["links"]["items"]) or bool(re.search(r"clutch\.co|g2\.com|trustpilot|google\.com/maps|g\.page", " ".join(l["url"] for l in assets["links"]["items"]))),
    }
    return L


def machine(cap, assets, speed, tracking, business):
    """Every MACHINE and BUSINESS item: id -> (fraction 0..1 or None for n/a, evidence, applies)."""
    m = cap["viewports"]["mobile"]["facts"]; t = cap["viewports"]["tablet"]["facts"]; d = cap["viewports"]["desktop"]["facts"]
    model = business.get("model")
    conv = (business.get("converts_by") or "").lower()
    L = layers(cap, assets, tracking)
    imgs = assets["images"]; vids = assets["videos"]; lks = assets["links"]
    sp = (speed or {}).get("mobile") or {}
    tr = tracking
    forms = tr["forms"]; f = forms[0] if forms else None
    R = {}
    def put(i, frac, ev, applies=True):
        R[i] = (None if not applies else max(0.0, min(1.0, frac)), ev, applies)

    put("M5", 1.0 if (m["h1"] and 4 <= m["h1Words"] <= 14 and (m["h1Top"] or 9999) < 844) else (0.5 if m["h1"] else 0.0),
        f"H1 \"{m['h1'][:70]}\" · {m['h1Words']} words · top at {m['h1Top']}px on mobile" if m["h1"] else "no H1")
    # A founder video is whichever video's TRANSCRIPT says the owner is speaking. Position is
    # not evidence: a DJ site's founder video sits at 2314px and used to score zero (Jono,
    # 27 Sep 2026). Full marks if it exists, half if it is buried below two screens.
    from .copy_check import classify_video as _cv
    _kinds = [(v, _cv(v.get("transcript"))[0]) for v in vids["items"]]
    founder = [v for v, k in _kinds if k == "founder"]
    clients = [v for v, k in _kinds if k == "client"]
    if not founder and not clients:
        founder = [v for v in vids["items"] if v["top"] < 844 * 2]  # no transcripts: old guess
    _high = [v for v in founder if v["top"] < 844 * 2]
    put("P1", (1.0 if _high else 0.7) if founder else 0.0,
        (f"founder video at {founder[0]['top']}px"
         + ("" if _high else " - it works, but it is below the first two phone screens"))
        if founder else "no founder video anywhere on the page")
    others = clients or [v for v, k in _kinds if k not in ("founder",)]
    good = [v for v in others if v["kind"] == "self-hosted" and not v["autoplay"] and v["poster"]]
    put("P3", min(1.0, len(others) / 3) if others else 0.0,
        f"{len(others)} client video(s) on camera · {len(good)} self-hosted with poster · "
        f"{vids['third_party']} third-party embeds")
    quotes = max(len(re.findall(r"[\"“][^\"”]{40,400}[\"”]", m["text"])), d.get("quotes", 0))
    put("P5", min(1.0, quotes / 5), f"about {quotes} testimonial blocks found")
    # MAJORITY real is the bar, not perfection - one or two stock shots on a page of forty is
    # not a conversion problem (Jono, 27 Sep 2026).
    bad_imgs = imgs["stock_suspects"] + imgs["upscaled"]
    _tot = max(1, imgs["count"])
    _share = bad_imgs / _tot
    put("P7", 1.0 if _share <= 0.25 else (0.5 if _share <= 0.5 else 0.0),
        f"{bad_imgs} of {imgs['count']} images look like stock or upscaled "
        f"({round(100 * (1 - _share))}% look real)")
    rating_link = any(l["kind"] == "review-profile" for l in lks["items"])
    # the score and its count are what count. A link to the profile is a fourth exit on an
    # ad page, so it earns nothing and is named as a leak by C10.
    put("P9", 1.0 if L["rating_count"] else 0.0,
        ("rating with its count" if L["rating_count"] else "no rating with a count")
        + (" · it also links off the page, which C10 counts as a leak" if rating_link else ""))
    badges = sum(1 for im in imgs["items"] if re.search(r"google|yelp|trustpilot|facebook|bbb|homestars|angi|houzz|checkatrade", (im["alt"] + " " + im["src"]).lower()))
    put("P10", 1.0 if badges else 0.0, f"{badges} platform badge image(s)")
    magnet = re.search(r"\b(?:free (?:audit|guide|checklist|report|calculator|quote|sample|template)|"
                       r"graded audit|download|cheat ?sheet|swipe file|pdf)\b", m["text"], re.I)
    magnet_sold = re.search(r"\b(?:just (?:want|enter)|only want|no strings|nothing else|"
                            r"get the (?:free )?(?:guide|checklist|pdf) now)\b", m["text"], re.I)
    put("P14", 0.0 if not magnet else (0.5 if magnet_sold else 1.0),
        ("no lead magnet named near the form" if not magnet
         else ("lead magnet \"" + magnet.group(0) + "\" - but it reads as the reason to enquire" if magnet_sold
               else "lead magnet: " + magnet.group(0))))
    put("P11", 1.0 if L["licence"] else 0.0, "licence, insured or bonded found" if L["licence"] else "no licence, insurance or bond line", applies=model in ("trade", "professional") or model is None)
    if model == "trade":
        ok = L["portfolio_grid"] or L["case_studies"]; ev = f"portfolio grid {L['portfolio_grid']} · case studies {L['case_studies']}"
    elif model in ("professional", "agency", "saas"):
        ok = L["case_studies"] or L["cases_or_results"]; ev = f"case studies or results {ok}"
    else:
        ok = L["portfolio_or_cases"]; ev = f"portfolio or case studies {ok}"
    put("P12", 1.0 if ok else 0.0, ev, applies=model != "ecommerce")
    # P13 proof traceability: our pages against context/proof.md; other pages are flagged for the owner
    try:
        import check_page_quality as cpq
        nums = cpq.proof_numbers()
    except Exception:
        nums = set()
    # the numbers that are CLAIMS: money, percentages, ratings, counts of three digits or more. Not years, times, step numbers.
    raw = re.findall(r"\$\s?\d[\d,]*(?:\.\d+)?[kKmM]?\+?|\d[\d,]*(?:\.\d+)?\s?%|\b\d\.\d\s*(?:/\s*5|stars?)|\b\d{1,3}(?:,\d{3})+\+?|\b[1-9]\d{2,}\+?", re.sub(r"\d{1,2}:\d{2}|\b(19|20)\d\d\b", "", m["text"]))
    page_nums = {re.sub(r"\s+", "", n) for n in raw}
    if tr["ours"] and nums:
        def known(n):
            core = re.sub(r"[^\d.]", "", n)
            return any(core == re.sub(r"[^\d.]", "", str(k)) for k in nums)
        missing = [n for n in page_nums if not known(n)]
        put("P13", 1.0 if not missing else max(0.0, 1 - len(missing) / max(len(page_nums), 1)), f"{len(page_nums)} numbers on the page · {len(missing)} not in context/proof.md" + (": " + ", ".join(missing[:8]) if missing else ""))
    else:
        put("P13", 0.5 if page_nums else 1.0, f"{len(page_nums)} numbers on the page · not our page, so each one is for the owner to source: " + ", ".join(sorted(page_nums)[:10]))
    put("C1", sum(1 for v in (m, t, d) if v["ctasAbove"] >= 1) / 3, f"CTAs above the fold · mobile {m['ctasAbove']} · tablet {t['ctasAbove']} · desktop {d['ctasAbove']}")
    secs = [s for s in d["sections"] if s["words"] > 120]
    with_cta = sum(1 for s in secs if s["ctas"] >= 1)
    _share_cta = (with_cta / len(secs)) if secs else 0
    put("C2", 1.0 if (_share_cta >= 0.5 or d["ctasTotal"] >= 4) else (0.5 if d["ctasTotal"] >= 2 else 0.0),
        f"{with_cta} of {len(secs)} sections carry a button · {d['ctasTotal']} buttons in total"
        + (" - most sections have one, which is the bar" if _share_cta >= 0.5 else ""))
    def _one_each(bars):
        seen, out = set(), []
        for b in bars:
            key = ((b.get("text") or "")[:40].strip().lower(), b.get("hasTel"), b.get("hasFormLink"))
            if key not in seen:
                seen.add(key)
                out.append(b)
        return out
    mob_bar = _one_each([b for b in m["fixedBottom"] if b["hasTel"] or b["hasFormLink"]])
    desk_bar = _one_each([b for b in d["fixedBottom"] if b["hasTel"] or b["hasFormLink"]])
    _both = [b for b in mob_bar if b["hasTel"] and b["hasFormLink"]]
    mob_top = m.get("fixedTop") or []
    put("C3", 1.0 if (len(mob_bar) == 1 and not desk_bar and not mob_top) else (0.5 if mob_bar else 0.0),
        (f"one fixed bar on mobile"
         + (" with call and form" if _both else
            " - form only, which does the job" if mob_bar and mob_bar[0]["hasFormLink"] else " - call only")
         + (f" · {len(desk_bar)} on desktop too, remove those" if desk_bar else "")
         + (" · plus a bar fixed at the top - a phone gets one bar, at the bottom" if mob_top else ""))
        if mob_bar else "no fixed bar at the bottom on mobile")
    off = [c for c in d["ctas"] if c["href"] and not re.match(r"^(#|tel:|sms:)", c["href"])]
    put("C4", 1.0 if not off else max(0.0, 1 - len(off) / max(d["ctasTotal"], 1)), f"{len(off)} CTA(s) lead to another page" + (": " + ", ".join(c['text'][:20] for c in off[:4]) if off else ""))
    if f:
        ess = f.get("essentials") or {}
        missing = [k for k, ok in ess.items() if not ok]
        put("C5", 0.5 * (sum(ess.values()) / len(ess) if ess else 0) + (0.25 if 3 <= f["fields"] <= 6 else 0.05) + (0.25 if f["selects"] + f["textareas"] == 0 else 0),
            ("missing " + ", ".join(missing) if missing else "asks all four") + f" · {f['fields']} fields · {f['selects']} dropdowns · {f['textareas']} text boxes · chips {f['chips']}")
        seven = [f["labelled"] >= f["fields"], f["autocomplete_on"] >= max(1, f["fields"] - 1), f["required_marked"] >= 1, f["phone_reason"], f["consent_line"] and f["consent_not_condition"] and f["consent_stop"], f["honeypot"], f["privacy_link"]]
        names = ["labels", "autofill", "required", "phone reason", "consent line", "honeypot", "privacy link"]
        put("C6", sum(seven) / 7, "missing: " + (", ".join(n for n, ok in zip(names, seven) if not ok) or "nothing"))
        put("C7", 0.0 if f["zip_asked"] else 1.0, "asks for a ZIP or postcode" if f["zip_asked"] else "no lookup fields")
        put("C8", 1.0 if f["button_outcome"] else 0.0, f"button says \"{f['button']}\"")
    else:
        for i in ("C5", "C6", "C7", "C8"):
            put(i, 0.0, "no form with two or more fields on the page")
    ty = tr.get("thank_you") or {}
    if ty.get("exists"):
        checks = [ty["noindex"], ty["nav_links"] <= 3, ty["tel"], ty["callback_wording"], ty["calendar"] or "book" not in conv]
        put("C9", sum(checks) / 5, f"/thank-you · noindex {ty['noindex']} · {ty['nav_links']} nav links · tel {ty['tel']} · callback time {ty['callback_wording']} · calendar {ty['calendar']}")
    else:
        # applies=False means "not sure", which is honest. Scoring 0 claimed the page was
        # missing when it simply was not reachable from outside (Jono, 27 Sep 2026).
        put("C9", 0.0, "could not reach a thank-you page from outside - not checked, not a fault. "
                       "Confirm yours has no menu, a phone number and when you will call", applies=False)
    put("C10", 1.0 if lks["leaks"] == 0 else (0.5 if lks["leaks"] <= 2 else 0.0), f"{lks['leaks']} link(s) leave the page · nav {len(m['navLinks'])} · footer {len(m['footerLinks'])}")
    put("T1", 1.0 if len(tr["tel_numbers"]) == 1 else 0.0, f"{len(tr['tel_numbers'])} distinct phone number(s) in tel links")
    put("T2", 1.0 if tr["call_tracking"] else 0.0, "call tracking present (" + ", ".join(k for k in ("callrail", "ctm", "whatconverts", "invoca", "ringba") if tr["scripts"].get(k)) + (" google phone snippet" if tr["google_phone_snippet"] else "") + ")" if tr["call_tracking"] else "no call-tracking script, no Google phone snippet")
    put("T3", 1.0 if (tr["replay_tool"] or tr["scripts"].get("gtm") or tr["scripts"].get("ga4")) else 0.0, "analytics present: " + ", ".join(k for k, v in tr["scripts"].items() if v) if any(tr["scripts"].values()) else "no analytics script at all")
    ct = tr.get("check_tracking")
    put("T4", (1.0 if ct["passed"] else 0.3) if ct else (0.5 if tr["conversion_script"] else 0.0), ("fires once, verified" if ct and ct["passed"] else "check_tracking failed" if ct else ("conversion script present, fire not verified" if tr["conversion_script"] else "no conversion script")))
    g = tr["gclid_persisted"]
    put("T5", (0.6 if (g["hidden"] or g["storage"]) else 0.0) + (0.4 if tr["utm_persisted"] else 0.0), f"gclid in hidden field {g['hidden']} · in storage {g['storage']} · utm kept {tr['utm_persisted']}")
    put("T6", 1.0 if tr["replay_tool"] else 0.0, "replay tool present" if tr["replay_tool"] else "no replay or heat map tool")
    wmax = MODELS.get(model, {}).get("words_max", 700)
    put("W1", 1.0 if m["words"] <= wmax else (0.5 if m["words"] <= wmax * 1.5 else 0.0), f"{m['words']} words · ceiling {wmax} for this model")
    put("W2", 1.0 if (m["bullets"] >= m["paras"] or m["words"] <= 400) else 0.0, f"{m['bullets']} bullets · {m['paras']} paragraphs")
    banned = BANNED.findall(m["text"])
    put("W6", 1.0 if not banned else 0.0, "banned phrases: " + ", ".join(sorted(set(b.lower() for b in banned))[:6]) if banned else "clean")
    fk = fk_grade(m["text"])
    put("W7", 1.0 if fk is not None and fk <= 7 else (0.5 if fk is not None and fk <= 9 else 0.0), f"Flesch-Kincaid grade {fk}" if fk is not None else "too little text to grade")
    put("D3", (0.5 if len([x for x in m["fonts"] if "mono" not in x.lower()]) <= 2 else 0) + (0.5 if len(m["colors"]) <= 6 else 0), f"fonts: {', '.join(m['fonts'][:4])} · {len(m['colors'])} text colours")
    over = [n for n, v in (("mobile", m), ("tablet", t), ("desktop", d)) if v["overflowX"]]
    put("D4", (0.5 if not over else 0) + (0.25 if m["smallText"] < 6 else 0) + (0.25 if m["smallTaps"] < 4 else 0), f"horizontal scroll on: {', '.join(over) or 'none'} · {m['smallText']} text nodes under 12px on mobile · {m['smallTaps']} tap targets under 44px" + (" · overflowing: " + ", ".join(m["overflowing"][:3]) if m["overflowing"] else ""))
    put("D5", (0.5 if imgs["upscaled"] == 0 else 0) + (0.5 if imgs["heavy"] == 0 else 0), f"{imgs['upscaled']} upscaled · {imgs['heavy']} over 300 KB")
    put("D6", (0.5 if mob_bar else 0) + (0.5 if (d["ctasTotal"] >= 3 and not desk_bar) else 0), f"mobile bar {bool(mob_bar)} · desktop per-section CTAs {d['ctasTotal']} · desktop fixed bar {bool(desk_bar)}")
    if sp:
        lcp = sp.get("lcp_s")
        if lcp is not None and lcp > 30:
            put("S1", 0.0, f"LCP measured at {lcp}s on mobile, which no real visit takes - a measuring fault. "
                           "Re-test in PageSpeed Insights before saying anything about speed", applies=False)
        else:
            put("S1", 1.0 if lcp is not None and lcp <= 2.5 else (0.5 if lcp is not None and lcp <= 4 else 0.0), f"LCP {lcp}s mobile · element {sp.get('lcp_element', '')[:60]}")
        put("S2", (0.5 if (sp.get("cls") or 0) <= 0.1 else 0) + (0.5 if (sp.get("tbt_ms") or 0) <= 200 else 0), f"CLS {sp.get('cls')} · TBT {sp.get('tbt_ms')}ms")
        perf = sp["scores"]["performance"]; put("S3", 1.0 if perf >= 90 else (0.5 if perf >= 70 else 0.0), f"performance {perf} · accessibility {sp['scores']['accessibility']} · best practices {sp['scores']['best-practices']} · SEO {sp['scores']['seo']} (mobile)")
    else:
        for i in ("S1", "S2", "S3"):
            put(i, 0.0, "Lighthouse did not run: " + ((speed or {}).get("note") or "unknown"))
    sync_head = [s for s in m["headScripts"] if s["src"] and not s["async"] and not s["defer"] and not s["module"] and not re.search(r"googletagmanager|gtag", s["src"])]
    third_kb = cap["network"]["third_party_kb"]
    put("S4", (0.5 if third_kb <= 300 else 0) + (0.5 if not sync_head else 0), f"{third_kb} KB third-party · {len(sync_head)} synchronous head script(s)")
    hyg = [("noindex", "noindex" in (m["robots"] or "").lower()), ("no popup", not m["popup"]), ("no chat", not m["chat"]), ("no countdown", not m["countdown"]),
           ("no autoplay", vids["autoplay"] == 0), ("posters", vids["no_poster"] == 0), ("no third-party video", vids["third_party"] == 0)]
    put("S5", sum(ok for _, ok in hyg) / 7, "failing: " + (", ".join(n for n, ok in hyg if not ok) or "nothing"))
    mm = MODELS.get(model)
    if mm:
        wrong = [w for w in mm["wrong"] if L.get(w)]
        req = [r for r in mm["required"] if not L.get(r)]
        put("F1", 1.0 if not wrong else max(0.0, 1 - 0.5 * len(wrong)), ("wrong for a " + mm["label"] + " - " + ", ".join(wrong)) if wrong else "nothing off-model")
        put("F2", 1 - len(req) / max(len(mm["required"]), 1), ("missing for a " + mm["label"] + " - " + ", ".join(req) + f" (bar: {mm['bar']})") if req else f"all present (bar: {mm['bar']})")
    else:
        put("F1", None, "business model not set - ask, then re-score", applies=False)
        put("F2", None, "business model not set - ask, then re-score", applies=False)
    return R, L


def score(cap, assets, speed, tracking, business, judgments=None):
    judgments = judgments or {}
    mres, L = machine(cap, assets, speed, tracking, business)
    rows, area_tot = [], {a: {"earned": 0.0, "possible": 0.0, "pending": 0.0} for a, _, _ in AREAS}
    for iid, area, name, pts, kind, measure, fix, models in ITEMS:
        row = {"id": iid, "area": area, "name": name, "points": pts, "kind": kind, "measure": measure, "fix": fix, "applies": True, "status": "PENDING", "earned": 0.0, "evidence": "", "reason": ""}
        if kind == "JUDGED":
            j = judgments.get(iid)
            if j and "score" in j:
                frac = max(0, min(2, float(j["score"]))) / 2
                row.update(earned=round(pts * frac, 2), evidence=j.get("evidence", ""), reason=j.get("reason", ""), status="PASS" if frac >= 0.99 else ("PARTIAL" if frac > 0 else "FAIL"))
                if j.get("fix"):
                    row["fix"] = j["fix"]
                area_tot[area]["possible"] += pts
            else:
                area_tot[area]["pending"] += pts
        else:
            frac, ev, applies = mres.get(iid, (None, "not measured", True))
            row["evidence"] = ev
            if not applies or frac is None:
                row.update(applies=False, status="N/A")
            else:
                row.update(earned=round(pts * frac, 2), status="PASS" if frac >= 0.99 else ("PARTIAL" if frac > 0 else "FAIL"))
                area_tot[area]["possible"] += pts
        area_tot[area]["earned"] += row["earned"]
        rows.append(row)
    possible = sum(v["possible"] for v in area_tot.values()); earned = sum(v["earned"] for v in area_tot.values()); pending = sum(v["pending"] for v in area_tot.values())
    total = round(100 * earned / possible) if possible else 0
    hard_fail = [r for r in rows if r["area"] in ("proof", "path", "tracking") and r["status"] == "FAIL"]
    grade = round(total / 10, 1)
    ten = total >= 90 and not hard_fail
    mm = MODELS.get(business.get("model")) or {}
    return {"total": total, "grade": grade, "ten_out_of_ten": ten, "provisional": pending > 0, "pending_points": pending, "benchmark": mm.get("bench", ""), "bar": mm.get("bar", ""),
            "earned": round(earned, 1), "possible": round(possible, 1), "areas": area_tot, "rows": rows, "layers": L, "hard_fails": [r["id"] for r in hard_fail]}


def write_reference(path=None):
    path = path or os.path.join(ROOT, "references", "audit-rubric.md")
    L = ["# The landing page rubric - 100 points, a grade out of 10", "Generated from code/audit/rubric.py · never edit by hand, run `python3 -m audit.rubric --write-reference`",
         "Next: read the audit.md the command wrote; every line below is one row in it.", "",
         "MACHINE is scored by code. JUDGED is scored by Claude from the screenshots, contact sheets and transcripts (0, 1 or 2). BUSINESS applies by the model in context/business.md; items that do not apply leave the denominator.",
         "Grade: 90 or more is a 10-out-of-10 candidate, and only when no Proof, Conversion path or Tracking item fails.", ""]
    for a, label, pts in AREAS:
        L += [f"## {label} · {pts} points", ""]
        for iid, area, name, p, kind, measure, fix, models in ITEMS:
            if area != a:
                continue
            L += [f"### {iid}. {name} · {p} points · {kind}" + (f" · {', '.join(models)} only" if models else ""), f"- Measure: {measure}", f"- Fix: {fix}", ""]
    L += ["## The business models", ""]
    for k, v in MODELS.items():
        L += [f"### {k} · {v['label']}", "- Needs: " + ", ".join(v["required"]), "- Wrong: " + ", ".join(v["wrong"]), f"- Mobile bar: {v['bar']}", f"- Word ceiling: {v['words_max']}", f"- Benchmark: {v['bench']}", "- The full layer lists, per model, are in references/cro-by-business-model.md", ""]
    open(path, "w").write("\n".join(L))
    return path


if __name__ == "__main__":
    if "--write-reference" in sys.argv:
        print("wrote", write_reference())
    else:
        print(json.dumps([(i[0], i[2], i[3], i[4]) for i in ITEMS], indent=0)[:2000])
