# Research dossier - analyzing split tests, heat maps, funnels and sessions
Built 23 September 2026 · 57 sources opened (60 listed, 3 snippet only) · for /analytics
Next: fold into references/analysis.md and code/analyze.py

## Sources
1. PostHog docs - Bayesian statistics - https://posthog.com/docs/experiments/statistics - 2026 - chance_to_win = 1 - NormalCDF(0, posterior_mean, posterior_std); significant when > confidence_level or < (1 - confidence_level); default 95%.
2. PostHog docs - Frequentist statistics - https://posthog.com/docs/experiments/statistics-frequentist - 2026 - Welch's t-test, alpha 0.05 default (0.10 / 0.01 options), significant when p_value < alpha.
3. PostHog docs - Experiment significance rules - https://posthog.com/docs/experiments/significance - 2026 - 50 exposures per variant minimum; funnel metrics need 5 conversions per variant and n×p > 5 and n×(1-p) > 5.
4. PostHog docs - Experiment statistics overview - https://posthog.com/docs/experiments/experiment-significance - 2026 - confidence level set in Experiments > Settings or per experiment; 90 / 95 / 99.
5. PostHog docs - Sample size and running time - https://posthog.com/docs/experiments/sample-size-running-time - 2026 - N = 16 × variance / d²; default MDE 30%; needs 1 day and 100 exposures before an estimate appears.
6. PostHog docs - Analyzing results - https://posthog.com/docs/experiments/analyzing-results - 2026 - delta chart shows Delta, Exposures, Chance to win or p-value, interval, Total value; "if the interval doesn't cross zero, the result is statistically significant".
7. PostHog docs - Query API - https://posthog.com/docs/api/queries - 2026 - POST /api/projects/:project_id/query/ with query.kind; 2400 req/hour, 240/min, 3 concurrent, 10 s max execution; OFFSET pagination rejected with 400.
8. PostHog docs - Heatmaps API - https://posthog.com/docs/api/heatmaps - 2026 - GET /api/projects/:project_id/heatmaps/ with type click|rageclick|mousemove|scrolldepth, aggregation total_count|unique_visitors, scope heatmap:read.
9. PostHog docs - Toolbar heatmaps - https://posthog.com/docs/toolbar/heatmaps - 2026 - three views (heatmap, clickmap, scrollmap); clickmaps need autocapture, scrollmaps need $pageleave; rageclick = 3 clicks within 30 px in 1 s.
10. PostHog docs - Scroll depth health check - https://posthog.com/docs/health-checks/scroll-depth - 2026 - scroll depth "is collected automatically by posthog-js as part of $pageleave when autocapture is enabled"; property $prev_pageview_max_content_percentage.
11. PostHog tutorial - How to track scroll depth - https://posthog.com/tutorials/scroll-depth - 2026 - percentage depth preferred over pixel depth; $prev_pageview_max_scroll_percentage lives on $pageleave.
12. PostHog docs - Web analytics dashboard - https://posthog.com/docs/web-analytics/dashboard - 2026 - bounce = one pageview, no autocaptures, under 10 seconds.
13. PostHog docs - Autocapture - https://posthog.com/docs/product-analytics/autocapture - 2026 - $autocapture carries $event_type (click / change / submit) and elements_chain; input values are not captured; capture_dead_clicks: true.
14. PostHog tutorial - Analyze autocapture events with SQL - https://posthog.com/tutorials/hogql-autocapture - 2026 - extract(elements_chain, '[:|"]attr__id="(.*?)"') and splitByChar(';', elements_chain) patterns.
15. PostHog docs - SQL - https://posthog.com/docs/product-analytics/sql - 2026 - tables events, persons, groups, raw_session_replay_events; default LIMIT 100.
16. PostHog docs - Funnels - https://posthog.com/docs/product-analytics/funnels - 2026 - sequential / strict / any-order steps; exclusion steps; breakdown by event or person property.
17. PostHog docs - Alerts - https://posthog.com/docs/alerts - 2026 - alerts on trends, funnels (steps and trends views) and SQL insights; absolute or relative thresholds; hourly / daily / weekly / monthly; free tier 5 alerts.
18. PostHog GitHub - posthog/schema.py - https://raw.githubusercontent.com/PostHog/posthog/master/posthog/schema.py - 2026 - Bayesian variant result: key, chance_to_win, credible_interval, delta, significant; frequentist: key, p_value, confidence_interval, delta, significant.
19. PostHog GitHub - schema-general.ts - https://raw.githubusercontent.com/PostHog/posthog/master/frontend/src/queries/schema/schema-general.ts - 2026 - ExperimentStatsBase has number_of_samples, sum, sum_squares (partial read).
20. Evan Miller - How Not To Run An A/B Test - https://www.evanmiller.org/how-not-to-run-an-ab-test.html - 2010 - peeking at 5% turns the real error rate into 26.1%; n = 16σ²/δ².
21. Lukas Vermeer - SRM checker FAQ - https://www.lukasvermeer.nl/srm/docs/faq/ - 2019 - chi-square goodness of fit, extension flags p < 0.01; Microsoft ~6% and LinkedIn ~10% of experiments had SRM; a +1.18% lift reversed to -17.87%.
22. Ronny Kohavi - KDD 2015 keynote (PDF) - https://exp-platform.com/Documents/2015-08OnlineControlledExperimentsKDDKeynoteNR.pdf - 2015 - 1/3 positive, 1/3 flat, 1/3 negative at Microsoft; Bing lower; Twyman's law; Bing keeps a 10% global holdout changed once a year.
23. abtestresult.com - The Winner's Curse in A/B Testing - https://abtestresult.com/articles/winners-curse - 2025 - significant results biased ~13% at 80% power, ~21% with two treatments, ~25% with three; discount 13% minimum, 20%+ with many variants.
24. GuessTheTest - The winner's curse - https://guessthetest.com/the-winners-curse-the-big-problem-with-enormous-winners-in-a-b-testing/ - 2024 - +364% "lift" from 1 vs 3 conversions on 17 vs 11 visitors; Kohavi targets ~2% MDE at Bing.
25. Georgi Georgiev - Analysis of 115 A/B tests - https://blog.analytics-toolkit.com/2018/analysis-of-115-a-b-tests-average-lift-statistical-power/ - 2018 - mean lift 3.77%, median 3.92% across 85 clean tests; ~70% underpowered.
26. Georgi Georgiev - What can be learned from 1,001 A/B tests - https://blog.analytics-toolkit.com/2022/what-can-be-learned-from-1001-a-b-tests/ - 2022 - 33.5% significant winners; median lift of all tests 0.08%; winners median 7.5%; median run 30 days.
27. Georgi Georgiev - Bayesian probability and nonsensical Bayesian statistics - https://blog.analytics-toolkit.com/2020/bayesian-probability-and-nonsensical-bayesian-statistics-in-a-b-testing/ - 2020 - "probability to be best" rests on a Beta(1,1) prior; A/A tests sit near 50% forever.
28. Statsig docs - Holdouts - https://docs.statsig.com/experiments/holdouts-introduction - 2026 - hold out 1-2% of users, run 3-6 months, then release.
29. Statsig - Hold-out groups in A/B testing - https://www.statsig.com/perspectives/holdout-groups-ab-testing - 2025 - alternative 45 / 45 / 10 split; holdout guards against summing individual lifts.
30. Statsig - The multiple comparisons problem - https://www.statsig.com/perspectives/multiple-comparisons-abtests-care - 2025 - family-wise error 1-(1-α)^m; 20 tests gives 64%; Bonferroni divides alpha; "data dredging kills more experiments than any statistical error".
31. Conversion.com - 3 mistakes that invalidate A/B test results - https://www.conversion.com/blog/3-mistakes-invalidate-ab-test-results/ - 2023 - 41 shades of blue = 88% false positive chance; Simpson's paradox example 2.30% vs 2.02% and 1.2% vs 1.0% flipping to 1.20% vs 1.68%; post-hoc segments too small.
32. ConversionTeam - A/B test win rate, 2,288 audited tests - https://www.conversionteam.com/ab-test-win-rate/ - June 2026 - 19.1% statistically significant wins; lead gen tests 60.8% raw win vs 49.9% ecommerce; forms 43.4% raw.
33. Huang, White, Buscher - User See, User Point (CHI 2012, PDF) - https://jeffhuang.com/papers/GazeCursor_CHI12.pdf - 2012 - cursor inactive 58.8% of time; median gaze-cursor distance 233 px inactive, 150 px reading, 77 px action, 74 px at click.
34. Contentsquare (ex Hotjar) - Heatmaps guide - https://contentsquare.com/guides/heatmaps/ - 2026 - move maps show "where people might be looking"; collect at least 2,000-3,000 pageviews before drawing conclusions.
35. Microsoft Learn - Clarity scroll maps - https://learn.microsoft.com/en-us/clarity/heatmaps/scroll-maps - Sep 2025 - % scrolled in 5% increments, # of visitors, % drop off; average fold; pageviews capped at 100,000 per heatmap.
36. Microsoft Learn - Clarity area maps - https://learn.microsoft.com/en-us/clarity/heatmaps/area-maps - Sep 2025 - area CTR = clicks in area / total clicks on matched pages; areas not saved across sessions.
37. Zuko - Form type benchmarking - https://www.zuko.io/benchmarking/form-type-benchmarking - 2025 - contact forms 47.4% completion (desktop 51.2%, mobile 39.4%), enquiry 42.7% (47.7% / 37.7%); 93,022,997 sessions.
38. Zuko - 8 surprising insights from benchmarking data - https://www.zuko.io/blog/8-surprising-insights-from-zukos-benchmarking-data - 2024 - 34% of starters abandon; desktop 47.01% vs mobile 42.95%; average abandonment at 1 min 43 s; field returns 5.61 completed vs 4.55 abandoned.
39. Zuko - Industry benchmarking - https://www.zuko.io/benchmarking/industry-benchmarking - 2025 - property 34.55%, utilities 43.38%, automotive 44.78% view-to-completion.
40. Baymard - Checkout form fields - https://baymard.com/blog/checkout-flow-average-form-fields - June 2024 - average 11.3 fields, can be 8; 17% abandoned for "too long / complicated".
41. LocaliQ - Search advertising benchmarks 2026 - https://localiq.com/blog/search-advertising-benchmarks/ - June 2026 - all-industry CVR 8.18%, CPL $66.69, CPC $5.42, CTR 6.64%; Home & Home Improvement CVR 8.05%, CPL $90.92.
42. TheeDigital - 2026 Google Ads benchmarks (WordStream/LocaliQ mirror) - https://www.theedigital.com/blog/google-ads-benchmarks - 2026 - 13,474 US search campaigns, 23 industries, April 2025 to March 2026, medians.
43. WordStream - 2026 Google Ads benchmarks - https://www.wordstream.com/blog/2026-google-ads-benchmarks - 2026 - (snippet only) same dataset as 41 and 42.
44. Unbounce - Conversion Benchmark Report - https://unbounce.com/conversion-benchmark-report/ - 2024 - median landing page CVR 6.6%; 41,000+ pages, 464M visitors, 57M conversions; paid search 10.9%.
45. Ruler Analytics - Conversion rate by industry 2026 - https://www.ruleranalytics.com/blog/insight/conversion-rate-by-industry/ - May 2026 - overall 5.13%; paid search 5.4%; construction & engineering 4.9%; 110M sessions.
46. Google Ads Help - Data discrepancies factors - https://support.google.com/google-ads/answer/7457111 - 2026 - Ads reports on the interaction date, other tools on conversion date; invalid conversions removed after the fact; cross-device modeled.
47. Google Ads Help - Understand your conversion tracking data - https://support.google.com/google-ads/answer/6270625 - 2026 - primary conversion columns "calculated based on the time of the click"; lag up to 24-48 hours; count "One" for leads.
48. Google Ads Help - About conversion windows - https://support.google.com/google-ads/answer/3123169 - 2026 - click-through default 30 days, range 1-90; view-through default 1 day; engaged-view 3 days.
49. Google Ads Help - Offline conversion imports with GCLID - https://support.google.com/google-ads/answer/7012522 - 2026 - auto-tagging required; sample cookie expiry 90 days; enhanced conversions for leads uses hashed email/phone.
50. Nice Looking Data - Google Ads vs GA4 conversions don't match - https://www.nicelookingdata.com/blog/ga4-vs-google-ads-conversions-dont-match - 2026 - 10-30% gap "isn't, by itself, evidence of a bug"; double counting when native tag and imported key event are both Primary.
51. HighLevel Support - Understanding attribution source - https://help.gohighlevel.com/support/solutions/articles/48001219997-understanding-attribution-source - 2026 - First and Latest attribution; Paid Search when utm_source contains "adwords" or gclid / wbraid / gbraid present; matching is case-sensitive.
52. Attributer - Capture the GCLID in GoHighLevel - https://attributer.io/blog/capture-gclid-gohighlevel - 2025 - hidden GCLID field; value stored in browser so it survives multi-page visits; push to Ads via Zapier "Send Offline Conversion".
53. UTM Grabber - Track UTM parameters in GoHighLevel - https://utmgrabber.com/blog/gohighlevel-utm-parameters/ - 2026 - custom fields gclid, gbraid, wbraid, fbclid, msclkid; hidden field "Query Key"; protect first-touch fields.
54. CallRail - What is dynamic number insertion - https://www.callrail.com/blog/what-is-dynamic-number-insertion - 2025 - cookie pins one number per visitor; source-level vs visitor-level pools.
55. CallRail - Google Ads call tracking - https://www.callrail.com/blog/adwords-call-tracking - 2025 - visitor-level pool captures gclid; calls pushed to Ads as conversions.
56. Lunio - Spam leads - https://www.lunio.ai/blog/spam-leads - 2025 - same IP / fingerprint, mistyped emails, tiny session times as spam tells; AI-driven fraud attempts +27% YoY.
57. Speero - Program metrics blueprint - https://speero.com/blueprints/program-metrics - 2024 - velocity, idea rate, backlog, test creation time; report monthly or quarterly beside wins / losses.
58. Speero - Decision matrix blueprint - https://speero.com/blueprints/decision-matrix - 2023 - (partial) tags each test implement / iterate / abandon; matrix itself is in the PDF.
59. CXL - How to communicate A/B test results - https://cxl.com/blog/how-to-communicate-ab-test-results/ - 2019 - (snippet only) show lift, conversion rate per variation, interval, projected value, lessons learned.
60. Exp-platform / Fabijan et al. - Diagnosing SRM (KDD 2019) - https://exp-platform.com/Documents/2019_KDDFabijanKDD.pdf - 2019 - (snippet only, 404 at this URL) numbers taken from source 21.

