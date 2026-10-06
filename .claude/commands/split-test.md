---
description: Two pages at one URL, PostHog flips the coin, leads decide - wires PostHog itself from one key, builds the challenger, proves the scripts fire on both pages, launches today, and reads the result whenever you ask
argument-hint: [slug] [status | stop --winner test|control | aa]
---

The testing machine: $ARGUMENTS

**Read first:** `references/split-testing.md` - the lead math, structural variants, the run rules, how a result is read. And `references/posthog-setup.md` - step 0 and the manual stops.

**Two rules, and the first one is absolute.**

⛔ **THE KEY GATE. Without the PostHog personal API key in `.env`, this command does NOTHING.** No math, no hypothesis, no challenger page, no side-by-side screenshot, no log entry, no file written or copied anywhere. A split test with no flag is not a split test, and a "drafted" one is worse than none: it reads as work done and it measures nothing. The only output of a keyless run is the ask.

**Otherwise nothing waits (Jono, 25 September 2026).** No lead-count gate, no mandatory A/A test. Low traffic means the command says how long the read will take and starts anyway.

⛔ **But it says what the read will be worth, in the same breath.** At 20% power and a realistic 10 to 15% base success rate, more than half the "winners" a test declares are false (Kohavi, Deng and Vermeer, KDD 2022). So when the planned sample is months away, the first line says so plainly: how many leads a side, how many months, and that a result called before then is a coin flip with a confidence interval drawn on it. Start the test; never let it be read early as though it meant something.

## STEP 0. The key, or nothing

Read `.env` for `POSTHOG_PERSONAL_API_KEY` and `POSTHOG_PROJECT_ID`, and CLAUDE.md "## My setup" for a TRACKING VERIFIED date.

**Connected and verified in the last 30 days:** skip to step 1.

**Not connected:** your ENTIRE first reply is the manual stop block from `references/posthog-setup.md`, in its words, and nothing else. Do not run `sample_size.py`. Do not open the queue. Do not copy `_split-template`. Do not write `context/test-log.md`. Do not screenshot anything. Do not describe the test you would build. Then stop and wait for the key. The 25 September 2026 run built a whole challenger page first, reported "split pair built, test not started", and PostHog was never wired - that is the failure this gate exists to prevent.

**When the key lands,** with no further questions: `python3 code/posthog_setup.py --connect --key phx_... --enable --dashboard`, then `python3 code/dev_server.py --restart`, then `python3 code/check_tracking.py http://localhost:3000/lp/<slug>` until it passes (fix every FAIL here), then write "## My setup". Only then step 1.

`/split-test status <slug>` and `--stop` obey the same gate: no key, no read.

## STEP 0b. The page's phone number, and the call webhook

A page under test converts by phone as well as by form, so the calls have to land in PostHog before the test starts. Ask for this in the same first message as the keys, as one numbered line:

> **Two GoHighLevel phone numbers for this test.** GoHighLevel, Settings, Phone numbers, buy two and forward both to the line you actually answer. One goes on the control, one on the challenger - that is the ONLY thing that can tell a call from page A apart from a call from page B, because GoHighLevel never sees the browser. With one number on both pages, calls are the page's total and the test is decided on form submissions alone. Paste both numbers.
>
> Only want one number? Say "one" and paste it. Calls then count for the page, not per arm, and the report says so every time.

Already recorded in CLAUDE.md "## My setup" for this page: do not ask again.

When it lands, with no further questions:
1. Generate `CALL_WEBHOOK_SECRET` (16 hex characters) into `website/.env.local`, and set the same value in the host's environment variables (`vercel env add CALL_WEBHOOK_SECRET production preview development`).
2. Put a number on each page: the control's number in `VariantA.tsx`, the challenger's in `VariantB.tsx` - the hero, every call button, the mobile bar. Each page shows exactly ONE number; `score_page.py` fails a page carrying two.
3. Write `CALL_NUMBER_MAP` into `website/.env.local` and the host, so a call knows its arm: `CALL_NUMBER_MAP=<control digits>=lp-<slug>:control,<challenger digits>=lp-<slug>:test`. One number given: leave it empty and say in the report that calls are the page total.
4. `python3 code/dev_server.py --restart`, then prove the route with the payload GoHighLevel sends: `curl -s -X POST "http://localhost:3000/api/call?secret=<secret>" -H "Content-Type: application/json" -d '{"phone":"+15555550123","customData":{"phone":"<the challenger number>"}}'` and expect `"counted":true` and `"variant":"lp-<slug>=test"`. Repeat with the control number and expect `=control`. Every call MUST count, missed or not.
5. Print the setup block below, filled in, and stop until they confirm the workflow is saved.

**The walkthrough to hand back, with the real values already filled in.** They have never seen a webhook. Number every click, name every screen, and never write a placeholder they have to work out - paste the real URL, the real secret, the real numbers.

