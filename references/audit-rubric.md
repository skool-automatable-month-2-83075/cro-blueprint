# The landing page rubric - 100 points, a grade out of 10
Generated from code/audit/rubric.py · never edit by hand, run `python3 -m audit.rubric --write-reference`
Next: read the audit.md the command wrote; every line below is one row in it.

MACHINE is scored by code. JUDGED is scored by Claude from the screenshots, contact sheets and transcripts (0, 1 or 2). BUSINESS applies by the model in context/business.md; items that do not apply leave the denominator.
Grade: 90 or more is a 10-out-of-10 candidate, and only when no Proof, Conversion path or Tracking item fails.

## Message and offer · 15 points

### M1. Headline names the service and the place · 4 points · JUDGED
- Measure: H1 carries what they searched and where, with continuity of meaning, not a keyword string. The keyword and the city STAY - that is the message match the ad is paying for
- Fix: Rewrite the H1 as proof word + city + service, in the buyer's words. Keep the keyword and the city whatever else changes

### M2. The offer above the fold · 5 points · JUDGED
- Measure: An 'X in Y or Z' promise sits above the fold. On an ad page it belongs in the SUBHEADLINE, because the H1 has to carry the keyword and the city for Quality Score
- Fix: Write the offer into the line under the headline: what they get, by when, or what you do if you miss. Leave the H1 to the keyword and the city

### M3. H1 plus subhead is the whole pitch · 3 points · JUDGED
- Measure: Reading only those two lines, a stranger knows what you do, for whom, and why to call
- Fix: Cut the subhead to the offer plus one proof number

### M6. A guarantee, stated in words anyone can hold you to · 3 points · JUDGED
- Measure: The page says what happens if it does not work - money back, a redo, you stop paying, we keep going free. Named, specific, and easy to find
- Fix: Write the one you would actually honour and put it beside the button: 'if you are not happy with the work, we refund the deposit'. Vague confidence is not a guarantee

### M4. One promise, not three · 2 points · JUDGED
- Measure: The fold makes one promise; competing promises or slogans are absent
- Fix: Keep the promise the ad made, move the rest below the proof

### M5. H1 exists, short, in the first screen · 1 points · MACHINE
- Measure: An H1 of 4 to 14 words whose top is inside the phone's first screen. Shorter is better, but never at the cost of the keyword or the city
- Fix: Add a real H1 above the fold. Tighten the words around the keyword and the city, never remove them

## Proof · 25 points

### P1. Founder video in the first two screens · 2 points · MACHINE
- Measure: A video or provider embed within the first two phone screens
- Fix: Record 30 to 60 seconds, face to camera, why you started and the promise. Self-host it, and make the still behind the play button you, smiling, looking at the camera - never a stock photo standing in

### P2. The founder video says why and the promise · 2 points · JUDGED
- Measure: Its transcript names the person, why they do this, and the promise the page makes
- Fix: Re-record to the script: who you are, why, the promise, one line on what happens after they call

### P3. Video testimonials, three or more, click to play · 3 points · MACHINE
- Measure: At least three videos beyond the founder's, self-hosted, poster, no autoplay
- Fix: Ask three happy clients for a phone video; self-host with posters

### P4. Testimonial transcripts name a real outcome · 2 points · JUDGED
- Measure: Each transcript names the job, the result and something specific, not 'great service'
- Fix: Prompt clients: what was broken, what happened, what changed - in that order

### P5. Written testimonials, five or more, with names · 2 points · MACHINE
- Measure: Five or more review blocks with a first name
- Fix: Pull the real reviews from the profile with names and dates

### P6. Written testimonials are specific · 1 points · JUDGED
- Measure: They name staff, jobs, numbers, dates; nothing reads generic or invented
- Fix: Swap generic quotes for ones that name the job and the result

### P7. Real photos, no stock, no generated faces · 2 points · MACHINE
- Measure: No image from a stock or avatar host, no upscaled or generated-looking file beside a real name
- Fix: Replace every flagged image with a real photo of the team, the work, the client

### P8. The photos show this business · 1 points · JUDGED
- Measure: From the contact sheets: the images show this team, this work, this place - not lifestyle stock
- Fix: Shoot the van, the crew, the finished job; nothing else

### P9. A real review score with its count · 3 points · MACHINE
- Measure: A star average with the number of reviews it comes from, in the first screen. On an ad page it is NOT linked out: the only ways off the page are the call, the form, or leaving
- Fix: Show the real score and the count it comes from - '4.9 from 214 Google reviews' - with the platform named so it can be checked. No link away from the page

