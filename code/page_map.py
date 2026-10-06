"""Name every section of a page by code, so the heat map, the scroll map and every finding say the same words.

    python3 code/page_map.py http://localhost:3000/lp/drain-cleaning        # -> code/cache/pagemap-lp-drain-cleaning-{mobile,desktop}.json + full-page screenshots
    python3 code/page_map.py https://example.com/lp/drain-cleaning --slug lp-drain-cleaning

Two viewports: mobile 390 wide and desktop 1366 wide, the same classes PostHog's heat map splits on. Per section: a short
name (the first section is "Hero", the one holding the form is "Form", the rest are their heading cut to six words), its
top and bottom in page pixels, the heading, and every clickable thing inside it with its box. Reuses the DOM probe from
code/audit/capture.py; never opens a window. No change to the website: every template page already has section headings.

Importable: slug_for(page), load(slug, viewport), names(m), section_at(m, y), section_list(m).
"""
import argparse
import json
import os
import re
import sys
from datetime import datetime
from urllib.parse import urlparse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import _posthog as ph  # noqa: E402  ROOT, CACHE, and it loads .env
from audit.botcheck import BLOCKED, settle  # noqa: E402

SCREENS = os.path.join(ph.CACHE, "screens")
MAX_SHOT = 16000       # Chromium refuses a full-page screenshot much taller than this; the map still covers the whole page
MOBILE_UA = "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1"
DESKTOP_UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0 Safari/537.36"
VIEWPORTS = {
    "mobile": {"width": 390, "height": 844, "ua": MOBILE_UA, "mobile": True},
    "desktop": {"width": 1366, "height": 768, "ua": DESKTOP_UA, "mobile": False},
}


def slug_for(page):
    """'/lp/drain-cleaning' or a full URL -> 'lp-drain-cleaning'. The key every cache file uses."""
    path = urlparse(page).path if "://" in page else page
    return re.sub(r"[^a-z0-9]+", "-", path.lower()).strip("-") or "home"


def split_page(page):
    """'/lp/x' -> ('', '/lp/x'). 'one audited site' or 'https://www.one audited site/audit' -> ('one audited site', '/audit').

    A page on this site is a path. A page on another site in the same PostHog project is named by its host,
    and a path alone cannot find it: a homepage's pathname is a bare '/', which is every site's homepage."""
    p = (page or "").strip()
    if not p or p.startswith("/"):
        return "", p
    u = urlparse(p if "://" in p else "//" + p)
    return re.sub(r"^www\.", "", u.netloc.lower()), u.path or "/"


def page_sql(page, prop="$pathname"):
    """The WHERE fragment for a page on another site: its host, and the homepage matched exactly.
    '' for a plain path, where each script keeps its own pattern."""
    host, path = split_page(page)
    if not host:
        return ""
    on_path = (f"properties.{prop} = '/'" if path == "/"
               else f"properties.{prop} like {ph.sql_str(path.rstrip('/') + '%')}")
    return f"properties.$host like {ph.sql_str('%' + host)} and {on_path}"


def path_for(slug, viewport):
    return os.path.join(ph.CACHE, f"pagemap-{slug}-{viewport}.json")


def load(slug, viewport="mobile"):
    p = path_for(slug, viewport)
    return json.load(open(p)) if os.path.exists(p) else None


def names(m):
    return [s["name"] for s in (m or {}).get("sections", [])]


def section_at(m, y):
    """The section name at page pixel y. Above the first section is the first; below the last is the last."""
    secs = (m or {}).get("sections") or []
    if not secs:
        return "Page"
    for s in secs:
        if s["top"] <= y < s["bottom"]:
            return s["name"]
    return secs[0]["name"] if y < secs[0]["top"] else secs[-1]["name"]


def section_list(m):
    """The page as a numbered list: every section name and what is tappable in each."""
    lines = []
    for n, s in enumerate((m or {}).get("sections", []), 1):
        taps = ", ".join(dict.fromkeys(c["text"] for c in s.get("clickables", []) if c.get("text")))[:120]
        head = f' · "{s["heading"][:70]}"' if s.get("heading") else ""
        lines.append(f"{n}. {s['name']} · {s['top']} to {s['bottom']}px{head}" + (f" · tap: {taps}" if taps else ""))
    sticky = ", ".join(dict.fromkeys(c["text"] for c in (m or {}).get("sticky", []) if c.get("text")))
    if sticky:
        lines.append(f"Always on screen, a sticky bar: {sticky}")
    return "\n".join(lines)


def _short(text, words=6):
    """Six words, but never cut mid-phrase: stop at the last full word and drop a trailing joining word."""
    h = re.sub(r"\s+", " ", text or "").strip()
    h = re.sub(r"[.!?:,;]+$", "", h)
    parts = h.split(" ")[:words]
    while parts and parts[-1].lower() in ("the", "a", "an", "and", "or", "of", "to", "for", "in", "on", "with", "that", "other", "your", "our"):
        parts.pop()
    return " ".join(parts)


