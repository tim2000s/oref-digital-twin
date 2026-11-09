"""Step 1 of RESPONSE_PLAN.md: the twin's estimate of two choices under three simulator arms.

For each subject-condition where the weak-fix run and the comparison run chose differently, the
learning fortnight is regenerated, the replay inputs the twin builds from it are captured, and both
choices are estimated with and without the decay of DECAY.md. The outcomes they are set against
come from the two result files.

    ~/.venvs/boost-insilico/bin/python validation/response_check.py --workers 7
"""
import argparse
import json
import os
import random
import statistics as st
import sys
import time
import uuid
from concurrent.futures import ProcessPoolExecutor

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import timsim_roundtrip as T  # noqa: E402

STORE = os.path.join(HERE, "results", "titrated_2026-10-09.json")
NEW = os.path.join(HERE, "results", "bad_profiles_2026-11-08-weakfix.json")
OLD = os.path.join(HERE, "results", "bad_profiles_2026-11-08-fix.json")
ARMS = {"page": {"rescue": True, "decay": 0}, "decay": {"rescue": True, "decay": 144},
        "decay_no_rescue": {"rescue": False, "decay": 144}}


class _Captured(Exception):
    pass


def scenario(chosen, treatments):
    from replay.scenarios import meal_bolus_doses
    sc = {k: chosen[k] for k in ("basal_scale", "isf_scale", "cr_scale", "target_offset")}
    sc["extra_doses"] = meal_bolus_doses(treatments, chosen["cr_scale"])
    ps = {}
    if chosen.get("smb_minutes") is not None:
        ps.update(maxSMBBasalMinutes=chosen["smb_minutes"], maxUAMSMBBasalMinutes=chosen["smb_minutes"])
    if chosen.get("max_iob") is not None:
        ps["max_iob"] = chosen["max_iob"]
    if ps:
        sc["profile_set"] = ps
    return sc


