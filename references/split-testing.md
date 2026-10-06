# Split testing - two pages, one URL, the visitors decide
Written 23 September 2026 from research/research-split-testing.md (69 sources) · for /split-test
Next: `python3 code/sample_size.py --baseline <your rate> --lift 0.3 --leads-per-month <n>` before building anything. The call is an 80% chance to win.

## Count leads, not clicks

The old rule, 300 clicks a side, does not hold. At a 7.6% conversion rate that is 23 leads a side, which only detects an 80% lift; against a realistic 20% lift the test has about a 10% chance of seeing it, and most "winners" it declares are noise.

The call is an 80% chance to win, Bayesian (Jono, 3 October 2026: "one in five odds of failure, four in five odds of success"). A small business cannot wait a year for 95%. One call in five will be wrong, and that is the price of calling in weeks. Planned at 80% power, leads per variant is about 6 divided by the lift squared. The baseline rate cancels out.
- a +20% lift needs about 145 leads a side
- a +30% lift needs about 70
- a +50% lift needs about 27
- a +10% lift needs about 560, which nobody at this traffic can afford
- a test runs 8 weeks at most; neither page at 80% by then is a tie: keep the control, test something bigger
Below about 30 leads a side the read takes months. Say so, and start anyway with a whole-page change big enough to show sooner. A slow test that runs beats a fast one that never starts (Jono, 25 September 2026).

Say what the read is worth, in the same breath. At 20% power and a 10 to 15% base success rate, over half the winners a test declares are false (Kohavi, Deng and Vermeer, KDD 2022). The test runs; it is not read early as though the number meant something.

PostHog's own displayed sample size runs 6 to 17% low (one variance term); treat its "complete" as a floor. PostHog shows nothing under 50 exposures and 5 conversions a side, and those are far below any real threshold.

## How many arms, and how many candidates

- Two arms. A third does not cost a third more - it costs 82% more leads in total (349 to 634 at a 30% target), because the extra arm needs its own sample and Bonferroni raises every arm's threshold.
- Below 300 leads a month a third arm is refused. At or above 300 it is offered with the corrected numbers and an explicit yes.
- Multivariate never: seven axes is about 49,000 leads, 162 years at 300 a month.
- Draft three whole pages, build ONE. Drafting widens the search nearly free; running more pages is what costs.
- The pick is made on observable properties only - the noticeability gate, then the evidence tier, then build cost.
  - Never on predicted lift: an LLM judge scored kappa 0.141 against 330 real tests, and 44% of a well-known case library's labels come from non-significant tests.

## Evidence tiers, logged every time

- Tier 1: our own prior significant result, or a pattern replicated in significant tests.
- Tier 2: a session replay of non-converting visits, form-field drop-off, or a sales-call objection.
- Tier 3: user testing with 5 to 10 people, or an exit survey.
- Tier 4: a heuristic read of the page's own shape, with no outside evidence.
- Tier 4 is legitimate for a first test on a never-tested page. It is recorded as tier 4.
- Heatmaps are not evidence below 300 leads a month; the sample is too small to read. Session replays and form analytics are.

## The challenger is derived, not invented

`python3 code/audit/invert.py <url>` reads the control and writes `context/pages/<slug>/challenger-brief.md`. Ten axes, ranked by what moves a number - what the page SAYS first, how it is built second, design last.

- 1 · The benefit it leads on. The biggest lever on the page.
  - Which of the nine buying motivations the hero sells, read from the page's own copy (`code/audit/motivations.py`).
  - The challenger leads on the strongest one the page never mentions.
- 2 · The features backing it, rewritten so each one proves the new benefit.
- 3 · The offer. The same deliverable stated as a different promise.
- 4 · The guarantee. The same risk reversed a different way - money back against we keep working free.
- 5 · The images. Real work and real faces against staged or stock.
- 6 · The form. Two fields in the hero against four with a qualifier after the proof.
- 7 · Length. Long against short.
- 8 · The FAQ. Which objection gets answered.
- 9 · Layout and order. Reversed after the hero. Cheapest to move, which is why it is near the bottom.
- 10 · The page style. Flips: calm to bold or bold to calm, same brand. Two pages in one style read as one page (Jono, 28 September 2026).

Reframing the offer or the guarantee is a legitimate test, not a change of business: "30 leads in 30 days or your money back" against "we work free until you get them" is the same promise with different risk framing.

Social proof never flips (Jono, 28 September 2026). Both arms carry the same testimonials, reviews, case studies, logos and client videos. Removing proof handicaps an arm; it is not a test.

What else never flips: a claim, number or testimonial not in `context/proof.md` · a promise the business cannot deliver · the form handler, the thank-you page and the tracking. The page style flips.

The three candidate cuts: **say something else** (benefit, features, offer, guarantee), **show something else** (images, FAQ), or **the opposite page** (everything but design - the default at low traffic).

⛔ Never build the challenger with `/audit`. That command builds the best page it knows, so both arms converge and the test asks nothing.

## What to test - the whole page, not the button

