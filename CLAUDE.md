# CRO Blueprint

## ⛔ FIRST RUN: `./setup.sh`, before any command

The repo ships **starters**, not your files. If `website/` or `context/` is missing, run `./setup.sh` first. It copies them into place once:

- `website-starter/` → `website/`
- `starters/context/...` → `context/`
- `.env.example` → `.env`

**Everything it creates is gitignored, and that is the point.** Your business facts, your proof, your buyers, your reports and your entire site are yours alone - git never tracks them. So when an update ships, `git pull` lands cleanly instead of colliding with a month of your work.

Then the tools, once: `pip install -r code/requirements.txt`, `python3 -m playwright install chromium`, and `npm install` inside `website/`. If a script stops on a missing module, install it and run the script again - never hand the member the error as a blocker.

**Updating later:** `git pull`. That is the whole procedure. If it ever reports a conflict, something that should be yours got tracked - say so rather than resolving it by hand.


The whole job in one line: build the page to the 18 components, let the buyers argue over it, watch real visitors, fix what is broken today, test what is an opinion, read the numbers honestly, repeat.

## Two guardrails that never bend

- Never put a number or claim on a page unless it appears in `context/proof.md`.
  - No proof, the slot ships empty and labelled - never a placeholder number, because a placeholder number reads exactly like a real one.
  - On a page that already exists, a claim not in proof.md is ASKED about - confirm or remove - and confirmed claims are written into proof.md in the same run.
    - A live page is improved, never silently gutted (Jono, 25 September 2026).
- Never quote a lead count until `python3 code/check_tracking.py` has passed on that page in the last 30 days.
  - Every PostHog command runs it itself in step 0; a number from a broken counter is worse than no number.

## The four commands, in the order they run

1. `/audit` · the full audit of any live URL - three viewports, every image, video and link opened, Lighthouse, tracking, a 100-point rubric tied to the business model, an HTML report - then improve the page (edit or duplicate, never gut) and audit it again. Module 1.
2. `/personas` · about seven buyers, one per way of deciding, from real calls and online research, approved on one dashboard; what buyers say (Reddit, reviews) and what the best rivals sell in `context/voc/`; then every buyer reads the live page and marks where they leave. It never rewrites the page - `/split-test` writes whole pages from these files. Module 2.
3. `/analytics` · see your visitors: wires PostHog the first time from one key, then the heat map drawn over a picture of the page, every session's log read, the numbers written to `analysis.md`, and two lists - fix now ships today, test later goes to `/split-test`. Module 3.
4. `/split-test` · two pages at one URL, PostHog flips the coin, leads counted not clicks, starts today, `status` prints ship / kill / keep going whenever you ask.

## What lives where

- `context/business.md`, `context/proof.md` · the facts and the only allowed claims. Filled by hand or by the Ads track's `/context-layer`.
- `context/personas/` · one file per buyer, `dashboard.html` the picture of them and every panel round (drawn by `code/build_persona_dashboard.py`), `runs.md` the panel's memory.
- `context/voc/` · what buyers say and what the best rivals sell, written by /personas and read by /split-test.
  - `reddit.md`, `reviews.md`, `rivals.md`, `facts.md`, `reasons.md`, checked by `code/check_voc.py`
  - `research.html` · the second dashboard, drawn by `code/build_research_dashboard.py`
  - `options-judged.json` · ten copy options per section, each judged by every buyer, made by `code/copy_options.py`
- `context/sessions/` · one file per read, dated. `analysis.md` at the root · the latest numbers, decision first. `context/test-queue.md`
- what waits for a test. `context/test-log.md` · every test, every weekly read, every call.
- `website/` · Next.js 15.
  - `app/lp/_template` is THE page; `app/lp/_split-template` is the two-page shape.
  - PostHog is wired in `components/posthog/`, `lib/posthog.ts`, `lib/posthog-server.ts`, `components/lp/LeadEvents.tsx`.
  - Every route is server-rendered per visitor so split tests never flicker.
- `code/` · `setup_check.py` (the gate), `posthog_setup.py` (`--connect` from one key), `check_tracking.py`, `dev_server.py`, `page_map.py` (the section names), `read_sessions.py`
  - `split_test.py`, `sample_size.py`, `analyze.py`, `persona_panel.py`, `build_persona_dashboard.py`, `check_readable.py`.