Note: sources 43, 59 and 60 were not opened (403 / 404). Everything else above was fetched and read on 23 September 2026. Sources 18, 19 and 58 were read only in part.

## Findings

### 1. Reading an experiment honestly
- (a) PostHog defaults to Bayesian. chance_to_win = 1 - NormalCDF(0, posterior_mean, posterior_std). 95% credible interval = posterior_mean ± 1.96 × posterior_std. Significant when chance_to_win > 0.95 or < 0.05 at the default 95% level (source 1).
- (a) Frequentist option uses Welch's t-test; significant when p_value < alpha, alpha 0.05 by default. Interval is point_estimate ± t_critical × sqrt(pooled_variance) (source 2).
- (a) Nothing is reported until each variant has 50 exposures. Funnel metrics also need 5 conversions per variant and n×p > 5 and n×(1-p) > 5 (source 3). A plumber page at 3% CVR needs 167 exposures per arm just to clear the 5-conversion floor.
- (a) PostHog's own sample size formula: N per variant = 16 × variance / d², variance = p(1-p) for funnels, d = absolute effect. Default MDE 30% relative. The estimate shows "Pending" until 1 day and 100 exposures have passed (source 5). Worked example: p = 0.04, 30% MDE means d = 0.012; N = 16 × 0.0384 / 0.000144 = 4,267 per arm. At 20% MDE it is 9,600 per arm. At 10% MDE it is 38,400 per arm.
- (a) Evan Miller: with a nominal 5% level and stopping the first time it looks significant, the real false positive rate is 26.1%. To keep a true 5% after 10 peeks you need a reported 1.0% (source 20). PostHog's docs say to "look for results that stay consistent over several days" but set no run-length rule (source 6).
- (c) Georgiev's critique: "probability to be best" from a Beta(1,1) prior treats a refined control and an untested variant as 1-to-1 odds; on an A/A test the number hovers near 50% no matter how much data arrives. Treat chance_to_win as a belief statement, not an error rate (source 27).
- (a/b) SRM: chi-square goodness of fit on the exposure split. The SRM checker flags p < 0.01; Microsoft saw SRM in ~6% of experiments, LinkedIn ~10%. One documented +1.18% "win" became -17.87% after the ~2,000 missing subjects were accounted for (source 21). Bing runs a 10% global holdout changed once a year (source 22).
- (b) Segment cuts: family-wise error = 1-(1-α)^m. Five cuts (mobile, desktop, new, returning, campaign) at α 0.05 gives 22.6%; twenty cuts gives 64%. Bonferroni divides alpha by m (source 30). Conversion.com: post-hoc segments are too small and reintroduce the same problem; Google's 41 shades of blue had an 88% false positive chance (source 31).
- (b) Simpson's paradox is real on small pages: variant won Friday (2.30% vs 2.02%) and Saturday (1.2% vs 1.0%) yet lost combined (1.20% vs 1.68%) because allocation changed mid-test (source 31). Never change the split mid-test.
- (b) Winner's curse: conditioning on significance inflates the estimate. At 80% power the bias is about 13%; with two treatments ~21%; three treatments ~25%. Plan with a 13% haircut minimum, 20%+ when there are several variants or metrics (source 23). GuessTheTest's +364% example came from 1 vs 3 conversions (source 24).
- (b) Base rates: Microsoft 1/3 positive, 1/3 flat, 1/3 negative; Bing lower (source 22). Georgiev 1,001 tests: 33.5% significant winners; median lift across all tests 0.08%; winners median 7.5%, mean 15.9%; median run 30 days; median sample 60,342 users (source 26). Georgiev 115 tests: mean lift 3.77%, ~70% underpowered (source 25). ConversionTeam 2,288 tests: 19.1% significant wins; lead gen 60.8% raw win rate; form tests only 43.4% raw (source 32).
- (a/c) Holdouts: Statsig recommends 1-2% held out for 3-6 months then released; the holdout is compared with an equal-sized served sample (source 28). A 45 / 45 / 10 split is the practical shape for a small site (source 29). For a page doing 500 visits a week a 10% holdout is 50 visits and will never read; use the holdout only for the programme number, never for a single test.
- (c) Inconclusive: if the interval spans zero and includes both meaningful gain and meaningful loss, it is inconclusive, not a loss. Move on after two or three iterations with no signal (search summary of source list; treat as practitioner consensus).

