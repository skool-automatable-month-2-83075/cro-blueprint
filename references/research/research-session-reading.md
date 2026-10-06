# Research dossier - reading sessions: Claude on the logs, Gemini on the video
Built 23 September 2026 · 59 sources opened · for /analytics
Next: fold into references/session-reading.md and code/read_sessions.py, code/render_replay.py, code/gemini_watch.py

## Sources
1. PostHog API overview (rate limits) - https://posthog.com/docs/api - 2026 - query endpoint 2400/hour, analytics 240/min and 1200/hour, CRUD 480/min.
2. PostHog OpenAPI schema (live) - https://us.posthog.com/api/schema/ - 2026 - the only place the SessionRecording fields, RecordingsQuery and scopes are written down; 8.5 MB, grep it.
3. PostHog snapshot API doc - https://posthog.com/docs/session-replay/snapshot-api - 2025/26 - sources + blob_v2, max 20 blob keys per call, JSONL lines are `[windowId, event]`, 24h immutability, "never built for public use".
4. PostHog "Use Session Replay over the API" - https://posthog.com/docs/session-replay/surfaces/api - 2026 - key scoped to session_recording and session_recording_playlist; list endpoints return metadata not events.
5. PostHog Replay API reference - https://posthog.com/docs/api/replay - 2026 - full endpoint list for recordings and playlists.
6. PostHog personal API keys - https://posthog.com/docs/api/personal-api-keys - 2026 - Bearer header, pick minimal scopes, org/project/unscoped access.
7. PostHog sessions table doc - https://posthog.com/docs/data/sessions - 2026 - every `$entry_*`, `$exit_*`, `$pageview_count`, `$session_duration`, `$is_bounce` column.
8. PostHog sessions.mdx (GitHub source) - https://github.com/PostHog/posthog.com/blob/master/contents/docs/data/sessions.mdx - 2026 - same list with descriptions, confirms `$is_bounce` = single pageview session.
9. PostHog SQL editor doc - https://posthog.com/docs/data-warehouse/sql.md - 2026 - `SELECT session_id, min_first_timestamp, click_count FROM raw_session_replay_events`; default LIMIT 100.
10. PostHog SQL access doc - https://posthog.com/docs/sql - 2026 - ClickHouse function set, `multiIf` example.
11. PostHog session replay architecture (handbook) - https://posthog.com/handbook/engineering/session-replay/session-replay-architecture - 2025/26 - session_replay_events columns, S3 blocks as newline JSON `[windowId, event]`, Snappy compressed.
12. PostHog PR #26972 "add replay view" - https://github.com/PostHog/posthog/pull/26972 - closed Jan 2025 - `session_replay_events` HogQL view was proposed and closed unmerged; raw table query pattern with `groupUniqArrayArray(all_urls)`.
13. PostHog issue #22520 snapshots API stability - https://github.com/PostHog/posthog/issues/22520 - 2024 - snapshots endpoint originally did not accept personal API keys.
14. PostHog autocapture doc - https://posthog.com/docs/product-analytics/autocapture - 2026 - `$rageclick` = 3 clicks each within 30px and 1s; `$dead_click` needs `capture_dead_clicks: true`; `.ph-no-rageclick`.
15. PostHog autocapture (data) - https://posthog.com/docs/data/autocapture.md - 2026 - captures click, change, submit; `dom_event_allowlist`; no focus/blur.
16. PostHog session replay troubleshooting - https://posthog.com/docs/session-replay/troubleshooting - 2026 - CORS fonts, `crossorigin="anonymous"` on stylesheets, expired signed image URLs, third-party iframes blank.
17. PostHog control which sessions you record - https://posthog.com/docs/session-replay/how-to-control-which-sessions-you-record - 2026 - `sampleRate`, `minimumDurationMilliseconds`, URL and event triggers, "start with 100%".
18. PostHog Replay Vision - https://posthog.com/docs/replay-vision.md - 2026 - PostHog itself renders a sped-up video, sends video + events to Gemini, emits `$recording_observed`.
19. PostHog Replay Vision scanner types - https://posthog.com/docs/replay-vision/scanner-types.md - 2026 - Monitor, Classifier, Scorer, Summarizer and their `scanner_output_*` properties.
20. PostHog Replay Vision creating scanners - https://posthog.com/docs/replay-vision/creating-scanners.md - 2026 - credits per observation: 3.5 Flash Lite 2, 3 Flash 5, 3.7 Flash 15; skips >1h active sessions.
21. PostHog session summaries (AI) - https://posthog.com/docs/session-replay/session-summaries-ai - 2026 - now redirects into Replay Vision; summaries are a scanner type.
22. PostHog find replays with AI - https://posthog.com/docs/session-replay/find-replays-ai - 2026 - natural-language filters for rage, dead clicks, errors, navigation; no API shape given.
23. Posthog-session-analyzer (third party CLI) - https://github.com/amirfish1/Posthog-session-analyzer - 2025 - personal API key, 20-blob chunking, gzip `0x1f 0x8b` blocks, rrweb events to a markdown timeline.
24. Flowsery: analyze PostHog recordings - https://flowsery.com/en/blog/analyze-posthog-session-recordings - 2026 - `click_count > 0` strips bots; `keypress_count > 10` finds typers; Frustration signals collection.
25. PostHog session metrics tutorial - https://github.com/PostHog/posthog.com/blob/master/contents/tutorials/session-metrics.md - 2025 - `select avg($num_uniq_urls) from sessions`; events JOIN sessions example.
26. rrweb guide - https://github.com/rrweb-io/rrweb/blob/master/guide.md - 2026 - rrweb-player constructor, Replayer options `insertStyleRules`, `useVirtualDom`, `unpackFn`.
27. rrweb-player README - https://github.com/rrweb-io/rrweb/blob/master/packages/rrweb-player/README.md - 2026 - CDN URLs at cdn.rrweb.com, options table, `goto`, `setSpeed`, `toggleSkipInactive`, `finish` event.
28. rrweb types - https://raw.githubusercontent.com/rrweb-io/rrweb/master/packages/types/src/index.ts - 2026 - EventType 0-7, IncrementalSource 0-16, MouseInteractions (Focus=5, Blur=6), fullSnapshot/meta shapes.
29. rrvideo package (in monorepo) - https://github.com/rrweb-io/rrweb/tree/master/packages/rrvideo - 2026 - `npm i -g rrvideo`, outputs `rrvideo-output.webm`.
30. rrvideo source - https://raw.githubusercontent.com/rrweb-io/rrweb/master/packages/rrvideo/src/index.ts - 2026 - Playwright chromium + recordVideo, waits for player `finish`, `resolutionRatio: 0.8`, timeout = expected playback + 2 min.
31. rrvideo standalone repo (archived) - https://github.com/rrweb-io/rrvideo - archived - README still says mp4 and ffmpeg; superseded.
32. rrweb recipes index - https://github.com/rrweb-io/rrweb/blob/master/docs/recipes/index.md - 2026 - "Convert To Video", "Canvas", "Console Recorder" recipes exist.
33. Playwright videos (Node) - https://playwright.dev/docs/videos - 2026 - `recordVideo: { dir, size }`, saved on `context.close()`, `page.video().path()`.
34. Playwright videos (Python) - https://playwright.dev/python/docs/videos - 2026 - `record_video_dir`, `record_video_size`, `page.video.path()`.
35. ffmpeg cookbook webm to mp4 - https://ffmpeg-cookbook.com/en/articles/webm-to-mp4/ - 2026 - `-c:v libx264 -crf 23 -c:a aac -movflags +faststart`.
36. Gemini video understanding - https://ai.google.dev/gemini-api/docs/video-understanding - 2026 - all Gemini models take video; 1 fps; ~100 tok/s default, ~300 high; Files API code with ACTIVE polling.
37. Gemini Files API guide - https://ai.google.dev/gemini-api/docs/files - 2026 - 48h retention, 2 GB per file, 20 GB per project.
38. Gemini Files REST reference - https://ai.google.dev/api/files - 2026 - `state` enum PROCESSING, ACTIVE, FAILED; resumable upload headers.
39. Gemini Interactions API - https://ai.google.dev/gemini-api/docs/interactions - 2026 - GA June 2026, recommended; `generateContent` still supported but legacy.
40. Gemini quickstart - https://ai.google.dev/gemini-api/docs/quickstart - 2026 - `pip install -U google-genai`; `client.interactions.create(model="gemini-3.8-flash", input=...)`.
41. Gemini structured output - https://ai.google.dev/gemini-api/docs/structured-output - 2026 - `response_format={"type":"text","mime_type":"application/json","schema":...}`; enums, required, minimum/maximum supported.
42. Gemini pricing - https://ai.google.dev/gemini-api/docs/pricing - 2026 - 3.8 Flash $0.75 in / $3.75 out per 1M; 3.1 Flash-Lite $0.25/$1.50; 2.5 Flash $0.30/$2.50.
43. Gemini models list - https://ai.google.dev/gemini-api/docs/models - 2026 - 2.5 family marked "Limited Access"; current ids gemini-3.8-flash, 3.7-flash, 3.6-flash, 3.5-flash, 3.5-flash-lite, 3.1-flash-lite.
44. Gemini media resolution - https://ai.google.dev/gemini-api/docs/media-resolution - 2026 - video 70 tokens/frame at low/medium, 280 at high; `"resolution": "high"` on the content item.
45. Gemini 3.8 Flash model card - https://deepmind.google/models/model-cards/gemini-3-8-flash/ - 2 Sep 2026 - 1M input, 64K output, video input, cutoff March 2026.
46. Gemini rate limits - https://ai.google.dev/gemini-api/docs/rate-limits - 2026 - numbers now live only in AI Studio; page gives no RPM/TPM.
47. NN/g "Why you only need to test with 5 users" - https://www.nngroup.com/articles/why-you-only-need-to-test-with-5-users/ - 2000, still canonical - N(1-(1-L)^n), L=31%, 5 users find 85%, 3 studies of 5 beat 1 of 15, 3-4 per distinct user group.
48. FullStory frustration signals - https://help.fullstory.com/hc/en-us/articles/360020624154 - 2026 - rage, error, dead clicks, thrashed cursor definitions and false-positive caveat.
49. FullStory frustrated sessions - https://help.fullstory.com/hc/en-us/articles/360020828013 - 2026 - needs a threshold of combined signals; ranks by count; shows up to 10.
50. FullStory session replay for CRO - https://www.fullstory.com/blog/how-to-use-session-replay-for-conversion-rate-optimization/ - 2025 - stop at diminishing returns; segment "engaged checkout but did not convert".
51. Microsoft Clarity filters - https://learn.microsoft.com/en-us/clarity/filters/clarity-filters - May 2026 - rage, dead, excessive scrolling, quick backs, scroll depth, click count, JS errors filters.
52. Microsoft Clarity semantic metrics - https://learn.microsoft.com/en-us/clarity/insights/semantic-metrics - Dec 2025 - quick back = return faster than dwell-time threshold; click errors.
53. Microsoft Clarity data export API - https://learn.microsoft.com/en-us/clarity/setup-and-installation/clarity-data-export-api - 2025 - 10 requests/project/day, last 1-3 days, 1,000 rows, aggregates only, no recordings.
54. Microsoft Clarity Copilot guide - https://clarity.microsoft.com/blog/the-quick-guide-to-microsoft-claritys-copilot/ - 2025 - single and grouped session summaries, heatmap summaries, dashboard chat; UI only.
55. Contentsquare rage clicks blog (ex-Hotjar URL) - https://contentsquare.com/blog/rage-clicks/ - 2026 - habit-clicking while reading causes false positives; look for patterns not single signals.
56. Zuko industry benchmarking - https://www.zuko.io/benchmarking/industry-benchmarking - 2026 - 93,022,997 sessions; starter-to-completion 51.71% overall, desktop 55.5%, mobile 47.5%.
57. CueFully form abandonment statistics (checked at source) - https://cuefully.com/blog/form-abandonment-statistics - 2026 - Zuko view-to-complete 45%, starter-to-complete 66%, password 10.5%, email 6.4%, phone 6.3% field drop-off; Zuko publishes no form count.
58. Wheremore "what session replay shows you" - https://wheremore.com/what-session-replay-shows-you-and-what-it-doesnt/ - 2026 - quiet sessions leave no trace; one painful session vs a thousand quiet ones; company-size field trap.
59. UXCam session recordings guide - https://uxcam.com/blog/session-recordings/ - 2026 - "watch five to ten sessions in the same filter"; 20 random clips out of 10,000/day is guessing.
60. Hotjar help (snippet only, 403 on fetch) - https://help.hotjar.com/hc/en-us/articles/36820019361041 - rage click = same element 5 times within 500 ms; u-turn = back to previous URL within 7 seconds.
61. Contentsquare frustration score support (snippet only, 403) - https://support.contentsquare.com/hc/en-us/articles/37271767248273 - rage click = element clicked 3+ times in under 2 s; multiple field interaction = field clicked 3+ times; 0-100 score.
62. Velyr scroll depth (snippet only) - https://velyr.io/blog/good-scroll-depth-landing-page - `properties.$prev_pageview_max_scroll_percentage` on `$pageleave`.
63. posthog-js issue #4912 (snippet only) - https://github.com/PostHog/posthog-js/issues/4912 - Sep 2026 - `$prev_pageview_max_scroll*` leaks across SPA navigations in one tab; fix in progress.