- `references/` · one file per command, plus:
  - `audit-rubric.md` (generated from `code/audit/rubric.py`) · `cro-by-business-model.md`
  - `landing-page-blueprint.md` (the 18, amended 23 September 2026) · `persuasion.md` · `cro-cheatsheet.md`
  - `output-format.md` · `file-examples.md`
  - `references/research/` holds the dossiers behind every rule - Claude reads those, members do not need to.
  - `references/research/` holds the dossiers behind every rule - Claude reads those, members do not need to.

## Hard rules

- Link only what the member needs to open (CRITICAL).
  - A page to preview (the localhost URL first, the live URL once it exists), a report worth reading, a PostHog screen.
  - Never a code tour, never "Files changed".
- **Every page you build gets a URL I can CLICK, every time (CRITICAL).** Start the dev server yourself if it is down. One line per page.
- A file is not a build (CRITICAL).
  - A page is built when it renders and `score_page.py` passes.
  - A flag is created when PostHog returns an id.
  - A lead is counted when the server event exists.
  - Words like built, live, shipped and done are reserved for those; everything else is drafted or pending, and the first line of the reply says so.
- NEVER a table in a file a human reads (CRITICAL).
  - No markdown tables, no pipes, no CSV in any `.md` this repo writes.
  - One thing per line, `·` separated, four facts a line maximum, a heading and plain labels for anything longer.
  - `python3 code/check_readable.py <file>` before any run is reported done; a FAIL means the file is not finished.
  - `references/output-format.md` has the rules, `references/file-examples.md` the pictures; when they disagree, file-examples wins.
- THE SPLIT (CRITICAL).
  - If a human needs to read it, it goes in the human file.
  - If only Claude needs it, it goes in `references/`.
  - Would the owner DO something differently because of this paragraph?
  - No means cut it.
- Three lines at the top of every file:
  - what it is, when it was made, the one next action.
  - Decision before data.
- PostHog first, and it is a WALL, not a warning (CRITICAL).
  - Any command that touches PostHog (`/analytics`, `/split-test`) runs step 0 from `references/posthog-setup.md` before anything else.
  - `/audit` is not one of them (2 October 2026). It asks for no key and runs on a project that is not connected: type `/audit <url>` and it scores the page.
  - Without the key, the run's only output is the ask - no analysis, no page built, no file written, no screenshot, no log entry, and no account of the work it would have done.
  - "Built but not started" is a failure, not a deliverable.
  - Not connected means the manual stop (one personal API key) as the first message, then connect, enable, restart the dev server, verify with `check_tracking.py`, continue.
  - No command runs a PostHog script on a project that is not connected, and no command builds while the key is missing.
- **A manual stop is said, never skipped (CRITICAL).** What code cannot do is listed in `references/posthog-setup.md` under "What only a human can do".
  - A command that hits one prints the block, waits, and continues the moment the answer lands.
  - A run never ends with something left to wire later; if it must pause, the first line of the reply is the manual stop and the exact thing to do.
- **Nothing changes on a page while a test runs on it.** The fix-now list waits, and you say so.
- **STAY counts for nothing, LEAVE counts.** Two personas on one element is one signal until something outside the model confirms it.
- **Leads, not clicks.** Call it at an 80% chance to win, Bayesian: about 6 / lift² leads a side. A tie at 8 weeks. Under 30 a side the read takes months - say so and start anyway with a whole-page change. Never wait to start a test.
- **Field values never leave the page.** Names of fields, yes. What was typed, never. Inputs are masked in every replay.
- **A model's claim is not evidence until it is checked (CRITICAL).**
  - "Converted" needs a lead event in the log. A broken thing needs a rage click, dead click, error or failed send near it, or it cannot make FIX NOW alone.
  - A discarded read is reported as discarded. Never fill the gap with what you think the visitor was feeling.
- **Say where, not how far down.** `code/page_map.py` names every section from its own heading, so a number reads "46 of 100 reached Price".
  - It runs before the read, and again after the page changes. "50% down the page" is not something an owner can act on.
- **Add a `console.log` at the start and end of every API route** so the flow is easy to follow.
- Retired numbers are never said
  - : "half of callers will not phone during work hours", "one second costs 7%", "53% abandon after 3 seconds"
    - "every extra field costs conversions", "37% abandon on the phone field", "chatbots convert 3x".
  - The blueprint's amendment block has the replacements.

## My setup

Filled by the commands as they run. Nothing here gets asked twice.

- PostHog: not connected yet
- Dashboard: not made yet
- Site: not set
- Replay masking: not proven yet
- TRACKING VERIFIED: never
- Pages: none built yet
