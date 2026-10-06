"""The full on-page audit of one landing page. Everything opened, everything scored, two reports.

    python3 code/audit/page_audit.py <url>                       # capture, assets, Lighthouse, tracking, rubric, audit.md + audit.html
    python3 code/audit/page_audit.py <url> --judgments j.json    # re-score with Claude's judged items, rewrite both reports (no re-crawl)
    python3 code/audit/page_audit.py <url> --no-lighthouse       # skip the speed pass (it is the slow part)
    python3 code/audit/page_audit.py <url> --model trade         # override the business model for this run
    python3 code/audit/page_audit.py <url> --judgments j.json --fresh   # re-crawl AND apply the judgments (the after-build run)

Output folder: context/pages/<slug>/ - audit.md, audit.html, audit.json, judgments-needed.json, assets/ (every screenshot
and contact sheet). Downloads and Lighthouse JSON land in code/cache/audit/<slug>/ (gitignored).

judgments.json shape, written by Claude after reading the screenshots, sheets and transcripts:
  {"M1": {"score": 2, "reason": "...", "evidence": "mobile-fold.png: H1 reads ..."}, ..., "images": {"img-03": "the crew beside the van, real"}, "videos": {"video-0": "founder, says why + the 8-week promise"}}
"""
import argparse
import json
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))

from audit import assets as A, capture as C, report as R, report_html as RH, rubric as RB, speed as S, tracking as T  # noqa: E402
from audit.common import CODE, ROOT, cache_dir_for, out_dir_for, rel  # noqa: E402
import _business as biz  # noqa: E402


def business_ctx(model_override=None):
    md = biz.read()
    info = {"name": os.environ.get("BUSINESS_NAME", ""), "model": None, "converts_by": "", "judges_on": "", "job_value": ""}
    try:
        info.update(biz.model())
    except Exception:
        pass
    if model_override:
        info["model"] = RB.model_key(model_override) or model_override
    if not info["model"] and md:
        info["model"] = RB.model_key(biz.section(md, "business model") or biz.section(md, "what we do"))
    return info



