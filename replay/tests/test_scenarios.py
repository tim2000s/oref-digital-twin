"""Staged settings tests (replay.scenarios) against a fake simulator: no Node needed."""

import pytest

from ingestion.models import GlucoseReading, Treatment
from replay.scenarios import (
    _metrics,
    choose,
    classify,
    guard_refuses,
    meal_bolus_doses,
    run_settings_tests,
    sample_cycles,
)

T0 = 1_760_000_000_000
MIN = 60_000


def _readings(values, step_min=5, t0=T0):
    return [GlucoseReading(ts_ms=t0 + i * step_min * MIN, sgv_mgdl=v) for i, v in enumerate(values)]


def test_sample_cycles_keeps_one_per_five_minutes():
    class C:
        def __init__(self, ts):
            self.ts_ms = ts
    t0 = T0 - T0 % (5 * MIN)                                 # slots are clock-aligned
    cycles = [C(t0 + m * MIN) for m in range(0, 30)]         # a one-minute loop
    kept = sample_cycles(cycles)
    assert len(kept) == 6
    assert all(b.ts_ms - a.ts_ms == 5 * MIN for a, b in zip(kept, kept[1:]))


def test_classify_logged_carbs_rise_and_correction():
    vals = ([100] * 120                                      # 10 h flat
            + [100 + 10 * i for i in range(10)]              # +90 in 45 min, no carbs logged
            + [190] * 39 + [150] * 40)
    entries = _readings(vals)
    carbs = [Treatment(ts_ms=T0 + 2 * 3_600_000, event_type="Meal Bolus", carbs_g=40)]
    labels = classify(entries, carbs)
    assert labels[0] == "fasting"
    assert labels[24] == labels[72] == "meal"                # logged carbs, 4 h window
    assert labels[73] == "fasting"
    # an unannounced rise from 100: the window runs 4 h from the last low point that still
    # sits 45 below the reading, which moves up the climb as the hour rolls forward
    assert labels[120] == labels[172] == "meal"
    assert labels[173] == labels[204] == "correction"        # above 180 within 3 h, no meal
    assert labels[205] == "fasting"


def test_classify_recovery_from_a_low_is_not_a_meal():
    labels = classify(_readings([110] * 12 + [55] * 4 + [110] * 12), [])
    assert set(labels) == {"fasting"}


def test_meal_bolus_doses_scale_with_inverse_ratio():
    tr = [Treatment(ts_ms=T0, event_type="Meal Bolus", carbs_g=50),
          Treatment(ts_ms=T0 + 5 * MIN, event_type="Bolus", insulin_u=5.0),
          Treatment(ts_ms=T0 + 6 * MIN, event_type="Correction Bolus", insulin_u=0.3, is_smb=True),
          Treatment(ts_ms=T0 + 300 * MIN, event_type="Correction Bolus", insulin_u=2.0)]
    doses = meal_bolus_doses(tr, 1.25)                        # a 25% higher ratio: 1/1.25 = 0.8
    assert doses == [{"t": T0 + 5 * MIN, "u": -1.0}]          # SMB and late bolus untouched
    assert meal_bolus_doses(tr, 1.0) == []


def test_metrics_counts_low_episodes_of_fifteen_minutes():
    vals = [100] * 5 + [65] * 4 + [100] * 5 + [60] * 2 + [100] * 3   # 15 min low, then 5 min low
    m = _metrics([r.ts_ms for r in _readings(vals)], vals, [True] * len(vals), 5)
    assert m["lows"] == 1
    assert m["tbr"] == round(6 / len(vals) * 100, 1)
    assert m["hours"] == round(len(vals) * 5 / 60, 1)


def _row(v, tir, tbr):
    return {"value": v, "distance": v - 1.0, "est": {"tir": tir, "tbr": tbr}}


def test_choose_prefers_smallest_change_meeting_both_goals():
    rows = [_row(0.8, 80, 1.0), _row(0.9, 75, 1.5), _row(1.0, 72, 3.0), _row(1.1, 90, 4.0)]
    best, why = choose(rows)
    assert best["value"] == 0.9 and "smallest change" in why


def test_choose_keeps_lows_down_when_range_goal_unreachable():
    rows = [_row(0.8, 60, 1.0), _row(0.9, 65, 1.9), _row(1.0, 68, 3.0)]
    best, why = choose(rows)
    assert best["value"] == 0.9 and "under 2%" in why
    rows = [_row(0.8, 60, 2.5), _row(1.0, 68, 3.0)]
    assert choose(rows)[0]["value"] == 0.8


