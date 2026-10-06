"""Check the research /personas leaves for /split-test: context/voc/ reddit.md, reviews.md, rivals.md, facts.md, reasons.md.

    python3 code/check_voc.py [context/voc]

PASS, or what is missing. Each file must exist, say at the top what it is and when it was made, carry real quotes
with where they came from (reddit, reviews), name its rivals (rivals), list what the page may and may not say
(facts), rank exactly three reasons people buy, each backed by real quotes (reasons), and hold no table.
A thin file is a warning, never a fail: a small sample said plainly is still research."""
import os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIR = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "context", "voc")
QUOTE = re.compile(r"[\"“][^\"”]{12,}[\"”]")
DATE = re.compile(r"20\d\d|january|february|march|april|may|june|july|august|september|october|november|december", re.I)


def check(name, text):
    fails, warns = [], []
    top = "\n".join(text.splitlines()[:8])
    if not DATE.search(top):
        fails.append("no date in the top lines - say when it was made")
    if re.search(r"^\s*\|.*\|\s*$", text, re.M):
        fails.append("a table - one fact per line instead")
    quotes = QUOTE.findall(text)
    if name in ("reddit.md", "reviews.md"):
        if len(quotes) < 10:
            fails.append(f"{len(quotes)} quotes - copy at least 10, word for word")
        elif len(quotes) < 40:
            warns.append(f"only {len(quotes)} quotes - a small sample, say so in the top line")
        sourced = sum(1 for line in text.splitlines() if QUOTE.search(line) and re.search(r"[·,(\-]\s*\S", line.split(QUOTE.findall(line)[0])[-1]))
        if quotes and sourced < len(quotes) * 0.6:
            fails.append("quotes without a source - every quote says where and when")
    if name == "rivals.md":
        heads = len(re.findall(r"^#{2,3} ", text, re.M))
        if heads < 5:
            fails.append(f"{heads} rivals or sections - pick 10 to 15 and give each a block")
        if not re.search(r"none of them|almost none|nobody", text, re.I):
            fails.append("no 'what none of them say' - the gap is the point of the file")
    if name == "reasons.md":
        blocks = re.split(r"^##\s+", text, flags=re.M)[1:]
        if len(blocks) != 3:
            fails.append(f"{len(blocks)} reasons - rank exactly three, one '## ' heading each")
        for i, b in enumerate(blocks, 1):
            title = b.splitlines()[0].strip()
            if not re.search(r"^\s*-\s*buyers:\s*\d+\s+of\s+\d+", b, re.I | re.M):
                fails.append(f"reason {i} ({title[:40]}): no 'Buyers: N of 7' line")
            if len(QUOTE.findall(b)) < 2:
                fails.append(f"reason {i} ({title[:40]}): fewer than two quotes - a reason rests on what people said")
            if not re.search(r"^\s*-\s*moves them:", b, re.I | re.M):
                fails.append(f"reason {i} ({title[:40]}): no 'Moves them:' line naming one of the nine")
    if name == "facts.md":
        if not re.search(r"do not print|never say|don't print", text, re.I):
            fails.append("no do-not-print list")
        if not re.search(r"\d", text):
            fails.append("no numbers - the page needs the real ones from proof.md")
    return fails, warns


def main():
    bad = 0
    for name in ("reddit.md", "reviews.md", "rivals.md", "facts.md", "reasons.md"):
        path = os.path.join(DIR, name)
        if not os.path.exists(path):
            print(f"FAIL  {name}: missing - /personas step 1c writes it"); bad += 1; continue
        fails, warns = check(name, open(path, encoding="utf-8").read())
        for f in fails:
            print(f"FAIL  {name}: {f}")
        for w in warns:
            print(f"WARN  {name}: {w}")
        if not fails:
            print(f"ok    {name}")
        bad += len(fails)
    print("PASS  the research is ready for /split-test" if not bad else f"\n{bad} thing(s) to fix before /split-test writes from it.")
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