def run(url, out=None, judgments_path=None, no_lighthouse=False, no_links=False, model=None, quiet=False, fresh=False, before=None):
    out_dir = out_dir_for(url, out); cache = cache_dir_for(url); assets_dir = os.path.join(out_dir, "assets")
    say = (lambda *a: None) if quiet else print
    t0 = time.time()
    business = business_ctx(model)
    prev = os.path.join(out_dir, "audit.json")
    if judgments_path and os.path.exists(prev) and not fresh:
        data = json.load(open(prev))
        cap, ast, sp, tr = data["capture"], data["assets"], data["speed"], data["tracking"]
        say("re-scoring from the last crawl")
    else:
        say(f"capturing {url} at three viewports")
        cap = C.capture(url, out_dir)
        say(f"  {cap['viewports']['mobile']['facts']['words']} words · {len(cap['viewports']['mobile']['facts']['images'])} images · {len(cap['viewports']['mobile']['facts']['links'])} links · load {cap['viewports']['mobile']['facts']['load_s']}s")
        say("opening every image, video and link")
        ast = A.collect(cap, url, cache, assets_dir) if not no_links else {"images": A.images(cap, cache, assets_dir), "videos": A.videos(cap, url, cache), "links": {"count": 0, "items": [], "leaks": 0, "by_kind": {}}}
        say(f"  {ast['images']['count']} images ({ast['images']['stock_suspects']} stock suspects) · {ast['videos']['count']} videos · {ast['links']['count']} links opened, {ast['links']['leaks']} leaks")
        say("checking the tracking plumbing")
        tr = T.tracking(url, cap, cache)
        say(f"  {len(tr['tel_numbers'])} phone number(s) · call tracking {tr['call_tracking']} · conversion script {tr['conversion_script']} · gclid kept {tr['gclid_persisted']['hidden'] or tr['gclid_persisted']['storage']}")
        if no_lighthouse:
            sp = {"source": "unavailable", "mobile": None, "desktop": None, "field": None, "note": "skipped with --no-lighthouse"}
        else:
            say("running Lighthouse, mobile and desktop (the slow part)")
            sp = S.lighthouse(url, cache)
            m = sp.get("mobile") or {}
            say(f"  {sp['source']} · performance {m.get('scores', {}).get('performance', '?')} · LCP {m.get('lcp_s', '?')}s · CLS {m.get('cls', '?')}")
    judgments = json.load(open(judgments_path)) if judgments_path and os.path.exists(judgments_path) else {}
    cap["viewports"]["desktop"]["facts"]["_judgments"] = judgments
    sc = RB.score(cap, ast, sp, tr, business, judgments)
    json.dump({"url": url, "business": business, "score": sc, "capture": cap, "assets": ast, "speed": sp, "tracking": tr, "judgments": judgments}, open(prev, "w"), indent=1, default=str)
    md = R.write(out_dir, url, sc, cap, ast, sp, tr, business, judgments)
    subprocess.run([sys.executable, os.path.join(CODE, "check_readable.py"), md], capture_output=True)

    # ---- the band walk: the page cut into sections, one card each (Jono, 27 Sep 2026) ----
    from audit import walk as W
    from audit.eighteen import roll as _roll
    facts = cap["viewports"]["desktop"]["facts"]
    facts["_mobile"] = {k: cap["viewports"]["mobile"]["facts"].get(k) for k in ("fixedTop", "fixedBottom", "tel")}
    # every reviewer photo and big photo, searched on TinEye before any of them is called real
    try:
        from audit.reverse_search import run as _reverse
        facts["reverseSearch"] = _reverse(facts, cache)
        _st = [r for r in facts["reverseSearch"] if r.get("verdict") == "stock"]
        say(f"{len(facts['reverseSearch'])} photos reverse-searched · {len(_st)} found on stock sites")
    except Exception as _e:
        facts["reverseSearch"] = []
        say(f"(reverse image search could not run: {_e})")
    r = _roll(sc)
    bands = W.build_bands(facts)
    try:
        from audit.markup import _pins
        from audit.copy_check import check as _cp
        hints = _pins(_cp(facts, business)["findings"], facts, sc, r, ast)
    except Exception as _e:
        hints = []
        say(f"(the code's own notes could not be gathered: {_e})")
    full = cap["viewports"]["desktop"]["shots"].get("full")
    if full and os.path.exists(full):
        W.crop(bands, full, facts.get("scrollHeight") or 0, assets_dir)
    need = W.sheet(facts, ast, bands, r, hints, url)
    json.dump(need, open(os.path.join(out_dir, "judgments-needed.json"), "w"), indent=1)
    say(f"{len(bands)} sections, top to bottom · screenshots in {rel(assets_dir)}/band-NN.png")

    if judgments.get("cards"):
        judgments = {**judgments, "_videos": W._vid_kinds(ast)}
        model, problems = W.finish(bands, judgments, facts, r)
    else:
        model, problems = None, [f"none of the {len(bands)} sections has been judged yet"]
    if problems:
        html = RH.write_unfinished(out_dir, url, problems, len(bands))
        say(f"⛔ NOT FINISHED - {len(problems)} thing(s) still open, so no report was written:")
        for p_ in problems[:25]:
            say(f"   - {p_}")
        say(f"judge every section in {rel(os.path.join(out_dir, 'judgments-needed.json'))}, save it as "
            f"judgments.json beside it, and re-run with --judgments")
    else:
        html = RH.write(out_dir, url, model, cap)
        t = model["tally"]
        say(f"{t['ok']} of {t['total']} components in place · fix {t['weak']} · missing {t['missing']} · not counted {len(t['left_out'])} · "
            f"cut {t['cut']} of {len(bands)} sections · {len(model['boxes'])} boxes, {len(model['cards'])} cards")
    say(f"{round(time.time() - t0)}s\nreport: {rel(md)}\npage:   {rel(html)}")
    return sc, out_dir


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("url"); ap.add_argument("--out"); ap.add_argument("--judgments"); ap.add_argument("--no-lighthouse", action="store_true"); ap.add_argument("--no-links", action="store_true"); ap.add_argument("--model"); ap.add_argument("--fresh", action="store_true", help="re-crawl even when judgments are given")
    ap.add_argument("--before", help="an earlier audit.json; the page then shows what was ticked off since")
    a = ap.parse_args()
    run(a.url, a.out, a.judgments, a.no_lighthouse, a.no_links, a.model, fresh=a.fresh, before=a.before)