def test_choose_keeps_current_when_it_already_meets_goals():
    rows = [_row(0.9, 85, 0.5), _row(1.0, 80, 1.0), _row(1.1, 88, 1.5)]
    best, why = choose(rows)
    assert best["value"] == 1.0 and why == "already meets both goals"


def test_run_settings_tests_stages_in_order_with_a_fake_simulator():
    # a day of fasting readings dipping below 70 every few hours
    vals = ([110] * 30 + [62] * 6) * 8
    entries = _readings(vals)
    requests = [{"currentTime": r.ts_ms, "profile": {"target_bg": 100}} for r in entries[::1]]
    calls, kept = [], {}

    def fake_sim(payload):
        calls.append(payload["scenarios"])
        # like the real simulator: cycles arrive once, later calls name them by cache_key
        if "cycles" in payload:
            kept[payload["cache_key"]] = payload["cycles"]
        t = [r["currentTime"] for r in kept[payload["cache_key"]]]
        out = []
        for sc in payload["scenarios"]:
            # less basal or a higher target raises glucose evenly
            shift = (1 - sc["basal_scale"]) * 50 + sc["target_offset"] * 0.5
            out.append({"label": sc["label"], "du": [0.0] * len(t), "dbg": [shift] * len(t),
                        "failed": 0})
        return {"t": t, "baseline": [0.0] * len(t), "scenarios": out}

    res = run_settings_tests(fake_sim, requests, entries, [], {"enable_smb": False})
    names = [s["name"] for s in res["stages"]]
    assert names == ["Basal", "ISF", "Carb ratio", "Target", "SMB limit", "Max IOB"]
    basal = res["stages"][0]
    # observed fasting TBR is 6/36 = 16.7%; -20% (+10 mg/dL) is the smallest change that
    # lifts 62 to 70 or above
    assert basal["observed"]["tbr"] == 16.7
    assert basal["chosen"] == 0.8
    # later stages run with the chosen basal: every scenario they send carries it
    assert all(sc["basal_scale"] == 0.8 for batch in calls[1:] for sc in batch)
    # no carbs logged and no SMB: those stages are explained, not run
    assert res["stages"][2]["rows"] == [] and "no carbs" in res["stages"][2]["why"]
    assert res["stages"][4]["chosen_label"] == "not tested"
    assert res["stages"][5]["chosen_label"] == "not tested"      # max IOB unknown here
    assert res["final"]["est_all"]["tbr"] == 0.0
    # a scenario already run (each stage's no-change row) is not sent again
    sent = [str(sorted(sc.items())) for batch in calls for sc in batch if sc.pop("label", None) or True]
    assert len(sent) == len(set(sent))


def test_max_iob_stage_steps_the_current_value():
    entries = _readings(([110] * 30 + [62] * 6) * 8)
    requests = [{"currentTime": r.ts_ms, "profile": {"target_bg": 100}} for r in entries]
    kept, seen = {}, []

    def fake_sim(payload):
        if "cycles" in payload:
            kept[payload["cache_key"]] = payload["cycles"]
        t = [r["currentTime"] for r in kept[payload["cache_key"]]]
        seen.extend(payload["scenarios"])
        return {"t": t, "scenarios": [{"du": [0.0] * len(t), "dbg": [0.0] * len(t), "failed": 0}
                                      for _ in payload["scenarios"]]}

    res = run_settings_tests(fake_sim, requests, entries, [], {"max_iob": 6.0})
    stage = res["stages"][5]
    assert [r["value"] for r in stage["rows"]] == [4.2, 4.8, 5.4, 6.0, 6.6, 7.2, 7.8]
    assert any(sc.get("profile_set", {}).get("max_iob") == 4.2 for sc in seen)
    assert stage["rows"][3]["label"] == "6 U (current)"


