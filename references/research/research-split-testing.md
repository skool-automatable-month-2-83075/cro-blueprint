# Research dossier - split testing with PostHog for lead-gen pages
Built 23 September 2026 · 69 sources opened · for /split-test
Next: fold into references/split-testing.md and code/split_test.py, code/sample_size.py

Extends the "300 clicks per variant" section of research-cro-gaps-2026-09-12.md. That section already established: 300 clicks per variant detects only a +80 percent lift at 7.6 percent baseline, count leads not clicks, leads per variant ≈ 16 / lift², do not test below ~70 leads per variant, pool one structural variant across a portfolio. This dossier does not repeat that argument. It verifies the math, documents the exact PostHog API and Next.js plumbing, and adds the operating rules (goal definition, peeking, SRM, novelty, Google Ads interaction, win rates).

## Sources
1. PostHog OpenAPI schema - https://us.posthog.com/api/schema/ - live 2026-09-23 - the authoritative request and response schemas for feature_flags and experiments (8.8 MB YAML, parsed locally).
2. PostHog Feature flags API reference - https://posthog.com/docs/api/feature-flags - live - POST body fields, scopes, response example.
3. PostHog Experiments API reference - https://posthog.com/docs/api/experiments - live - POST body, all action endpoints, response example.
4. PostHog tutorial "How to set up Next.js A/B tests" - https://posthog.com/tutorials/nextjs-ab-tests - Feb 16 2024, code updated - cookie read, getAllFlags, bootstrap, server-rendered variant, flicker explanation.
5. PostHog Next.js library docs - https://posthog.com/docs/libraries/next-js - live - bootstrapping only works if flags are evaluated before render.
6. PostHog "Bootstrapping feature flags" - https://posthog.com/docs/feature-flags/bootstrapping - live - bootstrap object shape, ID consistency warning.
7. PostHog "Experiment statistics overview" - https://posthog.com/docs/experiments/experiment-significance - live - significance rule, 50 exposures, 5 conversions, 90/95/99.
8. PostHog "Bayesian statistics" - https://posthog.com/docs/experiments/statistics-bayesian - live - chance to win, credible interval formula, priors.
9. PostHog "Frequentist statistical method" - https://posthog.com/docs/experiments/frequentist-method - live - two-sided t-test, alpha, sequential testing.
10. PostHog "Experiment exposures" - https://posthog.com/docs/experiments/exposures - live - $feature_flag_called properties, metric events need no flag property.
11. PostHog "Sample size and running time" - https://posthog.com/docs/experiments/sample-size-running-time - live - N = 16 × variance / d², 30 percent MDE default, 100 exposures.
12. PostHog "Creating feature flags" - https://posthog.com/docs/feature-flags/creating-feature-flags - live - multivariate, persist across auth trade-offs.
13. PostHog "Experiment troubleshooting" - https://posthog.com/docs/experiments/troubleshooting - live - SRM causes, bots as participants, 55/45 normal under 1,000.
14. PostHog "Creating an experiment" - https://posthog.com/docs/experiments/creating-an-experiment - live - primary vs secondary metrics.
15. PostHog "Holdouts" - https://posthog.com/docs/experiments/holdouts - live - 1 to 10 percent, holdout-{id}, locked after launch.
16. PostHog "Adding experiment code" - https://posthog.com/docs/experiments/adding-experiment-code - live - only flag value access counts as exposure.
17. PostHog "Experiment metrics" - https://posthog.com/docs/experiments/metrics - live - funnel step 0 is exposure, conversion windows.
18. PostHog React library - https://posthog.com/docs/libraries/react - live - useFeatureFlagVariantKey, undefined while loading.
19. PostHog Node library - https://posthog.com/docs/libraries/node - live - evaluateFlags, $feature_flag_called dedup, serverless flush.
20. PostHog "Experiments best practices" - https://posthog.com/docs/experiments/best-practices - live - peeking, running time calculator, 5 percent soak, never restart.
21. PostHog product analytics troubleshooting (bots) - https://posthog.com/docs/product-analytics/troubleshooting - live - bot list, HeadlessChrome rule, flag requests still go out.
22. PostHog feature flags common questions - https://posthog.com/docs/feature-flags/common-questions - live - 100 to 500 ms flag fetch, hashing.
23. PostHog "Server-side local evaluation" - https://posthog.com/docs/feature-flags/local-evaluation - live - personalApiKey, 30 s polling, continuity incompatible.
24. PostHog "Keeping flag evaluations stable" - https://posthog.com/docs/feature-flags/stable-identity-for-flags - live - hash("flag_key","distinct_id"), device bucketing, recommendation order.
25. PostHog "Running experiments without feature flags" - https://posthog.com/docs/experiments/running-experiments-without-feature-flags - live - $feature/<key> on custom exposure and metric events.
26. PostHog "Analyzing results" - https://posthog.com/docs/experiments/analyzing-results - live - interval not crossing zero, wait for consistency over days.
27. PostHog Flags evaluation API - https://posthog.com/docs/api/flags - live - /flags?v=2 response, server-side events need $feature/<key>.
28. PostHog "Traffic allocation" - https://posthog.com/docs/experiments/traffic-allocation - live - even split, 20 percent exposure variance under 1,000.
29. PostHog "Testing and launching" - https://posthog.com/docs/experiments/testing-and-launching - live - optional override for QA.
30. PostHog "Identify" - https://posthog.com/docs/product-analytics/identify - live - merge rules, blocked ids.
31. PostHog Capture API - https://posthog.com/docs/api/capture - live - required fields, batch limit 20 MB.
32. posthog-js issue #2623 - https://github.com/PostHog/posthog-js/issues/2623 - closed - flag value changed after identify despite persistence.
33. Vercel ab-testing-simple middleware.ts and lib/ab-testing.ts - https://github.com/vercel/examples/tree/main/edge-middleware/ab-testing-simple - live - cookie plus rewrite pattern, crypto random bucket.
34. Next.js proxy.js reference - https://nextjs.org/docs/app/api-reference/file-conventions/proxy - v16.3.6, 2026-09-07 - middleware renamed proxy, matcher, cookies, prefetch header matchers.
35. Next.js NextResponse - https://nextjs.org/docs/app/api-reference/functions/next-response - v16.3.6 - rewrite, cookies.set.
36. Next.js Link - https://nextjs.org/docs/app/api-reference/components/link - v16.3.6, 2026-08-25 - viewport prefetch in production only.
37. Next.js Caching (previous model) - https://nextjs.org/docs/app/guides/caching-without-cache-components - v16.3.6 - dynamic = 'force-dynamic', force-static empties cookies().
38. Kohavi, Longbotham, Sommerfield, Henne, "Controlled experiments on the web: survey and practical guide", Data Min Knowl Disc 2009 - https://ai.stanford.edu/~ronnyk/2009controlledExperimentsOnTheWebSurvey.pdf - PDF parsed - n = 16σ²/Δ², A/A, robots, primacy/newness, full weeks, 50/50.
39. Kohavi, Deng, Frasca, Walker, Xu, Pohlmann, "Online Controlled Experiments at Large Scale", KDD 2013 - https://exp-platform.com/Documents/2013%20controlledExperimentsAtScale.pdf - PDF parsed - one third of Microsoft ideas succeed, Google 10 percent, Netflix 90 percent wrong, Twyman's law.
40. Dmitriev, Gupta, Kim, Vaz, "A Dirty Dozen: Twelve Common Metric Interpretation Pitfalls", KDD 2017 - https://exp-platform.com/Documents/2017-08%20KDDMetricInterpretationPitfalls.pdf - PDF parsed - SRM chi-square, novelty example.
41. Evan Miller, "How Not To Run An A/B Test" - https://www.evanmiller.org/how-not-to-run-an-ab-test.html - 2010 - peeking inflation table, 26.1 percent, n = 16σ²/δ².
42. Evan Miller sample size calculator - https://www.evanmiller.org/ab-testing/sample-size.html - live - 10.2 to 13.2 percent needs 2,545 per variation.
43. Lukas Vermeer SRM checker FAQ - https://www.lukasvermeer.nl/srm/docs/faq/ - live - chi-square, p < 0.01 flag, Microsoft 6 percent, LinkedIn 10 percent.
44. Ron Kohavi LinkedIn post - https://fi.linkedin.com/posts/ronnyk_abtesting-experimentguide-activity-7064709778190594048-5jNv - 2023 - success rate 8 to 33 percent.
45. Wingify/VWO "Peek Inside Booking.com's Experimentation & CRO Culture" - https://wingify.com/blog/cro-best-practices-booking/ - 1,000 concurrent experiments, 9 out of 10 fail.
46. Wingify "Inconclusive A/B Test Results - What's Next?" - https://wingify.com/blog/inconclusive-ab-test-results/ - definition, causes, actions.
47. Wingify "A/B Testing for Big Wins" - https://wingify.com/blog/ab-test-big-changes/ - 500 visits/day at 2 percent: 5 percent lift 1,254 days, 50 percent lift 13 days.
48. Georgi Georgiev, "One-tailed vs Two-tailed Tests of Significance in A/B Testing" - https://blog.analytics-toolkit.com/2017/one-tailed-two-tailed-tests-significance-ab-testing/ - 2017 - two-sided needs 20 to 60 percent more sample.
49. Recast, "The Winner's Curse: Why Underpowered Experiments Are Likely to Be Extra Wrong" - https://getrecast.com/the-winners-curse/ - mechanism, 11x vs 2.3x example, use the bound nearest zero.
50. GuessTheTest, "The winner's curse" - https://guessthetest.com/the-winners-curse-the-big-problem-with-enormous-winners-in-a-b-testing/ - +364 percent from 1 vs 3 conversions.
51. LogRocket, "How to catch the novelty effect in A/B testing" - https://blog.logrocket.com/product-management/novelty-effect-ab-testing/ - new vs returning split, week-one spike shape, two business cycles.
52. Kameleoon, "Are you stopping your A/B tests too early?" - https://www.kameleoon.com/blog/stopping-ab-tests-too-early - 2 business cycles, 2 to 4 weeks, Safari 7-day cookie.
53. Optimizely glossary, A/A testing - https://www.optimizely.com/optimization-glossary/aa-testing/ - 10 percent false conclusive at 90, 5 percent at 95, quarterly.
54. Optimizely support, "Run and interpret an A/A test" - https://support.optimizely.com/hc/en-us/articles/4410283989005-Run-and-interpret-an-A-A-test - validates configuration.
55. Statsig, "Confidence Interval in A/B Testing" - https://www.statsig.com/perspectives/confidence-interval-ab-testing - zero inside interval means hold.
56. Statsig, "How to Choose Confidence Interval Levels" - https://www.statsig.com/perspectives/choose-confidence-interval-ab-testing - 90 vs 95 trade-off.
57. GrowthBook, Sequential Testing - https://docs.growthbook.io/statistics/sequential - Waudby-Smith 2023 confidence sequences, wider intervals.
58. Google Search Central, "Website testing" - https://developers.google.com/search/docs/crawling-indexing/website-testing - no cloaking, canonical, 302, run only as long as necessary.
59. Google Ads Help, "About Quality Score for Search campaigns" (6167118) - https://support.google.com/google-ads/answer/6167118 - three components, historical impressions for exact searches.
60. Google Ads Help, "Understanding landing page experience" (2404197) and "Improve your landing page experience" (6167130) - https://support.google.com/google-ads/answer/6167130 - conversion rate does not impact landing page status.
61. Google Ads Help, "About conversion counting options" (3438531) - https://support.google.com/google-ads/answer/3438531 - "One" for leads.
62. Google Ads Help, "Set up your web conversions" (16560108) - https://support.google.com/google-ads/answer/16560108 - page load vs click, URL contains "thank-you".
63. Google Ads Help, "Track clicks on your website as conversions" (6331304) - https://support.google.com/google-ads/answer/6331304 - onclick plus event snippet.
64. Google Tag Platform, "Measure conversions" - https://developers.google.com/tag-platform/devguides/conversions - gtag event snippet, page load default.
65. Google Ads Help, "Test your landing page" (6328603) - https://support.google.com/google-ads/answer/6328603 - landing page and final URL must share domain.
66. CallRail API v3 docs - https://apidocs.callrail.com/ - live, parsed locally - Webhooks integration config (pre_call_webhook arrays), signing_key, call fields first_call, landing_page_url, source.
67. CallRail Webhooks integration page - https://www.callrail.com/integrations/webhooks - event list: Call started, Call routing complete, Call completed, Call modified, SMS, Form submission received.
68. HBR, "Building a Culture of Experimentation" (Thomke) - https://hbr.org/2020/03/building-a-culture-of-experimentation - Booking.com some 25,000 tests a year (snippet only, paywalled body).
69. HBR, "The Surprising Power of Online Experiments" (Kohavi, Thomke) - https://hbr.org/2017/09/the-surprising-power-of-online-experiments - Bing 12 percent revenue example only (snippet only, body paywalled).

