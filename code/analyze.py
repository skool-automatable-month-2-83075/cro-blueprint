"""The read. Everything the page has produced, in one plain file an owner can act on. The engine of /analytics.

    python3 code/analyze.py --page /lp/drain-cleaning --days 30
    python3 code/analyze.py --page /lp/drain-cleaning --days 30 --experiment drain-cleaning
    python3 code/analyze.py --page /lp/drain-cleaning --crm-leads 55 --ads-conversions 49     # the reconciliation

    python3 code/analyze.py --page /lp/drain-cleaning --json          # ...and code/cache/analysis-<slug>.json for the dashboard

Writes analysis.md at the repo root (or --out). Decision first, one number per line, plain words.
Scroll drops and click hotspots are named by section when code/page_map.py has run on the page - "46 of 100 reached
Price" beats "46 of 100 got 50% down". Every count excludes test leads.
Every query is HogQL with a LIMIT; under 20 queries a run. Numbers are only read when there is enough
behind them: heat map reads need 2,000 pageviews, form funnel reads need 100 starters - below that the
file says "not enough yet" instead of a percentage.
"""
import argparse
import json
import os
import subprocess
import sys
from datetime import date

import _posthog as ph
import page_map as pm

# LocaliQ 2026 medians (home services, US search), the caveat being they never define a conversion.
BENCH = {"home services": 8.05, "plumbing": 7.63, "roofing": 3.70, "handyman": 13.45, "cleaning": 17.65, "all industries (Unbounce median, forms only)": 6.6}


def q(name, sql):
    cols, rows = ph.hogql(sql + ("" if "limit" in sql.lower() else " limit 1000"), name)
    return ph.rows_as_dicts(cols, rows)


def on_page(page, prop="$pathname"):
    """The page filter. A path on this site, or a page on another site by its host and path."""
    return pm.page_sql(page, prop) or f"properties.{prop} like {ph.sql_str(page + '%')}"


def where(page, days):
    return (f"timestamp > now() - interval {int(days)} day and {on_page(page)}"
            " and coalesce(toString(properties.test_lead), '') != 'true'")


def traffic(page, days):
    """Sessions and views. A page that sends no $pageview is counted by its $pageleave, one per view, and says so."""
    r = q("traffic", f"""select count(distinct $session_id) as sessions, countIf(event = '$pageview') as pageviews,
        countIf(event = '$pageview' and properties.$device_type = 'Mobile') as mobile_views,
        countIf(event = '$pageleave') as pageleaves,
        countIf(event = '$pageleave' and properties.$device_type = 'Mobile') as mobile_leaves
        from events where {where(page, days)}""")[0]
    if not (r["pageviews"] or 0) and (r["pageleaves"] or 0):
        return {**r, "pageviews": r["pageleaves"], "mobile_views": r["mobile_leaves"], "no_pageview_event": True}
    return r


def leads(page, days):
    r = q("leads", f"""select
        count(distinct if(event = 'lead_form_submitted', $session_id, null)) as forms,
        count(distinct if(event = 'lead_received', $session_id, null)) as forms_server,
        count(distinct if(event = 'call_clicked', $session_id, null)) as calls,
        count(distinct if(event = 'text_clicked', $session_id, null)) as texts,
        count(distinct if(event = 'booking_made', $session_id, null)) as bookings,
        count(distinct if(event = 'thank_you_viewed', $session_id, null)) as thank_you,
        count(distinct if(event = 'lead_form_failed', $session_id, null)) as failed
        from events where timestamp > now() - interval {int(days)} day
          and coalesce(toString(properties.test_lead), '') != 'true'
          and (({on_page(page)}) or properties.$pathname = '/thank-you')""")[0]
    return r


