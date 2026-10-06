"""Pull every session on the page, rank them, pick about ten across three strata, and fetch
their event logs so Claude can read them. The "what happened" half of /analytics.

    python3 code/read_sessions.py --days 7 --url /lp/                # summary + the ten picked, written to context/sessions/<date>.md
    python3 code/read_sessions.py --days 7 --url /lp/ --fetch-logs   # ...and one timeline JSON per picked session in code/cache/sessions/

The three strata (research pass, 12 Sep 2026 - random "worst five" is a bug sample, not a friction sample):
  A  the most frustration signals - rage clicks, dead clicks, errors, a form that failed to send   (4)
  B  the quiet ones - reached the form or the call button, no errors, and left                       (3)
  C  converted - the control, so the read knows what a good session looks like                       (3)
Everything is HogQL over the events table. Session recordings are joined only to say "has a replay".

The heat map is pulled as points, not only as counts: clicks, rage clicks and scroll depth from PostHog's own
heatmaps endpoint, per viewport class (phone and desktop), cached to code/cache/heatmap-<slug>-<class>.json.
build_visitors_dashboard.py draws them over the page screenshot; the numbers in the date file come from HogQL.
"""
import argparse
import json
import os
import re
from datetime import date

import _posthog as ph
import page_map as pm

LEAD_EVENTS = ("lead_form_submitted", "call_clicked", "text_clicked")

# Local dev and the check scripts run on localhost. They are not visitors: on 28 September 2026, 45 of 49
# "quit the form at the name field" were check_tracking.py runs. --include-dev keeps them, to test the pipe.
DEV_HOSTS = "properties.$host not like 'localhost%' and properties.$host not like '127.0.0.1%'"


def on_page(url_like, prop="$current_url"):
    """The page filter. A path is matched anywhere in the URL; a page on another site by its host and path."""
    return (pm.page_sql(url_like, "$pathname" if prop == "$current_url" else prop)
            or f"properties.{prop} like {ph.sql_str('%' + url_like + '%')}")


def sessions(days, url_like, include_dev=False):
    # scroll is stored 0 to 1 and read here as a percentage. A page that sends no $pageview still sends the
    # leave, its clicks and its web vitals, so any of them makes a session and a server-only event does not:
    # one audited site's homepage sent 0 pageviews in 765 sessions.
    dev = "" if include_dev else f"and {DEV_HOSTS}"
    q = f"""
    select
      $session_id as sid,
      min(timestamp) as started,
      dateDiff('second', min(timestamp), max(timestamp)) as secs,
      countIf(event = '$pageview') as pageviews,
      countIf(event in ('$pageleave', '$autocapture', '$web_vitals')) as browser_events,
      countIf(event = '$rageclick') as rage,
      countIf(event = '$dead_click') as dead,
      countIf(event = '$exception') as errors,
      countIf(event = 'lead_form_started') as form_started,
      countIf(event = 'form_field_focused') as fields_touched,
      countIf(event = 'lead_form_submitted') as submitted,
      countIf(event = 'lead_form_failed') as failed,
      countIf(event = 'call_clicked') as calls,
      countIf(event = 'text_clicked') as texts,
      100 * max(toFloat(properties.$prev_pageview_max_scroll_percentage)) as scroll,
      any(properties.$device_type) as device,
      any(distinct_id) as person,
      argMin(properties.$current_url, timestamp) as entry,
      any(properties.$referring_domain) as referrer
    from events
    where timestamp > now() - interval {int(days)} day
      and timestamp < now() - interval 24 hour
      and $session_id is not null
      and {on_page(url_like)}
      {dev}
    group by sid
    having pageviews > 0 or browser_events > 0
    order by started desc
    limit 5000
    """
    cols, rows = ph.hogql(q, "sessions")
    return ph.rows_as_dicts(cols, rows)


def replays(days):
    q = f"""
    select session_id, round(sum(active_milliseconds) / 1000) as active_secs, sum(click_count) as clicks,
           sum(keypress_count) as keys, sum(console_error_count) as console_errors
    from raw_session_replay_events
    where min_first_timestamp > now() - interval {int(days)} day
      and min_first_timestamp < now() - interval 24 hour
    group by session_id
    limit 5000
    """
    status, out = ph.call("POST", "query/", {"query": {"kind": "HogQLQuery", "query": q}}, soft=True)
    if status != 200 or not isinstance(out, dict):
        return {}
    cols, rows = out.get("columns") or [], out.get("results") or []
    return {r[0]: dict(zip(cols, r)) for r in rows}


