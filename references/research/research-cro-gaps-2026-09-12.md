# CRO research: what the series is missing, and what to fix

Date: 12 September 2026
Method: eight parallel research passes, roughly 130 sources opened and read, not skimmed from search results.
Scope: conversion rate optimization for local service businesses running Google Ads.
Every number below is traced to a source that was actually opened. Where a famous number did not survive, that is said plainly.

Audience assumption throughout: plumbers, roofers, HVAC, electricians, cleaners. One location or a few. Paid search to a landing page.

---

## Part 1. The seven things to add

### 1. Track the phone call, or Modules 3 and 4 are measuring the wrong thing
The page has a CALL button. For a plumber the call is most of the revenue.
Invoca read 70 million calls: paid search calls to home services convert at 48 percent once qualified.
Nothing in the four modules mentions call tracking or dynamic number insertion.
If calls are not tracked, three things break at once.
A variant that moves people from the form to the phone reads as a loser while making more money.
PostHog sees the tap and then the session just ends.
Google Ads Smart Bidding learns to buy clicks that produce forms, not clicks that produce jobs.
Fix: a call tracking number, calls over 30 seconds counted as a conversion, imported into Google Ads.
This is the single biggest hole because everything downstream depends on it.

### 2. A Module 0 that verifies the tracking before anything gets optimized
The series assumes conversion tracking works because the Ads track set it up.
That is the assumption that fails most often.
The five faults, in order of how often they bite: tag fires on page load not on submit success, tag fires through failed validation, thank-you page counted again on the back button, the native tag and the imported GA4 event both set to Primary, and counting Every instead of One for a lead.
Google's own rule: use One for leads, Every for sales.
A 10 to 30 percent gap between GA4 and Google Ads is normal, not a bug. Ads books to the click date, GA4 books to the conversion date.
Fix: one hour before Module 1. Submit a real lead, confirm exactly one conversion fires, submit a deliberately broken one and confirm nothing fires, reconcile 30 days of Ads conversions against the actual GoHighLevel records.
Then run an A/A test in PostHog before the first real test. Two identical variants. It should come back non significant about 95 percent of the time. If it does not, the measurement is broken.

### 3. What happens after the form, which is where most of the money actually is
The course ends at the thank-you page. The evidence says the money is past it.
Velocify, 3.5 million leads: 93 percent of converted leads are reached by the sixth call attempt.
Half of all leads are called exactly once.
InsideSales audited 9,538 companies: only 22 percent responded by phone at all, and 36 percent of those called once.
Invoca: 55 percent of home services businesses never ask the lead to buy or book the job.
ServiceTitan, 3,000 plus trade businesses: average call booking rate is 42 percent, but 24 percent for shops under five techs and 59 percent for shops with 25 plus.
A small contractor going from 24 to 42 percent is a 75 percent increase in jobs from identical traffic.
No landing page change in this course is worth that.
Fix: a six attempt call cadence over about 14 days, five emails alongside it, and a scripted ask for the booking.

### 4. Price on the page
Nothing in the 18 components addresses money. This is the biggest omission inside Module 1 itself.
Nielsen Norman Group found price is the single most wanted piece of information, and that participants left for competitors when it was missing.
Baymard: 40 percent of abandonment traces to unexpected cost, and 12 percent to not being able to work out the total up front.
Their words: people view companies that hide costs as evasive.
Fix, and it is concrete for trades: the diagnostic or call-out fee stated plainly, typical ranges by job, whether the quote is free, and whether financing exists.
This also needs a rule change. "Every line is social proof, results or benefits or it gets cut" currently deletes the thing buyers most want, because a call-out fee is none of the three.
Add a fourth allowed category: answers a question the buyer will otherwise leave to find.

### 5. Mine the phone calls for the copy
A plumber's page converts to a call. Every objection, every price question, every reason someone rang three companies and picked one is sitting in call recordings.
Nobody in the four modules listens to one.
The strongest published result in the whole research pack is a mined headline: "If you think you need rehab, you do." Over 400 percent more CTA clicks and over 20 percent more form submissions. It was found, not written.
Griffin and Hauser: 20 to 30 customer conversations gets you 90 to 95 percent of customer needs.
Fix: goes at the front of Module 2, before the avatars exist. Transcribe 20 to 30 calls, code them for repeated phrases and objection order, build the avatars from that, and use the phrases as the copy bank for the rewrite.
Also free and currently unused: the Google Ads search terms report is verbatim customer language, already paid for, perfectly matched to the traffic hitting the page.