def scroll(page, days):
    rows = q("scroll", f"""select b as bucket,
        countIf(toFloat(properties.$prev_pageview_max_scroll_percentage) >= b / 100) as reached, count() as total
        from events array join [25, 50, 75, 90] as b
        where event = '$pageleave' and timestamp > now() - interval {int(days)} day
          and coalesce(toString(properties.test_lead), '') != 'true'
          and {on_page(page, "$prev_pageview_pathname")}
        group by b order by b""")
    return rows


def clicks(page, days):
    return q("clicks", f"""select properties.$el_text as text, arrayElement(splitByChar('.', elements_chain), 1) as tag,
        count() as clicks, uniq(distinct_id) as people
        from events where event = '$autocapture' and properties.$event_type = 'click' and {where(page, days)}
        group by text, tag order by clicks desc limit 12""")


def rage(page, days):
    return q("rage2", f"""select event, properties.$el_text as text, count() as n from events
        where event in ('$rageclick', '$dead_click') and {where(page, days)} group by event, text order by n desc limit 10""")


def form_funnel(page, days):
    starters = q("starters", f"select count(distinct $session_id) as n from events where event = 'lead_form_started' and {where(page, days)}")[0]["n"]
    fields = q("fields2", f"""select properties.field as field, count(distinct $session_id) as touched,
        count(distinct if(toString(properties.filled) = 'true', $session_id, null)) as filled
        from events where event = 'form_field_blurred' and {where(page, days)} group by field order by touched desc limit 20""")
    last = q("last-field", f"""select field, count() as n from (
        select $session_id as sid, argMax(properties.field, timestamp) as field,
               countIf(event = 'lead_form_submitted') as sent
        from events where event in ('form_field_focused', 'lead_form_submitted') and {where(page, days)} group by sid)
        where sent = 0 and field is not null group by field order by n desc limit 5""")
    return starters, fields, last


def experiment_block(slug, lift):
    import io, contextlib
    import split_test
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        try:
            split_test.status(slug, lift)
        except SystemExit as e:
            print(f"- could not read the experiment: {e}")
    return buf.getvalue().strip().splitlines()


def section_name(pmap, bucket):
    """A scroll percentage as a section name. '' when no page map has been built for this page."""
    if not pmap or not pmap.get("page_height"):
        return ""
    return pm.section_at(pmap, pmap["page_height"] * bucket / 100)


