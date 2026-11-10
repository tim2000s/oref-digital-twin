# Does the overnight rule of thumb point basal the right way? Plan, fixed before the run

Written 10 November 2026, before the script was run. Results go in `BASAL_RULE.md`.

## Why

The twin chooses a basal change from its own estimate of time in range, and that estimate
overstates the gain from more insulin about threefold (`RESPONSE.md`, `RATCHET_PLAN.md`). The
clinical rule of thumb reads the direction from what the loop did instead: overnight, with no food
on board, glucose above target with net insulin on board above zero means the loop has been adding
insulin to the schedule, so basal is probably too low; glucose below target with net insulin on
board below zero means it has been withholding, so basal is probably too high. Changes are made in
steps of about 10%. This check asks only whether the rule gives the right direction, before it is
built into anything.

## Design

The twelve S2008 adults of `titrated_2026-10-09.json`, each of the nine conditions of
`timsim_roundtrip.CONDITIONS` (titrated and the eight mis-set ones), 14 days on the learning seed
202 with the mis-set profile, as review 1 of every run so far saw it. Four workers, beside the
guard runs.

For each night, the 5-minute steps from 00:00 to 06:00 are used, less any step within 5 hours
(the insulin's duration of action) after announced carbohydrate; a night with under 3 hours left is
not counted. Per night: the median sensor glucose and the mean of oref's net insulin on board (its
`IOB`, which is net of the scheduled basal), against the profile's target midpoint (110 mg/dL).

- A night votes up when median glucose is above the target midpoint and mean net insulin on board
  is above +0.1 U.
- A night votes down when median glucose is below the midpoint and mean net insulin on board is
  below −0.1 U.
- The rule says up when at least 60% of the counted nights vote up, down when at least 60% vote
  down, and hold otherwise, or when fewer than 7 nights were counted.

The 0.1 U, 60% and 7-night thresholds are modelling choices. The per-night figures are kept, so
other thresholds can be read from the same file and will be reported as such, not as the result.

The right answer is the direction back towards the titrated basal: up for basal_low and all_weak,
down for basal_high and all_strong, and hold for the other five, whose basal is the titrated one.
The twin's own basal choice at review 1 for the same subject-conditions, from
`bad_profiles_2026-11-09-stepA.json`, is set beside it (no titrated condition there).

## Judgement

The rule goes forward to being planned as a basal stage when both hold:

- it gives the right direction in at least 36 of the 48 basal-wrong cases (75%);
- it holds in at least 45 of the 60 basal-right cases (75%), so it does not move a correct basal
  because of a wrong ISF or carb ratio.

Reported as well: the twin's basal choice scored the same way, the counts by condition, and how
often the rule pointed the wrong way (up where down was right, or the reverse), which matters
more than a hold.

Expected, stated before the run: right in most basal_low and basal_high cases; less clear in
all_weak and all_strong, where the ISF and carb ratio errors add to the overnight picture; some
false ups in isf_weak and cr_weak, where under-corrected evening highs carry into the night.

## Limits

The titrated basal is TimSim's titration under its trend loop, not a basal proven right under
oref, so "hold" being right in the five basal-right conditions is an assumption. Unannounced meals
in TimSim are invisible to the rule, as they would be in real data.

## Amendment, 10 November 2026, while the run was going and before any result was read

TimSim supports relative comparisons, not absolute ones: the titrated basal is not known to be
right for oref, so scoring the rule against "the right answer" above claims more than the simulator
can give. The judgement above is withdrawn and replaced by two comparisons within each subject on
the same seed; the counts against the titrated basal are still printed but decide nothing.

- Ordering. Mean overnight net insulin on board, and the share of nights voting up, should rank
  basal_low above titrated above basal_high. The rule goes forward when the mean net insulin on
  board is in that order in at least 10 of the 12 subjects. By chance a given order of three
  comes up one time in six, so 10 of 12 is far beyond chance (P < 0.0001); the bar is set for
  consistency, not significance.
- Specificity. The change in the share of nights voting up, against titrated, should be smaller
  for a 30% ISF or carb-ratio error than for a 30% basal error. The rule goes forward when the
  median absolute change across isf_strong, isf_weak, cr_strong and cr_weak is under half the
  median absolute change across basal_low and basal_high. Half is a modelling choice.

Neither decides use on real data; that needs its own test on real records.
