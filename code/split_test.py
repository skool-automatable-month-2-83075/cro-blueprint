"""The PostHog side of a split test: the flag, the experiment, the read, the stop.

    python3 code/split_test.py --create drain-cleaning                # flag lp-drain-cleaning (control/test 50/50) + experiment, goal = leads
    python3 code/split_test.py --create drain-cleaning --aa           # an A/A test: same flag shape, name says A/A, both variants show the same page
    python3 code/split_test.py --status drain-cleaning                # visitors and leads per variant, the maths, the call
    python3 code/split_test.py --status drain-cleaning --lift 0.3     # judge against a +30% target instead of +20%
    python3 code/split_test.py --stop drain-cleaning --winner test    # end the experiment and send 100% to the winner
    python3 code/split_test.py --list

The code side (moving page.tsx into VariantA.tsx, building VariantB.tsx) is done by the /split-test command
from website/app/lp/_split-template. This script never touches website/.

Leads = lead_form_submitted + text_clicked + the calls, one per person per variant. Exposure = $feature_flag_called.
The calls are the REAL ones (lead_call, from GoHighLevel through /api/call, its arm read from CALL_NUMBER_MAP) when the
page has a number per arm; only without those do the call-button taps (call_clicked) stand in. Never both: most real
callers tapped first, and counting the tap and the call would count one person twice.
PostHog's own experiment page cannot see the real calls - the caller is a different person to it than the visitor -
so this read is the one the call is made on.
Every event posthog-js sends carries $feature/<flag> once the flag is bootstrapped, which is how leads know their variant.
"""
TIME_BOX_DAYS = 56   # a test runs 8 weeks at most, then it is a tie (Jono, 3 October 2026: weeks, not six months)
import argparse
import sys
from datetime import datetime, timezone

import _posthog as ph
import sample_size as ss

LEADS = ["lead_form_submitted", "call_clicked", "text_clicked"]


def flag_key(slug):
    return slug if slug.startswith("lp-") else f"lp-{slug}"


def find_flag(key):
    out = ph.get("feature_flags/", search=key)
    for f in out.get("results", []):
        if f.get("key") == key:
            return f
    return None


def find_experiment(key):
    out = ph.get("experiments/", limit=200)
    for e in out.get("results", []):
        if e.get("feature_flag_key") == key or (e.get("feature_flag") or {}).get("key") == key:
            return e
    return None


def lead_action():
    """One PostHog action that means 'a lead': any of the three events. Steps in an action are OR'd."""
    out = ph.get("actions/", limit=200)
    for a in out.get("results", []):
        if a.get("name") == "Lead (form, call or text)":
            return a["id"]
    st, a = ph.call("POST", "actions/", {"name": "Lead (form, call or text)", "description": "Made by /split-test. Any one of these is a lead.",
                                          "steps": [{"event": e} for e in LEADS]}, soft=True)
    if st in (200, 201):
        return a["id"]
    print(f"Could not create the Lead action ({st}) - the experiment goal falls back to the form event only.")
    return None


