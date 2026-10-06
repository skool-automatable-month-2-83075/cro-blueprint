---
description: Build about seven buyers from your own data and online research, mine what real buyers say and what the best rivals sell, approve the buyers on one dashboard, have each one read your live page and mark where they leave, then draft ten copy options per section and have every buyer judge them. /split-test writes the page.
argument-hint: [research | words | assemble | approve | read <url> | copy | log] - default runs whatever comes next
---

The persona panel: $ARGUMENTS

**Read first:** `references/persona-panel.md` - the file shape, the research, the dashboard, the panel prompt verbatim and why every buyer counts the same. This skill builds the buyers and the research, reads the live page, and drafts copy options the buyers judge. It never rewrites the page: `/split-test` writes the challenger from what this skill leaves behind, because a rewrite only means something once real visitors judge it (Jono, 28 September 2026). This is a port of Jono's own /personas skill with the corrections from the September 2026 research pass. The honest frame goes in your first message: personas catch confusion, weak promises and friction; they cannot predict conversion; real visitors are the only authority.

**Where to start when no argument is given.** Look in `context/personas/` first. No buyer files: step 1. Files without an `Approved` line: step 2, rebuild the dashboard and ask for approval. Every file approved and no page named: ask for the page URL, then step 3. `panel <url>` is the old name for `read <url>` and still works. Research that already sits in the folder is never redone - say what is there and go on.

## STEP 1. Ask what exists, then score it BEFORE building anything

Ask for, in one message: recorded calls or call transcripts, DM threads, won and lost quotes, 90 days of Google Ads search terms, and which kinds of buyer have actually paid, from the books or a best guess. Anything already in `context/` is never asked for again.

Then go and get the calls yourself, wherever they live, before asking twice: a Fireflies, Fathom, Gong or Zoom connector if one is connected; a Google Drive folder of transcripts; a folder on the computer; sent emails and form messages. Real sales calls rank first, always - they are the only source that holds both the buyers and the words that closed them.

Then say the confidence score out loud, before a single file is written. `references/persona-panel.md` has the scoring; `python3 code/build_persona_dashboard.py` prints it once files exist. The first message carries the number, the band and the one line of what it means:

> Two calls and no search terms is about 8 out of 100. These will be guesses that catch an unclear page and nothing more. Forty calls and 90 days of search terms is 95. Here is what you have: **N out of 100**.

That number decides the tone of everything after it. It is never softened, and never inflated by counting the same conversation twice.

## STEP 1b. Research the buyer online. This runs on nearly every job.

⛔ This step is not a fallback. Most businesses arriving here have nothing recorded, and a run that stops there is a run that never happens. Research first, then let whatever real data exists overwrite it.

Use WebSearch and WebFetch. What to go and find, in this order:

- First-person threads where someone describes this exact problem in their own words. Reddit, forums, question sites, complaint threads, the text inside competitor reviews.
  - Search the way a buyer types, not the way a marketer does
  - "how much should [job] cost" · "[trade] ripped me off" · "how do I choose a [trade]" · "[job] gone wrong"
- Competitor pages and ads for the same service in the same area, for the objections the market already answers and the ones nobody does.
- Published surveys and category benchmarks, for the shape of the market only. Never for a person.
- Industry articles about "the [trade] customer persona": last, weakest, and named as such on the line.

Stop when the same complaints repeat and nothing new appears, usually six to ten threads per buyer pattern. Quote what people actually wrote; never smooth it into marketing language.

Three rules, and they are the whole reason this is safe to do:

- Own data always wins. A researched line never overwrites something a real buyer said, it only fills what nobody said.
  - When a call later contradicts a researched line, the call replaces it and the score goes up
- Every researched line ends `· assumption, <where it came from>`. The dashboard draws those with a dashed rule and tags the card, so nobody mistakes one for a quote.
- Never write a quote that sounds like a buyer. If no real person said it, the field stays empty. Invented verbatim lines destroy the only part of this that carries accuracy.

Read everything. Group by the decision pattern (what made them pick, what made them leave), not by demographics. Every buyer counts the same (Jono, 29 September 2026): a share was always a guess, so no buyer outranks another.

A pattern that never paid gets `- Non-buyer: yes` and the count of organisations behind it. It sits on the dashboard in its own section, and its exits are shown, never counted.

Record what could not be counted from the files in `context/personas/evidence.md`, one line: `search terms: yes|no`. The score reads it.

## STEP 1c. What buyers say, and what the best rivals sell

