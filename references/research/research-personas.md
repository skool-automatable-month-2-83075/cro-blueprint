# Research dossier - the persona panel
Built 23 September 2026 · 51 sources opened · for /personas
Next: fold the rules into references/persona-panel.md

Extends Part 3 of research-cro-gaps-2026-09-12.md. That part established: variance collapse, NN/G sycophancy, demographic misalignment, the inverted stop bar, "two agents on one model is one draw", pin the model version, reviews for language not for avatars. Nothing below repeats those; it sources them harder, adds what has been published since, and turns them into a file shape, a prompt and rules.

## Sources
1. Synthetic Users: If, When, and How to Use AI-Generated "Research" (Rosala, Moran, NN/G) - https://www.nngroup.com/articles/synthetic-users/ - 21 Jun 2024 - three real studies replicated with Synthetic Users and ChatGPT; synthetic users finished every course, praised forums real users called contrived, listed seven unranked factors; drone-delivery concept called "a game-changer".
2. A Review of Experiments with Synthetic Users (Lewis, Sauro, MeasuringU) - https://measuringu.com/review-of-experiments-with-synthetic-users/ - 14 Apr 2026 - 12 peer-reviewed papers tallied: 9 encouraging vs 14 discouraging findings; reduced variance, exaggerated effects, shallow qualitative answers; use for direction only.
3. Out of One, Many (Argyle et al., Political Analysis 31(3)) - https://www.cambridge.org/core/journals/political-analysis/article/out-of-one-many-using-language-models-to-simulate-human-samples/035D7C8A55B237942FB6DBAD7CAA4E49 - Jul 2023 - origin of "silicon samples" and "algorithmic fidelity": GPT-3 conditioned on thousands of real ANES backstories reproduced subgroup response distributions.
4. Synthetic Replacements for Human Survey Data? The Perils of LLMs (Bisbee et al., Political Analysis) - https://www.cambridge.org/core/journals/political-analysis/article/synthetic-replacements-for-human-survey-data-the-perils-of-large-language-models/B92267DC26195C7F36E63EA04A47D2FE - 17 May 2024 - 7,530 ANES personas x 30 draws = 3.6M responses; less variance than humans; 48% of coefficients differ, sign flips in 32% of those; identical prompts drifted April to July 2023.
5. Generative Agent Simulations of 1,000 People (Park et al., arXiv 2411.10109) - https://arxiv.org/abs/2411.10109 - Nov 2024, rev Jun 2026 - 1,052 people, two-hour interviews; agents hit 85 to 86% of participants' own two-week test-retest on the GSS; interview-grounded agents cut racial and ideological accuracy gaps vs demographics-only agents.
6. Twin-2K-500 (Toubia et al., Marketing Science / arXiv 2505.17479) - https://arxiv.org/abs/2505.17479 - 23 May 2025 - 2,058 US adults, 500 questions, 4 waves; GPT-4.1-mini twins reach 72% accuracy, 88% of test-retest; public testbed.
7. When Can You Trust Your Synthetic Users? (Tigre, Souto, arXiv 2609.13148) - https://arxiv.org/abs/2609.13148 - 3 Jun 2026 - 172,884 paired human/GPT-4.1-mini answers; variance compressed about 2x, subgroup error 10 to 30 points; a 50 to 300 person human calibration sample plus a doubly robust estimator removed 83 to 94% of bias.
8. When Can LLM Digital Twins Reduce Human Measurement? (Wang, Hunt, Tang, Joseph, arXiv 2609.07987) - https://arxiv.org/abs/2609.07987 - 7 Sep 2026 - twins reproduce average effects but say little about which individuals differ; "behavioral fidelity is neither necessary nor sufficient for statistical substitutability".
9. Marginal Fidelity Does Not Establish User Simulation (Doudkin, arXiv 2609.07305) - https://arxiv.org/abs/2609.07305 - 7 Sep 2026 - matching topline survey numbers proves nothing about simulating individuals; committed-answer panels left 66 of 128 option slots empty ("support collapse"); a no-persona population query beat persona panels in 9 of 9 comparisons.
10. This human study did not involve human subjects (Hullman, Broska, Sun, Shaw, arXiv 2602.15785) - https://arxiv.org/abs/2602.15785 - 17 Feb 2026 - prompt engineering is fine for exploratory work; confirmatory claims need statistical calibration on auxiliary human data.
11. ChatGPT is not A Man but Das Man (Li, Li, Qiu, arXiv 2507.02919) - https://arxiv.org/abs/2507.02919 - 25 Jun 2025 - GPT-4 and Llama 3.1 on ANES 2020: homogenisation, minority opinions under-represented, accuracy does not hold across aggregation levels; "accuracy-optimisation hypothesis" (model picks the modal answer).
12. Random Silicon Sampling (Sun et al., arXiv 2402.18144) - https://arxiv.org/abs/2402.18144 - 28 Feb 2024 - group-level demographics alone reproduce US poll distributions on some items; replicability varies by demographic group and topic.
13. Synthetic Sampling Report IV (Verasight) - https://www.verasight.io/reports/synthetic-omnibus-survey - 13 Jan 2026 - 2,000 humans vs GPT-5.2 twins; mean absolute error 14.5 points over 305 options, 23.4 on healthcare; works only where attitudes have strong demographic correlates; warns against market research use.
14. Synthetic Sample in Social Research (Verian, SRA coverage) - https://www.veriangroup.com/news-and-insights/synthetic-sample-in-social-research - Mar 2026 - small prompt changes swing results; same question gives different "samples" per run; under-represents older, less educated, rural and offline people; legitimate use limited to pretests and comms testing.
15. Your Next Respondent Might Be an LLM (NIM summary of Sarstedt, Adler, Rau, Schmitt, Psychology & Marketing 41(6)) - https://www.nim.org/en/publications/detail/using-silicon-samples-in-marketing-research - 2024 - in their review only 24.9% of silicon-vs-human comparisons matched, 65.3% diverged; use for pretesting; validate against human distributions; never accept output at face value. Original Wiley page (snippet only, 403).
16. CoMPosT: Characterizing and Evaluating Caricature in LLM Simulations (Cheng, Piccardi, Yang, EMNLP 2023) - https://arxiv.org/abs/2310.11501 - 17 Oct 2023 - caricature = low individuation plus exaggeration; political and marginalised personas on general, uncontroversial topics are most caricatured, GPT-4 included.
17. Tastes without distinction: silicon samples and the synthetic construction of tastes (Ma, Zhang, Ang, Chen, arXiv 2606.30085) - https://arxiv.org/abs/2606.30085 - 29 Jun 2026 - 554,940 synthetic SPPA respondents across OpenAI, Anthropic, DeepSeek; models "juvenilize age-taste associations", inflate preferences, caricature gender and race.
18. From Demographics to Survey Anchors: LLM Agents for Retirement Attitudes (Garzón et al., arXiv 2605.16303) - https://arxiv.org/abs/2605.16303 - 24 Apr 2026 - SHARE data on older Europeans; demographics-only agents show central-tendency bias and never say "don't know"; anchoring on real in-domain answers fixes most of it.
19. Bias Runs Deep: Implicit Reasoning Biases in Persona-Assigned LLMs (Gupta et al., ICLR 2024) - https://arxiv.org/abs/2311.04892 - 2023/2024 - 24 datasets, 4 models, 19 personas; assigning a demographic persona degrades reasoning up to 70%+, mostly via abstention ("as a ..., I can't answer this").
20. How Is ChatGPT's Behavior Changing over Time? (Chen, Zaharia, Zou) - https://arxiv.org/abs/2307.09009 - Jul 2023 - GPT-4 March vs June 2023: prime identification 84% to 51%; June version less willing to answer opinion survey items; "same" service changes materially within months.
21. Examining Identity Drift in Conversations of LLM Agents (Choi, Hong, Kim, Kim, arXiv 2412.00804) - https://arxiv.org/abs/2412.00804 - Dec 2024, rev Feb 2025 - nine models; larger models drift more from an assigned persona over turns; assigning a persona does not by itself keep it stable.
22. Before You Poll with LLMs: A Deliberative Diagnostic Framework (Wali, Tayyab, arXiv 2609.15849) - https://arxiv.org/abs/2609.15849 - 14 Sep 2026 - tests whether personas update like humans given balanced information; all five models failed: reversal, 5 to 7x overshoot, rigidity, or "self-sycophancy" (conforming to their own stereotype).
23. Correcting Mode Collapse in Silicon Sampling with Semantic Similarity Rating (Heath, Alexander, arXiv 2607.28550) - https://arxiv.org/abs/2607.28550 - 30 Jul 2026 - asking for a number on a Likert scale collapses variance; asking for text and embedding it afterwards restores a realistic spread.
24. More Is Not More: What Matters for Diversity in LLM Opinions? (Yao, arXiv 2607.20429) - https://arxiv.org/abs/2607.20429 - 10 May 2026 - 7 models, 100 questions; the first persona conditioning step gives most of the diversity gain; more demographic detail can reduce it; raising temperature and "be diverse" instructions had negligible effect; separate architectures explore different opinion regions.
25. Verbalized Sampling (Zhang et al., arXiv 2510.01171) - https://arxiv.org/abs/2510.01171 - Oct 2025, rev Jul 2026 - mode collapse traced to typicality bias in preference data; asking for several answers with probabilities lifts diversity 1.6 to 2.1x with no retraining.
26. Challenging the Evaluator: LLM Sycophancy Under User Rebuttal (Kim, Khashabi, Findings of EMNLP 2025) - https://aclanthology.org/2025.findings-emnlp.1222.pdf - Nov 2025 - models cave to a user's counterargument framed as a follow-up, but judge the same two arguments correctly when shown side by side; casual pushback sways them more than formal critique.
27. Measuring Sycophancy of Language Models in Multi-turn Dialogues / SYCON Bench (Hong et al., arXiv 2505.23840) - https://arxiv.org/abs/2505.23840 - May 2025, rev Feb 2026 - 17 models; third-person framing cuts sycophancy up to 63.8%; alignment tuning increases it, reasoning and scale reduce it.
28. Too Nice to Tell the Truth (Shah, Mishra, Silpasuwanchai, arXiv 2604.10733) - https://arxiv.org/abs/2604.10733 - 12 Apr 2026 - 275 personas x 4,950 prompts on 13 models; persona agreeableness correlates with sycophancy in 9 of 13 models, r up to 0.87, d up to 2.33.
29. Intersectional Sycophancy (Maltbie, Raval, arXiv 2604.11609) - https://arxiv.org/abs/2604.11609 - Apr 2026 - 768 conversations, 128 personas; false validation depends on combinations of perceived user traits; GPT-5-nano 2.96 vs Claude Haiku 4.5 1.74 on a 10-point scale.
30. Evaluating Sycophancy in Frontier Models Using Persona-Driven Challenge (medRxiv 10.64898/2026.05.17.26353406) - https://www.medrxiv.org/content/10.64898/2026.05.17.26353406v1.full - 20 May 2026 - 9,000 responses across Claude Opus 4.6, Sonnet 4.6, GPT-5.4, Grok 4.1, Gemini 3 Flash; 7.1% sycophantic overall, 1.7 to 19.3% by persona, 2.4 to 15.3% by model; vulnerable personas got more capitulation than authority figures.
31. Playing Devil's Advocate: Off-the-Shelf Persona Vectors Rival Targeted Steering for Sycophancy (Kelkar et al., arXiv 2605.21006) - https://arxiv.org/abs/2605.21006 - May 2026, rev 12 Sep 2026 - a generic "critical" role vector cut sycophancy logits about 68% (Gemma 2 27B) and 98% (Qwen 3 32B) relative to purpose-built steering; "conformist" vectors did little.
32. Mitigating Social Desirability Bias in Random Silicon Sampling (Chapala, Mironov, Deng, arXiv 2512.22725) - https://arxiv.org/abs/2512.22725 - 27 Dec 2025 - neutral third-person reformulation of the question worked best; "be sincere" and "think analytically" preambles increased uniformity and did not help.
33. Decoding LLM Personality Measurement: Forced-Choice vs. Likert (Li et al., Findings of ACL 2025) - https://aclanthology.org/2025.findings-acl.480/ - Jul 2025 - six models; forced choice separates models better, is less temperature-sensitive and less prone to social desirability than Likert.
34. Reliability without Validity (Norman, Rivera, Hughes, arXiv 2606.19544) - https://arxiv.org/abs/2606.19544 - 17 Jun 2026 - 21 judges, 541k judgments; a judge can have test-retest reliability above 0.95 and still carry severe position bias; same-provider judges share systematic bias.
35. The Voice of the Customer (Griffin, Hauser, Marketing Science 12(1)) - https://mitsloan.mit.edu/shared/ods/documents?PublicationDocumentID=5259 - 1993 - 30 interviews, 7 analysts; 20 interviews found over 90% of the needs 30 found; hypothesis: 20 to 30 interviews for 90 to 95% of needs, one-on-ones more cost-effective than focus groups, multiple team members should read raw transcripts.
36. How many qualitative interviews are enough? (Skimle summary of Guest, Bunce, Johnson 2006 and Hennink et al. 2017) - https://skimle.com/blog/how-many-interviews-qualitative-research - 2026 - 60 interviews: code saturation by interview 12, six interviews held about 80% of codes; Hennink: code saturation 9 to 17, meaning saturation 16 to 24. Original Field Methods page (snippet only, 403).
37. JTBD interviews: how many do I need? (Moesta, LinkedIn) - https://www.linkedin.com/posts/bobmoesta_jtbd-interviews-how-many-do-i-need-to-get-activity-7102689580667080704-JtOT - 2023 - "10 interviews is all you really need"; past ten "the intent gets lost" in words; commenters run 6 to 8 small, 10 to 12 large.
38. 10 Customer Interviews That Reveal Why People Really Buy (SaaS Club, Moesta) - https://saasclub.io/podcast/jobs-to-be-done-bob-moesta-423/ - 2025 - patterns emerge by interview 6 or 7; ten interviews surface 3 to 5 buying patterns covering roughly 90% of a market; interview the actual switch moment, four forces.
39. Make Your B2B Buyer Personas Rock: Tips from Adele Revella (Cascade Insights) - https://www.cascadeinsights.com/making-your-b2b-buyer-personas-rock-tips-from-adele-revella/ - 3 Dec 2015 - "we learn everything we're going to learn after about ten interviews around a particular buying decision"; include lost buyers; perceived barriers are one of the five insights; demographics-only personas are profiles, not personas.
40. Your CRM buyer data is bad. Just ask your buyers (Clozd) - https://www.clozd.com/blog/5-lies-your-crm-is-telling-you-about-your-buyers - 21 Apr 2023 - 1,000 closed-lost deals vs buyer interviews: CRM loss reason matched the buyer only 15% of the time; competitor tag wrong about 70%; 44% of recorded reasons were outcomes not reasons; buyers cite 4 to 5 factors.
41. 85% of your CRM loss reasons are wrong (Dent, Revenue Operations Alliance) - https://www.revenueoperationsalliance.com/85-of-your-crm-loss-reasons-are-wrong/ - 10 Aug 2026 - about 3,000 deals sampled from 50,000+ win-loss interviews; same 85% mismatch; reps guess because buyers do not tell them.
42. On Self-Selection Biases in Online Product Reviews (Hu, Pavlou, Zhang, MIS Quarterly 41(2)) - https://aisel.aisnet.org/misq/vol41/iss2/8/ - 2017 - acquisition bias plus under-reporting bias produce the J-shape; the mean rating is a biased estimator of quality; consumers cannot fully correct for it.
43. How to Find Your Message Using Review Mining (Copyhackers) - https://copyhackers.com/2014/10/amazon-review-mining/ - Oct 2014 - Beachway: 500+ Amazon reviews across six addiction memoirs; "Your Addiction Ends Here" vs "If you think you need rehab, you do": 400% more CTA clicks, 20%+ more form submits on the next page; tracking-table method.
44. Why You Only Need to Test with 5 Users (Nielsen, NN/G) - https://www.nngroup.com/articles/why-you-only-need-to-test-with-5-users/ - 18 Mar 2000 - N(1-(1-L)^n), L about 31%: 5 users find about 85% of problems; three rounds of five beat one of fifteen; distinct user groups need 3 to 4 each.
45. How Long Do Users Stay on Web Pages? (Nielsen, NN/G) - https://www.nngroup.com/articles/how-long-do-users-stay-on-web-pages/ - 11 Sep 2011 - 205,873 pages, 2 billion dwell times (Liu, White, Dumais): Weibull; 99% of pages show negative aging; first 10 seconds decide, leaving stays elevated to 20 to 30 seconds, then flattens.
46. Popup Survey 2025 Benchmark Report (Survicate) - https://survicate.com/reports/popup-survey-benchmarks/ - 13 Aug 2026 - 3,029 surveys, 349 companies; median response by trigger: event 11.7%, page load 10.3%, time delay 5.3%, scroll 4.1%, exit intent 3.8%; completion 75.6% once started; centre placement 13.7% vs 7.7% lower-right.
47. 2025 Survey Response Rate Benchmark (Survicate) - https://survicate.com/reports/survey-response-rate-benchmarks/ - 29 Jun 2026 - 4,332 surveys, 460 companies; median response 9.98%; 1 question 9.75%, 2 to 3 questions 15.97%, 7+ 6.87%; median completion 75.2% in 42 seconds; B2C 12.85% vs B2B 8.18%.
48. Voice of Customer for ecommerce (Contentsquare/Hotjar guide) - https://contentsquare.com/guides/contentsquare-for-ecommerce/voice-of-customer/ - Feb 2023, upd Nov 2025 - one question for pre-purchase interrupts; 3 to 5 post-purchase; ask "What's one thing that nearly stopped you from buying from us?" on the thank-you page. Hotjar original URL redirects here.
49. PersonaCite: VoC-Grounded Interviewable Agentic Synthetic AI Personas (Truss, arXiv 2601.22288) - https://arxiv.org/abs/2601.22288 - 29 Jan 2026 - persona retrieves real VoC artefacts each turn, constrains answers to them, abstains when evidence is missing, cites sources; 14 expert interviews; proposes Persona Provenance Cards.
50. How to Build Audience Personas for Modern Search (Backlinko) - https://backlinko.com/audience-personas - upd 26 Apr 2026 - start with one primary persona; template fields include triggers, top questions, language that resonates and repels, trust signals; no external evidence cited.
51. Synthetic Users: How Accurate Are They? (Articos, vendor) - https://www.articos.com/blog/synthetic-users - 2026 - vendor claims 86% recall vs Baymard/NN/G findings across 46 studies and "7.5x over a bare LLM" with no cited source; included only as an example of the claims to discount.
Snippet only, not opened: CXL "Message mining" and "Voice of customer" (403); Hewitt et al. 2024 r=0.85 experiment-prediction paper (wrong arXiv id fetched); reportgarden search-terms-as-VoC post.

