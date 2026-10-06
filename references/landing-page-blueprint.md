# How to build a landing page that converts at about 20%
Revised 23 September 2026 · the exact component stack, proven over years of testing and tens of thousands in ad spend, checked against 62 sources in August and 43 more in September (research/research-landing-page-2026.md)
Next: pick the offer. It sits above the fold and it is the highest-leverage element on the page.

The structure is the asset. Don't reinvent it - fill it in. Everything below uses `[bracketed placeholders]` you swap for your own business, niche and numbers, so it works for any service business.

**Read `references/persuasion.md` before you write a word into the placeholders.** The structure below is the skeleton; that file is what goes on it. Four sections carry most of the result here:

- **Message match (section 7) is worth more than any design change on this page.** A documented 212.74% conversion lift
  - and 66% from aligning the headline to the ad alone with no design change. The promise in the ad appears above the fold **in the same words**
    - not a synonym. Every point of mismatch also costs roughly 13-16% more per conversion through Quality Score
- **Reading level (section 5).** Pages at grade 5 to 7 converted at 11.1% against 5.3% for professional-level writing. Difficult words correlated with a 24.3% drop. Write for someone mid-problem
  - on a phone
- **The six fears (section 4).** Every block on this page either kills a specific fear or gets cut. That is the test, not "does it look finished"
- **Substantiation (section 9).** A guarantee in the ad must appear on this page in that wording, and a testimonial with a number in it needs a typical-results line beside it

**The 2026 pattern to know:** CTR rose 7.49% while conversion rates fell in 13 of 14 industries. High CTR with a low conversion rate is now the default, and it is a page problem, not an ad problem. Mobile is 65% of clicks and 47% of conversions, and that gap is almost entirely this page.

Where a line carries a grade, (a) is Google's own documentation or a study of 10,000+ pages or leads, (b) is a named study or documented test with a stated sample, (c) is a practitioner claim or house rule without a controlled test behind it. Ungraded lines are the house ruling and stay as written.

**What 20% means.** The all-industry median landing page converts at 6.6%. Home improvement pages convert at 2.6% at the median and 19.5% at the top quartile; legal pages 4.4% and 25.3% (a, Unbounce 2024, 41,000 pages). A 20% page is a top-quartile page. It needs everything below plus the speed-to-lead wiring, not the copy alone.

## The score

A page is measured by `references/audit-rubric.md` - 100 points across message, proof, conversion path, tracking, copy, design, speed and business fit - run by `python3 code/audit/page_audit.py <url>`. The 18 below are the build spec; the rubric is how the built page is judged.

## Amended 23 September 2026 - what the research pass changed

These override anything below that disagrees. Each one traces to research/research-cro-gaps-2026-09-12.md or research/research-landing-page-2026.md.
- Qualifying questions are tappable chips or radios. Never a dropdown, never an open text box: those two field types are the measured killers; single text fields cost almost nothing.
- Autofill on every field: a real form tag, a label above, correct autocomplete tokens, type=tel, one unsplit phone input. Chrome telemetry: about 75% less abandonment when autofill fires.
- One line under the phone field saying why: "So we can call you back about your quote." People enter fake numbers rather than abandon when it is unexplained.
- Mark required fields, or say "All fields required" once. Validate on blur with a positive tick, never while typing.
- Consent line above the button, unchecked: business named, calls and texts named, "not a condition of purchase", STOP and HELP
  - privacy link. Logged with timestamp, IP and text version. references/tracking-events.md has the wording. Money attached.
- Licence, insurance and bond with the real number, in the hero. It replaces the six-logo wall for residential trades: homeowners rank "licensed and insured" first
  - and there is no controlled evidence for logo walls. Component 5 becomes the licence line; logos stay only for businesses whose clients are brands.
- Never show a rating average without its count. Three reviews at 5.0 reads as mom and two friends; 340 at 5.0 reads as excellent. Do not teach "4.7 beats 5.0" - that is CPG products with high counts.
- Video testimonials: three well-attributed ones plus a linked live rating profile is the default. Nine is a test candidate
  - not a rule; nearly all the lift from proof lands in the first five to ten, and nine videos is real page weight on phones.
- Stack videos because everything is visible at once, not because carousels were proven to fail (the evidence is against auto-forwarding carousels).
- Response time is a Module 4 test candidate, not a rule. No evidence that STATING a response time lifts conversion
  - the research measures actually responding fast. It stays on the page only where the auto-dial actually hits it.
- Never "no spam", "no obligation", "no pressure", "no hidden fees". Measured twice at -18.7% and -24%; the word plants the idea it denies. Positive reframe gained 19.5%.
- "About eight CTAs on desktop" is a default worth testing, not a constant. 74% of viewing time is in the first two screenfuls.
- Message match: continuity of meaning, not word-for-word keyword reuse. "Emergency Plumber Near Me Open Now" reads as machine-written. Teach the practice, never the 144% number.
- Speed, specified: LCP under 2.5s at the 75th percentile of real mobile visits, aim 1.8; INP under 200ms
  - CLS under 0.1 including after a scroll. Replay and testing scripts load after LCP. Under 300 KB of third-party weight before LCP.
- The founder video's poster is the LCP element: real poster at the exact aspect ratio, preloaded with fetchpriority high
  - preload="none", tap to play, never autoplay, never lazy-loaded in the hero. Self-hosted MP4, no YouTube iframe (an exit and a speed hit).