def _name(sec, i, has_form, taken):
    # the first section is the Hero even when the form sits inside it - that is the fold, and it is what a
    # visitor and an owner both call it. A later section holding the form is the Form.
    if i == 0:
        base = "Hero"
    elif has_form:
        base = "Form"
    else:
        # no heading: name it after what it holds, so a band never reads "Section 2"
        base = _short(sec.get("heading")) or (sec.get("_label") or f"Band {i + 1}")
    name, k = base, 2
    while name in taken:
        name, k = f"{base} {k}", k + 1
    return name


def _clickables(facts):
    out, seen = [], set()
    def add(c, kind, tag):
        key = (c.get("text", ""), c.get("top"), c.get("left"))
        if key in seen or not c.get("visible", True):
            return
        seen.add(key)
        out.append({"text": (c.get("text") or "")[:60], "tag": tag, "kind": kind, "href": c.get("href", ""),
                    "top": c.get("top", 0), "left": c.get("left", 0), "w": c.get("w", 0), "h": c.get("h", 0), "fixed": bool(c.get("fixed"))})
    for c in facts.get("tel", []):
        add(c, "call", "a")
    for c in facts.get("sms", []):
        add(c, "text", "a")
    for c in facts.get("ctas", []):
        add(c, "cta", c.get("tag", "a"))
    for c in facts.get("links", []):
        if c.get("where") == "body":
            add(c, "link", "a")
    return out


def build(url, slug, viewport, vp, facts, shot, page_height):
    secs = facts.get("sections") or []
    form = (facts.get("forms") or [None])[0]
    form_top = form["top"] if form else None
    clicks = _clickables(facts)
    out, taken = [], set()
    for s in secs:
        top, bottom = int(s["top"]), int(s["top"] + s["h"])
        has_form = (s.get("id") == "lead-form") or (form_top is not None and top <= form_top < bottom)
        # A section with no heading is named for what it holds, so a band never reads "Band 2".
        # Its own text is judged first: a testimonial and a stats strip have no image to go on.
        if not (s.get("heading") or "").strip():
            body = re.sub(r"\s+", " ", (s.get("text") or "")).strip()
            here = lambda items: [it for it in (items or []) if top <= (it.get("top") or 0) < bottom]
            imgs = here(facts.get("images"))
            vids = here(facts.get("videos")) + [f for f in here(facts.get("iframes"))
                                                if f.get("provider") in ("youtube", "vimeo", "loom", "wistia")]
            numbers = len(re.findall(r"\d[\d,.]*\s*[%+kKmM]\b|\b\d{3,}\b", body))
            if vids:
                s["_label"] = "The video"
            elif re.search(r"[“‘\"]", body[:120]):
                s["_label"] = "A testimonial"
            elif numbers >= 2 and len(body) < 400:
                s["_label"] = "Proof numbers"
            elif len(imgs) >= 4 and len(body) < 200:
                s["_label"] = "Logo strip"
            elif any(top <= (c.get("top") or 0) < bottom for c in clicks if c.get("kind") == "cta"):
                s["_label"] = "Call to action"
            elif imgs:
                s["_label"] = "A picture"
        name = _name(s, s["i"], has_form, taken)
        taken.add(name)
        inside = [c for c in clicks if not c["fixed"] and top <= c["top"] < bottom]
        out.append({"i": s["i"], "name": name, "heading": (s.get("heading") or "")[:80], "id": s.get("id", ""), "top": top, "bottom": bottom,
                    "kinds": s.get("kinds") or {},
                    "words": s.get("words", 0), "has_form": has_form, "clickables": inside[:12]})
    if not out:
        out = [{"i": 0, "name": "Hero", "heading": facts.get("h1", "")[:80], "id": "", "top": 0, "bottom": page_height, "words": facts.get("words", 0),
                "has_form": bool(form), "clickables": [c for c in clicks if not c["fixed"]][:12]}]
    return {"url": url, "slug": slug, "viewport": viewport, "width": vp["width"], "height": vp["height"], "page_height": page_height,
            "screenshot": os.path.relpath(shot, ph.ROOT), "made": datetime.now().isoformat(timespec="seconds"), "h1": facts.get("h1", ""),
            "sections": out, "sticky": [c for c in clicks if c["fixed"]][:6],
            "form": ({"top": form_top if form else min((x["top"] for x in facts.get("field_boxes") or []), default=0),
                       "bottom": (form_top + form.get("h", 0)) if form else max((x["bottom"] for x in facts.get("field_boxes") or []), default=0),
                       "fields": ([f.get("name") or f.get("label") or f.get("type") for f in form.get("fields", [])]
                                  if form else [x["name"] for x in facts.get("field_boxes") or []]),
                       "boxes": facts.get("field_boxes") or []} if (form or facts.get("field_boxes")) else None)}


