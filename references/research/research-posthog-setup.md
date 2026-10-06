# Research dossier - PostHog setup, heatmaps, replay and conversion events
Built 23 September 2026 · 51 sources opened · for /analytics
Next: fold into references/posthog-setup.md and code/posthog_setup.py

## Sources
1. Next.js - https://posthog.com/docs/libraries/next-js - 2026 - instrumentation-client.ts is the documented install; `defaults: '2026-05-30'`; identify after login; CSP wildcard `https://*.posthog.com`.
2. JavaScript web configuration - https://posthog.com/docs/libraries/js/config - 2026 - full option list; each `defaults` date and what it flips; rageclick config; `capture_heatmaps` replaces `enable_heatmaps`.
3. PostHogConfig type reference - https://posthog.com/docs/references/posthog-js/types/PostHogConfig - 2026 - `capture_pageview` accepts true/false/'history_change'/object; `capture_pageleave` accepts 'if_capture_pageview'; `scroll_root_selector`; `mask_personal_data_properties`.
4. JavaScript Web SDK - https://posthog.com/docs/libraries/js - 2026 - `defaults` is a dated config snapshot, explicit options override it.
5. Next.js rewrites reverse proxy - https://posthog.com/docs/advanced/proxy/nextjs - 2026 - three rewrites (static, array, catch-all) plus `skipTrailingSlashRedirect: true`; `ui_host`; middleware matcher caveat; do not name the path /analytics or /posthog.
6. Install PostHog - https://posthog.com/docs/getting-started/install - 2026 - the HTML snippet for WordPress/other sites, loads `/static/array.js` from `*-assets.i.posthog.com`.
7. Tracking pageviews in SPAs - https://posthog.com/tutorials/spa - 2026 - `defaults` recent date gives `capture_pageview: 'history_change'`; manual `$pageview` plus history_change makes duplicates.
8. Session replay privacy controls - https://posthog.com/docs/session-replay/privacy - 2026 - inputs masked by default; `maskInputOptions`, `maskInputFn`, `maskTextSelector`, `maskTextFn`, `ph-no-capture`; masking runs in the browser.
9. JS SDK features (rrweb defaults) - https://posthog.com/docs/libraries/js/features - 2026 - `blockClass 'ph-no-capture'`, `ignoreClass 'ph-ignore-input'`, `maskTextClass 'ph-mask'`, `maskAllInputs true`; `get_session_replay_url()`; `before_send` sampling of `$heatmap`/`$dead_click`.
10. How to control which sessions you record - https://posthog.com/docs/session-replay/how-to-control-which-sessions-you-record - 2026 - trigger groups (posthog-js 1.369.0+), sampling hash on session id, URL regex anchored `^...$`, strict minimum duration, sample rate applied after conditions.
11. Replay recording retention - https://posthog.com/docs/session-replay/data-retention - 2026 - Free 30 days, PAYG 90 days, Boost/Scale 1 year, Enterprise 5 years; changes apply to new recordings only.
12. Session replay pricing - https://posthog.com/docs/session-replay/pricing and https://posthog.com/pricing - 2026 - first 5,000 web recordings/month free, then $0.005 down to $0.0015.
13. Canvas recording - https://posthog.com/docs/session-replay/canvas-recording - 2026 - `captureCanvas: { canvasFps, canvasQuality }`, canvas not covered by DOM masking, project toggle.
14. Iframe recording - https://posthog.com/docs/session-replay/iframes - 2026 - `recordCrossOriginIframes: true` on both sides, only for iframes you control; third-party embeds (Calendly, GHL) render as blank placeholders.
15. Network recording - https://posthog.com/docs/session-replay/network-recording - 2026 - `recordHeaders`/`recordBody` off by default, bodies truncated at 1MB, explicit local false wins.
16. Session replay troubleshooting - https://posthog.com/docs/session-replay/troubleshooting - 2026 - `$has_recording`, `$recording_status`, `$sdk_debug_recording_script_not_loaded`, `$replay_sample_rate`; recorder.js lazy-loaded; blocked by ad blockers/CSP.
17. Session replay ingestion - https://posthog.com/docs/how-posthog-works/recordings-ingestion - 2026 - rrweb snapshots, batched to disk then flushed to S3; metadata in ClickHouse.
18. Heatmaps - https://posthog.com/docs/toolbar/heatmaps - 2026 - three maps (heatmap, scrollmap, clickmap); heatmap data does not bill; clickmap needs autocapture, scrollmap needs pageleave; WAF IPs.
19. heatmaps_list OpenAPI - https://posthog.com/docs/open-api-spec/heatmaps_list - 2026 - `GET /api/projects/{project_id}/heatmaps/`, params, "Heatmap data is retained for 90 days", scope `heatmap:read`.
20. posthog-js page-view.ts - https://github.com/PostHog/posthog-js/blob/main/packages/browser/src/page-view.ts - 2026 - exact `$prev_pageview_*` scroll and duration property names.
21. Scroll-depth health check - https://posthog.com/docs/health-checks/scroll-depth - 2026 - scroll depth rides on `$pageleave`, checked via `$prev_pageview_max_content_percentage`, needs autocapture on.
22. Autocapture - https://posthog.com/docs/product-analytics/autocapture - 2026 - tags captured, no form values captured, `data-ph-capture-attribute-*`, `$rageclick` 3 clicks/30px/1s, dead click definition, `capture_dead_clicks`, `.ph-no-deadclick`.
23. Capturing events - https://posthog.com/docs/product-analytics/capture-events - 2026 - `[object] [verb]` naming (`user signed up`); `$process_person_profile: false`.
24. JS usage - https://posthog.com/docs/libraries/js/usage - 2026 - `$set`/`$set_once` in capture; `{ transport: 'sendBeacon', send_instantly: true }` for pre-navigation events; `register`/`register_once`.
25. UTM segmentation - https://posthog.com/docs/data/utm-segmentation - 2026 - five utm params auto-captured to event, person (latest + `$initial_*`) and session (`$entry_gclid`, `$entry_gad_source`); `custom_campaign_params`.
26. Event properties reference - https://posthog.com/docs/data/events - 2026 - `$gclid`, `$utm_*` as event properties; bounce rate relies on `$pageleave`.
27. Identify users - https://posthog.com/docs/getting-started/identify-users - 2026 - anonymous events up to 4x cheaper; identify links anon id to distinct id.
28. Python SDK - https://posthog.com/docs/libraries/python - 2026 - `Posthog(token, host=...)`, `capture('event', distinct_id=..., properties=...)`, `$set_once`, `shutdown()` flushes, `capture_immediate()`.
29. Capture API - https://posthog.com/docs/api/capture - 2026 - `POST https://us.i.posthog.com/i/v0/e/` and `/batch/`, body fields, 20MB limit, 200 even for dropped events.
30. API overview - https://posthog.com/docs/api - 2026 - private host `us.posthog.com`/`eu.posthog.com`; rate limits 480/min 4800/h CRUD, 240/min 1200/h analytics, 2400/h query; pagination; `/users/@me/`; `phx_` keys auto-rolled if leaked.
31. Personal API keys - https://posthog.com/docs/api/personal-api-keys - 2026 - create at Settings > user-api-keys, choose scopes, max 10 keys, `Authorization: Bearer`, key shown once.
32. organizations_projects_partial_update OpenAPI - https://posthog.com/docs/open-api-spec/organizations_projects_partial_update - 2026 - `PATCH /api/organizations/{organization_id}/projects/{id}/`, scope `project:write`, every replay/heatmap field with type and description.
33. organizations_projects_list OpenAPI - https://posthog.com/docs/open-api-spec/organizations_projects_list - 2026 - `GET /api/organizations/{organization_id}/projects/`, scope `project:read`, returns `id`, `api_token`, `name`.
34. users_retrieve OpenAPI - https://posthog.com/docs/open-api-spec/users_retrieve - 2026 - `GET /api/users/@me/`, scope `user:read`, response has `team.id`, `team.api_token`, `organization.id`, `organization.teams`.
35. actions_create OpenAPI - https://posthog.com/docs/open-api-spec/actions_create - 2026 - `POST /api/projects/{project_id}/actions/`, scope `action:write`, `ActionStepJSON` fields and matching enums.
36. insights_create OpenAPI - https://posthog.com/docs/open-api-spec/insights_create - 2026 - `POST /api/projects/{project_id}/insights/`, scope `insight:write`, `query` is `InsightVizNode{source: TrendsQuery|FunnelsQuery}`, `dashboards` deprecated in favour of `dashboard_tiles`.
37. dashboards_create OpenAPI - https://posthog.com/docs/open-api-spec/dashboards_create - 2026 - `POST /api/projects/{project_id}/dashboards/`, scope `dashboard:write`, fields `name`, `description`, `pinned`, `tags`, `use_template`.
38. Query API - https://posthog.com/docs/api/queries - 2026 - `POST /api/projects/{project_id}/query/` with `{"query":{"kind":"HogQLQuery","query":"..."}}`, scope `query:read`, 240/min, 2400/h, 3 concurrent.
39. PostHog/posthog team.py - https://github.com/PostHog/posthog/blob/master/posthog/api/team.py - 2026 - server validators: `session_recording_masking_config` keys, `session_replay_config` keys, `session_recording_linked_flag` shape, trigger groups v2 schema, `session_recording_trigger_match_type_config` all|any.
40. Actions - https://posthog.com/docs/data/actions - 2026 - retroactive; selectors supported (`[data-attr=...]`, `#id`, `.class`, child combinators), wildcards unsupported; multiple fields AND together.
41. Persistence and cookies - https://posthog.com/docs/libraries/js/persistence - 2026 - `persistence: 'memory'`; `set_config({persistence: ...})` on consent.
42. Controlling data collection - https://posthog.com/docs/privacy/data-collection and https://posthog.com/tutorials/cookieless-tracking - 2026 - do not gate the snippet; `opt_out_capturing_by_default` then `opt_in_capturing()`; `cookieless_mode` `always`/`on_reject` needs "Cookieless server hash mode" project setting; IP capture toggle, EU default off.
43. GDPR and CCPA compliance - https://posthog.com/docs/privacy/gdpr-compliance and https://posthog.com/docs/privacy/ccpa-compliance - 2026 - EU Cloud Frankfurt; DPA as processor; CCPA notice at collection and 45-day deletion.
44. AI wizard - https://posthog.com/docs/ai-engineering/ai-wizard and https://github.com/PostHog/wizard - 2026 - `npx -y @posthog/wizard@latest`; uses Anthropic/OpenAI models through PostHog's gateway; writes .env, client and server SDK code, creates events, insights, dashboards; `--region eu`, `--ci`, `--api-key`, `--no-telemetry`.
45. MCP and FAQ - https://posthog.com/docs/model-context-protocol, /faq, /tools - 2026 - `https://mcp.posthog.com/mcp`, OAuth or `Authorization: Bearer phx_...`, `x-posthog-project-id`, `x-posthog-read-only`, tools `action-create`, `project-create`, insight/dashboard tools.
46. Calendly advanced embed - https://calendly.com/help/advanced-calendly-embed-for-developers - 2026 - `window.postMessage` events `calendly.event_scheduled` etc., origin `https://calendly.com`.
47. GoHighLevel GTM tracking (practitioner) - https://www.optizent.com/blog/how-to-track-gohighlevel-form-submissions-and-booking-completions-using-google-tag-manager/ and https://krmdigital.uk/blog/form-tracking-connectorhq/ - 2025 - booking iframe posts `['msgsndr-booking-complete', {calendarId}]` from `https://api.leadconnectorhq.com`.
48. rrweb performance benchmark (Highlight, now LaunchDarkly) - https://launchdarkly.com/docs/tutorials/session-replay-performance - Oct 2023 - rrweb added 0.017-0.07s per interaction, 6-60MB memory, 21-25% CPU on an extreme React app.
49. Rollbar replay script comparison - https://rollbar.com/blog/session-replay-scripts-performance/ - Sep 2025 - PostHog core bundle 52.4KB, replay lazy-loaded.
50. Contentsquare heatmap guide (practitioner) - https://contentsquare.com/guides/heatmaps/ - 2026 - collect at least 2,000-3,000 pageviews before reading a heatmap.
51. Session recording remote config type - https://posthog.com/docs/references/posthog-js/types/SessionRecordingRemoteConfig - 2026 - what the SDK receives from the project: `sampleRate`, `minimumDurationMilliseconds`, `linkedFlag`, `urlTriggers`, `eventTriggers`, `triggerMatchType`, `masking`, `networkPayloadCapture`, `recordCanvas`, `triggerGroups`.

