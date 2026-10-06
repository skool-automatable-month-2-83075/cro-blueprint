# Research dossier - lead events, call tracking and reconciliation
Built 23 September 2026 · 53 sources opened (52 read in full, 1 snippet only) · for /analytics and /analytics
Next: fold into references/tracking-events.md and code/check_tracking.py

Scope note: research-tracking-google-ads.md (28 August 2026, 76 sources) already covers Google's tag rules, primary vs secondary, One vs Every, conversion windows, offline import timing, Data Manager API and GHL's native Google Ads integration. This file covers the PostHog side, call-tracking vendors, GHL webhook shapes, calendar events, consent law and spam. Where the two overlap this file defers to the earlier one and says so.

---

## Sources

### PostHog official

1. Capture API - https://posthog.com/docs/api/capture - 2026 - single event to `/i/v0/e/`, batch to `/batch/`, required `api_key`, `event`, `distinct_id` (200 char max); missing `distinct_id` returns 200 and drops silently; batch body under 20 MB
2. Identify - https://posthog.com/docs/product-analytics/identify - 2026 - identify() merges anonymous person into identified; already-identified user cannot be re-identified to a different id; reserved strings null, true, false, undefined, anonymous, guest are rejected
3. UTM segmentation - https://posthog.com/docs/data/utm-segmentation - 2026 - utm_source/medium/campaign/content/term auto-captured, `$initial_*` first touch stored in a cookie and backfilled on identify, `$entry_gclid` and `$entry_gad_source` as session properties
4. Sessions - https://posthog.com/docs/data/sessions - 2026 - `$session_id` is UUIDv7, 30 min idle or 24 h max, `posthog.get_session_id()`, pass it as `$session_id` on server events to land them in the same replay
5. Query API - https://posthog.com/docs/api/queries - 2026 - POST `/api/projects/:id/query/` with `{"query":{"kind":"HogQLQuery","query":"..."}}`, Bearer personal key with Query Read scope, 2400 req/h, 240/min, 3 concurrent, 10 s execution cap, no OFFSET
6. Person properties - https://posthog.com/docs/product-analytics/person-properties - 2026 - `$set` overwrites, `$set_once` only if never set, both follow ingestion order not event timestamp, 512 KB per person, `$set` on anonymous events with `identified_only` creates no profile
7. JS config - https://posthog.com/docs/libraries/js/config - 2026 - `custom_campaign_params` default `[]`, `persistence` default `localStorage+cookie`, `cross_subdomain_cookie` true, `cookieless_mode` `always` or `on_reject`, `session_idle_timeout_seconds` 1800
8. JS usage - https://posthog.com/docs/libraries/js/usage - 2026 - `{ transport: "sendBeacon", send_instantly: true }` for an event fired right before navigation; `request_batching` on by default; `posthog.get_distinct_id()`
9. CDP troubleshooting - https://posthog.com/docs/cdp/troubleshooting.md - 2026 - "Events with the same UUID, event name, timestamp, and distinct_id are considered duplicates and are eventually de-duplicated"; send a `uuid` with every server event
10. Ingestion warnings - https://posthog.com/docs/data/ingestion-warnings - 2026 - dedupe by uuid "is not guaranteed due to how merges work in ClickHouse"; invalid uuid drops the event; events over 1 MB dropped; "Refused to merge an already identified user"
11. Google Ads destination - https://posthog.com/docs/cdp/destinations/google-ads - 2026 - experimental; OAuth-linked account, 10-digit customer id, needs gclid on the event, uses person data as it exists at processing time, 6 to 48 h before Google shows it
12. GDPR compliance - https://posthog.com/docs/privacy/gdpr-compliance - 2026 - EU cloud in Frankfurt, IP capture off by default on EU projects, you must not load or must disable capture on opt-out
13. Controlling data collection - https://posthog.com/docs/privacy/data-collection - 2026 - `opt_out_capturing()` stops autocapture, manual capture and replay; `opt_out_capturing_by_default`; `cookieless_mode: 'on_reject'` captures nothing until consent is given or denied, then counts denied users by a server hash
14. posthog-js campaign params (snippet only) - https://github.com/PostHog/posthog-js/issues/922 and posthog-js source via search - 2025-2026 - the SDK registers 24 campaign keys including gclid, gad_source, gbraid, wbraid, gclsrc, fbclid, msclkid, ttclid, dclid; `$initial_gbraid` exists as a person property

### Call tracking vendors

15. CallRail API v3 (webhooks and call object) - https://apidocs.callrail.com/ - changelog to 21 May 2026 - post-call fires after recording and transcription attach, up to 20 min after hangup; call object has `duration` (seconds), `answered`, `first_call`, `gclid`, `fbclid`, `landing_page_url`, `utm_source`, `person_id`, `lead_status`; HMAC-SHA1 `Signature` header; `grab_cookies` custom cookie capture
16. CallRail pricing - https://www.callrail.com/pricing - 2026 - Lead Tracking $50/mo, 5 local numbers, 250 local minutes, 25 texts, $3 per extra number, $0.05 to $0.06 per extra minute, $0.03 per text
17. WhatConverts phone call webhook - https://www.whatconverts.com/help/docs/automations-and-advanced-systems/webhooks/receive-phone-call-data-with-webhooks/ - 2026 - full JSON with `call_duration_seconds`, `answer_status`, `caller_number`, `gclid`, `msclkid`, `google_analytics_client_id`, `landing_url`, `lead_url`, `duplicate`, `spam`
18. WhatConverts pricing - https://www.whatconverts.com/pricing/ - 2026 - single account Call Tracking $30, Plus $60, Pro $100, Elite $160; webhooks only on Elite (single) or any agency plan from $500; local numbers $2.50, local minutes 4.5c
19. Nimbata CTM pricing guide - https://www.nimbata.com/blog/calltrackingmetrics-pricing-guide - January 2026 - CTM Marketing Lite $79, Marketing Pro $179, Sales Engage $329, Enterprise $1,999; numbers and minutes billed on top; webhooks/API from Marketing Pro
20. CTM Training Center Triggers - https://training.ctm.com/platform/triggers/ - 2026 - triggers "automate processes in your account based on specific aspects of a call"; detail lives in a Zendesk article that returned 403 twice
21. Twilio Call resource - https://www.twilio.com/docs/voice/api/call-resource - 2026 - StatusCallback posts `CallSid`, `CallStatus`, `CallDuration` (seconds, terminal events only), `From`, `To`, `Direction`, `ForwardedFrom`, `AnsweredBy`, `Timestamp`, `SequenceNumber`; `X-Twilio-Signature`
22. Twilio US voice pricing - https://www.twilio.com/en-us/voice/pricing/us - 2026 - local number $1.15/mo, inbound $0.0085/min, outbound $0.0140/min, recording $0.0025/min

### GoHighLevel

