Written 23 September 2026, the clock and the validator added 25 September 2026 · for /analytics
Next: `python3 code/page_map.py <url>`, then `python3 code/read_sessions.py --days 7 --url /lp/<slug> --fetch-logs`.


## Who gets watched - three strata, never "the five worst"

Sessions with the most rage clicks are a bug sample: five copies of the same broken button and nothing about the offer. The sessions that decide the offer are the quiet ones.
- A · friction (4): the most rage clicks, dead clicks, errors, or a form that failed to send. Score of 2 or more.
- B · quiet exit (3): reached the form or scrolled past 60%, no errors, at least 30 seconds, left. Picked systematically down the list, not the longest three.
- C · converted (3): the control. Preference for one that touched two or more fields.
Rules: sessions older than 24 hours only (immutable after that); one session per person per stratum; drop anything with zero clicks or under 10 active seconds (bots and blinks); never fill a stratum from another. If B is empty the page is not reaching the form and the finding is upstream (scroll depth) - report that instead of watching.

Frustration thresholds, named in the report: PostHog rage click = 3 clicks within 30px in 1 second; dead click = a click that changed nothing on the page.

## The pipeline

0. `page_map.py <url>` · names every section from its own heading, at a phone and a desktop width, and screenshots the whole page. Everything downstream says "Price", not "50% down the page". Run it before the read and again after the page changes.
1. `read_sessions.py` · HogQL over `events` and `raw_session_replay_events`, plus PostHog's heat map points (clicks, rage clicks, scroll depth, per viewport class). Writes `context/sessions/<date>.md`, the same numbers as `<date>.json` for `code/audit/visitor_fixes.py`, and `code/cache/sessions/picked.json`, pins the ten to a dated playlist, and `--fetch-logs` writes one timeline JSON per picked session.
2. Claude reads the ten timelines and the aggregates. Writes "Claude's read" in the date file: per session, what they did and where they stopped, in one or two lines. Counts, groups, ranks across ALL sessions: "9 rage-tap sessions, all on the same price. 41 abandoned forms, 30 died on the address field."
5. `analyze.py --page /lp/<slug> --json`, then `build_visitors_dashboard.py --page /lp/<slug>` · the numbers and the picture.
6. Claude writes the two lists, then the findings file and the queue.

## Three reads that turn straight into changes (28 September 2026)

- Where they quit the form: the field each starter touched last before leaving without sending.
- How far each section gets: viewers per section, phone and desktop apart, and the share who never reach the next.
- Where they leak off the page: every clicked link that is not a call, a text, an anchor or a legal page.
- `code/audit/visitor_fixes.py` turns them into changes by four rules. Its docstring has the rules and the thresholds.
- Localhost is left out of every count. `--include-dev` keeps it, for testing the pipe only.

## The two lists - the only output that matters

FIX NOW, ships today, no test:
- a bug or friction: the price that does nothing when tapped, the phone field that rejects a local number, a button cut off on a phone, the form that failed to send
- needs a mechanism plus log evidence, or two or more sessions showing it
- nobody argues that a broken button should stay broken

TEST LATER, goes to /split-test, never shipped mid-test:
- anything about copy, the offer, or the structure: the headline feels vague, the offer is buried, reviews sit below the form
- needs a pattern in stratum B that is absent in stratum C
- opinions until a split test proves them. Never change a page while a test is running on it - you contaminate the result and lose weeks of data

## Form field funnel

Field order and the last field before giving up come from the `form_field_focused` / `form_field_blurred` events `LeadEvents.tsx` sends (PostHog autocapture has no focus events). Across 93 million sessions, phone abandonment is 6% mean, 3% median - behind password and email. The killers are dropdowns and open text boxes, which is why the form has neither.

## Rules

- Field names are read, field values never are; inputs are masked in every replay.
- Same window, same run: re-running produces the same ten sessions.
- If the snapshot endpoint refuses the personal key (401), stop and say so. Never scrape with browser cookies.
- The date file is the record, `<date>.html` beside it is the picture. `context/sessions/` keeps every read; the fix-now items are ticked off in the markdown when shipped.
- A session recorded before input masking was switched on is never rendered. Field values never leave the page.
- Every finding goes into `context/visitor-findings.md`, every TEST LATER into `context/test-queue.md`, in the shape each file describes.
- The next `/audit` and `/split-test` read both before they touch the page. A read nobody acts on was not a read.
- Scheduling: `0 7 * * 1 cd <repo> && python3 code/read_sessions.py --days 7 --url /lp/<slug> --fetch-logs` in `crontab -e` makes Monday's read wait in the folder; Claude still writes the lists.
