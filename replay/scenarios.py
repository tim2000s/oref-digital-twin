"""Staged settings tests: basal, then ISF, then carb ratio, then target and SMB limits.

Each stage steps one setting across a band, runs the loop through the whole period under
each value with the closed-loop simulator (oracle/request.js `simulate`), and judges every
value on the stretches of the day that setting governs, against time in range above 70% and
time below range under 2%:

  1. basal, on fasting stretches (no carbs or unannounced rise in the last 4 h, and no
     reading above 180 mg/dL in the last 3 h);
  2. ISF, on the whole period, judged only when there are at least 6 h of correction stretches
     (a reading above 180 mg/dL in the last 3 h, outside meals), with the basal from stage 1;
  3. carb ratio, on meal stretches (the 4 h after logged carbs or an unannounced rise), with
     the basal and ISF chosen before it; logged meal boluses are scaled by the same factor,
     on the assumption that they came from the bolus wizard;
  4. target, 5. SMB limits and 6. max IOB, on the whole period, with everything chosen
     before.

The order follows a manual basal test, then an ISF test, then a carb-ratio test: each
setting is tested where the ones after it have least influence, and later stages build on
the earlier choices.

The glucose each value is judged on is the observed CGM shifted by the simulator's estimate,
which takes the profile ISF as the body's sensitivity and assumes meals, activity and the
person's own treatments would have been unchanged. These are modelled estimates, not
outcomes, and each stage's choice is a trial to test, not a setting to apply.
"""

from __future__ import annotations

import bisect
import json
import uuid
from collections import deque
from dataclasses import dataclass
from typing import Any, Callable

from ingestion.models import GlucoseReading, Treatment

GOAL_TIR_PCT = 70.0       # time in range, 70-180 mg/dL: more than this
GOAL_TBR_PCT = 2.0        # time below 70 mg/dL: less than this
# A value giving more insulin than the current setting is only considered when the whole
# period's estimate stays under both of these (Tim Street, 9 October 2026). Without it the rule
# could trade a person with almost no lows up towards 2% for time in range, which on TimSim took
# one subject's time below 54 from 0.01% to 0.81% (validation/BAD_PROFILES.md).
STRENGTHEN_TBR70_MAX = 2.0
STRENGTHEN_TBR54_MAX = 0.6

SCALES = (0.7, 0.8, 0.9, 1.0, 1.1, 1.2, 1.3)
TARGET_OFFSETS_MGDL = (-18, -9, 0, 9, 18)      # about -1, -0.5, 0, +0.5, +1 mmol/L
MIN_TARGET_MGDL = 80
SMB_MINUTES = (15, 30, 45, 60, 90)

CADENCE_MIN = 5
MEAL_WINDOW_MIN = 240
RISE_MGDL = 45            # an unannounced rise: this much within RISE_WINDOW_MIN
RISE_WINDOW_MIN = 60
RISE_FROM_MGDL = 80       # a climb out of a low is recovery, not a meal
CORRECTION_LOOKBACK_MIN = 180
HIGH_MGDL = 180
LOW_MGDL = 70
LOW_EPISODE_MIN = 15
MIN_SEGMENT_HOURS = 6     # below this a stage is reported but not judged

SimRunner = Callable[[dict], dict]

CAVEAT = (
    "Estimated, not measured: each value's glucose is your CGM shifted by the change in "
    "insulin the loop would have given, times your profile ISF, with the loop reacting to "
    "the shifted glucose at every step. It assumes your meals, activity and own treatments "
    "would have been the same, and that your profile ISF is your real sensitivity. Treat "
    "any change as a trial to test, one setting at a time."
)


@dataclass
class Window:
    lo: int
    hi: int


def sample_cycles(cycles: list, cadence_min: int = CADENCE_MIN) -> list:
    """One cycle per `cadence_min` slot, the first in each, in time order.

    Loops that run every minute would otherwise give five times the cycles for the same
    decisions.
    """
    out, last_slot = [], None
    for c in sorted(cycles, key=lambda c: c.ts_ms):
        slot = c.ts_ms // (cadence_min * 60_000)
        if slot != last_slot:
            out.append(c)
            last_slot = slot
    return out