def test_target_labels_describe_the_whole_schedule():
    # a target of 86 overnight and 112 by day: the step applies to both, and the label says so
    entries = _readings([120] * 300)
    requests = [{"currentTime": r.ts_ms, "profile": {"target_bg": 112 if i % 2 else 86}}
                for i, r in enumerate(entries)]
    kept = {}

    def fake_sim(payload):
        if "cycles" in payload:
            kept[payload["cache_key"]] = payload["cycles"]
        t = [r["currentTime"] for r in kept[payload["cache_key"]]]
        return {"t": t, "scenarios": [{"du": [0.0] * len(t), "dbg": [0.0] * len(t), "failed": 0}
                                      for _ in payload["scenarios"]]}

    res = run_settings_tests(fake_sim, requests, entries, [], {})
    labels = [r["label"] for r in res["stages"][3]["rows"]]
    assert labels[0] == "86–112 mg/dL (4.8–6.2 mmol/L) (current)"   # 86-9 = 77 is under 80
    assert labels[1] == "+0.5 mmol/L (+9 mg/dL) on every target: 95–121 mg/dL (5.3–6.7 mmol/L)"


def test_max_iob_no_change_row_is_the_exact_current_value():
    entries = _readings(([110] * 30 + [62] * 6) * 8)
    requests = [{"currentTime": r.ts_ms, "profile": {"target_bg": 100}} for r in entries]
    kept, seen = {}, []

    def fake_sim(payload):
        if "cycles" in payload:
            kept[payload["cache_key"]] = payload["cycles"]
        t = [r["currentTime"] for r in kept[payload["cache_key"]]]
        seen.extend(payload["scenarios"])
        return {"t": t, "scenarios": [{"du": [0.0] * len(t), "dbg": [0.0] * len(t), "failed": 0}
                                      for _ in payload["scenarios"]]}

    res = run_settings_tests(fake_sim, requests, entries, [], {"max_iob": 7.19})
    stage = res["stages"][5]
    assert 7.19 in [r["value"] for r in stage["rows"]]
    assert "7.19 U (current)" in [r["label"] for r in stage["rows"]]
    assert stage["chosen"] == 7.19          # nothing to gain from moving it, so it stays exact
    assert res["chosen"]["max_iob"] == 7.19


def _shift_sim(shift_of):
    kept = {}

    def fake_sim(payload):
        if "cycles" in payload:
            kept[payload["cache_key"]] = payload["cycles"]
        t = [r["currentTime"] for r in kept[payload["cache_key"]]]
        return {"t": t, "scenarios": [{"du": [0.0] * len(t), "dbg": [shift_of(sc)] * len(t),
                                       "failed": 0} for sc in payload["scenarios"]]}
    return fake_sim


def test_more_insulin_is_excluded_when_it_would_raise_lows_past_the_limits():
    # A flat 68-75 day: below 70 now and then. More basal lowers glucose and raises time in
    # range only on paper; any value giving more insulin that takes the whole period's time below
    # 54 to 0.6% or more must be excluded, however much range it adds.
    vals = ([72] * 20 + [100] * 20 + [56] * 1) * 10
    entries = _readings(vals)
    requests = [{"currentTime": r.ts_ms, "profile": {"target_bg": 100}} for r in entries]
    res = run_settings_tests(_shift_sim(lambda sc: (1 - sc["basal_scale"]) * 30),
                             requests, entries, [], {})
    basal = res["stages"][0]
    stronger = [r for r in basal["rows"] if r["more_insulin"]]
    assert stronger and all(r["excluded"] == (r["est_all"]["tbr"] >= 2.0 or r["est_all"]["tbr54"] >= 0.6)
                            for r in stronger)
    assert basal["chosen"] <= 1.0
    assert not any(r["excluded"] for r in basal["rows"] if not r["more_insulin"])


def test_isf_is_judged_on_the_whole_period_not_on_the_high_slice():
    # Correction stretches (3 h after a reading over 180) are high by selection, 0% in range
    # here, but the whole period meets both goals; ISF must be left alone.
    # a slow rise (30 mg/dL an hour) so the high is not taken for an unannounced meal
    ramp = [round(110 + 90 * i / 36) for i in range(36)]
    day = [110] * 100 + ramp + [200] * 12 + [150] * 36 + [110] * 64
    entries = _readings(day * 4)
    requests = [{"currentTime": r.ts_ms, "profile": {"target_bg": 100}} for r in entries]
    res = run_settings_tests(_shift_sim(lambda sc: (1 - sc["isf_scale"]) * -40), requests,
                             entries, [], {})
    isf = res["stages"][1]
    assert isf["enough_hours"] >= 6 and isf["measured_on"] == "all"
    assert isf["chosen"] == 1.0 and isf["why"] == "already meets both goals"


