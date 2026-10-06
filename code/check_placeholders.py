"""No page goes live with a placeholder still in it.

The template marks everything waiting on the owner as [SQUARE BRACKET] copy. The build step leaves
those in place when a fact only the owner has is missing - a number, the guarantee terms, a review
count - and this check lists every one left, so the page cannot ship half-filled.

    python3 code/check_placeholders.py website/app/lp/<slug>/page.tsx
Exit 0 = none left. Exit 1 = placeholders remain (listed, with their line).
"""
import os
import re
import sys

PAT = re.compile(r"\[([^\]\n]{2,120})\]")
CODE = re.compile(r"^[\"'`{(]|%|\.length|=>|\{|\}|^[a-z_]+(?:, ?[a-z_]+)+$|^\d+(?:, ?\d+)*$|^[a-z_]+$|^\.\.\.|^[A-Z_][A-Z0-9_]*(?:, ?[A-Z_][A-Z0-9_]*)+$")


def is_placeholder(inner):
    """Copy waiting for the owner, not code: '[Business name]', '[+1 555 555 5555]', '[registered address]'.
    Not an array, an index or a list of variable names."""
    inner = inner.strip()
    return bool(re.search(r"[A-Za-z0-9]", inner)) and not CODE.search(inner)


def find(path):
    out = []
    for n, line in enumerate(open(path, encoding="utf-8"), 1):
        s = line.strip()
        if s.startswith("//") or s.startswith("{/*") or s.startswith("*"):
            continue          # the template's own instructions mention [SQUARE BRACKET]
        out += [(n, m.group(0)) for m in PAT.finditer(line) if is_placeholder(m.group(1))]
    return out


SLOT = re.compile(r"^\s*(\w+):\s*\{\s*fill:\s*(null|\[\])(?=[\s,]).*?hint:\s*\"([^\"]+)\"")
SLOT_FILES = ("slots.ts", "proof.tsx")


def empty_slots(folder):
    """Slots the owner has not filled yet (Jono, 28 September 2026). Not a blocker: an empty slot shows
    visitors its fallback, or nothing. This is the owner's to-do list, one line per slot."""
    out = []
    for name in SLOT_FILES:
        path = os.path.join(folder, name)
        if os.path.exists(path):
            for line in open(path, encoding="utf-8"):
                m = SLOT.match(line)
                if m:
                    out.append((name, m.group(1), m.group(3)))
    return out


if __name__ == "__main__":
    target = sys.argv[1]
    folder = target if os.path.isdir(target) else os.path.dirname(target)
    slots = empty_slots(folder)
    if slots:
        print(f"{len(slots)} slot(s) still empty - visitors see the fallback, or nothing, until each is filled:")
        for name, key, hint in slots:
            print(f"  {name} · {key} · {hint}")
    files = [os.path.join(folder, f) for f in sorted(os.listdir(folder)) if f.endswith(".tsx")] if os.path.isdir(target) else [target]
    left = [(os.path.basename(f), n, p) for f in files for n, p in find(f)]
    if not left:
        print("no placeholders left")
        sys.exit(0)
    print(f"{len(left)} placeholder(s) left - the page is not ready to go live:")
    for f, n, p in left:
        print(f"  {f} line {n}: {p}")
    sys.exit(1)
