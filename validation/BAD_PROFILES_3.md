# Mis-set profiles through TimSim, third run: the tighter aim. Results

Judged against `BAD_PROFILES_PLAN_3.md`, committed (30dbf38) before the run. The twin aimed for
time in range above 80% and time below 70 under 2%. Everything else matched the second run, whose
mis-set and null arms were reused. Ninety-six round trips, none failed, 16,204 s on seven
workers. Tables from `summarise_bad_profiles_3.py`.

## Verdict against the plan

The plan judged the tighter aim to work when more subject-conditions met it with the tighter twin
than with the standard twin, and no harm criterion was met. Both held, so by the plan it works.
The size of the gain is small.

| Subject-conditions meeting above 80% in range and under 2% below (pooled sensor, of 96) | |
|---|---|
| Mis-set profile | 26 |
| Twin, standard aim | 35 |
| Twin, tighter aim | 37 |

Two subject-conditions met the aim with the tighter twin and not the standard one; none went the
other way. Two against none is not distinguishable from chance on its own (exact sign test,
P = 0.5).

| Harm criterion (any one counts against the tighter aim) | Result |
|---|---|
| Ten or more of 96 rises in time below 54 beyond the null 95th percentile (+0.349) | 0 |
| Any rise above the null maximum (+0.413) | 0 |
| An excess of exceedances among subjects given more insulin | 0 of 38 |
| Fewer subjects passing the pass rule than with the mis-set profile, any condition | none |

## What the tighter aim did

It made the twin give more insulin more often: in 38 of 96 subject-conditions against 14 under
the standard aim, most in the too-weak conditions (all three too weak: 11 of 12; basal ×0.7: 7;
carb ratio ×1.4: 6). None of the 38 produced a rise in time below 54 beyond the noise. The changes
were small. In the all-too-weak condition median time in range went from 76.1% to 77.5%, and
median time below 70 from 0.77% to 0.99%.

The two gains:

| Subject, condition | Standard twin | Tighter twin |
|---|---|---|
| adult#003, basal ×0.7 | 79.0% in range, 0.40% below; no change | 80.4%, 0.38%; carb ratio −20% |
| adult#010, all too weak | 77.9%, 0.60%; basal −30%, carb ratio −10% | 82.7%, 1.23%; the same, and SMB limit 90 minutes |

## Why it did not get more people there

Of the 59 subject-conditions still short of the aim with the tighter twin, 26 fell short on time
in range alone, 21 on lows alone and 12 on both. More insulin cannot fix the 21 and is limited by
the strengthening rule in the 12.

Of the 26 short on range alone, the twin's own estimate on the learning fortnight put 18 above 80%
in range and under 2% below, so it had nothing to change. The evaluation's 84 days on other seeds
then came in at or under 80%. The twin aims at the line on two weeks of data, and a different
period lands about half of the cases near the line on the wrong side of it. Getting people over
80% reliably would need the twin to aim with a margin, for example 83% on the learning data, or
to judge on a longer period. Neither is in the plan; both are untested.

The twin's estimated change in time in range against the realised change: median −0.20 against
0.00, correlation 0.44.

## What follows

The tighter aim is safe on this test and does what it says at the margin, but it moves few
people across the line. It is offered on the page as it is. Whether to add a margin is a separate
decision, and one to test in the same way first.