def test_the_tighter_aim_acts_where_the_standard_aim_is_satisfied():
    # 75% in range with no lows, judged on the target stage (whole period): the standard aim
    # (70%) leaves the target alone; the tighter (80%) takes the smallest step reaching it.
    day = [120] * 75 + [200] * 25
    entries = _readings(day * 4)
    requests = [{"currentTime": r.ts_ms, "profile": {"target_bg": 100}} for r in entries]
    shift = lambda sc: sc["target_offset"] * 2.0            # a lower target lowers glucose
    std = run_settings_tests(_shift_sim(shift), requests, entries, [], {})
    tight = run_settings_tests(_shift_sim(shift), requests, entries, [], {}, aim="tighter")
    assert std["stages"][3]["chosen"] == 0 and std["goals"]["tir_gt_pct"] == 70.0
    assert tight["stages"][3]["chosen"] == -18 and tight["goals"]["tir_gt_pct"] == 80.0
    assert tight["aim"] == "tighter"


def test_an_unknown_aim_is_refused():
    import pytest
    entries = _readings([120] * 300)
    requests = [{"currentTime": r.ts_ms, "profile": {"target_bg": 100}} for r in entries]
    with pytest.raises(ValueError):
        run_settings_tests(_shift_sim(lambda sc: 0.0), requests, entries, [], {}, aim="tight")


def test_classify_a_bolus_without_carbs_under_180_as_a_meal():
    flat = _readings([120] * 120)                            # 10 h, no rise a meal would show
    at = lambda h: T0 + int(h * 3_600_000)
    bolus = Treatment(ts_ms=at(2), event_type="Correction Bolus", insulin_u=4.0)
    labels = classify(flat, [bolus])
    assert labels[23] == "fasting" and labels[24] == labels[72] == "meal" and labels[73] == "fasting"
    smb = Treatment(ts_ms=at(2), event_type="Correction Bolus", insulin_u=1.0, is_smb=True)
    tiny = Treatment(ts_ms=at(2), event_type="Correction Bolus", insulin_u=0.3)
    assert set(classify(flat, [smb, tiny])) == {"fasting"}
    high = _readings([200] * 120)                            # a correction, not a meal
    assert "meal" not in classify(high, [Treatment(ts_ms=at(2), event_type="Correction Bolus", insulin_u=4.0)])


def test_classify_bolus_meal_rule_edges():
    at = lambda h: T0 + int(h * 3_600_000)
    b = lambda h, u=4.0: Treatment(ts_ms=at(h), event_type="Correction Bolus", insulin_u=u)
    # no reading in the 15 minutes before the bolus: not judged
    gap = [r for r in _readings([120] * 120) if not (at(1.5) < r.ts_ms <= at(2))]
    assert "meal" not in classify(gap, [b(2)])
    # a bolus at 175 on the way down from 250 is a correction
    down = _readings([250] * 12 + [175] * 108)
    assert "meal" not in classify(down, [b(1.05)])
    # unflagged automatic boluses, every 5 minutes, would make the day a meal: the rule stands down
    flat = _readings([120] * 288)
    auto = [b(i / 12, 0.6) for i in range(288)]
    assert set(classify(flat, auto)) == {"fasting"}


def test_settings_tests_ask_the_simulator_to_treat_new_lows():
    from replay.scenarios import RESCUE
    seen, inner = [], _shift_sim(lambda sc: 0.0)

    def sim(payload):
        seen.append(payload)
        return inner(payload)

    entries = _readings([120] * 300)
    requests = [{"currentTime": r.ts_ms, "profile": {"target_bg": 100}} for r in entries]
    run_settings_tests(sim, requests, entries, [], {})
    assert seen and all(p.get("rescue") == RESCUE for p in seen) and RESCUE["mode"] == "new"


_NOW = {"before": {"tir": 70.0, "tbr": 1.0}, "after": {"tir": 71.0, "tbr": 1.0}}


def test_guard_caps_each_setting_at_twenty_percent_from_the_reference():
    h = {"cumulative": {"basal": 1.1, "isf": 0.9, "cr": 1.0, "target": -9}}
    assert guard_refuses("basal", 1.1, h) is not None                 # 1.21
    assert guard_refuses("basal", 1.2, {"cumulative": {"basal": 1.0}}) is None
    assert guard_refuses("basal", 1.2, h) is not None                 # 1.32
    assert guard_refuses("isf", 0.9, h) is None                       # 0.81
    assert guard_refuses("isf", 0.8, h) is not None                   # 0.72
    assert guard_refuses("cr", 0.8, h) is None                        # 0.8 is the cap itself
    assert guard_refuses("cr", 0.7, h) is not None
    assert guard_refuses("target", -9, h) is not None                 # 18 below
    assert guard_refuses("target", -9, {"cumulative": {"target": 0}}) is None
    assert guard_refuses("basal", 1.3, None) is None                  # no history, no guard