Failed to open (403/404, not cited): Etsy "Mitigating the winner's curse", Airbnb "Experiments at Airbnb", CXL sample pollution and low-traffic posts, PostHog docs pages /experiments/statistics, /methodology, /sample-ratio-mismatch, /flag-persistence (all 404), CallRail support Webhooks article (403), Eppo blog posts.

## Findings

### 1. PostHog feature flags API
- (a) Endpoint is `POST /api/projects/{project_id}/feature_flags/` with a personal API key carrying scope `feature_flag:write` (source 2). The docs example sends only `key`; the OpenAPI create schema lists no required fields but `key` is the only thing the example posts (sources 1, 2).
- (a) Create body fields: `key`, `name` ("Feature flag description (stored in the name field for backwards compatibility)"), `filters`, `active`, `archived`, `tags`, `evaluation_contexts`, `is_remote_configuration`, `ensure_experience_continuity`, `evaluation_runtime` (`server` | `client` | `all`, defaults `all`), `bucketing_identifier` (`distinct_id` default | `device_id`) (source 1).
- (a) `filters` shape: `groups` is an array of release condition groups each with `properties` (array), `rollout_percentage` (number), `variant` (string or null, "Variant key override for multivariate flags"), `aggregation_group_type_index`. `multivariate` is `{ "variants": [ { "key", "name", "rollout_percentage" } ] }` where `key` and `rollout_percentage` are required per variant. `payloads` is an object keyed by variant key with string values. `early_exit` boolean defaults false (source 1).
- (a) Variant percentages must sum to 100: the experiment-side schema says "Across variants these must sum to 100" and each is an integer 0 to 100 (source 1). The flag-creation doc only says users are "randomly assigned to each variant based on these percentages" (source 12).
- (a) `is_eligible_for_experiment` (read only) is true when the flag is "multivariate with 2 to 20 variants" (source 1).
- (a) `ensure_experience_continuity`: "Whether to persist a user's flag value across the anonymous-to-identified transition (the 'persist across authentication steps' option). Incompatible with device_id bucketing" (source 1). It costs "a database read and write on every evaluation", has "no support for local evaluation", and "Values can still change after identify()" (source 24, confirmed by issue 32). Bootstrapping "relies on local evaluation, which cannot correctly calculate persistent flag values" (source 12). Recommendation order from PostHog: stable ID from first touch, then server-side bootstrap with a known ID, then device bucketing, then experience continuity last (source 24).
- (a) Stickiness comes from hashing, not from continuity: "hash("flag_key", "distinct_id")" and "We hash the user's distinct_id to a number between 0 and 1 (0-100%), and compare it against the roll out percentage" (sources 22, 24). So the same distinct_id always gets the same variant. For an anonymous lead-gen visitor who never logs in, continuity buys nothing.
- (a) Key naming: the experiment schema states the flag key allows "Letters, numbers, hyphens, and underscores only" (source 1). The flag docs recommend "a descriptive key that fits your code" with examples `new-landing-page`, `bigger_callout_button` (source 12).
- (a) Concurrency: writes carry a `version`; action endpoints refuse with 409 "The flag changed after the version you sent. Nothing was written" (sources 1, 2). `POST /feature_flags/{id}/roll_out_to_everyone/` requires `version` and, for a multivariate flag, `variant_key`; it "Adds a release condition with no property filters at 100%" and "On a multivariate flag the variant distribution is rewritten as well" (source 1).
- (a) Variant assignment is decided by the flag alone; a release condition "decides who the flag serves, not which variant they get" (source 2).