23. Workflow Action - Webhook (Outbound) - https://help.gohighlevel.com/support/solutions/articles/155000003299-workflow-action-webhook-outbound- - 2026 - POST default; every payload carries name, email, phone, address, tags, all custom fields, `contact_source`, `contact_type`, `gclid`, a `location` object; appointment triggers add a `calendar` object with `appointmentId`, `startTime`, `endTime`, `status`, `calendarName`
24. Inbound Webhook trigger - https://help.gohighlevel.com/support/solutions/articles/48001237383-how-to-use-the-inbound-webhook-workflow-premium-trigger - 2026 - unique URL per trigger, POST/GET/PUT, JSON keys without spaces, "Providing an Email or Phone number in the payload is mandatory" to create or find a contact, contactless mode exists, 100 free premium executions
25. Workflow Action - Custom webhook - https://help.gohighlevel.com/support/solutions/articles/155000003305-workflow-action-custom-webhook - 2026 - GET/POST/PUT/DELETE, custom headers, JSON or form body with `{{contact.email}}` merge fields, Bearer, API key, Basic, OAuth2
26. Contact Deduplication Preferences - https://help.gohighlevel.com/support/solutions/articles/48001181714-allow-duplicate-contact-explained - 2026 - Settings > Business Profile; Allow Duplicate Contact off means a matching email or phone updates the existing contact; primary field Email (default) or Phone plus an optional secondary; applies to forms, Zapier, Facebook and Instagram; CSV always merges
27. Marketplace webhook AppointmentCreate - https://marketplace.gohighlevel.com/docs/webhook/AppointmentCreate/index.html - 2026 - `{type, locationId, appointment:{id, calendarId, contactId, appointmentStatus, source, startTime, endTime, dateAdded}}`; `source` example `booking_widget`
28. Optizent - GHL forms and calendars via GTM - https://www.optizent.com/blog/how-to-track-gohighlevel-form-submissions-and-booking-completions-using-google-tag-manager/ - 2025 - GHL iframes postMessage; `event.data[0] === 'msgsndr-booking-complete'` is the booking signal; a form submit is a message whose `event.data[2]` JSON has `full_name`, `email`, `customer_id`
29. Attributer - capture GCLID in GoHighLevel - https://attributer.io/blog/capture-gclid-gohighlevel - 2026 - hidden GCLID field on the form; native capture only reads the URL at submit time, so persist in browser storage first

### Calendars

30. Calendly advanced embed - https://calendly.com/help/advanced-calendly-embed-for-developers - 2026 - events `calendly.profile_page_viewed`, `calendly.event_type_viewed`, `calendly.date_and_time_selected`, `calendly.event_scheduled`; `e.data.event`, `e.data.payload`; origin check `e.origin === "https://calendly.com"`
31. Calendly webhook subscriptions guide - https://developer.calendly.com/docs/api-guides/receive-data-from-scheduled-events-in-real-time-with-webhook-subscriptions - 2026 - POST `/webhook_subscriptions` with url, events, organization or user, scope; events `invitee.created`, `invitee.canceled`, `routing_form_submission.created`
32. Calendly v2 SDK wiki, webhook payload - https://github.com/kashew/calendly-v2-sdk/wiki/WebhookPayloadClient - 2024 - payload has `uri`, `email`, `name`, `status`, `timezone`, `event`, `tracking.utm_source/medium/campaign/content/term/salesforce_uuid`, `questions_and_answers`, `cancel_url`, `reschedule_url`, `rescheduled`; signing key with tolerance window

### Google Ads reconciliation

33. Offline conversion imports FAQ - https://support.google.com/google-ads/answer/10029210 - rolling - gclid uploads accepted up to 90 days; PII (enhanced conversions for leads) up to 63 days; "still processing this click, re-upload in 12 hours" error
34. ClickSambo 2026 OCI guide - https://clicksambo.com/blog-detail/google-ads-offline-conversion-guide-2026 - 2026 - "75-85% typical", "gclid near 100%", "dual identifiers +10-25% median"; no sample, no named study, vendor selling the thing

### Verification

35. Playwright network guide - https://playwright.dev/docs/network - 2026 - `page.waitForRequest`, `page.waitForResponse(url or predicate)`, `page.route(url, handler)`, `page.on('request')`, `request.postDataJSON()`

### Consent and law

36. 47 CFR 64.1200 - https://www.law.cornell.edu/cfr/text/47/64.1200 - current - (f)(9) prior express written consent definition and its two disclosures, (f)(9)(ii) electronic signature, (c)(1) 8 am to 9 pm local time of called party, (a)(10) any reasonable method and ten business days
37. Kelley Drye - Eleventh Circuit vacates 1:1 rule - https://www.kelleydrye.com/viewpoints/blogs/ad-law-access/eleventh-circuit-vacates-tcpa-11-consent-rule - January 2025 - IMC v. FCC, 24 January 2025, one seller per consent and "logically and topically related" both vacated; 2012 written-consent standard persists
38. BCLP - opt-out rules effective 11 April 2025 - https://www.bclplaw.com/en-US/events-insights-news/the-tcpas-new-opt-out-rules-take-effect-on-april-11-2025-what-does-this-mean-for-businesses.html - 2025 - any reasonable manner, keyword list, ten business days, one clarification message within five minutes with no marketing
39. Wiley - limited waiver of revoke-all - https://www.wiley.law/alert-FCC-Grants-Limited-Waiver-for-Part-of-the-TCPA-Consent-Revocation-Rule - April 2025 - order 7 April 2025 delayed only the cross-topic "revoke all" clause to 11 April 2026; everything else live 11 April 2025
40. Pierce Atwood - FCC deletes TCPA regulations - https://www.pierceatwood.com/alerts/fcc-deletes-tcpa-regulations-following-supreme-court-and-eleventh-circuit-rulings - July 2025 - 14 July 2025 order removed the 1:1 text; McLaughlin Chiropractic v. McKesson (20 June 2025) lets district courts read the TCPA without deferring to FCC orders
41. Consumer Financial Services Law Monitor - final rule on consent - https://www.consumerfinancialserviceslawmonitor.com/2025/09/fccs-final-rule-on-consent-kills-one-to-one-consent-requirement/ - 8 September 2025 - (f)(9) text back to the 2012 wording
42. Mac Murray & Shuster - revoke-all pushed to 31 January 2027 - https://mslawgroup.com/delayed-again-fcc-pushes-back-tcpas-revoke-all-rule-to-january-31-2027/ - January 2026 - order 7 January 2026; other revocation rules "remain in force"
43. Troutman - FCC revises revocation rules - https://www.troutman.com/insights/fcc-revises-tcpa-revocation-of-consent-rules-that-were-set-to-go-into-effect-in-january/ - September 2026 - Report and Order 9 September 2026: informational revocations may be scoped to category; "a single revocation still revokes consent or permission for all future telemarketing from that caller"; effective 30 days after Federal Register publication
44. ActiveProspect - express written consent checklist - https://activeprospect.com/blog/express-written-consent/ - 2025 - above the button, name the seller, say calls and texts, say autodialer and prerecorded or artificial voice, not a condition of purchase, how to opt out, unchecked checkbox, keep timestamp, IP, page URL, consent text, snapshot
45. ICO - cookies and similar technologies - https://ico.org.uk/for-organisations/direct-marketing-and-privacy-and-electronic-communications/guide-to-pecr/cookies-and-similar-technologies/ - current - consent before any non-essential storage or access, UK GDPR standard, no pre-ticked boxes; "helpful or convenient" is not "strictly necessary"
46. Termly - California wiretapping claims - https://termly.io/resources/articles/california-wiretapping-claims-against-website-tracking/ - 2026 - CIPA 631 and 638.51; Javier v. Assurance IQ (9th Cir. 2022) session replay before consent; $5,000 per violation; block replay, chat and pixels until opt-in
47. Enzuzo - SB 690 and CIPA - https://www.enzuzo.com/blog/sb-690-and-cipa - August 2026 - narrowed bill removes only the private right of action for 638.51 pen-register claims; 631 wiretap exposure for session replay stays at $5,000 per violation; not law as of that writing

