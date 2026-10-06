"""Score the page's copy, and say where on the page each problem is.

Every line the owner reads is plain English. Never "fold", "CTA", "message match",
"Quality Score", "above the fold" or "H1" - say what the thing DOES instead: the first
screen, a button, what Google reads to decide your ad matches, the headline.

Every finding carries the element's pixel box, so markup.py can draw it on the screenshot.
The rules that come from Jim Edwards' "Copywriting Secrets" are marked EDWARDS and are the ones
verified from the book's text: the bullet chain, the you-not-we rule, the buying reasons, the
headline shape. Anything else is marked HOUSE - our own default, never attributed to the book.

    python3 -m audit.copy_check context/pages/<slug>/audit.json
"""
import json
import re
import sys

# EDWARDS, secret 9 - the bullet chain: feature ... so you can [benefit] ... which means [meaning]
LINK1 = r"(?:so you can|so you|so that|so your|which gives you|giving you|that way|to help you|helping you|meaning you)"
LINK2 = r"(?:which means|meaning|so your|which is why|that means)"
CONNECTOR = re.compile(rf"\b(?:{LINK1}|{LINK2})\b", re.I)
SECOND = re.compile(rf"\b{LINK2}\b", re.I)

# a spec with no consequence attached: the classic feature-only line
OUTCOME_WORD = re.compile(r"\b(?:call|calls|phone|lead|leads|job|jobs|booking|booked|customer|client|"
                          r"sale|sales|revenue|money|\$[\d,]+|\d+%|hour|hours|day|days|week|weeks|"
                          r"competitor|competitors|rival|instead of|rather than|first|top|ahead)\b", re.I)

SPEC = re.compile(r"\b(24/7|24 hours|licensed|insured|bonded|certified|accredited|award[- ]winning|"
                  r"\d+\+? years|\d+ years|family[- ]owned|free (?:quote|estimate|audit)|no obligation|"
                  r"fully equipped|state of the art|iso ?\d*|\d+[- ]point|\d+[- ]step)\b", re.I)

# Why people buy - researched, in code/audit/motivations.py. Weighted per business model.
try:
    from .motivations import MOTIVATIONS
except ImportError:  # run directly: python3 code/audit/copy_check.py <audit.json>
    from motivations import MOTIVATIONS

# EDWARDS, secrets 4 and 13 - it is about them, never about you
WE = re.compile(r"\b(?:we|us|our|ours|i|me|my|mine)\b", re.I)
YOU = re.compile(r"\b(?:you|your|yours)\b", re.I)

# HOUSE - the phrases that say nothing. Most also fail the connector test on their own.
WEAK = ["quality service", "best in class", "world class", "cutting edge", "state of the art",
        "one-stop shop", "passionate about", "committed to excellence", "industry leading",
        "full service", "customer focused", "we pride ourselves", "we believe", "look no further",
        "no spam", "no obligation", "no pressure", "we strive", "solutions provider", "synergy"]

# HOUSE - a paragraph longer than this is a wall on a phone
PARA_MAX_WORDS = 40
SENTENCE_MAX_WORDS = 30
# EDWARDS - 5 to 6 bullets is the target, write 12 and keep the best
BULLETS_MIN, BULLETS_MAX = 4, 12


def _short(t, n=38):
    t = re.sub(r"\s+", " ", t or "").strip()
    return (t[:n] + "...") if len(t) > n else t


def sentences(t):
    return [x.strip() for x in re.split(r"(?<=[.!?])\s+", t) if x.strip()]


def motives_in(text, model=None):
    """Which buying motivations the copy actually appeals to, and which ones this model needs."""
    low = text.lower()
    hit = {}
    for key, spec in MOTIVATIONS.items():
        for t in spec["triggers"]:
            if t in low:
                hit[spec["label"]] = t
                break
    needed = [spec["label"] for key, spec in MOTIVATIONS.items()
              if (spec["weight"].get(model or "", 0.5)) >= 0.8 and spec["label"] not in hit]
    return hit, needed