Counted as opened: 1-59 (59 pages; some overlap). Snippet only: 60-63.

## Findings

### 1. PostHog session recordings API
- (a) List: `GET /api/projects/{project_id}/session_recordings/` with `limit`, `offset`; scope `session_recording:read`. The OpenAPI schema documents no other query params. Filtering is done by posting a `RecordingsQuery` to `/query/` (schema below) - that is what the UI does. Legacy query-string filters (`date_from`, `events`, `properties`, `having_predicates`, `console_log_filters`) still exist on the list endpoint per older posts but are undocumented: treat as inferred.
- (a) Recording fields (schema `SessionRecording`): `id`, `distinct_id`, `viewed`, `viewers`, `recording_duration`, `active_seconds`, `inactive_seconds`, `start_time`, `end_time`, `click_count`, `keypress_count`, `mouse_activity_count`, `console_log_count`, `console_warn_count`, `console_error_count`, `start_url`, `person` (MinimalPerson), `retention_period_days`, `expiry_time`, `recording_ttl`, `snapshot_source`, `snapshot_library`, `ongoing`, `activity_score`, `external_references`, `matches_filters`, `total_size`, `event_count`.
- (a) `RecordingsQuery` fields: `kind: "RecordingsQuery"`, `date_from` (default `-3d`), `date_to`, `events`, `actions`, `properties`, `having_predicates` (recording-level: duration, active_seconds, click_count, console counts), `console_log_filters`, `session_ids`, `distinct_ids`, `person_uuid`, `filter_test_accounts`, `hide_viewed_recordings`, `recommended_only`, `experiment_exposure`, `order` (default `start_time`), `order_direction` (default DESC), `limit`, `offset`, `after` (cursor).
- (a) Snapshots: `GET https://us.posthog.com/api/environments/{project_id}/session_recordings/{session_id}/snapshots?blob_v2=true` returns `{"sources":[{"source":"blob_v2","start_timestamp":"...","end_timestamp":"...","blob_key":"0"}]}`. Then `?source=blob_v2&blob_key=N` or `?source=blob_v2&start_blob_key=0&end_blob_key=19` (max 20 keys). Default `decompress=true` returns JSONL, one line per `[windowId, event]`; `decompress=false` returns Snappy. blob_v2 default since 23 June 2025. Not in the OpenAPI spec; doc says it "will change with relatively little notice".
- (a) Export only recordings that started more than 24 hours ago: sessions cut at 24h and become immutable.
- (a) Rate limits: query endpoint 2400/hour; analytics endpoints (recordings list falls here) 240/min, 1200/hour; CRUD 480/min, 4800/hour.
- (a) Scopes: `session_recording:read` for list/get, `session_recording_playlist:write` for playlists, `query:read` for `/query/`. Bearer header. Issue #22520 (2024) says snapshots did not accept personal keys; third-party CLI (source 23) uses a personal key successfully in 2025. Verify with one call before building; fallback is a session cookie.
- (b, PostHog handbook) `session_replay_events` ClickHouse columns: `session_id, team_id, distinct_id, min_first_timestamp, max_last_timestamp, block_first_timestamps[], block_last_timestamps[], block_urls[], click_count, keypress_count, mouse_activity_count, active_milliseconds, console_log_count, console_warn_count, console_error_count, size, message_count, event_count, first_url, all_urls[], snapshot_source, snapshot_library, retention_period_days`.

