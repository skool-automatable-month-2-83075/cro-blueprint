"""The copy options: ten for every section of the page, the vague ones cut, every buyer judges the rest.

    python3 code/copy_options.py cut      # the writers' options-1.json, -2, -3  ->  options-gated.json
    python3 code/copy_options.py sheets   # one blind reading sheet per approved buyer, letters shuffled
    python3 code/copy_options.py tally    # the buyers' votes and the editor's cuts  ->  context/voc/options-judged.json

Working files sit in context/voc/copy/. The result, context/voc/options-judged.json, is what /split-test reads
and what code/build_research_dashboard.py draws as "The copy, section by section".

This is a menu, never a page (Jono, 28 September 2026): the first page stitched from section winners said
"live in 8 weeks" thirteen times and scored 3 of 10. /split-test writes whole pages; these are lines it may draw on.

THE CODE CUT. An option is CUT when it is over length, uses filler, reads too hard, has a heading that is only a
label, carries a number that is on no file, or rewords a client's quote. An option that makes a promise the files
do not back - money back, a ranking, a result - is kept and marked ASK: a gap in proof is a question for the
owner, never a reason to write a weaker line. Every buyer counts the same: results are head counts.
"""
import argparse
import glob
import json
import os
import random
import re
import string
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build_persona_dashboard as bpd  # noqa: E402  the buyer files

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VOC = os.path.join(ROOT, "context", "voc")
WORK = os.path.join(VOC, "copy")
SPEC = os.path.join(ROOT, "references", "copy-sections.json")
NUM = re.compile(r"\$?\d[\d,.]*\+?%?")
FILLER = ["no spam", "no obligation", "no pressure", "no hidden fees", "no strings", "seamless", "leverage", "elevate",
          "unlock", "transform", "cutting-edge", "cutting edge", "solutions", "empower", "supercharge", "game-changer",
          "game changer", "robust", "next-level", "next level", "world-class", "world class", "passionate", "synergy",
          "one-stop", "industry-leading", "results-driven", "look no further", "we pride", "tailored", "holistic"]
ASKS = [(r"money back|refund", "Money back or a refund is promised here. Is it on offer, and on what terms?"),
        (r"#1|number one|\bbest\b|top[- ]rated|fastest|lowest|largest", "A superlative with no source on file. Can it be backed?"),
        (r"\b(rank|ranking|top \d)\b.*\b(in|within|by) (\d+|week|\[)|guarantee[ds]? (you |your )?(rank|results|leads|calls)",
         "A ranking or results promise. Is there a client result on file to back it?"),
        (r"\b(more|double|twice|\d+x) (calls|leads|jobs|customers|bookings)\b", "An outcome promise. Is there a result on file to back it?")]


def rel(p):
    return os.path.relpath(p, ROOT)


def read(*parts):
    p = os.path.join(ROOT, *parts)
    return open(p, encoding="utf-8").read() if os.path.exists(p) else ""


def spec():
    if not os.path.exists(SPEC):
        sys.exit(f"{rel(SPEC)} is missing. It ships with the repo - restore it from git.")
    return {s["id"]: s for s in json.load(open(SPEC, encoding="utf-8"))}


def nums(t):
    return {n.rstrip(".,+") for n in NUM.findall(t)}


def on_file():
    """Everything a page may quote a number or a client from: the facts sheet, proof, business, and any page read."""
    txt = read("context", "voc", "facts.md") + read("context", "proof.md") + read("context", "business.md")
    for extra in glob.glob(os.path.join(ROOT, "context", "proof", "**", "*.md"), recursive=True):
        txt += " " + open(extra, encoding="utf-8").read()   # the quote bank and anything else filed as proof
    for cap in glob.glob(os.path.join(ROOT, "context", "pages", "*", "capture.json")):
        try:
            txt += " " + (json.load(open(cap, encoding="utf-8")).get("html_text") or "")
        except Exception:
            pass
    return txt


def words(t):
    return len(re.findall(r"[\w$#%'’+-]+", t))


def syl(w):
    w = re.sub(r"[^a-z]", "", w.lower()); v = re.findall(r"[aeiouy]+", w)
    return max(1, len(v) - (1 if w.endswith("e") and len(v) > 1 else 0)) if w else 0


def grade(t):
    ws = re.findall(r"[A-Za-z']+", t)
    if len(ws) < 6:
        return 0
    sents = max(1, len(re.findall(r"[.!?]+", t)))
    return round(0.39 * len(ws) / sents + 11.8 * sum(syl(w) for w in ws) / len(ws) - 15.59, 1)


def cap_of(rule, key=None):
    m = re.search((rf"{key}\s*<=\s*(\d+)" if key else r"<=\s*(\d+)"), rule or "")
    return int(m.group(1)) if m else None


def flat(v):
    if isinstance(v, str): return [v]
    if isinstance(v, list): return [x for i in v for x in flat(i)]
    if isinstance(v, dict): return [x for k, i in v.items() if k != "kills" for x in flat(i)]
    return []


