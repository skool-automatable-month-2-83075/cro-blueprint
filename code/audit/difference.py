"""How different two pages are, as one number out of 100, and how different they need to be.

    python3 code/audit/difference.py <control-url> <challenger-url>
    python3 code/audit/difference.py "http://localhost:3000/lp/x?preview=control" "http://localhost:3000/lp/x?preview=test" --leads-per-month 40

⛔ WHY (Jono, 28 September 2026). Two pages that look alike cannot be told apart at the traffic most
owners have: the test runs for months and ends flat. So the challenger is scored before it goes live,
and a page under the bar is widened before anyone sends traffic to it.

⛔ THE BAR COMES DOWN WITH EVERY TEST CALLED ON THE PAGE. The first test is a big swing: the big wins
are still unfound, and only a big difference reads at low traffic. Each called test finds some of what
matters, so the next challenger can be narrower. The bar never drops below what the traffic can
resolve. Both curves are the constants below - a heuristic, stated as one, not a law.

What is scored, out of 100:
- 30 · the first screen: the words a visitor sees before scrolling, and the pixels, phone and desktop
- 25 · the words: how much of the page's copy is new
- 20 · the shape: sections added, removed, renamed or moved
- 15 · the ask: the form's fields, where the form sits, what the buttons say
- 10 · the pictures: which images are shown
The social proof and the design are held fixed on purpose, so even a page changed everywhere else tops
out below 100. That is expected, and the bar allows for it.
"""
import argparse
import difflib
import json
import os
import re
import sys
from urllib.parse import urlparse

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))

from audit.common import ROOT, cache_dir_for  # noqa: E402

WEIGHTS = {"first screen": 30, "words": 25, "shape": 20, "the ask": 15, "pictures": 10}
BAR_START, BAR_STEP = 50, 10           # first test 50, then 40, 30, 20 as tests are called
TRAFFIC_FLOORS = ((60, 35), (300, 25))  # leads a month under N -> the bar never goes below this
TRAFFIC_FLOOR_HIGH = 15
UNKNOWN_TRAFFIC_FLOOR = 35              # no lead count given: assume the low-traffic floor
PIXEL_FULL = 0.15                       # a mean pixel change this large counts as a fully new first screen
VIEWPORTS = {"desktop": {"viewport": {"width": 1366, "height": 768}},
             "phone": {"viewport": {"width": 390, "height": 844}, "is_mobile": True, "has_touch": True}}
CALLED = re.compile(r"\*\*Status:\*\*\s*(called|won|lost|flat|shipped|killed|inconclusive)", re.I)
LEVERS = {
    "first screen": "Change what a visitor sees before scrolling: the headline, the hero image, where the form sits.",
    "words": "Rewrite more of the copy: the benefits, the features, the FAQ answers.",
    "shape": "Add, remove or reorder whole sections.",
    "the ask": "Change the form: fewer or different fields, a different place, different button words.",
    "pictures": "Swap the images for different ones: real work, real people, the deliverable.",
}

PROBE = """() => {
  const vis = e => { const r = e.getBoundingClientRect(), s = getComputedStyle(e);
    return r.width > 0 && r.height > 0 && s.visibility !== 'hidden' && s.display !== 'none'; };
  const main = document.querySelector('main') || document.body;
  const fold = [], w = document.createTreeWalker(main, NodeFilter.SHOW_TEXT);
  for (let n; (n = w.nextNode());) {
    const el = n.parentElement;
    if (el && n.textContent.trim() && vis(el) && el.getBoundingClientRect().top + scrollY < innerHeight) fold.push(n.textContent.trim());
  }
  const form = document.querySelector('form');
  return {
    text: main.innerText,
    fold: fold.join(' '),
    heads: [...main.querySelectorAll('h1, h2')].filter(vis).map(h => h.innerText.trim()),
    fields: form ? [...form.querySelectorAll('input, select, textarea')]
      .filter(e => e.type !== 'hidden' && e.type !== 'radio' && e.name !== 'company_fax' && vis(e)).map(e => e.name) : [],
    radios: form ? [...new Set([...form.querySelectorAll('input[type=radio]')].map(e => e.name))] : [],
    form_at: form ? (form.getBoundingClientRect().top + scrollY) / document.documentElement.scrollHeight : null,
    ctas: [...main.querySelectorAll('a[href^="#"], a[data-l], button[type=submit]')].filter(vis).map(a => a.innerText.trim()).filter(Boolean),
    images: [...main.querySelectorAll('img')].filter(vis).map(i => i.currentSrc || i.src),
  };
}"""