### Spam and bots

48. Core Forms - reCAPTCHA v3 vs Turnstile vs hCaptcha - https://core-forms.com/blog/captcha-comparison/ - 2026 - bundle weights 110 KB, 60 KB, 80 KB; v3 thresholds 0.5 standard, 0.7 high value, 0.3 conversion-sensitive; author runs Turnstile + Akismet + honeypot on contact forms
49. Digital Applied - honeypot-first playbook - https://www.digitalapplied.com/blog/form-bot-defense-honeypot-first-playbook - 2026 - 20 to 40 percent junk on their lead forms; honeypot caught 8 of 14 junk in one batch; off-screen not display:none, tabindex -1, autocomplete off, silent 200
50. Google Cloud reCAPTCHA tiers - https://docs.cloud.google.com/recaptcha/docs/compare-tiers - 2026 - free to 10,000 assessments a month per organisation with a billing instrument, $8 flat for 10,001 to 100,000, $1 per 1,000 above
51. Cloudflare Turnstile server-side validation - https://developers.cloudflare.com/turnstile/get-started/server-side-validation/ - 2026 - POST `https://challenges.cloudflare.com/turnstile/v0/siteverify`, token valid 300 s, single use, `timeout-or-duplicate` on reuse, returns `success`, `challenge_ts`, `hostname`, `action`, `cdata`
52. Cloudflare Turnstile plans - https://developers.cloudflare.com/turnstile/plans/ - 2026 - free plan 20 widgets, 10 hostnames per widget, unlimited verifications
53. WPForms - research-based form conversion tips - https://wpforms.com/research-based-tips-to-improve-contact-form-conversions/ - rolling - CAPTCHA "around 3% of total conversions" (Moz), mandatory phone field abandonment 39% vs 4% optional (Small Farm Design), no sample sizes given

Not reached: CallRail support article on webhooks (403), CTM webhook Zendesk articles (403, twice), Calendly signature header doc (404), PostHog legacy `/api/projects/:id/events/` reference (page returned navigation only), FCC DA 25-312 PDF (binary). Anything that depended on these is marked inferred below.

---

## Findings

### 1. What counts as a lead and the five double-count faults in PostHog terms

- A lead is one real-world act by one person: a form that reached the server and was accepted, a call answered for at least the minimum length, a booking that exists in the calendar. Taps on tel: and sms: are intent signals, kept as separate events and never summed into the lead count. (repo rule, consistent with rules 1 and 2 of the Google Ads dossier)
- Fault 1, fires on load: a `lead_form_submitted` capture placed in page script instead of a success handler. PostHog will not save you; capture accepts anything with an `api_key`, `event` and `distinct_id` and returns 200. (a) #1
- Fault 2, fires through failed validation: capturing on the button click or the `submit` DOM event. The fix is capturing only in the callback that runs after the server returned 2xx. GHL embedded forms never emit a DOM submit, they postMessage from an iframe; the success signal is the message whose third array element parses to JSON with `full_name` and `email`. (b) #28
- Fault 3, thank-you page recounted on back or refresh: any pageview-based conversion re-fires. In PostHog the thank-you pageview is a fallback only, and the dedupe is `$set_once: { lead_form_submitted_at: <iso> }` on the person plus a server-issued `lead_id` carried as an event property so a HogQL `count(DISTINCT properties.lead_id)` is the truth. (a for `$set_once` semantics) #6
- Fault 4, two primaries: in PostHog terms two event names for one act, for example `form_submit` from autocapture-like instrumentation and `lead_form_submitted` from the handler, both counted in a dashboard. One event name per real act, everything else is a property. (repo rule)
- Fault 5, Every vs One: the PostHog analogue is counting events instead of persons. Insights that report leads use unique persons or `count(DISTINCT properties.lead_id)`, never raw event count. (a for HogQL) #5
- `$set_once` is ingestion-ordered, not timestamp-ordered, so a late-arriving server event can win the key. Idempotency therefore comes from `lead_id` plus a client-generated event `uuid`, not from `$set_once` alone. (a) #6 #9
- PostHog dedupes events with the same uuid, event name, timestamp and distinct_id "eventually" and "not guaranteed". Treat it as a safety net, not a design. (a) #9 #10
- Person profiles: with the default `person_profiles: 'identified_only'`, `$set_once` on an anonymous event creates no profile. Either identify the lead at submit time (email or phone hash as distinct_id, see area 5) or run `person_profiles: 'always'`. (a) #6
- identify() is one-way: once a browser is identified as A it cannot be re-identified as B, and PostHog logs "Refused to merge an already identified user". A shared tablet in a shop or a second lead from the same phone needs `posthog.reset()` after the thank-you, or the second lead inherits the first person. (a) #2 #10

### 2. Phone: tel: click vs answered call, DNI vendors, forwarding to PostHog