## Findings

### 1. Next.js 15.3+ App Router install
- (a) Documented install is `instrumentation-client.ts` at the project root, for both app and pages router. Content is three lines: import posthog, `posthog.init(process.env.NEXT_PUBLIC_POSTHOG_PROJECT_TOKEN!, { api_host: process.env.NEXT_PUBLIC_POSTHOG_HOST, defaults: '2026-05-30' })`. Source 1.
- (a) No provider component is needed with instrumentation-client. "Once initialized in instrumentation-client.js|ts, import posthog from 'posthog-js' anywhere and call the methods you need." React hooks from `@posthog/react` also work off the singleton. Source 1.
- (a) Values passed to `posthog.init` in instrumentation-client "remain fixed for the entire session", so consent-driven changes must go through `posthog.set_config()` or `opt_in_capturing()`, not re-init. Sources 1, 41.
- (a) Env vars must start with `NEXT_PUBLIC_`: `NEXT_PUBLIC_POSTHOG_PROJECT_TOKEN` and `NEXT_PUBLIC_POSTHOG_HOST=https://us.i.posthog.com` (EU: `https://eu.i.posthog.com`). Source 1.
- (a) `defaults` ladder, verbatim from the config page: `'2025-05-24'` (`capture_pageview` defaults to `'history_change'`); `'2025-11-30'` (+ `session_recording.strictMinimumDuration` and `rageclick.content_ignorelist`); `'2026-01-30'` (+ `external_scripts_inject_target: 'head'` to avoid SSR hydration errors); `'2026-05-30'` (+ `persistence_save_debounce_ms: 250`, `split_storage: true`, `detect_google_search_app: true`, expanded rageclick defaults); `'2026-06-25'` (+ `session_recording.streamNetworkBody: true`); `'2026-08-29'` (+ `cookieWinsOnConflict: true`); `'2026-08-30'` (+ `session_recording.captureJsonLd: true`). Docs currently recommend `'2026-05-30'`. Source 2.
- (a) `capture_pageview`: `true` = page-load pageviews only; `'history_change'` = initial plus pathname changes via the History API (what App Router needs). Adding a manual `usePathname` `$pageview` effect on top of `history_change` produces duplicates, so pick one. Sources 3, 7.
- (a) `capture_pageleave` default `true`; also accepts `'if_capture_pageview'`. Scroll depth and bounce rate depend on `$pageleave`, so leave it on. Sources 2, 3, 21, 26.
- (a) `autocapture` default `true`, does not affect pageviews. `person_profiles` default `identified_only`; anonymous events are up to 4x cheaper, so do not set `'always'` on a marketing site. Sources 2, 27.
- (a) `external_scripts_inject_target: 'head'` (on by `defaults >= '2026-01-30'`) exists specifically to stop Next.js hydration errors when PostHog injects the replay/surveys scripts. Source 2.
- (a) Reverse proxy via `next.config.js` rewrites: three rules in this order, `/<path>/static/:path*` to `https://us-assets.i.posthog.com/static/:path*`, `/<path>/array/:path*` to `https://us-assets.i.posthog.com/array/:path*`, `/<path>/:path*` to `https://us.i.posthog.com/:path*`, plus `skipTrailingSlashRedirect: true`. Replace `us` with `eu`. SDK then uses `api_host: '/<path>'` and `ui_host: 'https://us.posthog.com'` (or eu). Source 5.
- (a) Proxy caveats: "Don't use obvious path names like /analytics, /tracking, /telemetry, or /posthog"; an existing `middleware.ts`/`proxy.ts` matcher must exclude the path (`'/((?!api|yourpath|_next|_vercel|.*\\..*).*)'`) or `POST /yourpath/s` gets 307'd and replay silently dies while `/static/*.js` still loads; rewrites push replay bytes (1-5MB per session) through Vercel bandwidth, and PostHog's managed reverse proxy is free for Cloud users. Source 5.
- (a) CSP if the site sets one: `script-src 'self' https://*.posthog.com; connect-src 'self' https://*.posthog.com; worker-src 'self' blob: data:;`. Missing `connect-src` causes silent zero-event installs. Source 1.
- (a) Hosts: public ingestion `https://us.i.posthog.com` / `https://eu.i.posthog.com`; private REST `https://us.posthog.com` / `https://eu.posthog.com`; assets `https://us-assets.i.posthog.com` / `https://eu-assets.i.posthog.com`. Sources 30, 43 (EU data is in Frankfurt).
- (a) WordPress/other sites: paste the HTML snippet from the install page into `<head>` and set `api_host` and `defaults`. The snippet derives the asset host by replacing `.i.posthog.com` with `-assets.i.posthog.com` and loads `/static/array.js`. Source 6.
- (a) Identify: call `posthog.identify('<stable id>')` after login, never a shared literal like "anonymous"; `posthog.reset()` on logout. For a lead-gen site with no login, skip identify and keep the anonymous distinct id. Source 1.