### 6. Ask real visitors, and put three real humans in front of the page
Nothing in four modules asks a real person anything.
Survicate, 4,332 surveys: a website widget survey gets a 7.64 percent median response rate. Two to three questions outperform one question, 15.97 vs 9.75 percent.
Exit surveys hit 35 to 45 percent when they fire at a real decision moment, and 0 to 4 percent on generic mouse-out.
Two questions earn their place. On the thank-you page: what nearly stopped you from calling. On exit: what were you hoping to find that you did not.
Then three real humans. Not five, three. The comparison that matters is not 5 versus 20, it is three versus zero.
Baymard's finding is that layout bugs and janky interactions make people doubt a site and leave, and an AI reading the page source does not experience a broken mobile date picker.
Fix: a short gate between Module 2 and Module 3. Three people, one task, fifteen minutes each. Anything two of three hit gets fixed before you spend money on traffic.

### 7. The consent line on the form, because the course tells people to text leads
The course puts a TEXT button on the mobile bar, and the Ads track fires an automated text through GoHighLevel.
That is automated outbound texting to consumer mobiles. It carries real money risk.
TCPA damages are 500 dollars per text, up to 1,500 if willful, with a private right of action. Every text is a separate violation.
2,000 form fills with no valid consent is a seven figure theoretical exposure.
Status check, because the internet is wrong about this. The one-to-one consent rule was vacated by the Eleventh Circuit in January 2025 and formally removed by the FCC in August 2025. It is dead.
But the four prior express written consent elements survive untouched, and that is what people got wrong.
What the form needs: a clear disclosure that they agree to automated calls and texts, your business named specifically, a line saying consent is not a condition of purchase, and an unchecked box or button language. Above the submit button, not in the privacy policy.
Then log it: timestamp, IP, the exact consent text shown. If sued, you have to prove consent.
Two more: quiet hours are 8am to 9pm in the recipient's local time, which breaks naive speed to lead on a form filled at 11pm. And since April 2025 an opt-out by any reasonable wording counts, processed within 10 business days.
This is fifteen minutes of work. Not a lawyer, so have one read the form.

---

## Part 2. The claims in the series that do not survive

### "300 clicks per variant" is the one that matters most
Five separate research passes flagged this independently.
At the plumbing median conversion rate of 7.63 percent, 300 clicks per variant is about 23 conversions per side.
That detects a plus 80 percent relative lift and nothing smaller. On roofing at 3.70 percent it is plus 117 percent.
Power against a realistic 20 percent lift is about 10 percent. Against the median real lift of 4 percent it is about 3 percent.
Meaning: roughly 70 to 74 percent of the winners this design declares will be noise. And the ones that are real get inflated 25 to 50 percent by the winner's curse.
The stated reasoning does not hold either. The rule exists because "300 total cannot separate 10 percent from 14 percent." True. But 300 per variant cannot separate them either, p equals 0.13. You need about 1,400 per variant for that.
Sharp observation from the testing pass: run the numbers on your own chat widget test, 11.3 versus 19.7 percent, and the required sample is about 300 per variant. Exactly. The rule looks reverse engineered from the one test where it happened to be enough.
Replacement rule, and it is simpler than the current one. Count leads, not clicks. Leads per variant is roughly 16 divided by the lift squared.
Plus 20 percent lift needs about 400 leads per variant. Plus 50 percent needs about 70. Plus 10 percent needs about 1,475, which nobody can afford.
So: below roughly 70 leads per variant, do not A/B test. Ship best practice and say plainly that you shipped it on best practice, not on a measurement. That is a professional answer.
The unlock that makes testing possible at all: pool it. Ten plumber clients at 30 leads a month is 300 leads a month pooled. A 20 percent test becomes 2.6 months instead of 26. Run the same structural variant across the whole portfolio.
One thing the module already gets right and should claim credit for: testing massively different structural variants rather than button colours is correct, and it is the only thing that makes low traffic testing viable at all. Bigger effect, smaller sample. The error is not the strategy, it is believing 300 clicks measures it.