> **Part 1 · Buy the two numbers** (about 3 minutes)
> 1. In GoHighLevel, click **Settings** in the left sidebar, then **Phone Numbers**.
> 2. Click **Add Number**, pick your area code, and buy one. Do it again so you have two.
> 3. Click the first number. Under **Forward calls to**, enter the phone you actually answer. Save. Do the same for the second.
> 4. Copy both numbers and paste them to me. The first goes on the control page, the second on the challenger.
>
> **Part 2 · Make the workflow that tells the website about a call** (about 5 minutes)
> 1. Click **Automation** in the left sidebar, then the **Workflows** tab, then **Create Workflow**, then **Start from Scratch**.
> 2. Name it `Call to website` at the top, so you can find it later.
> 3. Click **Add New Trigger**. Search for **Call Status** and choose it.
> 4. Under **Filters**, add ONE filter: **Direction** is **Inbound**. **Add nothing else.** No duration filter, no "answered" filter - a missed call is still a lead, and the website decides what counts.
> 5. Click **Save Trigger**.
> 6. Click the **+** under the trigger, then choose **Webhook** (it is under Developers or External).
> 7. Set **Method** to **POST**.
> 8. Paste this exact address into the **URL** box:
>    `<the live URL>/api/call?secret=<the real secret>`
> 9. Under the URL there is a **Custom Data** section. Add ONE row. In the left box type `phone`. In the right box pick the number they rang, the split-test number, from GoHighLevel's variable list (click the **{{}}** icon and search for it). That number is what tells us which page they called from. You do not add the caller's number: GoHighLevel sends it on its own, as the contact's phone. (Jono, 29 September 2026.)
> 10. Click **Save Action**, then the **Publish** toggle at the top right so the workflow is live. A saved but unpublished workflow sends nothing.
>
> **Part 3 · Prove it works** (about 1 minute)
> 1. Ring the FIRST number from your mobile and hang up as soon as it rings. Do not answer it.
> 2. Tell me you have done it. I will check PostHog and read back what arrived: the number you rang, that it was recorded as a lead, and that it shows as a missed call.
> 3. If nothing arrives, the usual cause is step 10 - the workflow is saved but not published.
>
> **What this counts, so there are no surprises later:** every inbound call GoHighLevel sees, on either number. Missed calls included - the person raised their hand and their number is in your CRM to ring back. Whether you answered is recorded beside it as its own number, never as a filter on the lead count. One person ringing five times is one lead.

## STEP 1. The math, as information, not a gate

`python3 code/sample_size.py --baseline <current rate> --lift 0.3 --leads-per-month <leads a month>` (read both from `analysis.md` or PostHog; if unknown, use the vertical median from `references/analysis.md` and say so). Put the answer in one line: "A +30% lift shows in about N months at your lead rate. A whole-page change can move 50%, which shows in about M." Then start. Never refuse a test for low traffic; a slow test that runs beats a fast one that never starts. Low traffic is the reason the challenger is a different PAGE, not a different button.

## STEP 1b. Two arms, and why not five

A third page does not cost a third more traffic - it costs 82% more leads in total, because the extra arm needs its own sample AND Bonferroni pushes every arm's threshold up. `python3 code/sample_size.py` prints the curve: at a 30% target, 349 leads for two arms, 634 for three, 1,239 for five. At 30 leads a month that is 12 months against 21 against 41.

- Below 300 leads a month: two arms. Refuse a third and show the months.
- At or above 300 a month: a third arm is defensible. Print the corrected sample, the months, and the delta against two arms, then require an explicit yes.
- Multivariate: never. Seven axes is about 49,000 leads, which is 162 years at 300 a month. Refuse; do not price it.

Drafting three whole pages is nearly free and happens in step 2. Running several pages is what costs.

## STEP 2. The hypothesis and the challenger

Take the top item of `context/test-queue.md` (written by `/analytics`, worst first) and use its "We believe" line as the hypothesis, unchanged - it already carries the counts behind it. Only when the queue is empty: the LEAVE the most buyers share, or the biggest FAIL on the scorecard, written into the same shape. Structural means the whole page: order, hero shape, form beside the founder video, short against long, proof first against offer first.

⛔ **GATHER THE EVIDENCE BEFORE THE FIRST QUESTION (Jono, 28 September 2026).** The old interview read only the audit, so every recommendation was a guess. Three better sources already exist for most pages.
- `python3 code/audit/evidence.py <url>` prints, axis by axis, what each source says. `challenger.py` reads it too.
- **The visitors.** The heat map, the scroll map, the click map, rage and dead clicks, where the form dies, and the ten recordings.
  - It reads the newest `context/sessions/<date>.md` for this page, plus open items in `context/visitor-findings.md` and `context/test-queue.md`.
  - No read of this page, or one over 30 days old, and PostHog shows 50+ sessions on it: run the /analytics read first.
  - That is `read_sessions.py` on the control. The key gate already passed, so nothing new is needed.
  - Under 50 sessions: say the count in one line and go on. Never wait for traffic.
- **The buyers.** The approved files in `context/personas/`: silent question, what they buy on, leave moments, verbatim call lines.
  - An unapproved file is a draft and never counts.
  - No approved buyers: one line saying so, and that /personas builds them. Go on.