### 2. Session replay
- (a) Replay is controlled by project settings first. `posthog.startSessionRecording()` "will have no effect if session recordings are disabled in your PostHog Project Settings." The SDK receives the project config as `SessionRecordingRemoteConfig` (`sampleRate`, `minimumDurationMilliseconds`, `linkedFlag`, `urlTriggers`, `eventTriggers`, `triggerMatchType`, `masking`, `networkPayloadCapture`, `recordCanvas`, `triggerGroups`). Sources 10, 51.
- (a) SDK `session_recording` object rides on rrweb. PostHog defaults that differ from rrweb: `blockClass: 'ph-no-capture'`, `ignoreClass: 'ph-ignore-input'`, `maskTextClass: 'ph-mask'`, `maskAllInputs: true`. "The defaults for maskAllInputs, maskTextSelector and blockSelector will change depending on your masking configuration in the session replay section of your project settings." Source 9.
- (a) Masking options: `maskAllInputs` (default true), `maskInputOptions` (per input type, e.g. `password: true`, `tel`, `email`, `text`, `textarea`, `select`), `maskInputFn(text, element)`, `maskTextSelector` ("*" masks all non-input text; `.email, #sensitive` masks specific), `maskTextFn(text)` for regex masking, `ph-no-capture` class replaces the element with a same-size block and also suppresses autocapture on it. Masking happens in the browser so masked text never leaves the device. Source 8.
- (a) `blockSelector`: a CSS selector string, PATCHable at project level via `session_recording_masking_config.blockSelector`. Server accepts only `maskAllInputs` (bool), `maskTextSelector` (string), `blockSelector` (string) in that config. Source 39.
- (a) `recordCrossOriginIframes: true` must be set on both parent and iframe and both origins must be authorized recording domains; it only works for iframes you control. Third-party embeds (Calendly, GHL calendar) "appear as an empty placeholder" and cannot be recorded. Source 14.
- (a) Minimum duration: project field `session_recording_minimum_duration_milliseconds`, integer 0-30000. Strict mode (`session_recording.strictMinimumDuration: true`, default with `defaults >= '2025-11-30'` on posthog-js 1.291.0+) checks buffered data, clears the buffer on navigation, and only starts sending once one page has enough continuous data. Sources 10, 32.
- (a) Sampling: `session_recording_sample_rate` is a decimal string `"0.00"`-`"1.00"` (pattern `^-?\d{0,1}(?:\.\d{0,2})?$`). Deterministic per session id hash. "Our recommendation is to start with capturing 100% of sessions and decrease it as needed." The sample rate applies after a trigger group's conditions match. Sources 10, 32.
- (a) Trigger groups (posthog-js 1.369.0+, admin permission to edit) supersede legacy fields; PATCH field `session_recording_trigger_groups`, "If present, takes precedence over legacy trigger fields." Schema from the server: `{"version": 2, "groups": [{"id", "name", "sampleRate": 0-1, "minDurationMs": 0-30000, "conditions": {"matchType": "any"|"all", "events": [...], "urls": [{"url": "regex", "matching": "regex"}], "flag": "key" | {"id","key","variant"}}}]}`. Deleting the last group auto-creates "Record all sessions" at 100%. Sources 10, 32, 39.
- (a) Legacy fields still accepted: `session_recording_url_trigger_config` (array of `{url, matching}`), `session_recording_url_blocklist_config`, `session_recording_event_trigger_config` (array of event names, name match only, no property filters), `session_recording_trigger_match_type_config` (`"all"|"any"|null`), `session_recording_linked_flag` (`{"id": int, "key": str}` or with `"variant"`). URL trigger regexes are wrapped in `^` and `$`. Sources 10, 32, 39.
- (a) Canvas: project toggle is `session_replay_config: {"record_canvas": true}`; SDK `session_recording.captureCanvas: { canvasFps: 0-12 (default 4), canvasQuality: "0"-"1" (default "0.4") }`. Canvas is not covered by DOM masking. Sources 13, 39.
- (a) Network: `session_recording_network_payload_capture_config` accepts only `recordHeaders` and `recordBody` booleans; both off by default; bodies truncated at 1MB; a local `false` overrides remote `true`. Sources 15, 39.
- (a) Other project fields: `session_recording_opt_in` (bool, master switch), `recording_domains` (array of origins allowed to record replays and heatmaps, empty = all), `session_recording_retention_period` (`30d`|`90d`|`1y`|`5y`, plan-gated), `capture_performance_opt_in`, `capture_console_log_opt_in`. Sources 32, 39.
- (a) Retention: Free up to 30 days, Pay-as-you-go up to 90 days, Boost and Scale up to 1 year, Enterprise up to 5 years; a change only affects recordings captured from then on; expired recordings cannot be restored; export to JSON to keep one. Source 11.
- (a) Free tier: first 5,000 web recordings per month free (2,500 mobile), then $0.005 (5,001-15,000), $0.0035 (to 50,000), $0.002 (to 150,000), $0.0017 (to 500,000), $0.0015 above. Set a billing limit. Source 12.
- (a) Performance: replay code (`recorder.js`) is lazy-loaded separately from the core bundle; heavy SVG/Lottie animations may be throttled or ignored; canvas capture "can have a performance impact on some sites". Diagnostics on later events in a session: `$has_recording`, `$recording_status` (`buffering`, `active`, `sampled`, `sampled_out`), `$sdk_debug_recording_script_not_loaded` (ad blocker or CSP), `$replay_sample_rate`, `$replay_minimum_duration`. Sources 13, 16, 49.
- (b) Independent rrweb benchmark (Highlight, Oct 2023, Puppeteer on a React stress app): +0.017s per interaction, +6MB, +21% CPU at 100 items; +0.07s, +60MB, +25% CPU at 500 items; conclusion "there isn't a very large hit to user experience". PostHog uses rrweb so this is the right order of magnitude. Source 48.
- (a) Ingestion: snapshots go to a dedicated capture service, are batched to disk and periodically flushed to S3; metadata lands in ClickHouse. Docs give no SLA for when a recording appears; the troubleshooting page says to check a later event in the session for `$has_recording: true`. Sources 16, 17.