def create(slug, aa=False, lift=0.3):
    key = flag_key(slug)
    name = f"{'A/A check' if aa else 'Split test'} · {slug}"
    flag = find_flag(key)
    variants = [{"key": "control", "name": "Control - the page you have", "rollout_percentage": 50},
                {"key": "test", "name": "Test - the challenger", "rollout_percentage": 50}]
    if not flag:
        flag = ph.post("feature_flags/", {
            "key": key, "name": name, "active": True,
            # continuity off on purpose: it breaks bootstrapping and local evaluation, and stickiness
            # already comes from hashing the visitor id the middleware set
            "ensure_experience_continuity": False, "bucketing_identifier": "distinct_id",
            "filters": {"groups": [{"properties": [], "rollout_percentage": 100, "variant": None}],
                        "multivariate": {"variants": variants}, "payloads": {}},
            "tags": ["cro-blueprint", "split-test"],
        })
        print(f"Flag created: {key} · {ph.ui('feature_flags/' + str(flag['id']))}")
    else:
        print(f"Flag exists: {key} · {ph.ui('feature_flags/' + str(flag['id']))}")

    exp = find_experiment(key)
    if exp:
        print(f"Experiment exists: {ph.ui('experiments/' + str(exp['id']))}")
        return
    action_id = lead_action()
    body = {
        "name": name,
        "description": "Two pages at one URL. Goal: a lead - form submitted, phone tapped or text tapped. Read with code/split_test.py --status.",
        "type": "web",
        "feature_flag_key": key,
        "parameters": {"minimum_detectable_effect": int(round(lift * 100)), "variant_notes": {"control": "the page as it is", "test": "the challenger, see context/test-log.md"}},
        "exposure_criteria": {"filterTestAccounts": True, "multiple_variant_handling": "exclude"},
        "metrics": [{
            "kind": "ExperimentMetric", "metric_type": "funnel", "name": "Lead (form, call or text)", "goal": "increase",
            "funnel_order_type": "ordered", "conversion_window": 7, "conversion_window_unit": "day",
            "series": [{"kind": "ActionsNode", "id": action_id}] if action_id else [{"kind": "EventsNode", "event": "lead_form_submitted"}],
        }],
        "metrics_secondary": [
            {"kind": "ExperimentMetric", "metric_type": "funnel", "name": "Form submitted", "goal": "increase",
             "series": [{"kind": "EventsNode", "event": "lead_form_submitted"}]},
            {"kind": "ExperimentMetric", "metric_type": "funnel", "name": "Phone tapped", "goal": "increase",
             "series": [{"kind": "EventsNode", "event": "call_clicked"}]},
        ],
        "allow_unknown_events": True,
    }
    status, out = ph.call("POST", "experiments/", body, soft=True)
    if status in (200, 201):
        print(f"Experiment created (draft): {ph.ui('experiments/' + str(out['id']))}")
        st, _ = ph.call("POST", f"experiments/{out['id']}/launch/", {}, soft=True)
        if st not in (200, 201):
            st, _ = ph.call("PATCH", f"experiments/{out['id']}/", {"start_date": datetime.now(timezone.utc).isoformat()}, soft=True)
        print("Launched." if st in (200, 201) else "Could not launch it from here - press Launch in PostHog (one click).")
        return
    # PostHog's experiment schema moves. Fall back to the minimum it has always accepted.
    status2, out2 = ph.call("POST", "experiments/", {"name": name, "feature_flag_key": key,
                                                     "parameters": {"feature_flag_variants": variants}}, soft=True)
    if status2 in (200, 201):
        print(f"Experiment created without a goal (PostHog rejected the metric shape: {str(out)[:160]}).")
        print(f"Add the goal in one click - Experiments > {name} > Primary metric > funnel $pageview -> lead_form_submitted: {ph.ui('experiments/' + str(out2['id']))}")
        return
    print(f"Could not create the experiment ({status2}: {str(out2)[:200]}). The flag works on its own; --status reads the split without it.")


def status(slug, lift=0.2):
    key = flag_key(slug)
    q = f"""
    select properties.$feature_flag_response as variant, count(distinct person_id) as visitors
    from events where event = '$feature_flag_called' and properties.$feature_flag = {ph.sql_str(key)}
      and timestamp > now() - interval 90 day group by variant"""
    cols, rows = ph.hogql(q, "exposures")
    visitors = {r[0]: r[1] for r in rows}
    prop = f"properties.`$feature/{key}`"
    # The real calls when the page has a number per arm, the taps only when it does not (see the header).
    # The setup's test call counts here (it proves the numbers are wired); 555-01xx callers never count as leads.
    _, real = ph.hogql(f"""select count() from events where event = 'lead_call' and {prop} is not null
      and timestamp > now() - interval 90 day""", "real calls")
    call_event = "lead_call" if real and real[0][0] else "call_clicked"
    events = ["lead_form_submitted", "text_clicked", call_event]
    q2 = f"""
    select {prop} as variant, count(distinct person_id) as leads,
      countIf(event = 'lead_form_submitted') as forms, countIf(event = {ph.sql_str(call_event)}) as calls, countIf(event = 'text_clicked') as texts
    from events where event in ({', '.join(ph.sql_str(e) for e in events)}) and {prop} is not null
      and coalesce(toString(properties.test_lead), '') != 'true'
      and distinct_id not like 'caller:%55501__'
      and timestamp > now() - interval 90 day group by variant"""
    cols2, rows2 = ph.hogql(q2, "leads")
    leads = {r[0]: {"leads": r[1], "forms": r[2], "calls": r[3], "texts": r[4]} for r in rows2}

    na, nb = visitors.get("control", 0), visitors.get("test", 0)
    ca, cb = leads.get("control", {}).get("leads", 0), leads.get("test", {}).get("leads", 0)
    print(f"# {key}\n")
    for v, n, c in (("control", na, ca), ("test", nb, cb)):
        d = leads.get(v, {})
        rate = 100 * c / n if n else 0
        print(f"- {v} · {n:,} visitors · {c} leads · {rate:.1f}% · forms {d.get('forms', 0)} · calls {d.get('calls', 0)}"
              + (" (real calls)" if call_event == "lead_call" else " (call-button taps: no number per arm yet)"))
    if not na or not nb:
        print("\nNot enough exposure yet to say anything. Check the flag is bootstrapped (visit the page, then look for $feature_flag_called).")
        return
    srm = ss.srm_p(na, nb)
    obs_lift, z, p, _ = ss.z_test(ca, na, cb, nb)
    prob_b = ss.chance_to_win(ca, na, cb, nb)   # Bayesian, the bar the call uses
    base = ca / na if na else 0.05
    need = ss.leads_per_variant(base or 0.05, lift)
    haircut = obs_lift * 0.87   # winner's curse: a declared lift is inflated; plan on 13% less (Kohavi)
    exp = find_experiment(key)
    started = exp.get("start_date") if exp else None
    days = None
    if started:
        try:
            days = (datetime.now(timezone.utc) - datetime.fromisoformat(started.replace("Z", "+00:00"))).days
        except ValueError:
            days = None
    ph_read = ""
    if exp:
        for mr in (exp.get("metrics_results") or exp.get("metrics_result") or []):
            for v in (mr.get("variant_results") or mr.get("variants") or []):
                if isinstance(v, dict) and "chance_to_win" in v:
                    ph_read += f"\n- PostHog says: {v.get('key')} chance to win {float(v['chance_to_win']) * 100:.0f}% · significant {v.get('significant')}"
    print(f"\n- Split check: {100 * na / (na + nb):.1f}% / {100 * nb / (na + nb):.1f}%" + ("  ⛔ BROKEN SPLIT (p<0.01) - stop, do not read the result" if srm < 0.01 else "  ok"))
    print(f"- Observed: test is {obs_lift * 100:+.0f}% vs control · chance the test wins {prob_b * 100:.0f}% (the call is at {ss.WIN_BAR * 100:.0f}%)")
    print(f"- After the winner's-curse haircut: plan on {haircut * 100:+.0f}%, not {obs_lift * 100:+.0f}%")
    print(f"- Needed for a +{lift * 100:.0f}% read: about {need:,.0f} leads a side · have {min(ca, cb)}" + (f" · running {days} days" if days is not None else "") + ph_read)
    if srm < 0.01:
        call = "BROKEN SPLIT - fix before reading"
    elif min(na, nb) < 50 or min(ca, cb) < 5:
        call = "KEEP GOING - PostHog's own floor is 50 visitors and 5 leads a side before any number means anything"
    elif days is not None and days < 14:
        call = f"KEEP GOING - {14 - days} more days, two full weeks minimum so weekdays and weekends both count"
    # ⛔ THE CALL (Jono, 3 October 2026): an 80% chance to win, Bayesian. Four in five called winners are right.
    elif prob_b >= ss.WIN_BAR:
        call = f"SHIP - the test has a {prob_b * 100:.0f}% chance to win"
    elif prob_b <= 1 - ss.WIN_BAR:
        call = f"KILL - the control has a {(1 - prob_b) * 100:.0f}% chance to win"
    elif days is not None and days >= TIME_BOX_DAYS:
        call = f"TIE - {days} days and neither page reached {ss.WIN_BAR * 100:.0f}%. Keep the control and test something bigger"
    else:
        left = f" · the tie is called at day {TIME_BOX_DAYS}" if days is not None else ""
        call = f"KEEP GOING - the test has a {prob_b * 100:.0f}% chance, the call is at {ss.WIN_BAR * 100:.0f}%{left}"
    print(f"\n**The call: {call}**")


