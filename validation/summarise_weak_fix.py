"""The secondary tables of WEAK_FIX_PLAN.md: the change run against the comparison run.

    python3 validation/summarise_weak_fix.py results/bad_profiles_2026-11-08-weakfix.json \\
        results/bad_profiles_2026-11-08-fix.json

The harm criteria come from summarise_bad_profiles_3.py on the same pair.
"""
import json
import statistics as st
import sys

WEAK = ("isf_weak", "basal_low", "cr_weak", "all_weak")
LEVERS = {"isf_weak": ["isf"], "basal_low": ["basal"], "cr_weak": ["cr"],
          "all_weak": ["isf", "basal", "cr"]}


def meets(cgm):
    return cgm["tir"] > 80 and cgm["tbr70"] < 2


def load(p):
    return {(r["name"], r["condition"]): r for r in json.load(open(p))["rows"] if "error" not in r}


new, old = load(sys.argv[1]), load(sys.argv[2])
keys = sorted(set(new) & set(old))
print(f"{len(keys)} subject-conditions in both runs")
for label, sel in (("too little insulin", lambda c: c in WEAK),
                   ("too much insulin", lambda c: c not in WEAK), ("all", lambda c: True)):
    ks = [k for k in keys if sel(k[1])]
    print(f"meeting the tighter aim, {label} (of {len(ks)}): mis-set "
          f"{sum(meets(new[k]['eval_start']['cgm']) for k in ks)}, comparison "
          f"{sum(meets(old[k]['eval_twin']['cgm']) for k in ks)}, change "
          f"{sum(meets(new[k]['eval_twin']['cgm']) for k in ks)}")

print("\nper condition, median: mis-set -> comparison -> change")
for c in sorted({k[1] for k in keys}):
    ks = [k for k in keys if k[1] == c]
    line = []
    for m in ("tir", "tbr70", "tbr54"):
        med = lambda rows, arm: st.median(r[arm]["cgm"][m] for r in rows)
        line.append(f"{m} {med([new[k] for k in ks], 'eval_start'):.2f} -> "
                    f"{med([old[k] for k in ks], 'eval_twin'):.2f} -> {med([new[k] for k in ks], 'eval_twin'):.2f}")
    print(f"  {c}: " + "; ".join(line))

print("\nweak setting moved towards its titrated value (closer to 1 than the mis-set), comparison -> change")
for c in WEAK:
    ks = [k for k in keys if k[1] == c]
    for lever in LEVERS[c]:
        towards = lambda r: abs(r["titrated_vs_twin"][lever] - 1) < abs(r["titrated_vs_start"][lever] - 1) - 1e-6
        print(f"  {c} {lever}: {sum(towards(old[k]) for k in ks)} -> {sum(towards(new[k]) for k in ks)} of {len(ks)}")

mi = lambda r: r.get("more_insulin")
if all(mi(r) is not None for r in new.values()):
    print(f"\ngiven more insulin: comparison {sum(bool(mi(old[k])) for k in keys)}, "
          f"change {sum(bool(mi(new[k])) for k in keys)}")