### 3. Heatmaps
- (a) Three views: Heatmap (mouse movements, clicks, dead clicks, rageclicks, by coordinate, includes clicks on non-clickable areas), Scrollmap (from `$pageview` and `$pageleave` data), Clickmap (autocapture element clicks). "Heatmap data is captured along with other events, so it doesn't contribute to your bill, but the clickmap requires autocapture and the scrollmap requires pageleave events." Source 18.
- (a) Enable via project setting (`heatmaps_opt_in: true`, description "Enables heatmap recording on pages that host posthog-js") or SDK `capture_heatmaps` (boolean or `HeatmapConfig`); `capture_heatmaps: undefined` falls back to the project setting; `enable_heatmaps` is deprecated. Sources 2, 18, 32.
- (a) Heatmap payloads are sent as `$heatmap` events (the `before_send` sampling example filters `event.event === '$heatmap'`). Source 9.
- (a) Scroll depth properties, sent on `$pageleave` and on the next `$pageview`, exact names from the SDK: `$prev_pageview_id`, `$prev_pageview_pathname`, `$prev_pageview_duration` (seconds), `$prev_pageview_last_scroll`, `$prev_pageview_last_scroll_percentage`, `$prev_pageview_max_scroll`, `$prev_pageview_max_scroll_percentage`, `$prev_pageview_last_content`, `$prev_pageview_last_content_percentage`, `$prev_pageview_max_content`, `$prev_pageview_max_content_percentage`. PostHog's health check keys on `$prev_pageview_max_content_percentage`; it goes missing when autocapture or DOM/scroll tracking is disabled. `scroll_root_selector` changes the scroll root (e.g. `main`). Sources 3, 20, 21.
- (a) Toolbar: heatmap icon on the toolbar; in-app viewer at /heatmaps (beta, needs the feature preview) overlays your site in an iframe, so CSP must allow framing by PostHog, or use "View heatmap" from a recording. Aggregation: event count (default) or unique users; viewport tolerance; fixed-element handling; wildcard URLs `https://site.com/products/*`. Allow PostHog WAF IPs (US `44.205.89.55`, `52.4.194.122`, `44.208.188.173`; EU `3.75.65.221`, `18.197.246.42`, `3.120.223.253`) plus Browserless IPs for screenshots. Source 18.
- (a) Heatmap API: `GET /api/projects/{project_id}/heatmaps/` with `type` (`click` default, `rageclick`, `mousemove`, `scrolldepth`), `url_exact` or `url_pattern`, `date_from` (default `-7d`), `date_to`, `viewport_width_min/max`, `aggregation` (`total_count`|`unique_visitors`), `limit` (500), `offset`; scope `heatmap:read`. "Heatmap data is retained for 90 days." Source 19.
- (c) Minimum traffic: PostHog publishes no threshold. Contentsquare's guide says "collect at least 2,000-3,000 pageviews before drawing conclusions"; a 50-visit heatmap can show one person's behaviour as a hot spot. Use 2,000 pageviews per URL as the rule of thumb. Source 50.

### 4. Autocapture and form tracking
- (a) Autocapture records clicks, input changes and form submissions on `a`, `button`, `form`, `input`, `select`, `textarea`, `label`, plus `contenteditable` changes. "To prevent accidental sensitive data capture, we do not automatically capture form values from form submissions." Password fields are excluded from element text. Source 22.
- (a) Config knobs: `autocapture: { url_allowlist, url_ignorelist, dom_event_allowlist: ['click','change','submit'], element_allowlist, css_selector_allowlist, css_selector_ignorelist (default ['.ph-no-autocapture','[data-ph-no-autocapture]'], custom list replaces defaults), element_attribute_ignorelist, capture_copied_text }`. `mask_all_text` and `mask_all_element_attributes` strip text/attrs from autocapture. Sources 2, 22.
- (a) `data-ph-capture-attribute-<key>="<value>"` on a form or element adds `<key>: <value>` to that element's autocapture events, the sanctioned way to label a form submit. Source 22.
- (a) `$rageclick`: three clicks each within 30 pixels and 1 second of the previous; `rageclick` option is boolean or `{ css_selector_ignorelist, content_ignorelist (default true with defaults >= 2025-11-30, ignores next/previous/>/<, plus +/-/−/– from 2026-05-30), ignore_text_selection }`; `.ph-no-rageclick` opts an element out. Sources 2, 22.
- (a) `$dead_click`: "a click which isn't followed by a change to the page." Enable via project setting `capture_dead_clicks: true` (description in the API: "Enables capturing clicks that had no effect") or SDK `capture_dead_clicks: true | { css_selector_ignorelist }`; `.ph-no-deadclick` excludes an element. Heatmaps already record dead-click coordinates for free; autocaptured `$dead_click` events bill as normal events. Sources 22, 32.
- (a) Field drop-off funnel: autocapture emits `$autocapture` with `$event_type: 'change'` per input but no values, so per-field steps are possible from autocapture alone via actions on `[name=...]` selectors. There is no official PostHog tutorial for focus/blur field tracking; the pattern below (custom `form field focused` / `form field completed` events keyed by field name, no values) is inferred from the capture docs and naming guidance. Sources 22, 23, 40.
- (a) Actions are retroactive and can match autocapture by text, URL and CSS selector (attribute selectors like `[data-attr="value"]` recommended; wildcards and hyphenated classes unsupported); multiple match fields AND together; multiple steps OR together. Sources 35, 40.

