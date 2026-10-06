"""Jono's 18 components - the checklist, the score, and the plain-English line for each.

The 18 are the page. Every other rubric item is an extra the audit noticed, and it is never
scored beside them. `roll(score)` turns the 56 rubric rows into 18 checks:

    DONE     · everything behind it passed
    PARTIAL  · some of it is there
    TO DO    · it is missing
    N/A      · not for this business model (leaves the score entirely)

Score is `done out of the 18 that apply`. Nothing is weighted: the owner ticks boxes, they do
not do arithmetic. `says` is what the owner reads - one line, what is missing and what to do,
never a rubric id, a file name or a metric name.
"""

# n, name, the rubric rows behind it, what to do when it is not done
EIGHTEEN = [
    (1, "Founder video", ["P1", "P2"], "Film 45 seconds on your phone: who you are, why you do this, the promise. The still behind the play button is you, smiling, looking at the camera - the same person who is in the video."),
    (2, "The proof block above the fold", ["P9", "P10"], "Three parts in the first screen: the rating with its count and the stars drawn, three real client faces, and three ticks carrying numbers - years, jobs done, the guarantee. Do not link it out."),
    (3, "A button in every section", ["C1", "C2", "C4"], "Add a button to each section. Under the ones below the first screen, say how fast you answer and that it costs nothing - the first screen is already busy enough."),
    (4, "The offer", ["M2", "M3", "M4"], "Write the offer in the line under the headline: what they get, by when, and what you do if you miss. 'Twenty calls a month within 90 days, or you stop paying.'"),
    (5, "Licence and insurance", ["P11"], "Add your licence number and insurance line to the hero."),
    (6, "Video testimonials", ["P3", "P4"], "Three to start, nine is where it stops helping. Ask happy clients for a phone video: what was broken, what happened, what changed."),
    (7, "Three benefits", ["W4"], "Three reasons someone picks you, each as its own section rather than three bullets in one. Each runs: the feature, what it gets them, then what that means - 'so the calls come to you instead of the business above you'."),
    (8, "Little text", ["W1", "W2"], "Cut each section to its word limit. Keep the lines that sell and put the detail under a Read more."),
    (9, "Response time", [], "Only claim a callback time once the auto-dial actually delivers it."),
    (10, "Written testimonials", ["P5", "P6"], "Pull your real reviews onto the page with names."),
    (11, "A short form", ["C5", "C6", "C7", "C8"], "Keep it short: first name, last name, phone, email and one qualifying question. Split first and last so your email and text automations work."),
    (12, "Lead magnet", ["P14"], "Something they keep, beside the form on its left, with a picture of it so they can see what it is. Frame it as an extra - they are enquiring for the service, and the audit arrives quickly on the way. Never make it the reason to enquire."),
    (13, "Proof badges", ["P10"], "Two or three review badges: Google, Facebook, Trustpilot or TrustIndex, each with the stars drawn in and the score and count beside them - '4.9 out of 5, from 214 reviews'. A bare logo proves nothing."),
    (14, "No external links", ["C10"], "Strip the nav and footer; leave one legal line."),
    (15, "Case studies or portfolio", ["P12"], "Show real work you are proud of: photos or video of finished jobs, or two case studies with a number. If you would not want it seen, nobody else will."),
    (16, "Real photos, not stock", ["P7", "P8"], "Some of these images look like stock photography. Replace them with your own team, your own work, your own place - the ones marked on the page are the ones to swap."),
    (17, "Fixed call bar on mobile", ["C3", "D6"], "Add the bottom bar: call on the left, form on the right."),
    (18, "Feature, benefit, outcome", ["W3", "M1", "W5"], "Rewrite the weak lines as a chain: the feature, so you get the benefit, which means the outcome."),
    (19, "Page load speed", ["S1", "S3"], "Get it showing up in under 2.5 seconds on a phone. Every second after that loses people before they read a word."),
    (20, "A guarantee", ["M6"], "Say what happens if it does not work - money back, a redo, you stop paying. This is the single biggest thing standing between someone who likes the page and someone who enquires, and almost nobody does it. Make it specific enough that you could be held to it."),
    (21, "The thank-you page", ["C9"], "Where they land after the form: no menu, a phone number, when you will call, and the calendar if you book that way."),
    # Jono, 28 Sep 2026: "clickable phone number" and "a stats bar like years in business, reviews,
    # jobs completed" were missing from pages and the list had no way to say so.
    (22, "A phone number people can tap", [], "Put your number in the first screen and in the menu bar as a link that dials on a phone. In the footer only, most people never see it."),
    (23, "A stats bar", [], "Three or four numbers in a row, near the top: years in business, reviews with the star score, jobs completed, clients served. Numbers are believed where adjectives are not."),
    # Jono, 28 Sep 2026: logos borrow proof from companies people know, and that is its own job -
    # "not merged into the case studies, a separate point entirely".
    (24, "Client logos", [], "A row of five to eight logos of companies you have worked with, right under the first screen, with a line saying what they are: 'Trusted by'. Known names do the arguing before anyone reads a word."),
    # Jono, 2 Oct 2026: copy is its own group of four - little text (8), bullet points (25), feature,
    # benefit, outcome (18) and the reading level (26). 25 and 26 are measured from the sections.
    (25, "Bullet points", [], "Turn each paragraph into three to five bullets. People skip paragraphs and read bullets."),
    (26, "Reading level", [], "Write at grade 10 or below: shorter sentences, shorter words, one idea a line."),
]