- A tel: tap is a client event fired in the anchor's click handler with `{ transport: "sendBeacon", send_instantly: true }` because the dialler steals focus and the default batch queue may never flush. (a) #8
- A qualified call is a server event created from the vendor's post-call webhook when duration is at or above the threshold. The earlier dossier's default is 60 s with a 30 to 60 band; this repo's brief says 30 s, so the check reads the threshold from config and asserts the same number in Google Ads, the vendor filter and the PostHog event property. (repo)
- CallRail: post-call webhook fires only after recording, transcription and call summary attach, with a hard 20 minute ceiling after hangup; call-modified fires later with a `changes` array (`tags`, `note`, `value`, `transcription_text`, `recording_duration`, `auto_score`, `manual_score`) and also when a call is marked spam. Webhook slots per integration: `pre_call_webhook`, `answered_call_webhook` (Call Routing Complete), `post_call_webhook`, `updated_call_webhook`, `sms_received_webhook`, `sms_sent_webhook`, `form_captured_webhook`, `post_outbound_call_webhook`, `updated_outbound_call_webhook`. Body is the call object: `duration` in seconds, `answered` boolean, `first_call`, `prior_calls`, `lead_status` (`good_lead`, `not_a_lead`, `previously_marked_good_lead`, null), `gclid` and `fbclid` "as captured from the landing page parameter, available for calls placed to Website (Session) trackers", `landing_page_url`, `last_requested_url`, `utm_source`, `utm_term`, `keywords` (paid only), `person_id`, `milestones.first_touch` and `last_touch`, `tracking_phone_number`, `customer_phone_number` (E.164). Signature is Base64 of HMAC-SHA1 over the raw body with the company signing key, sent in a `Signature` header; test key `072e77e426f92738a72fe23c4d1953b4` must produce `UZAHbUdfm3GqL7qzilGozGzWV64=`. Retention 25 months. Transcript fields need Premium Conversation Intelligence from 21 May 2026. (a) #15
- CallRail `grab_cookies`: a Custom Cookie Capture integration takes an array of cookie names to attach to visitor sessions. Putting the PostHog cookie name there (default `ph_<project_token>_posthog`) attaches the PostHog distinct_id and session state to the CallRail visitor record, which is the cleanest join. The cookie value is JSON with `distinct_id` and `$sesid`; that it is readable this way is inferred, not tested. (a for the feature, inferred for the join) #15 #7
- WhatConverts: webhook fires "when a phone call lead is created" with `trigger: "new"`, `lead_type: "Phone Call"`, `lead_status: "Unique"` or repeat, `call_status`, `answer_status: "Answered"`, `call_duration_seconds`, `caller_number`, `tracking_number`, `destination_number`, `line_type`, `landing_url`, `lead_url`, `lead_source/medium/campaign/content/keyword`, `gclid`, `msclkid`, `google_analytics_client_id`, `facebook_click_id`, `ip_address`, `device_type`, `spam` and `duplicate` booleans. Up to five webhooks fire simultaneously. A separate "Phone Call (In Progress)" webhook exists for the answer moment and a "(Modified)" one for later edits. (a) #17
- WhatConverts pricing gate: single-account plans expose webhooks only on Elite ($160/mo); Plus ($60) and Pro ($100) have the Google Ads integration but no webhooks; Call Tracking ($30) has neither. Included volume on single plans is 148 calls and 300 forms/chats; overage local numbers $2.50, local minutes 4.5c. (a) #18
- CallRail pricing: four tiers $50, $95, $150, $195 (Lead Tracking, Lead Tracking Complete, Lead Conversion, Lead Conversion Complete per the search summary; the pricing page confirmed $50 with 5 numbers, 250 minutes, 25 texts, $3 per extra number, $0.05 to $0.06 per extra minute). Which tier unlocks webhooks is not on the pricing page; the API docs describe webhooks without a plan gate. (a for numbers, unconfirmed for gate) #16 #15
- CTM: Marketing Lite $79, Marketing Pro $179, Sales Engage $329, Enterprise $1,999 monthly; numbers and minutes billed on top, transcription $0.02/min; webhooks and API from Marketing Pro up; Triggers evaluate call attributes and can run actions, detail behind a 403 wall so field names are unconfirmed. (b for pricing, unconfirmed for payload) #19 #20
- Twilio DIY: buy a local number ($1.15/mo), forward with TwiML `<Dial>` and set `statusCallback` with `statusCallbackEvent` `initiated ringing answered completed`; the `completed` POST carries `CallDuration` in seconds, `CallStatus`, `From`, `To`, `ForwardedFrom`, `Direction`, `AnsweredBy` when AMD is on, `SequenceNumber`; verify `X-Twilio-Signature`. Inbound $0.0085/min, recording $0.0025/min. DIY has no DNI and no gclid; you build the swap script and the visitor-to-number pool yourself, so it only makes sense for a single static number per variant. (a) #21 #22
- Forwarding into PostHog: POST to `https://us.i.posthog.com/i/v0/e/` (or `eu.`) with `api_key`, `event: "lead_call_qualified"`, `distinct_id`, `timestamp` (ISO 8601, the call start), `uuid` (deterministic UUIDv5 of provider plus call id so a retried webhook lands on the same uuid), `properties.$session_id` (the visitor's UUIDv7 if the vendor captured it, else omitted), `properties.$set_once` for first-touch. Sessions expire at 30 idle minutes or 24 h, so a `$session_id` for a call that happens next day is stale; send it anyway for the replay link, the join key for reporting is `lead_id` or `gclid`. (a) #1 #4 #9
- distinct_id strategy: the browser's anonymous distinct_id is written into a hidden form field and into the vendor's session (via `grab_cookies` on CallRail, via `google_analytics_client_id` style custom fields elsewhere). Server events use that same distinct_id when present; when the caller never touched the site (call asset, GBP) use a stable hash of the E.164 caller number as distinct_id so repeat calls from one phone are one person. Never use raw phone numbers as distinct_id in a project with EEA visitors. (b) #2 #15
- Vendor webhooks arrive late (CallRail up to 20 min) and out of order (modified after post-call). The receiver upserts by provider call id and only emits `lead_call_qualified` once, keyed in its own store, before calling PostHog. (a for timing) #15

### 3. GoHighLevel as the truth for lead counts

- Inbound webhook trigger: one URL per trigger, POST/GET/PUT, flat JSON keys without spaces, email or phone mandatory to create or match a contact; contactless workflows can run without creating a contact. Deleting and recreating the trigger rotates the URL. Premium action, 100 free executions for agencies. (a) #24
- Payload for a form lead from the landing page server should be: `first_name`, `last_name`, `email`, `phone` (E.164), `source` (e.g. `lp-plumber-v2`), `variant`, `gclid`, `gbraid`, `wbraid`, `utm_source`, `utm_medium`, `utm_campaign`, `utm_term`, `utm_content`, `landing_page`, `ph_distinct_id`, `ph_session_id`, `lead_id`, `consent_text_version`, `consent_timestamp`, `consent_ip`, `test_lead`. Each maps to a contact custom field in the Create/Update Contact step; GHL custom fields are contact-scoped text fields whose query key must match exactly and is case-sensitive. (a for the mechanism, repo for the field list) #24 #29
- Outbound webhook action: sends full name, first, last, email, phone, address block, tags, every standard and custom field, `contact_source`, `contact_type`, `gclid`, a `location` object, plus trigger data: appointment triggers add a `calendar` object with `appointmentId`, `calendarName`, `startTime`, `endTime` (format `YYYY-MM-DDTHH:mm:ss`), `status`, `selectedTimezone`; pipeline triggers add `opportunity_name`, `status`, `lead_value`, `pipeline_stage`; generic triggers such as Tag Added send contact fields only. Custom key-value items accept merge fields like `{{contact.source}}`. No files. Retry behaviour undocumented. (a) #23
- Custom Webhook action: GET/POST/PUT/DELETE, custom headers, Bearer/API key/Basic/OAuth2, JSON or form body with merge fields. Use it to POST straight to PostHog's capture endpoint from a GHL workflow when a contact reaches a stage, with `api_key` in the body and `distinct_id` from the `ph_distinct_id` custom field. Signature verification of GHL-to-you calls is not documented on this page. (a) #25
- Marketplace webhooks (app-level, not workflow): `AppointmentCreate` delivers `{type, locationId, appointment:{id, calendarId, contactId, groupId, appointmentStatus, assignedUserId, source, startTime, endTime, dateAdded}}` with `source: "booking_widget"` for the embed. This is the cleanest booking truth if a marketplace app is installed; otherwise the workflow trigger "Appointment Booked" plus outbound webhook gives the same facts. (a) #27 #23
- Dedupe: Settings > Business Profile > Contact Deduplication Preferences. Allow Duplicate Contact off (default) means forms, Zapier, Facebook and Instagram submissions that match the primary field (Email by default, or Phone) update the existing contact; a secondary field can be checked when the primary misses. CSV imports always merge on phone or email regardless. For a local service business the primary should be Phone, secondary Email, because callers rarely give an email and the phone is what the call tracker sees. (a for the setting, b for the choice) #26
- Consequence for counting: with dedupe on, a repeat submitter produces one contact and a new "Form Submitted" trigger run, not a new contact. Lead count in GHL is therefore "contacts created" for new leads and "form submissions" for volume; /analytics compares PostHog `lead_form_submitted` unique `lead_id` against GHL form submissions, and unique persons against GHL contacts created, and reports both gaps. (repo)
- Tagging source and variant: write `variant` and `source` to custom fields, and add tags `src:lp-<slug>` and `var:<a|b>` in the Create/Update Contact step so filters and the outbound payload carry them. The earlier dossier noted gclids vanish on contact merges; the same is true of the first variant, hence `$set_once` in PostHog is the immutable copy. (b) #23 #26

### 4. Calendar bookings

- GHL embed: the calendar iframe posts a message whose first array element is `msgsndr-booking-complete`; a form step inside the widget posts contact JSON in the third element. Listen on `window`, check the origin is a GHL domain, and fire `lead_booking_made` once per `appointmentId` if present or once per page load if not. (b) #28
- Calendly embed: `calendly.event_scheduled` in `e.data.event`, with `e.data.payload.event.uri` and `e.data.payload.invitee.uri` (uri fields inferred from the SDK wiki, the help page only shows `payload`); guard with `e.origin === "https://calendly.com"` and `e.data.event.startsWith("calendly.")`. (a for names and guard, inferred for payload keys) #30 #32
- Calendly webhooks: POST `/webhook_subscriptions` with `url`, `events`, `organization` or `user`, `scope`; events `invitee.created`, `invitee.canceled`, `routing_form_submission.created`; payload has `email`, `name`, `status`, `timezone`, `event` (scheduled event uri), `tracking.utm_*` and `salesforce_uuid`, `questions_and_answers`, `cancel_url`, `reschedule_url`, `rescheduled`. UTMs appended to the scheduling URL flow into `tracking`, so put `utm_content=<variant>` and `salesforce_uuid=<lead_id>` on the embed URL. Signature header and plan gate not confirmed from an opened page. (a for subscription, b for payload) #31 #32
- The thank-you rule: a booking made on the thank-you page after a form is the same lead advancing, not a second lead. `lead_booking_made` carries `lead_id` from the form when available and `after_form: true`; /analytics counts leads as `uniq(lead_id)` across `lead_form_submitted` and `lead_booking_made`, and reports bookings as a stage. Google Ads gets one primary for the form and the booking goes to the secondary or offline stage action, as the earlier dossier's rule 16 already says. (repo)
- A booking with no prior form (calendar-first path) is a new lead: no `lead_id` in storage, so the booking handler mints one and sends it to GHL in the inbound webhook. The earlier dossier flagged calendar-first paths as where gclids get lost; the same listener must read gclid from storage, not the URL. (b) #29

### 5. Attribution join: first touch to GHL to Google Ads

- posthog-js registers 24 campaign keys including `gclid`, `gad_source`, `gbraid`, `wbraid`, `gclsrc`, `fbclid`, `msclkid`, `ttclid`, `dclid`, and stores first-touch values in a cookie so `$initial_utm_source`, `$initial_gclid`, `$initial_gbraid` survive the anonymous-to-identified transition; session-level `$entry_gclid` and `$entry_gad_source` exist too. `custom_campaign_params` (default `[]`) adds anything else, for example `variant`. (a for utm and entry, snippet only for the 24-key list) #3 #7 #14
- Initial properties are backfilled only when the user is identified, so the hidden-field copy the form posts to the server is the reliable one for leads; PostHog's `$initial_*` is the audit copy. (a) #3
- Google's identifier windows: gclid uploads accepted up to 90 days from click; hashed PII (enhanced conversions for leads) up to 63 days; a fresh click may reject with "still processing, re-upload in 12 hours". (a) #33
- Match rates: no Google page states one. The only numbers found are vendor claims without a sample ("75-85% typical", "gclid near 100%", "dual identifiers +10-25% median") and should be reported as a range to verify from the account's own diagnostics, not as fact. (c) #34
- PostHog's Google Ads destination can send conversions straight from the event stream: OAuth-linked account, 10-digit customer id in `XXX-XXX-XXXX` form, conversion action created first, events filtered to those with `gclid`, person data read as of processing time so identify before capture, 6 to 48 h before Google shows them, and new actions need about 6 h before accepting data. Marked experimental. It is a shortcut for `lead_call_qualified` and `lead_booking_made` when the site owner has no Data Manager pipeline. (a) #11
- Cross-subdomain: `cross_subdomain_cookie` is true by default, so a landing page on `go.example.com` and the booking page on `example.com` share the person; a GHL-hosted page on a different registrable domain does not, which is why `ph_distinct_id` travels in the form payload and calendar URL. (a) #7

### 6. Verification with Playwright and the query API

- Assertion path A, network: `page.waitForRequest(r => r.url().includes('/i/v0/e/') || r.url().includes('/batch/'))` around the action, then `request.postDataJSON()`; posthog-js compresses bodies by default, so either init the test page with `disable_compression: true` via a query flag or gunzip in the test. The compression default is carried-forward knowledge, not from an opened page. (a for Playwright API, c for compression) #35
- Assertion path B, ingestion: POST `/api/projects/:id/query/` with a HogQL query filtered on the test `distinct_id` and `properties.test_lead = true`, `refresh: "blocking"`, Bearer personal key with Query Read; expect exactly one row per event name. Limits 240/min, 2400/h, 3 concurrent, 10 s execution. PostHog does not publish an ingestion latency on the pages opened; poll every 5 s up to 60 s before failing. (a for API, inferred for latency) #5
- The legacy `/api/projects/:id/events/` list endpoint could not be opened; use the query endpoint. (unconfirmed) 
- Tel: assertion: Playwright cannot follow a `tel:` navigation, so intercept with `page.route('tel:*', r => r.abort())` is not possible either (scheme not routable); instead click and assert the beacon request was issued with `send_instantly`. Because the SDK also flushes on unload, a test that finds two requests for one click is a bug in the handler, not the SDK. (b) #8 #35
- Test leads: every test run sets `localStorage.ph_test_lead = 1` before load; the page reads it and adds `test_lead: true` to every event and to the GHL payload; the server tags the GHL contact `test-lead` and the call vendor call as `not_a_lead`. /analytics excludes `test_lead = true` in every HogQL query, and PostHog's project setting for internal and test users can hold the same filter (setting not opened, carried forward). (repo, c for the setting)
- Double-count assertion: after a form submit, press back and reload the thank-you URL; the count for `lead_form_submitted` with that `lead_id` must stay at one. (repo)

### 7. Consent and law for a form that triggers automated texts or calls

- Definition, 47 CFR 64.1200(f)(9): "an agreement, in writing, bearing the signature of the person called that clearly authorizes the seller to deliver or cause to be delivered to the person called advertisements or telemarketing messages using an automatic telephone dialing system or an artificial or prerecorded voice", with a clear and conspicuous disclosure that (A) the person authorises such calls and (B) the person "is not required to sign the agreement... as a condition of purchasing any property, goods, or services"; (f)(9)(ii) accepts an electronic or digital signature under E-SIGN or state law. (a) #36
- One-to-one: the FCC's 2023 rule (one identified seller per consent, "logically and topically related") was vacated by the Eleventh Circuit in IMC v. FCC on 24 January 2025 before it took effect; the FCC removed the text on 14 July 2025 and finalised the 2012 wording in September 2025. Result: one consent can name several sellers, but the seller still has to be named. (a) #37 #40 #41
- Revocation, (a)(10): from 11 April 2025 a consumer may revoke "by using any reasonable method"; the words stop, quit, end, revoke, opt out, cancel, unsubscribe by text are reasonable per se; honour within ten business days; one clarification message allowed within five minutes with no marketing. The "revoke all" clause (a revocation to one message type covers unrelated messages from the same caller) was waived to 11 April 2026, then to 31 January 2027, and on 9 September 2026 the FCC circulated a Report and Order narrowing it to category scope for informational messages only, while "a single revocation still revokes consent or permission for all future telemarketing from that caller"; effective 30 days after Federal Register publication. For a lead-gen form, which is telemarketing, one STOP kills all marketing texts and calls. (a) #36 #38 #39 #42 #43
- Quiet hours, (c)(1): no telephone solicitation before 8 am or after 9 pm local time at the called party's location. Speed-to-lead automations that text at 9:30 pm in the lead's time zone need a schedule gate; several states are narrower (not researched here). (a) #36
- McLaughlin Chiropractic v. McKesson (20 June 2025): district courts no longer defer to FCC TCPA interpretations, so FCC waivers reduce but do not remove litigation exposure. (a) #40
- Practitioner checklist for the consent block: above the button, contrasting text, names the seller, says calls and texts, says autodialer and prerecorded or artificial voice, says not a condition of purchase, says how to opt out, unchecked checkbox, button copy that reads as agreement; keep timestamp, IP, page URL, exact consent text, a form snapshot and the channel. (c) #44
- Cookies and replay in the UK and EEA: any storage or access on the device that is not strictly necessary needs prior consent to the UK GDPR standard; "helpful or convenient but not essential" does not qualify, so analytics cookies and session replay are opt-in. PostHog's `cookieless_mode: 'on_reject'` captures nothing until the banner answers and counts refusers by a server-side hash; `opt_out_capturing()` stops replay as well as events. EU cloud is Frankfurt with IP capture off by default. (a) #45 #13 #12
- California: CIPA 631 (contents) and 638.51 (pen register); Javier v. Assurance IQ held replay recorded before consent violated CIPA; $5,000 per violation; SB 690 as narrowed only removes the private right of action for 638.51 web claims and was not yet law in August 2026; 631 exposure for replay stays. Practical rule: do not start replay for California visitors until an affirmative click, which in practice means gate replay behind consent everywhere rather than geofence. (a for statute and case as reported, b for the advice) #46 #47

### 8. Spam and junk leads

- Junk share on lead forms observed by one practitioner: 20 to 40 percent of submissions; honeypot caught 8 of 14 junk in one reviewed batch. Honeypot build: positioned off-screen (not `display:none`, which many bots skip), `tabindex="-1"`, `autocomplete="off"`, and a silent 200 so the bot operator learns nothing. (c) #49
- CAPTCHA cost to conversion: WPForms cites Moz at "around 3% of total conversions"; the search summary cited an A/B on three client forms at 8 to 18 percent for v2 challenges and a WPForms figure of 4.7 percent on mobile, neither of which was found on an opened page. Use 3 percent as the only sourced figure and label the rest unverified. (c) #53
- Vendor facts: reCAPTCHA free to 10,000 assessments a month per organisation, $8 flat for 10,001 to 100,000, $1 per 1,000 above; Turnstile free with unlimited verifications, 20 widgets, 10 hostnames each, token 300 s and single use, must be verified server-side at `/turnstile/v0/siteverify` or the widget "does not protect your forms"; hCaptcha free to 1,000 verifications a month then $99 per the comparison article. Script weight 110 KB v3, 60 KB Turnstile, 80 KB hCaptcha. (a for Google and Cloudflare, c for hCaptcha and weights) #50 #51 #52 #48
- Recommended stack for a local service lead form: honeypot plus time-to-submit floor plus Turnstile invisible plus server-side phone validation (E.164 parse, reject premium and toll-free, optionally line type via a lookup API) plus per-IP rate limit. reCAPTCHA v3 at 0.7 only where junk survives that. (b) #48 #49
- Excluding spam from counts: the server decides `spam: true|false` before it fires anything. Spam gets no PostHog lead event at all (an optional `lead_form_rejected` with `reason`), no GHL contact, and no Google conversion. Vendors already mark calls: WhatConverts sends `spam` and `duplicate`; CallRail fires call-modified when a call is marked spam and `lead_status: not_a_lead` on scoring; the receiver must retract or never emit `lead_call_qualified` for those. (a for vendor fields) #17 #15
- Phone field friction: the only sourced number is WPForms quoting Small Farm Design, mandatory phone 39 percent abandonment vs 4 percent optional, no sample. A call-first business still needs the phone, so keep it required and note the trade. (c) #53

---

## Exact API facts (verified)

### PostHog capture, single event (confirmed #1 #4 #6 #9)

```json
POST https://us.i.posthog.com/i/v0/e/
Content-Type: application/json
{
  "api_key": "phc_xxx",
  "event": "lead_call_qualified",
  "distinct_id": "0192f3a1-...-anon-or-hash",
  "uuid": "5f8c1b2e-...-uuidv5(provider:call_id)",
  "timestamp": "2026-09-23T14:02:11Z",
  "properties": {
    "$session_id": "0192f3a1-7c2e-7b3a-9f1e-3c4d5e6f7a8b",
    "lead_id": "ld_01J8...",
    "provider": "callrail",
    "call_id": "CAL8154748ae6bd4e278a7cddd38a662f4f",
    "duration_seconds": 94,
    "threshold_seconds": 30,
    "answered": true,
    "first_call": true,
    "gclid": "CjwKCAjw...",
    "variant": "b",
    "test_lead": false,
    "$set_once": { "first_gclid": "CjwKCAjw...", "first_variant": "b" },
    "$set": { "crm_contact_id": "9NkT25Vor1v4aQatFsv2" }
  }
}
```

- Confirmed: endpoint, `api_key`, `event`, `distinct_id` required, `timestamp` ISO 8601, `$session_id` must be UUIDv7, `$set` and `$set_once` inside `properties`, `uuid` recommended for dedupe, batch at `/batch/` under 20 MB, EU host `eu.i.posthog.com` (the EU host name is inferred from the EU cloud docs, the capture page says "EU/self-hosted variants").
- Not confirmed: HTTP status codes; the capture page does not list them and says bad events still return 200.

### PostHog query (confirmed #5)

```json
POST https://us.posthog.com/api/projects/{project_id}/query/
Authorization: Bearer phx_personal_key_with_query_read
{
  "query": {
    "kind": "HogQLQuery",
    "query": "SELECT event, count(), uniq(properties.lead_id) FROM events WHERE distinct_id = {did} AND timestamp > now() - INTERVAL 10 MINUTE AND properties.test_lead = true GROUP BY event"
  },
  "refresh": "blocking",
  "name": "check_tracking_one_per_action"
}
```

- Response `{ "results": [...], "is_cached": bool, "timings": {...} }`; async variants return `query_status`. Limits 2400/h, 240/min, 3 concurrent, 10 s. No OFFSET; use keyset on timestamp. Placeholder syntax `{did}` with a `values` map is carried forward, not from the opened page.

### CallRail post-call webhook (confirmed #15)

- Trigger: after recording and transcription attach, at most 20 minutes after hangup; body is the call object.
- Fields used: `id`, `answered`, `duration` (seconds, string in the signature sample, integer in list responses), `call_type` (`abandoned`, `answered`, `in_progress`, `missed`, `outbound`, `voicemail`, `voicemail_transcription`), `first_call`, `prior_calls`, `total_calls`, `lead_status`, `customer_phone_number` (E.164), `tracking_phone_number`, `source_name`, `source`, `medium`, `campaign`, `keywords`, `gclid`, `fbclid`, `landing_page_url`, `last_requested_url`, `utm_source`, `utm_term`, `person_id`, `milestones.first_touch`, `milestones.last_touch`, `tags`, `note`, `value`, `recording`, `recording_duration`, `start_time`, `company_id`, `device_type`.
- Security: header `Signature` = Base64(HMAC-SHA1(signing_key, raw_body)).
- Call-modified adds `changes: ["note" | "tags" | "value" | "transcription_text" | "call_summary" | "recording_duration" | "auto_score" | "manual_score"]` and fires on spam marking.
- Pre-call and Call Routing Complete payload fields were not in the extracted section; treat as unconfirmed.

### WhatConverts phone call webhook (confirmed #17)

- Trigger: lead created; `trigger: "new"`; modified and in-progress variants exist.
- Fields: `lead_id`, `lead_type`, `lead_status` (`Unique` or `Repeat`), `lead_state`, `lead_score`, `quotable`, `quote_value`, `sales_value`, `call_status`, `answer_status`, `call_duration_seconds`, `caller_number`, `tracking_number`, `destination_number`, `line_type`, `phone_name`, `landing_url`, `lead_url`, `lead_source`, `lead_medium`, `lead_campaign`, `lead_content`, `lead_keyword`, `gclid`, `msclkid`, `google_analytics_client_id`, `facebook_click_id`, `ip_address`, `device_type`, `spam`, `duplicate`, `recording`, `call_transcription`, `additional_fields`.
- Signature: not on the opened page.

### Twilio status callback (confirmed #21)

- Form-encoded POST with `CallSid`, `AccountSid`, `CallStatus`, `CallDuration` (seconds, terminal events only), `Duration` (minutes), `From`, `To`, `Direction`, `ForwardedFrom`, `AnsweredBy`, `Timestamp` (RFC 2822 UTC), `CallbackSource`, `SequenceNumber`; `StatusCallbackEvent` values `initiated`, `ringing`, `answered`, `completed`; verify `X-Twilio-Signature`.

### CTM webhook (not confirmed)

- Plan gate (Marketing Pro and up) and trigger concept confirmed; payload field names not opened. Do not hard-code CTM fields in check_tracking.py; read them from a fixture the owner pastes.

### GoHighLevel shapes

- Inbound (confirmed #24): any flat JSON; email or phone mandatory to create a contact; keys without spaces; referenced later as workflow custom values.
- Outbound workflow webhook (confirmed #23): contact block (`full_name`, `first_name`, `last_name`, `email`, `phone`, `address1`, `city`, `state`, `country`, `postal_code`, `tags`, `contact_source`, `contact_type`, `gclid`, `date_created`, `timezone`, all custom fields) plus `location{id,name,...}` plus, on appointment triggers, `calendar{id, calendarName, title, appointmentId, startTime, endTime, status, selectedTimezone, notes}`; on pipeline triggers `opportunity_name`, `status`, `lead_value`, `pipeline_stage`, `pipeline_id`, `pipeline_name`; plus your custom key-values. Exact key casing inside `calendar` is as the help page lists; treat as confirmed for names, inferred for nesting depth.
- Marketplace `AppointmentCreate` (confirmed #27):

```json
{
  "type": "AppointmentCreate",
  "locationId": "0007BWpSzSwfiuSl0tR2",
  "appointment": {
    "id": "0007BWpSzSwfiuSl0tR2",
    "calendarId": "BqTwX8QFwXzpegMve9EQ",
    "contactId": "9NkT25Vor1v4aQatFsv2",
    "appointmentStatus": "confirmed",
    "source": "booking_widget",
    "startTime": "2023-09-25T16:00:00+05:30",
    "endTime": "2023-09-25T16:00:00+05:30",
    "dateAdded": "2023-09-25T16:00:00+05:30"
  }
}
```

- GHL iframe postMessage (practitioner, #28): booking complete is `event.data[0] === 'msgsndr-booking-complete'`; form submit is an array message whose `event.data[2]` is JSON containing `full_name`, `email`, `customer_id`, `full_address`. Origin list not documented; allow-list the GHL widget host you embed.

### Calendly

- Embed events (confirmed #30): `calendly.profile_page_viewed`, `calendly.event_type_viewed`, `calendly.date_and_time_selected`, `calendly.event_scheduled`; `e.data.event`, `e.data.payload`; guard `e.origin === "https://calendly.com" && e.data.event?.startsWith("calendly.")`.
- Webhook (confirmed #31, payload keys from #32): events `invitee.created`, `invitee.canceled`, `routing_form_submission.created`; payload `uri`, `email`, `name`, `status`, `timezone`, `event`, `tracking.utm_source|utm_medium|utm_campaign|utm_content|utm_term|salesforce_uuid`, `questions_and_answers[]`, `cancel_url`, `reschedule_url`, `rescheduled`, `old_invitee`, `new_invitee`, `text_reminder_number`, `created_at`, `updated_at`. Signature header name and HMAC scheme not opened.

---

## The event dictionary

- `lead_form_submitted` - client, fired once in the 2xx success callback; props `lead_id`, `form_id`, `variant`, `gclid`, `gbraid`, `wbraid`, `utm_source`, `utm_medium`, `utm_campaign`, `utm_term`, `utm_content`, `landing_page`, `test_lead`, `$set_once{first_variant, first_gclid, first_landing_page, lead_first_channel:"form"}`.
- `lead_form_rejected` - server, optional, one per rejected POST; props `reason` (`honeypot`, `turnstile`, `phone_invalid`, `rate_limit`, `duplicate`), `form_id`, `variant`, `test_lead`. Never counted as a lead.
- `lead_phone_click` - client, on tel: anchor click with `{transport:"sendBeacon", send_instantly:true}`; props `number_shown`, `is_tracking_number`, `placement` (`header`, `sticky`, `hero`), `variant`, `test_lead`. Intent, not lead.
- `lead_sms_click` - client, on sms: anchor click, same options and props as phone click. Intent, not lead.
- `lead_call_qualified` - server, from vendor post-call webhook when `duration_seconds >= threshold_seconds` and `answered = true` and not spam; props `lead_id`, `provider`, `call_id`, `duration_seconds`, `threshold_seconds`, `answered`, `first_call`, `caller_hash`, `tracking_number`, `source`, `gclid`, `variant`, `test_lead`, `$session_id` when known, `$set_once{lead_first_channel:"call"}`; `uuid` = UUIDv5(provider, call_id).
- `lead_call_short` - server, same source, below threshold or unanswered; props as above. Reported, never counted.
- `lead_booking_made` - client from postMessage or server from GHL/Calendly webhook, whichever arrives first, never both (server dedupes on `appointment_id`); props `lead_id`, `appointment_id`, `calendar_id`, `provider` (`ghl`, `calendly`), `after_form` (true when a `lead_id` already existed), `variant`, `gclid`, `test_lead`, `$set_once{lead_first_channel:"booking"}` only when `after_form` is false.
- `crm_contact_upserted` - server, from GHL outbound webhook on contact create/update; props `crm_contact_id`, `created` (bool), `tags`, `lead_id`, `variant`; `$set{crm_contact_id}`. Reconciliation only.
- `crm_stage_changed` - server, from GHL pipeline trigger; props `crm_contact_id`, `pipeline_stage`, `lead_value`, `lead_id`. Feeds offline import, not lead count.
- `thank_you_viewed` - client pageview of the thank-you URL; props `lead_id` if present, `has_lead_event` (true when `lead_form_submitted` already fired in this session). Fallback and diagnostic only; a `thank_you_viewed` with `has_lead_event=false` and no `lead_id` is a finding.
- Person properties: `$set_once` `first_variant`, `first_gclid`, `first_gbraid`, `first_wbraid`, `first_utm_source`, `first_utm_campaign`, `first_landing_page`, `lead_first_channel`, `consent_first_at`; `$set` `crm_contact_id`, `last_lead_at`, `test_lead`.
- Lead count for /analytics: `uniq(properties.lead_id)` over `lead_form_submitted`, `lead_call_qualified`, `lead_booking_made` where `properties.test_lead = false`; by variant via `properties.variant`. Intent metrics are `lead_phone_click` and `lead_sms_click` uniques per session.

---

## The consent line

```text
[ ] By checking this box and clicking "Get my free quote", I agree that {Business legal name} may call and text me at the number I entered about my request and related offers, including using an automatic telephone dialing system, prerecorded or artificial voice, and AI-generated messages. Consent is not a condition of purchase. Message frequency varies. Message and data rates may apply. Reply STOP to cancel or HELP for help at any time. See our Privacy Policy and Terms.
```

- Written agreement with a signature: unchecked checkbox plus a button whose label the sentence names, valid as an electronic signature under (f)(9)(ii) and E-SIGN. (a) #36
- Clearly authorises the seller to deliver telemarketing using an ATDS or artificial or prerecorded voice: "automatic telephone dialing system, prerecorded or artificial voice" appears verbatim; "AI-generated messages" covers the FCC's 2024 position that AI voices are artificial voices (carried forward, not from an opened page). (a) #36
- Not required as a condition of purchase: "Consent is not a condition of purchase". (a) #36
- Names the seller: `{Business legal name}`; add "and its service partners listed at {url}" only if others will call, since one-to-one is gone but the seller must still be identified. (a) #37 #41
- Revocation: "Reply STOP to cancel" matches the per-se reasonable keyword list; the backend must also accept any reasonable method and stop within ten business days. (a) #36 #38
- Carrier and CTIA boilerplate ("Message frequency varies", "Message and data rates may apply", "HELP") is industry practice, not TCPA text. (c) #44
- Placement: directly above the submit button, same font size as the labels, not collapsed, not in a tooltip. (c) #44
- Record kept per lead: `consent_text_version` (hash of the exact string shown), `consent_timestamp` (UTC), `consent_ip`, `consent_user_agent`, `page_url`, `form_id`, `variant`, `checkbox_checked: true`, `ph_distinct_id`, `ph_session_id` (links to the replay if consent to replay was also given), plus the rendered form HTML snapshot or a screenshot hash. Stored in the lead record and mirrored to GHL custom fields. (c) #44
- Quiet hours: outbound automation checks the lead's local time from area code or address and holds anything outside 8 am to 9 pm. (a) #36

---

## Rules for tracking

1. One event name per real-world act; tel: and sms: taps are intent events and never enter the lead count. (repo)
2. `lead_form_submitted` fires only in the success callback after a 2xx; never on click, submit, or page load. (a) #1 #28
3. The server mints `lead_id` before responding, the client puts it on the event, and every count is `uniq(lead_id)`. (a) #5
4. Thank-you page is a fallback and a diagnostic; it never fires the lead event when one already fired in the session. (repo)
5. Every server-side event carries a deterministic `uuid`; PostHog's dedupe is a net, not a design. (a) #9 #10
6. Server events carry the browser's `distinct_id` from the hidden field when it exists, else a salted hash of the E.164 phone; never a raw phone or email. (a) #2
7. Pass `$session_id` (UUIDv7) on server events when the vendor captured it so the replay shows the call; expect it stale after 30 idle minutes or 24 h. (a) #4
8. Identify at submit time or run `person_profiles: 'always'`, or `$set_once` on anonymous events does nothing. (a) #6
9. Call `posthog.reset()` after the thank-you so a second lead from the same device is a second person. (a) #2
10. Qualified call = answered and `duration_seconds >= threshold_seconds`, threshold read from config and asserted equal in Google Ads, the vendor filter and the event. (repo, Google Ads dossier rule 11)
11. Vendor webhooks arrive late and out of order; upsert by provider call id, emit `lead_call_qualified` once, and retract nothing in PostHog (write a `lead_call_reclassified` if spam is marked later). (a) #15 #17
12. Verify vendor signatures: CallRail HMAC-SHA1 `Signature`, Twilio `X-Twilio-Signature`; WhatConverts and GHL unverified, so give them secret-bearing URLs. (a) #15 #21
13. CallRail `grab_cookies` carries the PostHog cookie into the call record; that join is preferred over gclid matching. (a for feature, inferred for join) #15
14. GHL dedupe is Allow Duplicate Contact off, primary Phone, secondary Email, and the check reads the setting back. (a) #26
15. GHL inbound payload always has phone or email, `lead_id`, `variant`, `source`, click ids, utm_*, `ph_distinct_id`, `ph_session_id`, consent fields and `test_lead`, each mapped to a custom field with an exact-case query key. (a) #24 #29
16. Bookings on the thank-you page carry the form's `lead_id` and `after_form: true`; they advance a lead, they never add one. (repo)
17. Calendar-first bookings mint a `lead_id`, read gclid from storage not the URL, and post to GHL like a form. (b) #29
18. Click ids and utm_* are copied to a hidden field and browser storage on first touch and sent to GHL; PostHog `$initial_*` is the audit copy, not the primary. (a) #3
19. Offline import happens within 90 days of click for gclid and 63 for hashed PII, from the stage GHL says is qualified, keyed on `lead_id`; match rate is reported from the account, never assumed. (a) #33
20. Every check run flags itself `test_lead: true` in PostHog, `test-lead` tag in GHL, `not_a_lead` at the vendor, and every /analytics query excludes it. (repo)
21. check_tracking.py asserts exactly one row per event name for the test distinct_id via HogQL within 60 s, then back-navigates to the thank-you and asserts the count did not move. (a) #5 #35
22. Spam never reaches PostHog as a lead: honeypot, time floor, Turnstile verified server-side, E.164 parse and rate limit run first; rejected posts may log `lead_form_rejected` with a reason. (a) #51 #49
23. The consent checkbox is unchecked by default, the copy sits above the button, and the record stores timestamp, IP, page URL, text version, distinct_id and session_id. (a) #36 (c) #44
24. One STOP ends all marketing texts and calls from the business; honour within ten business days; automated outreach holds between 9 pm and 8 am in the lead's local time. (a) #36 #38 #43
25. Session replay and non-essential cookies load only after an affirmative opt-in for every visitor; use `cookieless_mode: 'on_reject'` so the lead count survives a refusal. (a) #45 #13 #46
26. Any lead path that depends on a field this dossier could not confirm (CTM payload, Calendly signature, CallRail pre-call body) is built from a pasted fixture and marked unverified in the report. (repo)
