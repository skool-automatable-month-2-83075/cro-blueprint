---
description: See your visitors - PostHog wired the first time, then the heat map, every session's log and ten replays read, the numbers written to one file, and two lists - fix now ships today, test later goes to /split-test
argument-hint: [the page path, e.g. /lp/drain-cleaning] [--days 7 | 30] [--crm-leads N --ads-conversions N]
---

See the visitors on: $ARGUMENTS

**Read first:** `references/session-reading.md` (the three strata, what qualifies for each list) and `references/analysis.md` (the report shape, when a number may be read). One command does the whole of Module 3: setup the first time, the read every time after.

It reads BOTH: the heat map (PostHog's own points drawn over a picture of the page, plus every click by element, the scroll map, rage and dead clicks, the form field drop-off) and the recordings (Claude reads every session's event log). Then it writes the numbers an owner acts on, as a file to work from and a page to look at.



Exit 1 means it printed the manual stop block(s) it needs. Send them to the member as your FIRST message, both in one message, in those words, and nothing else. No scoring, no reading, no files until the keys land.


### Link localhost, never a live URL you have not checked

Everything proved so far was proved on `http://localhost:3000`. Link that, and only that, until a deploy has happened in this run. A live URL that was deployed before PostHog was wired carries no tracking at all: the person opens it on their phone, does everything right, and nothing is recorded.

Never test that with `curl` or a grep of the HTML. posthog-js is loaded by the app at runtime, so it is absent from the served markup on a perfectly good page - a grep says FAIL on a page that works. The only honest check is a browser: `python3 code/check_tracking.py <url>`, whose preflight loads the page and asserts posthog actually booted.

### Then offer to put it live

The tracking only works for real visitors once the page is deployed with the PostHog key in it. Ask once, and take no for an answer:

> The tracking is working on your local copy. Want me to push it live so it starts recording real visitors? Nothing changes about the page itself.

⛔ NEVER DEPLOY WITHOUT A YES. On yes, the same route `/split-test` uses:
1. The host's environment variables first, or the live site renders with no key and measures nothing. From `website/`: `vercel env ls`, and for anything missing, `printf "%s" "<value>" | vercel env add <NAME> production` (repeat for `development`). The two that matter here: `NEXT_PUBLIC_POSTHOG_KEY` and `NEXT_PUBLIC_POSTHOG_HOST`.
2. `npx vercel --prod --yes` from `website/`. Not logged in is a manual stop, one line: run `vercel login`, then say so and the deploy runs. A repo Vercel already watches deploys on push instead; say which route was taken.
3. Prove the deploy before you link it: `python3 code/check_tracking.py <production url> --submit --remote`. That loads it in a real browser, so it catches a build that shipped without the key.
4. Only now is the live URL safe to hand over.

On no: link localhost only, and say the page records nothing from real visitors until it is deployed.

### Offer them a look

The headless check already proved every event fires, so nothing waits on this. But a person who watches their own visit back understands it in a way no PASS line achieves. Offer it once, on a first run, on whichever URL is actually tracked:

> Want to see it working? Open the page on your phone, scroll down, tap the call button and send the form with "TEST LEAD" as the name. Two minutes later I will link you your own recording. Or skip it - the check already passed and nothing is waiting on you.

They say yes: wait about two minutes, then hand back their recording, the heat map and the dashboard. Say a heat map needs hundreds of visits before it draws a picture, so one visit shows as a recording and a lead, not a heat map - otherwise they go looking for something that cannot be there yet. Remind them to delete the TEST LEAD from the CRM; it is excluded from every count either way.

They say no or say nothing: finish the run. Never ask twice, never block on it.

First run on a fresh install: finish with the three PostHog links, the dated TRACKING VERIFIED line, and "come back in seven days for the first read". Nothing to read yet is a fine answer; a read from twelve sessions is not.

Give three clickable links every first run, as `setup_check.py` prints them, with one line saying they never need to open them:
- Heat maps · `<host>/project/<id>/heatmaps` · where the clicks and scroll depth build up
- Session recordings · `<host>/project/<id>/replay/home` · every visit, watchable
- The dashboard · leads by day, the form funnel, calls by button, rage and dead clicks

## STEP 1. Map the page, then pull the heat map and the sessions

`python3 code/page_map.py http://localhost:3000/lp/<slug>` (or the live URL) first, every run. It names every section from its own heading and screenshots the whole page at a phone and a desktop width. Without it every number below is "50% down the page" instead of "reached Price", and the replay clock has no section to show.

Then `python3 code/read_sessions.py --days 7 --url <path> --fetch-logs`. Localhost sessions are left out, since they are our own checks, not visitors. It writes `context/sessions/<date>.md`: the numbers, the scroll map, the click map (hotspots on non-links flagged), rage and dead clicks, where the form dies, and ten sessions picked across three strata (4 friction, 3 quiet exit, 3 converted) with a replay link each, plus one timeline JSON per session in `code/cache/sessions/`. It pins the ten to a PostHog playlist named with the date.