### P10. Proof badges showing the stars and the count · 1 points · MACHINE
- Measure: The platform's mark with the stars drawn and the number of reviews beside it - not a bare logo
- Fix: Show the badge as people expect to see it: the platform mark, the stars filled in, the score and how many reviews it comes from

### P11. Licence, insurance and bond with the number · 2 points · BUSINESS · trade, professional only
- Measure: For a trade or professional: licence or insurance named with a number in the hero
- Fix: Put 'Licensed #XXXXX, insured to $Xm' in the hero tick strip

### P12. Real work on show - portfolio or case studies, whichever this buyer judges on · 2 points · BUSINESS · trade, professional, agency, saas only
- Measure: A business judged by looking (photography, events, trades, renovation, landscaping) shows real finished work as photos or video; a business judged on outcomes shows case studies with numbers. Either way it has to be work the owner is proud of - if they would not want it seen, it will not sell
- Fix: Show the work: photos or video of real finished jobs, or two case studies with a number and a timeframe. Nothing you would not want a client to see

### P13. Every number on the page has a source · 2 points · MACHINE
- Measure: Every figure on the page appears in context/proof.md (our pages) - or is flagged for the owner to source
- Fix: Source it in proof.md or take it off

### P14. A lead magnet beside the form, framed as an extra · 1 points · MACHINE
- Measure: Something they keep named near the form - an audit, a checklist, a calculator - with a picture of it, and framed as an add-on rather than the reason to enquire
- Fix: Put it to the left of the form with a picture of it. Say what they are really getting - help with the job - and that the audit arrives on the way. Never sell the magnet as the offer

## Conversion path · 20 points

### C1. A CTA above the fold on every viewport · 3 points · MACHINE
- Measure: At least one call or form CTA visible in the first screen on mobile, tablet and desktop
- Fix: Put the call button and the form button in the hero, above the fold, on every screen size

### C2. A CTA on every section on desktop · 2 points · MACHINE
- Measure: On desktop, most sections with real copy carry a CTA, or four or more CTAs total
- Fix: Add a CTA band after each proof block; every one scrolls to the form

### C3. One fixed bottom bar on mobile with call and form · 3 points · MACHINE
- Measure: Exactly one fixed bar at the bottom on mobile with a tel: link and a form button; none on desktop
- Fix: Add the mobile bar; remove any second sticky element

### C4. Every CTA dials or scrolls to the form · 1 points · MACHINE
- Measure: No CTA leads to another page
- Fix: Point every button at #lead-form or tel:

### C5. The form asks the four - first name, last name, email, phone - and little else · 3 points · MACHINE
- Measure: First name, last name, email and phone all asked (half the points), 3 to 6 fields, no select, no textarea, qualifying questions as chips
- Fix: Ask all four - first name, last name, email, phone - then at most one qualifying question as chips

### C6. Form hygiene - labels, autofill, required, phone reason, consent, honeypot, privacy · 3 points · MACHINE
- Measure: Seven checks: real labels, autocomplete tokens, required marking, the line under the phone field, the consent line with 'not a condition' and STOP, a honeypot, a privacy link
- Fix: Fix each missing check; the template form has all seven

### C7. Nothing they must look up · 1 points · MACHINE
- Measure: No ZIP, postcode or account fields
- Fix: Remove the ZIP field; ask for the city in the call

### C8. The button says the outcome · 1 points · MACHINE
- Measure: Button text is an outcome, never 'Submit'
- Fix: Change it to 'Get my free quote' or the real outcome

### C9. The thank-you page does its job · 2 points · MACHINE
- Measure: /thank-you exists, noindex, no nav, a tel link, a callback time, the calendar where the model books
- Fix: Build the thank-you page from the template; put the calendar there, not on the landing page

### C10. Three exits only · 1 points · MACHINE
- Measure: No link leaves the page except privacy and terms; every other link is a leak, named in the report
- Fix: Remove the nav, the footer links and every outbound link; keep one legal line

## Tracking · 10 points

### T1. One phone number · 2 points · MACHINE
- Measure: Every tel: link carries the same digits
- Fix: One number everywhere; Google's snippet or a tracking number swaps it

### T2. Calls are tracked · 2 points · MACHINE
- Measure: Google's phone snippet or a call-tracking script (CallRail, CTM, WhatConverts, Invoca) is on the page
- Fix: Install the Google phone snippet or a call-tracking number with dynamic insertion

