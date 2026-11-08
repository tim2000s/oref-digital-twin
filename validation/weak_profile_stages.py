"""Why the twin left too-weak ISF and basal alone: its stage tables on the weak conditions.

The fourth mis-set run (BAD_PROFILES_4.md, and the settings-fix rerun) showed the twin rarely
moving a too-weak ISF or basal back, and strengthening the carb ratio instead. This reruns the
learning fortnight and the twin for those subject-conditions, exactly as timsim_roundtrip.py
does, and keeps each stage's table: what each value was estimated to give, which values the
strengthening limit excluded, and which rule of `choose` picked the result. No evaluation runs.

    ~/.venvs/boost-insilico/bin/python validation/weak_profile_stages.py --workers 7
"""
import argparse
import json
import os
import sys
import time
from concurrent.futures import ProcessPoolExecutor

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import timsim_roundtrip as T  # noqa: E402

WEAK = ("isf_weak", "basal_low", "cr_weak", "all_weak")
STORE = os.path.join(HERE, "results", "titrated_2026-10-09.json")


def one(job):
    name, condition, aim = job
    T._paths()
    from replay import OrefOracle
    from report.browser import build_report, settings_tests
    from timsim.therapy import titrate

    rec = json.load(open(STORE))["subjects"][name]
    titrated = titrate._profile(name, rec["scale"],
                                1.0 if rec.get("basal_scale") is None else rec["basal_scale"])
    p0 = T.mis_set(titrated, condition)
    learn, sugg = T.run_timsim(name, p0, T.LEARN_DAYS, T.LEARN_SEED)
    raw = T.to_nightscout(learn, sugg, p0)
    oracle = OrefOracle()
    build_report(raw, oref_runner=oracle._runner, settings=T.twin_settings(p0))
    tests = settings_tests(sim_runner=oracle.simulate, aim=aim)
    oracle._simulator.close()
    if "skipped" in tests:
        return {"name": name, "condition": condition, "error": tests["skipped"]}
    keep = lambda m: {k: m.get(k) for k in ("hours", "tir", "tbr", "tbr54")}
    stages = [{"name": s["name"], "measured_on": s.get("measured_on"),
               "observed": keep(s.get("observed") or {}), "chosen": s.get("chosen"),
               "why": s.get("why"),
               "rows": [{"value": r["value"], "est": keep(r["est"]), "est_all": keep(r["est_all"]),
                         "more_insulin": r["more_insulin"], "excluded": r["excluded"]}
                        for r in s.get("rows", [])]}
              for s in tests["result"]["stages"]]
    return {"name": name, "condition": condition, "learn": T.outcomes(learn)["cgm"],
            "chosen": tests["result"]["chosen"], "stages": stages}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=7)
    ap.add_argument("--aim", default="tighter")
    ap.add_argument("--out", default=os.path.join(HERE, "results", "weak_profile_stages_2026-11-08.json"))
    a = ap.parse_args()
    names = [n for n, r in json.load(open(STORE))["subjects"].items() if r.get("found")][:12]
    jobs = [(n, c, a.aim) for c in WEAK for n in names]
    t0 = time.time()
    with ProcessPoolExecutor(a.workers) as ex:
        out = list(ex.map(one, jobs))
    json.dump({"aim": a.aim, "rows": out, "seconds": round(time.time() - t0, 1)},
              open(a.out, "w"), indent=1)
    print(f"wrote {a.out} in {time.time() - t0:.0f}s, {sum('error' in r for r in out)} skipped")


if __name__ == "__main__":
    main()