### 2. PostHog experiments API
- (a) Endpoint `POST /api/projects/{project_id}/experiments/`, scope `experiment:write`, "Create a new experiment in draft status with optional metrics" (source 3). Docs example body is `{ "name": "string", "feature_flag_key": "string" }` (source 3).
- (a) Write fields: `name`, `description`, `start_date`, `end_date`, `feature_flag_key`, `feature_flag` (an `ExperimentFeatureFlagInput`), `holdout_id`, `parameters`, `running_time_calculation`, `excluded_variants`, `secondary_metrics` (legacy), `saved_metrics_ids`, `filters` (legacy), `type` (`web` | `product`), `exposure_criteria`, `metrics`, `metrics_secondary`, `stats_config`, `scheduling_config`, `allow_unknown_events`, `conclusion`, `conclusion_comment`, `only_count_matured_users`, `update_feature_flag_params`, `version`, `original_experiment`, `tags` (sources 1, 3).
- (a) Flag config through the experiment: `feature_flag.filters.multivariate.variants` (2 to 20; "the baseline defaults to the variant keyed 'control' when present, else the first variant"), `feature_flag.filters.groups` must be "a single group with rollout_percentage only; release conditions are not supported here, edit the feature flag directly", `feature_flag.ensure_experience_continuity` (source 1). If the flag already exists with that key PostHog links it; "Draft experiments always sync" flag config, later updates need `update_feature_flag_params: true` (source 1).
- (a) `parameters` is small now: `minimum_detectable_effect` ("Suggest 20-30% for most experiments") and `variant_notes` (source 1). `feature_flag_variants` inside parameters is not in the current schema; the flag config lives under `feature_flag.filters` (source 1). Inferred: older tutorials that put `feature_flag_variants` in `parameters` are legacy.
- (a) Metrics: each item is `{ "kind": "ExperimentMetric", "metric_type": "funnel" | "mean" | "ratio" | "retention", ... }`. Funnel uses `series` (array of `EventsNode` or `ActionsNode`), `funnel_order_type` `ordered` default ("Do not use 'strict': experiment funnels give wrong counts with it"), `conversion_window` plus `conversion_window_unit` (`second` to `month`; "Omit both to count until the experiment ends"), `goal` `increase` | `decrease`, `name`, `uuid` auto-generated (source 1). Mean uses `source` with `math` `total` default, or `sum` with `math_property` (source 1). "Funnel metrics automatically prepend the experiment's exposure event as step_0" so a one-step series is a valid exposure to lead funnel (sources 1, 17).
- (a) `metrics_secondary` is "Same format as primary metrics" (source 1). No numeric limit is documented (source 17). `is_legacy` is true if any metric uses `ExperimentTrendsQuery` or `ExperimentFunnelsQuery`; those are the old engine (source 1).
- (a) Custom events: metric validation rejects "events not yet ingested by this project" unless `allow_unknown_events: true`, which "REQUIRES explicit user confirmation" (source 1). So fire the lead event at least once before creating the experiment, or set the flag deliberately.
- (a) Exposure: "PostHog considers a user exposed when it receives a $feature_flag_called event containing: The property $feature_flag matching your experiment's flag key" and "$feature_flag_response with a variant value" (source 10). `resolved_exposure_event` is "$feature_flag_called, or $experiment_exposure once the team" opts in (source 1). "You do not need to add $feature/<flag-key> or any other flag property to your metric events" (source 10). "Only flag value access counts as an exposure. Other methods like getAllFlags(), getFeatureFlags(), or payload-only accessors do not record an exposure event" (source 16).
- (a) `exposure_criteria`: `filterTestAccounts`, `multiple_variant_handling` `exclude` (default) | `first_seen`, `exposure_config` for a custom exposure event, `activation_config` for an extra event required after exposure (source 1). With custom exposure you "must manually include $feature/<flag-key> property" (sources 10, 25).
- (a) Lifecycle: `POST /experiments/{id}/launch/` "activates its linked feature flag, sets start_date to the current server time, and transitions the experiment to running", 400 if fewer than 2 variants. `POST /{id}/end/` "Sets end_date to now and marks the experiment as stopped. The feature flag is NOT modified", body `conclusion` (`won` | `lost` | `inconclusive` | `stopped_early` | `invalid`) and `conclusion_comment`. `POST /{id}/ship_variant/` body `variant_key` required, `release_to_everyone` default false, "Updates the feature flag so the selected variant gets 100% of the variant distribution" and ends a running experiment. Also `pause`, `resume`, `freeze_exposure`, `reset`, `duplicate`, `archive` (source 1). Status enum: `draft`, `running`, `paused`, `exposure_frozen`, `stopped` (source 1).
- (a) Reading results: `POST /experiments/{id}/metrics_recalculation/` queues a job (201) then `GET /experiments/{id}/metrics_recalculation/latest/` returns per-metric `results`; `GET /experiments/{id}/timeseries_results/?metric_uuid=` returns daily series (source 1). Ad hoc: `POST /api/projects/{id}/query/` with `{"query": {"kind": "ExperimentQuery", "experiment_id": N, "metric": {...}}}` returns `ExperimentQueryResponse` with `baseline`, `variant_results[]` (`key`, `method` `bayesian` | `frequentist`, `number_of_samples`, `sum`, `sum_squares`, `chance_to_win`, `credible_interval` [lo, hi] or `p_value`, `confidence_interval`, `significant`), `probability`, `significant`, `significance_code`, `credible_intervals` (source 1). For a funnel metric `number_of_samples` is exposures and `sum` is conversions (inferred from the sum/sum_squares base stats and `ExperimentVariantFunnelsBaseStats` success_count/failure_count, source 1).
- (a) Sample size fields: `running_time_calculation` holds `minimum_detectable_effect`, `recommended_running_time` ("Estimated number of days"), `recommended_sample_size` ("Recommended number of exposed users"), `exposure_estimate_config` (`conversionRateInputType` `manual` | `automatic`, `manualBaselineValue`, `manualExposureRate`) (source 1). Stateless calculator: `POST /experiments/calculate_running_time/` with `metric_type` (`funnel`, `mean_count`, `mean_sum_or_avg`, `ratio`, `retention`), `minimum_detectable_effect` ("as a percentage (e.g. 5 means a 5% lift)"), `number_of_variants` default 2, `baseline_value` ("conversion rate as a fraction 0-1"), optional `exposure_rate_per_day`; returns `recommended_sample_size` ("Total recommended sample size across all variants") and `recommended_running_time_days` (source 1).
- (a) PostHog's formula: "N = (16 × variance) / d²" per variant, funnel variance "p × (1 - p)", count "2 × baseline", d = MDE × baseline, "The default is 30%" MDE, automatic mode needs "at least 1 day of runtime and 100 exposures", days = sample size ÷ daily exposure rate (source 11).
- (a) Significance: Bayesian is default. "chance_to_win > confidence_level or chance_to_win < (1 - confidence_level)" at 95 default, 90 or 99 optional; "Each variant needs at least 50 exposures" and funnels "at least 5 conversions per variant" (sources 7, 8). Chance to win uses the normal CDF on the posterior; credible interval is "posterior_mean ± 1.96 × posterior_std"; priors are "non-informative" with mean 0 (source 8). Frequentist option is a "two-sided t-test", alpha 0.05/0.10/0.01, with optional sequential testing using "always-valid p-values and confidence sequences" per Waudby-Smith et al. 2023 (source 9). Results UI marks significance when "the interval doesn't cross zero" and advises waiting until "results stay consistent for several days" (source 26).
- (a) Holdouts: "Holdouts exclude a percentage of users from experiments", recommended "between 1% and 10%", value served is `holdout-{holdout_id}`, "locked once any experiment using it is launched", "Holdout users are not included in experiment results" (source 15). Experiment field `holdout_id` (source 1).
- (a) Traffic: "By default, users are split evenly across all variants"; "less than 1,000 users per variant, the difference in variant exposure can be as much as 20%" (source 28). SRM causes listed by PostHog: bots that hit server-side evaluation "are full experiment participants" and "hash deterministically into one variant", flag condition changes after launch ("Even API-level changes count"), identity fragmentation, server SDK dedup cache overflow at 50,000 entries, and "With fewer than ~1,000 exposures, a 55/45 split on a 50/50 experiment is statistically normal" (source 13).