### 2. Heatmap interpretation
- (b) Mouse is not eye. Huang, White and Buscher (36 subjects, 32 tasks, 50 Hz Tobii): cursor inactive 58.8% of the time; median gaze-cursor distance 233 px when inactive, 167 px examining, 150 px reading, 77 px on action, 74 px at click. The cursor lags gaze by at least 250 ms and on average 700 ms. They "question the maxim that gaze is well approximated by cursor" (source 33). Move maps are attention hints at best; on mobile there is no cursor at all.
- (c) Contentsquare / Hotjar: move maps show "where people might be looking"; collect at least 2,000-3,000 pageviews before drawing conclusions (source 34). For a local page doing 100 to 300 visits a week that is a 2 to 6 week wait; say so in the report.
- (a) PostHog heatmap types: click, rageclick, mousemove, scrolldepth. Rageclick = three clicks within 30 px in one second. Dead clicks need capture_dead_clicks: true. Clickmaps depend on autocapture; scrollmaps depend on $pageleave. Aggregation is total_count or unique_visitors; unique counts by distinct ID so one person on two devices counts twice (sources 8, 9, 13).
- (a) Scroll depth: $prev_pageview_max_scroll_percentage and $prev_pageview_max_content_percentage are written onto the next $pageleave. Collected only when autocapture is on (sources 10, 11). Known bug: values were kept for the whole tab in SPAs, so a later unscrolled page could inherit an earlier page's max scroll; fixed in posthog-js (GitHub issue 4912, seen in search only).
- (a) Clarity for comparison: scroll data listed in 5% increments with # of visitors and % drop off per band; hover shows exact % reaching that pixel; presets 25 / 50 / 75%; average fold line; 100,000 pageviews cap per heatmap (source 35). Area maps give CTR = clicks in the area / all clicks on matched pages (source 36). Copy this shape: the report should read "62% reached the reviews, 31% reached the form".
- (c) Known false positives: clicks on images and non-links (users expect a lightbox or a link), rage clicks on a slow button that did respond, clicks on text to select it, mobile scroll-taps counted as clicks, and cursor parked on a paragraph while reading (source 33, 34). Always pair a click hotspot with the element's tag; a hot non-link is a dead click problem, not interest.
- (c) Section-level read: convert scroll depth to section reach using each section's top offset as a percentage of page height at the median viewport; the section with the largest drop between its top and the next section's top is the leak. Report the drop in people, not percent.

