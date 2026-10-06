# PostHog setup - heat maps, replays, flags and events on the page
Written 23 September 2026, the manual stops added 25 September 2026 · step 0 of every command that touches PostHog
Next: paste the one personal API key when a command asks; it does the rest and proves it fires.

One tool does replay, heat maps, flags and experiments, which is why it is PostHog and not three tools. Free tier: 5,000 recordings a month, 30-day replay retention, heat map data kept 90 days.

## What only a human can do

Code cannot create these. Each one is a MANUAL STOP: the command prints the block, waits, and continues the moment the answer lands. Nothing else in this repo waits on anything.

1. A PostHog account and one personal API key. Once, about three minutes.
3. A Vercel login the first time the site deploys. `vercel login` opens a browser. Once.
4. The custom domain on the live site. Recordings are limited to the domain in SITE_BASE_URL.
5. Deleting the one TEST LEAD the tracking check sends to the CRM.
6. Real visitors. A test starts the day it launches; the read comes when the leads do.

Everything else is code's job and is never handed back: the npm package, the project id and key, the region, the project settings, the scripts on every page, the flag, the experiment, the dashboard, and the proof that all of it fires.

## The manual stop, in these words

When PostHog is not connected, the command's FIRST message is this block and nothing else. No scoring, no math, no challenger, no log entry until the key lands. The 25 September 2026 run that built the challenger first ended with a drafted test and nothing wired.

⛔ MANUAL STOP · PostHog account and key · about three minutes, once
1. Go to posthog.com and sign up. Free. Google login is fastest.
2. Name the project after your site when it asks. US or EU cloud, either works.
3. Settings, Personal API keys, Create personal API key. Name it cro-blueprint. Scopes: All access. Copy it, it starts with phx_ and PostHog shows it once.
4. Paste it here.
The moment it lands I do the rest: the project id and key, the region, replay and heat maps on, the scripts on every page, the tracking test, the dashboard. You never open PostHog again.

Both blocks go in ONE message when both are missing. `setup_check.py` prints the ones it needs, in these words.

Already on PostHog: steps 3 and 4 only. A scoped key instead of All access needs user:read, project:read, project:write, action:write, insight:write, dashboard:write, feature_flag:write, experiment:write, session_recording:read, session_recording_playlist:write, query:read.

## Step 0 for every command that touches PostHog

Run this FIRST in `/analytics` and `/split-test`. `/audit` never runs it: an audit needs no PostHog key. It is the only setup there is.

⛔ **It is a wall, not a warning.** Until the personal API key is in `.env`, the command's ONLY output is the ask. No analysis, no page built or copied, no file written, no screenshot, no log entry, and no description of the work it would have done. `/split-test` cannot flip a coin without a flag and `/analytics` cannot read sessions that were never recorded, so a keyless run has not started - it is not a partial one. "Built but not started" is a failure, not a deliverable.

1. Read `.env`, `website/.env.local` and CLAUDE.md "## My setup". Keys present and TRACKING VERIFIED dated in the last 30 days: skip to the command.
2. No personal key: print the manual stop above, and nothing else. Stop. Wait.
3. Key pasted, with no further questions, in this order:
   - `python3 code/posthog_setup.py --connect --key phx_... --enable --dashboard`
   - that one line finds the region, the project, its id and project key, writes `.env` and `website/.env.local`, turns on replay, heat maps and dead clicks, makes the dashboard once
   - `python3 code/dev_server.py --restart` · Next reads the key when it starts, so a running dev server restarts. Only ever stops a server running from this repo's `website/`.
   - `python3 code/check_tracking.py http://localhost:3000/lp/<slug>` · the preflight (package installed, provider mounted, key read, page answers), then every event once
   - a FAIL is fixed right there and the check re-run; never hand it back
   - a split pair: `--flag lp-<slug> --expect control` on `?preview=control`, then `--expect test` on `?preview=test`
4. "## My setup" is written by `setup_check.py` from `code/cache/setup.json`, never by hand: PostHog connected and the date, the project, the dashboard link, input masking, TRACKING VERIFIED with the date. `check_tracking.py` stamps the date itself on ALL PASS. Run `setup_check.py` once more; it says READY when every line is true. The member never opens PostHog.

## What the connect step writes

- `.env` · POSTHOG_PERSONAL_API_KEY, POSTHOG_PROJECT_ID, POSTHOG_API_HOST, NEXT_PUBLIC_POSTHOG_KEY, NEXT_PUBLIC_POSTHOG_HOST, SITE_BASE_URL
- `website/.env.local` · NEXT_PUBLIC_POSTHOG_KEY (the phc_ project key, safe in a browser), NEXT_PUBLIC_POSTHOG_HOST
- SITE_BASE_URL comes from `url:` in `website/lib/site.config.ts` when `.env` does not have it
- More than one project on the account: the current one is used, the rest are listed, `--connect --project <id>` picks another
- Never in the repo. Both files are gitignored, and PostHog rolls a leaked personal key on its own.

## What is already in the website

