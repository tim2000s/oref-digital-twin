"""Judge the tighter-aim run against BAD_PROFILES_PLAN_3.md, beside the standard-aim run.

    python3 validation/summarise_bad_profiles_3.py \
        validation/results/bad_profiles_2026-10-10-tighter.json \
        validation/results/bad_profiles_2026-10-09b.json
"""
import json
import statistics as st
import sys
from math import comb

import numpy as np


def aim_met(o):            # the tighter aim: time in range above 80%, below 70 under 2%
    return o["tir"] > 80.0 and o["tbr70"] < 2.0


def pass_rule(o):
    return o["tir"] > 80.0 and o["tbr70"] < 1.5 and o["tbr54"] < 0.4


def more_insulin(r):
    c = r["chosen"]
    return (c["basal_scale"] > 1 or c["isf_scale"] < 1 or c["cr_scale"] < 1
            or c.get("target_offset", 0) < 0 or (c.get("smb_minutes") or 75) > 75
            or (c.get("max_iob") or 0) > r["profile0"]["max_iob"] + 1e-6)


def tail(k, n, p=0.05):
    return sum(comb(n, i) * p ** i * (1 - p) ** (n - i) for i in range(k, n + 1))


tight = json.load(open(sys.argv[1]))
std = json.load(open(sys.argv[2]))
T = {(r["name"], r["condition"]): r for r in tight["rows"]}
S = {(r["name"], r["condition"]): r for r in std["rows"]}
keys = sorted(T)
conds = list(tight["design"]["conditions"])
assert set(keys) == set(S), "the two runs cover different subject-conditions"
assert all(T[k]["eval_start"] == S[k]["eval_start"] for k in keys), "mis-set arms differ"
print(f"rows {len(keys)}, failed {len(tight['failed'])}, aim {tight['design']['aim']}, "
      f"{tight['seconds']:.0f} s")

print("\nPrimary: subject-conditions meeting the tighter aim (pooled sensor), of 12 per condition")
print("condition | mis-set | standard twin | tighter twin")
tot = [0, 0, 0]
for c in conds:
    ks = [k for k in keys if k[1] == c]
    a = sum(aim_met(T[k]["eval_start"]["cgm"]) for k in ks)
    b = sum(aim_met(S[k]["eval_twin"]["cgm"]) for k in ks)
    t = sum(aim_met(T[k]["eval_twin"]["cgm"]) for k in ks)
    tot = [tot[0] + a, tot[1] + b, tot[2] + t]
    print(f"{c} | {a} | {b} | {t}")
print(f"total | {tot[0]} | {tot[1]} | {tot[2]}")
gained = [k for k in keys if aim_met(T[k]["eval_twin"]["cgm"]) and not aim_met(S[k]["eval_twin"]["cgm"])]
lost = [k for k in keys if aim_met(S[k]["eval_twin"]["cgm"]) and not aim_met(T[k]["eval_twin"]["cgm"])]
print(f"met by tighter but not standard: {len(gained)}; by standard but not tighter: {len(lost)}")

null = np.array([S[k]["eval_null"]["cgm"]["tbr54"] - S[k]["eval_start"]["cgm"]["tbr54"] for k in keys])
twin = np.array([T[k]["eval_twin"]["cgm"]["tbr54"] - T[k]["eval_start"]["cgm"]["tbr54"] for k in keys])
thr, nmax = float(np.percentile(null, 95)), float(null.max())
exc = [(k, d) for k, d in zip(keys, twin) if d > thr]
mi = [k for k in keys if more_insulin(T[k])]
exc_mi = [(k, d) for k, d in exc if k in mi]
fewer = [c for c in conds
         if sum(pass_rule(T[k]["eval_twin"]["cgm"]) for k in keys if k[1] == c)
         < sum(pass_rule(T[k]["eval_start"]["cgm"]) for k in keys if k[1] == c)]
print(f"\nHarm, against the second run's null arm (95th {thr:+.3f}, max {nmax:+.3f}):")
print(f"1. exceedances {len(exc)} of {len(keys)} (>= 10 counts); P = {tail(len(exc), len(keys)):.3f}")
print(f"2. rises above the null maximum: {int((twin > nmax).sum())}")
print(f"3. among {len(mi)} given more insulin: {len(exc_mi)} exceedances; P = "
      f"{tail(len(exc_mi), len(mi)) if mi else float('nan'):.3f} (< 0.05 counts)")
print(f"4. conditions with fewer passing the pass rule than mis-set: {fewer or 'none'}")
for k, d in sorted(exc, key=lambda x: -x[1]):
    c = T[k]["chosen"]
    print(f"  exceedance {k[1]} {k[0]}: +{d:.3f}; more insulin {k in mi}; basal x{c['basal_scale']} "
          f"ISF x{c['isf_scale']} CR x{c['cr_scale']} target {c.get('target_offset', 0):+} "
          f"SMB {c.get('smb_minutes')} maxIOB {c.get('max_iob')}")

print("\nPer condition, sensor, median: TIR and below 70, mis-set -> standard twin -> tighter twin;"
      " given more insulin, standard and tighter")
for c in conds:
    ks = [k for k in keys if k[1] == c]
    med = lambda f: st.median(f(k) for k in ks)
    print(f"{c}: TIR {med(lambda k: T[k]['eval_start']['cgm']['tir']):.1f} -> "
          f"{med(lambda k: S[k]['eval_twin']['cgm']['tir']):.1f} -> {med(lambda k: T[k]['eval_twin']['cgm']['tir']):.1f}; "
          f"<70 {med(lambda k: T[k]['eval_start']['cgm']['tbr70']):.2f} -> "
          f"{med(lambda k: S[k]['eval_twin']['cgm']['tbr70']):.2f} -> {med(lambda k: T[k]['eval_twin']['cgm']['tbr70']):.2f}; "
          f"<54 {med(lambda k: T[k]['eval_start']['cgm']['tbr54']):.2f} -> "
          f"{med(lambda k: S[k]['eval_twin']['cgm']['tbr54']):.2f} -> {med(lambda k: T[k]['eval_twin']['cgm']['tbr54']):.2f}; "
          f"more insulin {sum(more_insulin(S[k]) for k in ks)}, {sum(more_insulin(T[k]) for k in ks)}")

est = [T[k]["twin_estimate"]["est_all"]["tir"] - T[k]["twin_observed"]["tir"] for k in keys]
real = [T[k]["eval_twin"]["cgm"]["tir"] - T[k]["eval_start"]["cgm"]["tir"] for k in keys]
print(f"\nTime in range, estimated against realised change (tighter twin): median "
      f"{st.median(est):+.2f} against {st.median(real):+.2f}; correlation {np.corrcoef(est, real)[0, 1]:.2f}")
