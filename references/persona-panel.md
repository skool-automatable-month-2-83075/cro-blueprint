# The persona panel - your buyers read the page before a visitor does
Written 23 September 2026 from research/research-personas.md (51 sources) · for /personas
Next: build 3 to 5 persona files from real calls, then run the panel on the live page.

**The honest frame.** Personas are rehearsal partners, not evidence. They catch confusion, weak promises, missing trust and friction. They cannot predict conversion. Real visitors (/analytics) and real humans are the only authority. Never write "customers will" from a panel result; label every output "panel simulation".

## Where the personas come from, in order

Two tiers, and the difference is marked on every line of every file. EVIDENCE is this business's own buyers saying things. ASSUMPTION is everything else. A file may mix them; it may never blur them.

**Tier 1 - evidence. Always used first, always preferred.**

1. Recorded calls and DM threads. 12 to 20 conversations per service line saturate the buyer's needs; fewer than 6 behind a file makes it a proto-persona and the run says so.
2. Google Ads search terms, 90 days. Verbatim buyer language, already paid for, matched to the traffic hitting the page.
3. Reviews, for PHRASES only. Reviews are J-shaped (piled at 5 and 1 stars) and written by people who already bought. They hold zero of the people who did not call. Never build an avatar from a review; do mine the words people use for the problem.
4. CRM notes, for timestamps and ticket size only. Sales-entered "lost reasons" are wrong about 85% of the time.

**Tier 2 - assumption. Researched online, fills the gaps tier 1 left, never overwrites it.**

This tier runs on nearly every job, not as a fallback. Most businesses arriving here have nothing recorded, and a run that stops for want of transcripts is a run that never happens for nine owners in ten. Research the buyer with WebSearch and WebFetch, label every line, and let real data overwrite it the moment any exists. What is worth reading, best first:

5. First-person buyer language in public: forum and subreddit threads where someone describes this problem in their own words, question sites, complaint threads, competitor review text. This is the only external source that carries the thing personas need - how a buyer says it.
6. Competitor pages and ads for the same service, for the objections the market already answers.
7. Published research, surveys and category benchmarks, for the shape of the market only - never for a person.
8. Industry articles about "the [trade] customer persona": the weakest of all. Written by marketers, no first-person language. A last resort, and named as one on the line.

**The rule that makes tier 2 safe.** Every field and every quote carries its source. A researched line reads `· assumption, <where it came from>`. A buyer's own words read `· call, 14 August`. The dashboard colours the two differently and counts them separately. Nobody should ever have to ask which is which.

**Never**: a quote written to sound like a buyer. If no real person said it, there is no quote - the field stays empty. Inventing verbatim lines destroys the only part of this that carries accuracy.

## The persona file - one per buyer, under 60 lines

Fields, one line each unless marked. Blank beats invented.
- Name and label: first name plus the job in four words. "Burst-pipe Brenda, emergency plumbing"
- Non-buyer: yes, only for a pattern that never paid. Every other buyer counts the same - there is no share and no primary (Jono, 29 September 2026).
- Sources: how many calls, DMs, search terms, reviews built this file, and the date range.
- Age and household: the real range. Models drift young; stating it forces the correction.
- Device and moment: phone or desktop, time of day, where they physically are when they search.
- Urgency: same-hour, this-week, or researching, with the share of each.
- Trigger: the push that started the search, in their words.
- What they buy on: the one thing that decides between two similar businesses.
- Personality: one of four ways of reading a page - driver, analyst, steady, expressive - and one line on how this buyer reads.
- Moves them: two or three of the nine buying motivations below, picked from their own verbatim lines. Every rewrite for this buyer pulls on one of these, and no other.
- Silent question: the question they will not type but need answered before calling.
- Leave moment: the exact thing that makes them close the tab, from lost calls and DMs.
- Anxiety and habit: what they fear about switching, what they do today instead.
- Verbatim lines (5 to 8): exact quotes with a source tag. This is where accuracy comes from.
- Disposition: sceptical, time-poor, one tab open, low agreeableness, will not read past the fold unless earned.
- Not this person: two lines on who they are not, so the model does not slide to the average buyer.
- Out of the page's control: price ceiling, service area, hours. Needed for the stop rule.
- Calibration: last three runs, predicted verdict, what actually happened.
- Model pin: model id and the date the file was last used.
- Approved: the date the owner signed the file off, and by whom. Blank until then; the panel never runs on a blank.