- `components/posthog/PostHogProvider.tsx` in `app/layout.tsx` boots posthog-js on every page, both variants of a split pair included.
  - It starts with the visitor's flags from the server (`lib/posthog-server.ts`), so a split test never flickers.
- `next.config.mjs` proxies PostHog through `/ph-relay` on this site (three rewrite rules, `skipTrailingSlashRedirect`).
  - Without it ad blockers drop about a third of sessions.
  - The middleware matcher leaves `/ph-relay` alone.
- Init options: `defaults: "2026-05-30"`, pageviews on history change, page leave on (scroll depth rides on it)
  - autocapture, dead clicks, rage clicks, heat maps, replay with every input masked and `[data-ph-mask]` text masked.
- `components/lp/LeadEvents.tsx` dropped once in each page measures every tel: and sms: tap and every form field focus and blur. `references/tracking-events.md` has the event list.
- `components/lp/Variant.tsx` renders the split pair and leaves a hidden marker saying which page rendered; `check_tracking.py --flag` reads it.
- `posthog-js` and `posthog-node` are in `website/package.json`; `npm install` in `website/` puts them in place and the preflight checks they are there.

## What the script switches on in the project

`python3 code/posthog_setup.py --enable` (run by step 0) PATCHes the project settings:
- `session_recording_opt_in: true` · `session_recording_sample_rate: "1.00"` · `session_recording_minimum_duration_milliseconds: 2000`
- `session_recording_masking_config: {maskAllInputs: true, maskTextSelector: "a[href^='tel:'], .phone, [data-ph-mask]"}`
- `heatmaps_opt_in: true` · `capture_dead_clicks: true` · `autocapture_opt_out: false` · console logs and performance on
- `recording_domains` set to the live site so localhost and staging do not burn the free recordings
- never network body capture on a lead-gen site; never a retention above 30d on the free plan

The documented path is `PATCH /api/organizations/<org>/projects/<id>/`; the script tries the legacy `/api/projects/<id>/` first and falls back. Rate limits: 480 calls a minute; the whole setup is under 20 calls.

## Proving it, never eyeballing it

1. `python3 code/check_tracking.py http://localhost:3000/lp/<slug>` · preflight, then the page: pageview once, the phone tap once, the form start once, no lead before a submit.
2. `python3 code/check_tracking.py <live url> --submit --remote` · one TEST LEAD through the form, back and forward, then PostHog asked for exactly one of each event. Add `--flag lp-<slug>` on a split pair: the exposure event, the variant on every event, the page that rendered.
3. `python3 code/posthog_setup.py --check-dupes` · zero rows of an event firing twice in one session.
4. Replay on localhost is reported as SKIP when recordings are limited to the live site; the live URL proves it.

## Headless browsers are filtered, and that is not a bug

posthog-js runs its own bot check (`window.posthog._is_bot()`), and headless Chrome trips it even with a real user-agent and `navigator.webdriver` spoofed. A filtered browser still runs the page, still reads its flags and still renders the right variant - it just never sends an event. So:

- A Playwright run that reports "no events" is telling you about Playwright, not about the page.
  - Verify delivery by looking in PostHog for a SERVER event (`lead_received`, `call_click_received`, `lead_call`), which is captured by posthog-node and never filtered.
- `code/check_tracking.py` reads the events posthog-js *attempts* in the browser, which is why it passes on a page whose events never reach the server.
  - Both checks together are the truth: the script proves the page fires them, a server event proves the pipeline delivers.
- Never "fix" silent events on a live site from a headless result alone.
  - Open the page in a real browser and watch PostHog's live events first.
  - On 25 September 2026 this cost an hour: the production site was healthy the whole time and three working pieces of code were changed chasing it.

## Heat maps, honestly

- Clicks, rage clicks and scroll depth per URL. About 2,000 pageviews on one URL at one viewport class before the picture means anything; under 500 the read is "not enough yet".
- A mouse-move map is not an attention map.
  - The cursor sits still 59% of the time and is 233px from the eye when it does.
  - Read click and scroll maps; treat move maps as guesses and mobile move maps as nothing.
- Scroll depth comes from `$prev_pageview_max_scroll_percentage` on `$pageleave`. On a single-page app it is an upper bound.
- Open the toolbar on the live page (`?__posthog_toolbar=true` or the Heatmaps tab) and screen-share it; that is the lesson.

## Replays, honestly

- Every input masked, phone numbers on the page masked. A replay must never hold a phone number.
- Third-party booking iframes render blank in a replay. Browser policy, not a bug.
- A session is immutable 24 hours after it starts; /analytics only reads those.
- With a cookie banner (EEA, UK): init opted out and opt in from the banner. Without one in the EU: cookieless mode, and accept no identity across days.

## Other sites

WordPress or any HTML site: paste PostHog's snippet in `<head>` ending in `posthog.init('phc_...', { api_host: 'https://us.i.posthog.com', defaults: '2026-05-30' })`, add a tel:/sms: click listener and the form success capture from `research/research-posthog-setup.md`. No proxy without server config; expect some ad-blocker loss. The PostHog "wizard" is an alternative for a member's own site; never run it inside this command - it creates its own events and dashboards that collide with ours.
