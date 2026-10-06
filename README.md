# CRO Blueprint

Turn the page you already have into the page that books the job, with Claude Code. Four commands, one repo, the scripts included so nothing waits on Claude writing them.

## Quick start

1. Clone this repo (or download the folder) anywhere on your computer
2. Open a terminal in the folder and run `./setup.sh` once - it copies the starters into `website/`, `context/` and `.env`. They are yours from then on; git never touches them
3. `pip install -r code/requirements.txt` then `python3 -m playwright install chromium`
4. In `website/`: `npm install`, then `npm run dev`
5. Open a terminal in the folder and run `claude`
6. Type `/audit check https://your-page.com` and read the scorecard. Then go in order. The first PostHog command asks for one key (a PostHog personal API key), does the rest itself, and proves the events fire before it finishes.

## The four commands

- `/audit` · the full audit of any page, then it improves the page and audits it again.
  - phone, tablet and desktop, every image, video and link opened and understood
  - Lighthouse, phone and form tracking, a 100-point rubric tied to your business model, an HTML report you can show a client
- `/personas` · about seven buyers from your calls and online research, what real buyers say on Reddit and in reviews, and what the best rivals sell. Then it marks where each buyer leaves your page.
- `/analytics` · wires PostHog the first time from one key, then reads the heat map and every session, writes the numbers to one file, and hands back two lists: fix now (ships today), test later.
- `/split-test` · two pages at one URL, PostHog flips the coin per visitor, leads counted not clicks, starts today; `status` prints ship, kill or keep going whenever you ask.

## What you need

- [Claude Code](https://claude.com/claude-code)
- Python 3.10+ and Node 18+
- A PostHog account (free tier is enough to start: 5,000 recordings a month)
- A GoHighLevel inbound webhook for the form (any CRM webhook works)
- Optional: a PageSpeed Insights key (without one, Lighthouse installs itself locally on the first audit through npx)

## The parts you do by hand, once each

Every command tells you when, in its first line, and carries on the moment you have done it.
- Sign up to PostHog and copy one personal API key
- Log in to Vercel the first time the site deploys
- Delete the one TEST LEAD the tracking check sends to your CRM

## The honest bits

- A heat map needs about 2,000 visits on one page before it means anything.
- A split test needs leads, not clicks: about 145 a side to see a 20% lift, 70 for 30%, 27 for 50%.
  - Low traffic means a slower read, so the challenger is a whole different page, not a button colour. It starts today either way.
- A third of tests win, a third are flat, a third lose. That is normal.

Stuck? Post in the community - Help board answers same-day.
