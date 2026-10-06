"""Does it sell? Every option passes this before an owner sees it.

    python3 code/audit/sell_filter.py context/pages/<slug>/drafts     # PASS, or every failing option and why

⛔ WHY (Jono, 28 September 2026: "Everything you write needs the intention to sell. If things aren't able to sell
customers, filter them out and try again. Perhaps creating a filtering rubric for this so we don't waste time on
bs text"). The picker shows only options that pass every gate. A failure goes to rejected.json and back to its
writer, and is rewritten until each section has ten that pass. Nobody chooses between lines that cannot sell.
rewrite.json lists the same failures by file, key and option number: the writers rewrite exactly those, then the
buyers re-score exactly those.

The gates, all of them, every option:
  1 SPEAKS TO THEM   it talks to "you" - the buyer, not the business
  2 GETS TO WHY      a line reaches a benefit or an outcome, not only a feature
  3 SPECIFIC         something they can check: a number, a time, a price, a named thing, or a [bracket] to fill
  4 A REASON TO ACT  it moves one of the nine buying motivations, or answers one of the six fears (persuasion.md 4)
  5 CLEAR            clarity 6 or more: no abstract or vague words
  6 EASY TO READ     reading grade 9 or under
  7 FITS             inside the section's word limit, and the headline fits three lines: a first-screen headline
                     55 characters at most, a section heading 70 (Jono, 28 September 2026: "headlines should span max 3 rows")
  8 SAYS IT ONCE     no talking point and no four-word run twice in the section
  9 TRUE             numbers from proof.md or in [brackets]; nothing on the never-say list; no em dashes
 10 KEEPS THEM       once the buyers have read it: at least 5 of 10 on staying, every buyer counted the same
"""
import glob
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))

from audit.copy_check import motives_in  # noqa: E402
from check_page_quality import proof_numbers  # noqa: E402

YOU = re.compile(r"\b(?:you|your|you're|yours|you'll)\b", re.I)
# What any buyer can check, whatever the business: a number, a price, a time, a way to reach someone.
# The business's own nouns - the things ITS buyer can picture - come from the pool: points.json "vocabulary".
CONCRETE = re.compile(r"\d|\$|\[|\b(?:week|weeks|minute|minutes|hour|hours|day|days|month|months|date|call|calls|phone|email|"
                      r"review|reviews|form)\b", re.I)
# persuasion.md section 4: what a service buyer is actually afraid of, in words any business uses
FEARS = {"will not show up": r"\b(?:on time|show(?:s)? up|turn(?:s)? up|confirmed|in writing|a date|by week|within)\b",
         "the price will change": r"\$\d|\bprice\b|\bcost\b|\bfixed\b|\bup front\b|\bdeposit\b|\bquote\b",
         "not qualified": r"\bon camera\b|\bpaying clients?\b|\breviews?\b|\byears\b|\bexperience\b",
         "cannot reach a human": r"\ba person\b|\breal person\b|\btalk to\b|\bcall\b|\bphone\b",
         "stuck with you": r"month[- ]to[- ]month|no contract|lock-?in|walk away|refund|cancel"}
PAIN = re.compile(r"\b(?:money|losing|lose|lost|worried|afraid|stress|stuck|wasted|blamed|complain|let down)\b", re.I)


def vocabulary(pool):
    """The business's own words, from points.json: {"vocabulary": {"concrete": [...], "reasons": [...]}}.
    concrete - the things its buyer can picture (a DJ's: dance floor, first dance, playlist).
    reasons  - the words of why they buy and what they fear (reasons.md, the personas)."""
    v = pool.get("vocabulary") or {}
    return {"concrete": [w.lower() for w in v.get("concrete") or []], "reasons": [w.lower() for w in v.get("reasons") or []]}


NEVER = re.compile(r"#1|\bnumber one\b|\bbest\b|top-rated|guaranteed results|\bcertified\b|google partner|lowest price|\bfastest\b", re.I)
NUM = re.compile(r"\$?\d[\d,.]*\+?%?")
H1_MAX, HEADING_MAX = 55, 70   # three lines at the kit's hero and title sizes, in a half-width column
STOP = set("the a an and or to of you your we our it in for is that on with at be are this by from if not no so".split())


def text_of(f):
    out = [f[k] for k in ("eyebrow", "h1", "heading", "sub", "body", "button") if f.get(k)]
    out += list(f.get("bullets") or []) + list(f.get("rows") or [])
    for qa in f.get("items") or []:
        out += list(qa)
    return out


