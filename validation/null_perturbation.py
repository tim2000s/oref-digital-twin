"""How much does an inconsequential profile change move a subject's month? The noise floor.

Added after the mis-set run of 9 October 2026 had been seen (BAD_PROFILES.md says so): in three
of its harm cases the twin's profile differed from the start only by max IOB rounded up to
0.1 U, and TimSim, which is deterministic, gave a different month. This reruns every mis-set
profile of that run with max IOB 0.03 U higher, on the same seed, and compares each with the
mis-set arm already recorded there, so the twin's per-subject changes can be read against the
changes a meaningless difference produces.

    ~/.venvs/boost-insilico/bin/python validation/null_perturbation.py \
        validation/results/bad_profiles_2026-10-09.json --workers 7
"""
import argparse
import json
import os
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from dataclasses import replace

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import timsim_roundtrip as T  # noqa: E402

BUMP_U = 0.03


def one(job):
    name, condition, store, days, seed = job
    T._paths()
    from timsim.therapy import titrate
    rec = json.load(open(store))["subjects"][name]
    p = T.mis_set(titrate._profile(name, rec["scale"],
                                   1.0 if rec.get("basal_scale") is None else rec["basal_scale"]),
                  condition)
    p = replace(p, limits=replace(p.limits, max_iob_u=p.limits.max_iob_u + BUMP_U))
    r, _ = T.run_timsim(name, p, days, seed)
    return {"name": name, "condition": condition, "perturbed": T.outcomes(r)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("bad_profiles")
    ap.add_argument("--workers", type=int, default=7)
    a = ap.parse_args()
    d = json.load(open(a.bad_profiles))
    store = os.path.join(T.TWIN, d["design"]["store"])
    jobs = [(r["name"], r["condition"], store, d["design"]["eval_days"], d["design"]["eval_seed"])
            for r in d["rows"]]
    t0 = time.time()
    with ProcessPoolExecutor(a.workers) as ex:
        rows = list(ex.map(one, jobs))
    base = {(r["name"], r["condition"]): r["eval_start"] for r in d["rows"]}
    for r in rows:
        r["start"] = base[(r["name"], r["condition"])]
    out = a.bad_profiles.replace("bad_profiles_", "null_perturbation_")
    with open(out, "w") as fh:
        json.dump({"bump_max_iob_u": BUMP_U, "source": os.path.basename(a.bad_profiles),
                   "rows": rows, "seconds": round(time.time() - t0, 1)}, fh, indent=1)
    print(f"wrote {out} in {time.time() - t0:.0f}s")


if __name__ == "__main__":
    main()