def one(job):
    name, condition, choices = job
    T._paths()
    from replay import OrefOracle
    from replay.scenarios import RESCUE, _interp, _metrics
    from report import browser
    from timsim.therapy import titrate

    rec = json.load(open(STORE))["subjects"][name]
    titrated = titrate._profile(name, rec["scale"],
                                1.0 if rec.get("basal_scale") is None else rec["basal_scale"])
    p0 = T.mis_set(titrated, condition)
    learn, sugg = T.run_timsim(name, p0, T.LEARN_DAYS, T.LEARN_SEED)
    oracle = OrefOracle()
    browser.build_report(T.to_nightscout(learn, sugg, p0), oref_runner=oracle._runner,
                         settings=T.twin_settings(p0))
    got = {}

    def capture(payload):
        got["cycles"] = payload["cycles"]
        raise _Captured

    try:
        browser.settings_tests(sim_runner=capture, aim="tighter")
    except _Captured:
        pass
    pull = browser._LAST["pull"]
    pts = [r for r in pull.entries if r.sgv_mgdl is not None]
    ts, obs = [r.ts_ms for r in pts], [float(r.sgv_mgdl) for r in pts]
    gaps = sorted(b - a for a, b in zip(ts, ts[1:]) if b > a)
    step = gaps[len(gaps) // 2] / 60_000
    days = (ts[-1] - ts[0]) / 86_400_000
    out = {}
    for arm, opt in ARMS.items():
        payload = {"cycles": got["cycles"], "cache_key": uuid.uuid4().hex,
                   "scenarios": [scenario(c, pull.treatments) for c in choices]}
        if opt["rescue"]:
            payload["rescue"] = RESCUE
        if opt["decay"]:
            payload["decay_tau_min"] = opt["decay"]
        sim = oracle.simulate(payload)
        res = []
        for r in sim["scenarios"]:
            dbg = [d if d is not None else 0.0 for d in r["dbg"]]
            shifted = [g + _interp(sim["t"], dbg, t) for t, g in zip(ts, obs)]
            m = _metrics(ts, shifted, [True] * len(ts), step)
            m["du_per_day"] = round(sum(d for d in r["du"] if d is not None) / days, 2)
            m["mean"] = sum(shifted) / len(shifted)
            res.append(m)
        out[arm] = res
    oracle._simulator.close()
    return {"name": name, "condition": condition, "arms": out}


def spearman_ci(x, y, n_boot=10_000, seed=0):
    def rho(a, b):
        rank = lambda v: {i: r for r, i in enumerate(sorted(range(len(v)), key=v.__getitem__))}
        ra, rb = rank(a), rank(b)
        return st.correlation([ra[i] for i in range(len(a))], [rb[i] for i in range(len(b))])
    rng = random.Random(seed)
    boots = []
    for _ in range(n_boot):
        idx = [rng.randrange(len(x)) for _ in x]
        try:
            boots.append(rho([x[i] for i in idx], [y[i] for i in idx]))
        except st.StatisticsError:
            pass
    boots.sort()
    return rho(x, y), boots[int(0.025 * len(boots))], boots[int(0.975 * len(boots)) - 1]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=7)
    ap.add_argument("--out", default=os.path.join(HERE, "results", "response_check_2026-11-09.json"))
    a = ap.parse_args()
    L = lambda p: {(r["name"], r["condition"]): r for r in json.load(open(p))["rows"] if "error" not in r}
    new, old = L(NEW), L(OLD)
    keys = sorted(k for k in new if k in old and new[k]["chosen"] != old[k]["chosen"])
    jobs = [(n, c, [new[(n, c)]["chosen"], old[(n, c)]["chosen"]]) for n, c in keys]
    t0 = time.time()
    with ProcessPoolExecutor(a.workers) as ex:
        rows = list(ex.map(one, jobs))
    json.dump({"rows": rows, "seconds": round(time.time() - t0, 1)}, open(a.out, "w"), indent=1)
    print(f"{len(rows)} cases in {time.time() - t0:.0f}s")

    # the page arm must reproduce what both runs stored
    bad = 0
    for r in rows:
        k = (r["name"], r["condition"])
        for got, run in zip(r["arms"]["page"], (new[k], old[k])):
            want = run["twin_estimate"]["est_all"]
            if any(got[m] != want[m] for m in ("tir", "tbr", "tbr54")):
                bad += 1
                print("mismatch", k, {m: (got[m], want[m]) for m in ("tir", "tbr", "tbr54")})
    print(f"page arm reproduces stored estimates: {2 * len(rows) - bad} of {2 * len(rows)}")

    ev = lambda k, m: new[k]["eval_twin"]["cgm"][m] - old[k]["eval_twin"]["cgm"][m]
    for arm in ARMS:
        print(f"\n{arm}")
        for lab, em, rm in (("time in range", "tir", "tir"), ("below 70", "tbr", "tbr70"),
                            ("below 54", "tbr54", "tbr54"), ("mean glucose", "mean", "mean")):
            e = [r["arms"][arm][0][em] - r["arms"][arm][1][em] for r in rows]
            o = [ev((r["name"], r["condition"]), rm) for r in rows]
            rho, lo, hi = spearman_ci(e, o)
            sign = sum((a > 0) == (b > 0) for a, b in zip(e, o))
            print(f"  {lab}: estimated {st.median(e):+.2f}, realised {st.median(o):+.2f}; "
                  f"Spearman {rho:.2f} [{lo:.2f}, {hi:.2f}]; same sign {sign} of {len(e)}")
        e = [r["arms"][arm][0]["du_per_day"] - r["arms"][arm][1]["du_per_day"] for r in rows]
        o = [new[(r["name"], r["condition"])]["eval_twin"]["insulin_u_per_day"]
             - old[(r["name"], r["condition"])]["eval_twin"]["insulin_u_per_day"] for r in rows]
        print(f"  insulin: estimated {st.median(e):+.2f}, realised {st.median(o):+.2f} U/day")


if __name__ == "__main__":
    main()