- The two-button mobile bar (call and text) stays, for the right reason: age, not hours. Ages 25-34 text almost as often as they call; 55+ call seven to one. Sticky bars won 29% of 33 mobile tests.
- Something true about price, always: the call-out fee, a typical range, priced example jobs
  - or "free quote". Silence on money is one of the biggest exits. (Jono's ruling: a price is not required; a true statement about money is.)
- Retired numbers, never say them: "half of callers will not phone during work hours" (real figure 10 to 14%), "one second costs 7%" (2008, corrupt PDF)
  - "53% abandon after 3 seconds" (2016, 3G), "every extra field costs conversions", "37% abandon on the phone field" (real: 6% mean), "chatbots convert 3x", "sticky bars +31%".

## Every element does one of three jobs

This is sales copy on a page, not a brochure. An element earns its place by doing one of these:

1. **Social proof** - someone like you already trusted us and was happy
2. **Results and outcomes** - here is the specific thing you get
3. **Benefits, not features** - what it does *for you*, not what it *is*

If a sentence, image or section is not doing one of those three, cut it. Little text. Mostly bullets.

The page has **one job**: get the visitor to call or fill out the form. Everything points there.

## The searcher's city, on the page as well as in the ad

The ad says their city through `{LOCATION(City)}` in the pinned headline. **The page has to agree with it, or the match breaks at the click** - and message match is the highest-lift change available here (a documented 212.74%, and 66% from the headline alone). (Jono, 2 September 2026.)

**How it works, and the one gotcha.** Google's `{loc_physical_ms}` ValueTrack parameter puts a NUMERIC geo criterion id in the URL, never a city name, and **there is no API call that converts one at request time** [F, verified 2 September 2026 - `geo_target_constant` is the only source]. So the map is pulled once and ships with the site.

1. Every ad's final URL carries it: `https://you.com/lp/plumber?loc={loc_physical_ms}`
2. `python3 code/build_geo_map.py` writes `website/lib/geo-map.json` for the country in `context/business.md` - `--country XX` overrides it (about a thousand places, under 30 KB; the repo ships the file empty)
3. The page uses `<City fallback={MAIN_CITY} />` from `components/lp/City.tsx` - `MAIN_CITY` from `.env`

**The fallback is not optional and it is never "your area".** Google cannot resolve a location on a large share of clicks, and the fallback serves every one of them. Write a real place the business actually covers, and read the headline out loud with the fallback in it - that is the version most people see.

**Do not city-swap a claim.** Swapping "Emergency Plumber in Hamilton" is message match. Swapping "Hamilton's #1 rated plumber" onto a page for someone who has never worked in Hamilton is a false claim that happens to be automated.

## The one law: message match

The H1 carries the ad group's service AND the searcher's city (from the `loc` parameter) inside a line that
sells - never a bare echo. Formula: **proof word + city + service**, e.g. "Hire Award-Winning Vancouver Wedding
DJs", "Dallas's Fastest Emergency Drain Cleaning", where the proof word comes from `context/proof.md` (award,
review count, years, speed) and the city is inserted by the City component. Someone who clicked "Emergency
Drain Cleaning Dallas" lands on a headline that says drain cleaning and Dallas and a reason to pick you
(Jono, 12 September 2026). The line under it repeats the ad's offer.

- Matching the ad headline to the H1 alone lifted conversion 66% in one documented test and 212% with 69% lower cost per lead in another; strong match converts 2.5 to 3 times weak match (b)
- It is also the relevance half of Google's landing page experience rating, and above-average experience plus ad relevance is cited as worth about 36% lower cost per click (b, 2023)
- Google now writes ad headlines FROM the page when AI Max text customization is on, so a filler line on the page becomes a filler line in the ad (a, 2025)

**The H1 keeps the keyword and the city. The offer goes in the line under it (Jono, 26 September 2026).** These two rules pull against each other, and this is how they resolve: Google reads the H1 for landing page experience, so the keyword and the city stay there and the clicks stay cheap. The offer, the guarantee and the timeframe go in the subheadline, where there is room for them. Never cut the keyword or the city to make the headline shorter - tighten the words around them instead.

One ad group, one page. That is the whole reason the page exists.

## Why people buy - the nine reasons

Researched 25 September 2026 from 12 sources: Bain and HBR's 30 Elements of Value and the B2B 40, Google and CEB's emotion study, Maslow, Jobs To Be Done, prospect theory, self-determination theory, plus the copy canon (Whitman's LF8, Jim Edwards' ten reasons, Eugene Schwartz, Collier, Hopkins). The full list with its trigger phrases is `code/audit/motivations.py`, and `code/audit/copy_check.py` scores a page against it.

- Make it safe to say yes · the biggest one for a trade. Every review, licence number and guarantee is selling this
- Stop the pain I'm in now · escaping present pain, not preventing a future problem
- Tell me exactly what happens · upfront pricing, what happens after the form, no surprises
- Save me time · same day, within the hour, one visit
- Save me money · flat fee, no hidden fees, cheaper than
- Save me effort · we handle everything, done for you, leave it to us
- Give me my life back · hands off, off your plate, never think about it again
- Make me look good · for a business buyer this is career safety, and it is stronger than it looks
- Make me money · the stated reason a business hires an agency, and irrelevant to a homeowner

What the research changed from the working list: risk reduction and certainty are separate motivations, not part of pain aversion; saving money splits from making money because a homeowner never makes money; legacy and fun found no support for these business models and were dropped.

Which ones matter depends on the business. A trade lives on safety, pain and certainty. An agency lives on money, effort, freedom and looking good. `motivations.py` carries the weight per model, and the audit only asks for the ones that matter.

## The line above the headline names the deepest pain

Jono, 26 September 2026. It is the first thing read and its job is to make them feel the problem before anything is pitched. Not the symptom - the thing underneath it.

- A competitor is taking the calls they should be getting
- Money going out every month with nothing to show
- Another agency that promised and wasted a year
- Tried this twice already and it failed both times
- Everyone else in the trade seems to be doing better

"Tired of a profile that never shows up in the map pack?" is the symptom. "Watching a competitor take the calls you should be getting?" is the pain. Ask the owner what people say on the phone when they are fed up - those words are the line.

## Every section heading is an ad headline

Jono, 26 September 2026. These are the most important lines on the page after the H1, and they are written the way a Google Ads headline is written - the ones with the high click-through rate are the ones saying what people actually want. A heading earns its place by doing one of six things:

- **Promising a result** · "More calls from the map pack in 90 days"
- **Taking the work off them** · "We take care of everything" - nobody wants to piece it together from four suppliers
- **Answering the money worry** · "Prices that suit all budgets" - it reassures the careful buyer and flatters the one who wants premium
- **Making them curious about proof** · "See for yourself why clients love us" - what everyone wants to know is whether other people are happy
- **Borrowing authority** · "Trusted By Some Of The Largest Companies" - who already trusts you does the arguing for you
- **Taking the risk away** · "Get A Quote. No Risk." - names the action and removes the fear of it in four words
- **Asking a question they want answered** · "So Why Northside DJs?" - a question is a hook by construction, it makes you read the answer

A heading does not have to be the boldest claim on the page. Its job is to say what the section is about AND make someone want to read on. Both together is enough.

A heading that does any ONE of these is working. Do not rewrite it for the sake of it.

A claim about how customers feel counts as proof curiosity: "People Really Love Us" is doing the same job as "See for yourself why clients love us". Never reject a heading and then suggest a replacement that says the same thing - if the suggestion would pass, the heading passes. And never put a machine complaint about a heading inside a section that has been judged good: a green verdict and an amber one on the same block is a contradiction the reader has to resolve, and the human judgement wins.

