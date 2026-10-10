"""Judge bad_profiles_2026-10-09b.json against BAD_PROFILES_PLAN_2.md.

    python3 validation/summarise_bad_profiles_2.py validation/results/bad_profiles_2026-10-09b.json \
        validation/results/bad_profiles_2026-10-09.json
"""
import json
import statistics as st
import sys
from math import comb

import numpy as np

TIR_MIN, TBR70_MAX, TBR54_MAX = 80.0, 1.5, 0.4


def passes(o):
    return o["tir"] > TIR_MIN and o["tbr70"] < TBR70_MAX and o["tbr54"] < TBR54_MAX


def more_insulin(r):
    c = r["chosen"]
    return (c["basal_scale"] > 1 or c["isf_scale"] < 1 or c["cr_scale"] < 1
            or c.get("target_offset", 0) < 0 or (c.get("smb_minutes") or 75) > 75
            or (c.get("max_iob") or 0) > r["profile0"]["max_iob"] + 1e-6)


def tail(k, n, p=0.05):
    """P(X >= k) for X ~ Binomial(n, p)."""
    return sum(comb(n, i) * p ** i * (1 - p) ** (n - i) for i in range(k, n + 1))


d = json.load(open(sys.argv[1]))
first = json.load(open(sys.argv[2])) if len(sys.argv) > 2 else None
rows = d["rows"]
conds = list(d["design"]["conditions"])
print(f"rows {len(rows)}, failed {len(d['failed'])}, seeds {d['design']['eval_seeds']}, "
      f"{d['seconds']:.0f} s")

print("\nPass rule, subjects of 12 (pooled 84 days): start -> twin, sensor | true glucose"
      + (" | first run, sensor" if first else ""))
for c in conds:
    rs = [r for r in rows if r["condition"] == c]
    line = (f"{c}: {sum(passes(r['eval_start']['cgm']) for r in rs)} -> "
            f"{sum(passes(r['eval_twin']['cgm']) for r in rs)} | "
            f"{sum(passes(r['eval_start']['bg']) for r in rs)} -> "
            f"{sum(passes(r['eval_twin']['bg']) for r in rs)}")
    if first:
        fs = [r for r in first["rows"] if r["condition"] == c]
        line += (f" | {sum(passes(r['eval_start']['cgm']) for r in fs)} -> "
                 f"{sum(passes(r['eval_twin']['cgm']) for r in fs)}")
    print(line)
fewer = [c for c in conds
         if sum(passes(r["eval_twin"]["cgm"]) for r in rows if r["condition"] == c)
         < sum(passes(r["eval_start"]["cgm"]) for r in rows if r["condition"] == c)]

null = np.array([r["eval_null"]["cgm"]["tbr54"] - r["eval_start"]["cgm"]["tbr54"] for r in rows])
twin = np.array([r["eval_twin"]["cgm"]["tbr54"] - r["eval_start"]["cgm"]["tbr54"] for r in rows])
thr = float(np.percentile(null, 95))
exc = [(r, t) for r, t in zip(rows, twin) if t > thr]
mi = [more_insulin(r) for r in rows]
exc_mi = [(r, t) for r, t in exc if more_insulin(r)]
n_mi = sum(mi)
print(f"\nNull changes in time below 54 (sensor, pooled): 5/50/95% "
      f"{np.percentile(null, 5):+.3f}, {np.percentile(null, 50):+.3f}, {thr:+.3f}; max {null.max():+.3f}")
print(f"Twin changes: 5/50/95% {np.percentile(twin, 5):+.3f}, {np.percentile(twin, 50):+.3f}, "
      f"{np.percentile(twin, 95):+.3f}; max {twin.max():+.3f}")
for r, t in sorted(exc, key=lambda x: -x[1]):
    c = r["chosen"]
    print(f"  exceedance {r['condition']} {r['name']}: {r['eval_start']['cgm']['tbr54']:.3f} -> "
          f"{r['eval_twin']['cgm']['tbr54']:.3f} (+{t:.3f}); more insulin {more_insulin(r)}; basal "
          f"x{c['basal_scale']} ISF x{c['isf_scale']} CR x{c['cr_scale']} target "
          f"{c.get('target_offset', 0):+} SMB {c.get('smb_minutes')} maxIOB {c.get('max_iob')}")

print("\nCriteria (any one counts against the twin):")
print(f"1. exceedances {len(exc)} of {len(rows)} (>= 10 counts); P(X >= {len(exc)}) = "
      f"{tail(len(exc), len(rows)):.3f}")
print(f"2. twin rises above the null maximum ({null.max():+.3f}): {int((twin > null.max()).sum())}")
print(f"3. among {n_mi} given more insulin: {len(exc_mi)} exceedances; P(X >= {len(exc_mi)}) = "
      f"{tail(len(exc_mi), n_mi) if n_mi else float('nan'):.3f} (< 0.05 counts)")
print(f"4. conditions with fewer passing on sensor glucose: {fewer or 'none'}")

print("\nOutcomes, sensor, median, mean (range): start -> twin")
for c in conds:
    rs = [r for r in rows if r["condition"] == c]
    for k, lab in (("tir", "TIR"), ("tbr70", "<70"), ("tbr54", "<54")):
        a = [r["eval_start"]["cgm"][k] for r in rs]
        b = [r["eval_twin"]["cgm"][k] for r in rs]
        print(f"{c} {lab}: {st.median(a):.2f}, {st.mean(a):.2f} ({min(a):.2f}-{max(a):.2f}) -> "
              f"{st.median(b):.2f}, {st.mean(b):.2f} ({min(b):.2f}-{max(b):.2f})")

print("\nDirection: given more insulin, and mis-set settings moved towards titrated")
for c in conds:
    rs = [r for r in rows if r["condition"] == c]
    parts = [f"more insulin {sum(more_insulin(r) for r in rs)}"]
    for lever in d["design"]["conditions"][c]:
        tw = sum(abs(r["titrated_vs_twin"][lever] - 1) < abs(r["titrated_vs_start"][lever] - 1) - 1e-9 for r in rs)
        aw = sum(abs(r["titrated_vs_twin"][lever] - 1) > abs(r["titrated_vs_start"][lever] - 1) + 1e-9 for r in rs)
        parts.append(f"{lever}: towards {tw}, away {aw}, unchanged {len(rs) - tw - aw}")
    print(f"{c}: " + "; ".join(parts))

print("\nEstimated against realised change in time below 70 (sensor), median")
for c in conds:
    rs = [r for r in rows if r["condition"] == c]
    est = [r["twin_estimate"]["est_all"]["tbr"] - r["twin_observed"]["tbr"] for r in rs]
    real = [r["eval_twin"]["cgm"]["tbr70"] - r["eval_start"]["cgm"]["tbr70"] for r in rs]
    print(f"{c}: estimated {st.median(est):+.2f}, realised {st.median(real):+.2f}")
