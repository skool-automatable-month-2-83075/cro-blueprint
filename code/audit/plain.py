"""Is a line written so a visitor understands it on the first read?

Two measures (Jono, 28 September 2026):
  - the reading grade, Flesch-Kincaid. Grade 10 is the ceiling for anything on a landing page.
    "Regulatory-aware AI integration for MedTech and other high-stakes Decision support
    systems" reads far above it.
  - abstract words: nouns nobody can picture. "Specialized computer vision for high-stakes
    workflows" - no one knows what that means. A line needs a thing, a number, a person or
    a result someone can see.

    from audit.plain import grade, abstract, hard_lines
"""
import re

MAX_GRADE = 10
# How many words a section can carry before people stop reading (Jono, 28 Sep 2026: a B2B site's
# "What we do" at 135 words plus three hidden tabs - "no one is going to read it"). Proof sections
# (reviews, case studies) are allowed more, because the words are the evidence.
MAX_WORDS = {"hero": 60, "body": 80, "form": 80, "faq": 250, "proof_quotes": 200, "gallery": 180,
             "proof_video": 60, "founder_video": 80, "proof_logos": 30, "steps": 80, "pricing": 120}


def too_long(words, kind):
    limit = MAX_WORDS.get(kind, 80)
    return words > limit, limit

# Words that sound like something and show nothing. Each one is a sign the line needs a
# thing the visitor can picture in its place.
ABSTRACT = {
    "solution", "solutions", "workflow", "workflows", "high-stakes", "leverage", "leveraging", "synergy",
    "synergies", "ecosystem", "stakeholders", "stakeholder", "capabilities", "capability", "innovative",
    "innovation", "cutting-edge", "state-of-the-art", "seamless", "seamlessly", "robust", "holistic",
    "end-to-end", "best-in-class", "world-class", "next-generation", "industry-leading", "paradigm",
    "empower", "empowering", "optimize", "optimization", "streamline", "streamlined", "scalable",
    "transformational", "transformative", "disruptive", "value-added", "mission-critical", "enablement",
    "integrated", "integration", "commercialization", "methodology", "framework", "deliverables",
    "top-of-the-line", "high-quality", "premium", "tailored", "bespoke", "unparalleled", "unmatched",
}


def _syllables(word):
    w = re.sub(r"[^a-z]", "", word.lower())
    if not w:
        return 0
    if len(w) <= 3:
        return 1
    w = re.sub(r"(?:[^laeiouy]es|ed|[^laeiouy]e)$", "", w)
    w = re.sub(r"^y", "", w)
    return max(1, len(re.findall(r"[aeiouy]{1,2}", w)))


def grade(text):
    """Flesch-Kincaid grade of a line or a paragraph. None when there is too little to measure."""
    words = re.findall(r"[A-Za-z][A-Za-z'-]*", text or "")
    if len(words) < 6:
        return None
    sentences = max(1, len(re.findall(r"[.!?]+(?:\s|$)", text.strip())) or 1)
    syll = sum(_syllables(w) for w in words)
    g = 0.39 * (len(words) / sentences) + 11.8 * (syll / len(words)) - 15.59
    return round(max(0.0, g), 1)


def abstract(text):
    """The abstract words in a line, in the order they appear."""
    out = []
    for w in re.findall(r"[A-Za-z][A-Za-z-]*", text or ""):
        if w.lower() in ABSTRACT and w.lower() not in out:
            out.append(w.lower())
    return out


def hard_lines(lines, limit=12):
    """The lines in a section that read above grade 10 or lean on abstract words, worst first."""
    out = []
    for t in lines:
        t = (t or "").strip()
        if len(t.split()) < 4:
            continue
        g, a = grade(t), abstract(t)
        # a reading grade on a five-word heading is noise - long words, one line. The grade
        # counts from ten words; shorter lines are flagged only for abstract words.
        if len(t.split()) < 10:
            g = None
        if (g is not None and g > MAX_GRADE) or (a and len(t.split()) <= 20) or len(a) >= 2:
            out.append({"line": t[:220], "grade": g, "abstract": a})
    out.sort(key=lambda x: (-(x["grade"] or 0), -len(x["abstract"])))
    return out[:limit]


def section_grade(lines):
    """One grade for the body copy of a section, from its full sentences only."""
    # each line is its own sentence: a heading and the line under it are not one 40-word sentence,
    # and gluing them made a photography site's short first screen read at grade 11
    parts = []
    for t in lines:
        t = (t or "").strip()
        if len(t.split()) >= 6:
            parts.append(t if re.search(r"[.!?…]$", t) else t + ".")
    return grade(" ".join(parts))


# ---------------------------------------------------------------------------------------
# Feature, benefit, outcome (Jono, 28 Sep 2026: every text-heavy section says whether the copy
# reaches the benefit and the outcome, or stops at the feature).
#   feature: names the thing - "Push notifications, native UX, full feature parity"
#   benefit: says what it does for them - speaks to "you", a verb about their world
#   outcome: says what that means - "so you...", "which means...", "so your...", a result they can picture
# ---------------------------------------------------------------------------------------
_OUTCOME = re.compile(r"\b(?:so (?:you|your|that|the|nothing|there|no|every|shoppers|customers|buyers|people)|which means|"
                      r"means (?:you|your|no|more|less)|so they|you(?:'ll| will) (?:get|see|save|have|never|stop)|"
                      r"(?:more|fewer|less) (?:sales|revenue|calls|leads|customers|bookings|jobs|recalls|stops|time|money)|"
                      r"(?:save|saves|saving) (?:you|hours|time|money)|without (?:a|the|any|rebuilding|hiring|paying))\b", re.I)
_BENEFIT = re.compile(r"\b(?:you|your|you're|yours)\b", re.I)


def chain_line(t):
    t = (t or "").strip()
    if _OUTCOME.search(t):
        return "outcome"
    if _BENEFIT.search(t):
        return "benefit"
    return "feature"


def chain_mix(lines):
    """How far a section's lines get: feature only, benefit, or outcome. Headings and one-word labels
    are left out; so are client quotes."""
    rows = [t.strip() for t in lines if 3 <= len((t or "").split()) <= 60 and t.strip()[:1] not in "\"“‘'"]
    kinds = [chain_line(t) for t in rows]
    n = len(kinds)
    f, bft, out = kinds.count("feature"), kinds.count("benefit"), kinds.count("outcome")
    if not n:
        verdict = ""
    elif f / n >= 0.6:
        verdict = "mostly features"
    elif out == 0:
        verdict = "benefits, no outcomes"
    elif out / n < 0.34:
        verdict = "few outcomes"       # one line in nine reaching the outcome is not a pass
    else:
        verdict = "reaches the outcome"
    return {"lines": n, "features": f, "benefits": bft, "outcomes": out, "verdict": verdict}