While you know nothing about what works, the two variants are massively different pages: a different structure, the form beside the founder video, a short page against a long one, proof first against offer first. Bigger effect, smaller sample - it is the only thing that makes low-traffic testing viable. Green button against orange button is 600 clicks spent learning nothing. Once the structure is settled, test inside it.

The unlock at low traffic: pool one identical structural variant across every page and every client in the same trade. Ten sites at 30 leads a month is 300 pooled; a 26-month test becomes a 3-month one. Segment by `$host` for reporting only.

## How the split works in this repo

- One URL.
  - The middleware gives every browser a `ph_did` cookie.
  - The server asks PostHog which variant that id is in, renders it, and hands the browser the same answer as a bootstrap.
  - Nothing flickers, nothing redirects, no alternate URL, no noindex change.
- `website/app/lp/_split-template/` is the shape: `VariantA.tsx` is the page you have today, moved unchanged
  - `VariantB.tsx` is the challenger; `page.tsx` renders whichever `<Variant flag="lp-<slug>">` returns.
  - `<Exposure>` records `$feature_flag_called` from the browser.
- Every event the browser sends carries `$feature/lp-<slug>`, so leads know their variant.
- `python3 code/split_test.py --create <slug>` makes the flag (multivariate control/test at 50/50, one release group at 100%, continuity off, bucketing on distinct_id)
  - and the experiment (type web, primary metric a funnel on the "Lead (form, call or text)" action, secondaries form-only and calls-only, MDE 30%) and launches it.
- Until the flag exists every visitor sees VariantA, so copying the folder is safe before the test starts.

## Running it

- Decide the run length before launch: whole weeks, two minimum, eight maximum. Weekdays and weekends both have to count.
- Once launched, never touch the flag, the rollout, the variants or the page. A change means end the test and start a new one.
- Check the split every week: `python3 code/split_test.py --status <slug>` prints visitors and leads per variant, the split check (SRM
  - chi-square, broken under p 0.01), the observed lift, the probability the test is better, the leads still needed, and the call.
- Read it weekly, not daily. Stopping at the first green day inflates false winners to around 26%.
- An A/A test is optional: `--create <slug> --aa`, both variants the same page.
  - It checks the counter, not the call: at an 80% bar, two identical pages name a "winner" about two times in five. The split check should say ok and both arms should log leads.
  - Run it whenever a result looks too good.
- Ship: the test has an 80%+ chance to win, 50+ visitors and 5+ leads a side, two full weeks, split not broken.
  - Plan on the lift after a 13% winner's-curse haircut, never the point estimate.
- Kill: the control has an 80%+ chance to win, under the same checks. Three flat reads of one idea also kill it.
- Keep going: neither page at 80% yet, inside 8 weeks; say how many days are left.
- Tie at 8 weeks: keep the control, log it flat, claim no lift, build a bigger change.
- The read happens when you run `--status`; nothing is scheduled.
- `python3 code/split_test.py --stop <slug> --winner test` ships the winner to everyone.
  - Then move the winner into `page.tsx`, delete the loser, delete the flag - in the same sitting.

## Expectations, so nobody quits after three flat tests

Microsoft across all experiments: a third win, a third flat, a third lose. Mature products are worse. Across 115 published tests the average lift was about 4%; two larger sets agree - a median winner of +1.88% across 90+ brands and a mean of 3.77% across 85 tests. The widely-quoted "49% average lift on lead-gen" is a vendor self-report with no sample size and does not survive contact with any measured dataset. Twenty tests a year at a 15% win rate is about three real winners; a realistic year is a 10 to 25% improvement, not a doubling. The first test is the biggest win you will ever get and every one after it is smaller - that is fine, ten small wins is a page that converts three times better.

The lifts do not add up (selection bias, interaction, novelty decay). Above about 1,000 leads a month, hold 5 to 10% of traffic on the original page for a year; that one number is the programme's real score. Below that, do not bother with a holdout.

## Rules

- Call it at an 80% chance to win, Bayesian. A tie at 8 weeks. Never refuse a test for low traffic: print the weeks and start.
- Structural variants only. Never a single element while the structure is unproven.
- Default lift to plan for: 30%. Never below 20% under 300 leads a month.
- The variant is decided on the server. The browser never decides it.
- One URL, no redirects, no noindex changes, canonical to itself. Google sees one page.
- New versus returning before shipping: a lift concentrated in returning visitors gets two more weeks.
- Identify a person only at submission, after exposure, never before.
- Log every test in `context/test-log.md`: date, slug, the hypothesis in one line, the two pages, planned leads, the weekly reads, the call, what shipped.
- The hypothesis is not invented here. It is the top item's "We believe" line in `context/test-queue.md`, used unchanged, so the test answers what the visitors actually showed.
- On SHIP or KILL, the matching block in `context/visitor-findings.md` changes status to won or lost in the same sitting.

## The shape of a queue item

`/analytics` writes them, worst first, and `/split-test` reads the top one. Each item carries:
- We believe: the structural change lifts leads by X% because of the evidence, with counts
- Quiet exits: how many of the quiet sessions showed it
- Converted: how many of the converted sessions showed it
- Read: the date of the read it came from
- Status: queued, running or called

A queue item with no counts behind it is an opinion that skipped the read. Send it back.
