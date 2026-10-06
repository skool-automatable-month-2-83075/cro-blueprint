"""audit.md - the audit as a file an owner acts on. House shape: three lines at the top, decision first."""
import os
import re
from datetime import date

from .common import ROOT, rel
from .rubric import AREAS

STATUS_WORD = {"PASS": "PASS", "PARTIAL": "PARTLY", "FAIL": "FAIL", "PENDING": "AWAITING CLAUDE'S READ", "N/A": "not for this model"}


def _fixes(sc):
    rows = [r for r in sc["rows"] if r["status"] in ("FAIL", "PARTIAL")]
    rows.sort(key=lambda r: -(r["points"] - r["earned"]))
    return rows


def write(out_dir, url, sc, cap, assets, speed, tracking, business, judgments):
    m = cap["viewports"]["mobile"]["facts"]
    sp = (speed or {}).get("mobile") or {}
    today = date.today().isoformat()
    fixes = _fixes(sc)
    prov = " · provisional, awaiting Claude's read on the judged items" if sc["provisional"] else ""
    top = fixes[0] if fixes else None
    L = [f"# Landing page audit · {url}",
         f"{sc['total']} of 100 · grade {sc['grade']} of 10{prov} · {sum(1 for r in sc['rows'] if r['status'] == 'PASS')} pass · {sum(1 for r in sc['rows'] if r['status'] == 'FAIL')} fail · {today}",
         f"Next: {top['fix']}" if top else "Next: nothing failing - send the assets list to the owner.", ""]
    L += ["## The business", "", f"- Model: {business.get('model') or 'NOT SET - the score above ignores business fit until it is'}",
          f"- Benchmark for this model: {sc.get('benchmark') or 'set the model first'}", f"- The mobile bar for this model: {sc.get('bar') or 'set the model first'}",
          f"- A lead converts by: {business.get('converts_by') or 'not set'}", f"- The buyer judges on: {business.get('judges_on') or 'not set'}", ""]
    L += ["## Do this first", ""]
    for r in fixes[:12]:
        L += [f"### {r['id']} · {r['name']} · {r['points'] - r['earned']:.1f} points to gain", f"- Found: {r['evidence'] or r['reason']}", f"- Fix: {r['fix']}", ""]
    for a, label, pts in AREAS:
        t = sc["areas"][a]
        L += [f"## {label} · {t['earned']:.1f} of {t['possible']:.0f}" + (f" · {t['pending']:.0f} awaiting Claude" if t["pending"] else ""), ""]
        for r in sc["rows"]:
            if r["area"] != a:
                continue
            L.append(f"- {r['id']} {r['name']} · {STATUS_WORD[r['status']]} · {r['earned']:.1f} of {r['points']}")
            if r["evidence"]:
                L.append(f"  - {r['evidence'][:190]}")
            if r["reason"]:
                L.append(f"  - {r['reason'][:190]}")
        L.append("")
    L += ["## The three screens", ""]
    for vp in ("mobile", "tablet", "desktop"):
        f = cap["viewports"][vp]["facts"]; s = cap["viewports"][vp]["shots"]
        L += [f"### {vp} · {f['viewport']['w']}x{f['viewport']['h']}",
              f"- {f['ctasAbove']} CTAs above the fold · {f['ctasTotal']} in total · fixed bars {len(f['fixedBottom'])}",
              f"- horizontal scroll {f['overflowX']} · {f['smallText']} tiny text nodes · {f['smallTaps']} small taps",
              f"- fold: {rel(s['fold'])}", f"- full page: {rel(s['full'])}", ""]
    im = assets["images"]; vd = assets["videos"]; lk = assets["links"]
    L += ["## Every image", "", f"- {im['count']} images · {im['stock_suspects']} stock or generated suspects · {im['upscaled']} upscaled · {im['heavy']} over 300 KB · {im['alt_missing']} big images without alt text"]
    notes = (judgments or {}).get("images", {})
    for i, r in enumerate(im["items"][:40]):
        flags = " · ".join(x for x, ok in (("STOCK?", r["stock_suspect"]), ("UPSCALED", r["upscaled"]), ("HEAVY", (r["kb"] or 0) > 300), ("no alt", r["alt_missing"] and r["big"])) if ok)
        what = notes.get(f"img-{i:02d}") or notes.get(str(i)) or ""
        L.append(f"- img-{i:02d} · {r['naturalW']}x{r['naturalH']} · {r['kb']} KB · {r['format']}" + (f" · {flags}" if flags else ""))
        if what or r["alt"]:
            L.append(f"  - {what or 'alt: ' + r['alt'][:100]}")
    for s in im["sheets"]:
        L.append(f"- contact sheet: {rel(s)}")
    L.append("")
    L += ["## Every video", "", f"- {vd['count']} videos · {vd['third_party']} third-party embeds · {vd['autoplay']} autoplay · {vd['no_poster']} without a poster"]
    vnotes = (judgments or {}).get("videos", {})
    for i, v in enumerate(vd["items"]):
        L.append(f"- video-{i} · {v['kind']} · {v['duration_s'] or '?'}s · poster {bool(v['poster'])} · autoplay {v['autoplay']} · transcript {v.get('transcript_words', 0)} words")
        tr = (v.get("transcript") or "")
        L.append(f"  - {vnotes.get(f'video-{i}') or (tr[:180] if tr else 'no transcript')}")
    L.append("")
    L += ["## Every link that leaves the page", "", f"- {lk['count']} links opened · {lk['leaks']} leaks (anything that is not privacy or terms)"]
    for r in lk["items"]:
        L.append(f"- {r['kind']} · \"{r['text'][:40]}\" · {r['url'][:80]}")
        L.append(f"  - {r['title'][:80] or r['status']}" + (f" · {r['page_text'][:100]}" if r["page_text"] else ""))
    L.append("")
    L += ["## Speed", ""]
    if sp:
        L += [f"- Source: {speed['source']} · mobile performance {sp['scores']['performance']} · accessibility {sp['scores']['accessibility']} · best practices {sp['scores']['best-practices']} · SEO {sp['scores']['seo']}",
              f"- LCP {sp['lcp_s']}s · CLS {sp['cls']} · TBT {sp['tbt_ms']}ms · speed index {sp['si_s']}s",
              f"- LCP element: {sp['lcp_element'][:120] or 'unknown'}", f"- Page weight {sp['total_kb']} KB · third party {sp['third_party_kb']} KB · unused JS {sp['unused_js_kb']} KB"]
        for o in sp["opportunities"]:
            L.append(f"- Opportunity: {o['title']} · saves about {o['savings_ms']} ms" + (f" · {o['savings_kb']} KB" if o["savings_kb"] else ""))
        if speed.get("desktop"):
            dk = speed["desktop"]; L.append(f"- Desktop: performance {dk['scores']['performance']} · LCP {dk['lcp_s']}s · CLS {dk['cls']}")
        if speed.get("field"):
            for scope, f in speed["field"].items():
                L.append(f"- Real users ({scope}): {f['overall']} · LCP {f['lcp_ms']} ms · INP {f['inp_ms']} ms · CLS {f['cls']}")
        else:
            L.append("- Real-user data: none (lab numbers only)")
    else:
        L.append(f"- Lighthouse did not run: {(speed or {}).get('note', '')}")
    L.append("")
    L += ["## Tracking", "", f"- Phone numbers: {len(tracking['tel_numbers'])} · call tracking {tracking['call_tracking']} · conversion script {tracking['conversion_script']} · replay {tracking['replay_tool']}",
          f"- Scripts present: {', '.join(k for k, v in tracking['scripts'].items() if v) or 'none'}",
          f"- gclid kept: hidden {tracking['gclid_persisted']['hidden']} · storage {tracking['gclid_persisted']['storage']} · UTMs kept {tracking['utm_persisted']}"]
    ty = tracking.get("thank_you") or {}
    L.append(f"- Thank-you page: " + (f"exists · noindex {ty['noindex']} · {ty['nav_links']} nav links · tel {ty['tel']} · calendar {ty['calendar']} · callback time {ty['callback_wording']}" if ty.get("exists") else "none at /thank-you"))
    if tracking.get("check_tracking"):
        L += ["- check_tracking.py:"] + [f"  {l}" for l in tracking["check_tracking"]["lines"][:10]]
    L.append("")
    path = os.path.join(out_dir, "audit.md")
    open(path, "w").write("\n".join(_tidy(L)))
    return path


