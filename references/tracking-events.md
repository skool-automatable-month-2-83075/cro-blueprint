# Lead events - what counts, how it fires once, how it is checked
Written 23 September 2026 from research/research-tracking-events.md (53 sources) · for every PostHog command and /analytics
Next: run `python3 code/check_tracking.py <url> --submit --remote` before quoting any number.

## The events this repo sends

Client, from `website/lib/posthog.ts` and `components/lp/LeadEvents.tsx`:
- `lead_form_started` · first focus on any field
- `form_field_focused` / `form_field_blurred` · field name and whether it was left filled. Never the value.
- `lead_form_submitted` · fired in the SUCCESS branch after the server accepted the post. Once per form per session (sessionStorage guard).
- `lead_form_failed` · the webhook did not accept it. Every one of these was a lead.
- `call_clicked` · a tap on a tel: link, sent as a beacon so it survives the navigation.
  - Intent, not a lead: one person taps three times and that is one human.
  - A guardrail: when taps rise and calls do not, something breaks between the tap and the dial.
- `text_clicked` · a tap on an sms: link. Intent.
- `booking_made` · the calendar on /thank-you confirmed a slot. Advances a lead, never adds one.
  - Calendly sends `calendly.event_scheduled`, GoHighLevel sends `msgsndr-booking-complete`
  - carries `after_form: true`
- `thank_you_viewed` · reached /thank-you. Fallback and diagnostic only. A thank-you view with no lead event in the session is a finding, not a lead.

Server, from `website/app/api/call/route.ts`:
- `lead_call` · GoHighLevel recognised an inbound call to the page's tracking number. THE call conversion.
  - One per caller, forever.
  - Carries `answered`, `duration_seconds`, `call_status`, `tracking_number`, `page`.

Server, from `website/app/api/lead/route.ts`:
- `lead_received` · the webhook accepted the form. This is the count that survives ad blockers and refreshes.
  - carries `lead_id` (minted on the server), the click ids and UTMs, `test_lead`
  - never name, phone or email
- `call_click_received` · the click-to-call beacon reached the server.

Every event carries `$feature/<flag>` for any running split test, because the browser is bootstrapped with the server's flag read.

## What /analytics counts

- A lead = one session with `lead_form_submitted`, plus every `lead_call` (one per caller).
- `call_clicked` is intent, counted separately, never added to the lead total when `lead_call` exists.
- Form leads are cross-checked against `lead_received` from the server.
- When the two disagree by more than 15%, the server number is trusted and the tracking check is re-run.
- `test_lead = true` is excluded from every count.
- A check run submits a form named "TEST LEAD": it flows through like a real one, tagged `test-lead` in GoHighLevel, and never counts.
- A tel: tap is intent. The lead is the answered call. Until a call-tracking number is in place, phone taps are reported as taps, never as calls.

## The five faults, and how they are ruled out

1. Fires on page load: the event lives in the form's success callback. `check_tracking.py` loads the page and asserts zero lead events before a submit.
2. Fires through failed validation: same - only the success branch fires.
3. Thank-you recounted on the back button: the guard key in sessionStorage; the check goes back and forward and asserts the count did not move.
4. Two counts for one lead: one client event, one server event, reconciled, never added.
5. Everything doubles because two systems are both primary: PostHog holds the CRO count; Google Ads holds the bidding count; they are reconciled, never summed.

`python3 code/posthog_setup.py --check-dupes` groups the last 30 minutes by event and session and expects zero rows over 1.

## Calls - counted through GoHighLevel

A plumber's page converts by phone. Until calls are counted, a variant that moves people from the form to the phone reads as a loser, and Smart Bidding learns to buy form fills instead of jobs.

**What counts as a lead (Jono, 25 September 2026): any inbound call GoHighLevel recognised.** Not "answered". Not "over 30 seconds". A missed call is still a lead - the customer raised their hand and their number is in the CRM to call back. The 30-second rule that the industry quotes measures whether the BUSINESS picked up, which is a staffing problem, not a lead-count rule. `answered` and `duration_seconds` ride along as properties so the report can show the answer rate as its own number.