# ---------------------------------------------------------------------------------------
# Where each component LIVES on the page (Jono, 27 Sep 2026). The report is one card per
# section; a component is spoken about once, inside the card of the section it belongs to,
# or once in "Across the page", or once in "Add" when the page has nowhere for it yet.
# HOME: the section kinds that can hold it, first match wins. PAGE: true of the whole page.
# ---------------------------------------------------------------------------------------
HOME = {
    1: ["founder_video", "hero"],
    2: ["hero"],
    4: ["hero"],
    5: ["hero"],
    13: ["hero", "form"],
    20: ["hero", "form"],
    6: ["proof_video"],
    10: ["proof_quotes"],
    11: ["form"],
    12: ["form"],
    9: ["form"],
    14: ["nav", "footer"],
    15: ["gallery"],
    22: ["hero", "nav"],
    23: ["stats", "hero"],
    24: ["proof_logos", "hero"],
}
PAGE = [3, 7, 8, 16, 17, 18, 19, 21, 25, 26]

# The five groups the course slide teaches the 26 in, same names and same order as the slide
# (Jono, 2 Oct 2026: "that slideshow has the right sections"). Every part is in exactly one.
GROUPS = [
    ("Proof", [1, 2, 5, 6, 10, 13, 15, 16, 23, 24]),
    ("The offer", [4, 7, 20]),
    ("The copy", [8, 18, 25, 26]),
    ("The next step", [3, 9, 12, 17, 21, 22]),
    ("Nothing in the way", [11, 14, 19]),
]
GROUP_OF = {n: name for name, ns in GROUPS for n in ns}

# How much each one moves enquiries. Drives "Do these first". The offer and the guarantee
# carry the most (Jono: the guarantee "should be something we heavily measure").
WEIGHT = {20: 5, 4: 5, 11: 4, 2: 4, 1: 3, 6: 3, 10: 3, 3: 3, 17: 3, 18: 3, 19: 2, 13: 2,
          14: 2, 7: 2, 12: 2, 9: 1, 5: 1, 8: 1, 15: 1, 16: 1, 21: 1, 22: 3, 23: 3, 24: 2, 25: 1, 26: 2}

# Where a missing component goes, in the owner's words, when the page has no section for it.
WHERE_TO_ADD = {
    1: "Right under the headline, or beside it. The first thing people can press play on.",
    2: "In the first screen, under the headline: the star rating with its count, three client faces, three ticks.",
    4: "In the line under the headline.",
    5: "In the first screen, beside the proof.",
    6: "Its own section after the first screen: a title and three to nine client videos.",
    9: "Under every button: how fast you answer.",
    10: "Its own section: a title and six to nine written reviews with names and faces.",
    11: "Its own section near the end: a title, a short paragraph, three bullets, and the form.",
    12: "Beside the form, with a picture of what they get.",
    13: "In the first screen and beside the form: two or three review badges - Google, Facebook, Trustpilot or TrustIndex - each with the stars, the score and the count.",
    14: "Strip the menu and the footer links. Leave one legal line.",
    15: "Its own section: real finished work, with a line on each.",
    20: "In the line under the headline, and again beside the form.",
    21: "A page they land on after the form: no menu, your number, when you will call.",
    22: "In the first screen and the menu bar, as a link that dials when tapped on a phone.",
    23: "A row of three or four numbers right under the first screen, below the client logos when there are any: years in business, reviews and the star score, jobs completed.",
    24: "Its own section, directly under the first screen: a row of five to eight client logos with a line saying who they are. A stats bar does not replace it - the logos come first, the stats bar sits under them.",
}

