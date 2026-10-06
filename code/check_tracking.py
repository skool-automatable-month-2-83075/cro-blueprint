"""Prove every lead event fires exactly once, before anyone quotes a number. Headless.

    python3 code/check_tracking.py http://localhost:3000/lp/drain-cleaning
    python3 code/check_tracking.py <url> --flag lp-drain-cleaning                   # a split pair: the exposure event, the variant on every event, which page rendered
    python3 code/check_tracking.py "<url>?preview=test" --flag lp-drain-cleaning --expect test   # dev server: the preview rendered the page it should
    python3 code/check_tracking.py https://example.com/lp/drain-cleaning --submit    # sends ONE test lead named TEST LEAD (delete it in the CRM)
    python3 code/check_tracking.py <url> --submit --remote                            # ...then confirms the events landed in PostHog

Preflight first, every run: posthog-js installed, the provider mounted in app/layout.tsx, the project key in
website/.env.local, the page answering, the dev server not older than .env.local. A preflight FAIL names the fix.
Then: loads the page, watches every request posthog-js makes, taps the phone link, touches a field,
(optionally) submits the form, and counts the events by name. PASS = exactly one of each.
The faults it catches: fires on page load, fires through failed validation, thank-you recounted on back, two
events for one lead, no replay payload, no exposure event, events without the variant, the wrong page rendered.
Exit 0 = ALL PASS. Exit 1 = at least one FAIL, each on its own line.
On ALL PASS it stamps TRACKING VERIFIED with today's date into code/cache/setup.json and rewrites CLAUDE.md
"## My setup". That date is the 30-day gate every PostHog command checks, so it is written by code, never by hand.
"""
import argparse
import base64
import gzip
import json
import os
import re
import sys
import time
import urllib.parse
from collections import Counter
from urllib.parse import urlparse

import requests
from playwright.sync_api import sync_playwright

import _posthog as ph
import dev_server as ds
import setup_check as sc

WEBSITE = os.path.join(ph.ROOT, "website")
INGEST = re.compile(r"/(e|batch|capture|i/v0/e|s)/?(\?|$)")
FLAGS = re.compile(r"/(flags|decide)/?(\?|$)")
PHONE_UA = ("Mozilla/5.0 (iPhone; CPU iPhone OS 18_5 like Mac OS X) AppleWebKit/605.1.15 "
            "(KHTML, like Gecko) Version/18.5 Mobile/15E148 Safari/604.1")
LOOK_HUMAN = """Object.defineProperty(Navigator.prototype, 'webdriver', { get: () => false });
try { Object.defineProperty(Navigator.prototype, 'userAgentData', { get: () => undefined }); } catch (e) {}
// Playwright cannot read a sendBeacon body, and call_clicked goes out as a beacon. The beacon is still
// sent as normal; a copy of its bytes is kept on window.__phBeacons so the check can count the event.
window.__phBeacons = [];
const phBeacon = Navigator.prototype.sendBeacon;
navigator.sendBeacon = function (url, data) {
  try {
    const blob = data instanceof Blob ? data : new Blob([data == null ? '' : data]);
    blob.arrayBuffer().then(buf => window.__phBeacons.push({ url: String(url), bytes: Array.from(new Uint8Array(buf)) }));
  } catch (e) {}
  return phBeacon.call(navigator, url, data);
};"""
LEAD_EVENTS = ["call_clicked", "text_clicked", "lead_form_started", "form_field_focused", "form_field_blurred", "lead_form_submitted"]


def env_value(path, key):
    if not os.path.exists(path):
        return ""
    for line in open(path).read().splitlines():
        if line.startswith(key + "="):
            return line.split("=", 1)[1].split(" #")[0].strip().strip('"')
    return ""


def is_local(url):
    return (urlparse(url).hostname or "") in ("localhost", "127.0.0.1")