### 3. Serving variants in Next.js App Router without flicker
- (a) The client hook: `useFeatureFlagVariantKey('key')` "Returns the variant key of a feature flag and sends a $feature_flag_called event"; hooks return `undefined` "while flags are loading or absent" (source 18). "fetching flags from our servers takes about 100-500ms. During this time, the flag is disabled" (source 22). The PostHog tutorial shows the useEffect version and says it "causes the 'flicker,' but is solvable if we server-render the component" (source 4).
- (a) Bootstrap object: `bootstrap: { distinctID, isIdentifiedID, featureFlags: {...}, featureFlagPayloads: {...} }` passed to `posthog.init` (source 6). "Bootstrapping Feature Flags makes precomputed flag values available as soon as a client-side PostHog SDK initializes" and "If the server evaluates flags with one ID and the client initializes with another, the client can receive a different value" (source 6). After fetch "it will use those flag values instead of bootstrapped ones" (source 18).
- (a) Cookie: the tutorial reads `ph_${phProjectAPIKey}_posthog` via `cookies()`, `JSON.parse(value).distinct_id`, falls back to `uuidv7()` wrapped in React `cache()`, then `new PostHog(token, { host }).getAllFlags(distinct_id)` and returns `{ distinctID, featureFlags }` (source 4). The server page reads `bootstrapData.featureFlags['main-cta']` and renders the variant markup directly; "This shows your updated button text immediately on load. This method still uses the client-side for tracking, and this works because we bootstrap the distinct ID from the server-side to the client" (source 4).
- (a) Caveat from the Next.js docs page: with `instrumentation-client` "the values you pass to posthog.init remain fixed for the entire session. This means bootstrapping only works if you evaluate flags before your app renders (for example, on the server)" (source 5).
- (a) Node SDK: `getAllFlags` and `getFeatureFlag` still appear in the tutorial but the current Node docs present `client.evaluateFlags(distinctId, { flagKeys, personProperties, groups })` returning a snapshot; `flags.getFlag(key)` "automatically sends $feature_flag_called events" with dedup "per (distinct_id, flag, value) in a local cache"; `getFlagPayload()` does not (source 19). Capture with the snapshot: `client.capture({ distinctId, event, flags })` or manual `properties: { '$feature/feature-flag-key': 'variant-key' }` (source 19). Serverless: "set flushAt to 1 and flushInterval to 0" and "always call await posthog.shutdown()", or use `captureImmediate()` (source 19).
- (a) Local evaluation: pass `personalApiKey` and `featureFlagsPollingInterval` (default 30000 ms); the SDK "periodically fetches flag definitions from PostHog's /flags/definitions endpoint" so per-request evaluation is a local hash, no round trip; "not possible for flags that have experience continuity enabled" (source 23). This is what makes the middleware path fast.
- (a) Middleware/proxy: Next.js 16 renamed `middleware.ts` to `proxy.ts` ("The middleware file convention is deprecated and has been renamed to proxy"), it "run[s] code on the server before a request is completed", defaults to the Node.js runtime, exports `config.matcher`, and exposes `request.cookies.get` and `response.cookies.set` (source 34). `NextResponse.rewrite(url)` "rewrites (proxies) the given URL while preserving the original URL" so the browser keeps one URL (source 35). Vercel's reference pattern: read `bucket-home` cookie, if missing or invalid `getBucket()` (crypto random split into equal percentages), `url.pathname = \`${route.page}/${bucket}\``, `NextResponse.rewrite(url)`, `res.cookies.set(route.cookie, bucket)` only when newly assigned (source 33).
- (a) Prefetch: "Prefetching happens when a <Link /> component enters the user's viewport", "Prefetching is only enabled in production", default prefetches the full static route or partial dynamic route (source 36). Proxy matchers can skip prefetch requests via `missing: [{ type: 'header', key: 'next-router-prefetch' }, { type: 'header', key: 'purpose', value: 'prefetch' }]` (source 34). For prefetching through a rewrite "you need to tell Next.js both the URL to display and the URL to prefetch" using `<Link as="/dashboard" href={path}>` (source 36).
- (a) Caching: reading `cookies()` makes the route dynamic; `dynamic = 'force-static'` forces `cookies()` and `headers()` "to return empty values", `dynamic = 'force-dynamic'` renders per request (source 37). The tutorial relies on Next caching the bootstrap call within one render so page and provider agree (source 4). Inferred: a static landing page becomes per-request once it reads the PostHog cookie; do the split in proxy and rewrite to two prebuilt routes if you want static variants.
- (a) Bots: PostHog web SDK "blocks most known bots by default" (googlebot, adsbot-google, ahrefsbot, bingbot, gptbot, linkedinbot) and any browser where "navigator.webdriver is true, or the user agent ... contains HeadlessChrome"; for those "feature flag requests go out ... but event requests never leave the page" (source 21). Server-side evaluation has no such filter: "Bots that trigger server-side flag evaluations are full experiment participants" (source 13). Kohavi 2009: "robots caused many metrics to be significant when they should not have been" and robots "provide up to half the pageviews" on some sites (source 38).
- (a) Event wiring: "For server-side events, include feature flag context: Add $feature/{flag-key} property with the variant value" and "Send a $feature_flag_called event containing $feature_flag (flag key) and $feature_flag_response (variant name)" (source 27). Client events captured by posthog-js after bootstrap carry the flags automatically (inferred from source 27 scoping the requirement to server-side events, and from source 10 saying metric events need no flag property). Custom exposure events must carry `$feature/<key>` on both exposure and metric events (source 25).
- (a) QA before launch: add "an optional override to your release conditions" so team emails or a `utm_source` value get a fixed variant (source 29). PostHog also advises a soak "with a small rollout (e.g., 5% of users) for a few days" then full launch, because restarting "will produce unreliable results since many users have already seen your change" (source 20).