### 3. Funnel analysis for a lead form
- (b) Zuko, 93,022,997 sessions: contact forms 47.4% starter-to-completion (desktop 51.2%, mobile 39.4%, tablet 39.6%); enquiry forms 42.7% (47.7% / 37.7% / 35.6%); contact forms average 19.2 fields, enquiry 17.4 (source 37). 34% of starters abandon; desktop 47.01% vs mobile 42.95%; average time to abandonment 1 min 43 s; field returns 5.61 in completed sessions vs 4.55 in abandoned (source 38). Property 34.55%, utilities 43.38%, automotive 44.78% view-to-completion (source 39). Zuko is the renamed Formisimo product, so these are the Formisimo benchmarks.
- (b) Baymard: checkout averages 11.3 fields, 8 is achievable; 17% abandoned because checkout was too long or complicated (source 40). A plumber form needs name, phone, postcode, problem: four fields.
- (a) PostHog autocapture fires $autocapture with $event_type click / change / submit and elements_chain; input values are never captured, so field identity comes from attr__name or attr__id inside elements_chain (sources 13, 14).
- (c) Metrics to compute per field: starters (first change on any field), reach (distinct sessions with a change on that field), drop (reach of field k minus reach of field k+1), re-entry (more than one change event on the same field in a session), time-to-first-interaction (first field change minus $pageview), error rate needs an explicit form_error event because autocapture cannot see validation text.
- (c) Words for the owner: "312 people opened the form. 190 typed a name. 121 typed a phone. 74 hit send. Phone is where 69 people quit."