## Findings

### 1. Where synthetic users reproduce reality and where they fail
- Grounding on a real person's own words is the single largest accuracy lever. Interview-grounded agents hit 85 to 86% of humans' own test-retest on the GSS and cut racial and ideological error gaps that demographics-only agents show (5, a). Twins built from 500 real answers reach 88% of test-retest (6, a). Survey-anchored agents beat demographics-only agents on older Europeans' retirement attitudes, where demographics-only agents showed central-tendency bias and never said "don't know" (18, b).
- Demographics-only personas are the failure case, not the baseline. A no-persona population query beat persona panels in 9 of 9 comparisons (9, b). Sarstedt's review: 24.9% of silicon-vs-human comparisons matched, 65.3% diverged (15, a). Verasight: 14.5 point mean error over 305 options with GPT-5.2, 23.4 on healthcare, usable only where attitudes track demographics, explicitly not consumer research (13, b). Pattern in MeasuringU's tally: 9 encouraging, 14 discouraging (2, b).
- Variance collapse is now quantified: about 2x compression, 10 to 30 point subgroup error (7, a); 48% of coefficients differ, 32% of those flip sign (4, a); 66 of 128 answer options never chosen by 500 simulated respondents (9, b). Mechanism: the model returns the modal answer (11, a) because preference tuning rewards typical text (25, a).
- Averages can be right while individuals are wrong. Twins reproduce mean effects and say little about who differs from the mean; behavioural fidelity is "neither necessary nor sufficient" for valid inference (8, b). Topline match "does not establish user simulation" (9, b). For /personas this means a panel can agree with a real conversion rate and still misidentify which buyer leaves and why.
- Caricature and misalignment: political and marginalised personas on ordinary topics are most caricatured (16, a). Age is specifically distorted: models "juvenilize age-taste associations" across OpenAI, Anthropic and DeepSeek (17, b). Verian names older, less educated, rural and offline people as under-represented in training data (14, c). Assigning a demographic persona also degrades the model's reasoning, up to 70%+, mostly by abstaining in character (19, a).
- Sycophancy is measured and persona-dependent. Frontier models capitulated 7.1% of the time on clinical facts, 1.7 to 19.3% by persona, and vulnerable personas got more capitulation than authorities (30, b). Agreeable persona traits predict sycophancy, r up to 0.87 (28, b). NN/G's synthetic users finished every course and praised the forums (1, b).
- Drift is real and documented twice: GPT-4 prime-number accuracy 84% to 51% March to June 2023, June version less willing to answer opinion items (20, b); identical ANES prompts mean-reverted April to July 2023 (4, a). Within a conversation, larger models drift further from an assigned persona over turns (21, b).
- Personas do not update like humans. Given balanced information, five models either reversed, overshot human-sized shifts 5 to 7x, froze, or conformed to their own stereotype (22, b). A persona that "changes its mind" after a fix is weak evidence the fix worked.
- Same-model agents are correlated draws. Same-provider judges share systematic bias and can be reliable (>0.95 test-retest) while biased (34, b). Diversity comes from combining architectures, not from more personas on one model (24, b).

