"""Buying motivations and the phrases that reveal them on a landing page.

Researched 25 September 2026 from 12 sources: Maslow, Sheth-Newman-Gross, Jobs To Be Done,
Fogg, Cialdini, prospect theory, self-determination theory, Schwartz values, Bain/HBR's 30
Elements of Value and the B2B 40, Google/CEB's emotion research, plus the copy canon
(Whitman's LF8, Edwards' ten reasons, Schwartz, Collier, Hopkins, Sugarman).

Jono's original eight were: time, money, freedom, pain aversion, status, legacy, fun, ease.
What the research changed: risk reduction is a separate motivation and the biggest one for a
trade (it is what every review, licence number and guarantee is actually selling); certainty
splits from pain aversion; saving money splits from making money (a homeowner never makes
money); ease became save-effort; status became look-good. Legacy and fun found no support as
purchase drivers for these business models and were dropped.

Nine motivations, consolidated from 12 opened sources (academic frameworks, the
direct-response canon, and B2B/B2C purchase-driver research). Each entry:

    label    - plain business-owner name
    trigger  - lowercase substrings to match against visible page copy
    weight   - how much this motivation matters for each business model,
               0.0 (irrelevant) to 1.0 (dominant)
"""

MOTIVATIONS = {
    "make_money": {
        "label": "Make me money",
        "triggers": [
            "more leads", "more customers", "grow your revenue", "return on ad spend",
            "book more jobs", "roi", "pays for itself", "double your",
        ],
        "weight": {"trade": 0.1, "professional": 0.2, "agency": 1.0, "saas": 0.8},
    },
    "save_money": {
        "label": "Save me money",
        "triggers": [
            "save you money", "cheaper than", "no hidden fees", "flat fee",
            "free quote", "starting from", "cut your costs", "lower your bill",
        ],
        "weight": {"trade": 0.8, "professional": 0.7, "agency": 0.5, "saas": 0.6},
    },
    "save_time": {
        "label": "Save me time",
        "triggers": [
            "same day", "within 24 hours", "in minutes", "we answer in",
            "fast turnaround", "no waiting", "one visit", "get started today",
        ],
        "weight": {"trade": 0.9, "professional": 0.7, "agency": 0.7, "saas": 0.8},
    },
    "save_effort": {
        "label": "Save me effort",
        "triggers": [
            "we handle everything", "done for you", "we do the heavy lifting",
            "no paperwork", "we take care of", "one less thing", "leave it to us",
        ],
        "weight": {"trade": 0.8, "professional": 0.8, "agency": 0.9, "saas": 0.7},
    },
    "reduce_risk": {
        "label": "Make it safe to say yes",
        "triggers": [
            "licensed and insured", "guarantee", "money back", "no risk",
            "fully insured", "background checked", "warranty", "certified",
            "reviews", "rated", "trusted by", "years in business",
        ],
        "weight": {"trade": 1.0, "professional": 1.0, "agency": 0.9, "saas": 0.8},
    },
    "certainty": {
        "label": "Tell me exactly what happens",
        "triggers": [
            "here's what happens next", "upfront pricing", "no surprises",
            "we'll call you within", "step 1", "what to expect",
            "fixed price", "we'll text you when",
        ],
        "weight": {"trade": 0.9, "professional": 0.9, "agency": 0.8, "saas": 0.7},
    },
    "stop_the_pain": {
        "label": "Stop the pain I'm in now",
        "triggers": [
            "sick of", "tired of", "stop worrying about", "emergency",
            "fix it fast", "no more", "frustrated with", "finally",
        ],
        "weight": {"trade": 1.0, "professional": 0.9, "agency": 0.8, "saas": 0.7},
    },
    "freedom_control": {
        "label": "Give me my life back",
        "triggers": [
            "without lifting a finger", "hands off", "never think about it again",
            "get your weekends back", "off your plate", "while you sleep",
            "you stay in control", "cancel anytime",
        ],
        "weight": {"trade": 0.5, "professional": 0.5, "agency": 0.9, "saas": 0.9},
    },
    "look_good": {
        "label": "Make me look good",
        "triggers": [
            "be the envy of", "neighbours will ask", "impress your",
            "look like a hero", "report your boss will love",
            "award winning", "premium", "best in",
        ],
        "weight": {"trade": 0.5, "professional": 0.4, "agency": 0.8, "saas": 0.5},
    },
}
