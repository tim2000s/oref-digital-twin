# A guard on repeated strengthening: results, and the criteria corrected

The guard of `GUARD_PLAN.md` was run on 10 November 2026 on both TimSim bodies, three reviews
applied in full (`bad_profiles_2026-11-10-guardC.json`, `bad_profiles_2026-11-10-hovC.json`).
Figures are from `summarise_guard.py` (`results/guard_2026-11-11.json`), and from
`summarise_pace.py` where marked.

## Against its plan

The guard failed one criterion of its plan: any rise in time below 54 above the null arm's
maximum, of which it had 2 on each body. It met every other criterion on both bodies and was
non-inferior on the cases with too little insulin (S2008: 22 meeting the tighter aim against the
page's 20; Hovorka: 0 against 0). By its plan it did not go forward.

## The criteria corrected

After the guard's results had been read, two criteria were found to be met by the null arm, which
changes max IOB by 0.03 U and nothing else, or to be unable to vary (`PACE_PLAN.md`,
`null_criteria.py`). They were corrected on 11 November 2026 and each corrected criterion was
applied to the null arm before any arm was judged by it. Because this happened after the results
were known, what follows is a re-reading of stored runs, not a pre-registered pass.

| Criterion, any one counts against an arm | As planned | Corrected | Null arm, S2008 | Null arm, Hovorka |
|---|---|---|---|---|
| Exceedances of the null 95th percentile | 10 or more of 96 | unchanged | not met | not met |
| Rises above the null maximum | any | 5 or more (chance 0.030 for an arm exchangeable with the null) | not met | not met |
| Exceedances among those given more insulin | binomial P < 0.05 | unchanged | not met | not met |
| Fewer meeting the pass rule than at the mis-set start | in any condition (the null arm meets it on S2008) | over all 96 | not met: 15 to 19 | cannot vary: 0 to 0 |

On Hovorka no subject-condition meets the pass rule at the start or under any arm, so the last
criterion says nothing there.

## Re-read under the corrected criteria

| Body | Arm | Exceedances | Above the null maximum | Exceedances among more insulin | Passing, start to end | Harm criterion met | Change in time below 54, too much insulin (48) |
|---|---|---|---|---|---|---|---|
| S2008 | A, page | 9 | 6 | 9 of 83, P = 0.023 | 15 to 27 | yes, two | −0.36 (−0.77 to −0.19) |
| S2008 | C, guard | 5 | 2 | 5 of 79, P = 0.36 | 15 to 31 | none | −0.34 (−0.81 to −0.21) |
| S2008 | P, guard and pace | 1 | 0 | 1 of 64, P = 0.96 | 15 to 32 | none | −0.67 (−0.91 to −0.28) |
| Hovorka | A, page | 24 | 12 | 24 of 91, P < 0.001 | 0 to 0 | yes, three | −0.45 (−0.63 to −0.18) |
| Hovorka | C, guard | 7 | 2 | 7 of 91, P = 0.17 | 0 to 0 | none | −0.49 (−0.72 to −0.27) |
| Hovorka | P, guard and pace | 0 | 0 | 0 of 71, P = 1.0 | 0 to 0 | none | −0.74 (−1.21 to −0.65) |

Paired against the page (`summarise_pace.py`), the guard's time in range changed by 0.00 points
(−0.47 to 0.00) on S2008 and 0.00 (−1.91 to 0.00) on Hovorka, and pace's by −0.58 (−1.01 to 0.00)
and −4.44 (−7.38 to −2.68). No row under the guard ended more than 20% towards more insulin, against
59 and 51 of 96 under the page.

## What follows

The guard goes to the page, without pace: it removed the harm the page showed over repeated full
application at no measured cost in time in range, where pace bought somewhat fewer lows at a cost
in range on Hovorka. In use the page keeps nothing between visits, so the guard's history is read
from Nightscout (`replay.inputs.guard_history`): the reference is the profile in force 90 days
before, and the last change and the fortnight either side of it come from lasting Profile
Switches (AndroidAPS) or profile documents (Trio, Loop). The 90 days is a modelling choice. None of
this has been tested on people's records; the evidence is twelve simulated adults on each of two
bodies, most of whom were not running high at the start.