def check(sid, opt, S, allowed_txt, allowed_nums):
    f, why, asks = opt.get("fields") or {}, [], []
    rules = S[sid]["fields"]
    for k, v in f.items():
        for part in (v if isinstance(v, list) else [v]):
            for key, txt in (part.items() if isinstance(part, dict) else [(None, part)]):
                if not isinstance(txt, str):
                    continue
                lim = cap_of(rules.get(k, ""), key) or cap_of(rules.get(k, ""))
                if lim and words(txt) > lim + max(1, lim // 10):
                    why.append(f"{k}: {words(txt)} words, limit {lim}")
    text = " ".join(flat(f)).replace("’", "'")
    low = text.lower()
    why += [f'filler: "{w}"' for w in FILLER if w in low]
    for k in ("h1", "heading"):
        if k in f:
            h = f[k].strip().lower()
            label = len(h.split()) <= 4 and not re.search(r"\d|\?|\byou|\byour", h)
            described = re.match(r"(what (it|we) did|here is|here's|how (it|we) work|our (process|story|work|results)|a \w+ and a \w+[.,])", h) and not re.search(r"\d|\?|\byou", h)
            if label or described or re.match(r"(\w+|\d+) (steps|stages|phases)\b", h):
                why.append(f"{k} is a label or a description, not a promise")
    for k in ("sub", "body", "intro", "a"):
        if k in f and grade(f[k]) > 10:
            why.append(f"{k} reads at grade {grade(f[k])} - aim for 5 to 7")
    if sid == "featured":
        q = re.sub(r"\s+", " ", (f.get("quote") or "").strip().strip('"“”').rstrip(".…").strip())
        if not q or q.replace("’", "'") not in allowed_txt.replace("’", "'"):
            why.append("the quote is not word for word from proof.md or the page")
    else:
        bad = {n for n in nums(re.sub(r"\[[^\]]*\]", "", text)) if n not in allowed_nums and n.lstrip("$") not in allowed_nums}
        if bad:
            why.append(f"number on no file: {', '.join(sorted(bad))} - use [brackets] and ask the owner")
    # a promise the files do not back makes it ASK; the writer's own questions ride along as notes
    flagged = [q for pat, q in ASKS if re.search(pat, text, re.I)]
    return ("CUT" if why else "ASK" if flagged else "PASS"), why, list(dict.fromkeys(flagged + list(opt.get("asks") or [])))


def cut():
    S = spec()
    files = sorted(glob.glob(os.path.join(WORK, "options-[0-9]*.json")))
    if not files:
        sys.exit(f"No options yet in {rel(WORK)}/. The writers save options-1.json, -2 and -3 there - see references/copy-options.md.")
    allowed_txt = on_file()
    allowed_nums = nums(allowed_txt) | {str(i) for i in range(0, 13)} | {"15", "24", "30", "60"}
    out, bad = [], []
    for path in files:
        for sec in json.load(open(path, encoding="utf-8")):
            if sec.get("section") not in S:
                bad.append(f"{rel(path)}: \"{sec.get('section')}\" is not a section in {rel(SPEC)}")
                continue
            for o in sec["options"]:
                o["verdict"], o["why_cut"], o["ask"] = check(sec["section"], o, S, allowed_txt, allowed_nums)
            out.append(sec)
    order = list(S)
    out.sort(key=lambda s: order.index(s["section"]))
    missing = [sid for sid in order if sid not in {s["section"] for s in out}]
    json.dump(out, open(os.path.join(WORK, "options-gated.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    for s in out:
        v = [o["verdict"] for o in s["options"]]
        print(f"{s['section']:10} {len(v):>2} written · {v.count('CUT')} cut by code · {v.count('ASK')} need the owner's yes")
    for b in bad:
        print(f"FIX  {b}")
    if missing:
        print(f"FIX  no options for: {', '.join(missing)}")
    print(f"Wrote {rel(os.path.join(WORK, 'options-gated.json'))}. Next: the editor's cut, then `sheets`.")
    return 1 if bad or missing else 0


def buyers():
    pdir = bpd.DEFAULT_DIR
    files = sorted(f for f in glob.glob(os.path.join(pdir, "*.md")) if os.path.basename(f).lower() not in bpd.NOT_A_PERSONA)
    people = [bpd.parse_persona(f) for f in files]
    people = [p for p in people if p["share"]]
    if not people:
        sys.exit("No buyers yet. /personas builds them first.")
    waiting = [p["name"] for p in people if not p["approved"]]
    if waiting:
        sys.exit(f"Not approved yet: {', '.join(waiting)}. Nobody judges copy for a buyer the owner has not signed off.")
    return people


def slug(p):
    return os.path.splitext(p["file"])[0]


def show(v, ind="  "):
    if isinstance(v, str): return v
    if isinstance(v, list): return "\n".join(f"{ind}- {show(x, ind + '  ')}" for x in v)
    if isinstance(v, dict): return " · ".join(f"{k}: {show(x)}" for k, x in v.items())
    return str(v)


def gated():
    p = os.path.join(WORK, "options-gated.json")
    if not os.path.exists(p):
        sys.exit("Run `python3 code/copy_options.py cut` first.")
    secs = json.load(open(p, encoding="utf-8"))
    ed_path = os.path.join(WORK, "editor-cuts.json")
    ed = json.load(open(ed_path, encoding="utf-8")) if os.path.exists(ed_path) else {}
    for s in secs:
        for o in s["options"]:
            if o["id"] in ed and o["verdict"] != "CUT":
                o["verdict"], o["why_cut"], o["cut_by"] = "CUT", [str(ed[o["id"]])], "editor"
    return secs, bool(ed)


def sheets():
    S = spec(); secs, had_editor = gated()
    if not had_editor:
        print("No editor-cuts.json yet: the buyers will read every option the code left. The editor's cut comes first - see references/copy-options.md.")
    keys = {}
    for p in buyers():
        rnd = random.Random(slug(p)); lines = []; keys[slug(p)] = {}
        for s in secs:
            live = [o for o in s["options"] if o["verdict"] != "CUT"]
            if not live:
                continue
            rnd.shuffle(live); letters = string.ascii_uppercase[:len(live)]
            keys[slug(p)][s["section"]] = {l: o["id"] for l, o in zip(letters, live)}
            lines += [f"\n## Section: {s['section']} - {S[s['section']]['name']}", f"What this section is for: {S[s['section']]['job']}"]
            for l, o in zip(letters, live):
                lines.append(f"\nOption {l}:")
                for k, v in o["fields"].items():
                    if k != "kills":
                        lines.append(f"{k}:" + ("\n" + show(v) if isinstance(v, list) else f" {show(v)}"))
        path = os.path.join(WORK, f"read-{slug(p)}.md")
        open(path, "w", encoding="utf-8").write("# The page, section by section - every option that survived the cut\n" + "\n".join(lines) + "\n")
        print(f"{p['name']}: {sum(len(x) for x in keys[slug(p)].values())} options to judge · {rel(path)} · votes go to {rel(os.path.join(WORK, 'votes', slug(p) + '.json'))}")
    os.makedirs(os.path.join(WORK, "votes"), exist_ok=True)
    json.dump(keys, open(os.path.join(WORK, "keys.json"), "w"), indent=1)
    return 0


def tally():
    secs, _ = gated()
    kp = os.path.join(WORK, "keys.json")
    if not os.path.exists(kp):
        sys.exit("Run `python3 code/copy_options.py sheets` first, then one reader per buyer.")
    keys = json.load(open(kp))
    by_id = {o["id"]: o for s in secs for o in s["options"]}
    for o in by_id.values():
        o["panel"] = []
    names = {slug(p): p["name"].split()[-1] for p in buyers()}
    problems = []
    for b, m in keys.items():
        vp = os.path.join(WORK, "votes", f"{b}.json")
        if not os.path.exists(vp):
            problems.append(f"{b}: no votes yet - {rel(vp)}")
            continue
        got = {s["section"]: s for s in json.load(open(vp, encoding="utf-8")).get("sections", [])}
        for sid, letters in m.items():
            sv = got.get(sid) or {}
            for letter, oid in letters.items():
                v = str((sv.get("verdicts") or {}).get(letter, "")).upper()[:1]
                if v not in ("S", "L", "I"):
                    problems.append(f"{b}: no verdict for {sid} option {letter}")
                    continue
                if oid in by_id:
                    by_id[oid]["panel"].append({"buyer": names.get(b, b), "v": {"S": "STAY", "L": "LEAVE"}.get(v, "INDIFFERENT"),
                                                "why": (sv.get("why") or {}).get(letter, ""), "pick": sv.get("pick") == letter})
    if problems:
        print("FIX, send each sheet back to its reader:\n- " + "\n- ".join(problems[:20]))
        return 1
    for s in secs:
        for o in s["options"]:
            o["n"], o["stay_n"] = len(o["panel"]), sum(1 for p in o["panel"] if p["v"] == "STAY")
            o["leave_n"], o["picks"] = sum(1 for p in o["panel"] if p["v"] == "LEAVE"), sum(1 for p in o["panel"] if p.get("pick"))
        live = sorted([o for o in s["options"] if o["verdict"] != "CUT"],
                      key=lambda o: (-(o["stay_n"] - o["leave_n"]), -o["picks"], -o["stay_n"], o["id"]))
        for i, o in enumerate(live):
            o["rank"] = i + 1
        s["winner"] = [o["id"] for o in live[:6]] if s["section"] == "faq" else (live[0]["id"] if live else None)
    out = os.path.join(VOC, "options-judged.json")
    json.dump(secs, open(out, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    for s in secs:
        w = s["winner"][0] if isinstance(s["winner"], list) else s["winner"]
        if w:
            o = by_id[w]
            print(f"{s['section']:10} {o['stay_n']} of {o['n']} stay, {o['leave_n']} leave · {o['verdict']:4} · {str(o.get('angle', ''))[:60]}")
    print(f"Wrote {rel(out)}")
    import build_research_dashboard as brd
    brd.build(os.path.join(VOC, "research.html"))
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("step", choices=["cut", "sheets", "tally"])
    a = ap.parse_args()
    os.makedirs(WORK, exist_ok=True)
    sys.exit({"cut": cut, "sheets": sheets, "tally": tally}[a.step]())
