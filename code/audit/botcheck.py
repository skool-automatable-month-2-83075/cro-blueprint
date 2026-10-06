"""Wait out a bot check before reading a page.

Many hosts (SiteGround, Cloudflare, Sucuri) show an automated browser a challenge screen first: the page
answers 202, 403 or 503, runs a few seconds of script, redirects, and only then serves the real page.
Read it before it clears and the audit scores the challenge screen: on 1 October 2026 a DJ site came back
as one empty section titled "a DJ site", and the redirect crashed the capture half way through.

    status, blocked = settle(page, resp)      # after every page.goto() on a public URL
    if blocked: sys.exit(BLOCKED.format(url=url))
"""
import time

URL_MARKS = ("sgcaptcha", "cdn-cgi/challenge", "challenge-platform", "/_incapsula_", "captcha")
TITLE_MARKS = ("robot challenge", "just a moment", "checking your browser", "attention required", "verify you are human",
               "ddos protection", "access denied", "security check", "please wait")
BLOCKED = ("⛔ {url} is showing a bot check to this browser and it did not clear. That is the site's firewall, "
           "not the page, so nothing was read. Allow this computer in the host's security settings (SiteGround, "
           "Cloudflare), or run it again in a few minutes.")


def is_challenge(page):
    """True while the browser is on a challenge screen, or mid-redirect away from one."""
    try:
        url, title = (page.url or "").lower(), (page.title() or "").lower()
    except Exception:
        return True   # the context is navigating: still settling
    return any(m in url for m in URL_MARKS) or any(m in title for m in TITLE_MARKS)


def settle(page, resp, wait_s=30):
    """Returns (status, blocked). A cleared check reports 200; one that never clears reports blocked=True."""
    status = resp.status if resp else None
    if status != 202 and not is_challenge(page):
        return status, False
    deadline = time.time() + wait_s
    while time.time() < deadline:
        page.wait_for_timeout(1000)
        if is_challenge(page):
            continue
        try:
            page.wait_for_load_state("load", timeout=10000)
        except Exception:
            pass
        if not is_challenge(page):
            return 200, False
    return status, True
