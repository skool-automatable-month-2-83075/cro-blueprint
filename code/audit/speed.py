"""Lighthouse, mobile and desktop, without asking the member to install anything.

Order: PageSpeed Insights when PAGESPEED_API_KEY is set (free key, Google's servers run it), otherwise a local
Lighthouse through `npx --yes lighthouse@latest` (installs itself the first time, cached by npx). Both give the
same Lighthouse result object, so one parser reads both. CrUX field data comes back only from PSI, and only
when the origin has enough traffic; otherwise the report says "lab only".

    from audit.speed import lighthouse
    speed = lighthouse(url, cache_dir)   # {"source": "psi"|"local"|"unavailable", "mobile": {...}, "desktop": {...}, "field": {...}|None}
"""
import json
import os
import shutil
import subprocess
import urllib.parse
import urllib.request

CATEGORIES = ["performance", "accessibility", "best-practices", "seo"]
PSI = "https://www.googleapis.com/pagespeedonline/v5/runPagespeed"


def _num(audits, key, div=1.0):
    v = (audits.get(key) or {}).get("numericValue")
    return round(v / div, 2) if isinstance(v, (int, float)) else None


def parse_lhr(lhr):
    a = lhr.get("audits") or {}
    cats = lhr.get("categories") or {}
    score = lambda c: round(100 * ((cats.get(c) or {}).get("score") or 0))
    lcp_el = ""
    try:
        lcp_el = a["largest-contentful-paint-element"]["details"]["items"][0]["items"][0]["node"]["snippet"][:160]
    except Exception:
        pass
    opps = []
    for k, v in a.items():
        d = v.get("details") or {}
        if d.get("type") == "opportunity" and (d.get("overallSavingsMs") or 0) > 50:
            opps.append({"title": v.get("title", k), "savings_ms": round(d.get("overallSavingsMs") or 0), "savings_kb": round((d.get("overallSavingsBytes") or 0) / 1024)})
    opps.sort(key=lambda o: -o["savings_ms"])
    third = a.get("third-party-summary") or {}
    third_kb = None
    try:
        third_kb = round((third["details"]["summary"].get("wastedBytes") or 0) / 1024)
        third_items = [{"entity": i.get("entity", {}).get("text") if isinstance(i.get("entity"), dict) else i.get("entity"), "kb": round((i.get("transferSize") or 0) / 1024), "blocking_ms": round(i.get("blockingTime") or 0)} for i in third["details"]["items"][:6]]
    except Exception:
        third_items = []
    contrast = None
    try:
        contrast = len(a["color-contrast"]["details"]["items"])
    except Exception:
        pass
    render_blocking = []
    try:
        render_blocking = [i.get("url", "")[:100] for i in a["render-blocking-resources"]["details"]["items"][:5]]
    except Exception:
        pass
    return {
        "scores": {c: score(c) for c in CATEGORIES},
        "lcp_s": _num(a, "largest-contentful-paint", 1000), "fcp_s": _num(a, "first-contentful-paint", 1000),
        "si_s": _num(a, "speed-index", 1000), "tbt_ms": _num(a, "total-blocking-time"), "cls": _num(a, "cumulative-layout-shift"),
        "tti_s": _num(a, "interactive", 1000),
        "lcp_element": lcp_el, "lcp_lazy_loaded_ok": (a.get("lcp-lazy-loaded") or {}).get("score") in (1, None),
        "contrast_failures": contrast, "opportunities": opps[:5], "third_party_kb": third_kb, "third_party": third_items,
        "render_blocking": render_blocking,
        "total_kb": round(((a.get("total-byte-weight") or {}).get("numericValue") or 0) / 1024),
        "unused_js_kb": round((((a.get("unused-javascript") or {}).get("details") or {}).get("overallSavingsBytes") or 0) / 1024),
    }


def _field(psi_json):
    out = {}
    for scope, key in (("page", "loadingExperience"), ("origin", "originLoadingExperience")):
        le = psi_json.get(key) or {}
        m = le.get("metrics") or {}
        if not m:
            continue
        out[scope] = {"overall": le.get("overall_category"),
                      "lcp_ms": (m.get("LARGEST_CONTENTFUL_PAINT_MS") or {}).get("percentile"),
                      "inp_ms": (m.get("INTERACTION_TO_NEXT_PAINT") or {}).get("percentile"),
                      "cls": ((m.get("CUMULATIVE_LAYOUT_SHIFT_SCORE") or {}).get("percentile") or 0) / 100}
    return out or None


def _psi(url, strategy, key):
    q = [("url", url), ("strategy", strategy), ("key", key)] + [("category", c) for c in CATEGORIES]
    req = urllib.request.Request(PSI + "?" + urllib.parse.urlencode(q), headers={"User-Agent": "cro-blueprint-pro"})
    with urllib.request.urlopen(req, timeout=180) as r:
        return json.load(r)


def _local(url, strategy, cache_dir, max_age_h=24):
    if not shutil.which("npx"):
        return None, "npx not found - install Node.js"
    out = os.path.join(cache_dir, f"lighthouse-{strategy}.json")
    import time
    if os.path.exists(out) and time.time() - os.path.getmtime(out) < max_age_h * 3600 and os.path.getsize(out) > 10000:
        try:
            return json.load(open(out)), None   # today's run, reused - Lighthouse is the slow part
        except ValueError:
            pass
    cmd = ["npx", "--yes", "lighthouse@latest", url, "--output=json", f"--output-path={out}", "--quiet",
           "--chrome-flags=--headless=new --no-sandbox --disable-gpu", "--only-categories=" + ",".join(CATEGORIES)]
    if strategy == "desktop":
        cmd.append("--preset=desktop")
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
    except subprocess.TimeoutExpired:
        return None, "local Lighthouse timed out after 5 minutes"
    if p.returncode != 0 or not os.path.exists(out):
        return None, "local Lighthouse failed: " + (p.stderr or p.stdout)[-300:].strip()
    return json.load(open(out)), None


def lighthouse(url, cache_dir):
    key = os.environ.get("PAGESPEED_API_KEY", "").strip()
    result = {"source": "unavailable", "mobile": None, "desktop": None, "field": None, "note": ""}
    if key:
        try:
            for strategy in ("mobile", "desktop"):
                j = _psi(url, strategy, key)
                json.dump(j, open(os.path.join(cache_dir, f"psi-{strategy}.json"), "w"))
                result[strategy] = parse_lhr(j.get("lighthouseResult") or {})
                if strategy == "mobile":
                    result["field"] = _field(j)
            result["source"] = "psi"
            return result
        except Exception as e:  # noqa: BLE001 - fall through to local
            result["note"] = f"PageSpeed API failed ({str(e)[:80]}), used local Lighthouse. "
    for strategy in ("mobile", "desktop"):
        lhr, err = _local(url, strategy, cache_dir)
        if lhr:
            result[strategy] = parse_lhr(lhr)
            result["source"] = "local"
        else:
            result["note"] += (err or "") + " "
    if result["source"] == "local":
        result["note"] += "Lab numbers only, no field data (needs a PageSpeed key and 28 days of Chrome traffic)."
    return result


if __name__ == "__main__":
    import sys
    from .common import cache_dir_for
    r = lighthouse(sys.argv[1], cache_dir_for(sys.argv[1]))
    print(json.dumps({k: v for k, v in r.items() if k != "field"}, indent=1)[:3000])
