# A body model in the twin's simulator, and judging each value across a band of sensitivities: results

Run on 11 November 2026 to `BODY_PLAN.md`, as amended, on branch `body-model`. Part 1 figures come
from `summarise_same_week.py` on the `same_week_*` files; part 2 from `summarise_body.py`
(`results/body_part2_2026-11-11.json`) and `summarise_bad_profiles_3.py`. No run failed.

The body brings the twin's estimates close to the right size and passes part 1. Neither arm goes
forward from part 2: on S2008 the change in time below 54 is not distinguishable from zero, on
Hovorka it falls but time in range falls by more than the plan allows, and on S2008 more
subject-conditions rose in time below 54 beyond anything the null arm showed than with the current
page.

## Part 1: how far off each estimator is

Slope of TimSim's change on the twin's estimated change, over 12 subjects and 10 changes each,
with bootstrap 95% intervals over subjects. 1 means the estimate is the right size.

| Body | Estimator | Below 70 | In range | Below 54 | Spearman, below 70 |
|---|---|---|---|---|---|
| S2008 | Current | 0.35 (0.30–0.41) | 0.54 (0.42–0.68) | 0.27 (0.20–0.33) | 0.865 (0.817–0.914) |
| S2008 | Decay, 144 min | 0.92 (0.79–1.12) | 1.13 (0.90–1.45) | 0.73 (0.58–0.98) | 0.853 (0.798–0.908) |
| S2008 | Body | 0.83 (0.71–0.99) | 0.85 (0.70–1.04) | 0.85 (0.69–1.06) | 0.866 (0.816–0.916) |
| Hovorka | Current | 0.34 (0.26–0.41) | 0.63 (0.56–0.73) | 0.24 (0.15–0.30) | 0.868 (0.814–0.917) |
| Hovorka | Decay, 144 min | 0.80 (0.60–0.97) | 1.12 (0.96–1.41) | 0.64 (0.45–0.74) | 0.865 (0.819–0.912) |
| Hovorka | Body | 0.74 (0.57–0.90) | 0.91 (0.80–1.09) | 0.72 (0.52–0.83) | 0.866 (0.820–0.911) |

On S2008 the body's interval for time below 70 lies wholly above the current twin's and its
Spearman correlation lies within the current twin's interval, so it passes the plan's rule. The
ranking of changes was unaffected by any estimator; only their size moved. The prediction was
right for time below 70 and wrong for time in range, where the body came out at 0.85, nearer the
decay than the current twin. The decay's time constant had been fitted to S2008; the body's rates
were fitted to neither body.

## Part 2: does the advice improve?

Each figure is the arm's evaluation minus arm A's (the current page) for the same subject and
condition, sensor pooled over three seeds, median over 96 subject-conditions with a bootstrap 95%
interval over subjects. Points of percentage time.

| Body | Comparison | Below 54 | Below 70 | In range | Goes forward here |
|---|---|---|---|---|---|
| S2008 | H − A | −0.03 (−0.09 to +0.00) | −0.21 (−0.31 to −0.13) | −0.80 (−1.58 to −0.10) | No: below 54 interval reaches 0 |
| S2008 | HB − A | −0.02 (−0.07 to +0.01) | −0.06 (−0.19 to +0.10) | −0.90 (−2.33 to 0.00) | No: below 54 interval spans 0 |
| S2008 | HB − H | −0.00 (−0.04 to +0.00) | 0.00 (−0.05 to +0.19) | 0.00 (−0.50 to +0.02) | |
| Hovorka | H − A | −0.21 (−0.28 to −0.00) | −0.56 (−0.93 to +0.18) | −2.50 (−6.12 to −0.22) | No: in range below −1 |
| Hovorka | HB − A | −0.26 (−0.38 to −0.13) | −0.81 (−1.15 to −0.15) | −3.14 (−7.90 to −1.79) | No: in range below −1 |
| Hovorka | HB − H | −0.01 (−0.12 to +0.02) | −0.06 (−0.24 to 0.00) | −1.16 (−1.95 to −0.14) | |

