"""Round trip through TimSim: does the twin's suggested profile improve a simulated person?

For each subject:

  1. titrate the subject's settings with TimSim's own procedure (its reference loop, 28 days,
     TimSim's titration seed), which is the starting profile TimSim requires of any benchmark;
  2. run 14 days under TimSim's oref0 SMB controller with that profile (the learning run),
     and export it as the Nightscout data the twin reads;
  3. run the twin's settings tests on those 14 days, passing max IOB, the SMB limits, the
     insulin curve and max basal as a settings file would;
  4. apply the twin's choices to the profile;
  5. run a fresh 28 days on TimSim's benchmark seed twice, once with the starting profile and
     once with the twin's, and compare the two on the same glucose statistics.

The evaluation days are never seen by the twin, and both evaluation arms share a seed, so the
same meals, sensor noise and sensitivity drift fall on both and the difference is the profile.

TimSim's titrated-settings store is not used or written: titration here is saved to its own
file under validation/results, so this run cannot disturb other TimSim work.

Run with the TimSim environment, from anywhere:

    ~/.venvs/boost-insilico/bin/python validation/timsim_roundtrip.py --subjects 12 --workers 7

TimSim is found at $TIMSIM or ~/StudioProjects/TimSim.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from dataclasses import replace
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
TWIN = os.path.dirname(HERE)
TIMSIM = os.environ.get("TIMSIM", os.path.expanduser("~/StudioProjects/TimSim"))
RESULTS = os.path.join(HERE, "results")

LEARN_DAYS = 14
EVAL_DAYS = 28
LEARN_SEED = 202          # distinct from TimSim's titration (11) and benchmark (101) seeds
SAMPLE_MIN = 5


def _paths():
    for p in (TWIN, TIMSIM):
        if p not in sys.path:
            sys.path.insert(0, p)


# ----------------------------------------------------------------------------- TimSim side

class SettableOref:
    """TimSim's OrefController with the SMB limits taken from the profile under test.

    TimSim fixes maxSMBBasalMinutes at 75 and maxUAMSMBBasalMinutes at 45. The twin can
    suggest a different SMB limit, so the evaluation arm has to be able to run it.
    """

    @staticmethod
    def make(name, profile, smb_minutes=None):
        _paths()
        from timsim.controller import inputs as INP
        from timsim.controller import oref as O
        from timsim.therapy import insulin as INS

        # TimSim's oref adapter pruned its insulin ledger an hour early and used a curve
        # AndroidAPS does not (TimSim issue 54, fixed in f0e5e45). The 9 October run applied
        # both corrections here; with the fix in TimSim they are refused rather than repeated.
        if INP.iob_fraction is not getattr(INS, "oref_iob_fraction", None):
            raise RuntimeError("TimSim predates its issue 54 fix (f0e5e45); update it first")

        class _C(O.OrefController):
            def _static_profile(self):
                p = super()._static_profile()
                if smb_minutes is not None:
                    p["maxSMBBasalMinutes"] = float(smb_minutes)
                    p["maxUAMSMBBasalMinutes"] = float(smb_minutes)
                return p

        return _C(name, profile=profile)


def run_timsim(name, profile, days, seed, smb_minutes=None):
    _paths()
    from timsim import simulate

    c = SettableOref.make(name, profile, smb_minutes)
    try:
        r = simulate(name, days=days, seed=seed, controller=c, profile=profile)
        return r, list(c.suggestions)
    finally:
        c.close()


def _iso(ms: int) -> str:
    return datetime.fromtimestamp(ms / 1000, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z")


def to_nightscout(result, suggestions, profile) -> dict:
    """A TimSim run as the raw Nightscout JSON the twin's build_report takes.

    entries: the sensor reading at each step. devicestatus: oref's own result for that step,
    as both suggested and enacted. treatments: the basal actually delivered in each step as a
    5-minute absolute temp, each SMB as an AAPS 3 SMB, and each announced meal's carbohydrate.
    Rescue carbohydrate is left out, as most people do not log it.
    """
    _paths()
    from timsim.controller.oref import EPOCH_MS

    import numpy as np

    mins = np.asarray(result.minutes, float)
    cgm = np.asarray(result.cgm, float)
    ins = np.asarray(result.insulin_series, float)
    bol = np.asarray(result.bolus_series, float)
    if not (len(mins) == len(cgm) == len(ins) == len(bol) == len(suggestions)):
        raise ValueError(f"misaligned run: {len(mins)} {len(cgm)} {len(ins)} {len(bol)} "
                         f"{len(suggestions)}")
    t = lambda m: int(EPOCH_MS + m * 60_000)
    entries = [{"_id": f"e{i}", "date": t(m), "sgv": int(round(g)), "type": "sgv",
                "direction": "Flat", "device": "timsim"} for i, (m, g) in enumerate(zip(mins, cgm))]
    ds, tr = [], []
    for i, (m, s) in enumerate(zip(mins, suggestions)):
        rt = dict(s)
        rt["bg"] = int(round(cgm[i]))
        rt["timestamp"] = _iso(t(m))
        ds.append({"_id": f"d{i}", "created_at": _iso(t(m)), "device": "openaps://timsim",
                   "openaps": {"iob": {"iob": s.get("IOB"), "time": _iso(t(m))},
                               "suggested": rt, "enacted": {**rt, "received": True}}})
        # the step's insulin is delivered over the step that ends at minute m
        start = t(m - SAMPLE_MIN)
        if bol[i] > 0:
            tr.append({"_id": f"b{i}", "created_at": _iso(start), "eventType": "Correction Bolus",
                       "insulin": round(float(bol[i]), 3), "type": "SMB", "isSMB": True})
    # Basal as temps: consecutive steps at the same rate become one record, as a pump
    # uploads them. oref0's lib/iob rounds each temp's difference from schedule to whole
    # 0.05 U pulses, so a record per 5-minute step loses every small difference.
    rates = [round(max(float(ins[i] - bol[i]), 0.0) * 60.0 / SAMPLE_MIN, 3) for i in range(len(mins))]
    i = 0
    while i < len(rates):
        j = i
        while j + 1 < len(rates) and rates[j + 1] == rates[i] and (j + 1 - i) * SAMPLE_MIN < 120:
            j += 1
        tr.append({"_id": f"tb{i}", "created_at": _iso(t(mins[i] - SAMPLE_MIN)),
                   "eventType": "Temp Basal", "absolute": rates[i], "rate": rates[i],
                   "duration": (j - i + 1) * SAMPLE_MIN})
        i = j + 1
    for j, rec in enumerate(result.announced_log):
        minute, _eaten, announced = rec
        if announced and announced > 0:
            tr.append({"_id": f"c{j}", "created_at": _iso(t(minute)),
                       "eventType": "Carb Correction", "carbs": round(float(announced), 1)})
    hours = lambda arr: [{"time": f"{h:02d}:00", "timeAsSeconds": h * 3600,
                          "value": round(float(v), 4)} for h, v in enumerate(arr)]
    prof = {"_id": "p1", "defaultProfile": "TimSim", "startDate": _iso(EPOCH_MS),
            "store": {"TimSim": {
                "dia": float(profile.dia_min) / 60.0, "units": "mg/dl", "timezone": "UTC",
                "basal": hours(profile.basal_u_per_hour), "sens": hours(profile.isf),
                "carbratio": hours(profile.cr),
                "target_low": [{"time": "00:00", "timeAsSeconds": 0, "value": float(profile.target_lo)}],
                "target_high": [{"time": "00:00", "timeAsSeconds": 0, "value": float(profile.target_hi)}],
            }}}
    return {"base_url": "timsim", "start_ms": t(0), "end_ms": t(float(mins[-1])),
            "entries": entries, "treatments": tr, "devicestatus": ds, "profiles": [prof]}


def twin_settings(profile, smb_minutes=75, uam_minutes=45):
    """What a settings-file upload would give the twin for TimSim's oref controller."""
    lim = profile.limits
    return {"max_iob": float(lim.max_iob_u), "max_basal": float(lim.max_basal_u_per_hour),
            "enable_smb": True, "max_smb_minutes": smb_minutes, "max_uam_minutes": uam_minutes,
            "insulin_curve": "rapid-acting", "insulin_peak_min": float(lim.peak_min)}