- **The research.** `context/voc/` from /personas: what buyers say (Reddit, reviews), what the best rivals sell, the facts the page may use, and the three reasons people buy.
  - `python3 code/check_voc.py` must PASS. Missing: one line saying /personas step 1c writes it, then go on with what exists.
- **The panel's read of the control.** How each buyer reacted, section by section, in `context/pages/<slug>/persona-read/`.
  - Approved buyers but no read of THIS page: run the /personas read, its STEP 3, on the control first.
  - A read of another page, even the control's v2, is not evidence about this one.
- Weight, highest first:
  - what visitors did
  - what buyers said on real calls
  - how the panel reacted
  - The panel is a simulation. It catches confusion and friction; it cannot predict conversion.
  - Label it that way every time: "Ivan said on a call" is evidence, "the panel's Ivan left at section 4" is a simulation.
- Say what was gathered and what is missing in one short block. Then ask the facts, and only the facts.

⛔ **Each source has one job (Jono, 28 September 2026).**
- **The visitors decide what gets fixed or cut.** `python3 code/audit/visitor_fixes.py <url>` applies four rules, and none of them is a question for the owner:
  - A click on something that is not a link: make it scroll to the form, or stop it looking clickable.
  - A form field people quit on: remove it. First name, last name, email and phone are fixed instead, never removed.
  - A section that loses far more people than the rest: cut it or shrink it. Social proof is moved higher instead, never removed.
  - A link that takes people off the page: remove it. Privacy and terms stay, small, in the footer.
- Clicks, leaks and a broken contact field are bugs. They are fixed on both arms before the test starts, through the deploy gate.
- A removed field and a cut section change the page's shape, so they go on the challenger only.
- Under 50 sessions, only the audit's leaks are forced. The rest waits for traffic, and the brief says so.
- **The buyers decide the words and the emotion.** The brief's "Written for the buyers" block is the copy guide for VariantB.
  - The page sells in their order: the moment they started looking, the question they will not ask, what they buy on, every leave moment.
  - Every draft and every sidebar option uses the buyers' own language: the benefit, the headline, the offer, the guarantee, the three benefits, the button, the FAQ.
  - Borrowed words are phrasing. Never print a buyer line as a quote or a testimonial.
- **The panel only catches confusion.** It never decides a change on its own.

⛔ **ONLY ASK WHAT THE RESEARCH CANNOT ANSWER (Jono, 28 September 2026: "we shouldn't ask questions that are going to be overridden by that anyways").**
- The evidence above answers the taste questions: which benefit leads, the headline, the order, the length, the sections, the button. Never ask the owner those.
- Ask only the facts a page needs that only the owner holds.
  - Read `context/proof.md`, `context/business.md` and any `context/voc/facts.md` first.
  - Ask only what is blank there, or where two files disagree. Name both versions in the question.
- The usual gaps:
  - the offer and the guarantee they will stand behind. Write the winning one and ask them to back it.
  - the price, and how it is paid
  - how fast they call back, once that is real
  - years in business, clients served, the legal address
  - which owner-supplied things exist: a founder video, review scores, client logos, client videos, photos
- One `AskUserQuestion` per fact. When there are more than four, ask them as one numbered list in text.
- A skipped fact becomes a slot with its fallback. The drafts go on without it.
- The fifteen axes are no longer questions.
  - `python3 code/audit/challenger.py <url>` still writes them to `challenger-interview.md`.
  - They are raw material for the drafts, and after the pick, for the sidebar.

⛔ **THE ORDER: THE QUESTIONNAIRE, THREE PAGE TYPES, LOCK ONE, THEN THE WORDS (Jono, 28 September 2026).**
1. The questionnaire: the offer, the guarantee and the facts only the owner holds (the rule above).
2. The big picture: three big ideas, each with a message map.
   - The map says what the page must say, in what order: the offer, the guarantee, the three benefits, the proof, the objections.
   - One pool of talking points feeds all three, so none can invent a claim.
   - Every point lives in one section. A second mention goes only at the close.
3. The structure follows from each map, with the blueprint's skeleton as the default.
4. The words come last, in the picker, after the owner locks one page type.
- Only one challenger runs. Three live pages need about three times the traffic (STEP 1b), so three are drafted and one is built.

⛔ **THE POOL AND THE THREE MAPS.**
- The pool: `context/pages/<slug>/drafts/points.json`. Every fact, proof point, buyer worry and research angle, each with its source.
  - A promise not on file says `"source": "ask the owner"`. It ships only with their yes.
  - A point that carries a blueprint component says so: `"component": 4` for the offer, `20` for the guarantee.
  - The pool carries the business's own words, as `"vocabulary"`. The sell filter reads them, so a DJ's lines are not judged on a plumber's words.
    - `concrete`: the things its buyer can picture. For a DJ: dance floor, first dance, playlist.
    - `reasons`: the words of why they buy and what they fear, from `context/voc/reasons.md` and the personas.
  - The three reasons people buy, from `context/voc/reasons.md`, go in as points marked `"reason": 1`, `2` and `3`.