The buyer files say who buys. These say how they talk and what the market already promises - the raw material `/split-test` writes from. `references/persona-panel.md` has the method, the proven Apify inputs and the three research prompts verbatim. Three subagents, in parallel, each writing one file into `context/voc/`:

- `reddit.md` - owners in this trade on Reddit, word for word, with where and when
  - pains, the result they want, fears about hiring
  - what made them hire or fire someone, their words for things, the questions they ask
- `reviews.md` - reviews of the biggest competitors: Google Maps, Trustpilot, Clutch, Amazon for products
  - phrases only: reviews come from people who bought, so they hold the words, not the objections
- `rivals.md` - the 10 to 15 best competitors in North America, picked by money, not looks
  - first ads kept running six months or more (Meta Ad Library start dates, Semrush ad history), then scale, then review volume
  - for each: headline, offer, guarantee word for word, price shown or not, proof, which of the six fears it answers
  - then what they all say and what none of them say - the gap is usually the winning angle

⛔ MANUAL STOP, first line of the message when it is missing: an Apify API token in `.env` as `APIFY_TOKEN` (apify.com, Settings, API and integrations - the free plan's $5 a month covers one run). Without it, the research runs on web search and fetch: a smaller sample, said so in each file's top line. Never wait on it.

Then rank `context/voc/reasons.md`: the three reasons people buy from this business, ranked by how many of the seven buyers name one, each with a "Moves them" line from the nine and at least two quotes from calls, Reddit or reviews.
- A reason is what they want, from what paying buyers said made them buy - "more calls from Google", "it gets done for me". A fear is not a reason: fears go to the FAQ and the guarantee.
- These three are the three benefit sections on every page `/split-test` writes.

Then write `context/voc/facts.md`: every fact and number the page may use, from `context/proof.md` and `context/business.md`, and a do-not-print list. A promise that would win but is not on file goes in as a question for the owner, never as a reason to write weaker. `python3 code/check_voc.py` must pass before step 2.

Then `python3 code/build_research_dashboard.py` draws `context/voc/research.html`, the second dashboard: the three reasons, what buyers say on Reddit and in reviews, and the competitors, one thing at a time with tabs and arrow keys. Same look as the persona dashboard. When `/split-test` has judged copy options, it shows those too. Give its full path beside the persona dashboard's.

## STEP 2. Assemble, draw, approve

`context/personas/<name>.md`, under 60 lines, the fields from the reference, blank where the data is silent. "Moves them" names two or three of the nine buying motivations in the reference, picked from the buyer's own verbatim lines - never all nine. Every buyer counts the same - no share, no primary. Aim for about seven buyers: a market usually holds that many once research is in, and the calls alone only show the people who called. Each file names a personality - driver, analyst, steady or expressive - and the panel should cover all four; the dashboard build says when one is missing. Five to eight verbatim lines with source tags per file - that is where the accuracy comes from. Leave the `Approved` line empty.

Then `python3 code/build_persona_dashboard.py`. It draws `context/personas/dashboard.html`: the confidence score, the three reasons people buy, one card per buyer (their line, the silent question, stay against leave, then the rest as one strip), and every panel round once there is one. The page carries no instructions and no next step - that is your reply's job, never the dashboard's. Same shell as the Google Ads and SEO dashboards. A blank field is dropped from the card - never fill one to make it look complete, and never invent a quote to fill the hero line.

⛔ APPROVAL GATE. One message: the confidence score and its band FIRST, then the dashboard link, the three reasons people buy, which buyers are researched rather than drawn from real conversations, the proto-persona warning for any file with fewer than six conversations behind it. Nothing else goes in that message - anything else found on the way (an exposed password, a broken link, a wrong number on the site) is its own line before or after it, never mixed into the buyers. Then the question, in these words: **approve these buyers, or name the buyer and the line to change?** Wait. An edit goes into the file, the dashboard is rebuilt, the question is asked again. On "approved": write `- Approved: <date> by the owner` into every file, rebuild, and only then go on. The panel never reads a page on behalf of an unapproved buyer.

## STEP 3. The read - every buyer reads the page, section by section

The page is read where the audit cut it, so both reports point at the same numbered sections.

1. `python3 code/audit/page_audit.py <url> --no-lighthouse` if `context/pages/<slug>/judgments-needed.json` is missing or has no `cards`. It cuts the page into sections and screenshots each one.
2. `python3 code/persona_read.py prepare context/pages/<slug>`. It writes `persona-read/needed.json` (the prompt, the sections, the screenshots) and one blank sheet per approved buyer.
3. Name the sections. Unless the audit has already been judged, open the section screenshots and set each section's `name` and `kind` in `needed.json`: "The bar at the top", "The first screen", "The logo strip", "Written reviews", "The form", "The footer". The code's guesses are only guesses; the names survive every re-run.
4. One subagent per buyer, in parallel, fresh context. Each gets ONLY its own persona file, `context/proof.md`, `needed.json`, the screenshots and its own sheet. A phone buyer judges the first screen from the phone screenshot. The prompt in `references/persona-panel.md` goes over verbatim, with the sheet's hard rules. No reader sees another's file or sheet. Say plainly if one agent voiced them all - that is a simulation, not a panel.
5. `python3 code/persona_read.py write context/pages/<slug>`. It checks every sheet and refuses to draw one that breaks a rule: a quote not on the page word for word, a number not in proof.md, a rewrite that does not rest on one of the buyer's Verbatim lines, a client's own words rewritten. A refusal is sent back to that reader to fix, never patched by hand. When it passes, it draws `context/pages/<slug>/personas.html`, logs the round and redraws the dashboard.

**What the read shows** - the audit's look, one numbered box per section on the owner's own screenshot, one card per section beside it:
- a coloured rail per buyer down the page, ending where they close the tab, with a dashed "Ivan leaves here" line
- everything below the deepest paying buyer greyed out: "None of your buyers get this far"
- red where a paying buyer leaves, amber where one needed something, green where one was answered
- each card: every buyer's reaction, their exact words, the before and after, the buying motivation it moves, and the line from their own file it rests on
- "Do these first": the exits more buyers share, top of the page down

## STEP 4. Read it, the way the reference says

- STAY counts for nothing. LEAVE counts. A buyer only counts as won when they read to the end AND get in touch.
- Every buyer's LEAVE counts the same. Two buyers at one section is ONE signal until a call, a search term, a survey answer or a real human confirms it.
- A non-buyer's LEAVE is shown, never counted.
- Taste is ignored. A buyer changing its mind proves nothing.
- Under 45 out of 100 on the confidence score, a LEAVE is a note, never a FIX NOW on its own. Say the score beside it.

The read is a checklist, not a vote. Each buyer's exit and the one question the page never answers for them is what the challenger has to fix - `/split-test` reads it from `context/pages/<slug>/persona-read/` and writes whole pages against it. The rewrites a reader suggests are notes for that writer, never words that go on the page by themselves.

## STEP 5. The copy options - ten per section, cut, judged by every buyer

`references/copy-options.md` has the order and the three briefs, word for word. It makes a menu of lines, never a page.

1. Three writers in parallel, each ten options for its share of the sections in `references/copy-sections.json`. They save `context/voc/copy/options-1.json`, `-2.json` and `-3.json`.
2. `python3 code/copy_options.py cut` - the code cut: over length, filler, too hard to read, a heading that is only a label, a number on no file, a reworded client quote.
   - A promise the files do not back is kept and marked for the owner's yes. A gap in proof is a question, never a weaker line.
3. One editor subagent cuts what is vague or generic, with the reason. It saves `context/voc/copy/editor-cuts.json`.
4. `python3 code/copy_options.py sheets` - one blind sheet per approved buyer, letters shuffled.
5. One reader per buyer, in parallel, fresh context: its own buyer file and its own sheet, nothing else.
6. `python3 code/copy_options.py tally` - every buyer counts the same. It writes `context/voc/options-judged.json` and redraws `context/voc/research.html` with "The copy, section by section".
   - A sheet with a missing verdict is sent back to its reader, never patched by hand.

⛔ Nothing on the page changes here. Words picked one section at a time repeat the same promise everywhere - on 28 September 2026 a page stitched from section winners said "live in 8 weeks" thirteen times, and Jono scored it 3 out of 10 against his own page's 8. The options are what `/split-test` draws on when it writes whole pages.

## Finish - the only stop for you

One message:
- the confidence score and its band, first
- the absolute paths to both dashboards (`context/personas/dashboard.html` and `context/voc/research.html`) and the read (`personas.html`), and the three reasons people buy in one line each
- each buyer's exit, one line each, and the one question the page never answers for most of them
- what would raise the score: the next ten sales calls recorded, and one client's before-and-after numbers in `context/proof.md`
- how many copy options were written, cut and judged, and every promise that needs the owner's yes before it can go live
- ⛔ one line: **run `/split-test` to write the challenger from these files and put it in front of real visitors**

Label everything "panel simulation".

Rules: no table in any file a human reads · personas edited only on a pattern across three runs, never one · the prompt and the files are frozen for the life of a read · the dashboard is redrawn after every file edit and every run, never edited by hand.
