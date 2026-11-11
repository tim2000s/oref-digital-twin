"""One use at a time: the change in time below 54 that each review's choices made, on the same fortnight.

    python3 validation/per_use_lows.py

Reads the same-seed check of RATCHET_PLAN.md (results/ratchet_2026-11-09-stepA.json): for each
review, the profile it was given (base) and the profile after its choices (next), both run on that
review's learning seed for 14 days. Median next minus base over cases, bootstrap 95% interval over
subjects, for the reviews that chose more insulin and for all. Writes results/per_use_lows.json.
"""
import json

import numpy as np
from pathlib import Path

from summarise_pace import boot

R = Path(__file__).parent / "results"
rows = json.load(open(R / "ratchet_2026-11-09-stepA.json"))["rows"]
out = {}
for rv in (1, 2, 3):
    for which in ("more", "all"):
        by = {}
        for r in rows:
            for c in r.get("cases", []):
                if c["review"] == rv and (which == "all" or c["original"]["direction"] == "more"):
                    by.setdefault(r["name"], []).append(c["next"]["cgm"]["tbr54"] - c["base"]["cgm"]["tbr54"])
        med, ci = boot({s: np.array(v) for s, v in by.items()})
        out[f"review_{rv}_{which}"] = {"n": sum(map(len, by.values())), "median": round(med, 3),
                                       "ci": [round(x, 3) for x in ci]}
(R / "per_use_lows.json").write_text(json.dumps(out, indent=1))
print(json.dumps(out, indent=1))