### "Half of callers will not phone during work hours" is wrong by about four times
ServiceTitan's own 2025 data, twelve months of residential HVAC inbound calls: 14.1 percent off hours at the June peak, 9.8 percent in October. Off hours defined generously as before 8am, after 5pm, and all weekend.
The 47 and 50 percent figures circulating online cite "ServiceTitan 2026 panel data." No such report exists on their site. It traces to AI generated content farm pages citing each other.
But the two button bar is still right, for a better reason. The real split is age, not hours.
Leadferno, 1,000 consumers: ages 25 to 34 are phone 26.5 percent versus text 23.7 percent, near parity. Ages 55 plus are phone 58.5 percent versus text 8.2 percent, nearly seven to one.
A roofer sells to both groups. That is the argument for two buttons, and it survives someone fact checking it in the comments.

### "Under 2.5 seconds" is the right instinct with the wrong specification
2.5 seconds is an LCP threshold, not a page load threshold. Different numbers, and they diverge badly on a page with a video at the top.
Google states the threshold was chosen for quality of experience and achievability. Conversion was explicitly not a criterion. When it was set, only 42 percent of phone origins could hit it.
Google's own words: many sites would benefit from optimizing beyond the good thresholds.
Both controlled experiments suggest the target is loose. Vodafone's winning variant had an LCP of 5.7 seconds and still beat an 8.3 second page by 8 percent on sales. Rakuten's winner was at 1.6 seconds.
Fix the spec: LCP under 2.5 seconds at the 75th percentile of real mobile visits, aim for 1.8. And set the other two, because a page with nine videos plus a replay script plus a testing script is exactly the page that breaks them. INP under 200ms, CLS under 0.1.
Related and unsaid: the founder video's poster image is the LCP element. It needs a real poster, matched aspect ratio, high fetch priority, preloaded, and tap to play rather than autoplay. Never lazy loaded, because 16 percent of real pages lazy load their own LCP image.

### "A one second delay costs 7 percent of conversions" should be dropped
Traced to Aberdeen Group, November 2008. The PDF is corrupt and unopenable. Aberdeen's house method in that era was surveying IT managers about their own numbers.
It is 18 years old and routinely misattributed to Amazon.
Same family: "53 percent abandon after 3 seconds" is Google DoubleClick 2016, about 3,700 publisher sites that opted into analytics benchmark sharing, when average mobile load was 19 seconds on 3G. Akamai's famous 2017 report re-cites that same number rather than measuring it, so people citing both are citing one source twice.
If a speed number is needed, use Deloitte: 0.1 seconds faster is associated with 21.6 percent more lead generation form submissions, 30 million sessions across 37 brands, and say out loud that it is observational.

### "Every extra form field costs conversions" does not say what people think
Traced to Dan Zarrella's analysis of 40,000 HubSpot landing pages. That post contains no percentages at all, only unlabelled graphs, and it is correlational.
What it actually found: single line text fields show very little decrease. The killers are textareas and multiple dropdowns.
Zuko's field level data across 1,362 live forms: the trend line between field count and completion is almost flat.
So the highest leverage correction inside Module 1 is not fewer fields. It is that the two qualifying questions must be tappable chips or radio buttons, never dropdowns or open text boxes.
Related myth, same family: "multi-step converts 86 percent higher" is a survey of 173 marketers reporting their own numbers, and HubSpot's own authors said to take it with a grain of salt.
And the cheapest win nobody mentions: autofill. Chrome telemetry across millions of page loads, 75 percent less abandonment. It only fires with a real form tag and correct autocomplete attributes. Ten minutes of work.
One more, from Baymard's survey of 1,026 shoppers: 14 percent will never give a phone number, 39 percent of sites ask without explaining, and people enter fake numbers rather than abandon. A fake number on a plumber's form is a 100 percent wasted click. One line under the field fixes it.

### "Nine video testimonials" has no evidence behind the nine
The relevant research points the other way. Nearly all the lift from reviews happens in the first five to ten. After that, diminishing returns.
Nine videos is also a real page weight cost on the mobile ad traffic this page is built for.
Make it a test: three well attributed videos plus a linked live rating profile against nine. If nine wins that is genuinely new and worth publishing.
Related: "never a carousel" is overstated. Nielsen Norman's finding is against auto forwarding carousels and against showing one panel at a time. Keep stacking, change the reason. Stack because everything is simultaneously visible, not because carousels were proven to fail.