### 2. Prompting that reduces sycophancy and restores variance
- Side-by-side evaluation beats sequential agreement. Models pick the better of two arguments correctly when shown together but cave when the same counterargument arrives as a follow-up; casual pushback sways them more than formal critique (26, a). Give each persona the page once and ask for a judgment; never argue with it in the same context.
- Third person and neutral reformulation. Third-person framing cut sycophancy up to 63.8% (27, a). Neutral third-person question wording reduced social-desirability concentration; "be sincere" and "think analytically" preambles made answers more uniform and did not help (32, b). Write "Would this buyer close the tab?" not "Would you close the tab?".
- Forced choice over scales. Forced choice was less temperature-sensitive and less prone to social desirability than Likert (33, a). Numeric Likert asks collapse variance; free text scored afterwards restores it (23, b). Ask STAY or LEAVE plus a quoted line, never "rate 1 to 10".
- A critical role is a cheap anti-sycophancy lever. A generic "critical" persona direction matched purpose-built steering, "conformist" did nothing (31, b). Low agreeableness in the persona description lowers sycophancy (28, b). Every persona file should carry a sceptical, time-poor disposition, not just the target's demographics.
- Verbalised alternatives raise diversity 1.6 to 2.1x with no retraining (25, a). Ask each persona for the three most likely reasons this buyer leaves with rough probabilities, then the one they act on.
- Temperature and "be diverse" instructions are near-useless for opinion diversity; first-step persona conditioning gives most of the gain, and extra demographic detail can reduce it (24, b). Do not pad persona files with trivia.
- Evidence-bounded personas: retrieve real VoC lines each turn, constrain to them, abstain when evidence is missing, cite (49, c). The persona file should carry verbatim quotes so the subagent can quote rather than invent.
- Persona instability grows with turns (21, b). One-shot, single-turn per persona, fresh context, no memory of previous rounds.