def classify(entries: list[GlucoseReading], treatments: list[Treatment]) -> list[str]:
    """Label each reading 'meal', 'correction' or 'fasting' (see the module docstring)."""
    pts = [(r.ts_ms, r.sgv_mgdl) for r in entries if r.sgv_mgdl is not None]
    meal: list[Window] = [Window(t.ts_ms, t.ts_ms + MEAL_WINDOW_MIN * 60_000)
                          for t in treatments if (t.carbs_g or 0) > 0]
    # Unannounced rises: a reading this far above the lowest of the previous hour starts a
    # meal window at that low point, unless the low point was below 80 mg/dL, when the rise
    # is taken as recovery from a low. Boost and UAM users often log no carbs at all.
    lows: deque = deque()
    for ts, bg in pts:
        while lows and lows[0][0] < ts - RISE_WINDOW_MIN * 60_000:
            lows.popleft()
        while lows and lows[-1][1] >= bg:
            lows.pop()
        lows.append((ts, bg))
        lo_ts, lo_bg = lows[0]
        if lo_bg >= RISE_FROM_MGDL and bg - lo_bg >= RISE_MGDL:
            meal.append(Window(lo_ts, lo_ts + MEAL_WINDOW_MIN * 60_000))
    meal.sort(key=lambda w: w.lo)
    merged: list[Window] = []
    for w in meal:
        if merged and w.lo <= merged[-1].hi:
            merged[-1].hi = max(merged[-1].hi, w.hi)
        else:
            merged.append(Window(w.lo, w.hi))
    starts = [w.lo for w in merged]

    labels = []
    highs: deque = deque()           # times of readings above HIGH in the lookback
    for ts, bg in pts:
        while highs and highs[0] < ts - CORRECTION_LOOKBACK_MIN * 60_000:
            highs.popleft()
        if bg > HIGH_MGDL:
            highs.append(ts)
        i = bisect.bisect_right(starts, ts) - 1
        if i >= 0 and merged[i].lo <= ts <= merged[i].hi:
            labels.append("meal")
        elif highs:
            labels.append("correction")
        else:
            labels.append("fasting")
    return labels


def meal_bolus_doses(treatments: list[Treatment], cr_scale: float) -> list[dict]:
    """The change to each logged meal bolus if the carb ratio were scaled by `cr_scale`.

    A bolus counts as a meal bolus when it is not an SMB and falls within 15 minutes before
    or 30 after logged carbs. It is assumed to have come from the bolus wizard, so it scales
    with 1 / carb ratio.
    """
    if cr_scale == 1:
        return []
    carbs = [t.ts_ms for t in treatments if (t.carbs_g or 0) > 0]
    out = []
    for t in treatments:
        if not t.insulin_u or t.insulin_u <= 0 or t.is_smb:
            continue
        if any(-15 * 60_000 <= t.ts_ms - c <= 30 * 60_000 for c in carbs):
            out.append({"t": t.ts_ms, "u": round(t.insulin_u * (1 / cr_scale - 1), 3)})
    return out


def _interp(xs: list[int], ys: list[float], x: int) -> float:
    if not xs or x < xs[0]:
        return 0.0
    i = bisect.bisect_right(xs, x) - 1
    if i + 1 >= len(xs):
        return ys[i]
    x0, x1 = xs[i], xs[i + 1]
    return ys[i] + (ys[i + 1] - ys[i]) * (x - x0) / (x1 - x0) if x1 > x0 else ys[i]


def _metrics(ts: list[int], bg: list[float], mask: list[bool], step_min: float) -> dict[str, Any]:
    """Time in range, time below range and low episodes over the masked readings.

    `step_min` is the CGM interval, so the hours reported are hours of readings rather than
    the span they happen to cover.
    """
    sel = [(t, g) for t, g, m in zip(ts, bg, mask) if m]
    n = len(sel)
    if not n:
        return {"n": 0, "hours": 0.0, "tir": None, "tbr": None, "tbr54": None, "lows": 0}
    tir = sum(LOW_MGDL <= g <= HIGH_MGDL for _, g in sel) / n * 100
    tbr = sum(g < LOW_MGDL for _, g in sel) / n * 100
    tbr54 = sum(g < 54 for _, g in sel) / n * 100
    # a low episode is a run of readings below 70 lasting at least 15 minutes; a gap of more
    # than 15 minutes between readings ends a run
    lows, run_start, run_last = 0, None, None
    for t, g in sel:
        if run_last is not None and (g >= LOW_MGDL or t - run_last > 15 * 60_000):
            if run_last - run_start >= LOW_EPISODE_MIN * 60_000:
                lows += 1
            run_start = run_last = None
        if g < LOW_MGDL:
            run_start = t if run_start is None else run_start
            run_last = t
    if run_last is not None and run_last - run_start >= LOW_EPISODE_MIN * 60_000:
        lows += 1
    return {"n": n, "hours": round(n * step_min / 60, 1), "tir": round(tir, 1),
            "tbr": round(tbr, 1), "tbr54": round(tbr54, 2), "lows": lows}