## About seven buyers, and four ways of reading

A market usually holds about seven buyers (Jono, 28 September 2026: "different personality type, different buyer"). Your calls only show the people who called, so the rest come from research. Each buyer is a way of DECIDING - what makes them pick you, what makes them leave - and their personality is how they READ the page while they decide:

- Driver: decides fast, wants the result and the bottom line
- Analyst: wants the detail, the proof and the method
- Steady: wants safety, a person to trust and no surprises
- Expressive: buys on people, stories and how it will feel

A panel should read the page all four ways. `build_persona_dashboard.py` says when one is missing, and when there are fewer than five buyers. Two buyers with the same personality are fine when they decide differently - Ivan and Chad are both drivers, and leave for different reasons.

Every buyer counts the same, so the read lists them in file order and counts exits, never weights them.

## The nine buying motivations - every buyer gets two or three

All nine live in `code/audit/motivations.py`, with the phrases that reveal each one on a page. Researched 25 September 2026 from twelve sources; they replaced the working eight, and legacy and fun were cut because nothing supported them for a service business.

- Make it safe to say yes (reduce_risk) - the biggest one for a trade: reviews, a licence, a guarantee
- Stop the pain I'm in now (stop_the_pain)
- Tell me exactly what happens (certainty)
- Save me time (save_time)
- Save me money (save_money)
- Save me effort (save_effort)
- Give me my life back (freedom_control)
- Make me look good (look_good) - for a business buyer, career safety
- Make me money (make_money)

**Never all nine.** A page that pulls on every motivation promises nothing in particular. Each buyer file picks the two or three their own lines point to; the page leads with the three reasons people buy, ranked in `context/voc/reasons.md` by how many of the seven buyers name each one.

**Feature, benefit, outcome - and the outcome leads.** People buy on what it means for them and justify it with the feature. A rewrite never stops at a feature: the thing, so they get the benefit, which means something they can picture - a call, a job, money, hours back. The sheet check uses the audit's own test (`code/audit/plain.py`).

## The confidence score - said BEFORE anything is built

Every run opens with one number out of 100 and the sentence behind it. Two calls is not a small version of ninety calls, it is a different activity, and the number has to say so before the owner reads a single card.

**How it is scored.** Two parts, added:

- Conversations behind the files, up to 70 points. This is most of the score, because first-person buyer language is the only thing that makes a persona better than a guess.
  - None scores nothing, two scores 8, six scores 28
  - Twelve scores 51, twenty scores 64, forty or more scores 70
- Search terms, up to 30. 90 days of real search terms covers the people who never called, which no call can.

**Why it saturates.** Code saturation lands around twelve conversations and meaning saturation around twenty; past thirty you are reading words, not intent. So 40 conversations scores the same 70 as 400, and no run ever reports more than 95. Anything above that would be claiming a panel simulation predicts behaviour, which it does not.

**What each band means, said in the first message:**

- Under 20: guesses. Useful for catching an unclear page, useless for deciding who the page is for.
- 20 to 45: a working hypothesis. The panel's LEAVE verdicts are notes, never a FIX NOW on their own.
- 45 to 70: solid. Every buyer's LEAVE counts the same.
- Over 70: strong. Still a simulation; real visitors remain the only authority.

The score is printed before the research starts, again on the dashboard beside the buyers, and it never moves without the underlying files changing.

## When the business has no data at all

This is the common case, not the exception. The run does not stop and does not refuse.