VIEWPORT_CLASSES = {"phone": (320, 767), "desktop": (1024, 3000)}


def heatmap(days, url_like, site=None):
    """Points, per type and viewport class. {} when the endpoint refuses or SITE_BASE_URL is not set - never a crash."""
    site = (site if site is not None else os.environ.get("SITE_BASE_URL") or "").rstrip("/")
    out = {"site": site, "url": "", "types": {}, "refused": ""}
    if not site:
        out["refused"] = "SITE_BASE_URL is not set in .env, so there is no page URL to ask about"
        return out
    page_url = site + (url_like if url_like.startswith("/") else "/" + url_like)
    pattern = page_url.rstrip("/") + "*"
    host, path = pm.split_page(url_like)
    if host:
        # another site: the URL the page map loaded, and a homepage with its #anchors and ?tags but not its subpages
        slug = pm.slug_for(url_like)
        page_url = ((pm.load(slug, "desktop") or pm.load(slug, "mobile") or {}).get("url") or f"https://{host}{path}")
        pattern = page_url.rstrip("/") + ("/(#.*|\\?.*)?" if path == "/" else "*")
    out["url"] = page_url
    for kind in ("click", "rageclick", "scrolldepth"):
        for cls, (lo, hi) in VIEWPORT_CLASSES.items():
            # url_pattern with * wildcards, never url_exact: one page collects clicks under several URLs
            # (?preview=control, #lead-form, a trailing slash) and url_exact treats each as a different page,
            # splitting 19 clicks into piles of 8, 6 and 5 that each look like nothing. Proved 26 Sep 2026:
            # url_exact 10 clicks, url_pattern with * 19, the same page. PostHog globs with *, not SQL's %.
            st, hm = ph.call("GET", "heatmaps/", params={
                "type": kind, "url_pattern": pattern, "date_from": f"-{int(days)}d",
                "viewport_width_min": lo, "viewport_width_max": hi,
                "aggregation": "unique_visitors" if kind != "scrolldepth" else "total_count"}, soft=True)
            if st != 200 or not isinstance(hm, dict):
                out["refused"] = out["refused"] or f"PostHog answered {st} to the heat map endpoint ({str(hm)[:80]})"
                continue
            pts = hm.get("results") or []
            out["types"].setdefault(kind, {})[cls] = pts
            path = os.path.join(ph.CACHE, f"heatmap-{pm.slug_for(url_like)}-{kind}-{cls}.json")
            json.dump({"url": page_url, "type": kind, "viewport": cls, "days": days, "points": pts}, open(path, "w"), indent=1, default=str)
    return out


def aggregates(days, url_like, include_dev=False):
    dev = "" if include_dev else f" and {DEV_HOSTS}"
    where = f"timestamp > now() - interval {int(days)} day and {on_page(url_like)}{dev}"
    out = {}
    # the click map: every element clicked, with its tag, so a hotspot on a non-link is visible
    cols, rows = ph.hogql(f"""select properties.$el_text as el, arrayElement(splitByChar('.', elements_chain), 1) as tag,
        count() as n, uniq(distinct_id) as people from events
        where event = '$autocapture' and properties.$event_type = 'click' and {where} group by el, tag order by n desc limit 12""", "clickmap")
    out["clicks"] = ph.rows_as_dicts(cols, rows)
    # the scroll map: how many of 100 got a quarter, half, three quarters, nine tenths of the way down
    cols, rows = ph.hogql(f"""select b as bucket, countIf(toFloat(properties.$prev_pageview_max_scroll_percentage) >= b / 100) as reached, count() as total
        from events array join [25, 50, 75, 90] as b
        where event = '$pageleave' and timestamp > now() - interval {int(days)} day
          and timestamp < now() - interval 24 hour
          and {on_page(url_like, "$prev_pageview_pathname")}{dev} group by b order by b""", "scrollmap")
    out["scroll"] = ph.rows_as_dicts(cols, rows)
    # PostHog's own heat map POINTS, so the dashboard can draw them over the page: clicks, rage clicks, scroll depth,
    # split by viewport class the way PostHog stores them. Needs SITE_BASE_URL, and the key needs heatmap:read.
    out["heatmap"] = heatmap(days, url_like)
    cols, rows = ph.hogql(f"select properties.$el_text as el, count() as n from events where event = '$rageclick' and {where} group by el order by n desc limit 8", "rage")
    out["rage"] = ph.rows_as_dicts(cols, rows)
    cols, rows = ph.hogql(f"select properties.$el_text as el, count() as n from events where event = '$dead_click' and {where} group by el order by n desc limit 8", "dead")
    out["dead"] = ph.rows_as_dicts(cols, rows)
    cols, rows = ph.hogql(f"""select properties.field as field,
        countIf(event = 'form_field_focused') as focused,
        countIf(event = 'form_field_blurred' and toString(properties.filled) = 'false') as left_empty
        from events where event in ('form_field_focused', 'form_field_blurred') and {where} group by field order by focused desc""", "fields")
    out["fields"] = ph.rows_as_dicts(cols, rows)
    out["form"] = form_exits(where)
    out["reach"] = section_reach(days, url_like, dev)
    out["links"] = link_clicks(where, url_like)
    return out