### 4. Statistics for lead-gen tests
- (a) The rule of thumb: "n = 16σ²/Δ²" per variant at 95 percent confidence and 80 percent power, "Replace the 16 by 21 in the formula above to increase the power to 90%" (source 38, citing van Belle 2002). PostHog implements exactly this with funnel variance p(1-p) (source 11). Evan Miller states the same n = 16σ²/δ² (source 41).
- (a) Kohavi's own worked numbers: 5 percent conversion, detect a 5 percent relative change: "less than 122,000 users ... based on 16 ∗ (0.05 · (1 − 0.05))/(0.05 · 0.05)²"; "if the desired sensitivity is reduced to support detecting a 20% change in conversion instead of 5% (a factor of 4), the number of users needed drops by a factor of 16 to 7,600" (source 38). Restricting to users who could see the change halves the sample (source 38).
- (a) Evan Miller's calculator: baseline 10.2 percent, detect 10.2 to 13.2 percent (about +29 percent relative): "2,545 per variation" (source 42). Cross-check: 16 × 0.102 × 0.898 / 0.03² = 1,628; the 2,545 figure reflects his exact two-sample two-sided formula, so the 16 rule is optimistic by roughly a third at large relative lifts. Our own exact computation (below) shows the gap is 5 to 20 percent at 20 to 50 percent lifts.
- (a) One vs two sided: PostHog frequentist is "two-sided" (source 9). Georgiev: "to reliably detect a given effect with 95% two-sided significance, one needs 20-60% higher sample size than to detect the same effect at 95% one-sided significance" and one-sided fits when "one would act a certain way ... if a statistically significant difference in a particular direction is discovered" (source 48). The Bayesian chance-to-win rule (above 95 or below 5) is symmetric, equivalent to a two-sided 90 percent test in spirit (inferred from source 7).
- (a) Bayesian readout: "There's a 96% chance that variant B increases conversion rate", "95% credible interval ... There's a 95% probability the true effect lies in this range", significance when chance to win crosses the threshold, 50 exposures and 5 conversions minimum (sources 7, 8). PostHog does not document a peeking guard for the Bayesian engine; the frequentist engine offers sequential testing (source 9). GrowthBook notes sequential "produces wider confidence intervals than fixed-sample testing" (source 57).
- (a) Peeking: repeated testing at 5 percent nominal can give a real false positive rate of "26.1%" and to keep 5 percent you need reported significance of 2.9 percent for 1 peek, 1.8 percent for 3, 1.0 percent for 10; fix: "Decide on a sample size in advance and wait until the experiment is over" (source 41). PostHog: "Starting an experiment without deciding how long it should last can cause you to fall victim to the peeking problem" (source 20).
- (a) SRM: "If the actual ratio is different than the expected (a chi-square test can be used), it means something is wrong with the sampling process ... Most of the time SRM implies a severe selection bias, enough to render the experiment results invalid" (source 40). Vermeer's checker flags p < 0.01; Microsoft sees SRM in "approximately 6% of experiments", LinkedIn "about 10%" (source 43). PostHog surfaces an SRM warning and lists causes (source 13). For a 300-lead test the exposure counts are thousands, so a chi-square on exposures is meaningful even when leads are few.
- (a) A/A: "the Null hypothesis should be rejected about 5% of the time when a 95% confidence level is used" and "Continuously run A/A tests in parallel with other experiments" (source 38). Optimizely: conclusive A/A "should happen in only 10% of cases, if you have set your significance threshold to 90%", 5 percent at 95, run them "quarterly" (sources 53, 54). For /split-test an A/A is a plumbing check on exposure split and event attribution, not a stats exercise.
- (b) Novelty and primacy: "some users will investigate it, click everywhere, and thus introduce a 'newness' bias ... some experiments need to be run for multiple weeks. One analysis that can be done is to compute the OEC only for new users" (source 38). Microsoft's Edge coach-mark case: +2.07 percent top-site clicks over four weeks, but per-day deltas "declined quickly" and the effect "did not last beyond the first visit" (source 40). LogRocket: "sharp lift in week one, slow decline toward baseline by week four"; compare new vs returning (source 51). Local service pages are mostly new-visitor traffic, so novelty is a smaller risk than on product UIs (inferred).
- (c) Winner's curse: "statistically significant results from under-powered experiments exaggerate the lift"; +364 percent from 1 vs 3 conversions (source 50). Mechanism: "For a result to clear the significance bar in a noisy environment, the observed effect has to be large", so significance "systematically lets through the most extreme estimates"; use "the bound of the confidence interval closest to zero as your conservative estimate" (source 49). Kohavi: "Any figure that looks interesting or different is usually wrong ... Most amazing results turn out to be false when reviewed carefully" (source 39).
- (a) Duration: "we strongly recommend running experiments for at least a week or two, then continuing by multiples of a week so that day-of-week effects can be analyzed" and 50/50 split minimises running time, "1/(4p(1−p))" multiplier otherwise (source 38). Kameleoon: "at least 2 business cycles", "2-4 weeks", Safari deletes first-party cookies after 7 days (source 52). LogRocket: two business cycles minimum for UI changes (source 51).
- (c) Inconclusive: "The probability of a winner is less than 90-95%", "The pValue is bigger than 0.05", "The lift confidence interval includes 0"; causes include change too small, wrong audience, "Inadequate sample size"; actions: read the interval for best and worst case, extend cautiously, avoid re-analysis, revisit the hypothesis, run an MDE calculator (source 46). Statsig: "If the interval spans both positive and negative values, hold off on changes" (source 55). PostHog records this as `conclusion: "inconclusive"` (source 1).
- (c) 90 vs 95: Statsig frames 90 as "Faster results, higher risk, lower cost" for "smaller, less critical updates" (source 56); PostHog's 90 option gives "significant results sooner, but with a higher chance of false positives" (source 7).