- The maps: `draft-A.json`, `draft-B.json` and `draft-C.json`. Each is a big idea, a buying motivation, the ask (call or form first) and its message map.
  - Each leads on a different one of the nine motivations below, and opens on different points.
- `python3 code/audit/drafts.py check context/pages/<slug>/drafts` must PASS.
  - Each map: an offer in the hero, a guarantee, three benefit sections, one home per point, every component placed.
  - No point repeats another point's words elsewhere on the page. "What is included ... and a backup DJ" fails beside a first screen that already promises the backup DJ.
  - The three benefit sections are the three reasons people buy, one each, on every page type. The pages differ in which reason leads, never in which three.
  - Across the three: different motivations, big ideas, first screens and section orders.

⛔ **THREE REAL SWINGS, NOT THREE ORDERS (Jono, 28 September 2026: "should they be much more different?").**
- A visitor notices the first screen, the length and where the form sits. The order of the middle barely registers.
- So each page type differs in all four, set in its map file:
  - the first screen: the form beside the headline, the founder video beside it, or centred over a wide video
  - the length: one short, one medium, one long. Client videos and reviews fill to the blueprint's floor on the short one and its top on the long one.
  - the form: in the first screen on one of them
  - the look: paper, the blue field, or dark ink, all from the owner's kit
- `drafts.py check` refuses three that share a look or a length.
- The sidebar says what is different about each page's structure, never the page's own words again.

⛔ **THE PICKER: THE OWNER CHOOSES, THE SCORES ADVISE (Jono, 28 September 2026).** `python3 code/audit/picker.py context/pages/<slug>/drafts` writes `drafts/picker.html`, a dashboard like the audit report. Give its full path.
- The three page types, drawn in the owner's design kit with generic words.
  - Their proof is the owner's own (Jono, 29 September 2026: "anyone can run the skill, I don't want it built on my social proof").
  - `drafts/proof.json` holds the business name, the phone, the reviews word for word, the client videos and the faces.
  - It is written from `context/proof.md`, the quote bank and `context/business.md`.
  - It also says what the form's button reads, what they get for filling it in, the thank-you page's next steps and the client names for the logo row.
  - Nothing missing is borrowed. An empty list is a placeholder on the page.
  - Every one of the 26 components is on each, with placeholders for what the owner supplies, drawn the way `Slot.tsx` draws them.
  - Sample review badges from Google, Trustpilot, G2 and Trustindex, tagged as samples, until real scores exist.
  - The owner rotates between the three, on a computer or a phone view, and locks one in.
- Then they click a section. Its options are ranked by overall score, best first. The page changes as they rotate.
  - The top three show (Jono, 28 September 2026: "they're 10 variations of the same message - I think 3 is fine"). The other seven sit under "Show 7 more".
  - Ten are still written, so the buyers have enough to rank.
  - Each option shows its whole text: the line above, the headline, the words under it and every bullet.
  - Every option shows five scores out of ten: will they stay (the buyers), the reading grade, the length, benefits and outcomes over features, and how clear it is.
  - One to three options per section are marked ideal: the best thing to say, even before the proof is on file. Each says what it needs. They may already have it.
  - A "write your own" box sits under every section's options, scored as they type.
- The big idea heads the sidebar. A live check flags any point said twice across the whole page.
- Promises a page type makes that are not on file are asked plainly: "Can you promise these?", yes or not yet. The answers go into the picks.
- The 26 components are listed in groups: in place, placeholder, sample, every page, not needed.
- The numbers strip has its own picker. The owner ticks up to four.
  - The choices: every number on file, plus the blueprint's own (years in business, the rating, jobs done, clients served).
  - A number not on file is a placeholder that says what it needs.
  - The pool's `"stats"` list holds them: `{"id", "value", "label", "source"}`, or `"needs"` in place of a source.
- The thank-you page is drawn after the form, with the form's answers in it.
  - The owner ticks that a real test lead went through: it arrived, they landed on the thank-you page, the conversion fired once.
  - Downloading the picks without that tick asks them to send one first.
- "Download my picks" saves `picks.json`. Page B is built from exactly those.

⛔ **CHECK THE PICKER BEFORE THE OWNER SEES IT (Jono, 28 September 2026: "make sure it works properly every time").**
- `python3 code/audit/picker_check.py context/pages/<slug>/drafts` must print PASS before the owner gets the path.
- It checks the words: the maps, three options that sell in every section, every buyer's scores.
- It clicks through every page type headless, on a computer and a phone.
  - Nothing said twice, no headline past three lines, nothing scrolling sideways.
  - The options, "write your own", the numbers strip, the promises, the thank-you page and the download all work.
- A FAIL is fixed and the check run again. Never hand over a picker that has not passed.
- After any change to the picker's code, `python3 code/audit/picker_check.py --selftest` must pass too.
  - The self-test builds a made-up business's page and fails if anyone else's name, number, review or video shows on it.