def apply_choices(profile, chosen):
    """The twin's choices applied to a TimSim profile. Max basal and max bolus are unchanged."""
    lim = replace(profile.limits, max_iob_u=float(chosen.get("max_iob", profile.limits.max_iob_u)))
    off = float(chosen.get("target_offset", 0))
    return replace(profile,
                   basal_u_per_hour=profile.basal_u_per_hour * float(chosen["basal_scale"]),
                   isf=profile.isf * float(chosen["isf_scale"]),
                   cr=profile.cr * float(chosen["cr_scale"]),
                   target_lo=profile.target_lo + off, target_hi=profile.target_hi + off,
                   limits=lim)


def outcomes(result) -> dict:
    """One function for both arms: sensor (cgm) and true glucose (bg) bands, in percent."""
    import numpy as np

    out = {}
    for sig in ("cgm", "bg"):
        v = np.asarray(getattr(result, sig), float)
        out[sig] = {"tir": float(100 * np.mean((v >= 70) & (v <= 180))),
                    "tbr70": float(100 * np.mean(v < 70)), "tbr54": float(100 * np.mean(v < 54)),
                    "tar180": float(100 * np.mean(v > 180)), "tar250": float(100 * np.mean(v > 250)),
                    "mean": float(v.mean())}
    out["insulin_u_per_day"] = float(result.insulin_units) / max(result.days_requested, 1)
    out["rescue_events"] = int(result.rescue_events)
    out["completed"] = bool(result.completed)
    return out