### "4.0 to 4.7 beats a 5.0" should not be taught to a local service business
The peer reviewed number is 4.2 to 4.5, measured on light bulbs, athletic shoes, hair care and vitamins, on products with high review counts.
Baymard's data shows the real variable is the count, not the average. Nearly twice as many people chose a 4.5 from 57 raters over a 5.0 from 4 raters.
Three reviews at 5.0 reads as mom and two friends. 340 at 5.0 reads as excellent.
Do not tell a roofer with 31 five star reviews to worry about looking too good. Tell him to never show an average without the count next to it.

### Six brand logos is the weakest of the 18 components
No credible controlled evidence exists for logo walls or "as seen in" strips. The 48 percent and 400 percent figures trace to PR industry marketing pages with no method.
The one lead-gen trust mark test available goes the other way: removing a TRUSTe seal produced 12.6 percent more form completions, because a payment context badge on a top of funnel form makes people think a transaction is coming.
Context risk for a residential plumber: commercial brand logos can actively signal "this company does commercial, not my kitchen."
Better swap, and it is the top ranked thing homeowners actually say they want: licensed, insured and bonded, stated with the real licence number. A survey of 559 US homeowners put licensed and insured first at 25 percent, ahead of everything else.

### "Message match lifts conversion 144 percent" is one undocumented test
MECLABS, unnamed B2B client, no sample size, no duration, no confidence, no headline text, and presented as one step in a sequence claimed to compound to 603 percent, so it is not even isolated.
Teach message match as a production rule. Never quote the number.
Also soften the literal version. The evidence supports continuity of meaning, not string reuse. Word for word keyword reuse produces headlines like "Emergency Plumber Near Me Open Now," which fails the readability evidence and reads as machine written.

### Two smaller ones
"We call back in 75 seconds" repeated three times: there is no evidence that stating a response time lifts conversion. All the speed to lead research measures actually responding fast, never promising to. It is a good Module 4 test candidate and it is currently presented as a rule. Worse, the promise is made here and the machine that keeps it is taught in a different track, so anyone taking only the CRO course ships a promise with nothing behind it.
"We will never spam you" and its relatives: Michael Aagaard measured this twice, minus 18.7 percent and minus 24 percent. The word spam plants the idea it denies. The positive reframe gained 19.5 percent. Same family as no obligation, no pressure, no hidden fees.

---

## Part 3. What Module 2 needs, because AI personas have a documented failure mode

The persona panel has more published evidence behind it than the rest of the series, and it is mixed.

Where they work: reproducing known main effects at about 76 percent, and directional forecasting of treatment effects at r equals 0.85 when conditioned on real people's backstories.

Where they fail, and all three matter here.
Variance collapse. Simulated people cluster far tighter than real ones. Your five avatars will disagree with each other less than five real customers would.
Sycophancy. Nielsen Norman compared synthetic users against three completed real studies. Real users said they had not finished the online courses. Synthetic users claimed they finished all of them. Real users called the forums contrived. Synthetic users praised them.
Demographic misalignment is worst for adults 65 plus and widowed people, and it persists even when the model is explicitly told to be that person. A large share of emergency plumbing and HVAC buyers are older homeowners. The avatar you weight highest is the one the model is documented to be worst at simulating.

So the stop-bar is inverted. "Stop when no avatar says LEAVE" is the default state of a sycophantic model, reachable by a mediocre page and a friendly prompt.
Fix: weight negative verdicts heavily and positive verdicts at nearly zero. Force the LEAVE reason out with a forced choice prompt, something like: you have one tab open and 30 seconds, what makes you close it. Then stop when the remaining LEAVE reasons are all outside the page's control, meaning price, service area or availability.
Second fix: "a blocker two avatars hit independently" is not independent. Two agents on the same base model with similar prompts are one draw, not two. Keep the rule, but require one external confirmation: the same blocker appearing in a call recording, a search term, or one of the three real humans.
Third: pin and log the model version. Identical prompts produced materially different distributions three months apart in the published study.

One rule to refine rather than keep. "Never from Google reviews" is right, and the reason to give is better than the one being given. Reviews are J-shaped, piled at 5 and 1 stars, because only people who already bought write them and only extreme opinions get written down. Your avatars need to represent the people who did not call, and reviews contain zero of them.
But that reasoning only kills reviews as an avatar source. It does not kill them as a source of problem language, which is what message mining needs. Refine it to: never build an avatar from reviews, do mine reviews for the words people use to describe the problem.
And the inconsistency worth naming: if reviews are out for being unrepresentative, a 50 article industry research pass is worse on every axis. Written by marketers, SEO optimized, no first person language, its own selection bias and none of the authenticity. Demote it well below call recordings and search terms.