### 2. HogQL / query API
- (a) `POST /api/projects/{project_id}/query/` body `{"query": {"kind": "HogQLQuery", "query": "...", "values": {...}}}`; optional `refresh` (default `blocking`), `async`, `client_query_id`, `name`. Response `HogQLQueryResponse`: `results`, `columns`, `types`, `hasMore`, `limit`, `offset`, `hogql`, `clickhouse`, `timings`, `query_status`. `GET /query/{id}/` polls async status (marked Experimental).
- (a) HogQL table `raw_session_replay_events` is queryable (`SELECT session_id, min_first_timestamp, click_count FROM raw_session_replay_events`). A friendlier `session_replay_events` view was proposed in PR #26972 and closed unmerged; do not rely on it. The raw table holds partial rows per session, so aggregate with `sum()`/`min()`/`max()` and `GROUP BY session_id` (inferred from PR #26972's `groupUniqArrayArray(all_urls)` pattern and the handbook's aggregate columns).
- (a) `sessions` table columns: `$session_id, $start_timestamp, $end_timestamp, $entry_current_url, $entry_pathname, $exit_current_url, $exit_pathname, $entry_utm_source/campaign/medium/term/content, $entry_referring_domain, $entry_gclid, $entry_gad_source, $pageview_count, $autocapture_count, $channel_type, $session_duration, $is_bounce`. Tutorial also uses `$num_uniq_urls`. Access from `events` as `session.$session_duration` (tutorial JOIN and search snippet; inferred syntax, confirm in SQL tab).
- (a) Frustration events are ordinary events: `event = '$rageclick'` (3 clicks each within 30px and 1s of the previous) and `event = '$dead_click'` (requires `capture_dead_clicks: true`). Dead click properties include `$dead_click_mutation_timeout` and `$dead_click_absolute_timeout` (snippet only).
- (a) Autocapture records `click`, `change`, `submit` (property `$event_type`), plus `elements_chain`. It does not record focus or blur. A per-field drop-off funnel therefore comes from either `$autocapture` with `$event_type = 'change'` per field (fields the user typed in) or from the rrweb stream (IncrementalSnapshot source 2 MouseInteraction type 5 Focus / 6 Blur, and source 5 Input, keyed by node id). Use both: HogQL for counts, rrweb for order and dwell.
- (c) Scroll depth lives on `$pageleave` as `properties.$prev_pageview_max_scroll_percentage` (0-1) with `$prev_pageview_pathname`; posthog-js issue #4912 (Sep 2026) says the max value leaks across SPA navigations in one tab, so trust it on full page loads and treat SPA values as upper bounds.
- (a) Default `LIMIT 100`; set it explicitly.