### 4. Benchmarks 2025-2026 for local services
- (b) LocaliQ / WordStream 2026, 13,474 US search campaigns, 23 industries, April 2025 to March 2026, medians: all industries CVR 8.18%, CPL $66.69, CPC $5.42, CTR 6.64%. Home & Home Improvement CVR 8.05%, CPL $90.92, CPC $8.33, CTR 6.47%. Automotive repair CVR 15.51%, CPL $29.96. Attorneys CVR 5.55%, CPL $131.63. Dentists CVR 10.67%, CPL $72.97. Physicians CVR 12.43%, CPL $40.04. Personal services CVR 12.34%, CPL $54.60. "Cost per lead decreased overall for the first time in five years." A lead is any click that ends in a phone call, chat, form or email (sources 41, 42).
- (b) Unbounce 2024, 41,000+ pages, 464M visitors, 57M conversions: median landing page CVR 6.6%; paid search 10.9% (Google 11.3%); desktop converts 8% better than mobile; mobile is 83% of visits (source 44).
- (b) Ruler Analytics May 2026, 110M sessions: overall 5.13%; paid search 5.4%; construction & engineering 4.9%; conversion = qualified lead or sale (source 45).
- Caveats to print with any benchmark: LocaliQ counts calls, chats, forms and emails from the ad click; Unbounce counts the landing page form only; Ruler counts qualified leads after CRM matching. A page at 4% form-only CVR can be at 8% once calls are added. Never compare a form-only number to LocaliQ's all-contact number without saying so.