Under about 50 sessions: widen `--days`, and say the read is early.

## STEP 2. Claude reads - the WHAT

Read every timeline in `code/cache/sessions/` and the aggregates. Write "Claude's read" into the date file: one or two lines per session, then the counts across ALL sessions - "9 rage-tap sessions, all on the same price element; 41 abandoned forms, 30 died on the address field; 4 in 5 never scrolled to the form". Counts, groups, ranks. No adjectives.

## STEP 3. The numbers, in one file, then the page to look at

`python3 code/analyze.py --page <path> --days 30 --json [--experiment <slug>] [--crm-leads N --ads-conversions N] [--vertical plumbing]`. It writes `analysis.md` at the repo root, decision first: the split test read if one is running, sessions and lead rate, the scroll map, the click map, the form ladder, the count you can trust (PostHog against GoHighLevel against Google Ads), the market benchmark. For the reconciliation ask for two numbers in one message: contacts created in GoHighLevel in the window, and Google Ads conversions for the page's campaigns.

Add what the script cannot: the element behind each hotspot, Level A / B / C for the count. Section names come from the page map now, not from you. Never read a heat map under 500 pageviews or a funnel percentage under 100 starters - the file says "not enough yet".

Then `python3 code/build_visitors_dashboard.py --page <path>`. It draws the read in the same shell as `/audit`'s audit: a two-pane page, the full-length screenshot on the left with everything marked on it, the findings on the right, hover links the two. Zero console errors before you report it. Give me its absolute path - that page is the thing to look at, the markdown is the working file.

What it marks on the page, all of it per viewport, because a phone page and a desktop page are different heights and a box built from one lands in the wrong place on the other:
- **Section bands** · every section coloured by how many people it holds on to. Green keeps them, amber loses some, red is where the page stops working, hatched the way `/audit` hatches a cut. Each band carries how many were still there, how many left, and the share. The last section never counts as a leak - reaching the end of the page is not leaving.
- **A box per form field**, hugging the field itself, with the share of everyone who touched the form that reached it. Same colours.
- **A ring at each rage-tap cluster**, on the viewport it happened on, labelled with the count.

Every finding carries three things: what happened, **why it usually happens**, and **the change to make**. A finding with no change is not a finding. The rage read also says how many bursts started within three seconds of landing, because that is impatience while the page paints, not a broken control - say it out loud rather than crying wolf.

The five things it reads, worst first:
1. **What the ones who stay actually do** · of everyone who landed, how many touched the form, tapped to call, sent it, read past three quarters, or left for another site. The bands say where people stop; this says whether the ones who stayed did anything. A page nobody acts on is a different problem from a leaky top.
2. **Rage taps**, named by the element under them and what that element usually means.
3. **Off-page taps** · every link that sends someone away from a page whose only job is a call or a form.
4. **The form, field by field** · who reached each question and where the fall is.
5. **Where they leave**, by section.

If the page sends no `form_field_focused` events, the form is still measured - from autocapture clicks, whose `elements_chain` carries the field's `attr__name`. Say plainly that a tap is not a fill: it ranks the questions, it cannot say who left one empty. The change to prescribe is dropping `<LeadEvents />` into the page for the real read. A field with no name attribute is matched by its class, so a phone widget never reads as a false 0%.

## STEP 4. The two lists

Write them into the date file, one line each, worst first:
- FIX NOW · a bug or friction, a mechanism named, log evidence or two or more sessions. The tapped price that opens nothing, the phone field rejecting a local number, the button cut off on a phone, the form that failed to send, a click hotspot on a non-link.
- TEST LATER · copy, offer, structure. Needs a pattern in the quiet-exit stratum that the converted stratum does not show. Opinions until `/split-test` proves them.

Then write them into the two files the next command reads:
- `python3 code/audit/visitor_fixes.py <url>` first: its clicks, leaks and broken contact fields go on Fix now, its fields and sections on Test later
- every finding into `context/visitor-findings.md`, in that file's shape, merged by section and what happens (a repeat raises the count, never a second block)
- every test-later item into `context/test-queue.md`, in that file's shape, worst first, each carrying its counts

Show me both lists, the first three lines of `analysis.md`, and the absolute path to the dashboard. ⛔ APPROVAL GATE, because fix-now goes live today.

## STEP 5. Ship the fix-now list today

Edits in `website/app/lp/<slug>/page.tsx` or the component the bug lives in; `python3 code/check_tracking.py http://localhost:3000/lp/<slug>` still passes; deploy; tick each item in the date file with the date and set its block in `context/visitor-findings.md` to fixed. The one rule: never change a page while a split test runs on it - then the fix-now list waits for the test to be called, and you say so. Append test-later items to `context/test-queue.md`.

Every 30 days the run ends with kill / iterate / scale per test in `context/test-log.md` and the four programme numbers: tests run, won, flat, lost.

## Finish


