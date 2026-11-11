"""The harm criteria of BAD_PROFILES_PLAN_4.md applied to the null arm itself.

    python3 validation/null_criteria.py

The null arm changes max IOB by 0.03 U and nothing else, so a criterion it meets is one that a
change doing nothing can fail. The criteria on rises in time below 54 are set from the null arm and
are not repeated here; their chance under exchangeability is in PACE_PLAN.md. This checks the
pass-rule criterion, per condition, and whether it can bind at all. Writes
results/null_criteria.json.
"""
import json
from pathlib import Path

from summarise_pace import load, pass_rule

R = Path(__file__).parent / "results"
NULLS = {"S2008": R / "bad_profiles_2026-11-09-stepA.json", "Hovorka": R / "bad_profiles_2026-11-10-hovA.json"}

out = {}
for body, p in NULLS.items():
    T = load(p)
    conds = list(dict.fromkeys(k[1] for k in sorted(T)))
    per = {c: {"start": sum(pass_rule(T[k]["eval_start"]["cgm"]) for k in T if k[1] == c),
               "null": sum(pass_rule(T[k]["eval_null"]["cgm"]) for k in T if k[1] == c)} for c in conds}
    out[body] = {"passing_by_condition": per,
                 "null_fewer_passing": [c for c, v in per.items() if v["null"] < v["start"]],
                 "start_passing_total": sum(v["start"] for v in per.values())}
(R / "null_criteria.json").write_text(json.dumps(out, indent=1))
print(json.dumps(out, indent=1))
