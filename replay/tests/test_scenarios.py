"""Staged settings tests (replay.scenarios) against a fake simulator: no Node needed."""

from ingestion.models import GlucoseReading, Treatment
from replay.scenarios import (
    _metrics,
    choose,
    classify,
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