def check(facts, business=None):
    """Findings, each with a box on the page. kind: bullet | para | quote | heading | page."""
    blocks = facts.get("blocks") or []
    quotes = facts.get("quoteBlocks") or []
    text = facts.get("text") or ""
    out = []

    def add(severity, rule, title, says, b=None, source="HOUSE"):
        out.append({"severity": severity, "rule": rule, "title": title, "says": says, "source": source,
                    "box": {k: b[k] for k in ("top", "left", "w", "h")} if b else None,
                    "sec": (b or {}).get("sec", -1), "quote": (b or {}).get("text", "")[:160]})

    bullets = [b for b in blocks if b["kind"] == "bullet"]
    paras = [b for b in blocks if b["kind"] == "para"]

    # 1. The chain: feature, so you get BENEFIT, which means OUTCOME (EDWARDS secret 9).
    #    Every descriptive bullet is judged, not only the ones that already have a connector -
    #    a bullet with no chain at all is the worse case (Jono, 26 September 2026).
    SHAPE = ("The shape is: FEATURE, so you get BENEFIT, which means OUTCOME. "
             "'We rebuild your profile, so you show in the map pack, which means the call comes "
             "to you instead of the business above you.'")
    # where the first screen ends: a tick above this line is hero proof, not a selling bullet
    secs_all = facts.get("sections") or []
    vph_ = (facts.get("viewport") or {}).get("h", 800)
    hero_ = next((x for x in secs_all if x.get("h", 0) > 200), secs_all[0] if secs_all else None)
    fold_end = (hero_["top"] + min(vph_, hero_["h"])) if hero_ else vph_
    quote_tops = [(q["top"] - 10, q["top"] + q["h"] + 10) for q in quotes]
    cta_texts = {(c.get("text") or "").strip().lower() for c in (facts.get("ctas") or [])}
    faq_texts = {(q.get("q") or "").strip().lower() for q in (facts.get("faq") or [])}

    for b in bullets:
        t = b["text"]
        if len(t.split()) < 4 or re.match(r"^[\$\d]", t.strip()):
            continue  # a number badge, not a selling line
        if t.strip().endswith("?"):
            continue  # an FAQ question, judged by whether it answers a real objection
        if b["top"] < fold_end:
            continue  # a trust tick in the first screen: proof, not a selling bullet
        if any(lo <= b["top"] <= hi for lo, hi in quote_tops):
            continue  # inside a review - somebody else's words
        if b.get("interactive") or b.get("tag") in ("button", "a", "label", "input"):
            continue  # a button or a link is not a selling bullet
        low_t = t.strip().lower()
        if low_t in cta_texts or low_t in faq_texts:
            continue  # a button, or a question already judged in the FAQ
        if re.match(r"^[A-Z][a-z]+ [A-Z]?[a-z]* ?\d{1,2} [A-Z][a-z]+ \d{4}", t):
            continue  # a reviewer name and date
        # an attribution: a person's name AND a role or company after it
        ROLE = re.compile(r"\b(?:clinic|design|services?|ltd|inc|llc|co\.|company|owner|founder|director|"
                          r"manager|remodel|roofing|siding|plumbing|electric|landscap|dental|law|"
                          r"paying client|toronto|vancouver|chicago|dallas|austin)\b", re.I)
        if re.match(r"^[A-Z][a-z]+(?:[- ][A-Z][a-z]+){1,3}[,\s]", t) and ROLE.search(t) and len(t.split()) < 16:
            continue
        # already a result in plain numbers - it has nothing left to chain to
        if re.search(r"\d+\s*%|\$[\d,]+|\b\d+\+?\s*(?:leads?|jobs?|calls?|clients?)\b", t) and len(t.split()) < 12:
            continue
        has_link = bool(CONNECTOR.search(t))
        has_second = bool(SECOND.search(t))
        if not has_link:
            add("medium", "bullet-no-chain", f'"{_short(t)}" is a description',
                "It says what the thing is and stops. " + SHAPE, b, "EDWARDS")
        elif not has_second:
            add("medium", "bullet-two-links", f'"{_short(t)}" stops at the benefit',
                "One link short. " + SHAPE, b, "EDWARDS")
        elif not OUTCOME_WORD.search(t.split(SECOND.search(t).group(0))[-1]):
            add("low", "bullet-vague-outcome", f'"{_short(t)}" ends vaguely',
                "The last link should name something they can picture: a call, a job, money, "
                "hours back. " + SHAPE, b, "EDWARDS")

    # 2. walls of text (HOUSE). A quote is exempt: those are somebody else's words and
    #    rewriting them into bullets would be putting words in their mouth.
    quote_zones = [(q["top"] - 10, q["top"] + q["h"] + 10) for q in quotes]

    def _in_quote(b):
        return any(lo <= b["top"] <= hi for lo, hi in quote_zones)

    for b in paras:
        if _in_quote(b):
            continue
        words = len(b["text"].split())
        if words > PARA_MAX_WORDS:
            add("high" if words > 70 else "medium", "wall-of-text", f"{words} words in one block",
                f"Cut this to bullets. Anything over about {PARA_MAX_WORDS} words gets skipped on a phone.", b)
        else:
            long_s = [s for s in sentences(b["text"]) if len(s.split()) > SENTENCE_MAX_WORDS]
            if long_s:
                add("low", "long-sentence", "One very long sentence",
                    "Split it in two. One idea per sentence.", b)

    # 3. how many bullets (EDWARDS)
    if bullets and len(bullets) > BULLETS_MAX:
        add("low", "too-many-bullets", f"{len(bullets)} bullets on the page",
            "Keep the best 5 or 6 in each list. A long list stops being read.", None, "EDWARDS")

    # 5. which buying reasons the page appeals to, and the ones this model needs. No finding
    #    is raised here - the "Why people buy" section shows it in full.
    model = (business or {}).get("model") if isinstance(business, dict) else None
    hits, needed = motives_in(text, model)

    # 6. weak phrases (HOUSE)
    low = text.lower()
    found = [w for w in WEAK if w in low]
    if found:
        add("medium", "weak-phrases", f"{len(found)} phrase{'s' if len(found) > 1 else ''} that says nothing",
            "Cut or replace: " + ", ".join(f'"{w}"' for w in found[:5]) + ".", None)

    # 7. testimonials: a face, a name, a number (EDWARDS secret 14 - proof beats praise)
    if quotes:
        no_photo = [q for q in quotes if not q["hasPhoto"]]
        vague = [q for q in quotes if not re.search(r"[\d$%]|\b(?:week|month|year|day)s?\b", q["text"])]
        if no_photo:
            for q in no_photo[:6]:
                add("medium", "quote-no-photo", "This review has no face beside it",
                    "Add the client's photo. A quote with a face is believed; one without reads as invented.", q)
        if len(vague) >= max(1, len(quotes) // 2):
            # said once, on the first one, not on every card
            add("low", "quote-vague", f"{len(vague)} of these reviews have no number in them",
                "Ask each client for the result: what changed, by how much, how fast.", vague[0], "EDWARDS")

    # 8. a headline so long it eats the first screen. The keyword and the city stay: they are
    #    the message match the ad is paying for (Jono, 26 September 2026).
    h1b = facts.get("h1Box")
    vph = (facts.get("viewport") or {}).get("h", 800)
    if h1b and facts.get("h1Words", 0) > 14:
        add("medium", "headline-long", f"The headline is {facts['h1Words']} words",
            "Tighten the words AROUND the keyword and the city - never drop them, they are what the ad matched. "
            "Cut the filler, keep the service and the place.", h1b, "EDWARDS")

    # 8b. the headline (EDWARDS secret 6)
    h1 = facts.get("h1") or ""
    if h1:
        if not YOU.search(h1) and not re.search(r"\d", h1):
            add("medium", "headline-flat", "The headline has no number and does not say 'you'",
                'Try "How to [what they want] in [time], even if [their worry]".', None, "EDWARDS")
        n = re.search(r"\b(\d+)\b", h1)
        if n and int(n.group(1)) % 2 == 0 and int(n.group(1)) < 100:
            add("low", "headline-even", f"The headline uses {n.group(1)}",
                "Odd numbers get read more. Try 3, 5, 7 or 9 if the real number allows it.", None, "EDWARDS")

    # 8c. A heading that names what YOU do instead of what THEY get. The commonest copy
    #     failure on a service page, and it is machine-detectable.
    ABOUT_US = re.compile(r"^(?:what we|who we|our |we \w+|the (?:build|process|team|company)|about|services?$|everything (?:in|we))", re.I)
    THEIRS = re.compile(r"\byou(?:r|rs)?\b|\bcalls?\b|\bleads?\b|\bjobs?\b|\bcustomers?\b|\bbooked\b", re.I)
    for b in [x for x in blocks if x["kind"] == "heading"]:
        t = b["text"].strip()
        if len(t.split()) >= 2 and ABOUT_US.search(t) and not THEIRS.search(t):
            add("medium", "heading-about-us", f'"{_short(t)}" is about you, not them',
                "Say what they get. A heading that names your process makes the reader do the translating.", b)

    # 8c-ii. An H2 is an ad headline. Its job is to make someone keep reading, and it earns
    #        that by doing ONE of these (Jono, 26 September 2026): promising a result, taking
    #        work off them, answering a money worry, or making them curious about proof.
    #        "We take care of everything", "Prices that suit all budgets" and "See for
    #        yourself why clients love us" all pass. "Two builds, and what changed" does not.
    PULLS = [
        ("a result", re.compile(r"\b(?:call|calls|lead|leads|job|jobs|booked|booking|customer|client|sale|sales|"
                                r"revenue|\$[\d,]+|\d+%|rank|ranked|found|hired|busy|grow|more|double)\b", re.I)),
        ("taking work off them", re.compile(r"\b(?:we (?:take care|handle|do|sort|run|manage)|done for you|"
                                            r"everything|hands off|without (?:you|lifting)|never (?:chase|worry|think)|"
                                            r"stop \w+ing|no more|leave it (?:to|with) us|off your plate)\b", re.I)),
        ("the money question", re.compile(r"\b(?:price|prices|pricing|cost|costs|budget|budgets|afford|"
                                          r"free|no lock|cancel any|month to month|guarantee|refund|"
                                          r"pay|paid|cheaper|from \$)\b", re.I)),
        ("curiosity about proof", re.compile(r"\b(?:see (?:for yourself|what|why|how)|why \w+ (?:love|choose|pick|stay)|"
                                             r"what (?:happened|changed|they say)|here is (?:what|how|why)|"
                                             r"judge for yourself|look at|watch|real \w+|"
                                             r"(?:people|clients?|customers?|couples?|owners?) (?:really )?"
                                             r"(?:love|rate|recommend|trust|stay with|come back))\b", re.I)),
        ("a promise with a time on it", re.compile(r"\b(?:in \d+ (?:days?|weeks?|months?|hours?|minutes?)|"
                                                   r"same day|within \d+|by \w+day|or (?:we|you)\b)", re.I)),
        ("asking a question they want answered", re.compile(r"\?\s*$")),
        ("taking the risk away", re.compile(r"\b(?:no risk|risk[- ]free|no obligation|no card|no contract|"
                                            r"free|guarantee[ds]?|money back|refund|cancel any ?time|"
                                            r"no lock|nothing to (?:lose|pay)|yours to keep)\b", re.I)),
        ("borrowed authority", re.compile(r"\b(?:trusted by|used by|chosen by|as seen (?:in|on)|featured (?:in|on)|"
                                          r"behind \d|partner(?:ed)? with|works? with|the team behind|"
                                          r"largest|biggest|leading|\d[\d,]*\+? (?:companies|brands|clients|"
                                          r"weddings|events|businesses|contractors|owners))\b", re.I)),
    ]
    # these describe the seller's process or label the section. Whatever else is in the
    # line, it is not doing a headline's job.
    PROCESS = re.compile(r"^(?:\w+ steps?|\d+ steps?|how it works|the process|what we do|our \w+|"
                         r"everything (?:in|we) (?:the )?build|what you get|the build|next steps?|"
                         r"before you \w+|about \w+|two \w+,|where the \w+)", re.I)
    ABOUT_SELF = re.compile(r"^(?:\w+ we have \w+|what (?:we|clients|they) (?:said|did|built|changed)|"
                            r"\w+, unscripted|\w+ and what changed)$", re.I)
    # conventional labels people LOOK for. Leave them alone.
    CONVENTION = re.compile(r"^(?:frequently asked questions|faqs?|questions|common questions|"
                            r"pricing|prices|packages|contact|contact us|get in touch|"
                            r"how it works|our work|gallery|portfolio|reviews|testimonials)$", re.I)
    for b in [x for x in blocks if x["kind"] == "heading"]:
        t = b["text"].strip()
        if len(t.split()) < 2:
            continue
        if CONVENTION.match(t):
            continue
        if PROCESS.match(t) or ABOUT_SELF.match(t) or not any(rx.search(t) for _, rx in PULLS):
            why = ("it describes your process" if PROCESS.match(t)
                   else "it labels the section instead of selling it")
            EXAMPLES = ["We take care of everything", "Prices that suit all budgets",
                        "See for yourself why clients love us", "Trusted by 400+ owners",
                        "Booked in a day, or you pay nothing"]
            words = set(re.findall(r"[a-z]{4,}", t.lower()))
            # never suggest an example that says the same thing as the heading being rejected
            picks = [x for x in EXAMPLES if len(words & set(re.findall(r"[a-z]{4,}", x.lower()))) == 0][:3]
            add("medium", "heading-weak", f'"{_short(t)}" would not earn a click',
                f"Treat this like an ad headline - {why}. A heading pulls someone in by promising a "
                "result, taking work off them, answering the money worry, making them curious about "
                "the proof, borrowing authority, or taking the risk away. "
                + " · ".join(f"'{x}'" for x in picks), b, "EDWARDS")

    # 8d. A heading that is a label rather than a claim.
    LABELS = re.compile(r"^(?:services|our services|features|benefits|testimonials|reviews|gallery|portfolio|faq|questions|pricing|about us|why us|the team|where the record is public|kind words|what clients said)$", re.I)
    for b in [x for x in blocks if x["kind"] == "heading"]:
        if LABELS.match(b["text"].strip()):
            add("low", "heading-label", f'"{_short(b["text"])}" is a label, not a promise',
                "A heading is a chance to sell. Say what the section proves, not what it is.", b)

    # 8e. A section that repeats a heading above it.
    seen_h = {}
    for b in [x for x in blocks if x["kind"] == "heading"]:
        k = re.sub(r"[^a-z ]", "", b["text"].lower()).strip()
        words = set(k.split())
        for prev_k, prev_b in seen_h.items():
            shared = words & set(prev_k.split())
            if len(shared) >= 2 and len(shared) >= len(words) * 0.6:
                add("low", "heading-repeat", "This says the same as a section above",
                    f'It repeats "{_short(prev_b["text"])}". Two sections making the same point is one section.', b)
                break
        seen_h[k] = b

    # 9. a reason to act now, and a reason it is safe (EDWARDS)
    if not re.search(r"\b(?:today|now|this week|limited|only \d+|spots|expires|deadline|before)\b", low):
        add("low", "no-urgency", "Nothing gives them a reason to act today",
            "Add one honest line: the next start date, the number of jobs you take a month.", None, "EDWARDS")
    # The guarantee is component 20 on the list and is scored there (rubric M6). It was also
    # emitted here as a page-wide note with nowhere to pin it, which is how it ended up in the
    # deleted "writing, across the page" block (Jono, 27 Sep 2026).

    order = {"high": 0, "medium": 1, "low": 2}
    out.sort(key=lambda f: (order[f["severity"]], f["sec"]))
    return {"findings": out, "motives": hits, "needed": needed,
            "bullets": len(bullets), "paras": len(paras), "quotes": len(quotes)}


if __name__ == "__main__":
    d = json.load(open(sys.argv[1]))
    vp = d["capture"]["viewports"]["desktop"]["facts"]
    r = check(vp, d.get("business"))
    print(f"{len(r['findings'])} findings · sells on: {', '.join(r['motives']) or 'none'}")
    if r["needed"]:
        print(f"missing for this model: {', '.join(r['needed'])}")
    for f in r["findings"]:
        print(f"  [{f['severity']:6}] {f['title']}")
        print(f"           {f['says'][:110]}")
        if f["quote"]:
            print(f"           > {f['quote'][:90]}")

# ---------------------------------------------------------------------------
# What KIND of video is this? Read the transcript. Never the position.
#
# The bug this replaces: video-0 was called "the founder video" because it was
# topmost, and any page with 2+ frames got a "clients on camera" pin. On a page
# with nine client videos and one founder video, that is wrong twice over. The
# transcript says which is which in the first sentence - "Hi, my name is
# Alex, the owner of Northside DJs" is not a client. Use the words.
# ---------------------------------------------------------------------------

_OWNER = re.compile(r"\b(?:i(?:'m| am)|my name(?:'s| is)?|this is)\b[^.!?]{0,40}?\b(?:the )?"
                    r"(?:owner|founder|ceo|director|president|co-?founder)\b", re.I)
_OWNER_2 = re.compile(r"\b(?:owner|founder|ceo|co-?founder) (?:of|at|here)\b", re.I)
_HELPED = re.compile(r"\bthanks to (?!you\b|everyone\b)\w+|\b(?:helped|helping) (?:me|us)\b|\b(?:worked|working) with (?-i:[A-Z])\w+|"
                     r"\bbefore (?:\w+ ){0,2}came along\b|\bwe hired\b|\bi hired\b", re.I)
_WELCOME = re.compile(r"\b(?:welcome to|thanks for (?:visiting|stopping by|coming to)|"
                      r"our (?:company|team|business|process)|we (?:started|founded|built) "
                      r"(?:this|our)|here at)\b", re.I)
_CLIENT = re.compile(r"\b(?:we (?:hired|booked|used|worked with|reached out to|chose|picked)|i (?:hired|booked|"
                     r"used|found|reached out to|loved|chose)|they (?:did|were|made|handled|showed up|listened|"
                     r"treated|always)|(?:our|my) (?:wedding|event|party|project|house|roof|kitchen|experience|day|"
                     r"photographer|dj)|(?:highly )?recommend|would recommend|(?:so |really )?(?:happy|glad) (?:we|i)|"
                     r"best decision|couldn't be happier|exceeded (?:our|my) expectations|(?:was|were|is|are) "
                     r"(?:amazing|awesome|wonderful|unbelievable|incredible|fantastic)|thank(?:s| you)? (?:\w+ )?(?:for|so)|"
                     r"(?:want|wanted) to thank|hire \w+|smooth process|so easy|very (?:responsive|organized|"
                     r"professional)|did (?:an |a )?(?:amazing|great|fantastic) job)\b", re.I)
# A highlight film is music and vows, not a person talking to camera - never call it an explainer.
_FILM = re.compile(r"\[music\]|\bdo you take\b|\bi do\b|\byou may kiss\b|\bto be your (?:lawful|wedded)", re.I)


def classify_video(transcript, fallback_index=0):
    """founder | client | explainer | unknown - from the WORDS, not the position.

    Returns (kind, why) so the report can say what it read. A video with no
    transcript is "unknown", never assumed - see the unread-transcript gate in
    page_audit.py, which refuses to finish while one is unread.
    """
    t = (transcript or "").strip()
    if not t or t.startswith("("):   # "(no transcript: ...)" is a note from the fetcher, not words
        return "unknown", "no transcript could be read - judge it from the picture and say so"
    head = t[:600]
    # Someone crediting another business for what changed is a CLIENT, even when they own a business
    # of their own: "I'm one of the owners of Ridgeline Design ... thanks to Acme Marketing" is a
    # client video, and was read as a founder video until 28 Sep 2026.
    helped = _HELPED.search(t[:1200])
    if _OWNER.search(head) or _OWNER_2.search(head):
        if helped:
            return "client", f'owns their own business and credits someone else ("{helped.group(0)}")'
        return "founder", "the speaker introduces themselves as the owner/founder"
    # The owner welcoming a visitor to their own site - "thanks for visiting the website" - is the
    # founder, not a customer saying thanks.
    if _WELCOME.search(head) and not helped:
        return "founder", "the speaker speaks for the business, welcoming the visitor"
    if helped:
        return "client", f'credits someone else for what changed ("{helped.group(0)}")'
    client_hits = len(_CLIENT.findall(t))
    if client_hits >= 2:
        return "client", f"the speaker talks as a customer ({client_hits} customer phrases)"
    if _WELCOME.search(head):
        return "founder", "the speaker speaks for the business, not as a customer"
    if client_hits == 1:
        return "client", "the speaker talks as a customer"
    if _FILM.search(t):
        return "film", "music, vows or a ceremony - a highlight film, not someone talking to camera"
    return "explainer", "no one introduces themselves - this is a demo or explainer"


def video_kinds(assets):
    """[{index, kind, why, seconds, words}] for every video, transcript-first."""
    out = []
    for i, v in enumerate(((assets or {}).get("videos") or {}).get("items", [])):
        kind, why = classify_video(v.get("transcript"), i)
        out.append({"index": i, "kind": kind, "why": why,
                    "seconds": v.get("seconds"), "words": v.get("transcript_words") or 0,
                    "src": v.get("src") or ""})
    return out
