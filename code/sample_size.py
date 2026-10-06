"""How many LEADS a split test needs, and the maths /analytics reads results with. No scipy needed.

    python3 code/sample_size.py                                   # the table: baselines 5 / 7.5 / 10 %, lifts 20 / 30 / 50 %
    python3 code/sample_size.py --baseline 0.075 --lift 0.2       # one answer
    python3 code/sample_size.py --baseline 0.075 --lift 0.2 --leads-per-month 60   # ...and how many months

⛔ THE BAR (Jono, 3 October 2026): call it at an 80% chance to win, Bayesian - "one in five odds of failure,
four in five odds of success." Not 95%: a small business waiting six months for certainty never ships
anything. Planning uses the same bar with 80% power: leads per variant is about 6 / lift^2 for small
baselines. +30% lift needs ~70 leads a side, +50% ~26. Test a whole-page change so the lift is big.

Importable: leads_per_variant(), chance_to_win(), z_test(), srm_p(), normal_cdf().
"""
import math
import sys

WIN_BAR = 0.80      # call it at an 80% chance to win
Z_ALPHA = 0.841621  # the same bar, as a one-sided z: 80% sure
Z_BETA = 0.841621   # 80% power


def normal_cdf(z):
    return 0.5 * (1 + math.erf(z / math.sqrt(2)))


def visitors_per_variant(p, lift, z_a=Z_ALPHA, z_b=Z_BETA):
    """Classic two-proportion sample size per arm. p = baseline conversion rate, lift = relative (0.2 = +20%)."""
    p2 = p * (1 + lift)
    pbar = (p + p2) / 2
    num = (z_a * math.sqrt(2 * pbar * (1 - pbar)) + z_b * math.sqrt(p * (1 - p) + p2 * (1 - p2))) ** 2
    return num / (p2 - p) ** 2


def leads_per_variant(p, lift):
    return visitors_per_variant(p, lift) * p


def z_test(conv_a, n_a, conv_b, n_b):
    """Two-proportion z test. Returns (lift, z, p_two_sided, prob_b_better)."""
    if not n_a or not n_b:
        return 0.0, 0.0, 1.0, 0.5
    pa, pb = conv_a / n_a, conv_b / n_b
    pooled = (conv_a + conv_b) / (n_a + n_b)
    se = math.sqrt(pooled * (1 - pooled) * (1 / n_a + 1 / n_b)) or 1e-9
    z = (pb - pa) / se
    p = 2 * (1 - normal_cdf(abs(z)))
    lift = (pb - pa) / pa if pa else 0.0
    return lift, z, p, normal_cdf(z)


def chance_to_win(conv_a, n_a, conv_b, n_b, draws=40000, seed=7):
    """The Bayesian chance that B beats A: a flat Beta(1, 1) prior on each conversion rate, the posterior
    sampled. The same question PostHog's experiment page answers. Seeded, so a read never wobbles."""
    import random
    if not n_a or not n_b:
        return 0.5
    r = random.Random(seed)
    wins = sum(r.betavariate(1 + conv_b, 1 + n_b - conv_b) > r.betavariate(1 + conv_a, 1 + n_a - conv_a) for _ in range(draws))
    return wins / draws


def srm_p(n_a, n_b, expected_share=0.5):
    """Sample ratio mismatch: chi-square with 1 degree of freedom against the expected split."""
    n = n_a + n_b
    if not n:
        return 1.0
    ea, eb = n * expected_share, n * (1 - expected_share)
    chi = (n_a - ea) ** 2 / ea + (n_b - eb) ** 2 / eb
    return math.erfc(math.sqrt(chi / 2))


def z_for(p):
    """The z value at probability p, by bisection. Good to about 1e-6, and it saves a scipy dependency."""
    lo, hi = 0.0, 10.0
    for _ in range(200):
        mid = (lo + hi) / 2
        if normal_cdf(mid) < p:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


def arms_cost(p, lift, arms, power=0.80):
    """What a test with more than two arms costs. Every extra challenger is another comparison
    against the control, so alpha is split (Bonferroni) and each arm needs MORE leads, not fewer -
    while the traffic is divided between more arms. Both effects push the same way.
    Returns (leads per arm, leads in total)."""
    k = max(1, arms - 1)
    za, zb = z_for(1 - (1 - WIN_BAR) / k), z_for(power)
    per = visitors_per_variant(p, lift, z_a=za, z_b=zb) * p
    return per, per * arms


def months(leads_needed_per_variant, leads_per_month):
    return 2 * leads_needed_per_variant / leads_per_month if leads_per_month else float("inf")


def table():
    print("Leads needed PER VARIANT, to call it at an 80% chance to win (80% power)\n")
    for p in (0.05, 0.075, 0.10):
        print(f"Baseline {p*100:.1f}% conversion")
        for lift in (0.10, 0.20, 0.30, 0.50):
            print(f"- +{int(lift*100)}% lift · {leads_per_variant(p, lift):,.0f} leads a side · {visitors_per_variant(p, lift):,.0f} visitors a side")
        print()
    print("Every extra arm, at a 7.5% baseline and a +30% target:")
    for arms in (2, 3, 4, 5):
        per, tot = arms_cost(0.075, 0.30, arms)
        print(f"- {arms} arms · {per:,.0f} leads an arm · {tot:,.0f} in total · {tot / 60:.0f} months at 60 leads a month")
    print("Two arms is the only shape most pages can afford. Generate several candidate pages, ship ONE as the challenger.\n")
    print("Rule of thumb: about 6 / lift^2 leads a side. Under ~30 leads a side the read takes months - test a whole-page change so the lift is big enough to see sooner.")


if __name__ == "__main__":
    a = sys.argv[1:]
    def arg(f, d=None):
        return float(a[a.index(f) + 1]) if f in a else d
    p, lift, lpm = arg("--baseline"), arg("--lift"), arg("--leads-per-month")
    if p is None or lift is None:
        table(); sys.exit()
    need = leads_per_variant(p, lift)
    print(f"Baseline {p*100:.1f}% · to see a +{lift*100:.0f}% lift: {need:,.0f} leads a side ({visitors_per_variant(p, lift):,.0f} visitors a side)")
    if lpm:
        m = months(need, lpm)
        print(f"At {lpm:.0f} leads a month across both pages that is about {m:.1f} months." +
              ("  That is too long - test a bigger change, or pool the same variant across more pages." if m > 3 else ""))