What fails: a label ("Where the record is public"), a process ("Four steps, and the first costs nothing"), or a description of what you did ("Two builds, and what changed", "Profiles we have rebuilt"). `code/audit/copy_check.py` tests every heading against the four and names which one it should aim at.

## Every line is a chain: benefit, feature, meaning

Jim Edwards' bullet formula, and it applies to HEADINGS as much as bullets. The shape is the benefit first, then the thing that delivers it, then what that means for them. Connectors: so you can, which means, so your.

- "We rebuild your profile, so you show in the map pack, which means the call comes to you instead of the business above you when someone searches"
- Not "Google Business Profile - rebuilt, so you show in the map pack". That stops at what you do

The last link has to be something they can picture: a call, a job, a booking, money, hours back, beating a named competitor. "You show in the map pack" is still your world. "The call comes to you instead of the business above you" is theirs.

**Three benefits usually means three sections, not three bullets in one** (Jono, 26 September 2026). Each benefit gets its own section with the chain in the heading and the detail underneath. One section holding three bullets makes all three compete for the same glance, and none of them lands.

A heading that counts your steps, names your process, or labels the section has skipped the benefit. "Four steps, and the first costs nothing" is a process, and it also implies the other three cost money, including a phone call nobody pays for. "Your first leads inside 8 weeks, starting with a free audit" is the same section, sold.

`code/audit/copy_check.py` flags any heading with no outcome word in it. Where a section has a judged verdict the generic flag is dropped, because the verdict names the actual replacement line.

## The first screen holds five or six things, no more

Jono, 26 September 2026. In order, though the order is the designer's: a styled line above the headline (uppercase or coloured, the design touch), the headline, the line under it carrying the offer, the buttons, the three ticks, and the review score. That is the whole first screen.

A seventh element means something has to go. Four separate lines stacked under a headline is too much, and the reader stops before the buttons.

## What an audit may and may not say

A finding names something MISSING, unreadable, unproven or untrue. It never prescribes where a working element should sit. "Put the review score directly under the headline" is a made-up layout rule; "the rating has no number because nothing sources it" is the finding. Order, spacing and which side the form is on are the designer's choices unless they actually hide something.

The test before writing any fix line: would this still be a problem if the element were moved somewhere else in the same screen? If not, it is taste, and it does not belong in the report.

## The 26 components every page needs

Jono's 18 that a visitor sees, plus six added since (26 to 28 September 2026): page load speed (19), a guarantee (20), the thank-you page (21), a phone number people can tap (22), a stats bar (23) and client logos (24), then bullet points (25) and reading level (26) on 2 October 2026, when copy became its own group of four: little text, bullet points, feature then benefit then outcome, and reading level (grade 10 or below, measured line by line). Tracking was on the list and came off: whether a lead is counted is an analytics and Google Ads job, not a conversion one. The audit report counts out of all 24, with anything not needed for the business, or not checkable from outside, named as "not counted". The live list is `EIGHTEEN` in `code/audit/eighteen.py`.

Scope: this is the CRO track. Code hygiene, schema, meta tags, colour systems and model-fit layers belong to the SEO, Ads and web-design tracks and are not audited here.

Build every page with all of these. This is the recipe.

**Above the fold**

- [ ] **1. Founder video** near the top, 30 to 60 seconds - face and voice build trust faster than any copy. Their own why and their own promise
  - in their words. It sits high on the page because it is the closest thing to meeting them