def form_exits(where):
    """Where the form dies: the field each starter touched LAST before leaving without sending."""
    cols, rows = ph.hogql(f"""select uniqIf($session_id, event = 'form_field_focused') as started,
        uniqIf($session_id, event = 'lead_form_submitted') as submitted from events
        where event in ('form_field_focused', 'lead_form_submitted') and {where}""", "form-started")
    head = ph.rows_as_dicts(cols, rows)[0] if rows else {"started": 0, "submitted": 0}
    cols, rows = ph.hogql(f"""select f.last_field as field, count() as sessions from (
        select $session_id as sid, argMax(properties.field, timestamp) as last_field from events
        where event in ('form_field_focused', 'form_field_blurred') and {where} group by sid) as f
        where f.sid not in (select $session_id from events where event = 'lead_form_submitted' and {where})
        group by field order by sessions desc""", "form-exits")
    return {**head, "exits": ph.rows_as_dicts(cols, rows)}


def section_reach(days, url_like, dev=""):
    """How many reached each section, and what share of them never reached the next one.

    A section counts as seen once 150px of it (or half, if shorter) came into view: max_content is the
    lowest pixel a visitor ever had on screen. Phones are read against the phone map, the rest against
    desktop, because the same section sits at a different depth on each."""
    cols, rows = ph.hogql(f"""select properties.$viewport_width as w, properties.$prev_pageview_max_content_percentage as c
        from events where event = '$pageleave' and timestamp > now() - interval {int(days)} day
          and timestamp < now() - interval 24 hour
          and {on_page(url_like, "$prev_pageview_pathname")}{dev} limit 20000""", "reach")
    out = {}
    for cls in ("mobile", "desktop"):
        m = pm.load(pm.slug_for(url_like), cls)
        vals = [float(c) for w, c in rows if c is not None and (float(w or 0) < 768) == (cls == "mobile")]
        if not m or not m.get("sections") or not m.get("page_height") or not vals:
            continue
        secs = []
        for sec in m["sections"]:
            seen_at = (sec["top"] + min(150, (sec["bottom"] - sec["top"]) / 2)) / m["page_height"]
            secs.append({"name": sec["name"], "heading": sec.get("heading", ""), "reached": sum(1 for c in vals if c >= seen_at)})
        for i, sec in enumerate(secs[:-1]):
            lost = sec["reached"] - secs[i + 1]["reached"]
            sec["lost_pct"] = round(100 * lost / sec["reached"]) if sec["reached"] else None
        out[cls] = {"exits_read": len(vals), "sections": secs}
    return out


def classify_href(href, url_like):
    """contact (a lead), on page (an anchor), legal (keep, small) or leak (a way off the page)."""
    h = (href or "").strip()
    if re.match(r"^(tel|sms|mailto):", h, re.I):
        return "contact"
    if h.startswith("#") or h.split("#")[0].split("?")[0].rstrip("/").endswith(url_like.rstrip("/")):
        return "on page"
    if re.search(r"privacy|terms|legal|cookie", h, re.I):
        return "legal"
    return "leak"


