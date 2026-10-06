"""The money plumbing on the page as it stands: is the phone tracked, is the form wired, does the thank-you page
count once, do the click ids survive to the form. Headless.

    from audit.tracking import tracking
    t = tracking(url, capture_data, cache_dir)

What it looks at: one phone number across every tel: link · a call-tracking or dynamic-number script (Google's
phone snippet after ?gclid=test, CallRail, CallTrackingMetrics, WhatConverts, Invoca) · sms · the form's fields,
types, autofill, labels, required marking, consent wording, honeypot, privacy link, ZIP · conversion scripts
present (Google tag AW-, GTM, GA4, Meta, PostHog, Clarity, Hotjar) · gclid and UTMs persisted to hidden inputs
or storage · the thank-you page (noindex, no nav, tel, calendar embed, callback wording, conversion scripts).
On a page this repo owns (localhost or SITE_BASE_URL) it also runs code/check_tracking.py and merges its lines.
"""
import os
import re
import subprocess
import sys
from urllib.parse import urljoin, urlparse

from playwright.sync_api import sync_playwright

from .common import CODE, MOBILE_UA, is_ours
from .botcheck import settle

SCRIPT_SIGNS = {
    "google_tag": r"googletagmanager\.com/gtag/js\?id=AW-|gtag\('config',\s*'AW-|AW-\d{6,}",
    "gtm": r"googletagmanager\.com/gtm\.js|GTM-[A-Z0-9]{4,}",
    "ga4": r"G-[A-Z0-9]{6,}",
    "meta_pixel": r"connect\.facebook\.net|fbq\(",
    "posthog": r"posthog|/ph-relay/",
    "clarity": r"clarity\.ms",
    "hotjar": r"hotjar\.com",
    "callrail": r"calltrk|callrail|swap\.js",
    "ctm": r"tctm\.co|calltrackingmetrics",
    "whatconverts": r"whatconverts|wc_|scripts\.iconnode",
    "invoca": r"invoca",
    "ringba": r"ringba",
}
CONSENT_RE = re.compile(r"(text|sms|message).{0,120}(agree|consent)|(agree|consent).{0,120}(text|sms|call)", re.I | re.S)
NOT_CONDITION_RE = re.compile(r"not a condition of (purchase|buying)", re.I)
STOP_RE = re.compile(r"\bSTOP\b", re.I)
PHONE_REASON_RE = re.compile(r"(only|just).{0,40}(call|contact|reach) you|so we can call|used to (call|reach)|never (spam|share|sell)", re.I)
CALLBACK_RE = re.compile(r"(within|in under|under|inside)\s+\d+\s*(seconds|minutes|mins|hours?)|same[- ]day|right away|shortly|next business day", re.I)
CALENDAR_RE = re.compile(r"calendly|leadconnector|msgsndr|acuity|cal\.com|hubspot.*meetings|zcal|tidycal|savvycal|youcanbook|setmore", re.I)


def _scripts_in(html):
    return {k: bool(re.search(p, html)) for k, p in SCRIPT_SIGNS.items()}


# ⛔ The four every form asks, unless the owner says otherwise (Jono, 28 September 2026): first name,
# last name, email, phone. One "Your name" box counts as neither first nor last - the follow-up needs both.
ESSENTIALS = {
    "first name": re.compile(r"given-name|first[\s_-]?name|\bfname\b", re.I),
    "last name": re.compile(r"family-name|last[\s_-]?name|surname|\blname\b", re.I),
    "email": re.compile(r"\bemail\b|e-mail", re.I),
    "phone": re.compile(r"\btel\b|phone|mobile|\bcell\b", re.I),
}


def essentials(fields):
    """Which of the four a form asks for, read from each field's name, type, autofill tag and label."""
    seen = [" ".join(str(x.get(k) or "") for k in ("name", "type", "autocomplete", "label", "placeholder"))
            for x in fields if x.get("visible", True) and x.get("type") not in ("hidden", "checkbox", "radio")]
    return {k: any(rx.search(t) for t in seen) for k, rx in ESSENTIALS.items()}


def _form_read(f):
    """One form's facts from capture, judged."""
    t = f.get("text", "")
    return {
        "fields": len(f["fields"]), "field_names": [x["name"] or x["type"] for x in f["fields"]],
        "essentials": essentials(f["fields"]),
        "selects": f["selects"], "textareas": f["textareas"], "chips": f["radios"],
        "tel_input": f["tel"], "autocomplete_on": f["autocomplete"], "labelled": f["labelled"], "required_marked": f["required"],
        "zip_asked": f["zip"], "button": f["button"], "button_outcome": bool(f["button"]) and not re.fullmatch(r"submit|send|go|continue|next", f["button"].strip(), re.I),
        "honeypot": f["honeypot"], "privacy_link": f["privacyLink"],
        "consent_line": bool(CONSENT_RE.search(t)), "consent_not_condition": bool(NOT_CONDITION_RE.search(t)), "consent_stop": bool(STOP_RE.search(t)),
        "phone_reason": bool(PHONE_REASON_RE.search(t)),
        "spam_wording": bool(re.search(r"\bno spam\b|never spam|no obligation|no pressure|no hidden fees", t, re.I)),
    }


