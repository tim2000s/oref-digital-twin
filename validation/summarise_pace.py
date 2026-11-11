"""The judgement of PACE_PLAN.md: arm P (guard and pace) against arm A (the page) and arm C (guard).

    python3 validation/summarise_pace.py [--p-tag 2026-11-11]

Writes results/pace_<p-tag>.json. Figures are evaluation outcomes, sensor pooled over the three
seeds; medians carry a bootstrap 95% interval over subjects.
"""
import argparse
import json
from math import comb
from pathlib import Path

import numpy as np

R = Path(__file__).parent / "results"
STRONG = ("isf_strong", "basal_high", "cr_strong", "all_strong")
WEAK = ("isf_weak", "basal_low", "cr_weak", "all_weak")


def load(p):
    return {(r["name"], r["condition"]): r for r in json.load(open(p))["rows"] if "error" not in r}


def boot(diffs, n=4000, seed=1):
    """Median over subject-conditions with an interval from resampling subjects."""
    subs = sorted(diffs)
    rng = np.random.default_rng(seed)
    meds = [np.median(np.concatenate([diffs[s] for s in rng.choice(subs, len(subs))]))
            for _ in range(n)]
    return (float(np.median(np.concatenate(list(diffs.values())))),
            [float(np.percentile(meds, 2.5)), float(np.percentile(meds, 97.5))])


def by_subject(keys, f):
    d = {}
    for k in keys:
        d.setdefault(k[0], []).append(f(k))
    return {s: np.array(v) for s, v in d.items()}


def binom_tail(k, n, p=0.05):
    return sum(comb(n, i) * p ** i * (1 - p) ** (n - i) for i in range(k, n + 1))


def more_insulin(r):       # as summarise_bad_profiles_3.py
    c = r["chosen"]
    return (c["basal_scale"] > 1 or c["isf_scale"] < 1 or c["cr_scale"] < 1
            or c.get("target_offset", 0) < 0 or (c.get("smb_minutes") or 75) > 75
            or (c.get("max_iob") or 0) > r["profile0"]["max_iob"] + 1e-6)


def aim_met(o):
    return o["tir"] > 80.0 and o["tbr70"] < 2.0


def pass_rule(o):
    return o["tir"] > 80.0 and o["tbr70"] < 1.5 and o["tbr54"] < 0.4


def far(c):                # any of basal, ISF, carb ratio over 20% towards more insulin
    return c["basal_scale"] > 1.2 + 1e-9 or c["isf_scale"] < 0.8 - 1e-9 or c["cr_scale"] < 0.8 - 1e-9


def end_scales(r):         # the reviews' choices as one change from the mis-set profile
    out = {"basal_scale": 1.0, "isf_scale": 1.0, "cr_scale": 1.0}
    for rv in r.get("reviews") or [r]:
        for k in out:
            out[k] *= rv["chosen"][k]
    return out


def harm(T, keys):
    null = np.array([T[k]["eval_null"]["cgm"]["tbr54"] - T[k]["eval_start"]["cgm"]["tbr54"] for k in keys])
    rise = {k: T[k]["eval_twin"]["cgm"]["tbr54"] - T[k]["eval_start"]["cgm"]["tbr54"] for k in keys}
    thr, nmax = float(np.percentile(null, 95)), float(null.max())
    exc = [k for k in keys if rise[k] > thr]
    mi = [k for k in keys if more_insulin(T[k])]
    exc_mi = [k for k in exc if k in mi]
    above = [k for k in keys if rise[k] > nmax]
    fewer = [c for c in dict.fromkeys(k[1] for k in keys)
             if sum(pass_rule(T[k]["eval_twin"]["cgm"]) for k in keys if k[1] == c)
             < sum(pass_rule(T[k]["eval_start"]["cgm"]) for k in keys if k[1] == c)]
    p_mi = binom_tail(len(exc_mi), len(mi)) if mi else 1.0
    return {"null_95th": round(thr, 3), "null_max": round(nmax, 3),
            "exceedances": len(exc), "above_null_max": len(above),
            "above_null_max_chance_p": round(comb(len(keys), len(above)) / comb(2 * len(keys), len(above)), 4),
            "above_null_max_cases": [list(k) for k in above],
            "given_more_insulin": len(mi), "exceedances_more_insulin": len(exc_mi),
            "binomial_p_more_insulin": round(p_mi, 4), "fewer_passing": fewer,
            "met": {"exceedances_10": len(exc) >= 10, "above_max_5": len(above) >= 5,
                    "more_insulin_p": p_mi < 0.05, "fewer_passing": bool(fewer)}}