**One lead per caller, forever.** The event's uuid is a hash of the caller's number, so a customer who rings five times is one lead, however often GHL retries the webhook.

### The wiring

1. A GoHighLevel phone number, used on ONE page and nowhere else. Settings, Phone numbers, buy a number, forward it to the real line. One number per page under test - the number is what identifies the page.
2. That number is the only number on the page: the hero, every call button, the mobile bar.
3. `CALL_WEBHOOK_SECRET` in `website/.env.local` (and in the host's environment variables), generated by the command.
4. In GoHighLevel: Automation, new workflow, trigger **Call Status** (or Inbound Call), **no duration filter and no answered filter**. Action: Webhook, POST, to the URL the command prints.
5. The body maps the caller's number, the call id, the direction, the status, the duration and the number they dialled. The route reads the common GHL field names and their aliases.

`website/app/api/call/route.ts` verifies the secret, ignores outbound calls, dedupes by caller, and captures `lead_call` in PostHog with `answered`, `duration_seconds`, `call_status`, the tracking number and the page.

### One number or two, in a split test

- Two numbers, one per variant (the DEFAULT): `CALL_NUMBER_MAP` maps each tracking number to its arm, so `lead_call` carries `$feature/<flag>` and calls count in the verdict.
  - The map lives in `website/.env.local` and the host: `CALL_NUMBER_MAP=<digits>=lp-<slug>:control,<digits>=lp-<slug>:test`.
  - One GoHighLevel workflow covers both numbers; the route reads the dialled number and assigns the arm.
- One number on both variants: a call is attributed to the PAGE, never to an arm. The test is called on form submissions; calls are reported beside it as the page total and a guardrail.
  - The cost of two: a second number to answer, and a returning customer may have saved whichever number they first saw.
- Dynamic number insertion (CallRail-style, swapping the number per visitor and reading the analytics cookie) is the only way to attribute calls to an arm on ONE number.
  - GoHighLevel does not do it.

Say which of the three is in play in any report that shows calls beside a split-test result.

## The consent line - money attached

The form triggers automated texts and calls. Under the TCPA (prior express written consent, elements unchanged as of September 2026 - the one-to-one rule is dead, revocation by any reasonable means is live), the form needs, above the button, unchecked by default:

> By checking this box I agree that {Business legal name} may call and text me at the number I entered about my request, including with automated dialling or prerecorded, artificial or AI-generated messages. Consent is not a condition of purchase. Message frequency varies, message and data rates may apply. Reply STOP to cancel or HELP for help.

Log with the lead: the exact text version, timestamp, IP, page URL, `ph_distinct_id`, `ph_session_id`. Automated outreach holds between 9pm and 8am in the lead's local time. STOP in any reasonable wording ends it within ten business days. Fifteen minutes of work; not legal advice, have a lawyer read the form.

## Attribution

`gclid`, `gbraid`, `wbraid` and `utm_*` are stashed in sessionStorage on first touch (`lib/source.ts`), ride on every form post and call beacon as hidden fields, and reach GoHighLevel as custom fields. PostHog's `$initial_*` person properties are the audit copy, not the primary. Offline import to Google Ads happens from the CRM stage that predicts revenue, keyed on `lead_id`, within 90 days of the click.

## Reconciliation, before any number is quoted

- Level A: leads matched in PostHog, GoHighLevel and Google Ads by `lead_id` or gclid. Quote these.
- Level B: matched in two of three. Report, do not quote.
- Level C: in one system only. A list of things to investigate.
- A 10 to 30% gap between Google Ads and everything else is normal: Ads books the conversion to the click date, PostHog and GHL to the day it happened.
- Strip spam, duplicates and test leads first and say how many were stripped.

## Rules

- One event per real-world act. Names never change once /analytics reads them.
- Field names go to PostHog. Field values never do. Inputs are masked in every replay.
- A booking on the thank-you page is not a second lead.
- Session replay loads only after opt-in wherever a cookie banner is required (EEA, UK); use `opt_out_capturing_by_default` and opt in from the banner.
- Any lead path built on a webhook shape this repo could not verify (CallTrackingMetrics, Calendly signatures) is built from a pasted fixture and marked unverified in the report.