⛔ **WRITING THE OPTIONS.** Ten per section, at least eight different angles, written from:
- the pool and `context/proof.md`
- the buyers in `context/personas/`, in their words, never quoted as a testimonial
- the online research: `context/voc/reddit.md`, `rivals.md` and `reviews.md`
- `references/persuasion.md`: the fears, specificity, their words, grade 5 to 7
- When `context/voc/options-judged.json` has a section like this one, its top-ranked PASS option is one of the ten.
- `python3 code/audit/drafts.py needed context/pages/<slug>/drafts` writes the writers' brief, `drafts/options-needed.json`, from the three maps.
- Four writer subagents, in parallel. Their prompt is brief 1 in `references/picker-briefs.md`, verbatim.

⛔ **EVERY OPTION HAS TO SELL (Jono, 28 September 2026: "If things aren't able to sell customers, filter them out and try again").**
- `python3 code/audit/sell_filter.py context/pages/<slug>/drafts` runs ten gates on every option. The list is in its header.
- A failure goes to `drafts/rejected.json` and back to its writer, and is rewritten until every section has ten that pass.
  - `drafts/rewrite.json` lists exactly which options: the writers rewrite those (brief 3), the buyers re-score those (brief 4).
  - When buyers pull in different directions, the rewrite is a merge: one line that keeps one buyer's reason and brings the others in. On Northside DJs that took 69 rejected options to 14 in one round.
- The buyers re-score only what was rewritten. Three rounds at most.
- A section still short of ten after three rounds says why in one line: usually proof the owner does not have yet, like a map pack result. More words will not fix that.
- The picker hides anything that fails. Nobody chooses between lines that cannot sell.

⛔ **THE BUYERS SCORE EVERY OPTION.** One subagent per paying buyer, fresh context, its own persona file and the options only.
- Each writes `drafts/scores-<buyer>.json`: for every option, how likely they are to leave at that section, 0 to 10.
  - Their prompt is brief 2 in `references/picker-briefs.md`, verbatim.
- The picker averages them into the "stays" score, every buyer counting the same (Jono, 29 September 2026). Unapproved buyers are labelled a draft.
- The scores advise. The owner decides.

**Every option, in a map or in the picker:**
- ⛔ **Show the words, never the pattern.** An option quotes what is on their page today and what it becomes.
  - Wrong: "Each line finishes the chain: we do X, which gives you Y." That is a technique, and it confused the first person who read it (Jono, 28 September 2026).
  - Right: their real line, "Rebuilt, so you show in the map pack", then the rewrite, "...meaning calls from people ready to book today".
  - If an option cannot be written with their own copy in it, it is not ready to show.
- ⛔ **Social proof never rotates (Jono, 28 September 2026).**
  - Both arms carry the same testimonials, reviews, case studies, client logos and client videos.
  - Taking proof off one arm is not a test. It handicaps that arm and teaches nothing.
  - A draft can move the proof. It cannot change it, add it or take it away.
  - The portfolio is their own work, not social proof, so it can still rotate.
  - Frozen never means fake. Anything fabricated in it is replaced with the real thing or cut, on both arms. See the rule below.
  - Each person appears once on a page. A case-study client is not also a review, on either arm.
- ⛔ **List every real option (Jono, 28 September 2026).** Nine real angles are never cut to four. The sidebar holds as many as the section genuinely has.
- **The nine motivations, in full, wherever the question is why someone buys.**
  - Make me money. Save me money. Save me time. Save me effort.
  - Make it safe to say yes. Tell me exactly what happens.
  - Stop the pain I am in now. Give me my life back. Make me look good.
- **The three-benefit block.** Each draft picks its own three from the nine. The sidebar offers all nine.
- **Every option carries a recommendation,** first and marked "(Recommended)", with the reason.
  - The reason cites the strongest evidence, by source: "7 of 10 recordings stopped at the office photo", "Ivan on a call: where's my phone number?".
  - With no visitor, buyer or panel line behind it, the reason says "no evidence on file, this is a heuristic".
  - It is a starting point, not a verdict. Picking winners by taste is near-chance, so it says WHY, and the owner overrules it freely.
  - When nothing is clearly better, say so rather than inventing a preference.
- Every option carrying a number is drafted from `context/proof.md` only. Without proof behind it, the number goes in [brackets] as a question.

⛔ **PAGE B MUST LOOK LIKE A DIFFERENT PAGE (Jono, 28 September 2026: "these pages look very very similar... how can I really make this feel like a split test").** The first challengers kept the control's fonts, colours, components and words, then reshuffled them. A visitor could not tell them apart.
- Page B uses the design kit's other page style. The control is calm, so page B is bold, or the other way round.
  - Same brand tokens. Different colour coverage, alignment, density and tone.
  - The two styles are described in `design/kit/readme.md` under "Two page styles ship".
