# Strengthening a too-weak ISF or basal when it gains time in range: results

The rule of `WEAK_FIX_PLAN.md` (ad31d0a) was run on the fourth mis-set run's design on 8 and 9
November 2026: 96 subject-conditions, none failed, 10,250 s on seven workers. Results in
`results/bad_profiles_2026-11-08-weakfix.json`; the comparison is the settings-fix run
(`results/bad_profiles_2026-11-08-fix.json`). Figures from `summarise_bad_profiles_3.py` and
`summarise_weak_fix.py` on that pair.

The change fails both conditions of the plan and was reverted.

| Harm criterion | Counts against release when | Result |
|---|---|---|
| Exceedances of the null 95th percentile (+0.349 points below 54) | 10 or more of 96 | 11 (P 0.009) |
| Rises above the null maximum (+0.413) | any | 10 |
| Exceedances among subjects given more insulin | binomial P < 0.05 | 11 of 61, P < 0.001 |
| Conditions with fewer meeting the pass rule than the mis-set profile | any | basal too high, basal too low, carb ratio too weak |

Of the 48 subject-conditions with too little insulin, 21 met the tighter aim against 22 in the
comparison run, where the plan needed more than 22. Over all 96 the count fell from 34 to 30.

The rule did move ISF where it was meant to. With ISF too weak, ISF moved towards its titrated value
in 8 of 12 against 1 of 12 before, and with everything too weak in 11 against 6; median time in
range rose by 1.7 and 3.8 points in those two conditions. Basal did not move in either weak
condition (0 and 1 of 12, as before).

It also moved ISF where it was not needed. The twin took the strongest ISF on its grid (0.7 of the
mis-set value) in 35 of 96 subject-conditions, against none in the comparison run, and in every
condition including those where ISF or basal was already too strong. Adult#007 accounts for 7 of the
11 exceedances: its ISF went to 0.7 in each, and where ISF was already set too strong it ended at
0.49 of titrated. Median time below 54 rose in seven of the eight conditions, by most with ISF too
weak (0.24% to 0.43%) and carb ratio too weak (0.49% to 0.68%).

The rule judges ISF on the whole period's estimated time in range, which keeps rising as ISF
strengthens up to the end of the grid. A 2-point margin over the smallest change does not stop that,
and the strengthening limit, set at whole-period time below 70 under 2% and below 54 under 0.6%,
did not bind for these subjects. The estimate overstated the gain: median estimated change in time
in range +0.40 points against a realised +0.00.

Not tested here: a margin that grows with distance from the current value, or a cap on how far one
review moves ISF. Either would need its own plan.