- Say it plainly in the first message: there is nothing recorded, so these will be drafted from research and are hypotheses.
- Research the buyer (tier 2 above) and write the files with every line marked assumption.
- Every file is a proto-persona. The dashboard says so at the top, loudly, before any buyer card.
- The panel still runs. It is worth running: it catches a page that answers nobody's question, a promise with no proof, a form that asks too much. It cannot tell you which buyer matters.
- The run ends by naming the two things that turn assumptions into evidence: record the next ten sales calls, and put the page in front of three real people on their phones. Re-run after either.

An assumption-built panel never produces a FIX NOW on its own. Its LEAVE verdicts are notes until something outside the model confirms them, exactly like two personas agreeing.

## Buyers and non-buyers

A buyer is someone who paid, or someone the research says pays for this in the market. Every buyer counts the same: an exit is something the page has to answer, whoever it belongs to.

A pattern that came out of calls and never paid is a NON-BUYER, marked `- Non-buyer: yes`: real, and worth winning. Its exits are shown and never counted. It gets its own section on the dashboard.

## The dashboard - the picture of the buyers

`python3 code/build_persona_dashboard.py` draws `context/personas/dashboard.html` from the files: the three reasons people buy, one card per buyer (what decides the visit in ten seconds on the left, who they are on the right, their own words underneath), every panel round latest first, and the one next step. Same shell as the Google Ads and SEO audit dashboards. The template is `references/persona-dashboard-template.html`; only its JSON is ever replaced, never its markup.

- Rebuilt after every persona file edit and after every logged run (`persona_panel.py --log` does it itself).
- The page carries no instructions, no "next step" card and no explanation of what personas are. Those belong in the reply. The dashboard shows the buyers and the evidence behind them, nothing else.
- The owner approves the buyers on it before the panel runs. "Awaiting approval" in the chip means no buyer reads the page yet.
- A file with fewer than six conversations behind it is marked proto-persona on its card, and every verdict from it says so.
- A blank field is dropped from the card. The dashboard never fills a gap the file left, and never prints an empty row either.
- Each card opens on the buyer's strongest verbatim line, then the question they will not ask out loud. Put the best quote first in the file - that is the one that gets read.

## The run - section by section, on the audit's cut

The page is read where `/audit` cut it, so the persona read and the audit point at the same numbered sections. `code/persona_read.py prepare` writes the sections and one sheet per approved buyer; `write` checks the sheets and draws `personas.html`.

One subagent per buyer, in parallel, fresh context, one turn. Each gets only its own file, `context/proof.md`, the section screenshots in order with their words, and its own sheet. A phone buyer judges the first screen from the phone screenshot. No subagent sees another. One agent voicing all of them is a simulation, not a panel - say so if that is what ran.

Give each subagent this, verbatim. It lives in `code/persona_read.py` as `PROMPT` and is copied into every `needed.json`, so the three never drift apart:

```
You are reading a landing page on behalf of one specific buyer, described in the attached persona file. Answer in the third person about that buyer. Do not answer as yourself and do not be helpful to the page owner.

The buyer is on the device named in the file, has one tab open and has been burned before. They do not want the page to succeed. They read top to bottom and stop the moment a section gives them a reason to.

Read only the persona file, the proof file, the section screenshots in order and the words listed for each section. A phone buyer judges the first screen from the phone screenshot, not the desktop one. Quote the buyer's own lines from the file when you reason about them. If the file has no evidence for a reaction, say "no evidence in file" rather than inventing one.

Fill the answer sheet, one entry per section, in order:
- reaction: "leaves" if this is where the buyer closes the tab, otherwise "reads on". Keep going after a "leaves" and judge the rest as if an earlier fix had kept them - the owner needs every section read.
- tone: "answers" if the section answers something the file says they need, "misses" if they needed something here and did not get it, "neutral" if there is nothing here for them either way.
- quote: the exact words on the page this is about, copied, never paraphrased. Empty when neutral.
- says: one sentence, third person, what the buyer thinks here and which line of their file it comes from.
- rewrite, only when tone is "misses" or reaction is "leaves": before (the exact page words), after (the one line that would keep this buyer, in their language, under grade 10: lead with what it means for them, and never stop at a feature - the thing, so they get the benefit, which means something they can picture: a call, a job, money, hours back), moves (one of the two or three motivations the file lists under "Moves them" - never another), because (the verbatim line from their file it rests on). Never add a number that is not in the proof file - write [number] instead. Never rewrite a client's own words. Change words only: never remove or add a picture, a video, a section, a heading or a paragraph. A rewrite keeps the shape of what it replaces - a label stays a label, a heading stays a heading, a paragraph stays a paragraph, and it is never longer than it needs to be. If what the buyer needs here is a real thing only the owner can supply - a photo of finished work, a review count, a recorded video - write it in needs, in plain words, and change nothing on the page for it.

Then at the end: unanswered (the one question the whole page never answers for this buyer, in their words, or "none"), acts (yes only if, with no section making them leave, this buyer would fill in the form or call on this visit), acts_why (one sentence: what makes them act, or what stops them), out_of_control (yes if the reason they leave is price, area, hours or availability as the file lists it), confirmed_by (the call, email or search term in their file that confirms the leave reason, or "none").
```