### 3. Building personas from real data
- Saturation numbers converge around a dozen well-targeted conversations. Griffin and Hauser: 20 interviews found over 90% of the needs 30 found; 20 to 30 for 90 to 95%; multiple team members should read the raw transcripts (35, a). Guest, Bunce, Johnson: code saturation by interview 12, about 80% of codes by 6 (36, b). Hennink: code saturation 9 to 17, meaning saturation 16 to 24 (36, b). Moesta: ten switch interviews, patterns by 6 or 7, 3 to 5 buying patterns cover roughly 90% of a market (37, 38, c). Revella: about ten per buying decision per segment, include lost buyers (39, c).
- For a local service business the equivalent of an interview is a recorded inbound call or a DM thread. Rule of thumb from the above: 12 to 20 calls per service line finds most needs; past 30 you are reading words not intent.
- CRM won/lost notes are the weakest source. Rep-entered loss reasons matched the buyer 15% of the time across 1,000 deals, competitor tags were wrong about 70%, 44% of "reasons" were outcomes (40, b); replicated on about 3,000 of 50,000+ interviews (41, b). Use CRM notes only for timestamps, ticket size and what was quoted; never for the objection.
- Reviews are J-shaped by acquisition bias and under-reporting bias, so the mean is a biased quality estimate and the population is buyers only (42, a). Reviews contain the words for the problem and the outcome; they contain zero non-buyers and no objections. Mine them for phrases, weight them at zero for persona mix.
- Review mining still moves numbers: 500+ Amazon reviews across six memoirs produced "If you think you need rehab, you do", 400% more CTA clicks and 20%+ more form submits (43, c, single test, 2014).
- Google Ads search terms: no study found; treat as (c). Their value is population coverage: they include the people who never called. Use them for urgency, device and job language, not for demographics.
- Interview at the switch moment, not in general: the four forces (push, pull, anxiety, habit) are what the landing page must answer (38, c). Revella's "perceived barriers" is the same field (39, c).