def preflight(url):
    """(ok, text) lines - everything that has to be true before a browser is opened."""
    lines = []
    for pkg in ("posthog-js", "posthog-node"):
        p = os.path.join(WEBSITE, "node_modules", pkg, "package.json")
        if os.path.exists(p):
            lines.append((True, f"{pkg} {json.load(open(p)).get('version', '')} installed in website/node_modules"))
        else:
            lines.append((False, f"{pkg} is not installed - `cd website && npm install` (it is in package.json)"))
    layout = os.path.join(WEBSITE, "app", "layout.tsx")
    src = open(layout).read() if os.path.exists(layout) else ""
    mounted = "<PostHogProvider" in src
    lines.append((mounted, "PostHogProvider mounted in app/layout.tsx - every page, both variants" if mounted
                  else "PostHogProvider is not in app/layout.tsx - mount it around {children}"))
    key = env_value(os.path.join(WEBSITE, ".env.local"), "NEXT_PUBLIC_POSTHOG_KEY")
    lines.append((key.startswith("phc_"), f"NEXT_PUBLIC_POSTHOG_KEY in website/.env.local · {key[:8]}..." if key.startswith("phc_")
                  else "NEXT_PUBLIC_POSTHOG_KEY missing from website/.env.local - `python3 code/posthog_setup.py --connect --key phx_...`"))
    try:
        code = requests.get(url, timeout=60).status_code
    except requests.RequestException:
        code = 0
    lines.append((code == 200, f"{url} answers 200" if code == 200 else f"{url} does not answer ({code or 'no connection'}) - "
                  + ("`python3 code/dev_server.py --start`" if is_local(url) else "check the deploy")))
    if is_local(url):
        h = ds.holder()
        if h and ds.is_ours(h) and ds.env_newer_than_server(h):
            lines.append((False, "website/.env.local changed after the dev server started - `python3 code/dev_server.py --restart`"))
    return lines


def decode(req):
    """posthog-js posts gzip JSON, base64 `data=` forms, or plain JSON. Return the events as dicts."""
    return decode_raw(req.post_data_buffer or b"")


def decode_raw(raw):
    """The same decode for a body read some other way - a beacon copied off window.__phBeacons."""
    if not raw:
        return []
    try:
        body = json.loads(gzip.decompress(raw))
    except Exception:
        try:
            txt = raw.decode("utf-8", "ignore")
            if txt.startswith("data="):
                txt = urllib.parse.unquote_plus(txt[5:])
                try:
                    txt = base64.b64decode(txt).decode("utf-8", "ignore")
                except Exception:
                    pass
            body = json.loads(txt)
        except Exception:
            return []
    items = body if isinstance(body, list) else body.get("batch") or [body]
    return [i for i in items if isinstance(i, dict) and i.get("event")]