### 5. Reconciliation: PostHog vs CRM vs Google Ads
- (a) Google Ads counts on the click date, "not the time of the conversion"; reporting lag up to 24-48 hours; count "One" per click for leads to avoid refresh double counts (source 47). Click-through window default 30 days, allowed 1-90; view-through 1 day; engaged-view 3 days (source 48). Invalid conversions are removed after the fact when clicks are judged spam (source 46).
- (c) A 10-30% gap between Ads and GA4 or PostHog is normal and not itself a bug; the biggest single cause is click-date vs conversion-date, then double counting when a native tag and an imported key event are both Primary, then cross-device and view-through, then consent-mode modelling (source 50).
- (a) Offline import needs auto-tagging on and the gclid stored at form time; Google's sample cookie expires at 90 days; enhanced conversions for leads can match on hashed email or phone when gclid is missing (source 49).
- (a) GoHighLevel stores First and Latest attribution; it labels a session Paid Search when utm_source contains "adwords" or a gclid, wbraid or gbraid is present; matching is case-sensitive (source 51). To hold the raw gclid you create custom fields (gclid, gbraid, wbraid, fbclid, msclkid) and map hidden form fields by Query Key; protect first-touch fields from overwrite (sources 52, 53).
- (c) Calls: CallRail visitor-level DNI pins one number per visitor via cookie, captures the gclid and pushes calls to Ads as conversions (sources 54, 55). Calls from the Google Business Profile or a cached number are not swapped and will be missing from PostHog entirely.
- (c) Spam: same IP or fingerprint, mistyped or disposable emails, sub-5-second sessions, repeat submits; AI-driven fraud up 27% YoY (source 56). Search summaries claim 30-60% of paid leads are junk in some verticals; treat that as a claim, not a benchmark, and count your own.
- Rule for the join: key on gclid first, then lowercased email, then E.164 phone, then a 30-minute window on timestamp plus landing path. Dedupe PostHog by distinct_id and CRM by phone. Tag test leads by a known test email domain and any submission from the office IP.
- Trust levels to print before quoting: Level A, gclid matched in all three systems; Level B, email or phone matched between PostHog and CRM only; Level C, PostHog count only, unmatched. Quote the Level A count as the lead number, give B and C as the range.

### 6. Reporting shape for non-technical owners
- (c) CXL: show lift, conversion rate per variation, the interval, projected value, and a lessons-learned line; tailor depth to the audience (source 59, snippet). Speero tags every test implement / iterate / abandon and reviews programme metrics monthly or quarterly (sources 57, 58).
- (b) Realistic expectations to print: one third win, one third flat, one third lose (source 22); median lift of a real winner about 4-8% (sources 25, 26); a "+40%" on a local page is almost always noise from single-digit conversions (source 24).
- (c) Programme metrics: tests run, conclusive rate, win rate, median lift of winners after the 13% haircut, cumulative lift against the holdout, days from idea to live (source 57).
- (c) 30-day cadence: review on day 30 because Georgiev's median test ran 30 days (source 26) and most local pages need 4 full weeks to clear 100 exposures per arm per week. Kill if the variant is losing and the interval upper bound is below the MDE; iterate if inconclusive with a plausible mechanism; scale (roll to 100% and copy the pattern to other pages) if significant and the haircut lift still beats the MDE.