def test_guard_refuses_a_second_step_unless_the_last_one_showed_its_gain():
    last = {"cumulative": {"isf": 0.9}, "last": {"isf": 0.9}}
    assert guard_refuses("isf", 0.9, {**last, **_NOW}) is not None    # +1 point: not shown
    gained = {**last, "before": {"tir": 70.0, "tbr": 1.0}, "after": {"tir": 72.0, "tbr": 1.0}}
    assert guard_refuses("isf", 0.9, gained) is None
    more_lows = {**gained, "after": {"tir": 75.0, "tbr": 1.5}}
    assert guard_refuses("isf", 0.9, more_lows) is not None
    assert guard_refuses("isf", 0.9, last) is not None                # no outcomes: not shown
    # a last change towards less insulin, or one under 5%, does not count
    assert guard_refuses("isf", 0.9, {"last": {"isf": 1.1}, **_NOW}) is None
    assert guard_refuses("basal", 1.1, {"last": {"basal": 1.05}, **_NOW}) is None   # not more than 5%
    assert guard_refuses("isf", 0.9, {"last": {"isf": 0.95}, **_NOW}) is None
    assert guard_refuses("basal", 1.1, {"last": {"basal": 1.1}, **_NOW}) is not None
    assert guard_refuses("target", -9, {"last": {"target": -9}, **_NOW}) is not None
    assert guard_refuses("target", -9, {"last": {"target": -4}, **_NOW}) is None


def test_the_guard_reaches_basal_isf_carb_ratio_and_target_and_nothing_else(monkeypatch):
    import replay.scenarios as S
    seen = []

    def refuse(key, value, history):
        seen.append(key)
        return "refused"
    monkeypatch.setattr(S, "guard_refuses", refuse)
    entries = _readings(([120] * 75 + [200] * 25) * 4)
    requests = [{"currentTime": r.ts_ms, "profile": {"target_bg": 100}} for r in entries]
    meals = [Treatment(ts_ms=T0 + 60 * MIN, event_type="Meal Bolus", carbs_g=40)]
    shift = lambda sc: ((1 - sc["basal_scale"]) * 30 + (sc["isf_scale"] - 1) * 30
                        + (sc["cr_scale"] - 1) * 30 + sc["target_offset"] * 2.0)
    settings = {"enable_smb": True, "max_smb_minutes": 30, "max_iob": 5.0}
    res = run_settings_tests(_shift_sim(shift), requests, entries, meals, settings,
                             aim="tighter", history={"cumulative": {}})
    assert set(seen) == {"basal", "isf", "cr", "target"}
    for st in res["stages"]:
        stronger = [r for r in st["rows"] if r["more_insulin"]]
        if st["name"] in ("Basal", "ISF", "Carb ratio", "Target"):
            assert stronger and all(r["excluded"] and r["guard"] == "refused" for r in stronger)
        else:
            assert all(r["guard"] is None for r in st["rows"])
    # unguarded, the same data is given more insulin somewhere, as the aim asks
    monkeypatch.undo()
    free = run_settings_tests(_shift_sim(shift), requests, entries, meals, settings, aim="tighter")
    towards = lambda c: (c["basal_scale"] > 1 or c["isf_scale"] < 1 or c["cr_scale"] < 1
                         or c["target_offset"] < 0)
    assert towards(free["chosen"]) and not towards(res["chosen"])