# ------------------------------------------------------------------------------- workers

def titrate_one(job):
    name, days, seed = job
    _paths()
    from timsim.therapy import titrate
    try:
        return titrate.titrate_subject(name, days=days, seed=seed)
    except titrate.TitrationError as exc:
        return {"name": name, "found": False, "fatal": True, "error": str(exc)[:300], "trace": []}


def roundtrip_one(job):
    name, store, eval_seed = job
    _paths()
    from replay import OrefOracle
    from report.browser import build_report, settings_tests
    from timsim.therapy import titrate

    t0 = time.time()
    p0 = titrate.profile_for(name, path=store)
    learn, sugg = run_timsim(name, p0, LEARN_DAYS, LEARN_SEED)
    raw = to_nightscout(learn, sugg, p0)
    oracle = OrefOracle()
    rep = build_report(raw, oref_runner=oracle._runner, settings=twin_settings(p0))
    tests = settings_tests(sim_runner=oracle.simulate)
    oracle._simulator.close()
    if "skipped" in tests:
        return {"name": name, "error": tests["skipped"]}
    chosen = tests["result"]["chosen"]
    p1 = apply_choices(p0, chosen)
    smb1 = chosen.get("smb_minutes")
    e0, _ = run_timsim(name, p0, EVAL_DAYS, eval_seed)
    e1, _ = run_timsim(name, p1, EVAL_DAYS, eval_seed,
                       smb_minutes=None if smb1 in (None, 75) else smb1)
    return {
        "name": name, "seconds": round(time.time() - t0, 1),
        "profile0": {"basal_u_per_day": float(p0.basal_u_per_hour.sum()),
                     "isf_mean": float(p0.isf.mean()), "cr_mean": float(p0.cr.mean()),
                     "target": [p0.target_lo, p0.target_hi], "max_iob": p0.limits.max_iob_u},
        "chosen": chosen,
        "twin_estimate": tests["result"]["final"],
        "twin_observed": tests["result"]["observed"]["all"],
        "learn": outcomes(learn),
        "eval_start": outcomes(e0),
        "eval_twin": outcomes(e1),
        "report_md": rep["report_md"] + "\n\n" + tests["report_md"],
    }


# ---------------------------------------------------------------------------------- main

