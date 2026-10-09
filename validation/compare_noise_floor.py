"""Set the twin's per-subject changes beside the noise floor (null_perturbation_<tag>.json).

    python3 validation/compare_noise_floor.py validation/results/bad_profiles_2026-10-09.json \
        validation/results/null_perturbation_2026-10-09.json
"""
import json
import sys

import numpy as np

bad = json.load(open(sys.argv[1]))
null = json.load(open(sys.argv[2]))
key = lambda r: (r["name"], r["condition"])
twin = {key(r): r for r in bad["rows"]}
for metric, lab in (("tbr54", "below 54"), ("tbr70", "below 70"), ("tir", "in range")):
    for sig in ("cgm", "bg"):
        n = np.array([r["perturbed"][sig][metric] - r["start"][sig][metric] for r in null["rows"]])
        t = np.array([twin[key(r)]["eval_twin"][sig][metric] - twin[key(r)]["eval_start"][sig][metric]
                      for r in null["rows"]])
        q = lambda v: ", ".join(f"{x:+.2f}" for x in np.percentile(v, [5, 50, 95]))
        line = (f"{lab} ({sig}): null 5/50/95% {q(n)}, |change| median {np.median(np.abs(n)):.2f} | "
                f"twin 5/50/95% {q(t)}")
        if metric == "tbr54":
            line += (f" | rises > 0.2: null {int((n > 0.2).sum())}/{len(n)}, twin {int((t > 0.2).sum())}/{len(t)}"
                     f"; rises > null 95th ({np.percentile(n, 95):+.2f}): twin {int((t > np.percentile(n, 95)).sum())}")
        print(line)