### 5. Custom conversion events
- (a) Naming: "We recommend using a [object] [verb] format for your event names ... project created, user signed up, or invite sent." So: `form submitted`, `phone link tapped`, `text link tapped`, `booking made`. Source 23.
- (a) `posthog.capture(event, properties, options)`; properties may carry `$set` and `$set_once`; options include `send_instantly: true` and `transport: 'sendBeacon'` for events fired right before navigation (tel:, sms:, external booking links). `transport` alone does not bypass the queue. Source 24.
- (a) Fire `form submitted` in the success path (after the fetch/server action resolves), never on mount or on route change, and never alongside an autocapture-based action for the same conversion, or counts double. Duplicate-pageview guidance shows PostHog counts every capture. Sources 7, 24.
- (a) Dedupe per session: `posthog.register_for_session()` and `posthog.get_session_id()` exist in the SDK surface; store a `form_submitted_<formId>` flag in `sessionStorage` (or `register_for_session`) before capturing and skip if present. Server-side, use a per-lead idempotency key. Source 6 (method list in snippet), 24.
- (a) tel:/sms: links: autocapture already logs the `a` click with `href` in the element chain, but a named event is what the funnel needs; attach one delegated click listener on `a[href^="tel:"], a[href^="sms:"]`, capture `phone link tapped` / `text link tapped` with `{ href, link_text, page_path }` and `{ send_instantly: true, transport: 'sendBeacon' }`. Sources 22, 24.
- (a/c) Booking: Calendly posts `window.postMessage` events to the parent; official listener checks `e.origin === "https://calendly.com" && e.data.event?.startsWith("calendly.")`; fire `booking made` on `calendly.event_scheduled` (earlier funnel steps: `calendly.event_type_viewed`, `calendly.date_and_time_selected`); payload at `e.data.payload`. GoHighLevel (LeadConnector) calendars post an array `['msgsndr-booking-complete', {calendarId: '...'}]` from `https://api.leadconnectorhq.com`; this is practitioner-documented, not GHL-documented, so verify in the browser console before shipping. Neither iframe can be replayed (source 14). Sources 46, 47.
- (a) Server-side booking capture (webhook): `pip install posthog`; `Posthog('<token>', host='https://us.i.posthog.com')`; `posthog.capture('booking made', distinct_id=..., properties={...})`; call `posthog.shutdown()` before a serverless function exits or use `capture_immediate()`. Python 7.x needs Python 3.10+. Raw HTTP alternative: `POST https://us.i.posthog.com/i/v0/e/` with `{"api_key": "<project token>", "event": "booking made", "distinct_id": "...", "properties": {...}, "timestamp": "ISO 8601"}`; returns 200 even when the event is dropped (missing distinct_id), so validate before sending. Sources 28, 29.
- (a) Linking a server event to the browser person: pass the browser's `posthog.get_distinct_id()` through the form/booking payload, or enable `tracing_headers: ['api.yourdomain.com']` so fetches carry `X-POSTHOG-DISTINCT-ID` and `X-POSTHOG-SESSION-ID`. Sources 1, 27.
- (a) Attribution: `utm_source/medium/campaign/content/term` are auto-captured as event properties, latest and `$initial_*` person properties, and `$entry_*` session properties (`$entry_gclid`, `$entry_gad_source`); `$gclid` also appears as an event property. Add more click ids with `custom_campaign_params: ['gbraid', 'wbraid', 'msclkid']`. Send `$set_once: { first_gclid, first_landing_path }` on `form submitted` when you need it on the person even for anonymous-first visitors. `mask_personal_data_properties: true` strips gclid/fbclid from URLs if privacy requires it. Sources 3, 25, 26.

### 6. REST API for configuration
- (a) Personal API key: Settings > Personal API keys (`/settings/user-api-keys`) > "+ Create a personal API Key"; label it, pick scopes, copy once. Max 10 keys per user. Prefix `phx_`. GitHub secret scanning auto-rolls leaked keys. Auth: `Authorization: Bearer <key>` (or `personal_api_key` in the body). Sources 30, 31.
- (a) Scopes required by /analytics, from the OpenAPI security blocks: `user:read` (`/api/users/@me/`), `project:read` (list projects), `project:write` (PATCH project settings), `action:write`, `insight:write`, `dashboard:write`, `query:read`, `heatmap:read`. Access scope: organization-wide, specific projects, or all projects. Sources 19, 31-38.
- (a) Discover the project: `GET https://us.posthog.com/api/users/@me/` returns `team.id`, `team.api_token`, `team.project_id`, `organization.id`, `organization.teams` and `organizations[]`. Or `GET /api/organizations/{organization_id}/projects/` (paginated `results[]` with `id`, `api_token`, `name`). Sources 33, 34.
- (a) Read/PATCH project settings: `PATCH /api/organizations/{organization_id}/projects/{id}/` "Update one or more of a project's settings. Only the fields included in the request body are changed." Schema `PatchedProjectBackwardCompat` "is a superset of TeamSerializer's, so a request rewritten from /api/environments/ onto /api/projects/ never loses a field", which is the documented hint that `PATCH /api/projects/{id}/` also works (inferred, not shown as its own operation in the pages I opened). Source 32.
- (a) PATCHable fields confirmed in the schema with types: `session_recording_opt_in` bool; `session_recording_sample_rate` decimal string; `session_recording_minimum_duration_milliseconds` int 0-30000; `session_recording_linked_flag` object; `session_recording_network_payload_capture_config` object; `session_recording_masking_config` object; `session_recording_url_trigger_config` array; `session_recording_url_blocklist_config` array; `session_recording_event_trigger_config` array of strings; `session_recording_trigger_match_type_config` string; `session_recording_trigger_groups` object; `session_recording_retention_period` enum; `session_replay_config` object; `recording_domains` array of origins; `heatmaps_opt_in` bool; `capture_dead_clicks` bool; `autocapture_opt_out` bool; `autocapture_exceptions_opt_in` bool; `autocapture_web_vitals_opt_in` bool; `capture_performance_opt_in` bool; `surveys_opt_in` bool; `anonymize_ips` bool; `cookieless_server_hash_mode` enum; `app_urls` array; `name`; `product_description`; `tags`. Read-only: `id`, `api_token`, `secret_api_token`, `organization`, `heatmaps_screenshot_secret`. Source 32, 39.
- (a) `session_replay_config` is merged key-by-key with the existing value on the server, other JSON fields are replaced whole. Source 39.
- (a) Create an action: `POST /api/projects/{project_id}/actions/` with `name` (unique per project, max 400), `description`, `tags`, `steps[]`. Step fields: `event`, `properties[]` (`{key, value, operator, type}`), `selector`, `tag_name`, `text`, `text_matching` (`contains|regex|exact`, default exact), `href`, `href_matching` (default exact), `url`, `url_matching` (default contains). Steps OR together. Returns 201 with the action. Source 35.
- (a) Create an insight: `POST /api/projects/{project_id}/insights/` with `name`, `description`, `tags`, `favorited`, `query` (`{"kind":"InsightVizNode","source":{"kind":"TrendsQuery"|"FunnelsQuery","series":[{"kind":"EventsNode","event":"form submitted","math":"total"}],"dateRange":{...}}}`), and `dashboards: [id]` (marked DEPRECATED, "use dashboard_tiles instead", but still the write path on create since `dashboard_tiles` is read-only). Scope `insight:write`. Source 36.
- (a) Create a dashboard: `POST /api/projects/{project_id}/dashboards/` with `name`, `description`, `pinned`, `tags`, optional `use_template` or `use_dashboard`; `tiles` and `filters` are read-only on this schema. Scope `dashboard:write`. Source 37.
- (a) Verify counts: `POST /api/projects/{project_id}/query/` with `{"query":{"kind":"HogQLQuery","query":"select event, count() from events where timestamp > now() - interval 1 hour group by event"}}`; response has `results`, `columns`, `is_cached`. Limits 240/min, 2400/h, 3 concurrent, 10s execution. Source 38.
- (a) Rate limits: CRUD 480/min and 4800/h; analytics 240/min and 1200/h; `events/values` 60/min; limits are per team, shared by all keys. Public capture endpoints have no request rate limit but return `quota_limited` when over billing quota. Pagination via `next`/`previous`, page size usually 100. Body max 20MB. Source 30.