def link_clicks(where, url_like):
    """Every link clicked on the page, classified. A leak is any click that takes a paid visitor elsewhere."""
    href = """extract(elements_chain, 'attr__href="([^"]+)"')"""
    cols, rows = ph.hogql(f"""select {href} as href, count() as n, uniq(distinct_id) as people from events
        where event = '$autocapture' and properties.$event_type = 'click' and {where} and {href} != ''
        group by href order by n desc limit 40""", "links")
    return [{**r, "kind": classify_href(r["href"], url_like)} for r in ph.rows_as_dicts(cols, rows)]


def pick(rows, reps, n_a=4, n_b=3, n_c=3):
    """Three strata, one session per person per stratum, deterministic. Bots and blinks are dropped first:
    a session with a replay but zero clicks, or under 10 active seconds, is not a visitor."""
    def frustration(r):
        return (r["rage"] or 0) * 3 + (r["dead"] or 0) * 2 + (r["errors"] or 0) * 2 + (r["failed"] or 0) * 4
    def human(r):
        rep = reps.get(r["sid"])
        if rep is None:
            return (r["secs"] or 0) >= 10
        return (rep.get("clicks") or 0) > 0 and (rep.get("active_secs") or 0) >= 10
    rows = [r for r in rows if human(r)]
    def one_per_person(lst):
        seen, out = set(), []
        for r in lst:
            if r.get("person") in seen:
                continue
            seen.add(r.get("person")); out.append(r)
        return out
    converted = [r for r in rows if (r["submitted"] or 0) + (r["calls"] or 0) + (r["texts"] or 0) > 0]
    not_conv = [r for r in rows if r not in converted]
    a = one_per_person(sorted([r for r in not_conv if frustration(r) >= 2], key=lambda r: (frustration(r), r["secs"] or 0), reverse=True))[:n_a]
    quiet = [r for r in not_conv if r not in a and frustration(r) == 0
             and ((r["form_started"] or 0) > 0 or (r["scroll"] or 0) >= 60) and (r["secs"] or 0) >= 30]
    quiet = one_per_person(sorted(quiet, key=lambda r: (r["secs"] or 0), reverse=True))
    step = max(1, len(quiet) // n_b) if quiet else 1          # systematic, not top-k: not only the longest
    b = quiet[::step][:n_b]
    c = one_per_person(sorted(converted, key=lambda r: ((r["fields_touched"] or 0) < 2, r["sid"])))[:n_c]
    return [("A frustration", r) for r in a] + [("B quiet exit", r) for r in b] + [("C converted", r) for r in c]


def fetch_log(sid):
    q = f"""
    select timestamp, event,
      properties.$current_url as url, properties.$el_text as el_text, properties.$event_type as kind,
      properties.field as field, properties.filled as filled,
      properties.$prev_pageview_max_scroll_percentage as scroll, properties.$exception_message as error,
      substring(elements_chain, 1, 160) as chain
    from events where $session_id = {ph.sql_str(sid)} order by timestamp limit 800
    """
    cols, rows = ph.hogql(q, f"log-{sid[:8]}")
    return ph.rows_as_dicts(cols, rows)


def new_sections(agg):
    """The three reads that turn into changes: where the form dies, how far each section gets, what leaks."""
    L, form = [], agg.get("form") or {}
    if form.get("started"):
        L += ["## Where they quit the form", "", f"- Started it: {form['started']} sessions",
              f"- Sent it: {form.get('submitted', 0)} sessions"]
        L += [f"- Last field touched before leaving: {r['field']} · {r['sessions']} sessions" for r in form.get("exits", [])] + [""]
    for cls, d in (agg.get("reach") or {}).items():
        L += [f"## How far each section gets · {cls}", "", f"- Page exits read: {d['exits_read']}"]
        for sec in d["sections"]:
            lost = sec.get("lost_pct")
            L.append(f"- {sec['name']}: {sec['reached']} reached it" + (f" · {lost}% of them never reached the next" if lost is not None else ""))
        L.append("")
    leaks = [r for r in agg.get("links") or [] if r["kind"] == "leak"]
    if agg.get("links"):
        L += ["## Where they leak off the page", ""]
        L += [f"- {r['href'][:80]} · {r['n']} clicks by {r['people']} people" for r in leaks] or ["- No clicks on a link that leaves the page"]
        L.append("")
    return L


def section_at_percent(pmap, bucket):
    """25% down a 9,000px page is a section name, not a number. '' when there is no page map yet."""
    if not pmap or not pmap.get("page_height"):
        return ""
    return pm.section_at(pmap, pmap["page_height"] * bucket / 100)


def one_line(r, replay):
    bits = [f"{r['device'] or 'unknown device'}", f"{int(r['secs'] or 0)}s", f"scrolled {int(r['scroll'] or 0)}%"]
    if r["rage"]: bits.append(f"{r['rage']} rage")
    if r["dead"]: bits.append(f"{r['dead']} dead clicks")
    if r["errors"]: bits.append(f"{r['errors']} errors")
    if r["failed"]: bits.append("form failed to send")
    if r["form_started"]: bits.append(f"touched {r['fields_touched']} fields")
    if r["submitted"]: bits.append("SUBMITTED")
    if r["calls"]: bits.append("CALLED")
    if r["texts"]: bits.append("TEXTED")
    bits.append("replay" if replay else "no replay")
    return " · ".join(bits[:4]) + ("\n  - " + " · ".join(bits[4:]) if len(bits) > 4 else "")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--days", type=int, default=7)
    ap.add_argument("--url", default="/", help="only sessions whose URL contains this")
    ap.add_argument("--fetch-logs", action="store_true")
    ap.add_argument("--out", default="")
    ap.add_argument("--include-dev", action="store_true", help="keep localhost sessions - for testing the pipe only")
    a = ap.parse_args()

    pmap = pm.load(pm.slug_for(a.url), "mobile") or pm.load(pm.slug_for(a.url), "desktop")
    rows = sessions(a.days, a.url, a.include_dev)
    reps = replays(a.days)
    agg = aggregates(a.days, a.url, a.include_dev)
    picked = pick(rows, reps)
    today = date.today().isoformat()
    out = a.out or os.path.join(ph.ROOT, "context", "sessions", f"{today}.md")
    os.makedirs(os.path.dirname(out), exist_ok=True)

    total = len(rows)
    conv = sum(1 for r in rows if (r["submitted"] or 0) + (r["calls"] or 0) + (r["texts"] or 0) > 0)
    reached = sum(1 for r in rows if (r["form_started"] or 0) > 0)
    scroll_half = sum(1 for r in rows if (r["scroll"] or 0) >= 50)
    with_replay = sum(1 for r in rows if r["sid"] in reps)

    L = [f"# Session read · {today}",
         f"{total} sessions on pages containing {a.url} · last {a.days} days · {conv} converted · {with_replay} have a replay",
         "Next: read the ten below, write Fix now and Test later, ship Fix now today.", "",
         "A heat map means something at about 2,000 pageviews on one URL; under 500 the click and scroll maps below are early.", "",
         "Frustration = PostHog rage click (3 clicks within 30px in 1s), dead click (click, no change), error, or a form that failed to send.", "",
         "## The numbers", "",
         f"- Sessions: {total}",
         f"- Converted (form, call or text): {conv} · {100 * conv / total if total else 0:.1f}%",
         f"- Started the form: {reached} · {100 * reached / total if total else 0:.0f}%",
         f"- Scrolled past halfway: {scroll_half} · {100 * scroll_half / total if total else 0:.0f}%",
         f"- Rage clicked something: {sum(1 for r in rows if r['rage'])}",
         f"- Hit an error: {sum(1 for r in rows if r['errors'])}", ""]
    if agg["scroll"]:
        L += ["## How far they scroll (the scroll map)", ""]
        for r in agg["scroll"]:
            tot = r["total"] or 0
            at = section_at_percent(pmap, r["bucket"])
            L.append(f"- {r['reached']} of {tot} got {r['bucket']}% down the page" + (f", which is {at}" if at else "")
                     + f" · {100 * (r['reached'] or 0) / tot if tot else 0:.0f}%")
        L.append("")
    if agg["clicks"]:
        L += ["## Where they click (the click map)", ""]
        for r in agg["clicks"][:10]:
            flag = "" if (r["tag"] or "") in ("a", "button", "input", "label") else " · NOT A LINK - looks clickable and is not"
            L.append(f"- \"{(r['el'] or 'no text')[:50]}\" ({r['tag']}) · {r['n']} clicks by {r['people']} people{flag}")
        L.append("")
    hm = agg.get("heatmap") or {}
    if hm.get("types"):
        L += ["## The heat map", ""]
        for kind, by_class in hm["types"].items():
            for cls, pts in by_class.items():
                L.append(f"- {kind} on {cls}: {len(pts)} points on file")
        L += [f"- Drawn over the page by code/build_visitors_dashboard.py · in PostHog: {ph.ui('heatmaps')}", ""]
    elif hm.get("refused"):
        L += ["## The heat map", "", f"- Not pulled: {hm['refused']}", ""]
    if agg["rage"]:
        L += ["## Where they rage click", ""] + [f"- \"{(r['el'] or 'no text')[:60]}\" · {r['n']} times" for r in agg["rage"]] + [""]
    if agg["dead"]:
        L += ["## Where they click and nothing happens", ""] + [f"- \"{(r['el'] or 'no text')[:60]}\" · {r['n']} times" for r in agg["dead"]] + [""]
    if agg["fields"]:
        L += ["## Where the form dies", ""] + [f"- {r['field']} · focused {r['focused']} times · left empty {r['left_empty']} times" for r in agg["fields"]] + [""]
    L += new_sections(agg)
    L += ["## The ten sessions to read", ""]
    for stratum, r in picked:
        L += [f"### {stratum} · {r['sid'][:8]}", f"- {one_line(r, r['sid'] in reps)}", f"- Replay: {ph.ui('replay/' + r['sid'])}", ""]
    L += ["## Claude's read", "", "- ", "",
          "## Fix now · ships today", "", "- ", "", "## Test later · goes to /split-test", "", "- ", ""]
    open(out, "w").write("\n".join(L))
    # the numbers again, as data, for code/audit/visitor_fixes.py - it never parses the prose above
    json.dump({"url": a.url, "date": today, "days": a.days, "sessions": total, "include_dev": a.include_dev,
               "clicks": agg["clicks"], "dead": agg["dead"], "rage": agg["rage"], "fields": agg["fields"],
               "form": agg["form"], "reach": agg["reach"], "links": agg["links"]},
              open(out[:-3] + ".json", "w"), indent=1, default=str)

    picked_path = os.path.join(ph.CACHE, "sessions", "picked.json")
    os.makedirs(os.path.dirname(picked_path), exist_ok=True)
    json.dump([{"stratum": s, **{k: (str(v) if k == "started" else v) for k, v in r.items()}, "has_replay": r["sid"] in reps}
               for s, r in picked], open(picked_path, "w"), indent=1, default=str)

    # pin the ten to a playlist so a human can watch them in PostHog
    st, pl = ph.call("POST", "session_recording_playlists/", {"name": f"read-sessions {today}", "type": "collection",
                                                               "description": "4 friction · 3 quiet exit · 3 converted"}, soft=True)
    if st in (200, 201) and isinstance(pl, dict) and pl.get("short_id"):
        pinned = sum(1 for _, r in picked
                     if ph.call("POST", f"session_recording_playlists/{pl['short_id']}/recordings/{r['sid']}/", {}, soft=True)[0] in (200, 201))
        print(f"Playlist: {ph.ui('replay/playlists/' + pl['short_id'])} · {pinned} of {len(picked)} pinned")
    else:
        print(f"No playlist made (PostHog answered {st}). The key needs session_recording_playlist:write; the ten are still listed in the read.")

    if a.fetch_logs:
        for _, r in picked:
            log = fetch_log(r["sid"])
            json.dump(log, open(os.path.join(ph.CACHE, "sessions", f"{r['sid']}.json"), "w"), indent=1, default=str)
        print(f"Logs: code/cache/sessions/<session id>.json · {len(picked)} files")

    if not pmap:
        print(f"No page map for {a.url} - scroll depths are percentages, not section names. `python3 code/page_map.py <url>` fixes that.")
    print(f"Wrote {os.path.relpath(out, ph.ROOT)} · {total} sessions · {len(picked)} picked")
    for s, r in picked:
        print(f"- {s} · {r['sid'][:8]} · {one_line(r, r['sid'] in reps).splitlines()[0]}")


if __name__ == "__main__":
    main()
