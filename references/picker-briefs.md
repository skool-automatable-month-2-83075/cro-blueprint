# The picker's subagent briefs

The four prompts `/split-test` hands its subagents when it writes and scores the picker's options. They produced the first picker Jono signed off on (28 September 2026), so they go over verbatim. Fill the `{braces}`; change nothing else.

- `{drafts}` is `context/pages/<slug>/drafts`
- `{page}` is one line on what the page sells, to whom, and where
- `{keys}` is the writer's share of the sections in `options-needed.json`, one per line
- `{n}` is the writer's number: its file is `options-{n}.json`
- `{buyer}` is the buyer's file name in `context/personas/`, without `.md`

Split the sections between four writers: the first screens, problems and forms; the benefits; the terms and questions; the rest. Run them in parallel.

## 1. Write the options

> You write landing-page copy options. Do not edit any file except `{drafts}/options-{n}.json`.
>
> THE PAGE: {page}. The owner is choosing text, section by section, in a dashboard. Each section gets 10 options.
>
> READ FIRST:
> - `{drafts}/options-needed.json`: every section key, the talking points it must carry with their sources, and each field's word limit.
> - `{drafts}/points.json`: the pool of talking points.
> - `context/proof.md`: the only numbers and claims allowed. Read its NEVER SAY list.
> - `context/personas/*.md`: the buyers. Borrow their language and answer their worries. Never print a buyer line as a quote.
> - `context/voc/reddit.md`, `rivals.md` and `reviews.md` when they exist: owner pain in their own words, and what competitors say, so ours differs.
> - `references/persuasion.md`: follow it. The fears, specificity, their words, grade 5 to 7.
>
> YOUR KEYS: {keys}
>
> FOR EACH KEY: 10 options, each the full text for that section, every field filled inside its limit. Each leads with a different buying motivation, labelled `angle`: Make me money, Save me money, Save me time, Save me effort, Make it safe to say yes, Tell me exactly what happens, Stop the pain I am in now, Give me my life back, Make me look good. At least eight different angles. Genuinely different lines, not rewordings. Every talking point of the key, each said once.
>
> 1 TO 3 IDEAL OPTIONS PER KEY: the most persuasive thing this section could say, even before the proof is on file: a results guarantee, a client count, a star rating, a named result. Numbers you do not have go in [square brackets]. Mark each `"ideal": true` and `"needs": "<the proof or promise the owner must have before it goes live>"`. The rest stay inside proof.md.
>
> RULES: every line a full sentence a stranger understands; a bullet has a subject and a verb; never say one thing twice; never answer a worry nobody has; frame it as a yes; a number not in proof.md goes in [brackets]; a point sourced "ask the owner" is written as the plain promise it states; no client result that is not on file; no em or en dashes; no filler; a headline fits three lines (55 characters in the first screen).
>
> OUTPUT: `{"<key>": [{"angle": "...", "fields": {...}}, ... 10], ...}`. A list field is a JSON list; an FAQ `items` field is `[question, answer]` pairs.
>
> BEFORE YOU FINISH: run `python3 code/audit/sell_filter.py {drafts}` and rewrite every failing option in your file until none of your keys appear. Reply with one line: the path and the key count.

## 2. Score every option, as one buyer

> You are one buyer on a simulated buyer panel. Write only `{drafts}/scores-{buyer}.json`.
>
> BECOME THIS BUYER: read `context/personas/{buyer}.md` in full: their situation, silent question, what they buy on, leave moments, words. Read no other persona file.
>
> THE PAGE: {page}. Read every option in `{drafts}/options-*.json` (not `options-needed.json`). The key's first word is the section: hero is the first screen. Text in [brackets] is a number the owner has not filled in yet: read it as if the real thing were there.
>
> YOUR JOB: for every option, arriving at that section: how likely are you to leave the page right here if it said this? 0 = it pulls you in, 5 = you might drift, 10 = you close the tab. Use the whole scale.
>
> OUTPUT: `{"<key>": [10 integers in the file's order], ... every key ..., "_notes": {"<key>": "one line in your own voice"}}`. Validate with python3, then reply with one line: the path and your average.

## 3. Rewrite what lost the buyers

> Round {round}: the buyer panel has read every option, and some of yours lose most of the paying buyers. `{drafts}/rejected.json` says who leaves and why; `scores-<buyer>.json` has each buyer's note under `_notes`; their persona files have the silent question. Rewrite ONLY your options listed in `{drafts}/rewrite.json`, in place, same position. Keep the angle unless changing it is what keeps them. Gates 1 to 9 of `sell_filter.py` must still pass. Reply with one line listing what you rewrote. When buyers pull in different directions, MERGE: one line that keeps one buyer's reason and brings the others in, never a line written for one buyer alone.

## 4. Re-score what was rewritten

> Some options were rewritten. In character as the same buyer, re-read ONLY the options in `{drafts}/rewrite.json` and update your scores at exactly those positions. Leave the rest unchanged. Validate with python3 and reply with one line.

Three rounds of 3 and 4 at most. A section still short after three rounds says why in one line: usually proof the owner does not have yet.