### 3. PostHog AI summaries and playlists
- (a) PostHog's session summary product is now "Replay Vision": a scanner (prompt + type + recording filters + coverage mode + sampling rate + model) runs continuously, renders the recording as a sped-up video, sends video plus raw events to a Gemini model, and emits a `$recording_observed` event you can query.
- (a) Scanner types and outputs: Monitor (`scanner_output_verdict` yes/no/inconclusive, reasoning, confidence), Classifier (`scanner_output_tags`, `scanner_output_tags_freeform`), Scorer (`scanner_output_score`), Summarizer (`scanner_output_title`, `_summary`, `_intent`, `_outcome`, `_friction_points`, `_keywords`).
- (a) Cost is credits per observation: Gemini 3.5 Flash Lite 2, Gemini 3 Flash (default) 5, Gemini 3.7 Flash 15. Recordings with more than 1 hour of active interaction are skipped. No ad-hoc REST endpoint to summarise an arbitrary list of session ids is documented; it is scanner-driven.
- (a) Older "ask Max to summarise" flow reads the event stream, not video; it understands rage clicks, dead clicks, errors, navigation and person properties. In-app only.
- (a) Playlists: `GET/POST /api/projects/{id}/session_recording_playlists/`, `GET/PATCH/DELETE .../{short_id}/`, `GET .../{short_id}/recordings/`, `POST/DELETE .../{short_id}/recordings/{session_recording_id}/`. Body: `name`, `derived_name`, `description`, `pinned`, `type` (`collection` for curated, `filters` for saved filter; required on create), `filters` (JSON, only for type filters). Scope `session_recording_playlist:write`. Use a `collection` playlist to pin the ~10 sampled sessions so a human can open them.

### 4. Rendering rrweb replays to video
- (a) rrweb event types: 0 DomContentLoaded, 1 Load, 2 FullSnapshot, 3 IncrementalSnapshot, 4 Meta, 5 Custom, 6 Plugin, 7 Asset. Incremental sources: 0 Mutation, 1 MouseMove, 2 MouseInteraction, 3 Scroll, 4 ViewportResize, 5 Input, 6 TouchMove, 7 MediaInteraction, 8 StyleSheetRule, 9 CanvasMutation, 10 Font, 11 Log, 12 Drag, 13 StyleDeclaration, 14 Selection, 15 AdoptedStyleSheet, 16 CustomElement. MouseInteractions: 0 MouseUp, 1 MouseDown, 2 Click, 3 ContextMenu, 4 DblClick, 5 Focus, 6 Blur, 7 TouchStart, 9 TouchEnd. Meta event carries `href, width, height`; FullSnapshot carries `node` and `initialOffset`. Every event has `timestamp` ms.
- (a) rrweb-player: CSS + JS from `https://cdn.rrweb.com/rrweb-player/current/style.css` and `.../rrweb-player.umd.cjs` (or ESM `rrweb-player.js`). `new rrwebPlayer({target, props:{events, width:1024, height:576, autoPlay:true, speed:1, speedOption:[1,2,4,8], showController:true, skipInactive, mouseTail, insertStyleRules, UNSAFE_replayCanvas}})`. Methods `play, pause, goto, setSpeed, toggleSkipInactive, getMetaData, getReplayer`. Player emits `finish`.
- (a) rrvideo (now `packages/rrvideo` in the rrweb monorepo; standalone repo archived): `npm i -g rrvideo && rrvideo --input events.json --output out.webm --config cfg.json`. Source: launches Playwright chromium `headless: true`, `recordVideo: { dir, size }` where size = max viewport from Meta events times `resolutionRatio` 0.8, builds an HTML page with rrweb-player `showController:false, autoPlay:false`, spreads `config.rrwebPlayer` (speed, skipInactive etc.) into the player, listens for `finish`, times out at expected playback + 2 minutes. Output is webm. Archived README's "mp4 + ffmpeg" is stale.
- (a) Playwright direct: `browser.new_context(record_video_dir="videos/", record_video_size={"width":1280,"height":720})`; video only exists after `context.close()`; `page.video.path()`.
- (a) ffmpeg: `ffmpeg -i in.webm -c:v libx264 -crf 23 -c:a aac -b:a 128k -movflags +faststart out.mp4`; add `-pix_fmt yuv420p` for QuickTime/Safari (search consensus, not the cookbook). Gemini accepts webm directly, so convert only when a human needs to open the file.
- (a) Pitfalls from PostHog: fonts blocked by CORS unless the site allows the replayer origin; stylesheet rules unreadable unless `<link crossorigin="anonymous">` so the snapshot holds only the URL; signed or expired image URLs 404 at replay; third-party iframes (Typeform, Stripe Checkout, Calendly, YouTube) are blank; heavy SVG/Lottie frozen; masked inputs render as asterisks. Consequence for a local renderer: the page runs on `file://` or `localhost`, so any asset the site serves with a strict CORS or referrer policy will be missing; serve the player from a real localhost origin and set a normal Referer, and tell Gemini in the prompt that missing images or fonts are a rendering artefact, not a bug.
- (inferred) `blob:` URLs captured in snapshots cannot resolve outside the original tab; treat any `blob:` src as a known blank. Asset event type 7 exists in current rrweb for inlined assets; PostHog's older SDK versions do not emit it.
- (a) Feed the player one window at a time: PostHog lines are `[windowId, event]`; multi-tab sessions interleave windows. Pick the window with the most events (or the one containing the target URL) and require its first events to be Meta (4) then FullSnapshot (2); PostHog's own pipeline does "meta event patching" for this reason.
- (c) Typical durations: a 3-4 minute session at `speed: 4` with `skipInactive: true` renders in roughly 40-70 seconds; rrvideo's own timeout math assumes wall time = event span / speed. Budget 1-2 minutes of wall time per session including browser start.