def pct(a, b):
    return f"{100 * a / b:.1f}%" if b else "n/a"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--page", required=True, help="the page path, e.g. /lp/drain-cleaning")
    ap.add_argument("--days", type=int, default=30)
    ap.add_argument("--experiment", default="")
    ap.add_argument("--lift", type=float, default=0.2)
    ap.add_argument("--crm-leads", type=int, default=None)
    ap.add_argument("--ads-conversions", type=int, default=None)
    ap.add_argument("--vertical", default="home services")
    ap.add_argument("--out", default=os.path.join(ph.ROOT, "analysis.md"))
    ap.add_argument("--json", action="store_true", help="also write code/cache/analysis-<slug>.json, which the dashboard draws from")
    a = ap.parse_args()

    slug = pm.slug_for(a.page)
    pmap = pm.load(slug, "mobile") or pm.load(slug, "desktop")
    t = traffic(a.page, a.days); L = leads(a.page, a.days)
    sc = scroll(a.page, a.days); cl = clicks(a.page, a.days); rg = rage(a.page, a.days)
    starters, fields, last = form_funnel(a.page, a.days)
    sessions = t["sessions"] or 0
    total_leads = (L["forms"] or 0) + (L["calls"] or 0) + (L["texts"] or 0)
    rate = 100 * total_leads / sessions if sessions else 0
    form_rate = 100 * (L["forms"] or 0) / sessions if sessions else 0
    today = date.today().isoformat()

    decisions = []
    if a.experiment:
        exp_lines = experiment_block(a.experiment, a.lift)
        call = next((l for l in exp_lines if l.startswith("**The call")), "")
        if call:
            decisions.append(call.replace("**", ""))
    if L["failed"]:
        decisions.append(f"Fix the form: it failed to send {L['failed']} times. Every one was a lead.")
    if rg:
        top = rg[0]
        decisions.append(f"Fix \"{(top['text'] or 'an element')[:50]}\": {top['n']} {'rage' if top['event'] == '$rageclick' else 'dead'} clicks. Broken or looks clickable and is not.")
    if last:
        decisions.append(f"The form dies on \"{last[0]['field']}\" ({last[0]['n']} people left there). Shorten it, explain it, or move it last.")
    if sc:
        drop = None
        prev = None
        for r in sc:
            reach = (r["reached"] or 0) / (r["total"] or 1)
            if prev is not None and prev - reach > 0.25:
                drop = r["bucket"]
            prev = reach
        if drop:
            where = section_name(pmap, drop)
            decisions.append(f"The biggest exit is between {drop - 25}% and {drop}% down the page"
                             + (f", which is {where}. That section is where they stop." if where else ". Whatever sits there is where they stop."))
    if not decisions:
        decisions.append("Nothing broken. Queue the next structural test.")

    O = [f"# Analysis · {a.page}",
         f"{sessions:,} sessions in {a.days} days · {total_leads} leads · {rate:.1f}% lead rate · written {today}",
         f"Next: {decisions[0]}", "",
         "## Do this first", ""] + [f"- {d}" for d in decisions] + [""]

    if a.experiment:
        O += ["## The test", ""] + [("- " + l if not l.startswith(("-", "#", "**")) else l) for l in exp_lines if l.strip()] + [""]

    O += ["## The numbers", "",
          f"- Sessions: {sessions:,} · {pct(t['mobile_views'] or 0, t['pageviews'] or 0)} on a phone",
          f"- Form leads: {L['forms']} in the browser · {L['forms_server']} accepted by the server · {L['thank_you']} reached thank-you",
          f"- Phone taps: {L['calls']} · text taps: {L['texts']} · bookings on thank-you: {L['bookings']}",
          f"- Lead rate (form + call + text): {rate:.1f}% · form only: {form_rate:.1f}%",
          f"- Form failed to send: {L['failed']}", ""]
    if t.get("no_pageview_event"):
        O[-1:] = [f"- This page sends no $pageview event · the {t['pageviews']:,} views here are counted from page leaves", ""]
    if (L["forms"] or 0) and (L["forms_server"] or 0) and abs(L["forms"] - L["forms_server"]) > max(2, 0.15 * L["forms"]):
        O += [f"- ⛔ Browser and server counts disagree by more than 15% ({L['forms']} vs {L['forms_server']}). Trust the server. Ad blockers or a double fire - run code/check_tracking.py.", ""]

    O += ["## Where they stop reading", ""]
    if (t["pageviews"] or 0) < 500:
        O += [f"- Not enough yet: {t['pageviews'] or 0} pageviews. A scroll read needs about 2,000.", ""]
    else:
        for r in sc:
            at = section_name(pmap, r["bucket"])
            O.append(f"- {r['reached']} of {r['total']} reached {at}" if at
                     else f"- {r['reached']} of {r['total']} got {r['bucket']}% down the page")
            O[-1] += f" · {r['bucket']}% down · {pct(r['reached'] or 0, r['total'] or 0)}" if at else f" · {pct(r['reached'] or 0, r['total'] or 0)}"
        O.append("")

    O += ["## What they click", ""]
    if (t["pageviews"] or 0) < 500:
        O += ["- Not enough yet for a heat map read.", ""]
    else:
        for r in cl[:8]:
            flag = "" if (r["tag"] or "") in ("a", "button") else " · NOT A LINK - a dead click waiting to happen"
            O.append(f"- \"{(r['text'] or 'no text')[:50]}\" ({r['tag']}) · {r['clicks']} clicks by {r['people']} people{flag}")
        for r in rg:
            O.append(f"- {'Rage' if r['event'] == '$rageclick' else 'Dead'} clicks on \"{(r['text'] or 'no text')[:50]}\" · {r['n']}")
        O.append("")

    O += ["## The form", ""]
    if starters < 100:
        O += [f"- {starters} people started the form · {L['forms']} sent it. A percentage needs 100 starters, so these are counts only."]
    else:
        O += [f"- {starters} started the form · {L['forms']} sent it · {pct(L['forms'] or 0, starters)}"]
    for f in fields[:8]:
        O.append(f"- {f['field']} · {f['touched']} touched · {f['filled']} left it filled")
    if last:
        O.append(f"- Last field before giving up: {last[0]['field']} ({last[0]['n']} people)")
    O.append("")

    O += ["## The count you can trust", "",
          f"- PostHog: {L['forms_server']} form leads accepted by the server · {L['calls']} phone taps"]
    if a.crm_leads is not None:
        gap = 100 * (a.crm_leads - (L["forms_server"] or 0)) / (L["forms_server"] or 1)
        O.append(f"- GoHighLevel: {a.crm_leads} contacts · {gap:+.0f}% against PostHog" + (" · fine" if abs(gap) <= 10 else " · look at spam, tests and duplicates"))
    if a.ads_conversions is not None:
        O.append(f"- Google Ads: {a.ads_conversions} conversions · a 10 to 30% gap is normal (Ads books to the click date, PostHog to the day it happened)")
    O.append("- Quote the smallest of these to anyone who pays. Quote the PostHog number to nobody outside the team.")
    O.append("")

    O += ["## Against the market", "",
          f"- You: {rate:.1f}% of sessions become a lead (form + call + text) · {form_rate:.1f}% form only",
          f"- {a.vertical.title()} median (LocaliQ 2026, US search, conversion undefined): {BENCH.get(a.vertical, BENCH['home services'])}%",
          f"- Forms-only median across industries (Unbounce): {BENCH['all industries (Unbounce median, forms only)']}%",
          "- A third of tests win, a third are flat, a third lose. The median real lift is 4 to 8%. A lift over 20% is rare - check it twice.", ""]

    open(a.out, "w").write("\n".join(O))
    if a.json:
        out_json = os.path.join(ph.CACHE, f"analysis-{slug}.json")
        json.dump({"page": a.page, "slug": slug, "days": a.days, "written": today, "sessions": sessions, "pageviews": t["pageviews"] or 0,
                   "mobile_views": t["mobile_views"] or 0, "leads": total_leads, "rate": round(rate, 2), "form_rate": round(form_rate, 2),
                   "counts": dict(L), "decisions": decisions, "scroll": [dict(r, section=section_name(pmap, r["bucket"])) for r in sc],
                   "clicks": [dict(r) for r in cl], "rage": [dict(r) for r in rg], "starters": starters,
                   "fields": [dict(r) for r in fields], "last_field": [dict(r) for r in last],
                   "benchmark": {"vertical": a.vertical, "median": BENCH.get(a.vertical, BENCH["home services"]), "forms_only": BENCH["all industries (Unbounce median, forms only)"]},
                   "crm_leads": a.crm_leads, "ads_conversions": a.ads_conversions,
                   "thresholds": {"scroll_ok": (t["pageviews"] or 0) >= 500, "form_ok": starters >= 100, "pageviews_for_heatmap": 2000},
                   "experiment": a.experiment, "page_map": bool(pmap)},
                  open(out_json, "w"), indent=1, default=str)
        print(f"Wrote {os.path.relpath(out_json, ph.ROOT)}")
    print("\n".join(O[:12]))
    print(f"\nWrote {os.path.relpath(a.out, ph.ROOT)}")
    r = subprocess.run([sys.executable, os.path.join(ph.ROOT, "code", "check_readable.py"), a.out], capture_output=True, text=True)
    print(r.stdout.strip().splitlines()[-1] if r.stdout else r.stderr[-300:])


if __name__ == "__main__":
    main()