### 5. Strategy
- (b) Structural over element tests at low traffic: VWO's worked case, 500 visitors a day at 2 percent conversion: a 5 percent lift needs 1,254 days, a 50 percent lift 13 days; "for sites that receive less traffic, it is best to make big changes" then iterate on the winner (source 47). Kohavi: sensitivity is squared in the formula, so 4x the effect is 16x less sample (source 38). This is the quantitative basis for the existing dossier's "massively different structural variants" call.
- (a) Pooling: the sample formula is per variant regardless of how many sites feed it (source 38). PostHog flags are per project; a portfolio can share one project, one flag key and one experiment, with `$host` or a `site` event property used to segment afterwards (inferred from sources 1, 17). Confirmed constraint: exposures are keyed by distinct_id and the flag hash, so the same visitor on two client sites is two participants (source 24).
- (a) Global holdout: PostHog holdouts 1 to 10 percent, excluded from experiment results, "useful for understanding long term effects of product changes, typically over a few months" (source 15). At 30 to 300 leads a month a 5 percent holdout yields 1.5 to 15 leads a month, useless for measurement (arithmetic). Skip holdouts below roughly 1,000 leads a month.
- (a) Never edit mid-test: "Did someone modify the flag's release conditions or rollout percentage after launch? Check the flag's activity log. Even API-level changes count" is PostHog's second SRM cause (source 13). Restarting "will produce unreliable results" (source 20). Google: "remove all elements of the test as soon as possible" and "Run the experiment only as long as necessary" (source 58). Kohavi's "features must be implemented" and "primacy" notes imply a changed variant is a new experiment (source 38).
- (a) Google Ads interaction: Quality Score components are "Expected clickthrough rate", "Ad relevance", "Landing page experience: How relevant and useful your landing page is to people who click your ad" on a 1 to 10 scale, "based on historical impressions for exact searches of your keyword" (source 59). Google states conversion rate "doesn't impact your landing page status" (source 60). Google's own testing guidance: "Don't show one set of URLs to Googlebot, and a different set to humans", use `rel="canonical"` on alternates, "Use a 302 (temporary) redirect, not a 301" (source 58). Ads requires "The landing page and final URL ... share the same domain" or the ad is disapproved for destination mismatch (source 65). Inferred conclusion: a server-side rewrite at one URL satisfies all of these because there is no alternate URL, no redirect and both variants serve the same content to bots and humans for a given cookie.
- (b) Win rates: "Only one third of the ideas tested at Microsoft improved the metric(s) they were designed to improve"; at Google "about 10 percent of these [controlled experiments, were] leading to business changes"; "Netflix considers 90% of what they try to be wrong"; Etsy "nearly everything fails" (source 39). Kohavi 2023: "In software, our success rate of A/B tests ranges from about 8% to 33%" (source 44). Booking: "some 25,000 tests a year" (source 68), "1,000 concurrent experiments" and "9 out of 10 tests failing" (source 45). Airbnb and HBR full text were not reachable; no Airbnb figure is cited.
- (a) Tests per year at 30 to 300 leads a month: from the table below, a +30 percent structural test needs about 360 leads total, so one site at 100 leads a month supports roughly 3 tests a year and a site at 30 leads a month supports one test per year at best (arithmetic on source 11's formula). At a one-in-three win rate that is one winner a year for a 100-lead site.

### 6. Conversion goal definition for lead-gen
- (a) Google's counting guidance: "One conversion" per click for leads because "usually only one, unique lead per ad click likely adds value for your business" (source 61). Google's default web conversion is page load: "Count conversions when customers visit the conversion page, such as a confirmation page for a purchase or sign-up", with a click-based option that needs "an additional piece of code to the button or link" (source 64); URL rules like "URL contains thank-you" work with no code (source 62).
- (a) PostHog metric events are per person: funnels start at exposure and count a person once per step, and conversion windows count "Metric events ... only ... if they happen after the user's first exposure" (source 17). So a person who taps the phone number three times is one conversion in a funnel metric. A mean (count) metric would count all three, which is wrong for leads (inferred from source 1's `mean` with `math: total`).
- (a) Form success vs thank-you pageview: PostHog does not care which event name you use, but the event must exist before experiment creation or you must set `allow_unknown_events` (source 1). Inferred: fire a single server-confirmed `lead_submitted` event from the form handler (or after the API call resolves) rather than a `$pageview` of `/thank-you`, because a pageview can be reloaded, bookmarked or prefetched, and PostHog will otherwise attribute a thank-you visit without a submission.
- (a) Phone taps: capture `lead_call_tap` on the `tel:` link click. To make "any lead" one funnel step, emit one umbrella event `lead` with property `lead_type` `form` | `call_tap` | `call_answered`, then `series: [{ "kind": "EventsNode", "event": "lead" }]`. Alternative: create a PostHog action that matches either event and use `{ "kind": "ActionsNode", "id": <action id> }` (source 1 documents ActionsNode in `series`). Both count a person once.
- (a) Dedupe one lead per person: PostHog `identify(distinct_id)` "merges the anonymous person into the identified person" and distinct_id should be "something stable like a UID, their email, or their database ID" (source 30). A phone number or email hash as distinct_id at submission links the form to the anonymous browsing person; PostHog blocks ids like `null`, `guest`, `anonymous` and empty strings (source 30). Caution from source 13: identity fragmentation is an SRM cause, so identify only after exposure, never before.
- (a) Tracked calls: CallRail webhooks exist as the `Webhooks` integration with config arrays such as `pre_call_webhook` ("List of URLs to be notified for the Pre-Call event") and a `signing_key` "to be used in validating payloads" (source 66). Marketing event names on CallRail's site: "Call started", "Call routing complete", "Call completed", "Call modified", "Form submission received" (source 67). Call objects expose `customer_phone_number`, `duration`, `answered`, `first_call`, `source`, `landing_page_url`, `device_type` via field selection, and `call_type` filters include `first_call` (source 66). The exact post-call webhook JSON was not opened (support article 403), so treat field names beyond the call API list as unverified.
- (a) Server-side capture of a webhook lead: `POST /i/v0/e/` or `/batch/` with `api_key`, `event`, `distinct_id`, `properties`, `timestamp` (source 31). The event needs `$feature/<flag-key>` set to the variant (source 27), which means the site must have stored the variant against something the webhook can join on: the CallRail session cookie via a Custom integration, or the dynamic number pool session, or the `landing_page_url` query string carrying the variant (inferred; CallRail's "Custom" integration captures "custom cookie data from web visitors and associate it with calls", source 66).

## Exact API facts (verified)
Confirmed from the OpenAPI schema (source 1) and the API reference pages (sources 2, 3) unless marked inferred. Auth for both: `Authorization: Bearer <personal_api_key>`, base `https://us.posthog.com` or `https://eu.posthog.com`.

Create the flag first (or let the experiment create it). Multivariate, two variants, 50/50, 100 percent rollout:

```json
POST /api/projects/{project_id}/feature_flags/
{
  "key": "lp-plumber-structural-v2",
  "name": "Plumber landing page: control vs structural variant B",
  "active": true,
  "filters": {
    "groups": [
      { "properties": [], "rollout_percentage": 100, "variant": null }
    ],
    "multivariate": {
      "variants": [
        { "key": "control", "name": "Current page", "rollout_percentage": 50 },
        { "key": "test", "name": "Structural variant B", "rollout_percentage": 50 }
      ]
    },
    "payloads": {}
  },
  "ensure_experience_continuity": false,
  "bucketing_identifier": "distinct_id",
  "evaluation_runtime": "all",
  "tags": ["cro-blueprint", "split-test"]
}
```

- Response 201 returns the flag object with `id`, `key`, `filters`, `version`, `is_eligible_for_experiment` (true for 2 to 20 variants), `status` (confirmed).
- `ensure_experience_continuity: false` is deliberate: it is incompatible with local evaluation and bootstrapping, and adds a DB read and write per evaluation (sources 12, 23, 24). Variant stickiness comes from the distinct_id hash (confirmed).
- Later edits must send the current `version` or get 409 (confirmed for action endpoints; inferred for PATCH).

Create the experiment in draft, referencing custom lead events:

```json
POST /api/projects/{project_id}/experiments/
{
  "name": "Plumber LP structural test - Sep 2026",
  "description": "H1: a proof-first structure with sticky call bar lifts leads by 30%+",
  "type": "web",
  "feature_flag_key": "lp-plumber-structural-v2",
  "feature_flag": {
    "filters": {
      "groups": [ { "properties": [], "rollout_percentage": 100 } ],
      "multivariate": {
        "variants": [
          { "key": "control", "name": "Current page", "rollout_percentage": 50 },
          { "key": "test", "name": "Structural variant B", "rollout_percentage": 50 }
        ]
      }
    },
    "ensure_experience_continuity": false
  },
  "parameters": {
    "minimum_detectable_effect": 30,
    "variant_notes": { "control": "existing page", "test": "variant B, see brief" }
  },
  "exposure_criteria": {
    "filterTestAccounts": true,
    "multiple_variant_handling": "exclude"
  },
  "metrics": [
    {
      "kind": "ExperimentMetric",
      "metric_type": "funnel",
      "name": "Lead (form or call)",
      "goal": "increase",
      "funnel_order_type": "ordered",
      "series": [ { "kind": "EventsNode", "event": "lead" } ],
      "conversion_window": 7,
      "conversion_window_unit": "day"
    }
  ],
  "metrics_secondary": [
    {
      "kind": "ExperimentMetric",
      "metric_type": "funnel",
      "name": "Form submitted",
      "goal": "increase",
      "series": [ { "kind": "EventsNode", "event": "lead", "properties": [
        { "key": "lead_type", "type": "event", "value": ["form"], "operator": "exact" } ] } ]
    },
    {
      "kind": "ExperimentMetric",
      "metric_type": "funnel",
      "name": "Phone tapped",
      "goal": "increase",
      "series": [ { "kind": "EventsNode", "event": "lead", "properties": [
        { "key": "lead_type", "type": "event", "value": ["call_tap"], "operator": "exact" } ] } ]
    }
  ],
  "allow_unknown_events": false
}
```

- Field names, enums, the step_0 exposure rule, `funnel_order_type` warning against `strict`, conversion window semantics, `multiple_variant_handling` values, `minimum_detectable_effect` in `parameters`: confirmed (source 1).
- The `EventPropertyFilter` shape `{key, type: "event", value: [...], operator: "exact"}` is the standard PostHog property filter; its exact keys inside experiment metrics were not exercised against a live project (inferred).
- `allow_unknown_events: false` means the `lead` event must have been ingested already or the create call is rejected (confirmed).
- Response 201: `id`, `status: "draft"`, `start_date: null`, `feature_flag` object, `metrics` echoed with `uuid` filled, `running_time_calculation` (confirmed).

Launch, read, end:

```text
POST /api/projects/{project_id}/experiments/{id}/launch/          -> status running, flag activated, start_date set (confirmed)
POST /api/projects/{project_id}/experiments/calculate_running_time/
     {"metric_type":"funnel","minimum_detectable_effect":30,"baseline_value":0.075,"exposure_rate_per_day":40}
     -> {"recommended_sample_size": <total across variants>, "recommended_running_time_days": N} (confirmed)
POST /api/projects/{project_id}/experiments/{id}/metrics_recalculation/   -> 201 job (confirmed)
GET  /api/projects/{project_id}/experiments/{id}/metrics_recalculation/latest/ -> results[] per metric (confirmed; per-metric payload shape inferred to match ExperimentQueryResponse)
GET  /api/projects/{project_id}/experiments/{id}/timeseries_results/?metric_uuid=<uuid> (confirmed path and params; body shape undocumented)
POST /api/projects/{project_id}/query/
     {"query":{"kind":"ExperimentQuery","experiment_id":123,"metric":{"kind":"ExperimentMetric","metric_type":"funnel","series":[{"kind":"EventsNode","event":"lead"}]}}}
     -> {"variant_results":[{"key":"test","method":"bayesian","number_of_samples":2140,"sum":171,"chance_to_win":0.97,"credible_interval":[0.04,0.51],"significant":true}],
         "baseline":{"key":"control","number_of_samples":2098,"sum":140},"significant":true,"probability":{"test":0.97}} (field names confirmed; example values illustrative)
POST /api/projects/{project_id}/experiments/{id}/end/          {"conclusion":"inconclusive","conclusion_comment":"..."} (confirmed)
POST /api/projects/{project_id}/experiments/{id}/ship_variant/ {"variant_key":"test","release_to_everyone":true,"conclusion":"won"} (confirmed)
```

- Exposure event confirmed: `$feature_flag_called` with `$feature_flag` = key and `$feature_flag_response` = variant (source 10). Sent by `getFeatureFlag`, `useFeatureFlagVariantKey`, and Node `flags.getFlag()`; not by `getAllFlags` or payload getters (sources 16, 18, 19).
- Legacy shapes not to use: `parameters.feature_flag_variants`, `filters` on the experiment, `secondary_metrics`, `ExperimentTrendsQuery`, `ExperimentFunnelsQuery` (all still accepted but mark `is_legacy`) (confirmed).
- Significance defaults confirmed: Bayesian, 95, "chance_to_win > confidence_level or chance_to_win < (1 - confidence_level)", 50 exposures and 5 conversions per variant minimum (sources 7, 8).

## Exact Next.js code (verified)
Pattern A is PostHog's tutorial (source 4) adapted to the current Node SDK (source 19). Pattern B is the Vercel edge pattern (source 33) plus PostHog local evaluation (source 23). Both keep one URL and render the variant in the HTML, so there is nothing to flicker.

Pattern A: server component reads the PostHog cookie, evaluates once, renders, bootstraps the client.

```ts
// app/lib/posthog-server.ts
import { PostHog } from 'posthog-node'
import { cookies } from 'next/headers'
import { cache } from 'react'
import { uuidv7 } from 'uuidv7'

const TOKEN = process.env.NEXT_PUBLIC_POSTHOG_KEY!
const HOST = process.env.NEXT_PUBLIC_POSTHOG_HOST ?? 'https://us.i.posthog.com'
export const FLAG = 'lp-plumber-structural-v2'

const client = new PostHog(TOKEN, {
  host: HOST,
  personalApiKey: process.env.POSTHOG_PERSONAL_API_KEY, // enables local evaluation, no round trip (source 23)
  featureFlagsPollingInterval: 30000,
  flushAt: 1, flushInterval: 0,                          // serverless-safe (source 19)
})

const newId = cache(() => uuidv7())                       // one id per request render (source 4)

export const getVariant = cache(async () => {
  const jar = await cookies()
  const raw = jar.get(`ph_${TOKEN}_posthog`)?.value        // cookie name from source 4
  let distinctId = ''
  if (raw) { try { distinctId = JSON.parse(raw).distinct_id ?? '' } catch {} }
  if (!distinctId) distinctId = newId()

  const flags = await client.evaluateFlags(distinctId, { flagKeys: [FLAG] })
  const variant = (flags.getFlag(FLAG) as string | undefined) ?? 'control' // getFlag() records $feature_flag_called (source 19)
  await client.shutdown()                                   // flush the exposure event (source 19)
  return {
    variant,
    bootstrap: { distinctID: distinctId, isIdentifiedID: false, featureFlags: { [FLAG]: variant } }, // shape from source 6
  }
})
```

```tsx
// app/layout.tsx
import { PHProvider } from './providers'
import { getVariant } from './lib/posthog-server'
export const dynamic = 'force-dynamic'  // page reads cookies, so it is per request anyway (source 37)

export default async function RootLayout({ children }: { children: React.ReactNode }) {
  const { bootstrap } = await getVariant()
  return (
    <html lang="en">
      <body><PHProvider bootstrap={bootstrap}>{children}</PHProvider></body>
    </html>
  )
}
```

```tsx
// app/providers.tsx
'use client'
import posthog from 'posthog-js'
import { PostHogProvider } from '@posthog/react'

export function PHProvider({ children, bootstrap }: { children: React.ReactNode; bootstrap: any }) {
  if (typeof window !== 'undefined' && !posthog.__loaded) {
    posthog.init(process.env.NEXT_PUBLIC_POSTHOG_KEY!, {
      api_host: process.env.NEXT_PUBLIC_POSTHOG_HOST ?? 'https://us.i.posthog.com',
      bootstrap,                    // same distinctID the server used (source 6)
    })
  }
  return <PostHogProvider client={posthog}>{children}</PostHogProvider>
}
```

```tsx
// app/page.tsx  (server component, no flicker)
import { getVariant } from './lib/posthog-server'
import ControlPage from './variants/control'
import VariantB from './variants/test'

export default async function Page() {
  const { variant } = await getVariant()
  return variant === 'test' ? <VariantB /> : <ControlPage />
}
```

```tsx
// components/LeadEvents.tsx  (client, events carry the flag automatically after bootstrap)
'use client'
import { usePostHog } from '@posthog/react'

export function CallButton({ tel }: { tel: string }) {
  const posthog = usePostHog()
  return (
    <a href={`tel:${tel}`} onClick={() => posthog.capture('lead', { lead_type: 'call_tap' })}>
      Call now
    </a>
  )
}

export async function onFormSuccess(posthog: ReturnType<typeof usePostHog>, leadId: string) {
  posthog.capture('lead', { lead_type: 'form', lead_id: leadId })
}
```

- Why no flicker: the HTML already contains the chosen variant; the client SDK starts with the same flag value bootstrapped, so `useFeatureFlagVariantKey` never returns `undefined` for this key (sources 4, 6, 18).
- Exposure is recorded server-side by `getFlag()`; do not also call `useFeatureFlagVariantKey` on the client for the same key or you double the exposure event (dedup is per process on the server only, source 19). Inferred.
- `$feature/<key>` on client events: not required for the experiment metric (source 10) and posthog-js adds flag properties from the bootstrap state; for any server-side `lead` capture (webhook call) add `'$feature/lp-plumber-structural-v2': variant` explicitly (source 27).

Pattern B: proxy (middleware) split with a cookie, rewriting one URL to two static routes.

```ts
// proxy.ts  (Next 16 name; middleware.ts on 14/15, same body) - pattern from source 33
import { NextRequest, NextResponse } from 'next/server'

const COOKIE = 'ph_variant_lp-plumber-structural-v2'
const BUCKETS = ['control', 'test'] as const

function pick() {
  const n = crypto.getRandomValues(new Uint32Array(1))[0] / 0x100000000
  return n < 0.5 ? 'control' : 'test'
}

export const config = {
  matcher: [{
    source: '/',
    missing: [{ type: 'header', key: 'next-router-prefetch' }, { type: 'header', key: 'purpose', value: 'prefetch' }], // skip prefetches (source 34)
  }],
}

export function proxy(req: NextRequest) {
  let bucket = req.cookies.get(COOKIE)?.value
  const fresh = !bucket || !BUCKETS.includes(bucket as any)
  if (fresh) bucket = pick()
  const url = req.nextUrl.clone()
  url.pathname = `/_v/${bucket}`                          // two prebuilt static routes
  const res = NextResponse.rewrite(url)                    // browser URL stays "/" (source 35)
  if (fresh) res.cookies.set(COOKIE, bucket!, { path: '/', maxAge: 60 * 60 * 24 * 90, sameSite: 'lax' })
  return res
}
```

- Cost of Pattern B: the split is not PostHog's hash, so you must send the exposure yourself: on the client `posthog.capture('$feature_flag_called', { $feature_flag: FLAG, $feature_flag_response: bucket })` once per session and put `'$feature/<flag>': bucket` on every `lead` event, or configure a custom exposure event (sources 10, 25, 27). PostHog then reports results but its flag is decorative. Inferred from the docs; not run.
- Prefer Pattern A when the page can be dynamic (Vercel serverless renders in tens of ms with local evaluation). Prefer Pattern B when the landing page must stay fully static or cached at the CDN.
- Neither pattern needs `ensure_experience_continuity`; a visitor who clears cookies is a new participant in both PostHog's model and Google's (sources 24, 52).
- Bots: with Pattern A every crawler hit counts as an exposure server-side (source 13). Filter obvious user agents before calling `evaluateFlags` and serve control to them; that is not cloaking because the same rule applies to any request without a cookie and both variants are indexable at the same URL (source 58; the cloaking reading is inferred).

## The sample size math
Assumptions behind every number below: two variants split 50/50, a binary conversion (lead or no lead per exposed person), power 80 percent, alpha 5 percent two-sided, no variance reduction, independent visitors, and the effect held constant over the run.

- Start from Kohavi's rule, n per variant = 16 σ² / Δ², where σ² = p(1-p) for a conversion rate p and Δ is the absolute change you must detect (source 38). The 16 is (z_{0.975} + z_{0.80})² × 2 = (1.96 + 0.842)² × 2 = 15.7, rounded up (arithmetic; z values standard).
- Write Δ as a relative lift: Δ = p × lift. Then n = 16 p(1-p) / (p × lift)² = 16 (1-p) / (p × lift²).
- Multiply by p to convert visitors to leads: leads per variant = n × p = 16 (1-p) / lift². For any p under 10 percent, (1-p) is 0.90 to 0.95, so leads per variant ≈ 16 / lift². That is the whole derivation: the baseline rate cancels out, only the relative lift matters when you count leads.
- PostHog computes exactly this N (source 11), then multiplies by the number of variants and divides by daily exposures for the running time.
- One-sided version: replace 1.96 with 1.645, coefficient becomes (1.645 + 0.842)² × 2 = 12.4, so leads per variant ≈ 12.4 / lift², about 21 percent fewer (arithmetic; Georgiev's 20 to 60 percent range in source 48 covers other power and alpha settings).
- 90 percent power: coefficient 21 instead of 16 (source 38), leads per variant ≈ 21 / lift².

Worked table, computed with the exact two-sample two-sided formula n = (1.96 + 0.842)² × [p(1-p) + p₂(1-p₂)] / (p₂ - p)², and shown next to the 16 / lift² shortcut. "Leads" means expected control-arm leads = n × p.

- Baseline 5.0 percent, lift 20 percent (to 6.0): 8,155 visitors per variant, about 408 leads per variant. Shortcut 16 / 0.2² = 400. PostHog's 16 rule gives 7,600 visitors, 380 leads.
- Baseline 5.0 percent, lift 30 percent (to 6.5): 3,777 visitors per variant, about 189 leads. Shortcut 178. PostHog 3,378 visitors, 169 leads.
- Baseline 5.0 percent, lift 50 percent (to 7.5): 1,468 visitors per variant, about 73 leads. Shortcut 64. PostHog 1,216 visitors, 61 leads.
- Baseline 7.5 percent, lift 20 percent (to 9.0): 5,277 visitors per variant, about 396 leads. Shortcut 400. PostHog 4,933 visitors, 370 leads.
- Baseline 7.5 percent, lift 30 percent (to 9.75): 2,440 visitors per variant, about 183 leads. Shortcut 178. PostHog 2,193 visitors, 164 leads.
- Baseline 7.5 percent, lift 50 percent (to 11.25): 944 visitors per variant, about 71 leads. Shortcut 64. PostHog 789 visitors, 59 leads.
- Baseline 10 percent, lift 20 percent (to 12): 3,838 visitors per variant, about 384 leads. Shortcut 400. PostHog 3,600 visitors, 360 leads.
- Baseline 10 percent, lift 30 percent (to 13): 1,771 visitors per variant, about 177 leads. Shortcut 178. PostHog 1,600 visitors, 160 leads.
- Baseline 10 percent, lift 50 percent (to 15): 683 visitors per variant, about 68 leads. Shortcut 64. PostHog 576 visitors, 58 leads.
- Reading across rows: the leads column barely moves with baseline, which is the point. The shortcut is within 5 percent of exact at 20 percent lift and about 10 percent optimistic at 50 percent lift (the variance of the higher arm grows). PostHog's displayed sample size is 6 to 17 percent lower than exact because it uses one variance term; treat PostHog's "Complete" as a floor, not a finish line.
- One-sided: 321, 149, 58 leads per variant at 20, 30, 50 percent lift (baseline 5 percent). Same shape, a fifth cheaper.
- Calendar time, both arms, whole site: a 20 percent test needs about 800 leads, so 27 months at 30 leads a month, 8 months at 100, 2.7 months at 300. A 30 percent test needs about 360 leads: 12 months, 3.6 months, 1.2 months. A 50 percent test needs about 130 leads: 4.3 months, 1.3 months, 2 weeks (arithmetic; the 2-week case must still run 2 full weeks per source 38).
- Cross-check against the earlier dossier: 300 clicks per variant at 7.63 percent gives lift = sqrt(16 × (1-p) / (p × 300)) = 0.80, i.e. the +80 percent claim holds (arithmetic on source 38's formula).
- Minimum floor regardless of math: PostHog will not show results below 50 exposures and 5 conversions per variant (source 7); those are far below any power threshold and must not be mistaken for enough.

Plain-English rule: count leads, not visitors. You need about 16 divided by the lift squared leads in each arm at 80 percent power. A test that hopes for +20 percent needs 400 leads per arm, +30 percent needs 180, +50 percent needs 65. Below about 70 leads per arm, only a structural change with a plausible +50 percent effect is testable, and even then the run must last at least two full weeks. If you cannot reach the number inside 8 weeks with pooled traffic, do not test; ship best practice and say so.

## Rules for /split-test
- Count leads per arm, not clicks; required leads per arm = 16 / lift² (12.4 one-sided, 21 at 90 percent power).
- Refuse to create the experiment if pooled traffic cannot deliver 70 leads per arm inside 8 weeks; print the months required and recommend shipping on best practice.
- Only build structural variants (layout, offer order, proof placement, CTA architecture), never single-element tests, because the required sample scales with 1 / lift².
- Default MDE in PostHog to 30 percent, never accept below 20 percent at under 300 leads a month.
- Create the flag as multivariate `control` / `test` at 50 / 50 with one release group at 100 percent, `ensure_experience_continuity: false`, `bucketing_identifier: distinct_id`.
- Name the flag key `lp-<client>-<variant-slug>-v<n>` using only letters, numbers, hyphens and underscores.
- Fire the `lead` event once in production before calling the experiments API, or the create call fails on unknown events.
- Use one umbrella `lead` event with `lead_type` in a single-step funnel metric as primary; form-only and call-tap-only funnels as secondary; never a mean or count metric for leads.
- Exposure is `$feature_flag_called`; get it from server-side `flags.getFlag()` once per request and do not also call the client hook for the same key.
- Render the variant on the server and bootstrap posthog-js with the same `distinctID`; the client must never decide the variant.
- If the page must stay static, split in proxy with a cookie and rewrite to `/_v/control` or `/_v/test`, and send the exposure event and `$feature/<key>` yourself.
- Skip proxy on prefetch requests via the `next-router-prefetch` and `purpose: prefetch` header matchers.
- Serve control to known crawler user agents before evaluating flags so bots do not become exposures.
- Keep one URL, no redirects, no alternate URLs, no noindex; canonical points to itself.
- QA with a release-condition override on `utm_source=qa` and a 5 percent soak for 2 days before setting rollout to 100 percent.
- Once launched, never touch the flag, the rollout, the variants or the page content; a change means end with `stopped_early` and start a new experiment.
- Decide the run length before launch from `calculate_running_time`, round up to whole weeks, minimum 2 weeks, maximum 6 weeks.
- Check SRM on exposures weekly with a chi-square at p < 0.01; if it trips, mark the experiment `invalid` and fix plumbing.
- Do not read chance to win before the planned sample; if reading early is unavoidable, switch the experiment to frequentist with sequential testing on.
- Call a winner only when the planned leads per arm are reached and the credible interval excludes zero; report the interval bound nearest zero as the expected lift, never the point estimate.
- Below the planned sample with an interval spanning zero, record `inconclusive`, keep control, and either extend to the next whole week or design a bigger structural change.
- Compare new versus returning visitors before shipping; if the lift is concentrated in returning visitors, extend two more weeks.
- Do not create holdouts below 1,000 leads a month.
- Pool one identical structural variant across every client site in the same trade to reach sample, and segment by `$host` only for reporting.
- Identify a person with a hashed phone or email only at submission, after exposure, never before.
- For webhook-tracked calls, capture a server-side `lead` with `$feature/<key>` joined from the session variant; count `first_call` only.
- Expect one winner in three at best; budget for 1 to 3 tests a year per site at 30 to 300 leads a month.
- Ship a winner with `ship_variant` and `release_to_everyone: true`, then remove the flag code within the same sprint.