### T3. Taps and fields are measurable · 1 points · MACHINE
- Measure: An analytics or replay tool is present so tel taps and form fields can be counted
- Fix: Add PostHog (this repo wires it) so every tap and field is measured

### T4. A conversion fires once on the lead · 2 points · MACHINE
- Measure: A conversion script is present; on our pages check_tracking.py proves it fires exactly once
- Fix: Fire the lead event on the form's success, never on load; verify with check_tracking.py

### T5. Click ids and UTMs survive to the form · 2 points · MACHINE
- Measure: After ?gclid=test the id is in a hidden field or storage, and UTMs with it
- Fix: Capture gclid and utm_* on first touch and ride them on the form as hidden fields

### T6. Replay and heat maps are on · 1 points · MACHINE
- Measure: PostHog, Clarity or Hotjar present
- Fix: Turn on PostHog replay and heat maps (step 0 of /analytics)

## Copy · 10 points

### W1. Word count fits the buyer · 2 points · MACHINE
- Measure: Under 600 words for a trade or local service, under 900 for an outcome service
- Fix: Cut to bullets; visitors read a tenth of it

### W2. Bullets over paragraphs · 1 points · MACHINE
- Measure: More list items than paragraphs, or a short page
- Fix: Turn each paragraph into three bullets

### W3. Every line is proof, a result or a benefit · 3 points · JUDGED
- Measure: Section by section, nothing is filler, a feature without its outcome, or repeated
- Fix: Delete the line or finish its chain: feature, benefit, outcome

### W4. The feature-benefit-outcome chain is visible · 1 points · JUDGED
- Measure: The copy runs 'we do X, which gives you Y, meaning Z' at least in the key sections
- Fix: Rewrite the three reasons and the what-you-get bullets as chains

### W5. The FAQ answers why people do not enquire · 1 points · JUDGED
- Measure: FAQ questions are the real objections before the form (price, timing, guarantee, what happens next); nothing after the form
- Fix: Ask the owner what people say when they do not go ahead; those sentences are the FAQ

### W6. No banned phrases · 1 points · MACHINE
- Measure: No 'no spam', 'no obligation', 'no pressure', 'we strive', 'look no further', filler
- Fix: Delete them; reframe positively

### W7. Reads at grade 7 or under · 1 points · MACHINE
- Measure: Flesch-Kincaid grade of the visible copy is 7 or under
- Fix: Shorter sentences, shorter words, one idea a line

## Design and layout · 10 points

### D1. Hierarchy and whitespace · 2 points · JUDGED
- Measure: From the full-page screenshots on each viewport: one clear reading order, air between blocks, nothing cramped
- Fix: Increase section spacing, one heading size per level, cut the boxes

### D2. The first screen does its job · 2 points · JUDGED
- Measure: From the fold screenshots: a stranger sees what this is, why to trust it and what to do next, without scrolling. Five or six things is the ceiling - the styled line above the headline, the headline, the line under it, the buttons, the three ticks, the review score. A seventh is one too many and something has to go. Order is the designer's choice; proof above or below the buttons is taste, not a fault. Judge what is MISSING, unreadable, or one thing too many - never where a working element sits
- Fix: Name the one thing missing from the first screen and put it there. Never prescribe an order that already works. Plain words - never say fold, CTA, message match or Quality Score

### D3. Consistent type and palette · 1 points · MACHINE
- Measure: Two font families or fewer, six text colours or fewer
- Fix: Pick one display and one body font; one accent colour

### D4. Nothing overflows, no tiny text, no tiny taps · 2 points · MACHINE
- Measure: No horizontal scroll on any viewport, under 6 text nodes below 12px on mobile, under 4 tap targets below 44px
- Fix: Fix the overflowing element, raise the small text, enlarge the taps

### D5. Images crisp and light · 1 points · MACHINE
- Measure: No image upscaled past 1.3x, none over 300 KB
- Fix: Export at 2x the rendered width as WebP

### D6. The CTA pattern fits each viewport · 1 points · MACHINE
- Measure: Mobile has the fixed bar and no per-section clutter; desktop has per-section CTAs and no fixed bar
- Fix: Mobile bar plus per-section CTAs on desktop, as the template does

### D7. Looks like a business you would pay · 1 points · JUDGED
- Measure: Overall, 0 to 10 with three specific reasons: would a stranger with three tabs open trust this one
- Fix: Take the three reasons and fix them in order

## Speed and technical · 5 points