def body(files):
    arms = {a: load(p) for a, p in files.items()}
    keys = sorted(arms["A"])
    for a in arms:
        assert set(arms[a]) == set(keys), f"arm {a} covers different rows"
        for k in keys:      # reused mis-set and null arms must be identical across arms
            assert arms[a][k]["eval_start"] == arms["A"][k]["eval_start"], (a, k)
            assert arms[a][k]["eval_null"] == arms["A"][k]["eval_null"], (a, k)
    P = arms["P"]
    out = {"rows": len(keys), "harm": {a: harm(arms[a], keys) for a in arms}}
    strong = [k for k in keys if k[1] in STRONG]
    out["lows_fall_strong"] = {}
    for a in arms:
        med, ci = boot(by_subject(strong, lambda k: arms[a][k]["eval_twin"]["cgm"]["tbr54"]
                                  - arms[a][k]["eval_start"]["cgm"]["tbr54"]))
        out["lows_fall_strong"][a] = {"median": round(med, 3), "ci": [round(c, 3) for c in ci],
                                      "below_zero": ci[1] < 0}
    out["paired"] = {}
    for new, old in (("P", "A"), ("P", "C"), ("C", "A")):
        pair = {}
        for m in ("tbr54", "tbr70", "tir"):
            med, ci = boot(by_subject(keys, lambda k: arms[new][k]["eval_twin"]["cgm"][m]
                                      - arms[old][k]["eval_twin"]["cgm"][m]))
            pair[m] = {"median": round(med, 3), "ci": [round(c, 3) for c in ci], "upper": ci[1]}
        out["paired"][f"{new}-{old}"] = pair
    out["criteria"] = {
        "1_no_harm": not any(out["harm"]["P"]["met"].values()),
        "2_lows_fall_strong": out["lows_fall_strong"]["P"]["below_zero"],
        "3_lows_not_above_page": out["paired"]["P-A"]["tbr54"]["upper"] < 0.05,
    }
    out["goes_forward_here"] = all(out["criteria"].values())
    conds = list(dict.fromkeys(k[1] for k in keys))
    out["median_by_condition"] = {
        c: {"start": {m: round(float(np.median([arms["A"][k]["eval_start"]["cgm"][m] for k in keys if k[1] == c])), 2)
                      for m in ("tir", "tbr54")},
            **{a: {m: round(float(np.median([arms[a][k]["eval_twin"]["cgm"][m] for k in keys if k[1] == c])), 2)
                   for m in ("tir", "tbr54")} for a in arms}}
        for c in conds}
    out["weak_meeting_aim"] = {"start": sum(aim_met(arms["A"][k]["eval_start"]["cgm"]) for k in keys if k[1] in WEAK),
                               **{a: sum(aim_met(arms[a][k]["eval_twin"]["cgm"]) for k in keys if k[1] in WEAK)
                                  for a in arms}}
    out["ending_over_20pct_more_insulin"] = {a: sum(far(end_scales(arms[a][k])) for k in keys) for a in arms}
    # per review of P: which settings were strengthened (rows record refused labels, not reasons)
    strengthened = []
    for i in range(max(len(P[k].get("reviews", [])) for k in keys)):
        s = {"basal": 0, "isf": 0, "cr": 0, "target": 0, "none": 0}
        for k in keys:
            rv = P[k]["reviews"][i]
            c = rv["chosen"]
            up = [n for n, v in (("basal", c["basal_scale"] > 1), ("isf", c["isf_scale"] < 1),
                                 ("cr", c["cr_scale"] < 1), ("target", c["target_offset"] < 0)) if v]
            for n in up or ["none"]:
                s[n] += 1
        strengthened.append(s)
    out["P_strengthened_by_review"] = strengthened
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--p-tag", default="2026-11-11")
    a = ap.parse_args()
    bodies = {
        "S2008": {"A": R / "bad_profiles_2026-11-09-stepA.json", "C": R / "bad_profiles_2026-11-10-guardC.json",
                  "P": R / f"bad_profiles_{a.p_tag}-P.json"},
        "Hovorka": {"A": R / "bad_profiles_2026-11-10-hovA.json", "C": R / "bad_profiles_2026-11-10-hovC.json",
                    "P": R / f"bad_profiles_{a.p_tag}-hovP.json"},
    }
    out = {b: body(f) for b, f in bodies.items() if f["P"].exists()}
    out["P_goes_forward"] = len(out) == 2 and all(out[b]["goes_forward_here"] for b in bodies)
    (R / f"pace_{a.p_tag}.json").write_text(json.dumps(out, indent=1))
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