### 7. Automating the read
- (a) One endpoint does everything: POST /api/projects/:project_id/query/ with a personal API key holding Query Read. Kinds: HogQLQuery, EventsQuery, TrendsQuery, FunnelsQuery, RetentionQuery, PathsQuery. refresh accepts blocking, async, force_blocking, force_async, force_cache, lazy_async, async_except_on_cache_miss. Poll GET /api/projects/:project_id/query/:query_id/. Limits: 2400 requests per hour, 240 per minute, 3 concurrent, 10 s execution, default 100 rows, 50,000 max with an explicit LIMIT, no OFFSET (400). Budget exhaustion returns 429 api_queries_budget_exceeded (source 7).
- (a) Heatmap points come from GET /api/projects/:project_id/heatmaps/ with url_exact or url_pattern, viewport_width_min / max, date_from (default -7d), type, aggregation; needs heatmap:read (source 8).
- (a) Alerts run on trends, funnels and SQL insights with absolute or relative thresholds, hourly to monthly, to email, Slack, Discord, Teams or webhook; 5 alerts on the free tier (source 17).
- (c) Split of work: ask PostHog for raw counts (exposures, conversions, per-field change events, scroll percentages, heatmap points). Compute in Python: SRM chi-square, chance to win or p-value (so the number is reproducible), winner's-curse haircut, section reach from scroll buckets, field drop-off, reconciliation joins, trust levels. Never recompute what PostHog already returns unless you also want to audit it.
- (c) Scheduling: one cron at 06:00 local on Monday for the weekly read, one at day 30 for the review; stay under 240 requests per minute by issuing at most 20 queries per run with blocking refresh.

## Exact API facts (verified)
- Confirmed: POST /api/projects/:project_id/query/ body shape (source 7).

```json
{
  "query": { "kind": "HogQLQuery", "query": "SELECT ..." },
  "name": "scroll_depth_by_bucket",
  "refresh": "blocking"
}
```

- Confirmed: response fields results, is_cached, cache_key, cache_target_age, query_status {id, team_id, complete} (source 7).
- Confirmed: property names $prev_pageview_max_scroll_percentage and $prev_pageview_max_content_percentage on $pageleave (sources 10, 11). Inferred: $prev_pageview_pathname, $prev_pageview_duration, $prev_pageview_last_scroll_percentage also exist (seen in search results, not opened in docs).
- Confirmed: HogQL scroll depth query shape (source 11 plus search result quoting the docs).

```sql
SELECT
  round(avg(properties.$prev_pageview_max_scroll_percentage) * 100, 1) AS avg_max_scroll_pct,
  count() AS pageleaves
FROM events
WHERE event = '$pageleave'
  AND properties.$prev_pageview_pathname = '/plumber-toronto'
  AND timestamp > now() - INTERVAL 30 DAY
```

- Inferred (built from confirmed functions): scroll reach buckets for section mapping.

```sql
SELECT
  b AS bucket,
  countIf(properties.$prev_pageview_max_scroll_percentage >= b / 100) AS reached,
  count() AS total,
  round(reached / total * 100, 1) AS pct_reached
FROM events
ARRAY JOIN [10,20,30,40,50,60,70,80,90,100] AS b
WHERE event = '$pageleave'
  AND properties.$prev_pageview_pathname = '/plumber-toronto'
  AND timestamp > now() - INTERVAL 30 DAY
GROUP BY b ORDER BY b
```

- Confirmed: elements_chain extraction patterns (source 14). Inferred: applying them to count clicks per element.

```sql
SELECT
  extract(elements_chain, '[:|"]attr__id="(.*?)"') AS el_id,
  arrayElement(splitByChar('.', elements_chain), 1) AS tag,
  count() AS clicks,
  uniq(distinct_id) AS people
FROM events
WHERE event = '$autocapture'
  AND properties.$event_type = 'click'
  AND properties.$pathname = '/plumber-toronto'
  AND timestamp > now() - INTERVAL 30 DAY
GROUP BY el_id, tag ORDER BY clicks DESC LIMIT 50
```

- Inferred: per-field reach for the form funnel, keyed on the change event and the field name in elements_chain.

```sql
SELECT
  extract(elements_chain, '[:|"]attr__name="(.*?)"') AS field,
  uniq($session_id) AS sessions_touched,
  count() AS change_events
FROM events
WHERE event = '$autocapture'
  AND properties.$event_type = 'change'
  AND properties.$pathname = '/plumber-toronto'
  AND timestamp > now() - INTERVAL 30 DAY
GROUP BY field ORDER BY sessions_touched DESC
```

- Confirmed: experiment variant result fields. Bayesian: key, chance_to_win, credible_interval [lo, hi], delta, significant. Frequentist: key, p_value, confidence_interval [lo, hi], delta, significant (source 18, class names carry a Max prefix in schema.py). Base stats: number_of_samples, sum, sum_squares (source 19).
- Confirmed: significance rules 50 exposures, 5 conversions, n×p > 5, chance_to_win outside (1-c, c) (sources 1, 3). Frequentist alpha 0.05 (source 2).
- Inferred: the query kind for experiment results is ExperimentQuery (schema-general.ts shows the interface stub; response type not read). Confirm before coding by GET /api/projects/:project_id/experiments/:id/ and reading metrics_results.
- Confirmed: heatmaps endpoint and parameters (source 8). Inferred: scrolldepth response is cumulative reach buckets, exact JSON keys not seen.
- Confirmed: rate limits and no OFFSET (source 7).
- SRM in Python (compute locally): scipy.stats.chisquare([n_control, n_variant], f_exp=[N/2, N/2]); flag when p < 0.01 (source 21).