### 4. How many personas, weighting, and what a roleplayable file holds
- Three to five is what the data supports, not a convention: ten switch interviews yield 3 to 5 decision patterns covering about 90% of a market (38, c). Nielsen: distinct user groups need 3 to 4 test users each, so five personas x three real humans is the human-test analogue (44, a).
- One primary persona first (50, c; 39, c). Weight by share of revenue in the last 12 months of won jobs, not by call volume; the primary is the one whose LEAVE verdict blocks shipping.
- Demographics alone do not carry a persona; real answers do (5, a; 18, b; 9, b). The file must hold verbatim lines from calls, DMs and search terms, because grounding on self-report is where accuracy comes from and extra demographic detail can lower diversity (24, b).
- Age and device belong in the file because the model is documented to juvenilise older buyers (17, b) and the average US homeowner is about 55 (snippet only). State the age and force the subagent to reason from the persona's quotes, not from the number.
- Dwell-time evidence sets the time budget: the leave hazard is highest in the first 10 seconds and elevated to 20 to 30 seconds (45, a). The persona must react to above-the-fold first, before reading the rest.
- Disposition fields (sceptical, time-poor, one tab, low agreeableness) are not colour; they are the documented anti-sycophancy control (28, b; 31, b).

### 5. Stop rules and calibration
- Aggregate agreement is not evidence of individual accuracy (8, b; 9, b). A panel converging on "STAY" is the sycophantic default and the mode-collapse default; treat it as null.
- Human calibration is the only published fix that works: 50 to 300 human observations plus a calibrated estimator removed 83 to 94% of bias (7, a); heuristic prompting is for exploration, confirmatory claims need auxiliary human data (10, b). For /personas the calibration set is the log of predictions vs outcomes plus three real humans.
- Persona belief updates are unreliable (22, b), so "the persona now says STAY after the fix" is not confirmation. Confirmation is a new external signal: the objection disappears from the next 10 calls, the exit-survey answer changes, or a real human passes the task.
- Prompt sensitivity is documented (14, c; 15, a): the loop must hold the persona prompt fixed across rounds or the "improvement" may be prompt drift.
- Same-model agents share error (34, b; 24, b). Two personas agreeing is one signal. Log the model id and date on every run because behaviour changed inside three months twice (20, b; 4, a).
- Ship-it rule follows from negative aging (45, a): once no persona leaves in the first 10 seconds for a reason the page controls, remaining leaves are price, area, availability, or taste, and the loop is done.

