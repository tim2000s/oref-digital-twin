"""Same-fortnight accuracy of the twin's estimates in TimSim (SAME_WEEK_PLAN.md).

For each titrated subject: run the 14-day learning fortnight, ask the twin's simulator for its
estimate under ten changes, then rerun the same fortnight in TimSim under each change, same seed.

    ~/.venvs/boost-insilico/bin/python validation/same_week.py --workers 7
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

CHANGES = {
    "basal_down": {"basal": 0.7}, "basal_up": {"basal": 1.3},
    "isf_strong": {"isf": 0.7}, "isf_weak": {"isf": 1.3},
    "cr_strong": {"cr": 0.7}, "cr_weak": {"cr": 1.3},
    "target_down": {"target": -18}, "target_up": {"target": 18},
    "all_strong": {"basal": 1.3, "isf": 0.7, "cr": 0.7},
    "all_weak": {"basal": 0.7, "isf": 1.3, "cr": 1.3},
}
STORE = os.path.join(HERE, "results", "titrated_2026-10-09.json")


def score(points):
    """Sensor-glucose bands over a list of readings: one function for estimate and truth."""
    v = [g for g in points if g]
    n = len(v)
    return {"tir": 100 * sum(70 <= g <= 180 for g in v) / n,
            "tbr70": 100 * sum(g < 70 for g in v) / n, "tbr54": 100 * sum(g < 54 for g in v) / n}


def changed_profile(p, ch):
    off = ch.get("target", 0)
    return replace(p, basal_u_per_hour=p.basal_u_per_hour * ch.get("basal", 1.0),
                   isf=p.isf * ch.get("isf", 1.0), cr=p.cr * ch.get("cr", 1.0),
                   target_lo=p.target_lo + off, target_hi=p.target_hi + off)


def one(job):
    """job: a subject name, or (name, options, stored row list) to re-estimate with the twin's
    optional decay and rescue model and take the TimSim truth from an earlier run (--truth-from)."""
    name, opts, stored = (job, {}, None) if isinstance(job, str) else job
    T._paths()
    from ingestion.pull import pull_from_raw
    from ingestion.models import GlucoseReading
    from replay import OrefOracle, from_cycle
    from replay.scenarios import _interp, sample_cycles
    from report.browser import _active_profile
    from timsim.therapy import titrate

    rec = json.load(open(STORE))["subjects"][name]
    p0 = titrate._profile(name, rec["scale"], 1.0 if rec.get("basal_scale") is None else rec["basal_scale"])
    learn, sugg = T.run_timsim(name, p0, T.LEARN_DAYS, T.LEARN_SEED)
    raw = T.to_nightscout(learn, sugg, p0)
    cgm = [float(x) for x in learn.cgm]
    base = score(cgm)

    # the twin: requests built exactly as the page builds them, then one simulator call
    pull = pull_from_raw("x", raw["start_ms"], raw["end_ms"], raw["entries"], raw["treatments"],
                         raw["devicestatus"], raw["profiles"])
    profile = _active_profile(pull.profiles)
    settings = T.twin_settings(p0)
    merged = list(pull.entries) + [GlucoseReading(ts_ms=c.ts_ms, sgv_mgdl=c.bg_mgdl)
                                   for c in pull.devicestatus if c.bg_mgdl is not None]
    reqs = [r for r in (from_cycle(c, profile, merged, settings, pull.treatments)[0]
                        for c in sample_cycles(pull.devicestatus) if c.bg_mgdl is not None) if r]
    scen = [{"label": k, "basal_scale": ch.get("basal", 1.0), "isf_scale": ch.get("isf", 1.0),
             "cr_scale": ch.get("cr", 1.0), "target_offset": ch.get("target", 0)}
            for k, ch in CHANGES.items()]
    oracle = OrefOracle()
    sim = oracle.simulate({"cycles": reqs, "scenarios": scen, "cache_key": name})
    decayed = (oracle.simulate({"cycles": reqs, "scenarios": scen, "cache_key": name, **opts})
               if opts else None)
    oracle._simulator.close()
    ts = [e["date"] for e in raw["entries"]]
    obs = [float(e["sgv"]) for e in raw["entries"]]
    twin_base = score(obs)

    def estimate(s):
        dbg = [d if d is not None else 0.0 for d in s["dbg"]]
        est = score([g + _interp(sim["t"], dbg, t) for t, g in zip(ts, obs)])
        return {m: est[m] - twin_base[m] for m in est}

    rows = []
    if stored is not None:
        # The stored truth is only valid for this run if nothing upstream moved: the learning
        # fortnight and the twin without decay must reproduce the stored estimates exactly.
        by = {r["change"]: r for r in stored}
        exact = all(estimate(s) == by[k]["estimated"] for k, s in zip(CHANGES, sim["scenarios"]))
        for k, s, sd in zip(CHANGES, sim["scenarios"], decayed["scenarios"]):
            rows.append({"change": k, "estimated": estimate(sd), "estimated_no_decay": estimate(s),
                         "same_fortnight": by[k]["same_fortnight"], "rescues": by[k]["rescues"],
                         "failed_cycles": sd.get("failed", 0)})
        return {"name": name, "replay_exact": exact, "base": base, "twin_base": twin_base,
                "cycles": len(reqs), "rows": rows, **opts}

    # determinism: the unchanged profile replayed must give the learning run back exactly
    again, _ = T.run_timsim(name, p0, T.LEARN_DAYS, T.LEARN_SEED)
    exact = [float(x) for x in again.cgm] == cgm
    for (k, ch), s in zip(CHANGES.items(), sim["scenarios"]):
        truth_run, _ = T.run_timsim(name, changed_profile(p0, ch), T.LEARN_DAYS, T.LEARN_SEED)
        truth = score([float(x) for x in truth_run.cgm])
        rows.append({"change": k, "estimated": estimate(s),
                     "same_fortnight": {m: truth[m] - base[m] for m in truth},
                     "rescues": [learn.rescue_events, truth_run.rescue_events],
                     "failed_cycles": s.get("failed", 0)})
    return {"name": name, "replay_exact": exact, "base": base, "twin_base": twin_base,
            "cycles": len(reqs), "rows": rows}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=7)
    ap.add_argument("--subjects", type=int, default=12)
    ap.add_argument("--decay-tau-min", type=float, default=0,
                    help="re-estimate with the twin's decay at this time constant; needs --truth-from")
    ap.add_argument("--rescue", help="re-estimate with the twin's rescue model, given as JSON "
                    "{threshold, refractory_min, delay, rise, rise_min}; needs --truth-from")
    ap.add_argument("--truth-from", help="an earlier results file whose TimSim truth is reused")
    ap.add_argument("--out", default=os.path.join(HERE, "results", "same_week_2026-10-10.json"))
    a = ap.parse_args()
    names = [n for n, r in json.load(open(STORE))["subjects"].items() if r.get("found")][: a.subjects]
    jobs = names
    opts = {**({"decay_tau_min": a.decay_tau_min} if a.decay_tau_min else {}),
            **({"rescue": json.loads(a.rescue)} if a.rescue else {})}
    if opts:
        stored = {s["name"]: s["rows"] for s in json.load(open(a.truth_from))["subjects"]}
        jobs = [(n, opts, stored[n]) for n in names]
    t0 = time.time()
    with ProcessPoolExecutor(a.workers) as ex:
        out = list(ex.map(one, jobs))
    path = a.out
    json.dump({"changes": CHANGES, "subjects": out, "seconds": round(time.time() - t0, 1)},
              open(path, "w"), indent=1)
    print(f"wrote {path} in {time.time() - t0:.0f}s; replay exact for "
          f"{sum(s['replay_exact'] for s in out)} of {len(out)}")


if __name__ == "__main__":
    main()