### 7. Privacy and consent
- (a) Do not gate the snippet behind consent; load PostHog with `opt_out_capturing_by_default: true` and call `posthog.opt_in_capturing()` / `posthog.opt_out_capturing()` from the CMP callback. Opting out stops "all data ... This includes any autocaptures, manual captures, and session replays." `opt_out_capturing_persistence_type` can be `local_storage` or `cookies`. Source 42.
- (a) Cookieless: `cookieless_mode: 'always'` (no banner needed for PostHog itself, no cookies or storage, server-side privacy-preserving hash for uniques, do not call `identify()`, `alias()` events are dropped, set `person_profiles: 'never'`) or `'on_reject'` (no storage and no events until consent is given or denied; use `posthog.get_explicit_consent_status()` to decide whether to show the banner). Requires the project toggle "Cookieless server hash mode" under Project settings > Web analytics (API field `cookieless_server_hash_mode`), otherwise cookieless events are ignored. Sources 2, 42.
- (a) Memory persistence alternative: `persistence: 'memory'` keeps everything for the page view only; switch with `posthog.set_config({ persistence: consent === 'yes' ? 'localStorage+cookie' : 'memory' })` without re-init. Source 41.
- (a) IP: project-level "IP data capture" toggle (`anonymize_ips: true` drops the IP from every ingested event); EU organisations default to IP capture disabled. Source 42, 32.
- (a) Masking phone numbers in replays: inputs are masked by default (`maskAllInputs: true`), so a `<input type="tel">` is already stars. For phone numbers rendered as text or `tel:` link labels, use `maskTextSelector: 'a[href^="tel:"], .phone'` or a `maskTextFn` regex, or `ph-mask`/`ph-no-capture` classes. Masking runs client side. Source 8, 9.
- (a) GDPR: prefer EU Cloud (Frankfurt) for EU audiences, sign the DPA (PostHog is processor under Art. 28), banner for cookies or go cookieless, deletion tooling for right to be forgotten. CCPA: notice at collection, honour delete requests within 45 days, US Cloud recommended. Source 43.

### 8. Wizard, MCP, CLI
- (a) Wizard: `npx -y @posthog/wizard@latest` (also `npx @posthog/wizard`). It authenticates (OAuth), installs SDKs, scans the codebase, creates custom events "based on real product flows", writes `.env`, instruments client and server, generates insights and dashboards in the app, and optionally installs the MCP server. Uses "AI models from Anthropic or OpenAI, routed through PostHog's AI gateway" to read source files. Flags: `--region eu` (default us), `--signup`, `--install-dir`, `--ci`, `--api-key phx_...`, `--no-telemetry`, `--debug`; telemetry on by default. Subcommands: `wizard audit session-replay|autocapture|events|web-analytics|identify|all`, `wizard replay-vision`, `wizard mcp add|remove`, `wizard migrate`, `wizard self-driving`. Supports Next.js, React, Astro, Nuxt, SvelteKit, Python and more. Source 44.
- (a) MCP: remote server `https://mcp.posthog.com/mcp`; install with `npx @posthog/wizard mcp add` or a client config `{"mcpServers":{"posthog":{"url":"https://mcp.posthog.com/mcp","headers":{"Authorization":"Bearer phx_..."}}}}`; OAuth preferred; a personal key made with the "MCP Server" preset works. Pin with headers `x-posthog-project-id` / `x-posthog-organization-id`; `x-posthog-read-only: true` or `?readonly` disables write tools; `tools` query param filters tools. Tools include `action-create`, `action-update`, `actions-get-all`, `project-create`, insight and dashboard creators, HogQL query. There is also a Claude Code plugin: `claude plugin install posthog`. Sources 44, 45.
- (a) What the wizard changes in Next.js is not enumerated in its README; the docs show the outcome as instrumentation-client init plus a `posthog-node` client and env vars. Treat wizard output as a starting point and diff it against the snippets below. Sources 1, 44.