Module 3 note, same theme. Five session replays is better than it sounds because Claude filters first rather than sampling randomly. The problem is what "worst" means. Sessions with the most rage clicks are a bug sample, not a friction sample, so you get five copies of the same broken button and nothing about the offer. The sessions that matter are the quiet ones: arrived, scrolled to the price section, stopped, left, no errors at all. Nothing currently surfaces those, which is why the TEST LATER list will come out thin.
Fix: three strata instead of one. Three or four with the most frustration signals, three or four that reached the form or the call button and did not convert with no errors, and two or three that converted as a control. About ten sessions, still an hour, and it separates broken from unconvincing, which is exactly the FIX NOW versus TEST LATER split.

---

## Part 4. Numbers worth putting on a slide

The best one in the whole research pack, and it is the argument for the course existing.
Cost per lead in the trades has roughly doubled to tripled in four years. Same publisher, same method, four years apart.
Plumbing went from 48.91 dollars to 129.02.
Roofing went from 101.49 to 228.15.
Air conditioning went from 55.15 to 127.74.
Heating went from 62.18 to 129.02.
That reframes everything. Conversion rate is not an optimization any more, it is the only lever left that is not inflating.

Current benchmarks, LocaliQ, 3,211 US home services search campaigns, April 2024 to March 2025, medians.
Home services overall: 7.33 percent conversion rate, 7.85 dollar CPC, 90.92 dollar cost per lead.
Plumbing: 7.63 percent, 10.49, 129.02.
Roofing and gutters: 3.70 percent, 10.70, 228.15.
Handyman: 13.45 percent. Cleaning and maid: 17.65 percent.
Caveat worth saying on camera: LocaliQ never defines what counts as a conversion.

Speed to lead, told honestly.
Zero out of 114 companies called a lead within five minutes, in a March 2026 audit.
23 percent of companies never respond at all, and the average first response is 42 hours.
The edge is not that speed is magic. The edge is that the bar is on the floor.
The famous 100x number is odds of contact, not sales, from a 2007 vendor dataset with no home services in it, comparing 5 minutes to 30 minutes specifically. Use the Harvard Business Review version instead: about 7 times more likely to qualify inside an hour, from 1.25 million leads.

Test win rates, so nobody quits after three flat results.
Microsoft across all experiments: one third win, one third flat, one third lose.
Mature products are worse. Bing 15 percent, Booking and Netflix 10 percent, Airbnb search 8 percent.
Across 115 published tests the average lift was 3.77 percent.
Twenty tests a year at a 15 percent win rate is about three real winners. A realistic year is 10 to 25 percent relative improvement, not a doubling.
And the lifts do not add up. Measure the program with a global holdout, 5 to 10 percent of traffic left on the original page for a year. That one number is worth more than thirty scorecards.

---

## Part 5. Two structural notes

The module order is mostly right and one thing is missing from the front.
Build, then heuristic critique, then behavioural data, then testing is the standard research sequence. Module 2 sits correctly because there is no traffic to analyse yet.
What is missing is Module 0, verifying the measurement. Every module after it consumes conversion data.

Two overlaps worth a decision.
Slide 14, no header no footer, and slide 19, four ways out, are the same idea twice: remove the exits.
Slide 3, a button on every section, and slide 17, the mobile bar, also overlap.
The design system says merge duplicates and let the stronger graphic survive.

One thing to stop saying.
"About eight CTAs on desktop" is an invented constant. 74 percent of viewing time is in the first two screenfuls and median scroll depth is 50 to 60 percent, so CTAs five through eight are seen by a small minority. Harmless, probably, but it is not a rule. Demote it to a default worth testing.

---

## A note on source quality

A large cluster of sites surfaced repeatedly during this research with dense, confident home services statistics. They attribute numbers to reports that do not exist, most notably a "ServiceTitan 2026 panel" that is not on ServiceTitan's site.
They are AI generated and they cite each other.
Several numbers currently in the series appear to have come from that layer of the internet.
Everything in this document was traced to a page that was actually opened, and where that failed it says so.