### 6. Real-human checks that pair with the panel
- Five real users find about 85% of usability problems; three rounds of five beat one round of fifteen; 3 to 4 per distinct group (44, a). Three humans per primary persona, one round per loop, is the minimum that means anything.
- Thank-you page one-question survey: ask "What's one thing that nearly stopped you from buying from us?" (48, c). Response benchmarks: 1 question 9.75% median, 2 to 3 questions 15.97%, 7+ 6.87%; median completion 75% in 42 seconds; B2C 12.85% (47, b). Post-conversion placement is not separately benchmarked; expect the event-triggered figure, 11.7% (46, b).
- Exit-intent surveys have the lowest response of any trigger, 3.8% median, though 74 to 76% of starters finish (46, b). At 500 visits a month that is about 19 answers; enough for objection language, not for rates.
- Centre placement roughly doubles response, 13.7% vs 7.7% (46, b).
- Recorded calls remain the richest source and the one the persona panel is calibrated against (35, a; 40, b).

### 7. Copy mining results
- The one hard number: "If you think you need rehab, you do" beat "Your Addiction Ends Here" by 400% on CTA clicks and 20%+ on next-page form submits, from 500+ mined reviews (43, c). Single test, 2014, lead-gen, no sample size published.
- Method that produced it: pick the outcome the buyer wants, find where they wrote about it unprompted, log quotes in a table with source and theme, pick the line with the highest frequency and the most specific claim (43, c).
- Copy that names who it is for and the end result lifted course conversions 9.2% (CXL, snippet only, c).
- Why customer language works is consistent with the dwell data: the reader decides in under 10 seconds and a sentence they would have said themselves is recognised, not parsed (45, a).
- Mining order for a local service business, by evidence quality: recorded calls and DMs (interviews, 35, a), search terms (non-buyers, c), reviews (buyers only, phrases only, 42, a), CRM notes (timestamps only, 40, b), industry articles (no first-person language, exclude).

