"""Why the weak-fix rule failed: the twin's estimate against TimSim for the choices it changed.

    python3 validation/weak_fix_diagnosis.py results/bad_profiles_2026-11-08-weakfix.json \\
        results/bad_profiles_2026-11-08-fix.json

The two runs share subjects, seeds and arms and differ only in the rule, so where the chosen
settings differ, the difference between the runs' estimates (learning fortnight) can be set
against the difference in what TimSim gave on evaluation.
"""
import json
import statistics as st
import sys

L = lambda p: {(x["name"], x["condition"]): x for x in json.load(open(p))["rows"] if "error" not in x}
new, old = L(sys.argv[1]), L(sys.argv[2])
ks = [k for k in new if k in old and new[k]["chosen"] != old[k]["chosen"]]
print(f"{len(ks)} subject-conditions with a different choice")
est = lambda r, m: r["twin_estimate"]["est_all"][m]
ev = lambda r, m: r["eval_twin"]["cgm"][m]
for lab, em, rm in (("time in range", "tir", "tir"), ("below 70", "tbr", "tbr70"), ("below 54", "tbr54", "tbr54")):
    e = [est(new[k], em) - est(old[k], em) for k in ks]
    r = [ev(new[k], rm) - ev(old[k], rm) for k in ks]
    print(f"{lab}: estimated {st.median(e):+.2f}, realised {st.median(r):+.2f} points (medians); "
          f"realised above estimate in {sum(b > a for a, b in zip(e, r))}; correlation {st.correlation(e, r):.2f}")
du_e = [new[k]["twin_estimate"]["du_per_day"] - old[k]["twin_estimate"]["du_per_day"] for k in ks]
du_r = [new[k]["eval_twin"]["insulin_u_per_day"] - old[k]["eval_twin"]["insulin_u_per_day"] for k in ks]
dm_e = [new[k]["twin_estimate"]["mean_shift"] - old[k]["twin_estimate"]["mean_shift"] for k in ks]
dm_r = [ev(new[k], "mean") - ev(old[k], "mean") for k in ks]
print(f"insulin: estimated {st.median(du_e):+.2f}, realised {st.median(du_r):+.2f} U/day; "
      f"realised above estimate in {sum(b > a for a, b in zip(du_e, du_r))}")
print(f"mean glucose: estimated {st.median(dm_e):+.1f}, realised {st.median(dm_r):+.1f} mg/dL")
print(f"mg/dL per extra U/day: estimated {st.median(a / b for a, b in zip(dm_e, du_e) if b > 0.05):.1f}, "
      f"realised {st.median(a / b for a, b in zip(dm_r, du_r) if b > 0.05):.1f}")
resc = [new[k]["eval_twin"]["rescue_events"] - old[k]["eval_twin"]["rescue_events"] for k in ks]
print(f"rescue events on evaluation: median change {st.median(resc):+.0f}")