- Page B starts from a blank file. Never copy the control's code, section by section, and never edit its sentences into new ones.
- Change the three things a visitor sees in five seconds: the offer, the ask (call first or form first), and the first screen.
- The shared proof keeps its content. Each arm draws it in its own style from the same data in `proof.tsx`, so the words cannot drift.
- The five-second gate: put both first screens side by side. A stranger must name three differences in five seconds, or page B is not ready.
- The three page types each open differently, so locking one already picks the first screen.

⛔ **BUILD PAGE B FROM THE PICKS (Jono, 28 September 2026).**
- Phase one is the structure: the locked page type. Phase two is the words: the owner's picks. Both happen in the picker.
- Page B is built from `picks.json` exactly: each section's chosen or own words, in the locked order.
- An ideal line goes live only once its "needs" is on file. Until then its slot keeps the fallback.
- When the owner names a design kit, page B uses it, scoped to page B alone (a `series.css` under one class), so the control keeps its look.

⛔ **WHAT THE OWNER SUPPLIES IS A SLOT: NEVER INVENTED, NEVER LEFT OUT (Jono, 28 September 2026: "if they don't have it, there's a fallback value").**
- `components/lp/Slot.tsx` draws each one. Page B's slots live in `slots.ts`; the social-proof slots live in `proof.tsx`, shared by both arms.
- Filled, a slot shows the real thing. Empty, visitors see an honest fallback, or nothing.
- The dev server draws every empty slot as a dashed, labelled placeholder, with what to add and what visitors see meanwhile.
- Visitors never see an empty play button, a blank logo row or a stand-in face.
- `python3 code/check_placeholders.py website/app/lp/<slug>` lists the empty slots as the owner's to-do. Empty slots do not block launch; `[bracket]` copy still does.

⛔ **PAGE B IS BUILT TO EVERY `/audit` RULE (Jono, 28 September 2026).** The first interview-built challenger kept stand-in faces on its reviews, because it only followed the interview.
- Read `.claude/commands/audit.md` before writing a line of page B: every ⛔ rule in STEP 1, and the Never list in STEP 3.
- The picked draft decides WHAT changes. The `/audit` rules decide HOW every section is built.
- Where the two clash, the rule wins. The file's header comment names each answer that moved:
  - The headline keeps the service and the city. The drafts rotate the line above it and the line under it.
  - ⛔ The form always asks the four: first name, last name, email, phone (Jono, 28 September 2026).
    - Never fewer, unless the owner says so in words.
    - A draft can move the form and change what comes after the four, never the four themselves.
  - The three benefits are three sections. Each has bullets in the chain, a client's own words beside it, and both ways to act.
  - No band that is only a line and a button. Under every button: the reply time, and that the call costs nothing.
  - A slot nothing real can fill is cut, never left as an empty frame.
  - ⛔ Every one of the 26 components is on page B, filled to its count with slots (Jono, 28 September 2026). The counts are in `audit.md`.
  - The first screen runs in the order `audit.md` sets: pain line, offer headline, the line under it, ticks, badges or logos, both buttons.
- ⛔ **It has to look finished, not just pass the rules (Jono, 28 September 2026: "it just doesn't look good. Period.").**
  - Build every section from the kit's own layouts, like the two-up in `_template`: a picture or a graphic on one side, every word on the other.
  - Never strand a heading on one side with its content on the other. Never leave half a section empty.
  - The form button and the phone sit side by side on a computer, and as two equal full-width rows on a phone. Never one under the other in a narrow column.
  - No real picture for a section? Draw a graphic from the kit's tokens that shows the idea, with no names, stars or numbers on it. Stock is the last resort, and named where it sits.
  - Then screenshot every section at phone and computer width and look at each one. Anything that looks unfinished is fixed before anyone else sees the page.
  - Read every word as a stranger too, by the "read it as a stranger" rules in `audit.md`. A page can pass every check and still read like a four out of ten.
- ⛔ **Fabricated proof is fixed on BOTH arms before the test starts.**
  - It covers a stand-in face, a made-up logo, a rating or stars with no platform behind them, a stock photo under "our work", and a play button with nothing behind it.
  - Each is replaced with the real thing, or cut. Real means repo photos, the owner's own site, and the case-study videos.
  - Put the shared proof in one file both arms import, `website/app/lp/<slug>/proof.tsx`, so it cannot drift.
  - Changing the control this way is a bug fix, not a test change. It ships through the same deploy gate.
- ⛔ **Then prove it with `/audit` STEP 4, on both arms.**
  - Run the full audit, judged, on `<url>?preview=control` and `<url>?preview=test`, each with its own `--out`.
  - Page B's score is at least the control's.
  - No section of page B shows a stand-in.
  - `check_placeholders.py` and `check_page_quality.py` pass.
  - Anything that fails is fixed before the difference score runs.

**Then** write the picked draft's choices to `context/pages/<slug>/answers.json`, keyed by axis, and run `python3 code/audit/challenger.py <url> --answers <that file>`. It writes the build brief: what changes and the evidence each change rests on, what stays, the visitor fixes, the buyer copy guide, and any conflict worth settling first (asking for a tighter page and more sections at once is the common one). Show me the brief before a line of code.