def _tidy(lines, max_facts=4, max_chars=195):
    """Keep every bullet readable on a phone: at most four facts a line, never over ~195 characters.
    Longer bullets become a lead line plus sub-bullets of three facts each; over-long single facts are cut."""
    out = []
    for l in lines:
        m = re.match(r"^(\s*)- (.*)$", l)
        if not m:
            out.append(l); continue
        ind, body = m.group(1), m.group(2)
        facts = [f.strip() for f in body.split(" · ") if f.strip()]
        # `Label: a · b · c` - a label with several values goes underneath, one value a line
        lab = re.match(r"^([A-Z][^:·]{0,40}):\s*(.+)$", body)
        if lab and len(facts) > 1:
            out.append(f"{ind}- {lab.group(1)}:")
            vals = [v.strip() for v in lab.group(2).split(" · ") if v.strip()]
            for v in vals[:8]:
                out.append(f"{ind}  - {v[:max_chars]}")
            if len(vals) > 8:
                out.append(f"{ind}  - and {len(vals) - 8} more")
            continue
        if len(facts) <= max_facts and len(body) <= max_chars:
            out.append(l); continue
        if len(facts) > 1:
            head, rest = facts[0], facts[1:]
            out.append(f"{ind}- {head[:max_chars]}")
            for i in range(0, len(rest), 3):
                chunk = " · ".join(rest[i:i + 3])
                out.append(f"{ind}  - {chunk[:max_chars]}")
        else:
            words = body.split(" "); cur = ""
            first = True
            for w in words:
                if len(cur) + len(w) + 1 > max_chars:
                    out.append(f"{ind}{'- ' if first else '  - '}{cur.strip()}"); first = False; cur = ""
                cur += w + " "
            if cur.strip():
                out.append(f"{ind}{'- ' if first else '  - '}{cur.strip()}")
    return out