def test_isf_band_judges_each_value_on_its_least_favourable_sensitivity():
    # highs at 190 and a floor at 80, and a target 9 mg/dL lower that the fake simulator turns into
    # a fall of 10 mg/dL times the body's sensitivity scale. As the profile ISF says, that brings
    # the highs to 180 without a low; with insulin 30% stronger it takes 80 to 67, so under the
    # band it is refused. The target stage judges the whole period with no gate.
    vals = ([190] * 20 + [80] * 16) * 24
    entries = _readings(vals)
    requests = [{"currentTime": r.ts_ms, "profile": {"target_bg": 100}} for r in entries]
    payloads, kept = [], {}

    def fake_sim(payload):
        payloads.append({k: v for k, v in payload.items() if k not in ("cycles", "scenarios")})
        if "cycles" in payload:
            kept[payload["cache_key"]] = payload["cycles"]
        t = [r["currentTime"] for r in kept[payload["cache_key"]]]
        b = payload.get("body_isf_scale", 1.0)
        out = [{"label": sc["label"], "du": [0.0] * len(t),
                "dbg": [sc["target_offset"] * 10 / 9 * b] * len(t), "failed": 0}
               for sc in payload["scenarios"]]
        return {"t": t, "baseline": [0.0] * len(t), "scenarios": out}

    plain = run_settings_tests(fake_sim, requests, entries, [], {"enable_smb": False})
    assert plain["stages"][3]["chosen"] == -9
    payloads.clear()
    band = run_settings_tests(fake_sim, requests, entries, [], {"enable_smb": False},
                              sim_opts={"body": {"model": "hovorka"}}, isf_band=(0.7, 1.0, 1.3))
    assert band["stages"][3]["chosen"] == 0
    assert all(p["body"] == {"model": "hovorka"} for p in payloads)
    assert {p.get("body_isf_scale") for p in payloads} == {None, 0.7, 1.3}
    row = next(r for r in band["stages"][3]["rows"] if r["value"] == -9)
    assert row["est"]["tbr"] > 0 and row["excluded"]
    with pytest.raises(ValueError):
        run_settings_tests(fake_sim, requests, entries, [], {"enable_smb": False}, isf_band=(0.7, 1.3))


def _more(c):
    return {"basal": c["basal_scale"] > 1, "isf": c["isf_scale"] < 1, "cr": c["cr_scale"] < 1,
            "target": c["target_offset"] < 0}


def test_pace_strengthens_one_setting_by_one_step_per_review():
    # Highs spread over 185 to 215 that a stronger ISF brings into range step by step, and a lower
    # target that helps too, with nothing going low. Without pace ISF goes two steps, the
    # smallest change meeting the aim; with it one step, and no later stage adds insulin.
    entries = _readings(([120] * 60 + [185, 195, 205, 215] * 10) * 4)
    requests = [{"currentTime": r.ts_ms, "profile": {"target_bg": 100}} for r in entries]
    meals = [Treatment(ts_ms=T0 + 60 * MIN, event_type="Meal Bolus", carbs_g=40)]
    shift = lambda sc: (sc["isf_scale"] - 1) * 130 + sc["target_offset"] * 2.0
    settings = {"enable_smb": True, "max_smb_minutes": 30, "max_iob": 5.0}
    free = run_settings_tests(_shift_sim(shift), requests, entries, meals, settings, aim="tighter")
    paced = run_settings_tests(_shift_sim(shift), requests, entries, meals, settings, aim="tighter",
                               pace=True)
    assert free["chosen"]["isf_scale"] == 0.8
    c = paced["chosen"]
    assert c["isf_scale"] == 0.9 and sum(_more(c).values()) == 1
    assert c["smb_minutes"] == 30 and c["max_iob"] == 5.0
    reasons = set()
    for st in paced["stages"]:
        for r in st["rows"]:
            assert not r["excluded"] or r["more_insulin"]
            if r["guard"]:
                reasons.add(r["guard"].split(" ")[0])
        if st["name"] in ("Carb ratio", "Target", "SMB limit", "Max IOB"):
            assert all(r["excluded"] and r["guard"].startswith("another setting")
                       for r in st["rows"] if r["more_insulin"])
    assert reasons == {"more", "another"}


def test_pace_leaves_weakening_alone():
    # Frequent lows that only a large cut in basal clears: pace must not slow the cut.
    entries = _readings(([62] * 10 + [110] * 30) * 20)
    requests = [{"currentTime": r.ts_ms, "profile": {"target_bg": 100}} for r in entries]
    shift = lambda sc: (1 - sc["basal_scale"]) * 30
    free = run_settings_tests(_shift_sim(shift), requests, entries, [], {})
    paced = run_settings_tests(_shift_sim(shift), requests, entries, [], {}, pace=True)
    assert free["stages"][0]["chosen"] == 0.7
    assert paced["stages"][0]["chosen"] == 0.7
    weaker = lambda res: [r for r in res["stages"][0]["rows"] if not r["more_insulin"]]
    assert weaker(paced) == weaker(free)