def _thank_you(page, base_url):
    """Probe the same-origin /thank-you (the convention every page here uses). None when it does not exist."""
    u = urljoin(base_url, "/thank-you")
    try:
        r = page.goto(u, wait_until="load", timeout=30000)
    except Exception:
        return None
    if not r or r.status >= 400:
        return {"url": u, "exists": False}
    page.wait_for_timeout(600)
    html = page.content()
    d = page.evaluate("""() => { const vis = e => { const r = e.getBoundingClientRect(); return r.width > 0 && r.height > 0; };
      return { robots: (document.querySelector('meta[name=robots]') || {}).content || '', navLinks: [...document.querySelectorAll('header a, nav a, footer a')].filter(vis).length,
               tel: !!document.querySelector('a[href^="tel:"]'), forms: document.querySelectorAll('form').length,
               iframes: [...document.querySelectorAll('iframe')].map(f => f.src), text: (document.body.innerText || '').replace(/\\s+/g, ' ').slice(0, 3000) }; }""")
    return {"url": u, "exists": True, "noindex": "noindex" in (d["robots"] or "").lower(), "nav_links": d["navLinks"], "tel": d["tel"], "forms": d["forms"],
            "calendar": any(CALENDAR_RE.search(s or "") for s in d["iframes"]) or bool(CALENDAR_RE.search(html)),
            "callback_wording": bool(CALLBACK_RE.search(d["text"])), "scripts": _scripts_in(html)}


def tracking(url, cap, cache_dir):
    facts = cap["viewports"]["mobile"]["facts"]
    out = {"tel_numbers": facts["telNumbers"], "tel_links": len(facts["tel"]), "tel_above_fold_mobile": any(t["visible"] and t["top"] < 844 for t in facts["tel"]),
           "sms_links": len(facts["sms"]), "forms": [_form_read(f) for f in facts["forms"]]}
    test_url = url + ("&" if "?" in url else "?") + "gclid=AUDITTEST123&utm_source=audittest&utm_campaign=audittest"
    with sync_playwright() as pw:
        b = pw.chromium.launch()
        ctx = b.new_context(viewport={"width": 390, "height": 844}, user_agent=MOBILE_UA, is_mobile=True, has_touch=True)
        page = ctx.new_page()
        settle(page, page.goto(test_url, wait_until="load", timeout=60000))   # wait out a host's bot check
        try:
            page.wait_for_load_state("networkidle", timeout=8000)
        except Exception:
            pass
        page.wait_for_timeout(1500)
        html = page.content()
        out["scripts"] = _scripts_in(html)
        out["google_phone_snippet"] = page.evaluate("() => typeof window.google_wcc_status !== 'undefined' || typeof window._googWcmGet !== 'undefined'")
        out["gclid_persisted"] = page.evaluate("""() => { const inHidden = [...document.querySelectorAll('input[type=hidden]')].some(i => /AUDITTEST123/.test(i.value));
            let inStore = false; try { inStore = JSON.stringify(sessionStorage).includes('AUDITTEST123') || JSON.stringify(localStorage).includes('AUDITTEST123'); } catch (e) {}
            return { hidden: inHidden, storage: inStore, cookie: document.cookie.includes('AUDITTEST123') }; }""")
        out["utm_persisted"] = page.evaluate("""() => { const inHidden = [...document.querySelectorAll('input[type=hidden]')].some(i => /audittest/.test(i.value));
            let inStore = false; try { inStore = JSON.stringify(sessionStorage).includes('audittest') || JSON.stringify(localStorage).includes('audittest'); } catch (e) {}
            return inHidden || inStore; }""")
        out["thank_you"] = _thank_you(page, url)
        ctx.close(); b.close()
    out["call_tracking"] = any(out["scripts"].get(k) for k in ("callrail", "ctm", "whatconverts", "invoca", "ringba")) or out["google_phone_snippet"]
    out["conversion_script"] = any(out["scripts"].get(k) for k in ("google_tag", "gtm", "ga4", "meta_pixel", "posthog"))
    out["replay_tool"] = any(out["scripts"].get(k) for k in ("posthog", "clarity", "hotjar"))
    out["ours"] = bool(is_ours(url))
    out["check_tracking"] = None
    if out["ours"] and os.environ.get("NEXT_PUBLIC_POSTHOG_KEY"):
        p = subprocess.run([sys.executable, os.path.join(CODE, "check_tracking.py"), url], capture_output=True, text=True, timeout=240)
        lines = [l for l in p.stdout.splitlines() if l.startswith("- ")]
        out["check_tracking"] = {"lines": lines, "passed": p.returncode == 0}
    return out
