# Settings read and replayed as configured: results of the rechecks

Judged against `SETTINGS_FIX_PLAN.md` (4f65e62), committed before the runs. The twin was at
48e1f3b. The four runs were made in sequence by `rerun_settings_fix.sh` on 8 November 2026, from
15:10 to 18:44, on seven workers.

## Verdict against the plan

| Run | Judged by | Result |
|---|---|---|
| 2, same fortnight with the 10 g rule | Time-below-70 slope interval includes 1, Spearman at least 0.815 | Passed: slope 0.878 [0.743, 1.088], Spearman 0.839 [0.782, 0.893] |
| 4, harm on mis-set profiles | Any one of the four criteria of `BAD_PROFILES_PLAN_4.md` | None met; the fixes ship with the strengthening limit unchanged |

Runs 1 and 3 carry no criterion and are reported beside the earlier figures.

## Run 1: same fortnight in TimSim, without options

All 12 learning runs reproduced themselves. TimSim truth was recomputed
(`results/same_week_2026-11-08.json`).

| Measure | Spearman | Slope of realised on estimated | Before the fixes (Spearman, slope) |
|---|---|---|---|
| Time below 70 | 0.865 [0.817, 0.914] | 0.353 [0.303, 0.408] | 0.863, 0.348 |
| Time in range | 0.551 [0.367, 0.734] | 0.536 [0.424, 0.679] | slope 0.534 |
| Time below 54 | 0.616 [0.476, 0.788] | 0.267 [0.203, 0.325] | 0.608, 0.264 |

Turning UAM on and taking the daily basal as the day's largest rate moved every figure by less
than its interval's width. Without the 10 g rule the estimate for lows is still about three times
too large, as before.

## Run 2: the same, with the 10 g rule

Against the truth of run 1, all 12 subjects reproducing run 1's estimates without options
(`results/same_week_rescue10g_new_2026-11-08.json`).

| Measure | Spearman | Slope | 7 November (`RESCUE.md`) |
|---|---|---|---|
| Time below 70 | 0.839 [0.782, 0.893] | 0.878 [0.743, 1.088] | 0.819, 0.874 |
| Time in range | 0.571 [0.357, 0.750] | 0.482 [0.356, 0.587] | slope 0.482 |
| Time below 54 | 0.551 [0.381, 0.685] | 0.812 [0.630, 1.304] | 0.583, 0.830 |

The README's description of the estimate's accuracy stands.

## Run 3: twelve real AndroidAPS changes

Each logged SMB switch and both basal safety multipliers were now passed. Spearman of estimated
against realised change, one-sided permutation, results in the private analysis repository
(`twin_backtest/results_aaps_fix.json` and `results_aaps_rescue_fix.json`).

| Arm | Below 70 | In range | Below 54 | 7 November |
|---|---|---|---|---|
| Without options | +0.18 (p 0.28) | +0.55 (p 0.035) | +0.52 (p 0.045) | +0.11, +0.66, +0.41 |
| 10 g rule, new lows only | +0.01 (p 0.49) | +0.74 (p 0.004) | +0.37 (p 0.12) | +0.16, +0.72, +0.33 |

With twelve events from five people, none of these differences from 7 November can be told from
chance. With the rule, time in range still ranks the real changes and time below 70 still does
not.

## Run 4: harm on mis-set profiles

Ninety-six round trips, none failed, 9,903 s. The mis-set and null arms were reused from
`results/bad_profiles_2026-10-09b.json`, as in the third and fourth runs.

| Harm criterion (any one counts against release) | Result |
|---|---|
| Ten or more of 96 rises in time below 54 beyond the null 95th percentile (+0.349) | 1 (P = 0.993) |
| Any rise above the null maximum (+0.413) | 0 |
| An excess of exceedances among subjects given more insulin | 1 of 47 (P = 0.910) |
| Fewer subjects passing the pass rule than with the mis-set profile, any condition | none |

The one exceedance was adult#006 with all three settings too weak, at +0.384 points, the same
subject-condition as in the fourth run (+0.384 there as well).

The fixed twin gave more insulin in 47 of 96 subject-conditions, against 42 before the fixes, and
34 met the tighter aim against 36 (26 with the mis-set profile). The two lost were in the
conditions with ISF too strong and with the carb ratio too weak. Median time below 70 with the carb ratio
too strong was 2.40% against 2.53% before the fixes.

| Subject-conditions meeting above 80% in range and under 2% below (pooled sensor, of 96) | |
|---|---|
| Mis-set profile | 26 |
| Twin before the fixes (`BAD_PROFILES_4.md`) | 36 |
| Twin with the fixes | 34 |

## What follows

The fixes stay, with the 10 g rule and the strengthening limit as they were. Twelve simulated
adults remain the whole of the TimSim evidence, and twelve events from five people the whole of
the real evidence.
