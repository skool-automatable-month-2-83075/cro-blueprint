# The read - one file, decision first, that an owner acts on
Written 23 September 2026, the dashboard added 25 September 2026 · for /analytics
Next: `python3 code/analyze.py --page /lp/<slug> --days 30 --json`, then `python3 code/build_visitors_dashboard.py --page /lp/<slug>`.

## The shape of analysis.md

Three lines at the top: what page and window, the leads and the rate, the one next action. Then, in this order:
1. Do this first · the decisions, one line each, worst leak first
2. The test · visitors and leads per variant, the split check, the observed lift and the haircut lift, the call (from `split_test.py --status`)
3. The numbers · sessions, phone share, form leads in the browser against the server, phone taps, text taps, bookings, lead rate, failed sends
4. Where they stop reading · how many of 100 got 25 / 50 / 75 / 90% down the page, and the single biggest drop
5. What they click · the top clicked elements with their tag, non-links flagged as dead clicks waiting to happen, rage and dead click totals
6. The form · a count ladder: started, per field touched and left filled, the last field before giving up
7. The count you can trust · PostHog against GoHighLevel against Google Ads, the gap and why, which number to quote to whom
8. Against the market · the page's rate against its vertical median, with the caveat that LocaliQ never defines a conversion
9. Every 30 days: kill / iterate / scale per test, and the four programme numbers (tests run, won, flat, lost)

Written for a plumber. "82 of 100 saw your reviews. 46 reached the price box. 29 reached the form. The price box is where you lose half of them." Never a percentage without the count behind it.

Section names come from `code/page_map.py`, which reads them off the page's own headings. Without it the file says "50% down the page", which no owner can act on. Run the page map first, every time.

## The two files a read produces

- `context/sessions/<date>.md` is the working file: the numbers, Claude's read, the two lists, ticked off as fix-now items ship.
- `context/sessions/<date>.html` is the thing to show: the same read drawn, with the heat map over a picture of the page and the ten sessions as cards.
  - Built by `build_visitors_dashboard.py` from the analysis JSON, the heat map points and the verdicts.
- `analysis.md` at the root stays the latest numbers, decision first.
- Never hand-edit the HTML. If a rule changes, change the builder and rebuild.

## The dashboard, and what may be drawn on the page

`build_visitors_dashboard.py` copies `references/visitors-dashboard-template.html` and replaces ONLY the JSON inside `<script id="visitors-data">`. Never hand-edit the output. If a rule changes, change the builder and rebuild.

Everything drawn on the screenshot is per viewport. The same section sits at a different pixel on a phone and a desktop, so a band or a box built from one map lands in the wrong place on the other. This was a real fault on 28 September 2026: mobile coordinates drawn on a desktop screenshot put every boundary in the wrong place.

- Section bands · keep under 15% of the people who reached it left there, fix 15 to 34%, cut 35% or more.
- The last section is never a leak. Everyone still there has run out of page, not left.
- A box per form field, sized to the field, never the width of the page.
- A ring at each rage-tap cluster, drawn only on the viewport it was measured on.

## Every finding carries a change

A finding is what happened, why it usually happens, and the one change to make. A finding with no change is an observation, and an observation does not belong in a report an owner acts on.

Two honesty rules that stop the report crying wolf:
- Rage taps that start within three seconds of landing are usually impatience while the page paints. Say how many did.
- A tap on an element inside a real button is a normal tap on the icon, not a dead click. Only flag a non-link when nothing clickable sits above it in the chain.

## Measuring a form with no field events

The real read comes from `form_field_focused` and `form_field_blurred`. When a page does not send them, the form is still measured from autocapture clicks: the field's name sits in the `elements_chain` as `attr__name`, and a field with no name attribute is matched by its class, so a phone widget never reads as a false 0%.

Say plainly what that is worth: a tap is not a fill. It ranks the questions and finds the fall between them; it cannot say who left a field empty. The change to prescribe is `<LeadEvents />` on the page.

## What the ones who stay actually do

The scroll bands say where people stop. They do not say whether the people who stayed did anything. Of everyone who landed, count how many touched the form, tapped to call or text, sent it, read past three quarters, and left for another site. A page almost nobody acts on is being read and abandoned, which is a different problem from a leaky top of page and needs a different fix.

## When a number may be read

- A scroll or heat map read needs about 2,000 pageviews on the page; under 500 the file says "not enough yet".
- Every threshold that fails shows as a grey card on the dashboard saying which number and why. A number is never quietly missing.
- A form funnel with percentages needs 100 form starters; under that, counts only.
- An experiment read needs 50 visitors and 5 leads a side before any number means anything, and the planned leads per arm before a call.
- Nothing is read while the split check fails (SRM p under 0.01). Fix plumbing first.

## How to read each part

The test:
- run the split check before anything else
- quote PostHog's chance to win as given, then recompute from exposures and leads and note any gap
- apply the winner's-curse haircut (13%) to every declared lift and print both numbers
- never cut by segment unless the segment was named before launch; if you must, correct for multiple comparisons
- new versus returning before shipping

Scroll and clicks:
- turn scroll percentages into section reach using the page's section offsets at a phone viewport; name the single biggest drop
- treat move maps as guesses and mobile move maps as nothing
- pair every click hotspot with its element tag; a hotspot on a non-link is a dead-click bug

The form:
- report as a ladder: started, first field, phone, sent
- the last field focused in sessions that did not send is the wall

Reconciliation:
- match by `lead_id`, then gclid, then email, then phone, then time window
- Level A (in all three), Level B (two of three), Level C (one). Quote A.
- expect a 10 to 30% gap against Google Ads and say why in one line: Ads books to the click date
- strip spam, duplicates and test leads first and say how many

Benchmarks, LocaliQ 2026, US search, medians, conversion undefined:
- home services 8.05% · plumbing 7.63% · roofing 3.70%
- electricians 9.08% · handyman 13.45% · cleaning 17.65%
- forms-only median across industries (Unbounce): 6.6%
- compare against LocaliQ only after adding tracked calls; compare form-only rates against Unbounce

## Decision rules

- Ship · significant, 50+ visitors and 5+ leads a side, two full weeks, split clean, haircut lift still clears the planned lift.
- Kill · significant the wrong way, or the interval's top is below the planned lift after 30 days, or three iterations of one idea read flat.
- Keep running · not yet significant and the planned sample arrives within 30 more days; print the days.
- Inconclusive at sample · ship the simpler page, log flat, claim nothing.
- Do not test · under about 100 leads a side reachable in eight weeks at a 20% lift; fix tracking or do a before-and-after read instead.
- Do not trust · split broken, Level A under 70% of the PostHog count, or a lift over 50% built on under 30 leads a side.

## Rules

- Decision in the first line. Counts before percentages. Plain words.
- Under 20 PostHog queries a run, every HogQL query with a LIMIT.
- Base rates printed whenever a lift over 20% appears: a third win, median real lift 4 to 8%.
- `python3 code/check_readable.py analysis.md` passes before the file is handed over.