def stop(slug, winner):
    key = flag_key(slug)
    exp = find_experiment(key)
    if exp and not exp.get("end_date"):
        ph.patch(f"experiments/{exp['id']}/", {"end_date": datetime.now(timezone.utc).isoformat()})
        print(f"Experiment ended: {ph.ui('experiments/' + str(exp['id']))}")
    if exp and winner in ("control", "test"):
        st, _ = ph.call("POST", f"experiments/{exp['id']}/ship_variant/", {"variant_key": winner, "release_to_everyone": True}, soft=True)
        if st in (200, 201):
            print(f"Shipped {winner} to everyone through the experiment. Move the winner into page.tsx, delete the loser, then delete the flag.")
            return
    flag = find_flag(key)
    if flag and winner in ("control", "test"):
        f = flag["filters"]
        for v in f["multivariate"]["variants"]:
            v["rollout_percentage"] = 100 if v["key"] == winner else 0
        ph.patch(f"feature_flags/{flag['id']}/", {"filters": f})
        print(f"Everyone now sees {winner}. Move the winner into page.tsx, delete the loser, then delete the flag.")


def list_all():
    out = ph.get("experiments/", limit=100)
    for e in out.get("results", []):
        print(f"- {e.get('name')} · {e.get('feature_flag_key') or (e.get('feature_flag') or {}).get('key')} · "
              f"{'running' if not e.get('end_date') else 'ended'} · {ph.ui('experiments/' + str(e['id']))}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--create"); ap.add_argument("--aa", action="store_true")
    ap.add_argument("--status"); ap.add_argument("--lift", type=float, default=0.2,
                    help="the lift the test is built to detect; --create writes it into the experiment, --status judges against it")
    ap.add_argument("--stop"); ap.add_argument("--winner", default="")
    ap.add_argument("--list", action="store_true")
    a = ap.parse_args()
    if a.create: create(a.create, a.aa, a.lift if "--lift" in sys.argv else 0.3)
    elif a.status: status(a.status, a.lift)
    elif a.stop: stop(a.stop, a.winner)
    elif a.list: list_all()
    else: ap.print_help(); sys.exit(1)