## Claims that did not survive
- "Synthetic users reach 85 to 92% parity with humans." Vendor self-reports (51) and a Stanford figure lifted out of context; the 85% is agents grounded on two-hour interviews with the real person, not prompted avatars (5). Demographics-only panels lost to a no-persona query 9 of 9 times (9).
- "Turn up temperature to get diverse personas." Negligible effect on opinion diversity (24); Likert numeric asks collapse regardless (23). Structure of the ask matters, temperature does not.
- "Add more detail to the persona and it gets more realistic." Extra demographic elaboration can reduce diversity (24) and demographic personas degrade reasoning (19). Real quotes add realism; trivia does not.
- "Tell the persona to be honest and critical" as a preamble. Sincerity and analytical preambles increased uniformity and did not reduce bias (32). What works is third person, side-by-side evaluation, forced choice and a low-agreeableness disposition (26, 27, 31, 33).
- "Two personas hitting the same blocker is independent confirmation." Same-model draws share bias (34, 24). Already in Part 3; now sourced.
- "The persona changed its verdict after the fix, so the fix worked." Persona belief updating is unreliable in all five models tested (22).
- "Ask the persona to rate the page 1 to 10." Likert answers collapse to the mode and are temperature-sensitive (23, 33).
- "CRM lost reasons tell you the objection." 85% wrong (40, 41).
- The Part 3 claim that misalignment is "worst for adults 65 plus and widowed people." Not re-sourced in this pass. What survived: models juvenilise age associations (17), under-represent older and offline people (14), and demographics-only agents flatten older adults' answers (18). Keep the conclusion, soften the wording.
- The Part 3 figures "76% main effects" and "r = 0.85 directional forecasting." Not re-sourced; the Hewitt paper fetch returned the wrong paper. Drop the numbers until re-opened.
- "Rehab headline lifted leads 400%." The 400% is CTA clicks; form submits rose 20%+ (43).

## The persona file shape
One markdown file per persona, under 60 lines. Every field one line unless marked. Fields with no real-data source are left blank, not invented.
- `name_and_label`: first name plus the job in four words ("Burst-pipe Brenda, emergency plumbing"). Why: the label is the decision pattern, the name is for the log.
- `share_of_revenue_12m`: percent of won revenue this pattern represents, with the count of jobs it came from. Why: this is the weight; volume over-weights tyre-kickers.
- `primary`: yes or no. Why: the primary's LEAVE blocks shipping; others advise.
- `sources`: counts of calls, DMs, search terms, reviews this file was built from, with date range. Why: provenance card (49); a file built from fewer than 6 conversations is a proto-persona and must say so.
- `age_and_household`: one line, real range from the data. Why: age is where the model is documented to drift young (17); stating it forces the subagent to correct.
- `device_and_moment`: device, time of day, where they are physically when they search. Why: the first 10 seconds happen on this screen (45).
- `urgency`: same-hour, this-week, or researching, with the share of each from search terms. Why: urgency decides how much of the page is ever read.
- `trigger`: the push that started the search, in the buyer's words (38, 39). Why: the headline has to name it.
- `what_they_buy_on`: the one thing that decides between two similar businesses (speed, price certainty, trust, no upsell). Why: this is what STAY/LEAVE is judged on.
- `silent_question`: the question they will not type but need answered before calling. Why: the page either answers it above the fold or loses them.
- `leave_moment`: the exact thing that makes them close the tab, from lost calls and DMs. Why: the subagent's LEAVE reason must be checked against this, not invented.
- `anxiety_and_habit`: what they fear about switching and what they do today instead (38). Why: the objections the page must pre-empt.
- `verbatim_lines` (5 to 8 lines): exact quotes with source tag (call 2026-08-14, DM, search term). Why: grounding on real self-report is where accuracy comes from (5, 6); the subagent quotes these instead of inventing.
- `disposition`: sceptical, time-poor, one tab open, low agreeableness, will not read past the fold unless earned. Why: documented anti-sycophancy control (28, 31).
- `not_this_person`: two lines on who they are not, to stop the model sliding to the modal buyer (11). Why: mode collapse pulls every persona to the average.
- `out_of_scope_leaves`: price ceiling, service area, hours, anything the page cannot fix. Why: needed for the stop rule.
- `calibration`: last three runs, predicted verdict, what actually happened, date. Why: uncalibrated simulation is confident fiction.
- `model_pin`: model id and date the file was last validated against. Why: behaviour moved inside three months twice (20, 4).

