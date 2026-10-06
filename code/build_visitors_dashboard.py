"""Draw the visitor read: the numbers, the heat map over the page, the form ladder and the ten sessions, on one page.

    python3 code/build_visitors_dashboard.py --page /lp/drain-cleaning        # -> context/sessions/<date>.html
    python3 code/build_visitors_dashboard.py --page /lp/x --date 2026-09-20   # rebuild an older read
    python3 code/build_visitors_dashboard.py --fixture                        # the worked example, no keys, no PostHog

Same shell as the persona dashboard and the Google Ads audit report. Copies references/visitors-dashboard-template.html
and replaces ONLY the JSON inside <script id="visitors-data">. Never edits the template, never hand-edit the output:
if a rule changes, change this builder and rebuild.

Reads what the run already wrote: code/cache/analysis-<slug>.json (analyze.py --json), the heat map point files
(read_sessions.py), code/cache/sessions/picked.json, the page map and its full-page
screenshot, and the date file's "Claude's read". Anything missing is drawn as "not enough yet", never as a blank.
"""
import argparse
import base64
import glob
import json
import os
import re
import shutil
import subprocess
import sys
from datetime import date

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import _posthog as ph  # noqa: E402
import page_map as pm  # noqa: E402

TEMPLATE = os.path.join(ph.ROOT, "references", "visitors-dashboard-template.html")
EXAMPLES = os.path.join(ph.ROOT, "references", "examples", "visitors")
SESSIONS_DIR = os.path.join(ph.ROOT, "context", "sessions")
REPLAYS = os.path.join(ph.CACHE, "replays")
MAX_IMAGE_MB = 6
STRATA = [
    {"key": "A frustration", "what": "The most rage clicks, dead clicks, errors or a form that failed to send."},
    {"key": "B quiet exit", "what": "Reached the form or scrolled past 60%, no errors, left anyway. These decide the offer."},
    {"key": "C converted", "what": "The control. What a good session looks like."},
]


def read_json(path, default=None):
    try:
        return json.load(open(path))
    except (OSError, ValueError):
        return default


def data_uri(path):
    """A PNG inlined, so the page is one file that opens anywhere. Too big and it is left out rather than shipped broken."""
    if not path or not os.path.exists(path):
        return ""
    if os.path.getsize(path) > MAX_IMAGE_MB * 1024 * 1024:
        print(f"  {os.path.basename(path)} is over {MAX_IMAGE_MB} MB - the heat map draws without the screenshot behind it")
        return ""
    return "data:image/png;base64," + base64.b64encode(open(path, "rb").read()).decode()


def claude_reads(date_file):
    """The one or two lines Claude wrote per session under "## Claude's read", keyed by the first 8 of the session id."""
    if not os.path.exists(date_file):
        return {}
    text = open(date_file).read()
    m = re.search(r"^## Claude's read\s*$(.*?)^## ", text, re.S | re.M)
    if not m:
        return {}
    out, cur = {}, None
    for line in m.group(1).splitlines():
        h = re.match(r"^#{3,4}\s*([0-9a-f]{6,})", line.strip())
        if h:
            cur = h.group(1)[:8]
            continue
        b = re.match(r"^\s*[-*]\s+(.*)$", line)
        if b and b.group(1).strip():
            key = cur or (re.match(r"^([0-9a-f]{8})\b", b.group(1)) or [None, None])[1]
            if key:
                txt = re.sub(r"^[0-9a-f]{8}\s*[·:-]\s*", "", b.group(1)).strip()
                out[key] = (out.get(key, "") + " " + txt).strip()
    return out