def capture(url, tag):
    """Both viewports: the probe, plus a first-screen screenshot for the pixel comparison."""
    from playwright.sync_api import sync_playwright
    out, cache = {}, cache_dir_for(url)
    os.makedirs(cache, exist_ok=True)
    with sync_playwright() as p:
        b = p.chromium.launch(headless=True)
        for name, opts in VIEWPORTS.items():
            ctx = b.new_context(**opts)
            pg = ctx.new_page()
            pg.goto(url, wait_until="networkidle", timeout=60000)
            pg.wait_for_timeout(600)
            shot = os.path.join(cache, f"difference-{tag}-{name}.png")
            pg.screenshot(path=shot)
            out[name] = {**pg.evaluate(PROBE), "shot": shot}
            ctx.close()
        b.close()
    return out


def shingles(text, k=3):
    words = re.findall(r"[a-z0-9$%]+", (text or "").lower())
    return {tuple(words[i:i + k]) for i in range(max(0, len(words) - k + 1))}


def apart(a, b):
    """0 when two sets are the same, 1 when they share nothing."""
    a, b = set(a), set(b)
    return 0.0 if not a and not b else 1 - len(a & b) / len(a | b)


def pixels_apart(p1, p2):
    from PIL import Image, ImageChops, ImageStat
    a = Image.open(p1).convert("L").resize((96, 64))
    b = Image.open(p2).convert("L").resize((96, 64))
    mean = ImageStat.Stat(ImageChops.difference(a, b)).mean[0] / 255
    return min(1.0, mean / PIXEL_FULL)


def parts(ca, cb):
    d_a, d_b = ca["desktop"], cb["desktop"]
    fold = sum(0.6 * apart(shingles(ca[v]["fold"]), shingles(cb[v]["fold"])) + 0.4 * pixels_apart(ca[v]["shot"], cb[v]["shot"])
               for v in VIEWPORTS) / len(VIEWPORTS)
    moved = abs((d_a["form_at"] or 1) - (d_b["form_at"] or 1))
    ask = (0.4 * apart(d_a["fields"] + d_a["radios"], d_b["fields"] + d_b["radios"])
           + 0.3 * min(1.0, moved / 0.5) + 0.3 * apart(d_a["ctas"], d_b["ctas"]))
    return {
        "first screen": fold,
        "words": apart(shingles(d_a["text"]), shingles(d_b["text"])),
        "shape": 1 - difflib.SequenceMatcher(None, d_a["heads"], d_b["heads"]).ratio(),
        "the ask": ask,
        "pictures": apart(d_a["images"], d_b["images"]),
    }


def tests_called(path):
    """Tests already called on this page, from context/test-log.md."""
    p = os.path.join(ROOT, "context", "test-log.md")
    if not os.path.exists(p):
        return 0
    n = 0
    for block in re.split(r"\n(?=## Test )", open(p, encoding="utf-8").read()):
        head = block.splitlines()[0] if block else ""
        if head.startswith("## Test ") and path.rstrip("/") + " " in head.rstrip("/") + " " and CALLED.search(block):
            n += 1
    return n


def bar(called, leads_per_month):
    if leads_per_month is None:
        floor = UNKNOWN_TRAFFIC_FLOOR
    else:
        floor = next((f for limit, f in TRAFFIC_FLOORS if leads_per_month < limit), TRAFFIC_FLOOR_HIGH)
    return max(floor, BAR_START - BAR_STEP * called), floor


def score(control, challenger, leads_per_month=None, page=None):
    ca, cb = capture(control, "control"), capture(challenger, "challenger")
    p = parts(ca, cb)
    points = {k: round(WEIGHTS[k] * v, 1) for k, v in p.items()}
    total = round(sum(points.values()))
    path = page or urlparse(control).path
    called = tests_called(path)
    need, floor = bar(called, leads_per_month)
    weakest = sorted(points, key=lambda k: points[k] / WEIGHTS[k])[:2]
    return {"control": control, "challenger": challenger, "score": total, "bar": need, "floor": floor,
            "tests_called": called, "leads_per_month": leads_per_month, "different_enough": total >= need,
            "points": points, "out_of": WEIGHTS, "widen": [LEVERS[k] for k in weakest] if total < need else []}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("control")
    ap.add_argument("challenger")
    ap.add_argument("--leads-per-month", type=float)
    ap.add_argument("--page", help="the page path in context/test-log.md, when the URLs carry a preview flag")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    r = score(a.control, a.challenger, a.leads_per_month, a.page)
    if a.json:
        print(json.dumps(r, indent=1))
        return
    verdict = "different enough" if r["different_enough"] else "TOO SIMILAR - widen it before it goes live"
    print(f"# Difference · {r['score']} of 100 · bar {r['bar']} · {verdict}")
    print(f"- Bar: {BAR_START} for a first test, {BAR_STEP} lower per called test, floor {r['floor']}")
    print(f"- Tests already called on this page: {r['tests_called']}")
    print(f"- Leads a month: {r['leads_per_month'] if r['leads_per_month'] is not None else 'not given, so the low-traffic floor'}")
    for k, v in r["points"].items():
        print(f"- {k}: {v} of {WEIGHTS[k]}")
    for w in r["widen"]:
        print(f"- Widen: {w}")


if __name__ == "__main__":
    main()