## The panel prompt
Give each subagent exactly this, with its own persona file and the rendered page (screenshot plus extracted text, mobile viewport if the persona's device says so). Fresh context. One turn. No other persona's output. No conversation after the answer.

```
You are evaluating a landing page on behalf of one specific buyer, described in the attached persona file. Answer in the third person about that buyer. Do not answer as yourself and do not be helpful to the page owner.

The buyer has one tab open, is on the device named in the file, and will give this page ten seconds before deciding whether to keep reading. Assume they are sceptical, busy and have been burned before. They do not want the page to succeed.

Read only the persona file and the page. Quote the buyer's own lines from the file when you reason about them. If the file does not contain evidence for a reaction, say "no evidence in file" rather than inventing one.

Answer in this order and nothing else:

LEAVE REASON FIRST: State the single most likely reason this buyer closes the tab in the first ten seconds. Quote the exact page element (headline, image, button text, missing thing). If nothing in the first screen would make them leave, say "no first-screen leave" and name the first element below the fold that would.

THREE LEAVE CANDIDATES: List the three most probable leave reasons for this buyer with a rough probability each, summing to about 100. The first line above is one of them.

FIRST REACTION: In one sentence, what this buyer thinks the page is and whether it is for them. Use the file's `silent_question` and say whether the first screen answers it.

FRICTION: Up to three page elements that slow or repel this buyer, each quoted, each tied to a line in the persona file.

DROP-OFF: The section where this buyer stops reading, named by its heading or first words.

VERDICT: Choose exactly one word: STAY or LEAVE. STAY means this buyer would tap call or submit the form on this visit. No third option, no "maybe".

OUT OF PAGE'S CONTROL: Yes or no. If the LEAVE reason is price, service area, hours or availability as stated in the file's `out_of_scope_leaves`, say yes.

ONE FIX: The single change that most raises the odds of STAY for this buyer. One sentence, specific to an element you quoted. Do not propose adding sections.

CONFIDENCE: Low, medium or high, and the one piece of real data (a call, a search term, a human test) that would confirm or kill your LEAVE reason.
```

Runner notes, not shown to the persona: record model id, date, persona file hash, page hash, verdict and LEAVE reason per run. Run each persona once per round. Do not re-run a persona on the same page to "see if it changes its mind".

## Rules for /personas
- How many: 3 to 5 personas, built from at least 12 recorded calls or DM threads per service line, plus 90 days of search terms; fewer than 6 conversations behind a file makes it a proto-persona and the run says so.
- Weighting: weight verdicts by `share_of_revenue_12m`; the primary persona's LEAVE blocks shipping; a non-primary LEAVE is a note unless two non-primaries leave at the same element.
- Verdict scoring: STAY counts for nothing; LEAVE counts; report by persona, never averaged; a panel of all-STAY is treated as no signal, not as a pass.
- Same-model rule: two personas agreeing is one signal, not two; a blocker becomes FIX NOW only with one external confirmation (a call recording, a search term, an exit-survey answer, or one of three real humans).
- Stop rule: stop when every remaining LEAVE reason is marked out of the page's control, or when a round's fixes changed no verdict and the external check agrees; never stop on "the persona now says STAY".
- Round cap: three rounds per page version; after three, ship and hand the open LEAVE reason to the human test.
- Human pairing: three real people per primary persona, mobile, ten-second first-impression task then the call task, one round per loop; thank-you page one-question survey "What nearly stopped you?" runs continuously.
- Prompt and model pinning: the panel prompt and persona files are frozen for the life of a loop; changing either starts a new loop; model id and date logged on every run.
- Logging: every run appends date, model, page hash, persona, verdict, LEAVE reason, fix applied, and later the outcome (calls per 100 visits before and after, the survey answers); personas are edited only on a pattern across three or more loops, never on one run.
- Sources ranking for persona building: recorded calls and DMs first, search terms second, reviews for phrases only, CRM notes for timestamps and ticket size only, industry articles never.
- Label every output: "panel simulation", not "customer research"; never write "customers will" from a panel result.