### 5. Gemini video understanding
- (a) Every current Gemini model takes video. Current ids: `gemini-3.8-flash` (default in all docs, released 2 Sep 2026, 1M in / 64K out, cutoff March 2026), `gemini-3.7-flash`, `gemini-3.6-flash`, `gemini-3.5-flash`, `gemini-3.5-flash-lite`, `gemini-3.1-flash-lite`, `gemini-3.1-pro-preview`; `gemini-2.5-flash`, `-flash-lite`, `-pro` are now "Limited Access".
- (a) Sampling: static mode 1 fps, adjustable via `processing: {type: "static", fps: 0.5}`; clip with `start_offset`/`end_offset`. Tokens: about 100 per second of video at default (70 per frame) and about 300 at `"resolution": "high"` (280 per frame); audio 32 tokens/s. Length: at 1M context up to 3 hours at low resolution or 1 hour at high. Timestamps are `MM:SS`.
- (a) Files API: `client.files.upload(file=...)`, poll `client.files.get(name=...)` until `state.name == "ACTIVE"` (states PROCESSING, ACTIVE, FAILED), files kept 48 hours, 2 GB per file, 20 GB per project. Inline base64 allowed under 100 MB per the video page, but use Files for anything you might re-ask.
- (a) Interactions API is GA (June 2026) and recommended; `generateContent` stays supported as legacy. Structured output: `response_format={"type":"text","mime_type":"application/json","schema": Model.model_json_schema()}`, then `json.loads(interaction.output_text)` or `Model.model_validate_json(...)`. Supported: types, enum, required, additionalProperties, minimum/maximum, minItems/maxItems, format date-time. Deeply nested schemas may be rejected.
- (a) Price (per 1M tokens): 3.8 Flash $0.75 in, $3.75 out; 3.5 Flash $1.50/$9.00; 3.1 Flash-Lite $0.25/$1.50; 3.1 Pro preview $2.00/$12.00 (<=200k); 2.5 Flash $0.30/$2.50. Video minute at default resolution is ~6,000 tokens = $0.0045 on 3.8 Flash, ~$0.0135 at high resolution; 10 sessions rendered to ~1 minute each cost under 10 cents including a 600-token JSON answer each.
- (a) Rate limits are no longer printed; read them in AI Studio for the project's tier.
- (c, inferred from PostHog's own product) PostHog sends rendered video plus raw events to Gemini. Do the same: the event log gives exact timestamps and element text, the video gives what the user saw. Ask Gemini to cite `MM:SS` and to say when it is guessing.

### 6. Evidence on session replay analysis
- (b, NN/g, L=31% across many projects) Problems found = N(1-(1-L)^n); 5 sessions of one user type surface ~85% of problems; run 3 rounds of 5 rather than 1 of 15; with distinct user groups take 3-4 from each. Transfer: about 3-4 sessions per stratum, three strata, ~10 total, then iterate after fixes.
- (c) UXCam and FullStory: watch 5-10 sessions inside one filter before concluding; 20 random clips from 10,000/day is guessing; stop when new sessions add nothing; segment "reached checkout but did not convert" first.
- (a) Signal definitions differ by vendor, so state the threshold you use: PostHog rage = 3 clicks within 30px and 1s each; Hotjar rage = 5 clicks on one element in 500 ms (snippet); Contentsquare rage = 3+ clicks in under 2 s, "multiple field interaction" = a field clicked 3+ times (snippet); FullStory rage = multiple rapid clicks in one area, dead click = no page change within a few seconds, error click = click right before a JS/console error, thrashed cursor = erratic or circular desktop mouse movement; Clarity rage = clustered rapid clicks, dead click = no visual change and no navigation in a reasonable time, quick back = returned to previous page faster than that page's dwell-time threshold, excessive scrolling = more vertical scroll than the expected average; Hotjar u-turn = back to the previous URL within 7 s (snippet).
- (a) FullStory counts a session as "frustrated" only above a threshold of combined signals and ranks by count; Contentsquare rolls signals into a 0-100 score. Single signals mislead: habit-clicking while reading and Next/Prev steppers are known false positives (FullStory, Contentsquare).
- (b, Zuko, 93,022,997 sessions) Starter-to-completion 51.71% overall, desktop 55.5%, mobile 47.5%; view-to-completion 45%; worst fields by drop-off: password 10.5%, email 6.4%, phone 6.3%; name takes 3.5 s, address 7.4 s; field count is not correlated with completion; average field returns highest in software (~5.0). Zuko publishes session counts, not a form count; the "1,362 forms" figure could not be found in any opened page.
- (c) Quiet abandonment is the missing stratum: "the quiet sessions, the ones where everything worked, leave no trace" and "one painful session sticks in your head longer than a thousand quiet ones" (Wheremore). Frustration filters find bugs; they do not find the visitor who read everything, reached the form, and left without a fight. That visitor is a persuasion or offer problem and needs a control group of converters to tell apart.
- (c) Separating bugs from persuasion: a bug shows in the log first (console error, dead click on a CTA, rage on a disabled button, form validation loop) and reproduces across devices; a persuasion problem shows as a clean log with a stall (long dwell on price or a pause at a field, then exit) and no error. FIX NOW needs a reproducible mechanism; TEST LATER needs a hypothesis and a control comparison.

### 7. Alternatives
- (a) Microsoft Clarity: free replay, rage/dead/quick-back/excessive-scroll filters, Copilot summaries of single or grouped recordings and heatmaps (UI only). Data Export API returns aggregates only (rage, dead, quickback, script error, error click counts by up to three dimensions), 10 requests per project per day, last 1-3 days, 1,000 rows, no recordings or events. Not scriptable for this command.
- (c) Hotjar is now Contentsquare; its replay has no public snapshot API and the help site blocks fetches. Not scriptable either.
- (a) PostHog: recordings, raw rrweb snapshots over HTTP, HogQL over the same sessions, feature flags and experiments in one project, plus Replay Vision that already does video-to-Gemini. One key, one project id, one tool. That is the pick.

## Exact API facts (verified)

- Confirmed in docs or schema: everything in this section unless marked inferred.

```bash
# auth
export PH_HOST=https://us.posthog.com   # or https://eu.posthog.com
export PH_PROJECT=12345
export PH_KEY=phx_...   # scopes: session_recording:read, session_recording_playlist:write, query:read
H='Authorization: Bearer '"$PH_KEY"
```

```bash
# list recordings (metadata only), analytics bucket 240/min
curl -s -H "$H" "$PH_HOST/api/projects/$PH_PROJECT/session_recordings/?limit=100&offset=0"
# fields: id, distinct_id, recording_duration, active_seconds, inactive_seconds, start_time, end_time,
#         click_count, keypress_count, mouse_activity_count, console_log_count, console_warn_count,
#         console_error_count, start_url, person, activity_score, snapshot_source, ongoing, viewed
```

```bash
# filtered list the way the UI does it: RecordingsQuery through /query/ (2400/hour)
curl -s -H "$H" -H 'Content-Type: application/json' \
  "$PH_HOST/api/projects/$PH_PROJECT/query/" -d '{
  "query": {
    "kind": "RecordingsQuery",
    "date_from": "-14d",
    "filter_test_accounts": true,
    "order": "console_error_count",
    "order_direction": "DESC",
    "having_predicates": [
      {"type": "recording", "key": "active_seconds", "operator": "gt", "value": 15}
    ],
    "events": [{"id": "$rageclick", "type": "events", "name": "$rageclick"}],
    "limit": 50
  }}'
# having_predicates item shape and the events item shape are inferred from the UI payload; the field names are in the schema.
```

```bash
# snapshots: sources, then blobs (max 20 keys per call). Not in the OpenAPI spec. Note /api/environments/.
curl -s -H "$H" "$PH_HOST/api/environments/$PH_PROJECT/session_recordings/$SID/snapshots?blob_v2=true"
# {"sources":[{"source":"blob_v2","start_timestamp":"...","end_timestamp":"...","blob_key":"0"}, ...]}
curl -s -H "$H" "$PH_HOST/api/environments/$PH_PROJECT/session_recordings/$SID/snapshots?source=blob_v2&start_blob_key=0&end_blob_key=19" > s.jsonl
# each line: [windowId, rrwebEvent]   (decompress=true default; decompress=false gives snappy)
```

```python
# python: JSONL -> rrweb events for one window
import json, collections
by_win = collections.defaultdict(list)
for line in open("s.jsonl"):
    line = line.strip()
    if not line: continue
    win, ev = json.loads(line)
    by_win[win].append(ev)
win = max(by_win, key=lambda w: len(by_win[w]))
events = sorted(by_win[win], key=lambda e: e["timestamp"])
assert events[0]["type"] == 4 and events[1]["type"] == 2, "need Meta then FullSnapshot first"
json.dump(events, open("events.json", "w"))
```

```bash
# HogQL through /query/
curl -s -H "$H" -H 'Content-Type: application/json' "$PH_HOST/api/projects/$PH_PROJECT/query/" \
  -d '{"query":{"kind":"HogQLQuery","query":"SELECT session_id, min(min_first_timestamp) AS started, sum(click_count) AS clicks, sum(console_error_count) AS errors FROM raw_session_replay_events WHERE min_first_timestamp > now() - INTERVAL 14 DAY GROUP BY session_id ORDER BY errors DESC LIMIT 200"}}'
# response: {"results":[[...]], "columns":[...], "types":[...], "hasMore":..., "hogql":..., "clickhouse":...}
```

```bash
# playlist to hand the sample to a human
curl -s -H "$H" -H 'Content-Type: application/json' "$PH_HOST/api/projects/$PH_PROJECT/session_recording_playlists/" \
  -d '{"name":"read-sessions 2026-09-23","type":"collection","description":"3 strata x ~3"}'
# then for each session id:
# POST $PH_HOST/api/projects/$PH_PROJECT/session_recording_playlists/{short_id}/recordings/{session_id}/
```

```python
# Gemini: upload, wait for ACTIVE, ask with a JSON schema (Interactions API, GA June 2026)
import time, json
from google import genai
from pydantic import BaseModel
client = genai.Client()  # GEMINI_API_KEY in env
f = client.files.upload(file="session_abc.webm")          # video/webm accepted; 2 GB max; kept 48 h
while not f.state or f.state.name != "ACTIVE":
    if f.state and f.state.name == "FAILED": raise RuntimeError("upload failed")
    time.sleep(3); f = client.files.get(name=f.name)
ix = client.interactions.create(
    model="gemini-3.8-flash",
    input=[
        {"type": "video", "uri": f.uri, "mime_type": f.mime_type,
         "processing": {"type": "static", "fps": 1}},            # 1 fps default; ~100 tokens/s
        {"type": "text", "text": PROMPT + "\n\nEVENT LOG:\n" + event_log_text},
    ],
    response_format={"type": "text", "mime_type": "application/json",
                     "schema": SessionVerdict.model_json_schema()},
)
verdict = SessionVerdict.model_validate_json(ix.output_text)
```

- Inferred, not re-verified in an opened page: legacy path `client.models.generate_content(model=..., contents=[f, prompt], config={"response_mime_type":"application/json","response_schema":SessionVerdict})` still works per the Interactions doc's "remains fully supported" line.

```python
# render: rrweb-player in headless Playwright with video (python)
from playwright.sync_api import sync_playwright
HTML = """<!doctype html><html><head>
<link rel="stylesheet" href="https://cdn.rrweb.com/rrweb-player/current/style.css">
<script src="https://cdn.rrweb.com/rrweb-player/current/rrweb-player.umd.cjs"></script>
<style>body{margin:0;background:#fff}</style></head><body><script>
fetch('/events.json').then(r=>r.json()).then(events=>{
  const p = new rrwebPlayer({target: document.body, props: {events, width: %d, height: %d,
    autoPlay: true, speed: %d, skipInactive: true, showController: false, mouseTail: true}});
  p.addEventListener('finish', () => { window.__done = true; });
});</script></body></html>"""
def render(events_dir, w, h, speed, out_dir):
    with sync_playwright() as pw:
        b = pw.chromium.launch(headless=True)
        ctx = b.new_context(viewport={"width": w, "height": h},
                            record_video_dir=out_dir, record_video_size={"width": w, "height": h})
        page = ctx.new_page()
        page.goto(f"http://localhost:8765/player.html")     # serve events_dir with python -m http.server 8765
        page.wait_for_function("window.__done === true", timeout=15*60*1000)
        path = page.video.path(); ctx.close(); b.close()      # webm exists only after close
        return path
```

- Width/height: take from the first Meta event (`data.width`, `data.height`); scale down by 0.8 like rrvideo if over 1280 wide. Playwright saves the video only on `context.close()`.
- ffmpeg only if a human needs mp4: `ffmpeg -i in.webm -c:v libx264 -crf 23 -pix_fmt yuv420p -movflags +faststart out.mp4`.

## The sampling recipe

- Inputs: `TARGET_URL_RE` (landing page path), `REACH_RE` (form or call-button page or element text), `CONV_EVENT` (the conversion event name, e.g. `lead_submitted`, or the thank-you pathname), window 14 days. Session key everywhere is `properties.$session_id` on `events` and `session_id` on `raw_session_replay_events`.
- Column names in `raw_session_replay_events` and `sessions` are confirmed; the `sum()`/`GROUP BY` shape is inferred (see Findings 2). Run each query once in the SQL tab before wiring it.

```sql
-- base: one row per recorded session on the target page, last 14 days, human-looking
WITH replay AS (
  SELECT session_id,
         min(min_first_timestamp) AS started,
         max(max_last_timestamp)  AS ended,
         sum(click_count)         AS clicks,
         sum(keypress_count)      AS keys,
         sum(console_error_count) AS errors,
         round(sum(active_milliseconds)/1000) AS active_s,
         any(first_url)           AS first_url
  FROM raw_session_replay_events
  WHERE min_first_timestamp > now() - INTERVAL 14 DAY
    AND min_first_timestamp < now() - INTERVAL 24 HOUR      -- immutable after 24h
  GROUP BY session_id
  HAVING clicks > 0 AND active_s >= 10                      -- drop bots and blinks
),
sig AS (
  SELECT properties.$session_id AS session_id,
         countIf(event = '$rageclick')  AS rage,
         countIf(event = '$dead_click') AS dead,
         countIf(event = CONV_EVENT)    AS conv,
         countIf(event = '$pageview' AND match(properties.$pathname, REACH_RE)) AS reached_page,
         countIf(event = '$autocapture' AND match(properties.$el_text, REACH_RE)) AS reached_cta,
         maxIf(properties.$prev_pageview_max_scroll_percentage, event = '$pageleave' AND match(properties.$prev_pageview_pathname, TARGET_URL_RE)) AS max_scroll,
         countIf(event = '$autocapture' AND properties.$event_type = 'change') AS fields_changed
  FROM events
  WHERE timestamp > now() - INTERVAL 14 DAY
    AND match(properties.$current_url, TARGET_URL_RE)
  GROUP BY session_id
)
SELECT r.session_id, r.started, r.active_s, r.clicks, r.keys, r.errors,
       s.rage, s.dead, s.conv, s.reached_page, s.reached_cta, s.max_scroll, s.fields_changed
FROM replay r LEFT JOIN sig s ON r.session_id = s.session_id
LIMIT 5000
```

- Stratum A, friction (target 4): from the base rows, `conv = 0` ordered by `(rage*3 + dead*2 + errors*2)` desc, then `active_s` desc; require score >= 2; cap at one session per person (`distinct_id`) so one angry visitor is not the whole sample.
- Stratum B, quiet abandonment (target 3-4): `conv = 0 AND errors = 0 AND rage = 0 AND dead = 0 AND (reached_page > 0 OR reached_cta > 0 OR fields_changed > 0) AND active_s >= 30`, ordered by `active_s` desc, then pick every k-th row (systematic, not top-k) so you do not only see the longest.
- Stratum C, converted control (target 3): `conv > 0`, ordered randomly (`ORDER BY rand()`), prefer one with `fields_changed >= 2`.
- Counts: 10 sessions total (4 + 3 + 3). If stratum A has fewer than 4 with score >= 2 in 14 days, take what exists and widen to 30 days for A only; never pad A with quiet sessions. If B is empty the page is not reaching the form and the finding is upstream (scroll depth), so report that instead of watching.
- Form field funnel, per field, over all sessions that touched the form (HogQL, counts only):

```sql
SELECT properties.$el_text AS field_label,
       any(elements_chain) AS chain,
       count(DISTINCT properties.$session_id) AS sessions_changed
FROM events
WHERE event = '$autocapture' AND properties.$event_type = 'change'
  AND match(properties.$current_url, REACH_RE)
  AND timestamp > now() - INTERVAL 14 DAY
GROUP BY field_label ORDER BY sessions_changed DESC LIMIT 50
```

- Order and dwell per field for the 10 sampled sessions come from the rrweb stream: source 2 type 5 (Focus) and 6 (Blur) with node ids resolved against the FullSnapshot's input `name`/`id`/`placeholder` attributes; source 5 (Input) shows typing and clearing (masked text still shows length changes). Last focused field with no submit = abandonment field.
- Event log text handed to Claude and to Gemini per session: one line per `$pageview`, `$pageleave` (with max scroll), `$autocapture` (type, el_text, href), `$rageclick`, `$dead_click`, `$exception`/console error, focus/blur/input from rrweb, each with `MM:SS` from session start and, for the video, `MM:SS` of the rendered clip (event offset / speed, minus skipped idle time from `getMetaData()`).

## The Gemini prompt

```text
You are reviewing one visitor session on a marketing landing page. You get (1) a screen recording rendered
from a DOM replay, played at {SPEED}x with idle gaps removed, and (2) the event log with two clocks:
session time and video time (MM:SS). The visitor did NOT convert unless the log says CONVERTED.

Rendering artefacts you must ignore: missing web fonts, blank third-party iframes (calendars, payment,
video embeds), missing or broken images, input text shown as asterisks. These are replay limits, not bugs.

Answer only from what you can see or read in the log. Cite video timestamps for every claim. If the
evidence is thin, say so and lower confidence. Do not invent motives.

Tasks:
1. Where did attention go: the sections seen (by video time), scroll behaviour, backtracking.
2. The stall: the last meaningful place before exit, how long they stayed there, what they did.
3. Bugs and friction: anything that did not respond, looped, jumped, covered content, or blocked input.
   Tie each to log evidence (dead click, rage click, error) when present.
4. If a form or call button was reached: the last field touched, what happened there, whether validation
   or layout interfered.
5. Your best single explanation for leaving, classified as BUG, FRICTION, OFFER, COPY, TRUST, or STRUCTURE,
   with confidence 0-1 and the one observation that would change your mind.
6. One fix to ship today (only if BUG or FRICTION) and one thing to test later.

Event log follows.
```

```json
{
  "type": "object",
  "required": ["session_id", "sections_seen", "stall", "issues", "form", "exit_reason", "fix_now", "test_later", "confidence", "artefacts_noted"],
  "properties": {
    "session_id": {"type": "string"},
    "sections_seen": {"type": "array", "items": {"type": "object", "required": ["label", "video_time", "dwell_seconds"],
      "properties": {"label": {"type": "string"}, "video_time": {"type": "string"}, "dwell_seconds": {"type": "number", "minimum": 0}}}},
    "stall": {"type": "object", "required": ["video_time", "where", "what_happened", "duration_seconds"],
      "properties": {"video_time": {"type": "string"}, "where": {"type": "string"}, "what_happened": {"type": "string"}, "duration_seconds": {"type": "number", "minimum": 0}}},
    "issues": {"type": "array", "items": {"type": "object", "required": ["kind", "video_time", "element", "evidence", "reproducible"],
      "properties": {
        "kind": {"type": "string", "enum": ["dead_click", "rage_click", "error", "layout_shift", "overlay_block", "validation_loop", "slow_response", "confusing_control", "other"]},
        "video_time": {"type": "string"}, "element": {"type": "string"}, "evidence": {"type": "string"},
        "reproducible": {"type": "boolean"}}}},
    "form": {"type": "object", "required": ["reached", "last_field", "fields_touched", "submitted", "note"],
      "properties": {"reached": {"type": "boolean"}, "last_field": {"type": "string"}, "fields_touched": {"type": "array", "items": {"type": "string"}},
        "submitted": {"type": "boolean"}, "note": {"type": "string"}}},
    "exit_reason": {"type": "object", "required": ["category", "explanation", "counter_evidence"],
      "properties": {"category": {"type": "string", "enum": ["BUG", "FRICTION", "OFFER", "COPY", "TRUST", "STRUCTURE", "UNKNOWN"]},
        "explanation": {"type": "string"}, "counter_evidence": {"type": "string"}}},
    "fix_now": {"type": "string"},
    "test_later": {"type": "string"},
    "confidence": {"type": "number", "minimum": 0, "maximum": 1},
    "artefacts_noted": {"type": "array", "items": {"type": "string"}}
  }
}
```

- After 10 verdicts, Claude aggregates: an issue goes to FIX NOW when it appears in 2+ sessions or in 1 session with `reproducible: true` and log evidence; a category goes to TEST LATER when it appears in 2+ stratum B sessions and is absent in stratum C.

## Rules for /analytics
- Personal API key with `session_recording:read`, `session_recording_playlist:write`, `query:read`; nothing wider.
- Only sessions that started more than 24 hours ago; they are immutable after that.
- Selection is done in HogQL first; Claude reads every candidate's event log before picking, and picks by strata not by recency.
- Three strata, about 4 friction, 3 quiet abandonment, 3 converted; never fill a stratum from another.
- One session per person per stratum.
- Drop sessions with `click_count = 0` or under 10 active seconds; they are bots or blinks.
- Name the frustration thresholds in the report (PostHog: 3 clicks within 30px and 1s).
- Dead clicks need `capture_dead_clicks: true`; if the project lacks it, say so and rely on rrweb click-without-mutation from the stream.
- Form funnel: counts from `$autocapture` change events, order and last field from rrweb Focus/Blur/Input; autocapture has no focus events.
- Scroll depth from `$pageleave.$prev_pageview_max_scroll_percentage`; treat SPA values as upper bounds (posthog-js #4912).
- Render one window per session, Meta then FullSnapshot first, speed 4, skipInactive on, viewport from the Meta event, cap 3 minutes of video.
- Serve the player from localhost, not file://; log which assets 404ed and pass that list to Gemini as artefacts.
- Gemini via Files API, poll to ACTIVE, `gemini-3.8-flash`, 1 fps, default resolution, JSON schema response, event log attached with two clocks.
- Every Gemini claim must carry an `MM:SS`; discard claims without one.
- FIX NOW needs a mechanism plus log evidence or 2+ sessions; TEST LATER needs a stratum B pattern absent in stratum C.
- Pin the 10 sessions to a `collection` playlist named with the run date so a human can watch them in PostHog.
- Rate budget: stay under 240 list calls/min and 2400 queries/hour; snapshots fetched 20 blobs per call.
- Whole run is stateless: re-running on the same window must produce the same 10 sessions (order by deterministic keys, seed `rand()` with the run date).
- Cost note in the report: tokens in/out and dollars, expected under $0.10 per run on 3.8 Flash.
- Snapshot endpoint is unofficial; if it 401s with the personal key, stop and report, do not scrape with cookies unless the user says so.