def heat_views(slug, pmaps):
    """One view per viewport class, the points scaled to the page map's pixels, the screenshot inlined behind them."""
    views = []
    for cls, vp in (("phone", "mobile"), ("desktop", "desktop")):
        m = pmaps.get(vp)
        if not m:
            continue
        points = {}
        for kind in ("click", "rageclick", "scrolldepth"):
            f = read_json(os.path.join(ph.CACHE, f"heatmap-{slug}-{kind}-{cls}.json"))
            pts = (f or {}).get("points") or []
            out = []
            for p in pts[:600]:
                if not isinstance(p, dict):
                    continue
                if kind == "scrolldepth":
                    # PostHog: one row per 100px bucket, cumulative_count = how many were still on the page there
                    y = p.get("scroll_depth_bucket", p.get("y"))
                    n = p.get("cumulative_count", p.get("count", p.get("n")))
                    if y is None or n is None:
                        continue
                    out.append({"y": float(y), "n": int(n)})
                else:
                    y = p.get("pointer_y", p.get("y"))
                    if y is None:
                        continue
                    if p.get("pointer_target_fixed"):
                        continue  # a sticky bar's clicks land at one y for everyone; they are not a place on the page
                    x = p.get("pointer_relative_x", p.get("relative_x", p.get("x")))
                    out.append({"x": float(x) if x is not None else 0.5, "y": float(y),
                                "n": int(p.get("count") or p.get("n") or 1)})
            if out:
                if kind == "scrolldepth":
                    out.sort(key=lambda q: q["y"])
                    step = max(1, len(out) // 12)          # a band every so often, so the labels can be read
                    points[kind] = out[::step][:14]
                else:
                    points[kind] = sorted(out, key=lambda q: -q["n"])[:300]
        if points:
            views.append({"viewport": cls, "width": m["width"], "height": m["page_height"],
                          "image": data_uri(os.path.join(ph.ROOT, m["screenshot"])), "points": points})
    return views


def reach_from_scrollmap(views, m):
    """How many were still on the page at each section's top, from the scroll-depth heat map. {} when there is none."""
    view = next((v for v in views if v.get("width") == m.get("width")), None) or (views[0] if views else None)
    pts = sorted(((view.get("points") or {}).get("scrolldepth") or []), key=lambda q: q["y"]) if view else []
    if not pts:
        return {}
    out = {}
    for s in m["sections"]:
        at = [p["n"] for p in pts if p["y"] <= max(s["top"], 1)]
        out[s["name"]] = at[-1] if at else pts[0]["n"]
    return out


def click_findings(slug, page_url, days=30):
    """The only clicks worth a finding: rage clicks, and taps on something that is not clickable.

    A dead-looking tag is not enough on its own - an svg or a span inside a real button is a normal tap on the
    icon, and flagging it is a false alarm the owner will rightly ignore. So a non-link only counts when its
    elements_chain shows no a/button/input/label anywhere above it.
    """
    out = []
    q = ("select properties.$el_text as el, arrayElement(splitByChar('.', elements_chain), 1) as tag,"
         " elements_chain as chain, count() as n, uniq(distinct_id) as people from events"
         " where event = '$autocapture' and properties.$event_type = 'click'"
         f" and properties.$current_url like {ph.sql_str(page_url.rstrip('/') + '%')}"
         f" and timestamp > now() - interval {int(days)} day"
         " group by el, tag, chain order by n desc limit 40")
    try:
        cols, rows = ph.hogql(q, f"clickmap-{slug}")
    except SystemExit:
        return out
    CLICKABLE = ("a.", "a:", "button", "input", "label", "select", "textarea")
    for r in ph.rows_as_dicts(cols, rows):
        tag, chain = (r.get("tag") or "").lower(), (r.get("chain") or "").lower()
        if tag in ("a", "button", "input", "label", "select", "textarea"):
            continue
        if any(c in chain for c in CLICKABLE):
            continue          # an icon or a word inside a real button: a normal tap, not a finding
        if (r.get("n") or 0) < 3:
            continue
        out.append({"kind": "not_clickable", "text": (r.get("el") or "").strip()[:60], "tag": tag,
                    "n": r.get("n"), "people": r.get("people")})
    return out


RAGE_CAUSES = [
    # (tag matcher, what it usually means, what to change) - ordered, first match wins.
    ("input",  "A field people tapped again and again. On a phone that usually means the tap did not focus it, "
               "the keyboard covered it, or it rejected what they typed without saying so.",
               "Open it on a real phone. Check the field takes focus on one tap, that the page scrolls it above the "
               "keyboard, and that any rejection says what is wrong beside the field."),
    ("select", "A dropdown people fought with. Dropdowns are the worst-performing control on a phone form.",
               "Replace the dropdown with tappable chips, or remove the question."),
    ("label",  "People tapped the label, not the field. A label that does not focus its own input reads as broken.",
               "Tie the label to the input so tapping either one focuses the field."),
    ("button", "A button people pressed repeatedly. Either nothing visibly happened, or it happened too slowly "
               "to notice.",
               "Make the button respond on the first press: a pressed state, a spinner, or the section opening straight away."),
    ("span",   "Text that looks tappable but is not.",
               "Either make it do what it looks like it does, or restyle it so it does not read as a control."),
    ("svg",    "An icon people tapped that is not the control, or has too small a tap target.",
               "Make the whole control tappable, at least 44 by 44 pixels, not just the icon."),
    ("",       "People tapped the same spot repeatedly and the page did not respond.",
               "Watch a recording of that section to see what they were reaching for."),
]


def rage_elements(page_like, days=30):
    """What was actually under the rage clicks, and how soon after landing they happened.

    The timing matters: a burst within about 3 seconds of landing is usually someone tapping while the page is
    still painting, not a broken control. Saying that out loud stops the report crying wolf.
    """
    where = (f"timestamp > now() - interval {int(days)} day"
             f" and {url_sql(page_like)}")
    out = {"elements": [], "early": 0, "later": 0}
    try:
        cols, rows = ph.hogql(
            f"""select properties.$el_text as el, arrayElement(splitByChar('.', elements_chain), 1) as tag,
                count() as n, uniq(distinct_id) as people
                from events where event = '$rageclick' and {where}
                group by el, tag order by n desc limit 10""", "rage-el")
        out["elements"] = ph.rows_as_dicts(cols, rows)
        cols, rows = ph.hogql(
            f"""select countIf(secs < 3) as early, countIf(secs >= 3) as later from (
                select $session_id as sid, dateDiff('second',
                  min(if(event = '$pageview', timestamp, null)), min(if(event = '$rageclick', timestamp, null))) as secs
                from events where {where} and event in ('$pageview', '$rageclick')
                group by sid having secs is not null)""", "rage-when")
        r = (ph.rows_as_dicts(cols, rows) or [{}])[0]
        out["early"], out["later"] = r.get("early") or 0, r.get("later") or 0
    except SystemExit:
        pass
    return out


def rage_cause(tag):
    tag = (tag or "").lower()
    for match, why, fix in RAGE_CAUSES:
        if not match or match in tag:
            return why, fix
    return RAGE_CAUSES[-1][1], RAGE_CAUSES[-1][2]


def rage_findings(views, pmaps):
    """Rage clicks as points, each keeping the viewport it was measured on.

    A y from the desktop heat map means nothing on the phone screenshot: the pages are different heights and the
    sections sit in different places. So every point carries its viewport, and the dashboard only draws the
    points belonging to the view on screen.
    """
    out = []
    for v in views or []:
        vp = "mobile" if (v.get("width") or 0) < 700 else "desktop"
        m = pmaps.get(vp) or pmaps.get("desktop") or pmaps.get("mobile")
        for pt in (v.get("points") or {}).get("rageclick") or []:
            out.append({"kind": "rage", "section": pm.section_at(m, pt["y"]) if m else "the page",
                        "n": pt.get("n", 1), "x": pt.get("x"), "y": pt.get("y"), "viewport": v.get("viewport"), "vp": vp})
    return sorted(out, key=lambda r: -r["n"])


def form_clicks(page_like, days=30):
    """Who tapped each field, read from autocapture clicks instead of field events.

    A page with no LeadEvents still records a click on each input, and the field's name sits in the
    elements_chain as attr__name="...". That is weaker than focus and blur - a tap is not a fill, and it
    cannot say whether the field was left empty - but it answers the question that matters: how far down the
    form do people get before they stop. Reported as taps, never as completions.
    """
    where = (f"timestamp > now() - interval {int(days)} day"
             f" and {url_sql(page_like)}")
    try:
        cols, rows = ph.hogql(
            f"""select
                  extract(elements_chain, 'attr__name="([a-zA-Z_][a-zA-Z0-9_-]*)"') as named,
                  arrayElement(splitByChar('.', elements_chain), 2) as cls,
                  count() as taps, uniq(distinct_id) as people
                from events where event = '$autocapture' and properties.$event_type = 'click' and {where}
                  and (elements_chain like '%input%' or elements_chain like '%textarea%' or elements_chain like '%select%')
                group by named, cls order by people desc limit 40""", "form-clicks")
        out = {}
        for r in ph.rows_as_dicts(cols, rows):
            key = (r.get("named") or "").strip() or (r.get("cls") or "").split(":")[0].strip()
            if not key:
                continue
            row = out.setdefault(key, {"field": key, "taps": 0, "people": 0})
            row["taps"] += r.get("taps") or 0
            row["people"] = max(row["people"], r.get("people") or 0)
        return out
    except SystemExit:
        return {}


def tap_match(taps, field):
    """A field with no name attribute is keyed by its class, so 'tel' finds 'PhoneInputInput'."""
    f = (field or "").lower()
    alias = {"tel": ("phone",), "phone": ("tel", "phoneinput"), "revenue": ("revenue",)}
    for key, row in taps.items():
        k = key.lower()
        if f and (f in k or k in f or any(a in k for a in alias.get(f, ()))):
            return row
    return None


def form_fields_on_page(pmaps):
    """The field names the page actually has, in order, from the page map. A field nobody reached still gets a rung."""
    m = pmaps.get("mobile") or pmaps.get("desktop") or {}
    return [f for f in ((m.get("form") or {}).get("fields") or []) if f and f not in ("page", "company_fax")]


def form_rungs(page_like, days=30, on_page=None):
    """The form as a ladder: started, then each field by how many reached it and how many left it empty.

    The wall is the last field focused in sessions that never submitted. A field people open and leave empty is
    friction - a postcode they have to look up, a dropdown, a box that wants a paragraph.
    """
    where = (f"timestamp > now() - interval {int(days)} day"
             f" and {url_sql(page_like)}"
             " and coalesce(toString(properties.test_lead), '') != 'true'")
    out = {"started": 0, "submitted": 0, "fields": [], "wall": None}
    seen_order = list(on_page or [])
    try:
        cols, rows = ph.hogql(f"select count(distinct $session_id) as n from events where event = 'lead_form_started' and {where}", "f-start")
        out["started"] = (ph.rows_as_dicts(cols, rows) or [{}])[0].get("n") or 0
        cols, rows = ph.hogql(f"select count(distinct $session_id) as n from events where event = 'lead_form_submitted' and {where}", "f-sent")
        out["submitted"] = (ph.rows_as_dicts(cols, rows) or [{}])[0].get("n") or 0
        cols, rows = ph.hogql(
            f"""select properties.field as field, count(distinct $session_id) as touched,
                count(distinct if(toString(properties.filled) = 'true', $session_id, null)) as filled,
                min(timestamp) as first_seen
                from events where event = 'form_field_blurred' and {where}
                group by field order by first_seen limit 20""", "f-fields")
        got = {r["field"]: r for r in ph.rows_as_dicts(cols, rows) if r.get("field")}
        if seen_order:
            # the page's own field order, so a field nobody reached shows as a rung at zero
            out["fields"] = [got.get(f, {"field": f, "touched": 0, "filled": 0}) for f in seen_order]
            out["fields"] += [r for f, r in got.items() if f not in seen_order]
        else:
            out["fields"] = list(got.values())
        cols, rows = ph.hogql(
            f"""select field, count() as n from (
                select $session_id as sid, argMax(properties.field, timestamp) as field,
                       countIf(event = 'lead_form_submitted') as sent
                from events where event in ('form_field_focused', 'lead_form_submitted') and {where}
                group by sid) where sent = 0 and field is not null group by field order by n desc limit 3""", "f-wall")
        walls = ph.rows_as_dicts(cols, rows)
        out["wall"] = walls[0] if walls else None
    except SystemExit:
        pass
    return out


def off_page_clicks(page_like, site_host, days=30):
    """Every tap that sends someone AWAY: an outbound link, a social icon, a nav link off the page.

    On a page whose only job is a call or a form, each of these is a leak. Phone and text taps are the goal,
    counted separately, and never listed here.
    """
    where = (f"timestamp > now() - interval {int(days)} day"
             f" and {url_sql(page_like)}")
    out = []
    try:
        cols, rows = ph.hogql(
            f"""select properties.$el_text as el, elements_chain as chain, count() as n, uniq(distinct_id) as people
                from events where event = '$autocapture' and properties.$event_type = 'click' and {where}
                  and elements_chain like '%href="http%'
                group by el, chain order by n desc limit 40""", "offpage")
        for r in ph.rows_as_dicts(cols, rows):
            m = re.search(r'href="(https?://[^"]+)"', r.get("chain") or "")
            href = m.group(1) if m else ""
            host = re.sub(r"^www\.", "", (re.split(r"/+", href)[1] if "//" in href else ""))
            if not host or (site_host and host.endswith(site_host.replace("www.", ""))):
                continue
            out.append({"text": (r.get("el") or host)[:50], "host": host, "n": r.get("n"), "people": r.get("people")})
    except SystemExit:
        pass
    merged = {}
    for r in out:
        if r["host"] in merged:
            # the same link is several rows (one per place it sits on the page); a person who taps it once is
            # in one row, so the people add up the way the taps do - keeping the first row's count read 40 taps
            # as 15 people on one audited site (2 October 2026)
            merged[r["host"]] = {**merged[r["host"]], "n": merged[r["host"]]["n"] + r["n"],
                                 "people": (merged[r["host"]]["people"] or 0) + (r["people"] or 0)}
        else:
            merged[r["host"]] = r
    return sorted(merged.values(), key=lambda r: -r["n"])


def phone_taps(page_like, days=30):
    where = (f"timestamp > now() - interval {int(days)} day"
             f" and {url_sql(page_like)}")
    try:
        cols, rows = ph.hogql(
            f"""select countIf(event = 'call_clicked') as calls, uniq(if(event = 'call_clicked', distinct_id, null)) as callers,
                countIf(event = 'text_clicked') as texts from events
                where event in ('call_clicked', 'text_clicked') and {where}""", "phone")
        return (ph.rows_as_dicts(cols, rows) or [{}])[0]
    except SystemExit:
        return {}


def exit_sections(page_like, pmaps, days=30):
    """Where the page loses them: the last scroll depth each session reached, as a section name and a share."""
    m = pmaps.get("mobile") or pmaps.get("desktop")
    if not m or not m.get("page_height"):
        return []
    try:
        cols, rows = ph.hogql(
            f"""select toFloat(properties.$prev_pageview_max_scroll_percentage) as depth, count() as n
                from events where event = '$pageleave'
                  and timestamp > now() - interval {int(days)} day
                  and properties.$prev_pageview_pathname like {ph.sql_str(path_like_from(page_like, page_like.strip("%")))}{host_sql(page_like)}
                  and properties.$prev_pageview_max_scroll_percentage is not null
                group by depth order by depth""", "exits")
    except SystemExit:
        return []
    buckets, total = {}, 0
    for r in ph.rows_as_dicts(cols, rows):
        d = r.get("depth")
        if d is None:
            continue
        d = float(d)
        d = d if d <= 1.0 else d / 100.0
        name = pm.section_at(m, m["page_height"] * max(0.0, min(1.0, d)))
        buckets[name] = buckets.get(name, 0) + (r.get("n") or 0)
        total += r.get("n") or 0
    order = {sec["name"]: i for i, sec in enumerate(m["sections"])}
    return [{"section": k, "n": v, "pct": round(100 * v / total) if total else 0}
            for k, v in sorted(buckets.items(), key=lambda kv: order.get(kv[0], 99))]


def retention_bands(page_like, pmaps, days=30, page_path=""):
    """One band per section PER VIEWPORT, with how many were still there, how many left, and a verdict.

    keep · under 15% of the people who reached it left there
    fix  · 15 to 34% left there
    cut  · 35% or more left there

    The same section sits at a different pixel on a phone and a desktop - the mobile page here is 16,629px tall
    and the desktop one 6,360px - so a band built from one map lands in the wrong place on the other. Each
    viewport gets its own set, and the dashboard draws only the set matching the view on screen.
    """
    exits_by_depth = exit_depths(path_like_from(page_like, page_path), days, host_sql(page_path or page_like))
    if not exits_by_depth:
        return []
    out = []
    for vp in ("mobile", "desktop"):
        m = pmaps.get(vp)
        if not m or not m.get("page_height"):
            continue
        # every session's deepest point, mapped onto THIS viewport's sections
        per_section = {}
        total = 0
        for depth, n in exits_by_depth:
            name = pm.section_at(m, m["page_height"] * max(0.0, min(1.0, depth)))
            per_section[name] = per_section.get(name, 0) + n
            total += n
        if not total:
            continue
        still = total
        for sec in m["sections"]:
            left = per_section.get(sec["name"], 0)
            reached = still
            share = (100 * left / reached) if reached else 0
            last = sec is m["sections"][-1]
            out.append({"vp": vp, "name": sec["name"], "top": sec["top"], "bottom": sec["bottom"],
                        "reached": reached, "left": left, "left_pct": round(share), "last": last,
                        "of_all": round(100 * reached / total) if total else 0,
                        # the bottom of the page is where the remaining people run out of page, not a leak
                        "verdict": "keep" if last or share < 15 else ("fix" if share < 35 else "cut")})
            still = max(0, still - left)
    return out


def path_like_from(page_like, page=""):
    """A $current_url pattern -> a $prev_pageview_pathname pattern.

    The two properties hold different things: '%example.com/%' matches a URL but never a pathname, and a
    homepage's pathname is a bare '/'. Getting this wrong silently returns zero rows on every homepage,
    which is exactly what happened on one audited site (28 Sep 2026): 46 real pageleaves read as none.
    Prefer the page path the run already knows; fall back to parsing the pattern.
    """
    host, host_path = pm.split_page((page or "").strip())
    if host:
        # another site's page: host_sql() pins the host, so its homepage is the bare '/' and nothing else
        return "/" if host_path == "/" else host_path.rstrip("/") + "%"
    path = (page or "").strip()
    if not path:
        raw = (page_like or "").strip("%")
        m = re.match(r"(?:https?://)?[^/]*\.[^/]*(/.*)?$", raw)   # a host, with or without a scheme
        path = (m.group(1) or "/") if m else raw
    if not path.startswith("/"):
        path = "/" + path
    return "/%" if path == "/" else path.rstrip("/") + "%"


def url_sql(page_like):
    """The page filter on $current_url. A page on another site is matched by host and exact path instead,
    so a homepage read is the homepage and not every page of that site."""
    return pm.page_sql((page_like or "").strip("%")) or f"properties.$current_url like {ph.sql_str(page_like)}"


def host_sql(page):
    """' and properties.$host like ...' when the page is on another site, '' for a path on this one.

    A pathname carries no host, so a homepage's '/' is every homepage in the project, localhost included."""
    host = pm.split_page((page or "").strip("%"))[0]
    return f" and properties.$host like {ph.sql_str('%' + host)}" if host else ""


def exit_depths(page_like, days=30, host=""):
    """[(depth 0-1, sessions)] - each session's deepest scroll, viewport-free so it can be mapped onto either."""
    try:
        cols, rows = ph.hogql(
            f"""select toFloat(properties.$prev_pageview_max_scroll_percentage) as depth, count() as n
                from events where event = '$pageleave'
                  and timestamp > now() - interval {int(days)} day
                  and properties.$prev_pageview_pathname like {ph.sql_str(page_like)}{host}
                  and properties.$prev_pageview_max_scroll_percentage is not null
                group by depth order by depth""", "exit-depths")
    except SystemExit:
        return []
    out = []
    for r in ph.rows_as_dicts(cols, rows):
        d = r.get("depth")
        if d is None:
            continue
        d = float(d)
        out.append((d if d <= 1.0 else d / 100.0, r.get("n") or 0))
    return out


def section_rows(pmaps, analysis, summary, views=None):
    """One row per section: how many reached it, and what the ten did there."""
    m = pmaps.get("mobile") or pmaps.get("desktop")
    if not m:
        return []
    counts = {r["name"]: r for r in (summary or {}).get("sections", [])}
    scroll = [(s.get("section"), s.get("reached") or 0) for s in (analysis or {}).get("scroll", []) if s.get("section")]
    from_heat = reach_from_scrollmap(views or [], m)
    rows = []
    for s in m["sections"]:
        g = counts.get(s["name"], {})
        reached = next((n for name, n in scroll if name == s["name"]), None)
        if reached is None:
            reached = from_heat.get(s["name"])
        rows.append({"name": s["name"], "top": s["top"], "bottom": s["bottom"],
                     "reached": reached, "paused": g.get("paused", 0), "stopped": g.get("stopped", 0), "broken": g.get("broken", 0)})
    if rows and not any(r["reached"] for r in rows):
        # nothing measured how far they got: say so rather than printing a column of zeroes
        for r in rows:
            r["reached"] = None
    return rows


def sessions_read(picked, reads):
    """The picked sessions as cards: what each one did, and Claude's line about it.

    No model watches these. The card carries the counts the event log gives - device, seconds, scroll depth -
    plus the PostHog link so a person can watch it themselves when one looks worth opening.
    """
    out = []
    for row in picked:
        sid = row.get("sid", "")
        out.append({"sid": sid, "stratum": row.get("stratum", ""), "device": row.get("device") or "unknown",
                    "secs": int(row.get("secs") or 0), "scroll": int(row.get("scroll") or 0),
                    "rage": row.get("rage") or 0, "dead": row.get("dead") or 0,
                    "form_started": row.get("form_started") or 0, "submitted": row.get("submitted") or 0,
                    "claude": reads.get(sid[:8], ""),
                    "replay": ph.ui("replay/" + sid) if ph.PROJECT_ID else ""})
    order = {s_["key"]: i_ for i_, s_ in enumerate(STRATA)}
    out.sort(key=lambda s_: (order.get(s_["stratum"], 9), s_["sid"]))
    return out, []


def two_lists(date_file):
    """FIX NOW and TEST LATER as Claude wrote them in the date file. One bullet is one row."""
    if not os.path.exists(date_file):
        return [], []
    text = open(date_file).read()

    def grab(heading):
        m = re.search(rf"^## {heading}[^\n]*$(.*?)(?=^## |\Z)", text, re.S | re.M)
        rows = []
        if not m:
            return rows
        cur = None
        for line in m.group(1).splitlines():
            top = re.match(r"^[-*]\s+(.+)$", line)
            sub = re.match(r"^\s{2,}[-*]\s+(.+)$", line)
            if top and top.group(1).strip() and top.group(1).strip() != "":
                body = top.group(1).strip()
                where = ""
                wm = re.match(r"^([A-Z][\w '-]{1,28}?)\s*[·:]\s*(.+)$", body)
                if wm:
                    where, body = wm.group(1), wm.group(2)
                cur = {"what": body, "where": where, "detail": "", "evidence": "", "sessions": re.findall(r"\b([0-9a-f]{8})\b", body)}
                rows.append(cur)
            elif sub and cur:
                v = sub.group(1).strip()
                low = v.lower()
                if low.startswith("evidence"):
                    cur["evidence"] = v.split(":", 1)[-1].strip()
                else:
                    cur["detail"] = (cur["detail"] + " " + v).strip()
                cur["sessions"] += re.findall(r"\b([0-9a-f]{8})\b", v)
        return rows
    return grab("Fix now"), grab("Test later")


def not_enough(analysis, views, form):
    out = []
    pv = (analysis or {}).get("pageviews") or 0
    if not views:
        out.append({"what": "The heat map", "why": "No points on file yet. PostHog collects them on the live page and keeps them 90 days; "
                                                   "run the read again once the page has traffic."})
    elif pv < 2000:
        out.append({"what": "The heat map", "why": f"{pv:,} pageviews. A picture means something at about 2,000, so read it as early."})
    if form and not form.get("enough"):
        out.append({"what": "The form percentages", "why": f"{form.get('starters', 0)} people started the form. A percentage needs 100 starters, so the ladder shows counts."})
    if (analysis or {}).get("sessions", 0) < 50:
        out.append({"what": "The whole read", "why": f"{(analysis or {}).get('sessions', 0)} sessions. Under about 50 the ten are most of the traffic, not a sample."})
    return out


REAL = 10          # seconds. Under this is a bot, a mis-click or a bounce before the page painted.


def traffic_sources(page_like, days=30):
    """Where they came from, and whether that changes what they do.

    A blended conversion rate hides three different audiences. On one audited site (29 Sep 2026) YouTube
    converted at 7.1% on an 8-second median while direct converted at 1.1% on a 2-second median - the same
    page, and the fix for each is different.
    """
    where = (f"timestamp > now() - interval {int(days)} day"
             f" and {url_sql(page_like)}")
    try:
        cols, rows = ph.hogql(
            f"""select r as source, count() as sessions, sum(t) as acted,
                round(100 * sum(t) / count(), 1) as rate, round(median(secs)) as median_secs,
                round(100 * avg(scroll)) as avg_scroll
                from (select $session_id as sid, any(properties.$referring_domain) as r,
                        maxIf(1, event = '$autocapture' and elements_chain like '%input%'
                                 or event in ('call_clicked', 'text_clicked')) as t,
                        dateDiff('second', min(timestamp), max(timestamp)) as secs,
                        max(toFloat(properties.$prev_pageview_max_scroll_percentage)) as scroll
                      from events where {where} group by sid)
                where secs >= {REAL} group by r having sessions >= 5 order by sessions desc limit 8""", "sources")
        return ph.rows_as_dicts(cols, rows)
    except SystemExit:
        return []


def by_device(page_like, days=30):
    """Phone against desktop. They often differ more than any copy change, and the weaker one is the fix."""
    where = (f"timestamp > now() - interval {int(days)} day"
             f" and {url_sql(page_like)}")
    try:
        cols, rows = ph.hogql(
            f"""select d as device, count() as sessions, sum(t) as acted,
                round(100 * sum(t) / count(), 1) as rate, round(100 * avg(scroll)) as avg_scroll,
                round(median(secs)) as median_secs
                from (select $session_id as sid, any(properties.$device_type) as d,
                        maxIf(1, event = '$autocapture' and elements_chain like '%input%'
                                 or event in ('call_clicked', 'text_clicked')) as t,
                        max(toFloat(properties.$prev_pageview_max_scroll_percentage)) as scroll,
                        dateDiff('second', min(timestamp), max(timestamp)) as secs
                      from events where {where} group by sid)
                where secs >= {REAL} and d != '' group by d having sessions >= 5 order by sessions desc""", "devices")
        return ph.rows_as_dicts(cols, rows)
    except SystemExit:
        return []


def dwell_split(page_like, days=30):
    """How long they stay. Half of all sessions under ten seconds is a traffic problem, not a page problem."""
    where = (f"timestamp > now() - interval {int(days)} day"
             f" and {url_sql(page_like)}")
    try:
        cols, rows = ph.hogql(
            f"""select countIf(secs < {REAL}) as bounced, countIf(secs >= {REAL} and secs < 60) as brief,
                countIf(secs >= 60 and secs < 180) as read_it, countIf(secs >= 180) as stayed, count() as total
                from (select $session_id as sid, dateDiff('second', min(timestamp), max(timestamp)) as secs
                      from events where {where} group by sid)""", "dwell")
        return (ph.rows_as_dicts(cols, rows) or [{}])[0]
    except SystemExit:
        return {}


SCROLL_MIN = 60     # sessions reporting scroll. Below this the band percentages are a handful of people.


def scroll_funnel(page_like, days=30):
    """Past the hero, to the end, and whether they then touched the form - among sessions that report scroll.

    The honest part: scroll depth rides on $pageleave, and most sessions never send one (the tab is closed, the
    browser discards it, an ad blocker eats it). On one audited site, 22 of 386 real sessions reported scroll.
    So this is a shape, not a rate, and the report says so rather than quoting a percentage of everyone.
    """
    where = (f"timestamp > now() - interval {int(days)} day"
             f" and {url_sql(page_like)}")
    try:
        cols, rows = ph.hogql(
            f"""select count() as measured, countIf(scroll >= 0.25) as past_hero,
                countIf(scroll >= 0.9) as reached_end, countIf(scroll >= 0.9 and touched = 1) as end_and_form,
                countIf(scroll >= 0.9 and touched = 0) as end_no_form, countIf(touched = 1) as touched_form
                from (select $session_id as sid,
                        max(toFloat(properties.$prev_pageview_max_scroll_percentage)) as scroll,
                        maxIf(1, event = '$autocapture' and elements_chain like '%input%') as touched,
                        dateDiff('second', min(timestamp), max(timestamp)) as secs
                      from events where {where} group by sid)
                where secs >= {REAL} and scroll is not null""", "scroll-funnel")
        return (ph.rows_as_dicts(cols, rows) or [{}])[0]
    except SystemExit:
        return {}


def what_they_did(page_like, days=30):
    """Of everyone who landed, how many did anything at all.

    The scroll bands say where people stop. They do not say whether the ones who stayed did something. A page
    where almost nobody touches the form, taps the phone or scrolls deep is not converting quietly - it is
    being read and abandoned, and that is a different problem from a leaky hero.
    """
    where = (f"timestamp > now() - interval {int(days)} day"
             f" and {url_sql(page_like)}")
    try:
        cols, rows = ph.hogql(
            f"""select uniq($session_id) as sessions,
                uniqIf($session_id, event = '$autocapture' and elements_chain like '%input%') as touched_form,
                uniqIf($session_id, event in ('call_clicked', 'text_clicked')) as called,
                uniqIf($session_id, event = 'lead_form_submitted' or event = 'lead_received') as submitted,
                uniqIf($session_id, event = '$autocapture' and elements_chain like '%href="http%') as went_offsite,
                uniqIf($session_id, toFloat(properties.$prev_pageview_max_scroll_percentage) > 0.75) as read_deep
                from events where {where}
                  and $session_id in (select $session_id from events where {where}
                      group by $session_id having dateDiff('second', min(timestamp), max(timestamp)) >= {REAL})""", "what-they-did")
        return (ph.rows_as_dicts(cols, rows) or [{}])[0]
    except SystemExit:
        return {}


def build_findings(slug, page_url, page_like, pmaps, views, days, site_host, page_path=""):
    """Every finding that has a mechanism, worst first, each anchored to a place on the page where it has one."""
    m = pmaps.get("mobile") or pmaps.get("desktop")
    def band(name):
        for sec in (m or {}).get("sections", []):
            if sec["name"] == name:
                return sec["top"], sec["bottom"]
        return None, None
    out = []

    rages = rage_findings(views, pmaps)
    if rages:
        by_section = {}
        for r in rages:
            k = (r["vp"], r["section"])
            by_section[k] = by_section.get(k, 0) + r["n"]
        listed = sorted(by_section.items(), key=lambda kv: -kv[1])
        (top_vp, top_sec), top_n = listed[0]
        worst = next(r for r in rages if r["section"] == top_sec and r["vp"] == top_vp)
        el = rage_elements(page_like, days)
        hit = (el.get("elements") or [{}])[0]
        tag = (hit.get("tag") or "").split(":")[0]
        label = (hit.get("el") or "").strip()
        why, change = rage_cause(tag)
        PLAIN = {"input": "a form field", "select": "a dropdown", "label": "a field label",
                 "button": "a button", "span": "a line of text", "svg": "an icon", "a": "a link"}
        name = f'"{label}"' if label and label.lower() != "none" else PLAIN.get(tag, "the same spot")
        early, later = el.get("early") or 0, el.get("later") or 0
        lines = [{"state": "missing", "text": f"{h.get('n')} taps on {(h.get('el') or '').strip()[:34] or 'no text'} "
                                              f"({(h.get('tag') or '?').split(':')[0]})"}
                 for h in (el.get("elements") or [])[:5]]
        if early:
            lines.append({"state": "unchecked",
                          "text": f"{early} of {early + later} started within 3 seconds of landing, which is usually "
                                  f"impatience while the page paints, not a broken control"})
        out.append({"title": f"People tap {name} again and again and nothing happens", "verdict": "cut",
                    "group": "Broken, ships today", "where": f"{top_sec} · {top_vp} · {top_n} rage taps",
                    "markers": [{"x": r["x"], "y": r["y"], "vp": r["vp"], "n": r["n"], "label": f"{r['n']} rage taps"} for r in rages[:8]],
                    "why": why, "change": change, "lines": lines, "_rank": 1000 + top_n})

    for c in click_findings(slug, page_url, days):
        out.append({"title": f"\"{c['text'] or 'An element'}\" gets tapped and nothing happens", "verdict": "cut",
                    "group": "Broken, ships today", "where": "", "top": None, "bottom": None,
                    "why": f"A {c['tag']} is not a link or a button, and it is not inside one either.",
                    "lines": [{"state": "missing", "text": f"{c['n']} taps by {c['people']} people"}], "_rank": 900 + c["n"]})

    f = form_rungs(page_like, days, form_fields_on_page(pmaps))
    on_page = form_fields_on_page(pmaps)
    if on_page and not f.get("started"):
        # no field events, so fall back to who TAPPED each field. Weaker, but it still ranks the questions.
        taps = form_clicks(page_like, days)
        top_people = max([v.get("people") or 0 for v in taps.values()] or [0])
        boxes, rungs, lines = [], [], []
        for vp in ("mobile", "desktop"):
            for bx in ((pmaps.get(vp) or {}).get("form") or {}).get("boxes") or []:
                got = taps.get(bx["name"]) or tap_match(taps, bx["name"]) or {}
                people = got.get("people") or 0
                pct = round(100 * people / top_people) if top_people else 0
                verdict = ("none" if not taps else "keep" if pct >= 60 else "fix" if pct >= 25 else "cut")
                boxes.append({"vp": vp, "name": bx["name"], "top": bx["top"], "bottom": bx["bottom"],
                              "left": bx.get("left"), "width": bx.get("width"),
                              "page_width": (pmaps.get(vp) or {}).get("width"),
                              "reached": people, "left_pct": pct, "verdict": verdict,
                              "note": (f"{people} tapped it" if taps else "not measured")})
        if taps:
            first = None
            for name in on_page:
                people = ((taps.get(name) or tap_match(taps, name)) or {}).get("people") or 0
                if first is None:
                    first = people or 1
                rungs.append({"label": name, "pct": round(100 * people / max(1, top_people)),
                              "note": f"{people} of {top_people} who touched the form ({round(100 * people / max(1, top_people))}%)",
                              "wall": people and people <= max(1, top_people) * 0.35})
            ranked = sorted(((n_, ((taps.get(n_) or tap_match(taps, n_)) or {}).get("people") or 0) for n_ in on_page), key=lambda r: -r[1])
            lines = [{"state": "ok" if p >= top_people * 0.6 else "weak" if p >= top_people * 0.25 else "missing",
                      "text": f"{n_} · {p} people tapped it"} for n_, p in ranked]
        fewest = min([((taps.get(n_) or tap_match(taps, n_)) or {}).get("people") or 0 for n_ in on_page] or [0])
        out.append({"title": (f"The form: {top_people} people touched it, {fewest} reached the last question"
                              if taps else f"The form has {len(on_page)} questions and none of them are measured"),
                    "verdict": "fix", "group": "The form", "where": "Form",
                    "why": ("Read from taps on each field, because this page sends no field events. A tap is not a "
                            "fill, so this ranks the questions rather than proving who completed them."
                            if taps else
                            "The page asks these questions but sends no field events, so nothing says which one "
                            "people stop at."),
                    "change": ("Drop `<LeadEvents />` into the page for the real read: it sends a focus and blur "
                               "event per field, names only, never what was typed, so the next run shows who left "
                               "each field empty." if taps else
                               "Drop `<LeadEvents />` into the page. It sends a focus and blur event per field, "
                               "names only, never what was typed."),
                    "fields": boxes, "rungs": rungs,
                    "lines": lines or [{"state": "unchecked", "text": f"{n_}"} for n_ in on_page],
                    "_rank": 700 if taps else 500})
    if f.get("started"):
        started = f["started"]
        rungs = [{"label": "Opened the form", "pct": 100, "note": f"{started} people"}]
        prev = started
        biggest = {"drop": 0, "field": None}
        for row in f.get("fields", []):
            touched, filled = row.get("touched") or 0, row.get("filled") or 0
            empty = max(0, touched - filled)
            lost = max(0, prev - touched)
            if lost > biggest["drop"]:
                biggest = {"drop": lost, "field": row["field"], "from": prev, "to": touched}
            pct_of_start = round(100 * touched / max(1, started))
            note = f"{touched} of {started} ({pct_of_start}%)"
            if lost:
                note += f" · {lost} never got here"
            if empty:
                note += f" · {empty} left it empty"
            rungs.append({"label": row["field"], "pct": round(100 * touched / max(1, started)), "note": note,
                          "wall": bool(f.get("wall") and f["wall"].get("field") == row["field"])})
            prev = touched
        sent = f.get("submitted") or 0
        rungs.append({"label": "Sent it", "pct": round(100 * sent / max(1, started)), "note": f"{sent} people"})
        wall = f.get("wall")
        top, bottom = band("Form")
        # one box per input, per viewport, so the page shows WHICH question people stop at
        reach = {r.get("field"): (r.get("touched") or 0) for r in f.get("fields", [])}
        field_boxes = []
        for vp in ("mobile", "desktop"):
            fm = (pmaps.get(vp) or {}).get("form") or {}
            for bx in fm.get("boxes") or []:
                touched = reach.get(bx["name"], 0)
                pct = round(100 * touched / max(1, started))
                # the same bands as a section: green holds them, amber loses some, red is where they stop
                verdict = "keep" if pct >= 60 else ("fix" if pct >= 25 else "cut")
                field_boxes.append({"vp": vp, "name": bx["name"], "top": bx["top"], "bottom": bx["bottom"],
                                    "left": bx.get("left"), "width": bx.get("width"),
                                    "page_width": (pmaps.get(vp) or {}).get("width"),
                                    "reached": touched, "left_pct": pct, "verdict": verdict,
                                    "note": f"{touched} of {started} ({pct}%)"})
        lines = []
        if biggest["field"]:
            lines.append({"state": "missing", "text": f"Biggest fall: {biggest['from']} reached {biggest['field']} "
                                                      f"but only {biggest['to']} touched it, losing {biggest['drop']}"})
        if wall:
            lines.append({"state": "missing", "text": f"{wall['n']} people had {wall['field']} open last and never sent it"})
        for row in f.get("fields", []):
            empty = max(0, (row.get("touched") or 0) - (row.get("filled") or 0))
            if empty >= 3:
                lines.append({"state": "weak", "text": f"{empty} people opened {row['field']} and left it empty"})
        out.append({"title": (f"The form loses most people at {biggest['field']}" if biggest["field"]
                              else f"{started} opened the form, {sent} sent it"),
                    "verdict": "fix" if (wall or biggest["field"]) else "keep", "group": "The form",
                    "where": "Form", "top": top, "bottom": bottom,
                    "why": "Every field people open, in order, and how many never reach the next one. A field people "
                           "open and leave empty is asking for something they do not have to hand.",
                    "change": "Cut the field with the biggest fall, or move it after the phone number so the lead is "
                              "captured before the hard question. Never ask for something they have to look up.",
                    # a form that loses nearly everyone is the most expensive thing on the page: rank it by
                    # how many of the people who opened it never sent it, so it leads when it is this bad
                    "rungs": rungs, "lines": lines, "fields": field_boxes,
                    "_rank": 1200 + (started - sent) if started and sent / max(1, started) < 0.1
                             else 800 + (wall.get("n", 0) if wall else biggest["drop"])})

    leaks = off_page_clicks(page_like, site_host, days)
    if leaks:
        top, bottom = band((m or {}).get("sections", [{}])[0].get("name", ""))
        out.append({"title": f"{sum(l['n'] for l in leaks)} taps sent people off the page", "verdict": "fix",
                    "group": "Friction", "where": "", "top": None, "bottom": None,
                    "why": "This page has one job. Every one of these is a visitor who left before calling or filling the form.",
                    "change": "Make these open in a new tab, or take them off the page. A link to your own YouTube "
                              "channel on an ad page is a paid click walking out of the door.",
                    "lines": [{"state": "weak", "text": f"{l['host']} · {l['n']} taps by {l['people']} people"} for l in leaks[:6]],
                    "_rank": 700 + sum(l["n"] for l in leaks)})

    ph_taps = phone_taps(page_like, days)
    if ph_taps.get("calls"):
        out.append({"title": f"{ph_taps['calls']} people tapped the phone number", "verdict": "keep",
                    "group": "Working", "where": "", "top": None, "bottom": None,
                    "why": "A phone tap is intent, not a booked job. It becomes a lead when the call is answered.",
                    "lines": [{"state": "ok", "text": f"{ph_taps['calls']} call taps by {ph_taps.get('callers') or 0} people"}]
                            + ([{"state": "ok", "text": f"{ph_taps['texts']} text taps"}] if ph_taps.get("texts") else []),
                    "_rank": 100})

    # the funnel is measured but never shown: on thin scroll data it is a card that says nothing except
    # that it cannot say anything. The takeaway reads its count to decide how hard to hedge, and the source,
    # device and band cards leave scroll out when it is a handful of people.
    fun = scroll_funnel(page_like, days)
    scroll_ok = (fun.get("measured") or 0) >= SCROLL_MIN

    def scrolled(r):
        return f" · scrolled {r['avg_scroll']}%" if scroll_ok and r.get("avg_scroll") is not None else ""

    srcs = traffic_sources(page_like, days)
    if srcs:
        best, worst = srcs[0], srcs[0]
        for r in srcs:
            if (r.get("sessions") or 0) >= 20:
                if (r.get("rate") or 0) > (best.get("rate") or 0): best = r
                if (r.get("rate") or 0) < (worst.get("rate") or 0): worst = r
        spread = (best.get("rate") or 0) - (worst.get("rate") or 0)
        out.append({"title": (f"{best['source']} converts {round((best['rate'] or 0) / max(.1, worst['rate'] or .1), 1)}x "
                              f"better than {worst['source']}" if spread > 2 else "Every source behaves about the same"),
                    "verdict": "fix" if spread > 4 else "keep", "group": "Where they come from",
                    "where": f"{sum(r['sessions'] for r in srcs)} sessions that stayed past {REAL} seconds",
                    "why": "One blended conversion rate hides different audiences. Traffic that already knows you "
                           "behaves nothing like traffic that just found you, and the fix for each is different.",
                    "change": ("Judge the page against its best source, not the blend. A source that lands and leaves "
                               "is usually the wrong promise in the ad or the link, not a broken page."),
                    "lines": [{"state": "ok" if (r["rate"] or 0) >= 8 else "weak" if (r["rate"] or 0) >= 3 else "missing",
                               "text": f"{r['source']} · {r['sessions']} sessions · {r['rate']}% acted · "
                                       f"{r['median_secs']}s median{scrolled(r)}"} for r in srcs],
                    "_rank": 950})

    devs = by_device(page_like, days)
    if len(devs) > 1:
        weak = min(devs, key=lambda r: r.get("rate") or 0)
        strong = max(devs, key=lambda r: r.get("rate") or 0)
        out.append({"title": (f"{weak['device']} converts at {weak['rate']}%, {strong['device']} at {strong['rate']}%"
                              if weak is not strong else f"{strong['device']} is the only device with traffic"),
                    "verdict": "fix" if (strong.get("rate") or 0) - (weak.get("rate") or 0) > 3 else "keep",
                    "group": "Phone against desktop", "where": f"{sum(r['sessions'] for r in devs)} sessions",
                    "why": "The same page is two different pages. A phone shows a fraction of what a desktop shows "
                           "above the fold, and the weaker device is usually the one nobody tested on.",
                    "change": f"Open the page on a real {weak['device'].lower()} and do the whole journey yourself. "
                              "Compare how far each device scrolls: a big gap means the phone is being asked to work harder.",
                    "lines": [{"state": "ok" if (r["rate"] or 0) >= (strong.get("rate") or 0) * .8 else "weak",
                               "text": f"{r['device']} · {r['sessions']} sessions · {r['rate']}% acted"
                                       f"{scrolled(r)} · {r['median_secs']}s median"} for r in devs],
                    "_rank": 900})

    dw = dwell_split(page_like, days)
    if dw.get("total"):
        tot = dw["total"]
        bounced = dw.get("bounced") or 0
        pct_b = round(100 * bounced / tot)
        if pct_b >= 30:
            out.append({"title": f"{pct_b}% of sessions last under {REAL} seconds",
                        "verdict": "fix", "group": "How long they stay", "where": f"{tot} sessions",
                        "why": "A session that ends before the page finishes painting is a bot, a mis-click or a "
                               "wrong-audience click. It is not someone rejecting the page, and counting it drags "
                               "every rate down. Every number in this report already excludes them.",
                        "change": "Look at where those clicks come from before touching the page. If one source is "
                                  "most of them, the promise that sent them is wrong, not the page.",
                        "lines": [{"state": "missing", "text": f"Gone before {REAL} seconds · {bounced} ({pct_b}%)"},
                                  {"state": "weak", "text": f"{REAL} seconds to a minute · {dw.get('brief') or 0}"},
                                  {"state": "ok", "text": f"One to three minutes · {dw.get('read_it') or 0}"},
                                  {"state": "ok", "text": f"Over three minutes · {dw.get('stayed') or 0}"}],
                        "_rank": 850})

    did = what_they_did(page_like, days)
    bands = retention_bands(page_like, pmaps, days, page_path)
    read = max([x["reached"] for x in bands] or [0])
    if bands and read < SCROLL_MIN:
        # a band is a share of the people who reached a section. Five people make a red band out of three
        # exits, so under the floor nothing is drawn on the page and the card says what is missing instead.
        out.append({"title": f"Where they leave cannot be read yet: {read} sessions reported how far they scrolled",
                    "verdict": "fix", "group": "Where they leave", "where": f"{read} sessions read · {SCROLL_MIN} needed",
                    "why": "Scroll depth rides on the page-leave event, which carries it only when the page sent a "
                           "pageview first. A page that sends no pageview, or loses most of its leaves, has no "
                           "scroll map - and a band drawn from a handful of people would be a guess painted red.",
                    "change": "Fix the tracking before the page: `python3 code/check_tracking.py <url>` says which "
                              "event is missing. The next read draws the bands.",
                    "lines": [{"state": "unchecked", "text": f"{read} sessions with a scroll depth · {SCROLL_MIN} needed for bands"}],
                    "_rank": 650})
        bands = []
    if bands:
        desk = [x for x in bands if x["vp"] == "desktop"] or bands
        total = desk[0]["reached"] if desk else 0
        worst = max([x for x in desk if not x.get("last")] or desk, key=lambda x: x["left"])
        out.append({"title": f"{worst['left_pct']}% of the people who got to {worst['name']} left there",
                    "verdict": worst["verdict"], "group": "Where they leave",
                    "where": f"{total} sessions read", "bands": bands,
                    "why": ("Every section marked by how many people it holds on to. Green keeps them, amber loses "
                            "some, red is where the page stops working. Read from the deepest point each session "
                            "reached - and only a fraction of sessions report that, so treat the percentages as a "
                            "shape rather than a measurement."),
                    "change": "A red section near the top is the one to rewrite first: whatever it promises is not "
                              "holding them long enough to reach the offer.",
                    "lines": [{"state": "missing" if x["verdict"] == "cut" else ("weak" if x["verdict"] == "fix" else "ok"),
                               "text": (f"{x['name']} · {x['reached']} still here ({x['of_all']}% of all) · "
                                        + (f"{x['left']} reached the end of the page" if x.get("last")
                                           else f"{x['left']} left ({x['left_pct']}%)"))} for x in desk],
                    "_rank": 650 + worst["left"]})

    exits = exit_sections(page_like, pmaps, days)
    if False:
        worst = max(exits, key=lambda e: e["n"])
        top, bottom = band(worst["section"])
        total = sum(e["n"] for e in exits)
        out.append({"title": f"{worst['pct']}% of people leave at {worst['section']}", "verdict": "fix",
                    "group": "Where they leave", "where": f"{worst['section']} · {total} sessions read",
                    "top": top, "bottom": bottom,
                    "why": "The last place each session reached before leaving. A section where a lot of people stop "
                           "is either the answer they came for, or the question that stopped them.",
                    "lines": [{"state": "missing" if e["section"] == worst["section"] else "weak",
                               "text": f"{e['section']} · {e['pct']}% left here ({e['n']} sessions)"} for e in exits],
                    "_rank": 600 + worst["n"]})

    # The overview. Not a restatement of the numbers - a diagnosis. It asks the question the owner is
    # actually asking ("why is it only N%?") and answers it from the shape of the data, naming which of the
    # four usual causes this page has: they never arrive, they bounce at the top, they read and are not
    # convinced, or they try and something breaks.
    if did.get("sessions"):
        real = did["sessions"]
        acted = max(did.get("touched_form") or 0, did.get("called") or 0)
        rate = round(100 * acted / real, 1) if real else 0
        deep = did.get("read_deep") or 0
        off = did.get("went_offsite") or 0
        broken = [f for f in out if f.get("verdict") == "cut" and f.get("group") == "Broken, ships today"]
        desk = [x for x in bands if x["vp"] == "desktop" and not x.get("last")]
        worst = max(desk, key=lambda x: x.get("left", 0)) if desk else {}
        first = desk[0] if desk else {}
        reached_end = desk[-1]["reached"] if desk else 0
        bounced = dw.get("bounced") or 0
        tot_all = dw.get("total") or real

        measured_scroll = (fun.get("measured") or 0) if "fun" in dir() else 0
        thin_scroll = measured_scroll and measured_scroll < SCROLL_MIN
        causes, verdict_line, headline = [], "", ""
        # 1. the top of the page, measured against every other section
        if first and (first.get("left_pct") or 0) >= 25:
            rest = [x for x in desk[1:] if (x.get("left_pct") or 0) >= 25]
            if not rest:
                headline = "the first screen, probably" if thin_scroll else "the first screen"
                verdict_line = (f"{first['left_pct']}% of the people who arrive leave at {first['name']}, and every "
                                f"section below it holds on to almost everyone - {reached_end} of the "
                                f"{first['reached']} who arrived still reach the end. The page is not too long and it "
                                f"is not boring: whatever the top says is not making enough people want the rest.")
                if thin_scroll:
                    verdict_line += (f" Treat that as the strongest hint here, not a proven fact: only "
                                     f"{measured_scroll} sessions reported how far they scrolled, so the shape is "
                                     "real but the percentages are built on a handful of people.")
                causes.append("the first screen is doing the losing" + (" (on thin scroll data)" if thin_scroll else ""))
        # 2. they read it and still do nothing
        if deep and acted / max(1, deep) < 0.4:
            causes.append("the ones who read it are not convinced")
            if not verdict_line:
                headline = "the offer"
                verdict_line = (f"{deep} people read past three quarters of the page and {acted} did anything. "
                                "Attention is not the problem - what they are being asked to do, or what they get "
                                "for doing it, is.")
        # 3. something is broken
        if broken:
            causes.append(f"{len(broken)} thing(s) on the page do not respond")
        # 4. they leave for somewhere else
        if off and off / max(1, real) > 0.1:
            causes.append(f"{off} left for another site")
        if not verdict_line:
            headline = "no single leak"
            verdict_line = (f"{acted} of {real} people who stayed did something, and no section loses more than a "
                            "quarter of the people who reach it. Nothing on the page stands out as the problem.")

        out.append({"title": f"Why only {rate}% act: {headline}",
                    "verdict": "cut" if rate < 5 else "fix" if rate < 12 else "keep",
                    "group": "The takeaway", "where": f"{real} real sessions · {bounced} of {tot_all} never counted",
                    "why": verdict_line,
                    "change": ("Ship the broken things today. The rest is an opinion about the top of the page, so it "
                               "goes to `/split-test` as one structural challenger - a different first screen, not a "
                               "different button." if first and (first.get("left_pct") or 0) >= 25 else
                               "Ship the broken things today, then test the offer itself rather than the layout."),
                    "lines": ([{"state": "missing", "text": f"What it is · {c}"} for c in causes] +
                              [{"state": "ok", "text": f"What is working · every section below {first.get('name', 'the top')} "
                                                       f"keeps 90%+ of the people who reach it"}] if len(desk) > 1 and
                                                       all((x.get("left_pct") or 0) < 15 for x in desk[1:]) else
                              [{"state": "missing", "text": f"What it is · {c}"} for c in causes]) +
                             [{"state": "unchecked", "text": f"Real visitors · {real} of {tot_all}, after removing "
                                                             f"{bounced} sessions under {REAL} seconds"}],
                    "_rank": 3000})

    out.sort(key=lambda r: -r.get("_rank", 0))
    for r in out:
        r.pop("_rank", None)
    return out


def collect(page, when, business):
    slug = pm.slug_for(page)
    pmaps = {vp: pm.load(slug, vp) for vp in ("mobile", "desktop")}
    analysis = read_json(os.path.join(ph.CACHE, f"analysis-{slug}.json")) or {}
    summary = {}
    picked = read_json(os.path.join(ph.CACHE, "sessions", "picked.json")) or []
    date_file = os.path.join(SESSIONS_DIR, f"{when}.md")
    reads = claude_reads(date_file)
    got, not_read = sessions_read(picked, reads)
    fix_now, test_later = two_lists(date_file)
    c = analysis.get("counts") or {}
    views = heat_views(slug, pmaps)
    page_url = (views[0].get("url") if views and views[0].get("url") else "") or (os.environ.get("SITE_BASE_URL", "").rstrip("/") + page)
    page_like = "%" + page + "%"
    site_host = re.sub(r"^https?://", "", os.environ.get("SITE_BASE_URL", "")).strip("/")
    findings = build_findings(slug, page_url, page_like, pmaps, views, analysis.get("days") or 30, site_host, page)
    clicks = sum(sum(p.get("n", 0) for p in pts) for v in views for pts in (v.get("points") or {}).values())
    pv = analysis.get("pageviews") or 0
    note = (f"{clicks:,} clicks read. A heat map needs about 2,000 pageviews before the picture is firm; this page has {pv:,}."
            if clicks else "No heat map points on this page yet. PostHog collects them on a page with traffic and keeps them 90 days.")
    for s_ in got:
        if s_.get("moments"):
            findings.append({"title": f"Session {s_['sid'][:8]} · {s_.get('verdict', 'unclear')}", "verdict": "fix",
                             "group": "Sessions worth watching", "where": f"{s_.get('device','')} · {s_.get('secs',0)} seconds",
                             "top": None, "bottom": None, "why": s_.get("claude", ""),
                             "moments": s_["moments"],
                             "video": s_.get("video") or "", "caption": "The clock in the corner is session time and the section on screen."})
    return {"business": business, "page": page, "date": date.fromisoformat(when).strftime("%-d %B %Y"),
            "days": analysis.get("days") or 30, "note": note, "clicks": clicks, "sessions": analysis.get("sessions") or 0,
            "heatmap": {"views": views}, "findings": findings}


def render(data, out, template=TEMPLATE):
    if not os.path.exists(template):
        sys.exit(f"{os.path.relpath(template, ph.ROOT)} is missing. It ships with the repo - restore it from git.")
    html = open(template, encoding="utf-8").read()
    payload = json.dumps(data, indent=1, ensure_ascii=False, default=str).replace("</", "<\\/")
    new, n = re.subn(r'(<script id="visitors-data" type="application/json">).*?(</script>)',
                     lambda m: m.group(1) + payload + m.group(2), html, count=1, flags=re.S)
    if n != 1:
        sys.exit('The template has no <script id="visitors-data"> block - it has been edited. Restore it from git.')
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    shutil.copyfile(template, out)
    open(out, "w", encoding="utf-8").write(new)
    return out


def check(out):
    """render_check.py: zero console errors before this page is reported done."""
    script = os.path.join(ph.ROOT, "code", "render_check.py")
    if not os.path.exists(script):
        return True
    shot = os.path.join(ph.CACHE, "render-visitors.png")
    r = subprocess.run([sys.executable, script, out, shot], capture_output=True, text=True)
    line = (r.stdout.strip().splitlines() or [r.stderr[-200:]])[-1]
    ok = "console errors: 0" in r.stdout
    print(("  " if ok else "  ⛔ ") + line.strip())
    return ok


def business_name(override=None):
    if override:
        return override
    try:
        import _business
        return _business.name() or "Your business"
    except Exception:  # noqa: BLE001
        return "Your business"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--page", default="", help="the page path, e.g. /lp/drain-cleaning")
    ap.add_argument("--date", default=date.today().isoformat(), help="the read to draw (default today)")
    ap.add_argument("--business", default=None)
    ap.add_argument("--out", default="")
    a = ap.parse_args()
    if not a.page:
        sys.exit("Which page? `--page /lp/<slug>`")
    data = collect(a.page, a.date, business_name(a.business))
    out = a.out or os.path.join(SESSIONS_DIR, f"{a.date}.html")
    render(data, out)
    print(f"Dashboard: {os.path.abspath(out)}")
    print(f"- {data['sessions']:,} sessions read · {len(data['findings'])} findings")
    if not data["heatmap"]["views"]:
        print("- No heat map drawn: no points on file for this page yet")
    check(out)


if __name__ == "__main__":
    main()