def capture(url, slug):
    from playwright.sync_api import sync_playwright
    from audit.capture import FACTS_JS
    os.makedirs(SCREENS, exist_ok=True)
    maps = {}
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        try:
            for name, vp in VIEWPORTS.items():
                ctx = browser.new_context(viewport={"width": vp["width"], "height": vp["height"]}, user_agent=vp["ua"],
                                          is_mobile=vp["mobile"], has_touch=vp["mobile"], device_scale_factor=1)
                page = ctx.new_page()
                resp = page.goto(url, wait_until="load", timeout=60000)
                status, blocked = settle(page, resp)   # a host's bot check clears itself in a few seconds
                if blocked:
                    sys.exit(BLOCKED.format(url=url))
                if status and status >= 400:
                    sys.exit(f"{url} answered {status}. Nothing to map - check the URL and the dev server.")
                try:
                    page.wait_for_load_state("networkidle", timeout=10000)
                except Exception:
                    pass
                page.add_style_tag(content="html, body { scroll-behavior: auto !important; } *, *::before, *::after { animation: none !important; transition: none !important; }")
                total = page.evaluate("() => document.documentElement.scrollHeight")
                for y in range(0, min(int(total), 30000), vp["height"]):
                    page.evaluate(f"() => window.scrollTo(0, {y})")
                    page.wait_for_timeout(100)
                page.evaluate("() => window.scrollTo(0, 0)")
                page.wait_for_timeout(400)
                facts = page.evaluate(FACTS_JS)
                # the section texts, for naming a section that has no heading
                texts = page.evaluate("""() => [...document.querySelectorAll('section')].map(s =>
                    (s.innerText || '').replace(/\\s+/g, ' ').trim().slice(0, 300))""")
                # each form field's own box, so the dashboard can draw a box per input the way it does per
                # section. capture.py returns the form's outer box only, and a whole-form band cannot show
                # which question people stop at.
                facts["field_boxes"] = page.evaluate("""() => {
                    const vis = e => { const r = e.getBoundingClientRect(); const s = getComputedStyle(e);
                      return r.width > 0 && r.height > 0 && s.visibility !== 'hidden' && s.display !== 'none'; };
                    const seen = new Set(); const out = [];
                    document.querySelectorAll('input, select, textarea').forEach(x => {
                      if (['hidden','submit','button','image'].includes(x.type) || x.tabIndex === -1) return;
                      const key = x.name || x.id; if (!key || seen.has(key) || !vis(x)) return;
                      seen.add(key);
                      // a radio or checkbox group is one question: take the label block around it
                      let r = x.getBoundingClientRect();
                      if (x.type === 'radio' || x.type === 'checkbox') {
                        // a radio GROUP is one question, so take the wrapper - but only when it stays small.
                        // A consent checkbox's wrapper is often the whole form, which would cover every field.
                        const wrap = x.closest('fieldset, .field, label')?.parentElement;
                        if (wrap) {
                          const wr = wrap.getBoundingClientRect();
                          if (wr.height <= Math.max(160, r.height * 6)) r = wr;
                        }
                        if (r.height > 160) {                     // still tall: box the control and its first lines
                          const lab2 = x.closest('label') || x.parentElement;
                          const lr = lab2 ? lab2.getBoundingClientRect() : r;
                          r = new DOMRect(Math.min(r.left, lr.left), r.top,
                                          Math.max(r.width, Math.min(lr.width, 420)), Math.min(lr.height || r.height, 90));
                        }
                      }
                      const lab = (x.id && document.querySelector('label[for="' + CSS.escape(x.id) + '"]')) || x.closest('label');
                      out.push({ name: key, label: (lab ? lab.innerText : '').replace(/\\s+/g,' ').trim().slice(0,40),
                                 top: Math.round(r.top + window.scrollY), bottom: Math.round(r.bottom + window.scrollY),
                                 left: Math.round(r.left), width: Math.round(r.width) });
                    });
                    return out; }""")
                for k, sec in enumerate(facts.get("sections") or []):
                    sec["text"] = texts[k] if k < len(texts) else ""
                page_height = int(facts.get("scrollHeight") or total)
                shot = os.path.join(SCREENS, f"full-{slug}-{name}.png")
                try:
                    page.screenshot(path=shot, full_page=True)
                except Exception:
                    page.screenshot(path=shot, full_page=True, clip={"x": 0, "y": 0, "width": vp["width"], "height": min(page_height, MAX_SHOT)})
                maps[name] = build(url, slug, name, vp, facts, shot, page_height)
                ctx.close()
        finally:
            browser.close()
    return maps


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("url")
    ap.add_argument("--slug", default="", help="cache key; default is the URL path, e.g. lp-drain-cleaning")
    a = ap.parse_args()
    slug = a.slug or slug_for(a.url)
    maps = capture(a.url, slug)
    for name, m in maps.items():
        p = path_for(slug, name)
        json.dump(m, open(p, "w"), indent=1)
        print(f"{name}: {len(m['sections'])} sections · {m['page_height']:,}px tall · {os.path.relpath(p, ph.ROOT)}")
        for s in m["sections"]:
            taps = len(s["clickables"])
            print(f"  {s['name']} · {s['top']} to {s['bottom']}px" + (f" · {taps} tappable" if taps else "") + (" · the form" if s["has_form"] else ""))
    print(f"Screenshots: {os.path.relpath(SCREENS, ph.ROOT)}/full-{slug}-mobile.png and -desktop.png")


if __name__ == "__main__":
    main()