def summarise(rows, arm, sig, key):
    import numpy as np
    v = np.array([r[arm][sig][key] for r in rows])
    return {"median": float(np.median(v)), "mean": float(v.mean()),
            "min": float(v.min()), "max": float(v.max())}


def paired(rows, sig, key, n_boot=10_000, seed=0):
    """Median and mean of twin minus start, with a bootstrap 95% interval on each."""
    import numpy as np
    d = np.array([r["eval_twin"][sig][key] - r["eval_start"][sig][key] for r in rows])
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, len(d), size=(n_boot, len(d)))
    med = np.median(d[idx], axis=1)
    mean = d[idx].mean(axis=1)
    return {"median": float(np.median(d)), "median_ci": [float(np.percentile(med, 2.5)), float(np.percentile(med, 97.5))],
            "mean": float(d.mean()), "mean_ci": [float(np.percentile(mean, 2.5)), float(np.percentile(mean, 97.5))],
            "improved": int((d > 0).sum()) if key == "tir" else int((d < 0).sum()), "n": len(d)}


def main():
    _paths()
    ap = argparse.ArgumentParser()
    ap.add_argument("--subjects", type=int, default=12)
    ap.add_argument("--workers", type=int, default=7)
    ap.add_argument("--titration-days", type=int, default=28)
    ap.add_argument("--tag", default=datetime.now().strftime("%Y-%m-%d"))
    a = ap.parse_args()

    from timsim import seeds
    from timsim.population import names
    from timsim.therapy import titrate

    os.makedirs(RESULTS, exist_ok=True)
    store = os.path.join(RESULTS, f"titrated_{a.tag}.json")
    subjects = list(names("adult"))[: a.subjects]
    t0 = time.time()
    if not os.path.exists(store):
        with ProcessPoolExecutor(a.workers) as ex:
            tit = list(ex.map(titrate_one, [(n, a.titration_days, seeds.TITRATION) for n in subjects]))
        titrate.save(tit, path=store, meta={"by": "oref-digital-twin validation/timsim_roundtrip.py"})
        print(f"titrated {sum(r.get('found', False) for r in tit)}/{len(tit)} in {time.time()-t0:.0f}s", flush=True)
    ok = [n for n, r in json.load(open(store))["subjects"].items() if r.get("found")]

    with ProcessPoolExecutor(a.workers) as ex:
        rows = list(ex.map(roundtrip_one, [(n, store, seeds.BENCH) for n in ok]))
    good = [r for r in rows if "error" not in r]

    os.makedirs(os.path.join(RESULTS, f"reports_{a.tag}"), exist_ok=True)
    for r in good:
        with open(os.path.join(RESULTS, f"reports_{a.tag}", r["name"].replace("#", "_") + ".md"), "w") as fh:
            fh.write(r.pop("report_md"))
    summary = {
        "design": {"learn_days": LEARN_DAYS, "learn_seed": LEARN_SEED, "eval_days": EVAL_DAYS,
                   "eval_seed": seeds.BENCH, "titration_seed": seeds.TITRATION,
                   "titration_days": a.titration_days, "subjects_requested": subjects,
                   "subjects_titrated": ok, "subjects_failed": [r for r in rows if "error" in r]},
        "outcomes": {arm: {sig: {k: summarise(good, arm, sig, k)
                                 for k in ("tir", "tbr70", "tbr54", "tar180", "mean")}
                           for sig in ("cgm", "bg")} for arm in ("eval_start", "eval_twin")},
        "paired_twin_minus_start": {sig: {k: paired(good, sig, k)
                                          for k in ("tir", "tbr70", "tbr54", "tar180", "mean")}
                                    for sig in ("cgm", "bg")},
        "subjects": good,
        "seconds": round(time.time() - t0, 1),
    }
    out = os.path.join(RESULTS, f"timsim_roundtrip_{a.tag}.json")
    with open(out, "w") as fh:
        json.dump(summary, fh, indent=1, default=float)
    print(f"wrote {out} ({len(good)} subjects, {time.time()-t0:.0f}s)", flush=True)


if __name__ == "__main__":
    main()