### S1. LCP under 2.5 seconds on mobile · 1.5 points · MACHINE
- Measure: Lighthouse mobile LCP 2.5s or under (aim 1.8); 4s is half marks
- Fix: Preload the hero poster, self-host fonts, no video autoplay, compress the hero image

### S2. No layout shift, no blocking · 1 points · MACHINE
- Measure: CLS 0.1 or under and TBT 200ms or under
- Fix: Set width and height on every image and video; defer scripts

### S3. Lighthouse performance 90 or over on mobile · 1 points · MACHINE
- Measure: Performance score 90 or over; 70 is half marks
- Fix: Work the top opportunities in the speed section

### S4. Light third parties, clean head · 0.5 points · MACHINE
- Measure: Under 300 KB of third-party weight, no synchronous script in the head except the Google tag
- Fix: Remove or defer the third-party scripts listed

### S5. Technical hygiene · 1 points · MACHINE
- Measure: Seven checks: noindex on an ad page, no popup, no chat widget, no countdown, no autoplay, a poster on every video, no third-party video iframe
- Fix: Fix each failed check

## Business fit · 5 points

### F1. Nothing on the page is wrong for this business model · 2 points · BUSINESS
- Measure: The layers that read as off for this model are absent (portfolio grid on e-commerce, calendar on a product page, licence line on SaaS, commercial logos on a residential trade)
- Fix: Remove the layer the report names

### F2. The layers this model needs are present · 2 points · BUSINESS
- Measure: The proof form, the conversion action and the price treatment this model needs are on the page
- Fix: Add the layer the report names, from references/cro-by-business-model.md

### F3. The question they will not ask is answered before they scroll · 1 points · JUDGED
- Measure: Against the primary persona (or the model's typical buyer), the first screen answers the question they will not type
- Fix: Put the answer in the subhead or the tick strip

## The business models

### trade · local trade or home service
- Needs: phone_above_fold, licence, rating_count, price_statement, mobile_bar, form
- Wrong: logo_wall_commercial, calendar, chat, cart, trial_cta, security_badges, countdown
- Mobile bar: Call left, Get a quote right
- Word ceiling: 600
- Benchmark: plumbing 7.63%, HVAC 6.56 to 7.48%, electricians 9.08%, roofing 3.70%, cleaning 17.65% (LocaliQ 2026, paid search)
- The full layer lists, per model, are in references/cro-by-business-model.md

### professional · local professional service
- Needs: credentials, rating_count, price_statement, booking_or_call, form
- Wrong: portfolio_grid, cart, trial_cta, security_badges, chat, countdown, logo_wall_commercial
- Mobile bar: Call left, Free case review or Book online right
- Word ceiling: 800
- Benchmark: legal 5.55%, dentists 10.67%, orthodontics 14.21% (LocaliQ 2026); 56% of legal conversions are calls
- The full layer lists, per model, are in references/cro-by-business-model.md

### agency · agency or B2B service
- Needs: case_studies, review_profile_link, price_statement, form, booking_or_form
- Wrong: licence, portfolio_grid, cart, trial_cta, phone_first, textarea, countdown, yelp_bbb
- Mobile bar: Book a call left, See results right
- Word ceiling: 900
- Benchmark: business services 4.85% (LocaliQ 2026), professional services 6.1% (Unbounce, Ruler); 95% of agency conversions are forms
- The full layer lists, per model, are in references/cro-by-business-model.md

### ecommerce · e-commerce or physical product
- Needs: product_images, price, buy_cta, rating_count, shipping_returns
- Wrong: portfolio_grid, case_studies, calendar, lead_form_primary, licence, phone_first, logo_wall_commercial
- Mobile bar: Add to cart with price and variant, one button
- Word ceiling: 700
- Benchmark: e-commerce page action 4.2% (Unbounce); purchase 1.4% average, 3.2% top 20% (Shopify); add-to-cart 4.6% median
- The full layer lists, per model, are in references/cro-by-business-model.md

### saas · SaaS, app, course or community
- Needs: trial_or_demo_cta, product_visual, pricing_or_link, rating_count, logos_or_cases
- Wrong: licence, phone_first, portfolio_grid, yelp_bbb, countdown
- Mobile bar: Start free trial or Book a demo left, See it work right
- Word ceiling: 900
- Benchmark: SaaS 3.8%, online courses 18.3% (Unbounce); education 13.14% (LocaliQ 2026); software 7.6% (Ruler)
- The full layer lists, per model, are in references/cro-by-business-model.md