Neither H nor HB goes forward, since the rule needs both bodies. On S2008 the band changed little
against H: 12 of 96 subject-conditions had identical time below 54 and 9 identical time in range.
On Hovorka the band cost a further 1.2 points of time in range (interval −1.9 to −0.1) for no
change in time below 54 that the interval can separate from zero.

The medians hide the tail. Harm counts, against each body's null arm (a rise in time below 54 from
the mis-set start larger than the null arm's 95th centile is an exceedance):

| Body | Arm | Exceedances of 96 | Above the null maximum | Given more insulin | Meeting the tighter aim |
|---|---|---|---|---|---|
| S2008 | A | 9 | 6 | 83 | 37 |
| S2008 | H | 9 | 9 | 84 | 39 |
| S2008 | HB | 14 | 13 | 79 | 35 |
| Hovorka | A | 24 | 12 | 91 | 0 |
| Hovorka | H | 19 | 13 | 81 | 0 |
| Hovorka | HB | 15 | 11 | 77 | 0 |

On S2008 both new arms put more subject-conditions above the null maximum than arm A, HB more than
twice as many. Every exceedance in every new arm followed advice for more insulin, and most of the
large ones carried an ISF strengthened to ×0.39 to ×0.73 of the mis-set value, in a few subjects (adult#008 and adult#011 on S2008, hovorka#008, #013 and #015 on
Hovorka) who recur across conditions. The guard of `GUARD_PLAN.md` gave 2 above the maximum on
each body, for comparison.

Median time in range under the advice, against the mis-set start, sensor:

| Condition | S2008 start | S2008 A | S2008 H | S2008 HB | Hovorka start | Hovorka A | Hovorka H | Hovorka HB |
|---|---|---|---|---|---|---|---|---|
| isf_strong | 84.3 | 82.5 | 81.1 | 78.2 | 75.5 | 73.9 | 69.3 | 65.7 |
| isf_weak | 81.6 | 80.2 | 81.0 | 79.4 | 68.7 | 70.8 | 68.2 | 65.2 |
| basal_high | 85.9 | 81.4 | 82.5 | 80.1 | 77.0 | 72.9 | 73.3 | 63.7 |
| basal_low | 80.3 | 81.2 | 82.0 | 81.6 | 66.9 | 73.9 | 63.2 | 66.8 |
| cr_strong | 83.2 | 83.6 | 81.6 | 77.6 | 73.6 | 73.5 | 72.1 | 65.6 |
| cr_weak | 81.8 | 81.9 | 81.4 | 80.9 | 72.7 | 70.8 | 68.6 | 69.4 |
| all_strong | 84.9 | 82.2 | 79.4 | 81.0 | 77.1 | 73.0 | 64.2 | 63.9 |
| all_weak | 76.1 | 80.1 | 80.1 | 80.3 | 59.6 | 71.9 | 68.4 | 66.2 |

On Hovorka median time in range ended below the mis-set start in 5 of 8 conditions under arm A and
in 7 under each body arm. The twin's own estimate of
the change in time in range still exceeded what happened: on S2008 a median estimated +0.10 points
against a realised −1.65 for H, and on Hovorka +3.10 against −2.64.

Expected, stated in the plan: H reduces time below 54 on S2008, less so on Hovorka; HB reduces it
further on both, at a cost in range. The reduction was larger on Hovorka than on S2008, the band
added nothing on S2008, and its cost in range on Hovorka was as expected.

## What follows

The body corrects the size of a single change's estimate, which was the fault it was built for.
The advice is no better for it, because the stages still take any change the twin rates as an
improvement, and with a smaller estimated cost in lows the twin now rates more insulin as an
improvement in the same subjects. The band does not stop this: judging
on the least favourable sensitivity left the choices on S2008 mostly unchanged. The choice rule,
one of the faults listed before this work, is untouched by these runs and is the next thing to
test.

The three nits recorded in the plan's amendment are still open.
