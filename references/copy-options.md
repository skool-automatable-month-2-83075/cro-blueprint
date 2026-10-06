# The copy options - ten per section, cut, then judged by every buyer

For Claude only · /personas step 5 · the three briefs go to the subagents word for word
Next: `python3 code/copy_options.py cut`, the editor, `sheets`, one reader per buyer, `tally`.

## What it makes

A menu of lines for every section of the page, each one judged by every buyer. Never a page.
- `/split-test` draws on it when it writes whole pages. The research dashboard shows it as "The copy, section by section".
- The sections and their word limits are in `references/copy-sections.json`.
- Working files sit in `context/voc/copy/`. The result is `context/voc/options-judged.json`.

## The order

1. Three writers, in parallel. Each writes ten options for its share of the sections.
   - Writer 1: hero, trust, problem, get, featured
   - Writer 2: wall, how, cases, why, guarantee
   - Writer 3: cost, faq, faqhead, close
   - Each saves `context/voc/copy/options-1.json`, `-2.json` or `-3.json`.
2. `python3 code/copy_options.py cut` - the code cut.
3. One editor cuts what is vague. It saves `context/voc/copy/editor-cuts.json`.
4. `python3 code/copy_options.py sheets` - one blind reading sheet per approved buyer, letters shuffled.
5. One reader per buyer, in parallel, fresh context. Each saves its votes.
6. `python3 code/copy_options.py tally` - counts every buyer the same, writes the result, redraws the dashboard.

## Brief 1 - the writers

> You are the best direct-response copywriter alive. Write TEN genuinely different options for each of these sections of this business's landing page: [the writer's sections].
>
> Read first, in full: `references/persuasion.md`; `references/landing-page-blueprint.md` from "Why people buy" to "The first screen holds five or six things", and its "Copy principles"; `references/copy-sections.json` for each section's job, fields and word limits; `context/voc/facts.md`, the only facts and numbers you may use; `context/voc/reasons.md`, `reddit.md`, `reviews.md` and `rivals.md`; every approved buyer file in `context/personas/`; and the page as it reads today.
>
> Ten options per section means ten different angles, not ten rewordings. Label each angle. Lean on what `rivals.md` says none of the competitors say.
>
> Be specific: real numbers from `facts.md`, the buyers' exact phrases where they fit, with the source noted. Every heading does one of the blueprint's jobs. Every benefit runs the thing, so they get the benefit, which means something they can picture. Plain words, grade 5 to 7, sentence case, hyphens never em dashes. No filler, and never "no spam", "no obligation", "no pressure" or "no hidden fees".
>
> A winning offer that is not on file - a results guarantee, money back, a ranking promise - is allowed: write it and put the question for the owner in "asks". Never invent a number: one you need goes in [brackets] with an ask. A client quote is copied word for word or not used.
>
> Save a JSON list, one object per section: `{"section": "hero", "options": [{"id": "hero-01", "angle": "...", "for": ["buyer names"], "moves": "one of the nine", "fields": {...the section's fields...}, "asks": [], "sources": []}]}`. Check it loads as JSON before you finish.

## Brief 2 - the editor

> You are a ruthless direct-response editor. Your one job: cut every option that is vague or ambiguous, so the buyers only choose between lines that could win.
>
> Read `references/persuasion.md`, the blueprint's heading and copy rules, and `references/copy-sections.json`. Then read every option in `context/voc/copy/options-gated.json` that is not already CUT.
>
> Cut only for a real reason, named in one short line: vague (nothing concrete to picture), generic (could sit on any competitor's page), ambiguous (reads two ways), jargon (a word a stranger has not had explained), off-job (does not do what the section is for), muddled (several ideas, none lands). No quota. Never cut a line for making a bold promise; bold is not vague.
>
> Save `context/voc/copy/editor-cuts.json`: `{"<option id>": "<reason>"}`, only the options you cut.

## Brief 3 - the buyers

> You are reviewing a landing page on behalf of ONE buyer. Read their file, then the sheet of options. Read nothing else.
>
> Answer in the third person about that buyer, never as yourself, and do not help the page owner. They have been burned before and do not want the page to succeed. If their file has no evidence for a reaction, say "no evidence in file".
>
> For EVERY option in EVERY section give a verdict: "S" (it keeps them reading toward the form), "L" (this is where they close the tab) or "I" (indifferent). In the questions section: "S" means they need that question answered and the answer keeps them, "I" means they do not care, "L" means the answer makes them leave. Give a why of 15 words or fewer that quotes the option and, where it applies, their file. Pick the one best option per section.
>
> Save `{"buyer": "...", "sections": [{"section": "hero", "verdicts": {"A": "S"}, "why": {"A": "..."}, "pick": "A"}]}` to the votes file named on your sheet. Every letter needs a verdict and a why.

## Reading the result

- Every buyer counts the same. A result reads "5 of 7 stay".
- The winner in a section has the most stays over leaves. In the questions section the top six go on.
- An option the editor cut still shows what the buyers said, so the owner can bring it back.
- Buyers read by a model catch confusion and broken promises. They cannot predict conversion. `/split-test` decides.