⛔ **Do NOT run `/audit` to build the challenger.** That command builds the best page it knows, so both arms converge on the same shape and the test asks nothing.

**What flips:** what the page SAYS as well as how it is built. Reframing the offer or the guarantee is a legitimate test: "30 leads in 30 days or your money back" against "we work free until you get them" is the same business, the same promise, different risk framing.

**What never flips:** the social proof · a claim, number or testimonial that is not in `context/proof.md` · a promise the business cannot deliver · the form handler, the thank-you page and the tracking. The page style is not on this list: it flips.

**The gate - all three, or it is not worth building:** distinguishable in a 5-second side-by-side · adds or removes something rather than only rearranging · the difference is above the fold.

⛔ **THE DIFFERENCE SCORE, once page B is built (Jono, 28 September 2026).** Pages that look alike cannot be told apart at small-business traffic, so the test runs for months and ends flat.
- Run `python3 code/audit/difference.py "<url>?preview=control" "<url>?preview=test" --page <path> --leads-per-month <N>`.
- It scores 0 to 100: the first screen 30, the words 25, the shape 20, the ask 15, the pictures 10.
- The bar is 50 for a page's first test and drops 10 for every test already called on it.
- Big swings come first, because the big wins are still unfound. Each called test makes the next one narrower.
- The bar never drops below what the traffic resolves:
  - 35 under 60 leads a month, or when the lead count is unknown
  - 25 under 300 leads a month
  - 15 above that
- Under the bar: widen page B with the levers it prints, and score it again. It never goes to STEP 3 under the bar.
- The score goes in the test log beside the hypothesis.
- Calibration, 28 September 2026: the same page scores 0. A `/audit` rebuild of the control scored 44, too similar. The interview-built challenger scored 73.

**The evidence tier goes in the log, honestly.** Tier 1 is our own prior significant result; tier 2 a session read, a form drop-off or a real sales objection; tier 3 user testing or an exit survey; tier 4 a heuristic read of the page's shape. A first test on a never-tested page is tier 4 and that is fine - it is logged as tier 4, never dressed up.

⛔ **Do NOT run `/audit` to build the challenger.** That command builds the best page it knows, so both arms converge on the same shape and the test asks nothing. The challenger is the control's opposite, built to the brief.

**What flips:** what the page SAYS as well as how it is built - the benefit it leads on, the features, the offer, the guarantee, the images, the form, the length, the FAQ, the layout. Reframing the offer or the guarantee is a legitimate test: "30 leads in 30 days or your money back" against "we work free until you get them" is the same business, the same promise, different risk framing.

**What never flips:** the social proof · a claim, number or testimonial that is not in `context/proof.md` · a promise the business cannot deliver · the form handler, the thank-you page and the tracking. The page style is not on this list: it flips.

Build it:
```bash
cp -r website/app/lp/_split-template/* website/app/lp/<slug>/   # page.tsx, VariantA.tsx, VariantB.tsx
```
Move the existing page body into `VariantA.tsx` unchanged. Build `VariantB.tsx` to the brief, with the same components, the same claims and the same handlers. Both variants carry `<SourceCapture />` and `<LeadEvents />` - the PostHog scripts are on both pages or the test measures nothing. Set `flag="lp-<slug>"` in `page.tsx`. Until the flag exists everyone sees A, so this deploys safely first.

Prove both pages, on the dev server, with `?preview=control` and `?preview=test`:
- `python3 code/score_page.py` on each; both pass every machine check. Screenshots side by side.
- `python3 code/check_tracking.py "http://localhost:3000/lp/<slug>?preview=control"` and the same for `test`: pageview, phone tap and form start fire once on each page. A FAIL is fixed here.

⛔ ONE APPROVAL, because real visitors will see page B: the hypothesis, the two screenshots, the planned run length in whole weeks (two minimum, six maximum). Yes starts it.

## STEP 3. Flip the coin, today

1. `python3 code/split_test.py --create <slug>` - the flag (control/test 50/50), the "Lead (form, call or text)" action, the experiment (funnel on that action), launched. Both ids are printed; a flag is created when PostHog returns an id.
2. `python3 code/check_tracking.py "http://localhost:3000/lp/<slug>?preview=control" --flag lp-<slug> --expect control`, then the same with `test`. The exposure event goes out, every event carries the variant, the right page rendered. A FAIL is fixed here.
3. **The host's environment variables, before any deploy.** A live site with no `NEXT_PUBLIC_POSTHOG_KEY` renders both variants and measures nothing. On Vercel: `vercel env ls` from `website/`, and for anything missing, `printf "%s" "<value>" | vercel env add <NAME> production` (repeat for `development`; Preview needs a branch argument the CLI asks for interactively, so leave it unless they use preview URLs). The four that matter: `NEXT_PUBLIC_POSTHOG_KEY`, `NEXT_PUBLIC_POSTHOG_HOST`, `CALL_WEBHOOK_SECRET`, `CALL_NUMBER_MAP`. Read them back and show the list.

