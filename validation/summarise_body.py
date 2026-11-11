"""Part 2 of BODY_PLAN.md: arms H and HB against arm A, paired per subject-condition.

    python3 validation/summarise_body.py

Each figure is the arm's evaluation (sensor, pooled over the three seeds) minus arm A's for the
same subject and condition; the median over subject-conditions carries a bootstrap 95% interval
over subjects. Writes results/body_part2_2026-11-11.json.
"""
import json
import statistics as st
from pathlib import Path

import numpy as np

R = Path(__file__).parent / "results"
BODIES = {
    "S2008": {"A": R / "bad_profiles_2026-11-09-stepA.json",
              "H": R / "bad_profiles_2026-11-11-H.json", "HB": R / "bad_profiles_2026-11-11-HB.json"},
    "Hovorka": {"A": R / "bad_profiles_2026-11-10-hovA.json",
                "H": R / "bad_profiles_2026-11-11-hovH.json", "HB": R / "bad_profiles_2026-11-11-hovHB.json"},
}
PAIRS = (("H", "A"), ("HB", "A"), ("HB", "H"))
MEASURES = ("tbr54", "tbr70", "tir")
WEAK = ("isf_weak", "basal_low", "cr_weak", "all_weak")


def load(p):
    return {(r["name"], r["condition"]): r for r in json.load(open(p))["rows"] if "error" not in r}


def boot(diffs, n=4000, seed=1):
    """Median over subject-conditions, resampling subjects; diffs is {subject: [values]}."""
    subs = sorted(diffs)
    rng = np.random.default_rng(seed)
    meds = [np.median(np.concatenate([diffs[s] for s in rng.choice(subs, len(subs))]))
            for _ in range(n)]
    return float(np.median(np.concatenate(list(diffs.values())))), \
        [float(np.percentile(meds, 2.5)), float(np.percentile(meds, 97.5))]


def more_insulin(r):       # as summarise_bad_profiles_3.py
    c = r["chosen"]
    return (c["basal_scale"] > 1 or c["isf_scale"] < 1 or c["cr_scale"] < 1
            or c.get("target_offset", 0) < 0 or (c.get("smb_minutes") or 75) > 75
            or (c.get("max_iob") or 0) > r["profile0"]["max_iob"] + 1e-6)


out = {}
for body, files in BODIES.items():
    arms = {a: load(p) for a, p in files.items()}
    keys = sorted(arms["A"])
    assert all(set(arms[a]) == set(keys) for a in arms), f"{body}: arms cover different rows"
    for k in keys:              # reused mis-set and null arms must be identical across arms
        for a in ("H", "HB"):
            assert arms[a][k]["eval_start"] == arms["A"][k]["eval_start"], (body, a, k)
            assert arms[a][k]["eval_null"] == arms["A"][k]["eval_null"], (body, a, k)
    res = {"rows": len(keys)}
    for new, old in PAIRS:
        pair = {}
        for m in MEASURES:
            d = {}
            for k in keys:
                d.setdefault(k[0], []).append(arms[new][k]["eval_twin"]["cgm"][m]
                                              - arms[old][k]["eval_twin"]["cgm"][m])
            same = sum(arms[new][k]["eval_twin"]["cgm"][m] == arms[old][k]["eval_twin"]["cgm"][m]
                       for k in keys)
            med, ci = boot({s: np.array(v) for s, v in d.items()})
            pair[m] = {"median": round(med, 3), "ci": [round(c, 3) for c in ci], "identical": same,
                       "below_zero": ci[1] < 0}
        by_cond = {}
        for c in dict.fromkeys(k[1] for k in keys):
            ks = [k for k in keys if k[1] == c]
            by_cond[c] = {m: round(st.median(arms[new][k]["eval_twin"]["cgm"][m]
                                             - arms[old][k]["eval_twin"]["cgm"][m] for k in ks), 2)
                          for m in ("tbr54", "tir")}
        pair["by_condition"] = by_cond
        if old == "A":
            pair["goes_forward_here"] = pair["tbr54"]["below_zero"] and pair["tir"]["median"] >= -1
        res[f"{new}-{old}"] = pair
    res["more_insulin_share"] = {a: round(sum(more_insulin(r) for r in arms[a].values()) / len(keys), 3)
                                 for a in arms}
    res["median_eval"] = {a: {c: {m: round(st.median(arms[a][k]["eval_twin"]["cgm"][m]
                                                   for k in keys if k[1] == c), 2)
                                  for m in ("tir", "tbr54")}
                              for c in dict.fromkeys(k[1] for k in keys)}
                          for a in arms}
    res["median_start"] = {c: {m: round(st.median(arms["A"][k]["eval_start"]["cgm"][m]
                                                for k in keys if k[1] == c), 2)
                               for m in ("tir", "tbr54")}
                           for c in dict.fromkeys(k[1] for k in keys)}
    out[body] = res

for arm in ("H", "HB"):
    out[f"{arm}_goes_forward"] = all(out[b][f"{arm}-A"]["goes_forward_here"] for b in BODIES)
(R / "body_part2_2026-11-11.json").write_text(json.dumps(out, indent=1))
print(json.dumps(out, indent=1))
