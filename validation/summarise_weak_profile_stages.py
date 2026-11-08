"""Why each too-weak setting was or was not strengthened, from weak_profile_stages.py.

    python3 validation/summarise_weak_profile_stages.py validation/results/weak_profile_stages_2026-11-08.json

For the stage of each weak setting it counts the rule `choose` used and whether the
strengthening limit removed every stronger value, and lists the learning fortnight's time
below 70 beside it, since the limit is judged on the whole period's estimate.
"""
import json
import statistics as st
import sys
from collections import Counter

STAGE = {"isf_weak": ["ISF"], "basal_low": ["Basal"], "cr_weak": ["Carb ratio"],
         "all_weak": ["Basal", "ISF", "Carb ratio"]}
# the stronger direction for each stage
STRONGER = {"Basal": lambda v: v > 1, "ISF": lambda v: v < 1, "Carb ratio": lambda v: v < 1}


def rule(why):
    if why is None:
        return "not run"
    for key, label in (("already meets", "already meets the aim"),
                       ("smallest change", "smallest change meeting the aim"),
                       ("keeps lows under", "no value meets the aim: most in range with lows under 2%"),
                       ("fewest", "no value has lows under 2%: fewest lows"),
                       ("needed to judge", "too few hours to judge")):
        if key in why:
            return label
    return why


d = json.load(open(sys.argv[1]))
rows = [r for r in d["rows"] if "error" not in r]
print(f"{len(rows)} subject-conditions, {len(d['rows']) - len(rows)} skipped, aim {d['aim']}")
for cond, names in STAGE.items():
    for sname in names:
        sub = [(r, next(s for s in r["stages"] if s["name"] == sname))
               for r in rows if r["condition"] == cond]
        if not sub:
            continue
        direction = Counter()
        rules = Counter()
        all_excluded = 0
        stronger_better = 0
        for r, s in sub:
            c = s["chosen"]
            direction["stronger" if STRONGER[sname](c) else "unchanged" if c in (1, 1.0) else "weaker"] += 1
            rules[rule(s["why"])] += 1
            strong = [x for x in s["rows"] if STRONGER[sname](x["value"])]
            if strong and all(x["excluded"] for x in strong):
                all_excluded += 1
            neutral = next((x for x in s["rows"] if x["value"] == 1.0), None)
            if neutral and any(x["est"]["tir"] is not None and neutral["est"]["tir"] is not None
                               and x["est"]["tir"] > neutral["est"]["tir"] + 1 for x in strong):
                stronger_better += 1
        learn70 = [r["learn"]["tbr70"] for r, _ in sub]
        print(f"\n{cond}, {sname} stage (n {len(sub)}): chosen {dict(direction)}")
        print(f"  every stronger value excluded by the limit: {all_excluded}; a stronger value "
              f"estimated over 1 point more in range on its stretches: {stronger_better}")
        print(f"  learning fortnight below 70: median {st.median(learn70):.2f}%, over 2% in "
              f"{sum(v > 2 for v in learn70)}")
        for k, v in rules.most_common():
            print(f"  {v:2d}  {k}")