## Exact API facts (verified)
- Base URLs: public capture `https://us.i.posthog.com` (EU `https://eu.i.posthog.com`); private REST `https://us.posthog.com` (EU `https://eu.posthog.com`). Confirmed (source 30).
- Auth header for private endpoints: `Authorization: Bearer phx_...`. Confirmed (source 31).
- Who am I / project discovery. Confirmed (source 34).
```http
GET /api/users/@me/
scope: user:read
response: { "team": { "id": 12345, "project_id": 12345, "api_token": "phc_...", "name": "..." }, "organization": { "id": "uuid", "teams": [...] }, "organizations": [...] }
```
- List projects. Confirmed (source 33).
```http
GET /api/organizations/{organization_id}/projects/?limit=100
scope: project:read
response: { "count": n, "next": url|null, "previous": null, "results": [ { "id": 12345, "api_token": "phc_...", "name": "...", "timezone": "..." } ] }
```
- Read a project. Inferred from the PATCH schema and the "@current"/projects family; the retrieve operation page was not opened. Use `GET /api/organizations/{organization_id}/projects/{id}/` and expect the same fields as the PATCH response.
- Update project settings. Confirmed endpoint, scope, field names and types (sources 32, 39). `PATCH /api/projects/{id}/` is the legacy alias implied by the schema description, inferred.
```http
PATCH /api/organizations/{organization_id}/projects/{id}/
scope: project:write
Content-Type: application/json

{
  "session_recording_opt_in": true,
  "session_recording_sample_rate": "1.00",
  "session_recording_minimum_duration_milliseconds": 2000,
  "session_recording_masking_config": { "maskAllInputs": true, "maskTextSelector": "a[href^='tel:'], .phone", "blockSelector": null },
  "session_recording_network_payload_capture_config": { "recordHeaders": false, "recordBody": false },
  "session_replay_config": { "record_canvas": false },
  "recording_domains": ["https://www.example.com"],
  "heatmaps_opt_in": true,
  "capture_dead_clicks": true,
  "autocapture_opt_out": false,
  "capture_performance_opt_in": true
}
```
- Notes on the PATCH body: `session_recording_sample_rate` must be a string matching `^-?\d{0,1}(?:\.\d{0,2})?$`; `session_recording_masking_config` only accepts `maskAllInputs` (bool), `maskTextSelector` (string), `blockSelector` (string), so omit `blockSelector` rather than sending null (the null-vs-omit behaviour was not tested); `session_replay_config` only accepts `record_canvas` and `ai_config` and is merged key by key; `session_recording_retention_period` is one of `30d`, `90d`, `1y`, `5y` and is plan gated (expect 400/403 on Free above `30d`); `session_recording_linked_flag` must be `{"id": int, "key": str}` or with `variant`. Confirmed (source 39).
- Trigger groups v2 (preferred over the legacy trigger fields). Confirmed schema (source 39).
```json
{
  "session_recording_trigger_groups": {
    "version": 2,
    "groups": [
      { "id": "all-sessions", "name": "Record all sessions", "sampleRate": 1.0, "minDurationMs": 2000, "conditions": { "matchType": "any" } }
    ]
  }
}
```
- Create an action. Confirmed (source 35).
```http
POST /api/projects/{project_id}/actions/
scope: action:write

{
  "name": "Phone link tapped",
  "description": "Any click on a tel: link, autocaptured",
  "steps": [
    { "event": "$autocapture", "tag_name": "a", "href": "tel:", "href_matching": "contains" },
    { "event": "phone link tapped" }
  ]
}
```
- Create a dashboard then insights. Confirmed (sources 36, 37). `dashboards: [id]` on the insight is the write path even though the field is flagged deprecated; `dashboard_tiles` is read-only.
```http
POST /api/projects/{project_id}/dashboards/
scope: dashboard:write
{ "name": "See visitors - conversions", "description": "Created by /analytics", "pinned": true, "tags": ["see-visitors"] }

POST /api/projects/{project_id}/insights/
scope: insight:write
{
  "name": "Conversions by event",
  "dashboards": [<dashboard_id>],
  "query": {
    "kind": "InsightVizNode",
    "source": {
      "kind": "TrendsQuery",
      "dateRange": { "date_from": "-30d" },
      "interval": "day",
      "series": [
        { "kind": "EventsNode", "event": "form submitted", "math": "total" },
        { "kind": "EventsNode", "event": "phone link tapped", "math": "total" },
        { "kind": "EventsNode", "event": "text link tapped", "math": "total" },
        { "kind": "EventsNode", "event": "booking made", "math": "total" }
      ]
    }
  }
}
```
- Funnel insight body (same endpoint): `"source": { "kind": "FunnelsQuery", "series": [ {"kind":"EventsNode","event":"$pageview"}, {"kind":"EventsNode","event":"form field focused"}, {"kind":"EventsNode","event":"form submitted"} ], "dateRange": {"date_from": "-30d"} }`. Field names confirmed from the schema (`series` required, `funnelsFilter` optional); the exact `funnelsFilter` keys were not opened.
- Verify each event fired exactly once. Confirmed endpoint and shape (source 38).
```http
POST /api/projects/{project_id}/query/
scope: query:read
{ "query": { "kind": "HogQLQuery", "query": "select event, properties.$session_id as s, count() as c from events where timestamp > now() - interval 30 minute and event in ('form submitted','phone link tapped','text link tapped','booking made') group by event, s having c > 1" } }
```
- Server-side capture. Confirmed (source 29).
```http
POST https://us.i.posthog.com/i/v0/e/
{ "api_key": "phc_...", "event": "booking made", "distinct_id": "<browser distinct id or lead email>", "properties": { "source": "ghl_webhook", "calendar_id": "...", "$set_once": { "first_booking_at": "2026-09-23T10:00:00Z" } }, "timestamp": "2026-09-23T10:00:00Z" }
```
- Heatmap read. Confirmed (source 19). `GET /api/projects/{project_id}/heatmaps/?type=click&url_exact=https://www.example.com/&date_from=-7d&aggregation=unique_visitors` with scope `heatmap:read`.
- Rate limits: 480/min and 4800/h for these CRUD calls, 240/min and 2400/h for `/query/`. Confirmed (sources 30, 38).
- Not confirmed: the exact response for a plan-gated `session_recording_retention_period`; whether `null` clears `blockSelector`; the standalone `GET /api/projects/{id}/` and `/api/projects/@current/` operation pages; the `funnelsFilter` sub-keys; whether PostHog dedupes two captures that share a client-supplied `uuid` (the type page for `CaptureOptions` 404'd).

## Exact client code (verified)
- `instrumentation-client.ts` (Next.js 15.3+, App Router). Init lines from source 1, option semantics from sources 2 and 5.
```ts
import posthog from 'posthog-js'

posthog.init(process.env.NEXT_PUBLIC_POSTHOG_PROJECT_TOKEN!, {
  api_host: '/ph-relay',                 // proxy path, not /analytics or /posthog
  ui_host: 'https://us.posthog.com',     // eu.posthog.com for EU projects
  defaults: '2026-05-30',                // capture_pageview 'history_change', head script injection, strict min duration
  capture_pageleave: true,               // scroll depth and bounce rate ride on $pageleave
  person_profiles: 'identified_only',
  capture_dead_clicks: true,
  session_recording: {
    maskAllInputs: true,
    maskTextSelector: 'a[href^="tel:"], .phone',
  },
})
```
- `.env.local`
```shell
NEXT_PUBLIC_POSTHOG_PROJECT_TOKEN=phc_...
NEXT_PUBLIC_POSTHOG_HOST=https://us.i.posthog.com
```
- `next.config.js` rewrites, verbatim structure from source 5 with the path renamed.
```js
const nextConfig = {
  async rewrites() {
    return [
      { source: '/ph-relay/static/:path*', destination: 'https://us-assets.i.posthog.com/static/:path*' },
      { source: '/ph-relay/array/:path*', destination: 'https://us-assets.i.posthog.com/array/:path*' },
      { source: '/ph-relay/:path*', destination: 'https://us.i.posthog.com/:path*' },
    ]
  },
  skipTrailingSlashRedirect: true,
}
module.exports = nextConfig
```
- If `middleware.ts` exists: `export const config = { matcher: ['/((?!api|ph-relay|_next|_vercel|.*\\..*).*)'] }` (source 5).
- WordPress / any HTML site: paste the snippet from https://posthog.com/docs/getting-started/install inside `<head>` and end it with `posthog.init('phc_...', { api_host: 'https://us.i.posthog.com', defaults: '2026-05-30' })` (source 6). No proxy is available without server config; expect some ad-blocker loss.
- Form success capture (client component). Capture syntax from source 24, naming from source 23, dedupe guard is the inferred pattern.
```tsx
'use client'
import posthog from 'posthog-js'

async function onSubmit(values: FormValues) {
  const res = await fetch('/api/lead', { method: 'POST', body: JSON.stringify(values) })
  if (!res.ok) return showError()
  const key = `ph_form_submitted_${formId}`
  if (!sessionStorage.getItem(key)) {
    sessionStorage.setItem(key, '1')
    posthog.capture('form submitted', {
      form_id: formId,
      page_path: window.location.pathname,
      $set_once: { first_form_submitted_at: new Date().toISOString() },
    })
  }
  showThanks()
}
```
- Field-level events for a drop-off funnel (no values). Inferred pattern built on sources 22 and 23.
```tsx
function trackField(e: React.FocusEvent<HTMLInputElement>) {
  const field = e.currentTarget.name
  const key = `ph_field_focused_${formId}_${field}`
  if (sessionStorage.getItem(key)) return
  sessionStorage.setItem(key, '1')
  posthog.capture('form field focused', { form_id: formId, field })
}
function trackFieldDone(e: React.FocusEvent<HTMLInputElement>) {
  if (!e.currentTarget.value) return
  posthog.capture('form field completed', { form_id: formId, field: e.currentTarget.name })
}
// <input name="phone" type="tel" onFocus={trackField} onBlur={trackFieldDone} />
```
- tel: and sms: click listener (mount once in a client component or a small `useEffect` in the root layout). Options from source 24.
```ts
document.addEventListener('click', (ev) => {
  const a = (ev.target as HTMLElement).closest('a[href^="tel:"], a[href^="sms:"]') as HTMLAnchorElement | null
  if (!a) return
  const href = a.getAttribute('href') || ''
  const event = href.startsWith('tel:') ? 'phone link tapped' : 'text link tapped'
  posthog.capture(event, { href, link_text: a.textContent?.trim(), page_path: location.pathname },
    { send_instantly: true, transport: 'sendBeacon' })
})
```
- Calendly booking listener, verbatim shape from source 46.
```ts
function isCalendlyEvent(e: MessageEvent) {
  return e.origin === 'https://calendly.com' && e.data?.event?.startsWith('calendly.')
}
window.addEventListener('message', (e) => {
  if (!isCalendlyEvent(e)) return
  if (e.data.event === 'calendly.event_scheduled') {
    posthog.capture('booking made', { provider: 'calendly', page_path: location.pathname })
  }
})
```
- GoHighLevel calendar listener, shape from practitioner sources 47, verify in devtools first.
```ts
window.addEventListener('message', (e) => {
  if (e.origin !== 'https://api.leadconnectorhq.com') return
  if (Array.isArray(e.data) && e.data[0] === 'msgsndr-booking-complete') {
    posthog.capture('booking made', { provider: 'ghl', calendar_id: e.data[1]?.calendarId, page_path: location.pathname })
  }
})
```
- Consent gate (CMP present). Verbatim pattern from source 42.
```ts
posthog.init(token, { api_host: '/ph-relay', ui_host: 'https://us.posthog.com', defaults: '2026-05-30', opt_out_capturing_by_default: true })
function onConsentChange(hasConsented: boolean) {
  hasConsented ? posthog.opt_in_capturing() : posthog.opt_out_capturing()
}
```
- Server-side (webhook) capture in Python, verbatim signatures from source 28.
```python
from posthog import Posthog
posthog = Posthog(os.environ["POSTHOG_PROJECT_TOKEN"], host=os.environ.get("POSTHOG_HOST", "https://us.i.posthog.com"))
posthog.capture("booking made", distinct_id=lead_distinct_id, properties={"provider": "ghl", "calendar_id": calendar_id})
posthog.shutdown()  # flush before the function exits
```

## Rules for /analytics
- Install through `instrumentation-client.ts`, no provider, `defaults: '2026-05-30'`, never add a manual `$pageview` effect on top.
- Always ship the three-rule rewrite proxy with a non-obvious path and `skipTrailingSlashRedirect: true`; add the path to any middleware matcher.
- Set `ui_host` whenever `api_host` is a relative proxy path or the toolbar and heatmap links break.
- Pick US or EU once from the project's `api_token` host and use it for ingestion, assets and the private API consistently.
- Keep `capture_pageleave` and autocapture on or scrollmaps and bounce rate go blank.
- Turn replay on server-side via `PATCH /api/organizations/{org}/projects/{id}/` with `session_recording_opt_in: true`, `session_recording_sample_rate: "1.00"`, `session_recording_minimum_duration_milliseconds: 2000`, and a v2 trigger group.
- Turn heatmaps on with `heatmaps_opt_in: true` and dead clicks with `capture_dead_clicks: true`; do not also set `capture_heatmaps` in code, let remote config drive it.
- Leave `maskAllInputs: true`; add `maskTextSelector` for rendered phone numbers; never enable network body capture on a lead-gen site.
- Set `recording_domains` to the production origin so staging and localhost do not burn the 5,000 free recordings.
- Free plan replay retention is 30 days; do not PATCH `session_recording_retention_period` above `30d` without checking the plan first.
- Name events `object verb`: `form submitted`, `phone link tapped`, `text link tapped`, `booking made`, `form field focused`, `form field completed`.
- Fire `form submitted` only in the success branch after the server responds; guard with a per-form sessionStorage key.
- Never capture field values; capture field names only.
- Use `{ send_instantly: true, transport: 'sendBeacon' }` for tel:, sms: and any click that navigates away.
- Capture bookings from the embed's postMessage (`calendly.event_scheduled`, `msgsndr-booking-complete`) and from the vendor webhook server-side; pick one as the billing-truth event and tag the other `source` so the funnel does not double count.
- Tell the user third-party booking iframes will show as blank in replays; that is browser policy, not a bug.
- Create one dashboard and attach insights with `dashboards: [id]`; add a HogQL duplicate check that groups by event and `$session_id` with `having count() > 1` and expect zero rows.
- Personal API key needs `user:read`, `project:read`, `project:write`, `action:write`, `insight:write`, `dashboard:write`, `query:read`; keep it in env, never in the repo, PostHog auto-rolls leaked `phx_` keys.
- Budget API calls under 480/min; the whole setup is fewer than 20 requests.
- With a cookie banner: init opted out and call `opt_in_capturing()` from the CMP; without one in the EU: `cookieless_mode: 'always'` plus the project's "Cookieless server hash mode" toggle, and accept no identify and no cross-day identity.
- Do not run the PostHog wizard inside the command; it needs OAuth, uses an LLM and creates its own events and dashboards that would collide with ours. Mention it as an alternative.
- Do not promise a heatmap on day one; say roughly 2,000 pageviews per URL before reading it, and that heatmap data is kept 90 days.
- Verify with the query endpoint, not by eyeballing the UI: count each conversion event per session over the last 30 minutes after the smoke test.
