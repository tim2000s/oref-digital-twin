# A body model in the twin's simulator, and judging each value across a band of sensitivities: plan

Written 11 November 2026, after the code was written and its unit tests passed, and before any
TimSim run with it. Results go in `BODY.md`.

## Why

The simulator (`replay/oracle/request.js`) re-runs oref every 5 minutes on the logged glucose plus
an offset, and the offset is each extra or withheld unit times the profile ISF, along oref's
insulin curve. Two parts of that are assumptions, not findings.

- Nothing carries the offset after a dose has acted. Between cycles glucose follows the logged
  change, and a finished dose's full effect is kept for the rest of the period. In TimSim the
  realised change from an insulin difference falls to 0.12 of the rule's at 24 hours
  (`DECAY.md`), and the twin's estimate of the change in time below 70 was 2.9 times TimSim's
  (slope 0.348).
- The power of a unit is the profile ISF, which is the setting under test.

## Change

Both are options of a simulate call, off unless given, so the published page is unchanged.

1. Body (`body: {model: "hovorka"}`). A dose still acts as units × ISF along oref's insulin
   curve. The offset it leaves is carried, in steps of about a minute, by the glucose system of
   Hovorka et al. (2004) held at basal insulin: plasma and remote compartments exchanging at
   x1 = 0.02772 and k12 = 0.066 per minute, disposal from the remote one at x2 = 0.00425 per
   minute, non-insulin uptake of 1.091 mg/dL per minute that falls in proportion below 81 mg/dL,
   and renal loss of 0.003 per minute above 162 mg/dL. The rates are the medians of TimSim's 68
   Hovorka subjects with titrated settings, at their basal steady state. Holding insulin's
   actions at basal is a modelling choice: insulin's own effect stays the ISF rule, and the body
   only decides how the offset relaxes, from the glucose level it relaxes at. Linearised above
   81 mg/dL its slow time constant is 13.7 hours, against the 2.4 hours fitted to S2008.
2. Band (`isf_band`, given to the settings tests). Every value of every stage is simulated with
   the body's sensitivity at the profile ISF × 0.7, × 1 and × 1.3, oref still dosing with the
   profile ISF, and is judged on the least favourable of the three: least time in range, most
   time below 70 and 54, most lows. The strengthening limit reads the same values. The tables and
   final estimate show × 1. The band's width is a modelling choice, the size of the mis-set
   conditions.

## Part 1: how far off each estimator is (same fortnight)

`same_week.py`: for each subject, the twin's estimate of ten changes against TimSim's rerun of
the same fortnight with each change. Measures, as `SAME_WEEK.md`: per measure (time below 70,
time in range, time below 54), the slope of TimSim's change on the estimated change (1 means the
estimate is the right size, under 1 means it is overstated) and the Spearman correlation, each
with a bootstrap 95% interval over subjects (`summarise_same_week.py`).

- S2008: the twelve adults, truth from `results/same_week_2026-11-08.json` (reproduced exactly
  by the current code for adult#001 on 11 November). Estimators: current, decay of 144 minutes,
  body.
- Hovorka: the first twelve of TimSim's titrated Hovorka subjects, a new truth run, then the same
  three estimators.

S2008 is the real test of the body, since the model inside the twin differs from the body
simulated. On the Hovorka body the twin's model is that body's glucose system, but with insulin at
basal and the profile ISF as the dose's power, so agreement there checks the implementation more
than it validates anything.

The body goes forward as the twin's default candidate when, on S2008, its slope for time below 70
is above the current twin's with the two intervals not overlapping, and its Spearman correlation
for time below 70 lies within the current twin's interval. Part 2 runs whatever part 1 shows,
since the round trip is the test of advice.

Expected, stated before the run: on S2008 the body's slopes lie between the current twin's
(0.35 for time below 70) and the decay's (0.97), nearer the decay for time below 70, because its
pull-back is fastest below 81 mg/dL, and nearer the current twin for time in range, because above
81 it relaxes over 14 hours, not 2.4.

## Part 2: does the advice improve? (round trip, relative only)

`timsim_roundtrip.py` with the design of `GUARD_PLAN.md`: eight mis-set conditions, twelve
subjects, three reviews, tighter aim, evaluation seeds 101 to 103 over 28 days, null arm. On each
body, two new arms against that body's arm A (the current page), reusing its mis-set and null
arms:

| Body | Arm A (current page) | Arm H (body) | Arm HB (body and band) |
|---|---|---|---|
| S2008 | `bad_profiles_2026-11-09-stepA.json` | `--body hovorka` | `--body hovorka --isf-band 0.7,1,1.3` |
| Hovorka | `bad_profiles_2026-11-10-hovA.json` | the same | the same |

The band's effect is HB against H, and the body's is H against A. TimSim supports comparisons
within a subject, not absolute levels, so the judgement is relative. Per subject-condition,
evaluation (pooled sensor over the three seeds) minus arm A's, for time below 54 and time in range;
median over the 96 with a bootstrap 95% interval over subjects.

An arm goes forward when, on both bodies, the interval for the change in time below 54 lies
wholly below zero and the median change in time in range is no worse than −1 point. The −1 point
is a modelling choice: it lets an arm buy fewer lows with a little range, not more. Reported as
well: the harm counts of `BAD_PROFILES_PLAN_4.md` against each body's null arm, so arms can be set
beside the earlier ones; the cases with too little insulin meeting the aim; the medians by
condition; and how often each stage moved towards more insulin.

Expected, stated before the run: H reduces time below 54 against A on S2008, less so on Hovorka;
HB reduces it further on both, at a cost in time in range in the conditions with too little
insulin, which the −1 point may not cover.

## Limits

The parameters are the Hovorka population's medians, the same for every person; nothing is
fitted to anyone's records. The band does not learn the sensitivity, it only refuses changes that
fail at either end. Both are tested only in TimSim, whose two bodies bracket the twin's error
without measuring it in people.

## Amendment, 11 November 2026, while part 1 was running and before any result was read

A fresh-context review of 0f8be5d found the sentence "The tables and final estimate show × 1"
wrong in part: each row's time in range, time below 70 and 54 and lows are the least favourable
across the band, as the choice uses them; only the insulin difference, the mean shift and the final
estimate are at × 1. The code does what the rest of this plan says, so nothing is rerun. Three
nits wait for the runs to finish, since the runs read the same files: a `body_isf_scale` of 0 is
taken as 1; an extra dose dated before the first cycle loses, with the body, the part absorbed
before it; an integer 1 in the band misses the cache once.
