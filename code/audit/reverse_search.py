"""Is this photo somewhere else on the internet? Reverse image search, before a photo is called real.

Jono, 26 and 28 September 2026: "a photo that looks like stock is reverse-image searched before it is
called real" - "make sure to reverse search the images to make sure they're not on stock websites".

TinEye answers a search by image URL with its matches and the domains they sit on. A reviewer's face
found on Unsplash or Shutterstock is a stock photo standing in for a real client, and that is the
finding that matters most on a page. No match proves nothing about AI images - a generated picture
is unique by definition - so the filename check in assets.py catches those ("ChatGPT-Image-...").

Searched: every reviewer photo, and every photo shown larger than a thumbnail, up to 25 per page,
politely spaced, cached per image URL so a re-run costs nothing.

    from audit.reverse_search import run
    found = run(facts, cache_dir)   # [{src, top, matches, stock_domains, verdict}]
"""
import json
import os
import re
import time
from urllib.parse import quote

import requests

UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) "
      "Chrome/128.0 Safari/537.36")
CAP = 25
STOCK_HOSTS = re.compile(
    r"unsplash|pexels|pixabay|shutterstock|istockphoto|gettyimages|stock\.adobe|adobestock|freepik|"
    r"depositphotos|dreamstime|alamy|123rf|rawpixel|bigstockphoto|stocksy|vecteezy|canva\.com|"
    r"pond5|storyblocks|envato|twenty20|burst\.shopify|kaboompics|stockvault|randomuser|pravatar|thispersondoesnotexist|"
    r"uifaces|generated\.photos|picsum", re.I)


def _search(url):
    api = f"https://tineye.com/api/v1/result_json/?url={quote(url, safe='')}&sort=score&order=desc"
    r = requests.get(api, headers={"User-Agent": UA, "Accept": "application/json"}, timeout=25)
    if r.status_code != 200 or "json" not in (r.headers.get("content-type") or ""):
        return {"error": f"TinEye answered {r.status_code}"}
    d = r.json()
    domains = []
    for m in d.get("matches") or []:
        dom = (m.get("domain") or "").lower()
        links = [b.get("url", "") for b in (m.get("backlinks") or [])]
        if dom and dom not in domains:
            domains.append(dom)
        for u in links:
            host = re.sub(r"^https?://(?:www\.)?([^/]+).*", r"\1", u.lower())
            if STOCK_HOSTS.search(host) and host not in domains:
                domains.append(host)
    stock = [x for x in domains if STOCK_HOSTS.search(x)]
    n = d.get("num_matches") or 0
    return {"matches": n, "stock_matches": d.get("num_stock_matches") or 0,
            "stock_domains": stock[:5], "elsewhere": [x for x in domains if x not in stock][:5],
            "verdict": "stock" if (stock or (d.get("num_stock_matches") or 0)) else ("found elsewhere" if n else "unique")}


def _targets(facts):
    """Reviewer photos first (a stock face beside a real name is the worst case), then big photos."""
    seen, out = set(), []
    for q in facts.get("quoteBlocks") or []:
        src = q.get("photoSrc") or ""
        if q.get("hasPhoto") and src.startswith("http") and src not in seen:
            seen.add(src)
            out.append({"src": src, "top": q.get("top"), "why": "reviewer photo"})
    for i in facts.get("images") or []:
        src = i.get("src") or ""
        if not src.startswith("http") or src in seen or re.search(r"\.svg(?:\?|$)|logo|icon|badge", src, re.I):
            continue
        if (i.get("w") or 0) >= 160 and (i.get("h") or 0) >= 110:
            seen.add(src)
            out.append({"src": src, "top": i.get("top"), "why": "photo"})
    return out[:CAP]


def run(facts, cache_dir, delay=1.2):
    """Search each target once; cached per image URL."""
    os.makedirs(cache_dir, exist_ok=True)
    path = os.path.join(cache_dir, "reverse-search.json")
    try:
        cache = json.load(open(path))
    except (OSError, ValueError):
        cache = {}
    out, fresh = [], 0
    for t in _targets(facts):
        res = cache.get(t["src"])
        if STOCK_HOSTS.search(t["src"]):
            res = {"matches": 0, "stock_matches": 1, "stock_domains": [re.sub(r"^https?://(?:www\.)?([^/]+).*", r"\1", t["src"])],
                   "elsewhere": [], "verdict": "stock"}
        if not res or res.get("error"):
            if fresh:
                time.sleep(delay)
            try:
                res = _search(t["src"])
            except Exception as e:  # noqa: BLE001
                res = {"error": " ".join(str(e).split())[:160]}
            fresh += 1
            if not res.get("error"):
                cache[t["src"]] = res
        out.append({**t, **res})
    try:
        json.dump(cache, open(path, "w"), indent=1)
    except OSError:
        pass
    return out
