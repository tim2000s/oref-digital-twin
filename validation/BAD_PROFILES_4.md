# Mis-set profiles through TimSim, fourth run: lows treated in the estimate. Results

Judged against `BAD_PROFILES_PLAN_4.md`, committed (c0765ad) before the run. The twin at fe1e4f7
treated each low a setting change causes with 10 g every 15 minutes and aimed for the tighter goal.
Everything else matched the third run, and the second run's mis-set and null arms were reused.
Ninety-six round trips, none failed, 7,819 s on seven workers. Tables from
`summarise_bad_profiles_3.py` with this run first and the third run second (its "standard twin"
column is then the third run), and from `compare_choices.py`.

## Verdict against the plan

No harm criterion was met, so by the plan the change ships as committed.

| Harm criterion (any one counts against release) | Result |
|---|---|
| Ten or more of 96 rises in time below 54 beyond the null 95th percentile (+0.349) | 1 (P = 0.993) |
| Any rise above the null maximum (+0.413) | 0 |
| An excess of exceedances among subjects given more insulin | 1 of 42 (P = 0.884) |
| Fewer subjects passing the pass rule than with the mis-set profile, any condition | none |

The one exceedance was adult#006 with all three settings too weak: the twin lowered ISF by 20% and
the carb ratio by 30%, and time below 54 rose by 0.384 points, between the null 95th percentile and
its maximum. In the third run the same subject-condition was given ISF −10%, carb ratio −30% and an
SMB limit of 45 minutes, and did not exceed.

## What treating lows changed

The twin chose differently in 19 of 96 subject-conditions and gave more insulin in 42 against the
third run's 38. Subject-conditions meeting the tighter aim went from 37 to 36: one lost, none
gained.

| Subject-conditions meeting above 80% in range and under 2% below (pooled sensor, of 96) | |
|---|---|
| Mis-set profile | 26 |
| Twin, third run | 37 |
| Twin, lows treated | 36 |

The change was concentrated in the condition with the carb ratio 30% too strong, where the
profile already gives too much insulin at meals. There the twin gave more insulin in 6 of 12
against 2, including a basal rise of 10% for adult#002 and of 30% for adult#005 where the third
run had lowered basal by 30%. Median time below 70 in that condition went from 1.86% in the third
run to 2.53% (2.70% with the mis-set profile), median time below 54 from 0.52% to 0.74%, and the
number meeting the aim from 4 to 3. Neither of the two basal rises exceeded the null for time
below 54 (+0.074 and +0.306). The other seven conditions moved by no more than 0.03 points in
median time below 70.

This is the direction the plan anticipated: with lows no longer overstated, the same strengthening
limit lets through changes it used to stop. On this test those changes stayed within the noise of
time below 54, and the plan's harm criteria were set on that measure.

The twin's estimated change in time in range against the realised change: median 0.00 against
0.00, correlation 0.49 (0.44 in the third run).

## What follows

The 10 g rule stays on the page with the strengthening limit unchanged (time below 70 under 2%,
below 54 under 0.6%). The rise in more-insulin choices when the carb ratio is already too strong is
the case to watch: it did not meet a harm criterion here, but it moved median time below 70 back
towards the mis-set profile's in that condition. Twelve simulated adults over 84 days each is the
whole of the evidence.