Why it is shaped this way: third person cuts sycophancy by up to 64%; the buyer "stops the moment a section gives them a reason to", because a friendly model's default is to keep reading; forced choice (reads on or leaves, answers or misses) beats a 1 to 10 rating, which collapses to the mode; "be honest" preambles and higher temperature do nothing.

Why every section is read even after the exit: the owner can only fix the page in order. Fixing where a buyer leaves at section 3 is worthless if section 5 loses them next, and a panel that stopped at 3 would never say so. Sections past a buyer's exit are drawn as "Never gets here" - the note is there for the round after the fix.

**What the sheet check refuses** (`write` will not draw a sheet that breaks one; the reader fixes it, nobody patches it by hand):

- a quote or a rewrite's "before" that is not on the page word for word
- a rewrite that adds a number not in proof.md, unless it sits in [brackets]
- a rewrite with no buying motivation, or not resting on one of the buyer's Verbatim lines - the card prints it as "Because Ivan said", so it must be words they said
- a rewrite of a client's own words, in the reviews or on camera
- a miss or a leave with no rewrite

## Reading the verdicts

- STAY counts for nothing. LEAVE counts. A panel of all STAY is no signal, not a pass - send the page to three real humans instead.
- Every buyer's LEAVE counts the same. No single buyer blocks.
- Two personas hitting one element is ONE signal, not two.
  - Same model, same draw.
  - It becomes FIX NOW only with one confirmation from outside the model: a call recording, a search term, an exit-survey answer, or one of three real humans.
- Taste never goes on the scale: cheaper, a different font, more copy. Ignored.
- A persona changing its mind after a fix proves nothing. Belief updating is unreliable in every model tested. Confirmation is external or it is not confirmation.

## The words and the rivals - context/voc/

The buyer files say who buys. The five files in `context/voc/` say how they talk, what they fear, what the market already promises, and the three reasons people buy. `/split-test` writes from them; this skill only gathers them.

**Where the words come from, best first** (research/research-personas.md, the mining order):
- the owner's own recorded sales calls, wherever they live - the only source with both buyers and the words that closed them
- emails, DMs and form messages
- Reddit and forums - people describe the problem before they buy, so this is where the pains and the objections are
- competitor reviews - buyers only, so phrases for the result they wanted, never the objections
- industry articles - never

**Apify, the settings that worked on 28 September 2026.** The token sits in `.env` as `APIFY_TOKEN`, read inside Python and passed only as an `Authorization: Bearer` header - never printed, never on a command line. Every call is `POST https://api.apify.com/v2/acts/<actor>/run-sync-get-dataset-items?timeout=240`.
- Reddit: actor `trudax~reddit-scraper-lite`
  - input: `{"searches": ["..."], "type": "post", "sort": "relevance", "maxItems": 20, "maxPostCount": 20, "maxComments": 15, "skipComments": false, "proxy": {"useApifyProxy": true}}`
  - about $4 per 1,000 items, so one run of 400 posts and comments costs about $1.75
  - search the way an owner types: "quoted $3500 a month for local SEO", "agency locked me in", "missed calls on the job"
