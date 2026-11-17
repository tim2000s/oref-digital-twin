# Lows slept through overnight: what the rule does to the estimates

On 17 November 2026 the rescue rule of the settings tests was changed at the maintainer's
direction. A low that only the changed setting causes was treated with 10 g every 15 minutes at
any hour. Between 23:00 and 07:00, in the profile's time zone, it is now left untreated until
glucose falls below 54 mg/dL, the very-low alert, and from then is treated as before. The hours and
the threshold are a modelling choice. Nothing here was registered before it was run, and the rule
was not put to a pass or fail; this records what it changes.

## Against TimSim, the same fortnight

`same_week.py --rescue` with the night rule, against the truth of the 8 November run
(`results/same_week_2026-11-08.json`); all 12 subjects reproduced their estimates without options
exactly. Figures from `summarise_same_week.py`, pooled over 120 subject-changes, with bootstrap 95%
intervals.

| Measure | Without the night rule (8 Nov) | With it (17 Nov) |
|---|---|---|
| Below 70, Spearman | 0.839 [0.782, 0.893] | 0.872 [0.827, 0.917] |
| Below 70, slope of same fortnight on estimate | 0.878 [0.743, 1.088] | 0.679 [0.579, 0.816] |
| Below 54, Spearman | 0.551 [0.381, 0.685] | 0.689 [0.571, 0.789] |
| Below 54, slope | 0.812 [0.630, 1.304] | 0.759 [0.624, 1.039] |
| In range, slope | 0.482 [0.356, 0.587] | 0.510 [0.400, 0.621] |
| Sign agreement, large changes in time below 70 | 66 of 79 | 75 of 79 |

The ranking of changes by their effect on lows improved and the estimated change in time below 70
became about 1.5 times what followed (slope interval below 1). TimSim's people treat a low at 70
with a delay of 4 to 16 minutes at every hour (`timsim/person/behaviour.py`), so against them a
rule that sleeps through lows overstates lows by construction. Which is nearer a real person asleep
is not measured here.

The larger estimate of lows makes the floors on strengthening (time below 70 under 2%, below 54
under 0.6%) bind more often and moves the fewest-lows fallback towards weaker values. The repeated-
review results in `GUARD.md` and the per-use figures in REVIEW.md were measured under the old rule
and have not been rerun.

## On real records

The page's settings tests were run on 28 real weeks before a setting change (16 Boost, 12
AndroidAPS, from 12 people) with the twin before and after the rule, the guard's history not
applied in either. The chosen values differed in 4 of the 28 weeks. Of the 8 chosen values that
moved, 5 moved towards less insulin. The 3 towards more were each in a week where no value met the
aim and the fallback picked the most time in range with lows under 2%: one SMB limit raised from
30 to 45 minutes in the same week as an ISF strengthening was dropped, one carb ratio step from
0.8 to 0.7 in the same week as an SMB limit cut from 45 to 30 minutes, and one max IOB raised from
14 to 16 U. Basal and target choices did not change. The script is `night_rescue_real.py` in the
maintainer's private analysis repository, since it reads people's records.
