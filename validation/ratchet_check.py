"""Same-fortnight check of the repeated strengthening over reviews (RATCHET_PLAN.md).

For each row of a three-review run and each review, TimSim runs the profile the review was given
and the profile it left on the same learning seed; the page's settings tests then re-review the
second run, and the decayed twin reviews both. The rule the re-review uses is whatever this
checkout's replay/scenarios.py holds, so run it from the checkout that made the run.

    ~/.venvs/boost-insilico/bin/python validation/ratchet_check.py \
        validation/results/bad_profiles_2026-11-09-stepA.json --workers 7
    ~/.venvs/boost-insilico/bin/python validation/ratchet_check.py --summarise results/ratchet_<tag>.json
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from concurrent.futures import ProcessPoolExecutor, as_completed

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import timsim_roundtrip as T  # noqa: E402

DECAY_MIN = 144
KEYS = ("tir", "tbr70", "tbr54", "mean")
TOWARDS_MORE = {"basal_scale": (1.0, +1), "isf_scale": (1.0, -1), "cr_scale": (1.0, -1),
                "target_offset": (0.0, -1)}


def direction(c):
    """'more', 'less', 'mixed' or 'none' insulin for a set of choices."""
    signs = {1 if s * (float(c.get(k, base)) - base) > 0 else -1
             for k, (base, s) in TOWARDS_MORE.items() if abs(float(c.get(k, base)) - base) > 1e-9}
    return {frozenset(): "none", frozenset({1}): "more", frozenset({-1}): "less"}.get(
        frozenset(signs), "mixed")


def review(run, sugg, prof, smb_run, aim, decay):
    T._paths()
    from replay import OrefOracle
    from report.browser import build_report, settings_tests

    oracle = OrefOracle()
    build_report(T.to_nightscout(run, sugg, prof), oref_runner=oracle._runner,
                 settings=T.twin_settings(prof) if smb_run is None else
                 T.twin_settings(prof, smb_minutes=smb_run, uam_minutes=smb_run))
    sim = oracle.simulate if not decay else (lambda p: oracle.simulate({**p, "decay_tau_min": decay}))
    tests = settings_tests(sim_runner=sim, aim=aim)
    oracle._simulator.close()
    if "skipped" in tests:
        return {"skipped": tests["skipped"]}
    res = tests["result"]
    return {"chosen": res["chosen"], "direction": direction(res["chosen"]),
            "final": res["final"], "observed": res["observed"]["all"]}


def daily(run):
    import numpy as np
    day = (np.asarray(run.minutes, float) // 1440).astype(int)
    cgm, ins = np.asarray(run.cgm, float), np.asarray(run.insulin_series, float)
    days = range(int(day.max()) + 1)
    return ([float(cgm[day == d].mean()) for d in days], [float(ins[day == d].sum()) for d in days])


def one(job):
    name, condition, reviews, store, aim, learn_days = job
    T._paths()
    from timsim.therapy import titrate

    t0 = time.time()
    rec = json.load(open(store))["subjects"][name]
    titrated = titrate._profile(name, rec["scale"],
                                1.0 if rec.get("basal_scale") is None else rec["basal_scale"])
    p, smb, out = T.mis_set(titrated, condition), None, []
    for r, rv in enumerate(reviews):
        c, seed = rv["chosen"], T.LEARN_SEED + r
        smb_base = None if smb in (None, 75) else smb
        pn, smb_n = T.apply_choices(p, c), c.get("smb_minutes", smb)
        smb_next = None if smb_n in (None, 75) else smb_n
        base, sb = T.run_timsim(name, p, learn_days, seed, smb_minutes=smb_base)
        nxt, sn = T.run_timsim(name, pn, learn_days, seed, smb_minutes=smb_next)
        ob, on = T.outcomes(base), T.outcomes(nxt)
        stored = rv["learn"]
        repro = (all(abs(ob["cgm"][k] - stored["cgm"][k]) < 1e-9 for k in KEYS)
                 and abs(ob["insulin_u_per_day"] - stored["insulin_u_per_day"]) < 1e-9)
        (gb, ib), (gn, inn) = daily(base), daily(nxt)
        out.append({
            "review": r + 1, "seed": seed, "reproduced": repro,
            "original": {"chosen": c, "direction": direction(c), "final": rv["twin_estimate"]},
            "base": ob, "next": on,
            "daily_mean_diff": [b - a for a, b in zip(gb, gn)],
            "daily_insulin_diff": [b - a for a, b in zip(ib, inn)],
            "page_next": review(nxt, sn, pn, smb_next, aim, 0),
            "decay_base": review(base, sb, p, smb_base, aim, DECAY_MIN),
            "decay_next": review(nxt, sn, pn, smb_next, aim, DECAY_MIN),
        })
        p, smb = pn, smb_n
    return {"name": name, "condition": condition, "seconds": round(time.time() - t0, 1), "cases": out}


# ------------------------------------------------------------------------------- summary

def _boot(rows, stat, n_boot=10_000, seed=0):
    """Point and 95% interval of stat(rows), resampling subjects."""
    import numpy as np
    by = {}
    for x in rows:
        by.setdefault(x["name"], []).append(x)
    names = sorted(by)
    rng = np.random.default_rng(seed)
    vals = []
    for _ in range(n_boot):
        pick = [x for i in rng.integers(0, len(names), len(names)) for x in by[names[i]]]
        v = stat(pick)
        if v is not None:
            vals.append(v)
    if not vals:
        return stat(rows), None
    return stat(rows), [float(np.percentile(vals, 2.5)), float(np.percentile(vals, 97.5))]


def summarise(path):
    import numpy as np
    d = json.load(open(path))
    cases = [{**c, "name": row["name"], "condition": row["condition"]}
             for row in d["rows"] for c in row["cases"]]
    bad = [(c["name"], c["condition"], c["review"]) for c in cases if not c["reproduced"]]
    if bad:
        sys.exit(f"base runs did not reproduce the stored learning outcomes: {bad[:5]} ({len(bad)})")
    ok = lambda c, k: "skipped" not in c[k]
    out = {"n_cases": len(cases), "by_review": {}}
    for r in (1, 2, 3):
        cs = [c for c in cases if c["review"] == r]
        out["by_review"][r] = {
            "original_more": sum(c["original"]["direction"] == "more" for c in cs),
            "page_next_more": sum(ok(c, "page_next") and c["page_next"]["direction"] == "more" for c in cs),
            "n": len(cs)}

    more = [c for c in cases if c["original"]["direction"] == "more" and ok(c, "page_next")]
    rate = lambda cs: (sum(c["page_next"]["direction"] == "more" for c in cs) / len(cs)) if cs else None
    out["page_repeat"] = {"n": len(more), "repeat": sum(c["page_next"]["direction"] == "more" for c in more)}
    out["page_repeat"]["rate"], out["page_repeat"]["ci"] = _boot(more, rate)

    dm = [c for c in cases if ok(c, "decay_base") and ok(c, "decay_next")
          and c["decay_base"]["direction"] == "more"]
    drate = lambda cs: (sum(c["decay_next"]["direction"] == "more" for c in cs) / len(cs)) if cs else None
    out["decay_repeat"] = {"n": len(dm), "repeat": sum(c["decay_next"]["direction"] == "more" for c in dm)}
    out["decay_repeat"]["rate"], out["decay_repeat"]["ci"] = _boot(dm, drate)
    both = [{**c, "_p": c in more, "_d": c in dm} for c in cases]
    out["decay_minus_page"] = _boot(both, lambda cs: (drate([c for c in cs if c["_d"]]) - rate([c for c in cs if c["_p"]]))
                                    if any(c["_d"] for c in cs) and any(c["_p"] for c in cs) else None)

    # mg/dL of mean glucose lost per extra U/day, realised on the same seed and estimated
    rs = [c for c in cases if c["original"]["direction"] == "more"
          and c["next"]["insulin_u_per_day"] - c["base"]["insulin_u_per_day"] > 0.2
          and c["original"]["final"]["du_per_day"] > 0.2]
    real = lambda c: -(c["next"]["cgm"]["mean"] - c["base"]["cgm"]["mean"]) / (
        c["next"]["insulin_u_per_day"] - c["base"]["insulin_u_per_day"])
    est = lambda c: -c["original"]["final"]["mean_shift"] / c["original"]["final"]["du_per_day"]
    med = lambda f: (lambda cs: float(np.median([f(c) for c in cs])) if cs else None)
    out["per_unit"] = {"n": len(rs), "realised": _boot(rs, med(real)), "estimated": _boot(rs, med(est)),
                       "difference": _boot(rs, lambda cs: med(real)(cs) - med(est)(cs) if cs else None)}

    # the same-seed differences, every case where review r chose more insulin
    mo = [c for c in cases if c["original"]["direction"] == "more"]
    out["same_seed_more"] = {"n": len(mo), **{
        k: float(np.median([c["next"]["cgm"][k] - c["base"]["cgm"][k] for c in mo])) for k in KEYS},
        "insulin_u_per_day": float(np.median([c["next"]["insulin_u_per_day"] - c["base"]["insulin_u_per_day"] for c in mo])),
        "estimated_du": float(np.median([c["original"]["final"]["du_per_day"] for c in mo])),
        "estimated_mean_shift": float(np.median([c["original"]["final"]["mean_shift"] for c in mo])),
        "daily_mean_diff": [float(np.median([c["daily_mean_diff"][i] for c in mo]))
                            for i in range(len(mo[0]["daily_mean_diff"]))] if mo else []}

    p, dd = out["page_repeat"], out["per_unit"]
    out["verdict"] = {
        "page_repeats_in_half": p["rate"] is not None and p["rate"] >= 0.5,
        "realised_below_estimated": (dd["realised"][0] is not None and dd["realised"][0] < dd["estimated"][0]
                                     and dd["difference"][1] is not None and dd["difference"][1][1] < 0)}
    out["verdict"]["ratchet_from_lasting_shift"] = all(out["verdict"].values())
    print(json.dumps(out, indent=1))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("run", nargs="?", help="a three-review bad_profiles_<tag>.json")
    ap.add_argument("--workers", type=int, default=7)
    ap.add_argument("--tag", default=None)
    ap.add_argument("--limit", type=int, default=None, help="first N rows only, for a smoke test")
    ap.add_argument("--summarise", help="a ratchet_<tag>.json to summarise")
    a = ap.parse_args()
    if a.summarise:
        summarise(a.summarise)
        return
    src = json.load(open(a.run))
    design = src["design"]
    store = os.path.join(T.TWIN, design["store"])
    rows = [r for r in src["rows"] if "reviews" in r][: a.limit]
    jobs = [(r["name"], r["condition"], r["reviews"], store, design["aim"], design["learn_days"])
            for r in rows]
    tag = a.tag or os.path.basename(a.run).removeprefix("bad_profiles_").removesuffix(".json")
    path = os.path.join(T.RESULTS, f"ratchet_{tag}.json")
    commit = subprocess.run(["git", "-C", T.TWIN, "rev-parse", "--short", "HEAD"],
                            capture_output=True, text=True).stdout.strip()
    t0, done, failed = time.time(), [], []
    with ProcessPoolExecutor(a.workers) as ex:
        futs = {ex.submit(one, j): j[:2] for j in jobs}
        for f in as_completed(futs):
            try:
                done.append(f.result())
                print(f"{len(done)}/{len(jobs)} {futs[f]} {done[-1]['seconds']} s", flush=True)
            except Exception as exc:  # one subject's crash is recorded, not fatal to the run
                failed.append({"job": futs[f], "error": repr(exc)[:300]})
                print(f"FAILED {futs[f]}: {exc!r}", flush=True)
    json.dump({"source": a.run, "commit": commit, "decay_tau_min": DECAY_MIN, "failed": failed,
               "seconds": round(time.time() - t0, 1), "rows": done}, open(path, "w"), indent=1)
    print(path)


if __name__ == "__main__":
    main()
