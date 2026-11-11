"""Arms A (page), C (guard) and P (guard and pace) judged by the harm criteria as corrected on
11 November 2026, each first applied to the null arm (GUARD.md).

    python3 validation/summarise_guard.py

Writes results/guard_2026-11-11.json.
"""
import json
from pathlib import Path

from summarise_pace import STRONG, WEAK, aim_met, boot, by_subject, harm, load, pass_rule

R = Path(__file__).parent / "results"
BODIES = {
    "S2008": {"A": "bad_profiles_2026-11-09-stepA.json", "C": "bad_profiles_2026-11-10-guardC.json",
              "P": "bad_profiles_2026-11-11-P.json"},
    "Hovorka": {"A": "bad_profiles_2026-11-10-hovA.json", "C": "bad_profiles_2026-11-10-hovC.json",
                "P": "bad_profiles_2026-11-11-hovP.json"},
}


def corrected(h, T, keys, arm="eval_twin"):
    """Criteria a do-nothing arm should rarely meet: the pass-rule one counts the total over all 96."""
    start = sum(pass_rule(T[k]["eval_start"]["cgm"]) for k in keys)
    end = sum(pass_rule(T[k][arm]["cgm"]) for k in keys)
    return {"exceedances_10": h["exceedances"] >= 10, "above_max_5": h["above_null_max"] >= 5,
            "more_insulin_p": h["binomial_p_more_insulin"] < 0.05,
            "fewer_passing_total": end < start, "passing_start_end": [start, end],
            "passing_can_vary": start > 0 or end > 0}


out = {}
for body, files in BODIES.items():
    arms = {a: load(R / f) for a, f in files.items()}
    keys = sorted(arms["A"])
    A = arms["A"]
    null = {k: {**A[k], "eval_twin": A[k]["eval_null"]} for k in keys}
    res = {"null": {"criteria": corrected(harm(null, keys), A, keys, "eval_null")}}
    for a, T in arms.items():
        h = harm(T, keys)
        c = corrected(h, T, keys)
        lows = boot(by_subject([k for k in keys if k[1] in STRONG],
                               lambda k: T[k]["eval_twin"]["cgm"]["tbr54"] - T[k]["eval_start"]["cgm"]["tbr54"]))
        res[a] = {"harm": {k: h[k] for k in ("exceedances", "above_null_max", "given_more_insulin",
                                             "exceedances_more_insulin", "binomial_p_more_insulin")},
                  "criteria": c, "no_harm": not any(c[k] for k in ("exceedances_10", "above_max_5",
                                                                     "more_insulin_p", "fewer_passing_total")),
                  "lows_fall_strong": {"median": round(lows[0], 3), "ci": [round(x, 3) for x in lows[1]]},
                  "weak_meeting_aim": sum(aim_met(T[k]["eval_twin"]["cgm"]) for k in keys if k[1] in WEAK)}
    res["weak_meeting_aim_start"] = sum(aim_met(A[k]["eval_start"]["cgm"]) for k in keys if k[1] in WEAK)
    res["C_non_inferior"] = res["C"]["weak_meeting_aim"] >= res["A"]["weak_meeting_aim"] - 2
    out[body] = res
(R / "guard_2026-11-11.json").write_text(json.dumps(out, indent=1))
print(json.dumps(out, indent=1))