def run(url, submit, remote, flag, expect):
    events = Counter()
    sent = []
    replay_payloads = 0
    flag_calls = 0
    with sync_playwright() as pw:
        b = pw.chromium.launch()
        # posthog-js drops every event from a browser that looks automated (HeadlessChrome in the user agent or
        # its brands, navigator.webdriver true). The check has to look like the phone it pretends to be,
        # or it proves nothing. Re-proved 25 September 2026 on posthog-js 1.434: plain headless, _is_bot() true
        # and 0 events; with this UA and init script, _is_bot() false and /e/ posts go out.
        ctx = b.new_context(viewport={"width": 390, "height": 844}, is_mobile=True, has_touch=True, user_agent=PHONE_UA)
        ctx.add_init_script(LOOK_HUMAN)
        page = ctx.new_page()

        def on_req(req):
            nonlocal replay_payloads, flag_calls
            if FLAGS.search(req.url):
                flag_calls += 1
            if req.method != "POST" or not INGEST.search(req.url):
                return
            if re.search(r"/s/?(\?|$)", req.url):
                replay_payloads += 1
            for item in decode(req):
                events[item["event"]] += 1
                sent.append(item)
        page.on("request", on_req)

        page.goto(url, wait_until="networkidle", timeout=60000)
        page.wait_for_timeout(1500)
        loaded = page.evaluate("() => !!(window.posthog && window.posthog.__loaded)") or flag_calls > 0
        marker = page.evaluate("""() => { const m = document.querySelector('[data-split-variant]');
            return m ? { flag: m.dataset.splitFlag, variant: m.dataset.splitVariant, forced: m.dataset.splitForced === 'true' } : null; }""")
        did = next((c["value"] for c in ctx.cookies() if c["name"] == "ph_did"), "")

        tel = page.locator("a[href^='tel:']").first
        if tel.count():
            tel.evaluate("el => { el.addEventListener('click', e => e.preventDefault(), { once: true }); }")
            tel.click()
            page.wait_for_timeout(600)

        # beacons (call_clicked) are invisible to on_req; count the copies the init script kept
        for bcn in page.evaluate("() => window.__phBeacons || []"):
            if INGEST.search(bcn["url"]):
                for item in decode_raw(bytes(bcn["bytes"])):
                    events[item["event"]] += 1
                    sent.append(item)
        page.evaluate("() => { window.__phBeacons = []; }")

        field = page.locator("form input[name='name'], form input:not([type=hidden]):not([tabindex='-1'])").first
        if field.count():
            field.focus(); page.wait_for_timeout(200); field.blur(); page.wait_for_timeout(400)

        submitted_ok = None
        if submit:
            page.fill("form input[name='name']", "TEST LEAD delete me")
            page.fill("form input[name='phone']", "+15555550100")
            if page.locator("form input[name='email']").count():
                page.fill("form input[name='email']", "test-lead@example.com")
            page.locator("form button[type=submit], form input[type=submit]").first.click()
            try:
                page.wait_for_url(re.compile(r"/thank-you"), timeout=15000)
                submitted_ok = True
            except Exception:
                submitted_ok = False
            page.wait_for_timeout(2500)
            # the back-button fault: going back must not fire another lead
            page.go_back(); page.wait_for_timeout(1500); page.go_forward(); page.wait_for_timeout(1500)
        # posthog-js batches events and flushes every 3 seconds; closing sooner loses the form events
        # (25 September 2026: lead_form_started went out 0.5s after a 2s wait closed the browser).
        page.wait_for_timeout(4000)
        ctx.close(); b.close()

    fails = 0

    def line(ok, text):
        nonlocal fails
        fails += 0 if ok else 1
        print(f"- {'PASS' if ok else 'FAIL'} · {text}")

    line(loaded, "posthog-js loaded on the page" if loaded else "posthog-js did not load - the key is not read (restart the dev server) or the provider is not mounted")
    line(events["$pageview"] == 1, f"$pageview fired once · saw {events['$pageview']}")
    line(events["call_clicked"] == 1, f"call_clicked fired once on the phone tap · saw {events['call_clicked']}")
    line(events["lead_form_started"] == 1 and events["form_field_focused"] >= 1, f"form field focus tracked · started {events['lead_form_started']} · focused {events['form_field_focused']}")
    line(events["lead_form_submitted"] == 0 or submit, f"no lead event before a submit · saw {events['lead_form_submitted']}")
    site = os.environ.get("SITE_BASE_URL", "").strip()
    if replay_payloads or not (is_local(url) and site):
        line(replay_payloads >= 1, f"session replay payload sent · {replay_payloads} chunks")
    else:
        print(f"- SKIP · session replay is not expected on localhost (recordings are limited to {site}) - proved on the live URL")
    if submit:
        line(submitted_ok is True, "form reached /thank-you")
        line(events["lead_form_submitted"] == 1, f"lead_form_submitted fired exactly once (back button did not double it) · saw {events['lead_form_submitted']}")
        line(events["thank_you_viewed"] >= 1, f"thank_you_viewed seen · {events['thank_you_viewed']}")

    if flag:
        print(f"\nSplit test · {flag}")
        slug = flag[3:] if flag.startswith("lp-") else flag
        calls = [e for e in sent if e["event"] == "$feature_flag_called" and (e.get("properties") or {}).get("$feature_flag") == flag]
        response = (calls[0].get("properties") or {}).get("$feature_flag_response") if calls else None
        if not calls:
            line(False, "no $feature_flag_called for this flag - <Exposure> is not rendered or posthog-js is not loaded")
        elif response not in ("control", "test"):
            line(False, f"$feature_flag_called sent but the flag answered {response!r} - not created or not active: `python3 code/split_test.py --create {slug}`")
        else:
            line(len(calls) == 1, f"$feature_flag_called sent once · this visitor is in {response} · saw {len(calls)}")
        carried = [e for e in sent if e["event"] in LEAD_EVENTS]
        with_flag = [e for e in carried if (e.get("properties") or {}).get(f"$feature/{flag}") in ("control", "test")]
        if carried:
            ok = len(with_flag) == len(carried)
            line(ok, f"events carry $feature/{flag} · {len(with_flag)} of {len(carried)}" + ("" if ok else " - the browser was not bootstrapped with the flag (lib/posthog-server.ts)"))
        if not marker:
            line(False, "the page is not rendered through <Variant> - page.tsx does not use the split pair (app/lp/_split-template)")
        else:
            line(marker["flag"] == flag, f"page.tsx renders <Variant flag=\"{marker['flag']}\">" + ("" if marker["flag"] == flag else f" - expected {flag}"))
            rendered = marker["variant"]
            if expect:
                line(rendered == expect, f"rendered the {rendered} page" + (" as the preview asked" if rendered == expect else f" - expected {expect}"))
            elif response in ("control", "test"):
                line(rendered == response, f"server rendered {rendered}, PostHog put this visitor in {response}" + ("" if rendered == response else " - bootstrap out of sync"))
            else:
                print(f"- INFO · rendered the {rendered} page" + (" (forced by ?preview)" if marker["forced"] else ""))

    if remote and did:
        print(f"\nWaiting 30s, then checking PostHog for visitor {did[:8]}...")
        time.sleep(30)
        q = f"select event, count() from events where distinct_id = {ph.sql_str(did)} and timestamp > now() - interval 1 hour group by event order by event"
        cols, rows = ph.hogql(q, "tracking-check")
        got = {r[0]: r[1] for r in rows}
        expected = ["$pageview", "call_clicked"] + (["lead_form_submitted", "lead_received", "thank_you_viewed"] if submit else [])
        for name in expected:
            line(got.get(name, 0) == 1, f"PostHog has {name} · {got.get(name, 0)}")
        if flag:
            q2 = (f"select properties.$feature_flag_response as v, count() from events where distinct_id = {ph.sql_str(did)} "
                  f"and event = '$feature_flag_called' and properties.$feature_flag = {ph.sql_str(flag)} and timestamp > now() - interval 1 hour group by v")
            _, rows2 = ph.hogql(q2, "tracking-check-flag")
            seen = {r[0]: r[1] for r in rows2}
            line(bool(seen) and set(seen) <= {"control", "test"}, f"PostHog has $feature_flag_called for {flag} · {seen or 'none'}")
            prop = f"properties.`$feature/{flag}`"
            q3 = (f"select {prop} as v, count() from events where distinct_id = {ph.sql_str(did)} and event in ({', '.join(ph.sql_str(e) for e in LEAD_EVENTS)}) "
                  f"and timestamp > now() - interval 1 hour group by v")
            _, rows3 = ph.hogql(q3, "tracking-check-variant")
            variants = {r[0]: r[1] for r in rows3}
            line(bool(variants) and set(variants) <= {"control", "test"}, f"PostHog lead events carry the variant · {variants or 'none'}")
        print(f"Live events: {ph.ui('activity/explore')}")
    elif remote:
        line(False, "no ph_did cookie - the middleware did not run on this URL, so PostHog cannot be checked for this visitor")
    return fails


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("url"); ap.add_argument("--submit", action="store_true"); ap.add_argument("--remote", action="store_true")
    ap.add_argument("--flag", default="", help="the split-test flag, lp-<slug>")
    ap.add_argument("--expect", choices=["control", "test"], default="", help="with --flag on a ?preview= URL: the page that must have rendered")
    a = ap.parse_args()
    if a.expect and not a.flag:
        sys.exit("--expect needs --flag lp-<slug>.")
    print(f"# Tracking check · {a.url}\n\nPreflight")
    pre = preflight(a.url)
    for ok, text in pre:
        print(f"- {'PASS' if ok else 'FAIL'} · {text}")
    pre_fails = sum(1 for ok, _ in pre if not ok)
    if any(not ok and "does not answer" in text for ok, text in pre):
        print(f"\n{pre_fails} FAIL - the page has to answer before anything else can be checked")
        sys.exit(1)
    print("\nOn the page")
    fails = run(a.url, a.submit, a.remote, a.flag, a.expect) + pre_fails
    if not fails:
        # the 30-day gate every PostHog command reads is this date, written by code, never by hand
        page = urlparse(a.url).path or "/"
        sc.stamp("tracking_verified_at")
        sc.stamp("tracking_page", page)
        sc.write_setup()
    print(f"\n{'ALL PASS - tracking verified' if not fails else str(fails) + ' FAIL - fix before reading any number'}")
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