## The report shape
- Line 1, the decision: "Ship the new headline. It won."
- Line 2, the leads: "Old page: 41 leads from 1,204 visits. New page: 58 leads from 1,198 visits."
- Line 3, the confidence: "Chance the new page really is better: 97 out of 100. We only trust that because both pages got the same traffic (split checked)."
- Line 4, the honest lift: "Looks like +41%. Real lift is probably nearer +30% once luck is taken out. Plan on +25%."
- Section: where people stop reading. "82 of 100 saw your reviews. 46 of 100 reached the price box. 29 of 100 reached the form. The price box is where you lose half of them."
- Section: what they click. "The van photo got 88 clicks. It does nothing when clicked. Make it open the gallery or stop making it look clickable."
- Section: the form. "312 opened it. 190 typed a name. 121 typed a phone. 74 sent it. Phone is the wall. 69 people left there."
- Section: what the recordings showed. "12 of 20 mobile sessions pinched to zoom the price table. It is too small on phones."
- Section: do the numbers agree. "PostHog says 58 leads. GoHighLevel has 55 contacts. Google Ads says 49. 47 match in all three by click ID. Quote 47 to your accountant, 58 to nobody."
- Section: against the market. "You convert 4.8% of clicks to a form. Add calls and it is 7.9%. Home services median is 8.05%. You are at the median."
- Section: 30-day verdict. "Kill the video test. Iterate the form (cut to 4 fields). Scale the headline to the Mississauga page."
- Section: the programme. "3 tests run. 1 won, 1 flat, 1 lost. That is normal. Holdout says the site is up 9% on leads since June."
- Last line: next step, one sentence, with a date.

## Decision rules
- Ship: PostHog significant (chance_to_win ≥ 0.95, or p < 0.05), each arm has ≥ 50 exposures and ≥ 5 conversions, run ≥ 14 days covering two full weeks, SRM p ≥ 0.01, and the lift after a 13% haircut (20% if more than one variant) is still ≥ the MDE set at launch.
- Kill: significant in the wrong direction under the same checks, or the interval's upper bound is below the MDE after 30 days, or 3 iterations of the same idea have read flat.
- Keep running: not yet significant and projected exposures at current traffic will reach PostHog's recommended sample within 30 more days; report the day count remaining.
- Inconclusive after 30 days and sample reached: ship the cheaper or simpler variant, log it as flat, do not claim lift.
- Do not test: fewer than ~100 conversions per arm reachable in 8 weeks at 20% MDE (traffic × CVR × 56 days / 2 < 100); fix tracking or run a pre/post read instead.
- Do not trust: SRM p < 0.01, or reconciliation Level A count is under 70% of the PostHog count, or a lift over 50% built on fewer than 30 conversions per arm.
- Heatmap read allowed: ≥ 2,000 pageviews on the page at the same viewport class; below 500 say "not enough yet".
- Form funnel read allowed: ≥ 100 form starters; below that give counts only, no percentages.

## Rules for /analytics
- Open with the decision in five words or fewer, then the lead counts.
- Always run the SRM chi-square before reading any experiment number.
- Quote PostHog's chance_to_win or p_value as given, then recompute it from exposures and conversions and note any gap.
- Apply the winner's-curse haircut (13%, or 20% for A/B/n) to every declared lift and print both numbers.
- Never cut a result by segment unless the segment was named before launch; if you must, apply Bonferroni.
- Turn scroll percentages into section reach using section offsets at the median viewport; name the single biggest drop.
- Treat move maps as guesses and mobile move maps as nothing.
- Pair every click hotspot with its element tag; non-link hotspots are dead-click bugs.
- Report the form as a count ladder: opened, first field, phone, sent.
- Reconcile before quoting: gclid, then email, then phone, then time window; print Level A / B / C counts.
- Expect a 10-30% gap between PostHog and Google Ads and say why in one line (click date vs conversion date).
- Strip spam, duplicates and test leads before benchmarking and say how many were stripped.
- Compare against LocaliQ only after adding tracked calls; compare form-only rates against Unbounce.
- Print the base rates (one third win, median real lift 4-8%) whenever a lift over 20% appears.
- Every 30 days write kill / iterate / scale per test and the four programme numbers.
- Stay under 20 PostHog queries per run, blocking refresh, and keep every HogQL query with an explicit LIMIT.