def _meets(m: dict) -> bool:
    return m["tir"] is not None and m["tir"] > GOAL_TIR_PCT and m["tbr"] < GOAL_TBR_PCT


def choose(rows: list[dict]) -> tuple[dict, str]:
    """Pick a row: meet both goals with the smallest change; else keep lows down first.

    Time below range comes first because a low is the immediate harm: when no value meets
    both goals, the value with time below range under 2% and the most time in range wins,
    and failing that the value with the least time below range.
    """
    def change(r: dict) -> float:
        return abs(r["distance"])

    # More insulin than now is only on the table while the whole period's lows stay low.
    rows = [r for r in rows if not r.get("excluded")]
    ok = [r for r in rows if _meets(r["est"])]
    if ok:
        best = min(ok, key=lambda r: (change(r), -r["est"]["tir"]))
        why = ("already meets both goals" if change(best) == 0 else
               "the smallest change that meets both goals")
        return best, why
    safe = [r for r in rows if r["est"]["tbr"] is not None and r["est"]["tbr"] < GOAL_TBR_PCT]
    if safe:
        best = max(safe, key=lambda r: (r["est"]["tir"], -change(r)))
        return best, "no value reaches 70% in range; this keeps lows under 2% with the most time in range"
    judged = [r for r in rows if r["est"]["tbr"] is not None]
    best = min(judged, key=lambda r: (r["est"]["tbr"], -r["est"]["tir"], change(r)))
    return best, "no value gets lows under 2%; this has the fewest"