4. ⛔ **THE DEPLOY GATE. Never deploy without a yes.** Real visitors are about to be split between two pages, so the person decides when that starts, not the command. Show them, in one message: the two local URLs (`?preview=control` and `?preview=test`), the side-by-side screenshot, the difference score against its bar, the env vars now set on the host, and the exact command about to run. Then ask: **"Deploy this live now?"** and stop.

   On yes: `npx vercel --prod --yes` from `website/`. Not logged in is a manual stop, one line - run `vercel login` (it opens a browser), then say so and the deploy runs. A repo Vercel already watches deploys on push instead; say which route was taken and print the production URL.

   On no: everything stays built and the flag stays unlaunched. Say plainly that the test is not running and what the one next step is.

   Before asking, run `git status` in `website/`. A `vercel --prod` from the folder ships everything in it, so the gate message names any other unfinished work it would carry.
5. `python3 code/check_tracking.py <live url> --flag lp-<slug> --submit --remote` - the flag called, the variant on every event, one TEST LEAD landed in PostHog and the CRM. Deleting that lead in the CRM is the other manual stop; say it. The test has not started until this passes.
6. Prove the calls live, before the owner rings anything.
   - POST GoHighLevel's payload to the live `/api/call` once per number: `{"phone":"+15555550123","customData":{"phone":"<that page's number>"}}`. Each answer must name its own arm.
   - Load the live page a dozen times with no cookie. Each page must show only its own number, and both must appear.
   - Then the owner rings each number once and hangs up. PostHog must show both calls, each on its page. A call with no page means the workflow is not sending `customData.phone`.
7. Link the flag, the experiment, both pages and the live URL.

**Proving it is live, without fooling yourself.** posthog-js filters headless browsers, so a scripted visit renders the right variant but sends no browser event. Check the split by rendering (the page the server returns for several fresh cookie jars should be roughly 50/50) and check delivery by a SERVER event in PostHog (`lead_received` or `call_click_received`, which carry `$feature/<flag>`). For browser events, open the page yourself and watch PostHog's live events. See `references/posthog-setup.md`.

Write the test into `context/test-log.md`: date, slug, hypothesis, planned leads a side, run length, the two screenshots, the flag and experiment links. Then touch nothing - not the flag, not the split, not either page - for the whole run. A change means end and start over.

Want the A/A check first (two identical pages, proves the counter is honest)? `--create <slug>-aa --aa`. Optional. Most people skip it and run one later.

## STEP 4. Read it when you ask

`/split-test status <slug>` runs `python3 code/split_test.py --status <slug>` and prints, right then: visitors and leads per variant, the split check, the observed lift and the haircut lift, leads still needed, and one of four lines - **SHIP** (the test has an 80%+ chance to win), **KILL** (the control has an 80%+ chance), **KEEP GOING** (neither yet, with the days left), **TIE** (8 weeks and neither reached 80% - keep the control, log it flat, test something bigger). Leads are forms, texts and calls, one per person. The calls are the real GoHighLevel calls when the page has a number per arm, the call-button taps only when it does not. PostHog's own experiment page cannot see the real calls, so this read is the one the call is made on. Nothing is scheduled and nothing runs on its own; you run it whenever you want a read, and one line goes into the test log each time. To have the read waiting every Monday: `0 8 * * 1 cd <repo> && python3 code/split_test.py --status <slug> >> context/test-log.md` in `crontab -e`.

Do not read chance-to-win daily and stop at the first green - that inflates false winners to about one in four. Weekly is the rhythm.

SHIP or KILL: `python3 code/split_test.py --stop <slug> --winner <test|control>`, move the winner into `page.tsx`, delete the loser and the flag in the same sitting, then ask before deploying again - the deploy gate applies to shipping the winner too. Log the call and the expected lift (the interval bound nearest zero, never the point estimate). Set the matching block in `context/visitor-findings.md` to won or lost, and mark the queue item called, in the same sitting.

## STEP 5. The next pair

The winner is the new control. The next challenger comes from the queue. A third win, a third are flat, a third lose - say it before the first flat one.

## Finish - and what finished means

The run ends only when every line here is true. Anything not true is the first line of the reply, as a MANUAL STOP naming the exact thing to do, and the run picks up from there the moment it lands.
- posthog-js installed, the provider mounted, the project key in `website/.env.local` (the preflight lines of `check_tracking.py`)
- `check_tracking.py` ALL PASS on both previews with `--flag`, and on the live URL with `--remote`
- the flag id and the experiment id, both printed by `--create`
- `picker_check.py` PASS on the drafts, before the owner picked
- the deploy live, the test log written, "## My setup" carrying TRACKING VERIFIED with today's date

Then: the experiment link, the two page links, the one line of math, the log entry. Next: `/split-test status <slug>` in seven days.

Rules that never bend: call it at an 80% chance to win, Bayesian, on leads, never clicks · a tie at 8 weeks · structural only until the structure is settled · the server decides the variant, never the browser · one URL, no redirects, no noindex change · nothing changes mid-test · report the interval bound, never the point estimate · never wait to start · a manual stop is said, never skipped.