STATUS_WORD = {"ok": "In place", "weak": "Fix", "missing": "Missing", "n/a": "Not for you"}


# rubric rows that are the audit's own extras, grouped for the collapsed section
# Scored on the page itself, or owned by another track. Either way it is not repeated in
# the list: this is the CRO audit, not the SEO, Ads or web-design one (Jono, 26 Sep 2026).
# T2/T4 joined this set on 27 Sep 2026: whether a lead is counted is an analytics and Google
# Ads job, not a conversion-rate one, and it does not belong on the owner's list of page fixes.
ON_PAGE = {"D1", "D2", "D6", "D7", "F1", "F3", "W3", "W4", "W5", "M1", "M2", "M3", "M4",
           "T2", "T4",
           "C1", "C2", "C3", "C4", "C5", "C6", "C7", "C8", "C10",
           "S2", "S4", "S5", "D3", "D4", "D5", "M5", "P13", "W1", "W2", "W6", "W7",
           "T1", "T3", "T5", "T6", "F2", "P14"}

EXTRAS = []

RANK = {"TO DO": 0, "PARTIAL": 1, "UNREAD": 2, "DONE": 3, "N/A": 4}


def roll(score):
    """The 18, each with a status, the rows behind it and the one line to read. Plus the score."""
    by_id = {r["id"]: r for r in score["rows"]}
    out = []
    for n, name, ids, todo in EIGHTEEN:
        rows = [by_id[i] for i in ids if i in by_id]
        live = [r for r in rows if r["status"] != "N/A"]
        if not ids:
            # nothing measures this one: Claude judges it from the screenshots, or it stays unread
            j = (score.get("eighteen_judged") or {}).get(str(n)) or {}
            status = j.get("status") or "UNREAD"
            rows = []
        elif not live:
            status = "N/A"
        elif all(r["status"] == "PASS" for r in live):
            status = "DONE"
        elif any(r["status"] in ("PASS", "PARTIAL") for r in live):
            status = "PARTIAL"
        else:
            status = "TO DO"
        # what the owner reads: the gap in their words, never the rubric's
        gaps = [r for r in live if r["status"] != "PASS"]
        says = "" if status == "DONE" else todo
        out.append({"n": n, "name": name, "status": status, "says": says,
                    "waiting": any(r["status"] == "PENDING" for r in rows),
                    "rows": rows, "gaps": [r["id"] for r in gaps]})
    applies = [c for c in out if c["status"] != "N/A"]
    done = [c for c in applies if c["status"] == "DONE"]
    return {"checks": out, "done": len(done), "of": len(applies),
            "todo": [c for c in applies if c["status"] == "TO DO"],
            "partial": [c for c in applies if c["status"] == "PARTIAL"],
            "done_list": done,
            "sorted": sorted(out, key=lambda c: (RANK[c["status"]], c["n"]))}


def extras(score):
    """The audit's own findings, grouped, worst first. Never scored beside the 18."""
    by_id = {r["id"]: r for r in score["rows"]}
    owned = {i for _, _, ids, _ in EIGHTEEN for i in ids}
    out = []
    for label, ids in EXTRAS:
        rows = [by_id[i] for i in ids if i in by_id and by_id[i]["status"] not in ("N/A",)]
        gaps = [r for r in rows if r["status"] != "PASS"]
        if rows:
            out.append({"label": label, "rows": rows, "gaps": gaps, "clean": not gaps})
    # Anything left that a visitor can actually SEE is drawn on the page instead, so it
    # never appears down here as a second, competing list.
    listed = {i for _, ids in EXTRAS for i in ids}
    loose = [r for r in score["rows"] if r["id"] not in owned and r["id"] not in listed
             and r["status"] != "N/A" and r["id"] not in ON_PAGE]
    if loose:
        out.append({"label": "Other", "rows": loose, "gaps": [r for r in loose if r["status"] != "PASS"], "clean": all(r["status"] == "PASS" for r in loose)})
    return [g for g in out if g["rows"]]