def gates(kind, option, scores, known, repeats, vocab=None):
    """(passed, [failed gate lines]) for one option."""
    f = option["fields"]
    lines = text_of(f)
    text = " ".join(lines)
    unbracketed = re.sub(r"\[[^\]]*\]", "", text)
    low = text.lower()
    fail = []
    if not YOU.search(text):
        fail.append("1 speaks to them: no \"you\" anywhere - write it to the buyer")
    if scores["raw"]["mix"] == "mostly features":
        fail.append("2 gets to why: mostly features - say what it does for them, then what that means")
    vocab = vocab or {"concrete": [], "reasons": []}
    if not CONCRETE.search(text) and not any(w in low for w in vocab["concrete"]):
        fail.append("3 specific: nothing they can check - add a number, a time, a price or a named thing")
    hit, _ = motives_in(text)
    fears = [k for k, p in FEARS.items() if re.search(p, text, re.I)]
    if not hit and not fears and not PAIN.search(text) and not any(w in low for w in vocab["reasons"]):
        fail.append("4 a reason to act: no motivation, no fear answered, no pain named")
    if scores["clarity"] < 6:
        fail.append(f"5 clear: {scores['clarity']} - vague: {', '.join(scores['raw']['vague']) or 'too few concrete lines'}")
    if scores["raw"]["grade"] is not None and scores["raw"]["grade"] > 9:
        fail.append(f"6 easy to read: grade {scores['raw']['grade']}")
    if scores["raw"]["words"] > scores["raw"]["limit"]:
        fail.append(f"7 fits: {scores['raw']['words']} words, the limit is {scores['raw']['limit']}")
    if len(f.get("h1") or "") > H1_MAX:
        fail.append(f"7 fits: the headline is {len(f['h1'])} characters - {H1_MAX} fits three lines")
    if len(f.get("heading") or "") > HEADING_MAX:
        fail.append(f"7 fits: the heading is {len(f['heading'])} characters - {HEADING_MAX} fits three lines")
    twice = [r["label"] for r in repeats if len(re.findall(r["match"], low)) > 1]
    ws = re.findall(r"[a-z0-9$']+", low)
    grams = [" ".join(ws[i:i + 4]) for i in range(len(ws) - 3)]
    dup = sorted({g for g in grams if grams.count(g) > 1 and not set(g.split()) <= STOP})
    if twice or dup:
        fail.append("8 says it once: " + "; ".join(twice + [f'"{g}"' for g in dup[:2]]))
    bad = sorted({n.lstrip("$").rstrip(".,+%") for n in NUM.findall(unbracketed)} - known - {str(i) for i in range(13)} - {""})
    if bad:
        fail.append(f"9 true: numbers not in proof.md: {', '.join(bad)} - put them in [brackets]")
    if NEVER.search(text):
        fail.append(f"9 true: never say \"{NEVER.search(text).group(0)}\"")
    if "—" in text or "–" in text:
        fail.append("9 true: an em or en dash")
    if scores.get("stays") is not None and scores["stays"] < 5:
        fail.append(f"10 keeps them: {scores['stays']} of 10 - most of the buyers leave here")
    return not fail, fail


def run(folder):
    from audit.picker import buyers, measure, stays
    people = buyers()
    reads = {os.path.basename(p)[7:-5]: json.load(open(p, encoding="utf-8")) for p in glob.glob(os.path.join(folder, "scores-*.json"))}
    pool = json.load(open(os.path.join(folder, "points.json"), encoding="utf-8"))
    repeats = [{"label": p["point"], "match": p["match"]} for p in pool["points"] if p.get("match")]
    known = proof_numbers()
    vocab = vocabulary(pool)
    rejected, total, passed = {}, 0, 0
    for p in sorted(glob.glob(os.path.join(folder, "options-*.json"))):
        if p.endswith("options-needed.json"):
            continue
        for key, lst in json.load(open(p, encoding="utf-8")).items():
            kind = key.split(":")[0]
            for i, o in enumerate(lst):
                total += 1
                sc = measure(kind, o["fields"], vocab["concrete"])
                sc["stays"], who = stays(key, i, reads, people)
                ok, why = gates(kind, o, sc, known, repeats, vocab)
                if sc["stays"] is not None and sc["stays"] < 5:
                    why = why + ["leaves: " + ", ".join(f"{b['name']} {b['risk']}" for b in who if b["risk"] >= 6)]
                if ok:
                    passed += 1
                else:
                    rejected.setdefault(key, []).append({"option": i + 1, "file": os.path.basename(p), "why": why,
                                                         "text": " | ".join(text_of(o["fields"]))[:220]})
    json.dump(rejected, open(os.path.join(folder, "rejected.json"), "w"), indent=1, ensure_ascii=False)
    rewrite = {}
    for key, lst in rejected.items():
        for r in lst:
            rewrite.setdefault(r["file"], {}).setdefault(key, []).append(r["option"])
    json.dump(rewrite, open(os.path.join(folder, "rewrite.json"), "w"), indent=1)  # file -> key -> 1-based option numbers
    print(f"{passed} of {total} options sell. {total - passed} rejected, written to rejected.json.")
    for key, lst in rejected.items():
        print(f"\n{key}: {len(lst)} rejected")
        for r in lst:
            print(f"  option {r['option']}: " + " · ".join(r["why"]))
    return 0 if not rejected else 1


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__.split("\n\n")[1])
    sys.exit(run(sys.argv[1]))
