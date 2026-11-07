"""List the subject-conditions where two mis-set profile runs chose different settings.

    python3 validation/compare_choices.py \
        validation/results/bad_profiles_2026-10-10-tighter.json \
        validation/results/bad_profiles_2026-11-07-rescue.json
"""
import json
import sys

a, b = ({(r["name"], r["condition"]): r for r in json.load(open(p))["rows"]} for p in sys.argv[1:3])
ch = sorted(k for k in a if a[k]["chosen"] != b[k]["chosen"])
print(f"choices differ in {len(ch)} of {len(a)}")
for k in ch:
    d = b[k]["eval_twin"]["cgm"]["tbr54"] - b[k]["eval_start"]["cgm"]["tbr54"]
    print(f"{k[1]} {k[0]}: {a[k]['chosen']} -> {b[k]['chosen']}; "
          f"change below 54 {d:+.3f}")
