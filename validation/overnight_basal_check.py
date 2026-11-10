"""Does the overnight net-IOB rule point basal the right way? (BASAL_RULE_PLAN.md)

    ~/.venvs/boost-insilico/bin/python validation/overnight_basal_check.py --workers 4
    ~/.venvs/boost-insilico/bin/python validation/overnight_basal_check.py --summarise results/overnight_basal_<tag>.json
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from concurrent.futures import ProcessPoolExecutor

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import timsim_roundtrip as T  # noqa: E402

STORE = os.path.join(T.RESULTS, "titrated_2026-10-09.json")
TWIN_RUN = os.path.join(T.RESULTS, "bad_profiles_2026-11-09-stepA.json")
NIGHT = (0, 360)            # minutes after midnight
AFTER_CARBS_MIN = 300       # the insulin's duration of action
MIN_NIGHT_STEPS = 36        # 3 h of 5-minute steps
IOB_U = 0.1
SHARE = 0.6
MIN_NIGHTS = 7
TRUTH = {"basal_low": "up", "all_weak": "up", "basal_high": "down", "all_strong": "down"}


def nights(run, sugg, profile):
    import numpy as np
    mins = np.asarray(run.minutes, float)
    cgm = np.asarray(run.cgm, float)
    iob = np.array([float(s.get("IOB") or 0.0) for s in sugg])
    carbs = [m for m, _e, a in run.announced_log if a and a > 0]
    tod = mins % 1440
    fed = np.zeros(len(mins), bool)
    for m in carbs:
        fed |= (mins >= m) & (mins < m + AFTER_CARBS_MIN)
    target = (profile.target_lo + profile.target_hi) / 2
    out = []
    for d in range(int(mins.max() // 1440) + 1):
        k = (mins // 1440 == d) & (tod >= NIGHT[0]) & (tod < NIGHT[1]) & ~fed
        if k.sum() < MIN_NIGHT_STEPS:
            continue
        out.append({"day": d, "steps": int(k.sum()), "median_cgm": float(np.median(cgm[k])),
                    "mean_iob": float(iob[k].mean()), "target": float(target)})
    return out


def rule(ns, iob_u=IOB_U, share=SHARE, min_nights=MIN_NIGHTS):
    up = sum(n["median_cgm"] > n["target"] and n["mean_iob"] > iob_u for n in ns)
    down = sum(n["median_cgm"] < n["target"] and n["mean_iob"] < -iob_u for n in ns)
    if len(ns) < min_nights:
        return "hold"
    return "up" if up >= share * len(ns) else "down" if down >= share * len(ns) else "hold"


def one(job):
    name, condition = job
    T._paths()
    from timsim.therapy import titrate
    rec = json.load(open(STORE))["subjects"][name]
    titrated = titrate._profile(name, rec["scale"],
                                1.0 if rec.get("basal_scale") is None else rec["basal_scale"])
    p0 = T.mis_set(titrated, condition)
    r, s = T.run_timsim(name, p0, T.LEARN_DAYS, T.LEARN_SEED)
    return {"name": name, "condition": condition, "nights": nights(r, s, p0)}


def twin_dir(k):
    return "up" if k > 1 + 1e-9 else "down" if k < 1 - 1e-9 else "hold"


def summarise(path, **kw):
    d = json.load(open(path))
    twin = {}
    if os.path.exists(TWIN_RUN):
        twin = {(r["name"], r["condition"]): twin_dir(r["reviews"][0]["chosen"]["basal_scale"])
                for r in json.load(open(TWIN_RUN))["rows"]}
    rows = []
    for x in d["rows"]:
        truth = TRUTH.get(x["condition"], "hold")
        rows.append({"name": x["name"], "condition": x["condition"], "truth": truth,
                     "rule": rule(x["nights"], **kw), "twin": twin.get((x["name"], x["condition"])),
                     "nights": len(x["nights"])})
    out = {"thresholds": {"iob_u": IOB_U, "share": SHARE, "min_nights": MIN_NIGHTS, **kw}}
    for who in ("rule", "twin"):
        rs = [r for r in rows if r[who] is not None]
        wrong = [r for r in rs if r["truth"] != "hold"]
        right = [r for r in rs if r["truth"] == "hold"]
        out[who] = {
            "basal_wrong_n": len(wrong), "basal_wrong_right_direction": sum(r[who] == r["truth"] for r in wrong),
            "basal_right_n": len(right), "basal_right_held": sum(r[who] == "hold" for r in right),
            "opposite": sum(r[who] in ("up", "down") and r["truth"] in ("up", "down") and r[who] != r["truth"]
                            for r in rs),
            "by_condition": {c: {v: sum(r[who] == v for r in rs if r["condition"] == c) for v in ("up", "down", "hold")}
                             for c in sorted({r["condition"] for r in rs})}}
    r = out["rule"]
    out["verdict"] = {"right_direction_36_of_48": r["basal_wrong_right_direction"] >= 0.75 * r["basal_wrong_n"],
                      "holds_45_of_60": r["basal_right_held"] >= 0.75 * r["basal_right_n"]}
    out["nights_counted_median"] = sorted(x["nights"] for x in rows)[len(rows) // 2]
    print(json.dumps(out, indent=1))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--subjects", type=int, default=12)
    ap.add_argument("--tag", default=time.strftime("%Y-%m-%d"))
    ap.add_argument("--summarise")
    a = ap.parse_args()
    if a.summarise:
        summarise(a.summarise)
        return
    names = list(json.load(open(STORE))["subjects"])[: a.subjects]
    jobs = [(n, c) for c in T.CONDITIONS for n in names]
    t0 = time.time()
    with ProcessPoolExecutor(a.workers) as ex:
        rows = list(ex.map(one, jobs))
    path = os.path.join(T.RESULTS, f"overnight_basal_{a.tag}.json")
    json.dump({"store": os.path.relpath(STORE, T.TWIN), "seed": T.LEARN_SEED, "days": T.LEARN_DAYS,
               "seconds": round(time.time() - t0, 1), "rows": rows}, open(path, "w"), indent=1)
    print(path, f"{time.time() - t0:.0f} s")


if __name__ == "__main__":
    main()
