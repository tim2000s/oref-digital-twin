# Does the overnight rule of thumb point basal the right way? Results

`BASAL_RULE_PLAN.md`, as amended before any result was read, run on 10 November 2026 by
`overnight_basal_check.py` (2,774 s, four workers beside the guard run). Results in
`results/overnight_basal_2026-11-10.json`: twelve S2008 adults, nine conditions, 14 days on seed
202 with the mis-set profile, a median of 11 nights per fortnight counted after leaving out the
5 hours after announced carbohydrate.

The rule passes the ordering test and fails the specificity test, so it does not go forward as a
basal stage in this form.

## Ordering

Mean overnight net insulin on board ranked basal ×0.7 above ×1.0 above ×1.3 in 10 of 12 subjects,
at the plan's bar. Medians over subjects:

| Condition | Mean net IOB overnight, U | Share of nights voting up |
|---|---|---|
| basal_low (×0.7) | 2.32 | 0.81 |
| titrated | 2.04 | 0.68 |
| basal_high (×1.3) | 1.54 | 0.52 |
| isf_strong | 2.43 | 0.65 |
| isf_weak | 1.76 | 0.80 |
| cr_strong | 1.90 | 0.75 |
| cr_weak | 1.97 | 0.78 |
| all_strong | 2.07 | 0.56 |
| all_weak | 1.98 | 0.96 |

## Specificity

Against titrated, a 30% ISF or carb-ratio error moved the share of nights voting up by a median of
0.101, and a 30% basal error by 0.096. The plan required the first to be under half the second. A
weak ISF raised the share of up nights as much as a low basal did, and a strong ISF raised net
insulin on board more than a low basal did. In a loop, the night carries the correction settings
as well as the basal: the loop doses overnight through the ISF, and an under-corrected evening
stays high into the night.

## Other figures, deciding nothing

No night anywhere voted down: with the same thresholds the rule said up or hold in all 108
fortnights, including 5 of 12 with basal ×1.3. Mean net insulin on board stayed above 1.5 U
overnight in every condition. TimSim cannot say whether that level is right for oref, and the
plan's amendment set it aside for that reason. For comparison, the twin's own basal choice at
review 1 (`bad_profiles_2026-11-09-stepA.json`) never moved basal up in basal_low (5 down, 7 held)
and moved it down in 8 of 12 basal_high, so its direction for basal is no better.

## What follows

The overnight signal responds to basal in the right order, but not specifically. A form worth
testing would have to separate the two, for example by using only nights with no correction or
SMB after a set hour, or by reading the drift of glucose at near-zero net insulin rather than the
level of insulin on board. Neither was tested here.
