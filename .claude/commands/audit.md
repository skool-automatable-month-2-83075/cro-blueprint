---
description: Audit any page section by section against the 26 components - keep, fix, cut, add - then build a new ad landing page from the template, or a to-do list for the SEO page, with placeholders only for what the owner must supply
argument-hint: [a live URL or /lp/<slug> to improve, or a new slug to build fresh] [check - score only, change nothing]
---

Improve or build the money page: $ARGUMENTS

**Read first, every run:** `references/landing-page-blueprint.md` (the 26 components - Jono's 18 plus the eight added since - and the amendments), `references/audit-rubric.md` (the measured checks behind them; the report counts components out of 26, not points), `references/cro-by-business-model.md` (what is right and wrong for this model), `references/persuasion.md`, then `context/proof.md` and `context/business.md`.

**And what the visitors already showed:** `context/visitor-findings.md` and the top of `context/test-queue.md`. If either has anything in it, the FIRST lines of your reply quote the top three findings, with their counts, before any score. A page built against a rubric while real visitors are stalling on a named section is a page built with the evidence in the drawer.

**The rule of this command (Jono, 25 and 28 September 2026): a live page is never gutted.** For ads, the new landing page is built beside it from the template, carrying across every section and word that works, and the old page stays as the control for the split test. For SEO, the existing page is improved in place. What is missing is ADDED, filled from the owner's answers or left as a labelled placeholder. A claim with no source is ASKED about, not deleted, and no section is removed without a yes. The score after must not be lower than the score before.

## STEP 0. It starts now. Nothing is asked before the report.

⛔ `/audit <url>` RUNS (Jono, 2 October 2026: "somebody could come in and just type in slash audit and then type in their URL and then it'll run"). No first message, no setup list, no waiting. The first thing the owner sees is their own page, marked up. Go straight to STEP 1.

The audit runs on three defaults. Say them in one line at the top of the reply, so the owner can correct any of them:
- **Live or draft.** A URL on the public web is live. A `/lp/<slug>` in this repo is a draft when `check_placeholders.py` finds a placeholder in it or the audit finds a stand-in (a randomuser face, a template logo name); otherwise it is live. Say which was assumed and why: "Scored as a draft, because it still has four placeholders. Tell me if it is live." A draft is scored as if every placeholder were filled with the real thing, and the placeholders are listed as what blocks launch. On a live page, a stand-in is what a visitor actually sees.
- **Ads, SEO or both.** Judge for both. The report already says what is cut for ads and kept for search. The choice is asked in STEP 2, where it changes what gets built.
- **The business.** Read it off the page: what they sell and to whom, how a lead reaches them (form, call, booking), what the buyer judges on. Use `context/business.md` when it is filled in. Say the read in one line ("Read as: a local service business that sells by phone and form"). Never ask for it.

⛔ POSTHOG IS NOT PART OF THE AUDIT (Jono, 2 October 2026). No key is asked for and no setup runs. A project that is not connected audits exactly the same. `/split-test` and `/analytics` connect PostHog when they need it.

⛔ FIND IT, THEN CONFIRM IT. NEVER ASK FOR WHAT THE PAGE ALREADY SHOWS (Jono, 2 October 2026). The phone number, the calendar link, the city, the licence and insurance line: the audit has read the page, so it knows whether each one is there. Nothing about them is asked before the report. They are confirmed in STEP 2, in one block, and only what was NOT found is asked for, and only when a page is being built.

## STEP 1. The audit - everything opened, everything scored

`python3 code/audit/page_audit.py <url>` (a live URL, or `http://localhost:3000/lp/<slug>` with the dev server up). It loads the page on a phone, a tablet and a desktop, hides cookie banners and chat widgets before the screenshots, reads every video transcript and opens every FAQ answer, checks the tracking and the thank-you page, runs Lighthouse, and scores the rubric in `references/audit-rubric.md`. Then it CUTS THE PAGE INTO SECTIONS, top to bottom, with no gaps and no overlaps, and saves one screenshot per section as `assets/band-NN.png`. About five minutes.

**The report is one card per section (Jono, 27 September 2026).** The code measures; you read. The code finds where each section starts and ends and what sits in it: buttons, phone links, forms, videos and what their transcripts say, reviews, questions and their answers, the words. It cannot reliably tell what a section IS on the infinite ways pages get built, and every time it guessed, the report went wrong: the offer drawn on the nav bar, a gallery skipped, a founder video called a testimonial. So meaning is yours.

Open `context/pages/<slug>/judgments-needed.json`. For EVERY card, open its `screenshot` with Read and look at it, then fill in:
- `is`: what the section is, in the owner's words ("The first screen", "Nine client videos", "The quote form").
- `kind`: one of hero, body, proof_logos, proof_quotes, proof_video, founder_video, form, faq, steps, pricing, gallery, nav, footer, other. `kind_guess` is the code's suggestion; overrule it whenever the picture disagrees.
- `verdict`: keep, fix or cut. `why`: one line.
- `holds`: every component listed gets `status` (ok, weak, missing, n/a) and a one-line `note`. If a component really lives in a different section, move it there. It is spoken about in ONE place only.
- `notes`: up to three `{quote, says}` about the exact words, with the replacement line.
- The first-screen card also gets `headline` and `subheadline` verdicts (good, weak, bad) and a `says`. Those two lines get their own boxes.
Then `page.items` (what is true of the whole page: buttons in each section, bullets, photos, the mobile bar, speed, the thank-you page, copy overall), `page.mode` (landing or homepage) and, if you want to overrule the weights, `page.do_first`. Save the whole thing as `judgments.json` beside it and re-run with `--judgments context/pages/<slug>/judgments.json`.

⛔ NO REPORT UNTIL EVERY SECTION IS JUDGED. Until then `audit.html` says "Not finished" and lists what is open. A half-built report must never be mistaken for the real one: the a B2B site and a photography site reports Jono called junk were the machine pass, never judged. The run also refuses to write the report if any rule in `code/audit/walk.py` `check()` breaks, and `python3 code/audit/test_invariants.py` must pass after any change to the audit code.

⛔ KEEP, FIX, CUT, ADD. A page needs all four. Green is keep: say what is working and why, so they know what not to touch. Amber is fix. Red is cut: one reason and nothing else, no fix notes inside a section that should go. Add is for components the page has no section for, each with where it goes. Cut only on positive evidence you can SEE: it repeats a section above, it is not on the blueprint (About us, Our story, News, Careers, a second menu), or two blocks do one job. Never because the code found nothing in a band: a photography site's "empty" rows were nine video testimonials.

⛔ AN ADD NOTE SAYS WHERE. A missing component with no section for it lands in the Add list, away from any box, so "bring six of them here" means nothing. Say "after the client videos" or "beside the form". Use `unchecked` for anything the audit could not see from outside (a thank-you page behind the form): it shows as "Not checked" and stays out of the count. Never call it missing and never drop it.

⛔ CUTTING THE MENU AND FOOTER IS FOR AD PAGES. The audit judges a page as the destination of a paid ad, where every menu link is a way out, so the menu bar and footer links are cut. An SEO page keeps both: people and Google need them to move around the site (Jono, 28 September 2026). The verdict on a menu bar or footer is never `fix`: `keep` when there is nothing to leave by, `cut` when it has links off the page, and the report will not render otherwise (one audited site, 2 October 2026). A cut says what stays - the logo and the one button, one legal line and the phone number.

⛔ A HOMEPAGE IS NOT A LANDING PAGE. No form and ten or more sections means `mode: homepage`. The report then says so and reads as "build a landing page from this": keep the green, leave out the red, add the rest. Do not write a fix list for a page that should not be the ad's destination.

⛔ THE SCREENSHOT DECIDES WHAT IS VISIBLE, THE CODE DECIDES WHAT EXISTS. A closed dropdown's options and an off-screen slide are in the code and not on the page. A collapsed FAQ answer is on the page though the screenshot hides it; the card carries the answer text. A claim needs both.

⛔ WHAT A VIDEO IS COMES FROM ITS TRANSCRIPT, never its position. "Hi, my name is Alex, the owner of Northside DJs" is a founder video wherever it sits. The card's `code_sees.videos` carries the transcript: read it before you name the section. Both video slots are spoken about in every report, present or missing.

⛔ VIDEOS ARE NOT ALWAYS IFRAMES. Elementor video widgets, lightbox thumbnails and links to YouTube are read as videos too (`videoWidgets` in `capture.py`), and their transcripts are fetched like any other. Before the screenshots, a video that would paint black is swapped for its own YouTube thumbnail, so the picture shows what a visitor sees before pressing play. If a band still shows a black or blank frame, it is the capture, not the page: never report it as a fault.

⛔ NOT FOUND IS NOT THE SAME AS NOT THERE. If the code says a band is empty and the picture shows faces, the picture is right. Majority is the bar, not perfection: mostly real photos passes, most sections with a button passes, a mobile bar that opens the form counts. A thank-you page you cannot reach is "not checked", not missing.

⛔ JUDGE THE SECTION, NOT THE ROW, and reach by section, not proximity. A review block of three rows is one section with one button. "Can someone call or enquire from this section" is the question; a number in the paragraph above the button counts.

⛔ THE LINE ABOVE THE HEADLINE GETS ITS OWN VERDICT, EVERY TIME. It has its own box and its own line in the first-screen card, and the report is not written without it - if there is none, say so and write one. Its best use is the deepest pain, not the symptom: "Tired of a profile that never shows up?" is the symptom, "Watching a competitor take the calls that should be yours?" is the pain. A clear label that tells the visitor they are in the right place ("Website to app service for ecommerce brands") is fine: keep it, and offer the pain line as an alternative worth split-testing, not as a fault (Jono, 28 September 2026).

⛔ THE HEADLINE AND THE LINE UNDER IT HAVE DIFFERENT JOBS. The headline keeps the service and the city: that is what Google reads to match the ad, and it keeps the clicks cheap. The offer and the guarantee go in the line under it.

⛔ THE HEADLINE IS WHAT LOOKS LIKE THE HEADLINE. Some sites put the `<h1>` tag on a small label (a photography site: "WEDDING PHOTOGRAPHY"). `hero_lines()` in `walk.py` takes the biggest heading in the first screen as the headline and the first line of body text under it as the line under the headline. Judge those two, not the tags.

⛔ EVERY SECTION HEADING EARNS THE READ ONE OF SEVEN WAYS: promise a result, take the work off them, answer the money worry, make them curious about the proof, borrow authority, take the risk away, or ask a question they want answered. One is enough; say so and leave it. Labels people scan for ("Frequently Asked Questions", "Pricing", "Gallery") are fine as they are. Never suggest a replacement that says the same thing as the heading you rejected.

⛔ THE CHAIN, ON SELLING BULLETS AND BENEFIT HEADINGS: feature, so you get BENEFIT, which means OUTCOME, and the outcome is something they can picture. Not on buttons, trust ticks in the first screen, lines inside reviews, names, or FAQ questions.

⛔ EVERY TEXT SECTION SHOWS THREE MEASURES, ALWAYS (Jono, 28 September 2026): the reading grade (10 or below), the length against its word limit, and how far the copy gets - `chain_mix()` in `plain.py` sorts every line into a bare feature, a benefit (it speaks to "you"), or an outcome ("so you...", "which means..."). The card shows all three, green or red, on the first screen, selling sections, steps, the form and prices. "Mostly features" means the section needs rewrites, not a polish.

⛔ SHOW THE FIX, NOT JUST THE FAULT (Jono, 28 September 2026). "Six features and not one says what the couple gets" is right and useless on its own. Every weak selling line in a section - a bullet, a tick, a benefit heading - goes in the card's `rewrites` as a before and an after, and the after is the chain: "Editing" becomes "Every photo edited by hand, so the colours match your day, which means an album you would frame, not a folder of raw shots." Never invent a fact: write [your starting price] where a number is needed.

⛔ A SUGGESTED LINE PASSES THE SAME TEST AS THE ONE IT REPLACES. If it could sit on any competitor's page unchanged, it is word vomit: "from lab prototype to a product you can ship, with the risk taken out at each step" says nothing a buyer can picture. A replacement names something they receive, a number, a date, or what happens if it fails. The line under the headline carries the OFFER: what they get, by when, and the guarantee - "A yes-or-no on whether your product can be built, in [two weeks], for a fixed fee. If it can't, you pay nothing more."

⛔ THE THREE BENEFITS ARE SECTIONS. Component 7 counts the benefit sections by name and number: "Experience (7) and All In One Solution (8) are two; the third reason the founder gives, price, has no section." Never "only one gets a section" when two are on the page.

⛔ REVIEW BADGES ARE NAMED. Proof badges means two or three of Google, Facebook, Trustpilot or TrustIndex, each with the stars drawn, the score and the count, in the first screen and beside the form. Say which platforms, not "a rating".

⛔ "READ MORE" IS A TOOL, NOT A FAULT (Jono, 28 September 2026). Never tell someone to remove one. It is the fix for a section that says too much or says it in boring words: keep the persuasive lines visible for people who scan, and put the plain detail under a Read more, where it still counts for search. Recommend it whenever a section runs over its word limit. Only a button that takes people to another page, on an ad page, is a way off the page, said once under the menu and footer.

⛔ THE COUNT EXPLAINS ITSELF. All 26 are checked on every page. The number is out of the whole list: anything not needed for the business, or not checkable from outside, is named under it ("licence and insurance, not needed; the thank-you page, could not be checked"). Every one of the 21 appears somewhere in the report, including the not-needed ones.

⛔ GRADE 10 IS THE CEILING (Jono, 28 September 2026). `code/audit/plain.py` measures every line of ten words or more; `code_sees.hard_lines` lists the worst. The three hardest lines in every section that stays MUST get a rewrite, and every rewrite must itself read at grade 10 or below, or the report is not written. "Regulatory-aware AI integration for MedTech and other high-stakes Decision support systems" reads at grade 19.

⛔ NAME THINGS PEOPLE CAN PICTURE. "Specialized computer vision for high-stakes workflows" - no one knows what that means. Abstract words (workflows, solutions, capabilities, integration, high-stakes, seamless, innovative) are flagged; replace each with the thing, the number or the result: "Cameras that spot a bad part before it ships." A list of technologies is not a reason to buy.

⛔ LITTLE TEXT MEANS UNDER THE WORD LIMIT. Each section has a limit (`MAX_WORDS` in `plain.py`: 80 for a selling section, 60 for the first screen). Component 8 cannot be marked in place while two or more sections run over it; the card shows the count. 135 words plus three hidden tabs is not "mostly short bullets".

⛔ A REPEAT IS CUT, NOT POLISHED. Compare every section with every one above it by what it SAYS. Two long sections that both describe the business are one section too many: the code flags them, you confirm, and `repeats` is set. A kept section with `repeats` set stops the report.

⛔ PROOF NEEDS A NUMBER. The code counts the figures in every proof section. Case studies that say what was built and never what it achieved are a project list; reviews with no result are a compliment. Ask for the number in the fix, with a [placeholder].

⛔ A STOCK PHOTO IS NAMED WHERE IT SITS. Mostly real photos passes component 16, but a stock or AI-generated photo is always called out in its own section's card, and the component note names it.

⛔ EVERY FORM ASKS THE FOUR: FIRST NAME, LAST NAME, EMAIL, PHONE (Jono, 28 September 2026). "There should never be a moment in time where we don't ask for the email." Unless the owner says in words that they do not want one, all four are on every form, first and last name as two fields. A form missing one is a fix, never a style choice; the audit's C5 line names which is missing.

⛔ READ IT AS A STRANGER BEFORE ANYONE ELSE DOES (Jono, 28 September 2026: "do I really have to say these things? Is this not common sense?"). The first challenger passed the checklist and read like a four out of ten. Every page, before it is shown:
- A headline spans three lines at most, on a phone and a computer (Jono, 28 September 2026). A first-screen headline is 55 characters or fewer; a section heading 70.
- Every line is a full sentence someone new understands on first read. Explain the situation before the pitch: "When someone nearby searches for what you do, Google shows three local businesses."
- A bullet has a subject and a verb: "We fill in every part of your profile", never "Your profile, fully filled in".
- Never say one thing twice in a line: "in your account, in your name" is one point.
- Never answer a worry nobody has. "You own it" is obvious, and it takes the space a real doubt needs.
- Frame it as a yes: "Easy to say yes to", never "Nothing to lose".
- The first screen's proof is totals: counts, years, audience. One client's result up there is an anecdote. Clients come later, in the case studies.
- Every person appears once on the page, and every review once. A case-study client is not also a review.
- Sprinkle proof by moving a review, never by copying it. Too few reviews to move? Keep them together.
- A client's words are quoted exactly or not at all. A trimmed quote still reads as theirs; a paraphrase is never a quote.
- No face shown bigger than the photo was taken. A small photo blown up looks cheap.
- A video goes on the page only if its words match this page's offer and pass proof.md. It gets a heading and a reason to press play, never a frame on its own.
- Then read the whole page, top to bottom, at phone and computer width, as someone who has never heard of the business. Fix every line that makes you stop.

⛔ NO STRAY CALL-TO-ACTION SECTIONS, AND THE FORM STAYS ON THE PAGE. A band that is only a line and a button ("Start a conversation") is one more thing between the reader and the form: cut it, or make it the form. A button that opens an email app or sends people to another page to fill in a form loses most of them. `code_sees.buttons` says where every button goes.

⛔ ADD LISTS EVERYTHING MISSING. Every missing component appears in the Add list, by name, with where it goes; the ones that live in a section point at it ("In section 2, the first screen"). The reasoning stays in the card.

⛔ THE LIST IS 26. Jono's 18, then speed, the guarantee, the thank-you page, a phone number people can tap (22), a stats bar (23): years in business, reviews and the score, jobs completed, and client logos (24): a row of known companies you have worked with, near the top. Logos are their own point and their own section, directly under the first screen, never folded into case studies - partner logos inside a case study do not count. A stats bar does not stand in for them (Jono, 2 October 2026): the stats are your numbers, the logos are who trusts you. With both, the logos come first and the stats bar sits under them, and a missing-logos note says exactly that, never 'a thin row under the stats bar'. The report always counts out of 26, "not counted" names anything not needed for the business or not checkable from outside, and "All 26 at a glance" at the bottom lists every one as missing, fix, in place or not counted, with where it is discussed. Nothing is skipped because the page does not have it: missing is a verdict. ⛔ THE 26 SIT IN FIVE GROUPS, THE SAME FIVE THE COURSE SLIDE TEACHES (Jono, 2 October 2026): Proof (10) - founder video, proof in the first screen, licence, video testimonials, written testimonials, badges, case studies, real photos, stats bar, client logos. Offer (3) - the offer, three benefits, a guarantee. Copy (4) - little text (8), bullet points (25), feature then benefit then outcome (18), reading level (26). Next step (6) - a button in every section, response time, lead magnet, the phone bar, the thank-you page, a number people can tap. Nothing in the way (3) - a short form, no external links, loads fast. "All 26 at a glance" is laid out in those five groups, in the slide's order and with the slide's names (Proof, The offer, The copy, The next step, Nothing in the way), each group with its own count and each part with its verdict: in place, fix, missing or not counted. The groups live in `GROUPS` in `code/audit/eighteen.py`; when the slide's grouping changes, change it there. Bullet points (25) and reading level (26) are MEASURED: leave their status empty on the sheet and the code fills them from the judged sections - 25 fails when a text section has fewer than three bullets, 26 fails when one line the business wrote reads above grade 10 (client quotes are never graded). Judge them yourself only to add a better note, and the measurement still has to agree.

- about 45 seconds is the sweet spot for a founder video; over 60 loses most people before the promise
- someone who smiles and whose face changes holds attention; a flat face reading a script does not
- a little b-roll (the work, the place, the team) between talking keeps it moving; none at all is a talking head
- most people watch with the sound off, so no captions means most of the message is lost
The card shows a measured line ("46 seconds, smiles often, face lively, 20% b-roll, no captions"). Say what to change, specifically: "cut the first 20 seconds of introduction", "add captions", "cut in two shots of a finished wedding".

⛔ BROKEN PICTURES ARE ALWAYS NAMED (28 September 2026). The code records every picture that does not load (`brokenImages`), and each card lists its own in `code_sees.broken_images`. A reviewer showing their name where their face should be looks worse than no photo: name the people, say the files fail on the live site, and put it in "Do these first" when it sits in a proof section.

⛔ A FORM THAT FOLLOWS THE VISITOR IS A STRENGTH. `stickyForm` records a form that stays on screen as people scroll. A full-page screenshot shows it once, with an empty column below; the report draws a dashed column labelled "The form follows the visitor down here" so nobody reads the gap as nothing. It counts as a way to act in every section on a computer, so never ask for a button in each section on such a page. On a phone, the fixed bar does the same job.

⛔ A GUARANTEE HIDDEN IN THE FAQ IS STILL A GUARANTEE - MOVE IT. Read every answer for a refund, a redo, a free extra or a promise with a condition. If one is there, the note is Move, not Add: it goes under the form button, where people decide.

⛔ LESS IS MORE. MORE WORDS DO NOT SELL (Jono, 28 September 2026). Very few people read five blocks of text in a row. That is what the three benefits are for: pick the main three, give each its own short section, fold the other points into them, and cut or shrink the rest. Social proof matters most - a review, a face, a number beats another paragraph. The run refuses "three benefits: in place" while more than three selling sections are kept.

⛔ A DRAFT IS SCORED AS IF FILLED (Jono, 28 September 2026). When the owner says the page is a draft, set `page.status: draft`. Every slot the build filled with a stand-in - a randomuser.me face, a photo from `public/photos/`, the template's placeholder brand names, `[bracket]` copy - is judged as if the real thing were in it, and listed under "Fill before launch" at the top of "All 26 at a glance" and on its own card. A claim with no source is not a slot: an unsourced rating is cut, draft or not, and a slot that nothing real can fill (rebuilt profiles with no result on file) is cut, not scored as filled.

⛔ WHAT THE OWNER SUPPLIES IS A SLOT WITH A FALLBACK (Jono, 28 September 2026). A founder video, client logos, review badges, more client videos, a real photo, the offer headline: each is a slot (`components/lp/Slot.tsx`), filled from `slots.ts` or `proof.tsx`. Empty, visitors see an honest fallback or nothing, and the dev server draws a dashed placeholder saying what to add. `check_placeholders.py <page folder>` lists the empty ones as the to-do; they do not block launch, `[bracket]` copy does.

⛔ EVERY COMPONENT GOES ON THE PAGE, FILLED TO ITS COUNT (Jono, 28 September 2026: "if we don't have nine written testimonials you need to add another 6 placeholders"). Every one of the 26 components that fits the business is built, never left off because the owner has none yet.
- Where they have fewer than the count, slots fill the rest. The dev server shows each as a placeholder; visitors see only the real ones.
- The counts:
  - client videos: three to nine
  - written reviews: six to nine, each person once
  - review badges: two or three, only as many as fit one line
  - client logos: five to eight
  - the stats bar: three or four numbers
- Fill from what is already on file first. The quote bank in `context/proof/reviews/` often holds more real reviews than the page shows.
- A slot nothing real can ever fill is cut, not left as a frame: a result the business has never had.

⛔ THE FIRST SCREEN, TOP TO BOTTOM (Jono, 28 September 2026).
- The pain line, then the headline carrying the offer, then the line under it.
- Then three proof ticks, then the review badges or client logos, then both buttons side by side.
- The founder video sits beside the words. Until it exists, its slot shows a placeholder, never a drawing passed off as the page's picture.

⛔ ON A LIVE PAGE, ANYTHING FABRICATED IS 10/10 (Jono, 28 September 2026). A stand-in face, a made-up brand, an unsourced rating, a stock photo under "work we have done", a play button with nothing behind it: one of them makes a visitor doubt every real thing beside it, so the section's risk of losing them is 10 out of 10, whatever else is in it. The run refuses a lower score on any section showing a face from a stand-in portrait site.

⛔ EVERY SECTION GETS A RISK OF LOSING THEM, OUT OF 10. `drop_off` on every card, cut ones included, with one line of why: boring, text heavy, irrelevant, never ties back to a benefit, nothing to look at, nowhere to act. `drop_off_code_guess` is the code's starting point from what it measured; you read the section and set the real number. The card shows it in green, amber or red.

⛔ GRADE THE PICTURES, NOT THEIR PRESENCE. `image_grade` out of 10 on every kept section with pictures: real or stock or AI, relevant to what the section says, sharp or stretched, showing people or the result. `code_sees.image_facts` gives each picture's shown and real size, whether it is stretched, a stock or AI filename, and where TinEye found it.

⛔ REVERSE-SEARCH EVERY FACE. `code/audit/reverse_search.py` puts every reviewer photo and every large photo through TinEye before any of them is called real, cached per image. A face found on Unsplash or Shutterstock is a stock photo standing in for a client, and that goes first in the card. No match does not clear an AI picture - those are unique - so the filename check catches "ChatGPT-Image", "midjourney", "firefly" and the like.

⛔ TEXT SECTIONS NEED BULLETS, BOTH WAYS TO ACT, AND SOMETHING TO LOOK AT. People skip most paragraphs; a benefit or text-heavy section is three to five bullets with the detail under a Read more. Every selling section offers both the form button and a phone number to tap - the report writes that note itself when a section has neither. Where there is room, a tasteful graphic, a review badge (Capterra, Google), a one-line client quote with a face, or a client video keeps it from reading bland; the report flags a selling section with no proof at all.

⛔ A BOX THAT SAYS ITS TITLE TWICE. Step and feature boxes are where people cram useless text, and the line under the title often repeats it: "Build & integrate - We build and configure your app... every integration". `code_sees.echoes` finds them. A box is its title and one short line that adds something.

⛔ SPRINKLE THE PROOF (Jono, 28 September 2026). Proof works beside the claim it proves, not piled into one section at the bottom. Keep one review wall, and put a quote with a face next to each benefit: the client who launched in two weeks beside the steps, the one who cut costs 90% beside "skip the rebuild". Two review blocks on one page is the sign: keep one, move the rest next to the sections they prove - by name, quote and section number. The code lists which selling sections have no proof beside them.

⛔ REVIEWS: KEEP THEM ALL, TRUNCATE THE LONG ONES, SHOW THE TOTAL. More words are fine in a review section - never recommend cutting reviews. Cut a long review to its best line with a Read more. The section needs a total at the top with the stars drawn: "4.9 out of 5 across 432 reviews". `code_sees.aggregate_rating` says whether one is there.

⛔ REVIEW AND AWARD BADGES ARE REQUIRED ON EVERY PAGE. `components/lp/ReviewBadge.tsx` draws Google, Trustpilot and Trustindex badges from the owner's real score and count: inline, no card, the section's own text colour, one line only (Jono, 28 September 2026). Preview at `/dev/review-badges` on the dev server. Google, Yelp, Facebook, Trustpilot, TrustIndex, Capterra, G2, Bark and Product Hunt badges - the kind in mobiloud.com's footer - are what people should grab and place near the form and in the first screen. `references/review-badges.md` shows the look Jono wants and which platforms fit each kind of business; point owners to each platform's own badge or widget, not a copied image. The code lists every badge it finds; none is a Missing, naming the two or three that fit.

⛔ THE FAQ IS FOR THE NEXT STEP, NOT FOR SUPPORT. Its only job is to remove what stops someone from enquiring. Check the questions against the list for the business model in `references/research/research-cro-by-business-model.md` (software: pricing and cancellation, data and security, integrations, time to launch; trades: price, arrival time, licence, guarantee, what happens after the call, area, payment). `code_sees.questions` tags each as asked before or after enquiring - an after-sale question is swapped for a missing before one.

⛔ ONE FIXED BAR ON A PHONE, AT THE BOTTOM (Jono, 28 September 2026). A header that stays put at the top plus a bar at the bottom is two bars eating a small screen - mobiloud.com's Shopify page had both. The code records bars fixed at the top (`fixedTop`) as well as the bottom; component 17 cannot be in place while there is one at the top. Let the header scroll away and keep the bottom bar with the form button and the phone.

⛔ THE TICKS UNDER THE HEADLINE ARE PROOF, NOT FEATURES. In the first screen the three ticks carry numbers someone can check: years in business, jobs or clients, the rating with its count, the guarantee. "Push notifications, native UX, full feature parity" is a feature list in the one place it costs most. The chain does not apply here - never rewrite them as feature, benefit, outcome; swap them for proof. The first-screen card shows its anatomy (pain line, headline, offer line, proof ticks, badges, form button, phone, reply time) and flags feature ticks itself.

⛔ CHATBOTS AND POPUPS COME OFF. Both cover the page and pull attention from the form; the report lists them under "Remove" at the top of "All 26 at a glance". Cookie banners stay - they are often the law.

⛔ A STAND-IN IS NOT A PERSON (28 September 2026, the first real rebuild). Faces from randomuser.me, pravatar and the like, placeholder brand names in a "Trusted by" strip, stock photos under "work we have done", and play buttons with no video behind them are all fabrications, however they got there. The audit flags every face from those sites as stock without asking TinEye. On the build, each one is replaced with the real thing from the repo or the owner's own site - `website/public/images/team` and `clients`, the case-study videos, the reviewers' photos on their live site - or the section is cut. A real person with an initial beats a stand-in with a face.

⛔ OWNING A BUSINESS DOES NOT MAKE SOMEONE THE FOUNDER. A client who says "I'm one of the owners of Ridgeline Design ... thanks to Acme Marketing" is a client. The founder is the one speaking for THIS business - welcoming the visitor, "thanks for visiting the website". `classify_video()` credits whoever the speaker thanks.

⛔ THE FOUNDER VIDEO MUST MATCH THE PAGE. Read its last line against the page's offer: a video promising "a free 30-minute call" on a page offering a graded audit sends two different next steps. Every claim in it is held to proof.md like the page's own copy.

⛔ READ EVERY FAQ ANSWER. Is it asked before they enquire (cost, timing, risk, what happens next, why you)? Does the answer remove the doubt or repeat it? Name the obvious question that is missing.

⛔ SAY WHAT IS GOOD, SPECIFICALLY. Name the figure: "top 1% of 5,000 DJs" beats "good proof". A wall of known logos, clients on camera, a volume of real reviews: most businesses never get these, and a report silent on them teaches nothing.

⛔ TASTE IS NOT A FAULT. A note names something missing, unproven or untrue, never where a working element should sit.

⛔ PLAIN ENGLISH. Never "the fold", "CTA", "H1", "message match", "Quality Score" or "LCP" in anything the owner reads. Say what it does.

⛔ A NUMBER NO REAL PAGE PRODUCES IS A MEASURING FAULT. A load time over 30 seconds is not reported as fact: the speed row is marked unmeasured and the note says to re-test in PageSpeed Insights.

Things Jono corrected on 26 September 2026, still true: a line under every button saying how fast you answer and that it costs nothing · the lead magnet sits left of the form · component 7 is three BENEFITS, each its own section · dropdowns are fine · first and last name are split so the automations work · the portfolio is any real work the owner is proud of · a photo that looks like stock is reverse-image searched before it is called real. Where `context/visitor-findings.md` names a section, say in that card what the visitors did there.

Show me: the top line ("8 of 26 components in place, fix 6, missing 7, cut 3"), and the absolute path to `audit.html`.

**The report** · one view. The page, one numbered box per section: green keep, amber fix, red cut, plus the headline and the line under it. Down the right, in the same order: the top line, "Do these first", one card per section, "Across the page" (said once, naming the sections), and "Add". Hover a card and the page scrolls to its box.

**`/audit check <url>` stops here.**

## STEP 2. The build plan, the claims and the cuts - then wait

`python3 code/audit/build_plan.py context/pages/<slug> --mode ads|seo|both` turns the judged audit into the work (Jono, 28 September 2026: "so that we can actually update their page - or create a new one"). It writes `build-plan.md` and `build-plan.json`:
- **ads** - the course template's sections in their fixed order, each saying which of their sections feeds it, the words to use (their kept words with the rewrites applied), and the placeholders only the owner can fill. Cut sections are listed as left out.
- **seo** - their existing page in its own order: keep, rewrite these lines, move this under a Read more, merge this repeat, add this. The menu and footer stay.
- **questions for the owner** - every fact only they have, one plain question each: the guarantee terms, the price, the review platform and count, which clients will record a video, what goes in each [placeholder].

⛔ APPROVAL GATE. One message, five parts, then stop. This is the FIRST time the owner is asked anything:
1. **What to build.** "Is this page for your Google Ads, for SEO, or both?" For ads, a new landing page is built from the course template and the live page is left alone. For SEO, they get a to-do list for the page they already have - the menu, the footer and their words stay, because search needs them. If the page is already in this repo, also: "Edit it in place, or duplicate it?" Duplicate makes `/lp/<slug>-v2` (or `-v3`) and leaves the original untouched.
2. **The claims.** The audit's P13 line lists every number on the page with no source. Confirm each (it goes into `context/proof.md` with "owner, today's date" and stays) or remove it (its slot becomes a placeholder). "Confirm all" is an answer.
3. **The cuts.** Every section the audit marked cut, with its one-line reason. On the ad page they are left out; on an SEO page they are merged or moved under a Read more. Nothing is removed without a yes.
4. **What the page already shows, to confirm.** One block, read from the audit: "Found on your page: phone 416-555-0199, city Toronto, no calendar link, no licence line. Is that right?" Only the ones NOT found are asked for ("What number should the page show?"). Anything already recorded in CLAUDE.md "## My setup" is never asked again.
5. **The owner questions** from the build plan, numbered. Answers now go straight into the page; anything unanswered stays a placeholder.

⛔ THE LEAD WEBHOOK IS CHECKED, NOT ASKED FOR. Look at `LEAD_WEBHOOK_URL` in `website/.env.local` and `leadWebhook` in `website/lib/site.config.ts`. Set: say so in one line ("Leads from the form go to your CRM webhook, already connected"). Not set: say it once, as optional - the page is built without it, and it is listed with the placeholders as something to connect before launch. It never stops the build.

## STEP 3. Build

**Confirmed claims first:** write them into `context/proof.md` before touching a page. `check_page_quality.py` reads that file; a claim on the page before it is in proof.md fails the gate.

**For ads - a new page, whatever their site runs on.** `cp -r website/app/lp/_template website/app/lp/<slug>` and fill it in from `build-plan.json`, section by section, in the template's order. The template's layout, order and components never change - only the words, the photos and the numbers:
- **Keep** sections come across with their own words.
- **Fix** sections come across with every rewrite applied and every note acted on - the line above the headline, the headline, the line under it, the proof ticks, the bullets in the chain.
- **Cut** sections are left out.
- **Add** items go in the template section that holds them, filled from the owner's answers, or left as a `[placeholder]` naming what it waits for.
- Their real photos, logos, reviews and videos are used where the audit found them real; a photo found on a stock site or named by an AI tool is never carried across.
Their live page is not touched. It stays as the control for the split test.

**For SEO - their existing page.** If the page is in this repo (a `/lp/<slug>` or site page), apply `seo_todo` in place or on the `-v2` duplicate, as answered in STEP 2. If it lives on WordPress, Wix, Shopify or Webflow, the build plan's SEO section is the deliverable: each change written out so the owner or their developer can make it, with the new copy ready to paste.

**Both** - build the ad page, and hand over the SEO list for the existing one.

Every open finding in `context/visitor-findings.md` is either addressed in this build or named in the reply with the reason it is not.

Never: invent a rating, count, result, price, guarantee or years figure · strip a claim the owner confirmed · put a stock or AI face beside a real name · change the template's layout, order or components · write a new component · touch the design system (`python3 code/check_css_integrity.py`) · remove a section on an existing page without the STEP 2 yes.

## STEP 4. Prove it - the same audit, again

1. `npm run dev` in `website/` if it is not running. Give me `http://localhost:3000/lp/<slug>` (and the original if this is a v2) and `http://localhost:3000/thank-you`.
2. `python3 code/audit/page_audit.py http://localhost:3000/lp/<slug>`, judge every section, then `--judgments` - the full audit on the built page. **Every "Do these first" item from the original audit is gone, the risk of losing them drops section by section, and the score is at least the score before**, or the first line of the reply names what did not and why.
3. `python3 code/check_placeholders.py website/app/lp/<slug>/page.tsx` - every placeholder still waiting, with its line. ⛔ A page with a placeholder left does not go live; the list is the owner's to-do.
4. `python3 code/check_page_quality.py /lp/<slug>` - voice, proof traceability, render.
5. If PostHog is connected: `python3 code/check_tracking.py http://localhost:3000/lp/<slug>` - every lead event once on the new page. A FAIL is fixed here and re-run, never handed back. Not connected: skip it and say in one line that lead counting starts when `/split-test` or `/analytics` connects PostHog. Never ask for the key here.
6. When the placeholders are filled and the checks pass: `/split-test` - their old page against the new one, so the change is proven with real visitors, not argued.

## Finish

The two audits with the absolute path to both `audit.html` files, the absolute path to `build-plan.md`, the localhost links, the claims confirmed into proof.md, what was left out and why, the placeholders still waiting with the question for each, and the one next step: fill the placeholders, then `/split-test` the old page against the new one.

Rules that never bend: a live page is never gutted - the ad page is built new beside it · ask before removing any claim or any section · the score never goes down · no page goes live with a placeholder · every claim on the page is in `context/proof.md` first · no table in any file a human reads · every page as a clickable localhost URL.