- Google Maps reviews: `compass~google-maps-reviews-scraper` with place URLs, or `compass~crawler-google-places` with a search and `maxReviews`
- Trustpilot, Clutch, G2: an actor if one runs quickly, else fetch the public review pages - 106 Trustpilot reviews came that way
- The free plan is $5 a month and five runs at a time. Check `GET /v2/users/me/limits` before and after, and stop at $1.50 a file
- No token: web search and fetch do the same job on a smaller sample, and each file's top line says so

**The three research prompts**, one subagent each, in parallel, 12 minutes each - a smaller sample on time beats a big one late.

Reddit:
- "Mine Reddit for the real words of [the buyer] about [the problem and hiring help]. Pull posts AND comments."
- "Write reddit.md with six buckets: pains, the result they want, fears about hiring, what made someone hire or fire, their words for things, the questions they ask."
- "Each theme gets a count and 3 to 6 quotes copied exactly, with subreddit, year and link."

Reviews:
- "Pick 6 to 10 competitors with the most reviews. Pull 2 to 4 star reviews and long 1 and 5 star ones with specifics, about 40 each."
- "Write reviews.md: the results buyers praise, what disappointed them, the fears that came true, what made it worth it, their words."
- "Count each theme and quote exactly, with business, platform, stars and date."

Rivals:
- "Find the 10 to 15 best competitors in North America, picked by ads kept running six months or more, then scale, then reviews. Never local businesses that cannot market."
- "For each: headline and the line under it, offer, guarantee word for word and whether it promises results or delivery, price shown or not, proof, and which of the six fears it answers."
- "Then: what almost all of them say, what almost none of them say, every offer and guarantee seen, and the ten headlines most worth learning from."

**facts.md is the fourth file.** Every fact and number the page may use, from proof.md and business.md, then a do-not-print list. A winning promise that is not on file goes in as a question for the owner - a gap in proof is a question, never a reason to write a vaguer line.

**reasons.md is the fifth.** The three reasons people buy, ranked by how many of the seven buyers name each one. Each has a "Moves them" line from the nine, a "Buyers: N of 7" line, and at least two quotes from calls, Reddit or reviews. A reason is what they want; a fear is not a reason.

`python3 code/check_voc.py` checks all five: present, dated, quotes with sources, three reasons, no tables.

`python3 code/build_research_dashboard.py` then draws `context/voc/research.html` from them: the three reasons, what buyers say, the competitors with what none of them say first, and the judged copy options once `/split-test` has them. It borrows the persona dashboard's stylesheet, so the two pages look like one set.

## The panel reads, it never writes

The panel marks where each buyer leaves and what they never got answered. It never picks the words on the page: `/split-test` writes whole pages, each from one big idea, and real visitors decide.

The buyers also judge a menu of copy options, ten per section, in step 5. The order and the three briefs are in `references/copy-options.md`.

## What this takes from Jono's own /personas

The CRO command is a port of Jono's personal skill. What it keeps, and where:
- One agent per persona, no cross-contamination, and say so plainly when one agent voiced them all: the readers.
- Report by persona, never averaged: every card has a line per buyer.
- The escape hatch - if keeping everyone would make the page worse, say which buyer to lose and why. `/split-test` makes that call on whole pages.
- End every run on the objection still standing: each sheet ends on `unanswered`, and the finish names the one most buyers share.
- Watch scope creep, more content is usually the wrong lever: the read never adds to the page.
- Say "ship it" when it is clean: a read where every paying buyer gets in touch says so.
- Calibrate: every round is logged, and the confidence score says how far to trust it.

## Logging

`python3 code/persona_panel.py --log <run.json>` appends every run to `context/personas/runs.md`: date, model, page hash, verdict per persona, LEAVE reason and element, what was confirmed by what, the fix applied. Later add what happened: calls per 100 visits before and after. Personas are edited only on a pattern across three or more loops, never on one run.

Pair it with the thank-you page question that runs forever: "What nearly stopped you from calling?" Two to three questions get a 16% response rate against 10% for one.