def run_settings_tests(
    sim_runner: SimRunner,
    requests: list[dict],
    entries: list[GlucoseReading],
    treatments: list[Treatment],
    settings: dict[str, Any],
    progress: Callable[[str], None] | None = None,
) -> dict[str, Any]:
    """Run the stages and return the tables and choices for the report.

    `progress`, if given, is called with a short line as each stage starts, so a page can
    say what it is doing.
    """
    say = progress or (lambda _msg: None)
    n_stages = 6
    pts = [r for r in entries if r.sgv_mgdl is not None]
    ts = [r.ts_ms for r in pts]
    obs = [float(r.sgv_mgdl) for r in pts]
    labels = classify(pts, treatments)
    masks = {
        "fasting": [lab == "fasting" for lab in labels],
        "correction": [lab == "correction" for lab in labels],
        "meal": [lab == "meal" for lab in labels],
        "all": [True] * len(labels),
    }
    days = max((ts[-1] - ts[0]) / 86_400_000, 1e-9) if len(ts) > 1 else 1.0
    gaps = sorted(b - a for a, b in zip(ts, ts[1:]) if b > a)
    step_min = gaps[len(gaps) // 2] / 60_000 if gaps else CADENCE_MIN
    observed = {k: _metrics(ts, obs, m, step_min) for k, m in masks.items()}

    cache_key = uuid.uuid4().hex     # the simulator keeps insulin on board under this key
    done: dict[str, dict] = {}
    sent = [False]

    def key_of(sc: dict) -> str:
        return json.dumps({k: v for k, v in sc.items() if k != "label"}, sort_keys=True)

    def run(scenarios: list[dict]) -> list[dict]:
        # each stage's no-change row is the previous stage's choice; run it once
        todo = [sc for sc in scenarios if key_of(sc) not in done]
        if todo:
            # the cycles cross to the simulator once; later calls reuse them by cache_key
            payload = {"scenarios": todo, "cache_key": cache_key}
            if not sent[0]:
                payload["cycles"] = requests
                sent[0] = True
            sim = sim_runner(payload)
            for sc, res in zip(todo, sim["scenarios"]):
                done[key_of(sc)] = _summarise(sc, res, sim["t"])
        return [done[key_of(sc)] for sc in scenarios]

    def _summarise(sc: dict, res: dict, st: list[int]) -> dict:
        dbg = [d if d is not None else 0.0 for d in res["dbg"]]
        shifted = [g + _interp(st, dbg, t) for t, g in zip(ts, obs)]
        du = [d for d in res["du"] if d is not None]
        # The loop makes up most of a setting change over a day, so the net insulin
        # difference is usually near zero; where glucose settles is what changes.
        shift = [s - g for s, g in zip(shifted, obs)]
        return {"shifted": shifted, "du_per_day": round(sum(du) / days, 2),
                "mean_shift": round(sum(shift) / len(shift), 1) if shift else 0.0,
                "failed": res.get("failed", 0)}

    chosen: dict[str, Any] = {"basal_scale": 1.0, "isf_scale": 1.0, "cr_scale": 1.0,
                              "target_offset": 0}
    stages: list[dict] = []
    has_carbs = any((t.carbs_g or 0) > 0 for t in treatments)

    def stage(name: str, lever: str, measured_on: str, values: list, make, neutral,
              fmt, more_insulin, note: str | None = None, enough_on: str | None = None) -> Any:
        say(f"Settings tests: {name.lower()} ({len(stages) + 1} of {n_stages}), "
            f"{len(values)} values")
        scenarios = [make(v) for v in values]
        results = run(scenarios)
        rows = []
        for v, sc, res in zip(values, scenarios, results):
            est_all = _metrics(ts, res["shifted"], masks["all"], step_min)
            stronger = bool(more_insulin(v))
            rows.append({
                "value": v, "label": fmt(v), "distance": (v - neutral),
                "du_per_day": res["du_per_day"], "mean_shift": res["mean_shift"],
                "failed": res["failed"],
                "est": _metrics(ts, res["shifted"], masks[measured_on], step_min),
                "est_all": est_all,
                "more_insulin": stronger,
                "excluded": stronger and not (est_all["tbr"] < STRENGTHEN_TBR70_MAX
                                              and est_all["tbr54"] < STRENGTHEN_TBR54_MAX),
            })
        seg = observed[measured_on]
        gate = observed[enough_on or measured_on]
        entry = {"name": name, "lever": lever, "measured_on": measured_on,
                 "enough_on": enough_on, "enough_hours": gate["hours"],
                 "segment_hours": seg["hours"], "observed": seg, "rows": rows, "note": note}
        entry["neutral"] = neutral
        if gate["hours"] < MIN_SEGMENT_HOURS:
            entry["chosen"] = neutral
            entry["chosen_label"] = fmt(neutral)
            entry["why"] = (f"only {gate['hours']} h of {enough_on or measured_on} readings, "
                            f"under the {MIN_SEGMENT_HOURS} h needed to judge it; left unchanged")
        else:
            best, why = choose(rows)
            entry["chosen"] = best["value"]
            entry["chosen_label"] = best["label"]
            entry["why"] = why
        stages.append(entry)
        return entry["chosen"]

    def scen(**over) -> dict:
        s = {**chosen, **over}
        doses = meal_bolus_doses(treatments, s["cr_scale"])
        sc = {"label": ", ".join(f"{k}={v}" for k, v in over.items()),
              "basal_scale": s["basal_scale"], "isf_scale": s["isf_scale"],
              "cr_scale": s["cr_scale"], "target_offset": s["target_offset"],
              "extra_doses": doses}
        profile_set = {}
        if "smb_minutes" in s:
            profile_set.update(maxSMBBasalMinutes=s["smb_minutes"],
                               maxUAMSMBBasalMinutes=s["smb_minutes"])
        if "max_iob" in s:
            profile_set["max_iob"] = s["max_iob"]
        if profile_set:
            sc["profile_set"] = profile_set
        return sc

    pct = lambda k: f"{round((k - 1) * 100):+d}%" if k != 1 else "current"

    chosen["basal_scale"] = stage(
        "Basal", "basal rates", "fasting", list(SCALES),
        lambda k: scen(basal_scale=k), 1.0, pct, more_insulin=lambda k: k > 1)
    # ISF is judged on the whole period. Correction stretches, the readings within 3 h of one
    # above 180, only decide whether there is enough to judge: they are selected for being high,
    # so a time-in-range goal applied to them pushed ISF stronger for nearly everyone.
    chosen["isf_scale"] = stage(
        "ISF", "ISF", "all", list(SCALES),
        lambda k: scen(isf_scale=k), 1.0, pct, more_insulin=lambda k: k < 1,
        enough_on="correction")
    if has_carbs:
        chosen["cr_scale"] = stage(
            "Carb ratio", "carb ratio", "meal", list(SCALES),
            lambda k: scen(cr_scale=k), 1.0, pct, more_insulin=lambda k: k < 1,
            note="Logged meal boluses are scaled with the ratio, as the bolus wizard would.")
    else:
        stages.append({"name": "Carb ratio", "lever": "carb ratio", "measured_on": "meal",
                       "rows": [], "chosen": 1.0, "chosen_label": "current",
                       "why": "no carbs were logged in this period, so the carb ratio never "
                              "reached a dose; left unchanged"})

    # Targets often change through the day, so the offset is applied to every target in the
    # schedule and the label gives the step and the range of targets it produces.
    targets = sorted({round(r["profile"]["target_bg"]) for r in requests
                      if r.get("profile", {}).get("target_bg") is not None})
    lowest = targets[0] if targets else None
    offsets = [o for o in TARGET_OFFSETS_MGDL
               if lowest is None or lowest + o >= MIN_TARGET_MGDL]

    def fmt_target(o: int) -> str:
        if not targets:
            return f"{o:+d} mg/dL" + (" (current)" if o == 0 else "")
        lo, hi = targets[0] + o, targets[-1] + o
        span = (f"{lo} mg/dL ({lo / 18.0:.1f} mmol/L)" if lo == hi else
                f"{lo}–{hi} mg/dL ({lo / 18.0:.1f}–{hi / 18.0:.1f} mmol/L)")
        if o == 0:
            return f"{span} (current)"
        return f"{o / 18.0:+.1f} mmol/L ({o:+d} mg/dL) on every target: {span}"

    chosen["target_offset"] = stage(
        "Target", "target", "all", offsets, lambda o: scen(target_offset=o), 0, fmt_target,
        more_insulin=lambda o: o < 0)

    smb_on = bool(settings.get("enable_smb"))
    current_smb = settings.get("max_smb_minutes", 30)
    if smb_on:
        values = sorted(set(SMB_MINUTES) | {current_smb})
        chosen["smb_minutes"] = stage(
            "SMB limit", "maximum SMB basal minutes", "all", values,
            lambda m: scen(smb_minutes=m), current_smb,
            lambda m: f"{m} min" + (" (current)" if m == current_smb else ""),
            more_insulin=lambda m: m > current_smb,
            note=None if settings.get("max_smb_minutes") is not None else
            "Your current SMB limit was not in the data; 30 minutes was assumed.")
    else:
        stages.append({"name": "SMB limit", "lever": "maximum SMB basal minutes",
                       "measured_on": "all", "rows": [], "chosen": None,
                       "chosen_label": "not tested",
                       "why": "SMBs were not delivered in this period"})

    max_iob = settings.get("max_iob")
    if max_iob is not None and float(max_iob) > 0:
        current_iob = float(max_iob)
        # The other values are rounded to 0.1 U; the current one is not, or "no change" would
        # quietly move max IOB by up to 0.05 U. On 9 October that rounding alone moved one
        # simulated subject's month by 0.3 points of time below 54.
        values = sorted({round(current_iob * k, 1) for k in SCALES if k != 1.0} | {current_iob})
        chosen["max_iob"] = stage(
            "Max IOB", "max IOB", "all", values,
            lambda v: scen(max_iob=v), current_iob,
            lambda v: f"{v:g} U" + (" (current)" if v == current_iob else ""),
            more_insulin=lambda v: v > current_iob)
    else:
        stages.append({"name": "Max IOB", "lever": "max IOB", "measured_on": "all", "rows": [],
                       "chosen": max_iob, "chosen_label": "not tested",
                       "why": "max IOB is zero or unknown"})

    final = run([scen()])[0]
    return {
        "goals": {"tir_gt_pct": GOAL_TIR_PCT, "tbr_lt_pct": GOAL_TBR_PCT,
                  "strengthen_tbr70_lt_pct": STRENGTHEN_TBR70_MAX,
                  "strengthen_tbr54_lt_pct": STRENGTHEN_TBR54_MAX},
        "cycles": len(requests),
        "days": round(days, 1),
        "segment_hours": {k: observed[k]["hours"] for k in ("fasting", "correction", "meal")},
        "observed": observed,
        "stages": stages,
        "chosen": chosen,
        "final": {"est_all": _metrics(ts, final["shifted"], masks["all"], step_min),
                  "du_per_day": final["du_per_day"], "mean_shift": final["mean_shift"]},
        "caveat": CAVEAT,
    }