- [ ] **2. The above-the-fold proof block** - three parts, somewhere in the first screen (Jono, 2 September 2026; clarified 26 September 2026: IN the fold, not in a prescribed slot. Above or below the buttons is the designer's call, and an audit must never call a working position a fault):
  - **The rating line** - "4.9/5 from 78 reviews" with the stars actually drawn in, beside the platform's own badge. A bare platform logo with no stars and no count proves nothing. Real numbers only. On an AD page it does not link out (Jono, 26 September 2026): the only ways off the page are the call, the form, or leaving, and a review profile is a fourth exit. Name the platform so the number can be checked
  - **Three avatar circles** - real client photos where they exist, otherwise initials in a coloured circle from the palette. Never a stock face, never a grey silhouette
  - **A checkmark list, three items** - years in business, clients or jobs served, and the guarantee. Ticks, not bullets. These are the three fastest credibility hits on the page and they are all numbers
- [ ] **3. CTA above the fold AND on every major section** - about eight times total on desktop. **Every one of them scrolls smoothly down to the form** (Jono
  - 2 September 2026): an anchor to the form's id, `scroll-behavior: smooth` on the root, `scroll-margin-top` on the form so the heading is not cut off
  - and focus moved into the first field on arrival so a keyboard or screen-reader user lands where the click promised. A CTA that jumps the viewport reads as a page reload and loses people who thought they had left. Honour `prefers-reduced-motion` and jump instantly for anyone who asked for that. Phone CTAs are the exception
    - a `tel:` link dials, it never scrolls
- [ ] **4. Strong offer above the fold** that resonates with the niche - see the offer formula below

**Proof**

- [ ] **5. Licence, insurance and bond, with the real number**
  - in the hero for residential trades (amended 23 September 2026). A logo wall only where the clients are brands people recognise; never placeholder marks standing in for proof
- [ ] **6. Video testimonials - three to start, nine is where it stops helping** - the single biggest trust driver on the page. Three well-attributed videos plus a linked live rating profile is the default
  - nine is a split test, not a rule (amended 23 September 2026). Stacked, everything visible at once. Poster frame, play on click, never autoplay. Show what exists - never pad the grid with empty tiles
- [ ] **7. Three selling points** that sell this specific company - these rotate per business
- [ ] **9. Response time** - only where the auto-dial actually delivers it, and a split-test candidate rather than a rule (amended 23 September 2026)
- [ ] **10. Written testimonials** in volume, 20 or more, alongside the videos
- [ ] **13. Proof badges** - Google, Yelp, Trustpilot, Facebook
  - industry bodies. The platform mark plus the real score and count. No score on file means the badge comes off - a badge with an invented number is fabricated proof
- [ ] **15. Case studies or portfolio, whichever fits - and sometimes neither.** Case studies for businesses judged on outcomes, a portfolio for businesses judged by looking (photography
  - events, trades, renovation, landscaping). Forcing both onto a page that needs neither is padding, and padding reads as thin proof

**Conversion and layout**

- [ ] **8. Little text, mostly bullet points**
- [ ] **11. Sign-up form on the page** with a qualifying question as tappable chips - never a dropdown, never a text box - autofill on every field, the phone-reason line, the consent line
- [ ] **12. Lead magnet** for filling out the form - a free PDF, tool or generator, named on the form and delivered on the thank-you page and by email. Show a picture of it so they can see what they get. **It is the cherry on top, never the reason they enquire** (Jono, 26 September 2026): nobody is looking for a checklist, they are looking for help with the job. Frame it as "we will help you with X, and you will have the audit in your inbox within minutes". A page that sells the magnet as the main offer attracts people who want the magnet and nothing else
- [ ] **14. No header and no footer on AD pages. One legal line instead. Header and footer stay on SEO pages** - see the page-type rules
- [ ] **16. One inspiration screenshot for STYLE only** - copy the look, keep these components
- [ ] **17. On MOBILE, one CTA bar fixed to the bottom of the viewport**, visible the whole scroll
  - call on the left and the form on the right. It stays put while the page moves under it. Desktop gets the CTA repeated at every major section instead
- [ ] **18. Copy is mostly social proof, results, and benefits over features.** Every word earns its place.

## The offer - component 4, and the most important thing on the page

The offer sits above the fold and must instantly resonate with the niche. There are two ways to build it.

### Option A - the results guarantee, best for results-based services

> We'll help you increase **[result]** by **[X]%** in **[timeframe]**, or you don't pay.

Pattern variations:

- "Make your business up to **[X]x** more [profitable/efficient] in **[timeframe]** - or we [pay you / refund you]."
- "**[Number]+** qualified [leads/sales] per [week/month] in **[timeframe]** or you don't pay."

Risk-reversal options to bolt on: a money-back guarantee · "we pay you $[amount] just for showing up" · "only [N] spots this month" · an eligibility filter such as "for businesses doing $[X]/month+".

Every risk-reversal line must be literally true and recorded in `context/proof.md`. Google's misrepresentation policy names unavailable offers and misleading urgency as violations, and repeat violations can suspend the account without warning (a, read 2026).

### Option B - the emotional offer, best when a hard number doesn't fit

When you can't promise a percentage, sell the feeling and remove the fear. Frame it **positively**.

The pattern: name the fear of getting it wrong - picking the wrong provider, ruining a once-in-a-lifetime moment, wasting money. Then flip to the positive outcome: peace of mind, the experience, "focus on [what they actually care about]".

Example skeleton: **"We'll Take Care Of Everything."** + *"We hired the top [X]% of [providers] out of [large number]. We'll remove the stress from [the task] - so you can focus on [the payoff]."*

### How to pick the offer

Before writing, research the niche - search the top competitors and the buyer's real fears and desires - to find the strongest angle.

If the research isn't conclusive, ask the business owner what their buyers care about most. Never guess the offer.

## Section-by-section build order

Build top to bottom in this order. The order is part of the asset - it walks a stranger from "is this real" to "I'll press the button", and it does not get rearranged to suit a business. Each section is a fill-in template.

### 1. Hero - does the most work

- **Business name and phone as plain content at the top of the hero.** Not a bar, not a nav, nothing that links anywhere else on the site. The name is text, the number is a `tel:` link.
- **Big benefit headline:** `[One short promise - the outcome they want]` - and it repeats the ad group's headline word for word
- **Subhead = the offer + proof:** `[Offer] + [proof number, e.g. "4.9 stars from [N] reviews"]`
- **3 credibility bullets:** `[trait 1]` · `[trait 2]` · `[trait 3]` (e.g. Same-day
- 5-Star Rated · [N]+ jobs/year)
- **Licence and insurance line:** hiding qualifications is an "unacceptable business practice" under Google Ads policy, and it is the first thing a homeowner checks (a)
- **Both CTAs, side by side:** the phone as click-to-call, and the short form. On a 1,500-lead HVAC dataset 62% of paid calls were click-to-call from the ad or hero, and home-improvement pages that offer call AND form convert at 4% against a 2.6% baseline (b)/(a)
- **A real image, or a designed substitute.** Never a placeholder frame. A founder video can sit here instead
  - face to camera, 30 to 60 seconds - lazy-loaded so it never becomes the largest contentful paint (a)

### 2. Trust strip - immediately under the fold, where the first doubt lands

- Star rating with the **real average and the exact review count, source named** - Google, Yelp, Facebook, industry sites
- **Recognizable client and partner logos** where they exist. Borrowed credibility is the safe choice. Only logos of real clients in `context/proof.md`
- Scale in one line: `[N]+ [jobs] a year` · `[N] years in [city]` · `[licence number]`
- Five reviews is the floor: five raise purchase likelihood 270% over none, and the gain flattens after five (b
  - Spiegel 2017). Show the real average even if it is 4.7 - a 4.0 to 4.7 rating converts better than a perfect 5.0 (b)

### 3. The problem, then the promise - the bridge, kept short

- Two or three lines naming what they are dealing with right now: `[the thing that is broken, leaking, overdue, or about to cost them money]`
- Then one sentence on what you do about it: `[the promise, in the same words as the ad]`
- This is the shortest section on the page. It exists to make the visitor feel understood, not to pitch.

### 4. What you get - benefits, never features

- Headline: `[Everything that's included]`
- Bullets tied to outcomes: `[deliverable 1 → what it means for them]` · `[deliverable 2 → …]` · `[deliverable 3 → …]`
- Say what is NOT included too. Naming the boundary reads as honesty and filters the wrong lead before they cost a call.
- CTA repeats here

### 5. Proof - the trust engine, and the heaviest block on the page

- **Video testimonials** - real clients on camera. This is the single biggest lift. Nine is the target, one is better than none.
- **Written testimonials in volume, 20 or more**, each with a **real first name and date** and **specific details** - name the staff member, name the outcome. Specificity is what makes it believable.
- **Proof badges repeated** here with exact counts and the source named.
- Render reviews as static HTML, not a third-party widget. Review widgets are a known mobile speed drag (b, NN/g)

### 6. How it works - three steps

The biggest silent objection on a service page is "what actually happens if I press this button". Answer it in three steps and no more:

1. `[You call or book - takes 2 minutes]`
2. `[We [do the thing], [when]]`
3. `[You get [the outcome], [guarantee]]`

State the response time here in words: `[Average response time: 75 seconds.]` Speed signals you care, and it beats competitors who reply in days. It stays on the page only if the auto-dial actually hits it.

### 7. Results - case studies or portfolio

Choose the pattern that fits the business type - the two patterns are further down this file. Visual portfolio for trades and creative work, numbers-driven case studies for results services. Anchor every case to a number and a timeframe.

### 8. Why us - the three selling points

The three things this business is best at, chosen because they are **true and differentiating**, hammered here and echoed everywhere else on the page. Each one gets a line of proof under it, not an adjective. CTA repeats here.

### 9. Service area

The real towns served, named. Out-of-area visitors self-select out before they cost a call. One page per real service area the business can prove it works in - a template with only the city name swapped is a doorway page in Google's spam policy and "insufficient original content" under Google Ads destination rules, even when noindexed (a).

### 10. The guarantee

Risk reversal, in the **same wording as the ad**. A guarantee that appears in the ad and not on the page is a substantiation failure and a Quality Score leak. Every risk-reversal line must be literally true and recorded in `context/proof.md`.

Optional scarcity, in words only: `[We only take [N] [jobs/clients] per [period].]` No countdown timers unless the deadline is real and does not reset; a fake timer is named as misleading design in Google's misrepresentation policy (a).

### 11. What it costs

Silence on price is one of the biggest exits on a service page. Say something true: a starting price, a typical range, a per-unit figure, or plainly how pricing works and what changes it. "We quote after a 5-minute call, and the quote is fixed" is a legitimate answer. Refusing to mention money at all is not.

### 12. FAQ - the reasons they DON'T enquire, answered

Not general questions about the service. **The FAQ answers the reasons somebody reads this whole page and still closes the tab** (Jono, 2 September 2026), which makes it the highest-value block on the page after the proof.

Ask the owner directly: what do people say when they don't go ahead? Those exact sentences become the questions, in the customer's words, not tidied up. Five to seven of them.

The ones that show up for almost every service business:

- **"How much is this going to cost?"** - answer with a real range or a starting figure. "It depends" is the answer that loses the lead
- **"How do I know you won't disappear / do a bad job?"** - the guarantee, the licence, the insurance, the years
- **"What happens after I fill this in?"** - the exact next step and the callback time. Uncertainty about what happens next kills more forms than price
- **"Am I too small / too big for you?"** - say who this is for and who it is not. Disqualifying openly raises the fill rate from the people who do fit
- **"Why you and not the other three quotes I'm getting?"** - the three selling points, restated as an answer
- **"Do I have to commit to anything?"** - the terms, plainly

**Answer them straight and short.** An FAQ that dodges reads worse than no FAQ, because the reader came to it already suspicious. If an answer is genuinely bad news, say it plainly - it costs one lead who was never going to buy and wins three who now believe the rest of the page.

### 13. The close - form, phone, guarantee

The last thing before the legal line, and the second conversion point on the page.

- **The form again**, same fields, with the response-time line beside it
- **No calendar widget here, or anywhere on the landing page.** The calendar lives on the thank-you page only
  - on the landing page it would compete with the form and the call, and a page with three asks converts like a page with none
- **The phone number**, one more time
- **The guarantee restated**, because doubt peaks at the moment of action
- Button copy that affirms the choice: "Yes! I Want A Quote Now"

**The form spec - FOUR FIELDS. First name, last name, email, phone. Nothing else.** (Jono, 2 September 2026.) No segmenting dropdown, no postcode, no revenue band, no "how did you hear about us", no message box. Every extra field is a reason to close the tab, and the qualifying happens on the call where it is free. Conversion falls as fields rise across 40,000 pages (a, HubSpot). Conversion falls as fields rise across 40,000 pages (a, HubSpot), the exception being qualifying questions the visitor sees as benefiting them (b). Phone is the lead for a call-back service, so it stays and uses a `tel` input. Never split a phone number into boxes, never rely on placeholder-only labels, put labels above the fields, single column, keep what they typed when an error shows (a, Baymard and NN/g). Never add a fifth field to this page. If qualifying questions are genuinely needed, they belong on the thank-you page or the call, after the lead is already captured.

**A lead magnet raises the fill rate** where one fits: a free PDF such as "[Top N mistakes to avoid when [doing the thing]]", a free tool, or a generator.

**SMS consent on the form.** An unchecked checkbox reading "[Business] may text me about my request. Msg and data rates may apply. Reply STOP to cancel, HELP for help." Submitting must not depend on it. Since February 2025 US carriers block texts from unregistered numbers, and registration is refused without this wording and a privacy policy that says mobile opt-in data is never shared with third parties for marketing (a, Twilio and HighLevel 10DLC guidance).

### 14. The legal line - and nothing after it

One centred line, small type, directly under the close: `[Business name] · [street address, city] · [phone] · [Privacy Policy] · [Terms]`.

Two links, both new-tab, and that is every link on the page besides the CTAs. It exists because Google grades transparency, the 10DLC registrar needs a reachable privacy policy on the form page, and the Ads bot must be able to crawl the page. **It is one line. It is not a footer.**

### Running the whole page

- **Mobile:** one sticky call bar pinned to the bottom, always visible
- **Desktop:** the CTA repeats on every major section
- **Email capture, if the business wants one:** desktop exit-intent only, never on page load, never on a phone. A popup on an ad page is a liability - Google Ads disapproves destinations with pop-ups and interstitials that break the Better Ads Standards (a), and Google Search has treated intrusive mobile interstitials as a negative signal since 2017 (b). The mobile equivalent is the sticky call bar.

### The thank-you page

Its own URL, `/thank-you`, because that URL is where the conversion tag fires.

- A warm confirmation - "You're the best!" or "Thank you" - and the callback time stated in minutes
- **The GHL calendar embedded. Always.** (Jono, 2 September 2026.) This is the highest-intent moment on the whole site - they just raised their hand
  - so let them book while they still want to. A thank-you page that only says "we'll be in touch" throws that moment away. For emergency trades the phone number sits above the calendar
    - but the calendar is still there
- **The lead magnet delivered here and by email** - the PDF
  - checklist or tool promised on the form. It is the reason the page is worth landing on and the first thing that proves you deliver what you say
- The phone number, for anyone who does not want to wait
- `noindex`, out of the sitemap, no navigation, no second ask (a)

## The three selling points - component 7

Every business picks **three** things it's best at and hammers them the whole page. They rotate per company. A common strong trio:

1. **Price** - affordable, best value
2. **Customer service** - fast response, dedicated point of contact
3. **Taking care of everything** - start to finish, all-in-one, no stress

Pick the three that are **true and differentiating** for the specific business, then repeat them in every section.

## Case study and portfolio patterns - component 15

Choose the pattern that fits the business type.

### Pattern A - visual portfolio

For creative and visual services: photo, video, design, events, trades. Use it when the work itself is the proof.

- A clickable image grid, 20 or more pieces of real work, each captioned with `[client first name + date]`
- A scale line up top: `[Completed [N]+ [jobs] this year]`
- Scarcity on quality: `[From [large number] candidates we selected the top [X]%]`
- The same component stack around it - logos, video testimonials, response time, FAQ, repeated CTAs

### Pattern B - numbers-driven case studies

For results and ROI services: agencies, automation, marketing, consulting. Use it when outcomes are the proof, and always anchor to a number plus a timeframe.

Each case study must show **specific numbers achieved in a specific timeframe.** Fill this template per case study:

> **[Client first name or initials]**
> [Business type, city]
>
> [1-2 sentence situation: the painful before-state and what it was blocking]
>
> **Saved:** [$ amount / time] - [what it replaced]
> **Results:** [metric 1, e.g. leads/week] · [metric 2, e.g. show rate]
>
> "[Short quote with hard outcomes - include rates and timeframes]"

Filled illustrative skeleton - replace everything in brackets, and do not use real names:

> **[Initials]**
> [Service business, city]
>
> [Business was doing [task] manually. [Overhead] was blocking it from scaling.]
>
> **Saved:** [$X/yr] - [replaced [role/tool]]
> **Results:** [N]+ [leads]/wk · [X]% [show/close] rate
>
> "[From [start state] to [end state], the team only has to [tiny action]. Everything else is automated. [Headline outcome].]"

## Copy principles - component 18

**Benefits over features, always.** Not "[professional equipment included]" on its own, but "[so you can focus on [the payoff]]". Tie every feature to the outcome.

**Social proof everywhere.** Names, dates, logos, badges, star ratings. Specific beats vague.

**Results with numbers.** "Top [X]% of [N]+", "[75] seconds", "[N]+ jobs/year", "$[X]/yr saved", "[X]% show rate". Numbers are believable, adjectives aren't.

**Little text.** Bullets beat paragraphs. The eye scans.

**Every word earns its place.** If it doesn't sell, prove, or move toward the form, delete it.

**Repeat the differentiators.** The three selling points and the response time recur the whole way down.

**Speed as a selling point.** A stated, repeated response time such as "[75] seconds" signals you care, and beats competitors who reply in days.

**Write for a 12-year-old.** Pages at a 5th to 7th grade reading level convert at 11.1% against 5.3% for professional-level copy, and word count correlates negatively with conversion (a, Unbounce 2024). Length by niche: emergency trades and HVAC under 200 words, standard home services about 300, complex services such as pest control 400 to 500, legal as short as the proof allows (a).

## Ad pages have no header and no footer - component 14

**Ad page, paid traffic: no header, no footer, no nav of any kind.** Zero exits. The page has one job, calling, booking or filling the form.

- **Delete the header.** No sticky bar, no logo row with links, no phone bar that doubles as navigation. The business name and phone live inside the hero as plain content
  - name as text, number as a `tel:` link, neither of them navigating anywhere.
- **Delete the footer.** No sitemap, no service list, no social row, no second nav. A footer on an ad page is a dozen exits at the exact moment the visitor has finished reading and is deciding.
- **One legal line replaces it**, centred and small, directly under the final form: `[Business name] · [street address, city] · [phone]
- [Privacy Policy] · [Terms]`. Two links, both new-tab. Google grades "transparency" (who you are, what you do, what you ask for)
  - the 10DLC registrar needs the privacy link reachable from the form page, and the Ads bot must be able to crawl the page (a). One line covers all three.
- Removing navigation lifted conversion 0 to 4% on cold pages and 16 to 28% on warm pages in HubSpot's five-page test
  - and doubled or better in single-site cases (b). No published test shows adding nav to an ad page raising conversion.
- The page is `noindex` and left out of `sitemap.xml`, never blocked in `robots.txt` (a).

**Watch for the template's own header and footer surviving the copy.** Landing pages are duplicated from a full website template that ships with both. Search the built page for `<header` and `<footer` before calling it done - this is the commonest way an ad page ends up leaking.

**SEO page, organic traffic:** header nav and footer nav both stay. The page needs site navigation and internal links to rank, and real browsing needs them too. Same for the standard pages - about, services, contact, legal.

## Mobile and desktop handle the CTA differently - components 3 and 17

**Desktop:** the CTA repeats on every major section, about eight times down the page.

**Mobile:** ONE sticky CTA bar pinned to the bottom that scrolls with the user, instead of repeating CTAs inline. Always visible, never in the way. It is a click-to-call button first, "Get a quote" second, and it sits above the phone's home-bar safe area.

83% of landing page visits are on a phone and mobile converts 8% worse than desktop (a, Unbounce 2024), so the phone layout is designed first and the desktop version is the adaptation.

## Speed - the page loads in under 2.5 seconds on a real phone

- Targets are Google's Core Web Vitals "good" thresholds at the 75th percentile
  - largest contentful paint 2.5 seconds or less, interaction to next paint 200 milliseconds or less, layout shift 0.1 or less (a)
- A 0.1 second gain on mobile lifted conversions 8.4% in retail and cut lead-gen page bounce 8.3% across 37 sites and 30 million sessions (a, Google and Deloitte 2020)
- Only 48% of mobile sites pass all three, so passing is a competitive edge, not table stakes (b, Web Almanac 2025)
- How: WebP or AVIF images sized to the slot, hero image preloaded, founder video lazy-loaded, no third-party review or chat widget in the initial render, fonts limited to two, no popups
- Test on a mid-tier Android over cellular with PageSpeed Insights, not on office wifi (c)

## Where the lead goes - the GHL webhook, the phone and the calendar

Three destinations, and the page is not finished until all three are live and tested. This is the half of a landing page that nobody screenshots and everybody skips.

**1. The GHL inbound webhook - every form on the page posts here.**

- Built in GoHighLevel: Automation, new workflow, trigger "Inbound Webhook", copy the URL. Stored as `LEAD_WEBHOOK_URL`.
- The payload carries the lead's fields PLUS the stashed `gclid`, keyword, campaign and UTMs, so the CRM knows which search produced the lead and the outcome can be sent back to Google later.
- The same webhook triggers the speed-to-lead auto-dial below.
- **A form that posts nowhere is worse than no form.** The click was already paid for. A page with a dead webhook never gets published.

**2. One real phone number - `BUSINESS_PHONE`, everywhere on the page.**

- One number. No pools, no per-page numbers. The business's name, address and phone stay consistent for local search.
- Plain text, never inside an image, in ONE consistent format, with the display text and the `tel:` href matching exactly. Google's forwarding-number swap fails on any of those.
- Google's phone snippet sits right after the Google tag on every page. For ad traffic Google swaps the displayed number and the `tel:` link for a forwarding number
  - routes the call through, records it, and ties it to the exact keyword. Call reporting must be ON at account level or none of it counts.
- **Call recording ON**, with Google's recorded-call announcement left on and the owner's confirmation first. The recording is what lets the owner screen a lead
  - hear which keyword produced a tyre-kicker, and settle a "nobody called me back" dispute. Two-party consent law applies in many places, which is exactly why the announcement stays.
- The `tel:` link also fires the stashed keyword to the GHL webhook before dialling, so the CRM has keyword-level call attribution even when Google only counts the tap.

**3. The GHL calendar - `GHL_CALENDAR_URL`, on the thank-you page ONLY. Only if the owner wants one.**

- Asked once, up front. "No calendar" is recorded and the widget, its conversion action and its checklist lines are all skipped - a phone-and-form page is a complete page.
- **Never on the landing page itself.** The landing page sells the call and the form. The calendar is the follow-through for someone who has already converted
  - that moment happens on `/thank-you`, not beside the pitch.

- **A booking is NOT a Google Ads conversion.** Everyone who reaches `/thank-you` already fired the form conversion - tagging the booking too counts one lead twice. The booking lives in GHL
  - the appointment-booked workflow sends the confirmation SMS and updates the pipeline stage, and that stage flows back to Google through the offline import if anywhere.
- When the business has one, it goes on the thank-you page too - that is the highest-intent moment on the whole site.

## Tracking - every page ships instrumented

- On landing, capture `gclid`, campaign, ad group, keyword and UTMs into sessionStorage; every form post and every tel: click sends them to the webhook (a, Google offline conversion model)
- **One conversion per lead path the page actually has:** form submit, website call over the minimum length
  - and calls from the ad itself. Each one is a real lead and each one is primary. A calendar booking on `/thank-you` is NOT one
    - that lead already fired the form conversion. Views, scrolls, form starts and widget clicks never are
- Enhanced conversions for leads: the hashed email or phone leaves the form with the click, auto-tagging on, Google tag or Tag Manager in place. Google now recommends this over plain GCLID import (a)
- The form conversion fires on `/thank-you`, or from the form's success event - never both on one action (a)
- **Verify in Tag Assistant before the page is called done.** Connect the live URL at https://tagassistant.google.com/
  - then submit the form, tap the number and book a slot, and read the tag list: the Google tag fired
  - Conversion Linker present, one conversion request per action carrying the right label
    - and no duplicate request. A duplicate silently doubles every number in the account and is the commonest tracking failure there is
- The phone snippet is a second gtag config call - `gtag('config', 'AW-[id]/[call label]', { phone_conversion_number: '[number]' })`
  - never the legacy `wcm/loader.js` + `_googWcmGet` pair, which silently defines nothing on a gtag page. Tested in two stages
  - stage 1 the moment the page is live - load it with `?gclid=test` and read `window.google_wcc_status` in the console
    - `"no ad click"` is a PASS (Google's script asked for a number with your label and click id
  - and declined only because the click is invented), undefined means the phone config never registered. The display does NOT swap at stage 1
    - Google only allocates forwarding numbers to genuine ad traffic. Stage 2 once a campaign runs
    - the first real ad visitor sees the swap and the call lands in the calls report. Never click your own ad to test it (c for the synthetic-gclid convention, a for the rest)
- If AI Max is on for the campaign, either add URL exclusions for every non-converting page or turn final URL expansion off
  - otherwise Google can send the click to any page on the domain and override pinned headlines (a, 2025)

## Speed to lead - wired before the page goes live

The page's conversion rate is only half the number. Between a 5-minute and a 30-minute first call, the odds of reaching the lead fall about 100 times and the odds of qualifying them about 21 times (a, MIT and InsideSales, 15,000+ leads). Calling inside 1 minute lifts conversion 391% over a 2-minute wait (b, Velocify, about 3.5 million leads). 88% of home-service firms take longer than 5 minutes and 3% answer inside 1 minute (b, Hatch 2024), so the bar is low.

- The form's webhook triggers the auto-dial: the owner's phone rings, then bridges to the lead
- An SMS goes to the lead within 60 seconds naming the business and the number that will call, because 86% of people will not answer an unknown number (b, Hiya)
- That SMS needs the consent checkbox on the form and a registered 10DLC campaign; unregistered traffic has been blocked by US carriers since February 2025 (a)
- The stated response time on the page ("75 seconds") is the number this system actually hits, or it comes off the page

## Accessibility basics - four lines, always

- Tap targets at least 24 by 24 CSS pixels, 44 preferred for the call button (a, WCAG 2.2)
- Body text contrast at least 4.5 to 1 against its background (a)
- Real `label` elements above every field, `tel` and `email` input types, visible focus states (a)
- Alt text on every proof photo naming what it shows ("Owner Mike Reyes fitting a boiler in Leeds")

## Testing the page - only as a Google Ads experiment

- Duplicate the campaign as a custom experiment, cookie-based 50/50 split, change only the final URLs (a)/(b)
- Leave it 3 to 6 weeks and 50 to 100 conversions per arm; Smart Bidding relearns for 1 to 2 weeks after the change, so ignore days 1 to 3 (b)
- Judge on cost per lead and lead quality, not conversion rate alone (b)
- Below about 30 to 50 conversions a month the test cannot resolve; fix the CRO cheatsheet items instead (b)
- Re-check the landing page experience rating in Google Ads 2 to 4 weeks after any page change; Below average sends you to `references/cro-cheatsheet.md` top to bottom (b)

## Copy the style, never the structure - component 16

You can hand in a screenshot of any site you like for the look and feel - colours, fonts, spacing, vibe - and match the style to that reference.

But the components and structure in this blueprint stay fixed. Style is the skin, this stack is the skeleton. Never trade a converting component for a prettier layout.

## Optional polish

- **Localization toggle**, for example English and French, if the market is bilingual - widens reach without rebuilding
- **FAQ section** near the bottom to kill remaining objections - pricing, logistics, "what if" worries - with each answer ending in a soft CTA
- **Click-to-call** as the primary hero CTA for high-intent local buyers, with the form as the secondary path
- Nothing about the calendar is optional polish: it goes on `/thank-you` when the owner wants one, and nowhere else

## Check this before you launch

**The offer and the top of the page**

- [ ] H1 = proof word + city (from the URL) + service, in a line that sells; offer line repeats the ad's offer
- [ ] Offer is above the fold and niche-specific, researched or confirmed with the owner
- [ ] Sections run in the build order, 1 through 14, unchanged
- [ ] 3 credibility bullets plus licence and insurance line above the fold

**The proof**

- [ ] Logo wall of recognizable brands, all in proof.md
- [ ] 9 video testimonials and 20+ written testimonials, with real names and dates; never fewer than 5 reviews shown, real average shown
- [ ] Proof badges from Google, Yelp, Facebook and industry sites with exact counts, repeated
- [ ] Three selling points chosen and repeated throughout
- [ ] Response time stated and repeated, and the auto-dial actually hits it
- [ ] Case study or portfolio block matching the business type, with numbers if results-based
- [ ] Service area block with real towns

**The conversion path**

- [ ] Form is 3 to 4 fields, labels above, tel input, segmenting dropdown, outcome button text, guarantee beside it, plus a lead magnet
- [ ] Unchecked SMS consent checkbox with the 10DLC wording, privacy policy linked
- [ ] Second form in the close section - no calendar widget anywhere on the landing page; email capture is desktop exit-intent only, never a mobile popup
- [ ] Urgency and scarcity close in words, no timers, plus an objection-handling section
- [ ] Thank-you page at its own URL, noindex, fires the conversion, states the callback time, with the GHL calendar embedded if one was wanted
- [ ] Desktop has a CTA on every section. Mobile has one sticky bottom call bar
- [ ] Ad page has NO header and NO footer - one legal line under the final form. SEO page keeps both
- [ ] Copy is bullets, benefits, social proof and numbers, at a 5th to 7th grade reading level, every word earning its place
- [ ] Everything points to the call or the form

**Speed, tracking, policy**

- [ ] LCP 2.5 seconds or less on a mid-tier phone over cellular, layout shift 0.1 or less
- [ ] gclid, keyword and UTMs captured on landing and sent with every form post and call click
- [ ] Enhanced conversions for leads on, auto-tagging on, call reporting on, call recording on with the announcement
- [ ] Every lead path the page has wired to its own conversion action: form, website call, ads call. Never a booking tag - the form conversion already counted that lead
- [ ] Tag Assistant run on the live URL: form and tap-to-call fired, none twice
- [ ] The TRACKING VERIFIED block written into CLAUDE.md "## My setup" with the date - unwritten means unverified
- [ ] Number swap seen live with a gclid on the URL
- [ ] Test lead AND test booking confirmed as arrived in GHL, not just posted
- [ ] Page noindex, out of the sitemap, not blocked in robots.txt
- [ ] AI Max URL exclusions set, or final URL expansion off
- [ ] Every claim, logo, review and guarantee traces to context/proof.md; compliance.md checked
- [ ] Tap targets 24 pixels or larger, contrast 4.5 to 1, real labels
- [ ] Speed-to-lead tested live: form submitted, owner's phone rang, lead got the SMS

## What changed in this revision

**1 September 2026 - Jono's rulings after a live build**

- **No header AND no footer on ad pages.** The old version kept a four-line footer
  - it is now one centred legal line under the final form. Same transparency and 10DLC coverage, zero exits (Jono's ruling)
- **The section order rebuilt as a real landing page flow**: hero, trust strip, problem/promise, what you get, proof, how it works, results, why us
  - service area, guarantee, price, FAQ, close, legal line. The old order opened with a marketplace vetting story that only fitted one kind of business
- **Two new sections that were missing entirely**: "how it works" in three steps (the biggest silent objection on a service page) and "what it costs" (the second biggest exit)
- **New section: where the lead goes** - the GHL inbound webhook, the one real phone number with recording, and the GHL calendar. None of the three were named in this file before
- **The calendar (when the owner wants one) sits on `/thank-you` only and is never a Google Ads conversion**
  - the form conversion already counted that lead, and two primaries for one business event is the double-count our own rules ban. Bookings are tracked in GHL
- **Call recording is now ON** by default with the announcement and the owner's confirmation, reversing the old "never enabled" line. Recording is how the owner screens leads and audits keyword quality
- **Tag Assistant verification is part of the build**, not a follow-up: connect the live URL, fire all three lead paths, read the tag list back, confirm no duplicates

**28 August 2026**

- Component 12 (email-capture popup) changed to desktop exit-intent only, never on mobile
  - Google Ads destination policy disapproves pop-ups and interstitials, and it contradicted the "no popups" rule in the command (a)
- Component 14 refined: no header nav stays, but ad pages now carry a four-line footer (name, address, phone, privacy, terms) for Google's transparency signal, 10DLC registration and crawlability (a)
- Added "The one law: message match" with the 66% and 212% lifts and the AI Max text-customization warning (b)/(a)
- Added the form spec: 3 to 4 fields, labels above, tel input, no split fields, two-step when more questions are needed, SMS consent checkbox wording (a)/(b)
- Added the review floor of five and the "show the real 4.7" rule from Spiegel (b)
- Added the speed section with Core Web Vitals thresholds and the Deloitte 0.1 second data (a)
- Added the tracking section: gclid capture, enhanced conversions for leads, one number no pools, AI Max URL exclusions (a)/(c)
- Added the speed-to-lead section with the 5-minute and 1-minute data, the SMS rule and the February 2025 10DLC cut-off (a)/(b)
- Added the service-plus-city rule: one page per provable area, city-swap templates are doorway pages (a)
- Added the testing section: Google Ads custom experiment only, 50 to 100 conversions per arm, judge on cost per lead (a)/(b)
- Added four accessibility lines from WCAG 2.2 (a)
- Added reading-level and word-count-by-niche guidance from Unbounce 2024 (a)
- Reframed the 20% claim as top-quartile, with the 2024 medians stated (a)
- Countdown timers now explicitly banned unless real; scarcity stays in words (a)
- Thank-you page now specified as its own noindex URL that fires the conversion, with the calendar as an option for consult services (a)/(c)
- Launch checklist extended with a "Speed, tracking, policy" block
- All 18 components, the offer formulas, the three selling points, the case-study patterns and the copy principles kept verbatim as the house ruling
