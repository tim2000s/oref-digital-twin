# Same-fortnight accuracy of the twin's estimates in TimSim: plan, fixed before the run

Written 10 October 2026, before the run. Results go in `SAME_WEEK.md`.

## Question

The twin's figures answer "what would this period have looked like with these settings and
nothing else different?". Real data cannot check that, because the other period never happened.
TimSim can, because a period can be replayed exactly. How close are the twin's estimates to the
same fortnight replayed under the changed settings?

The earlier TimSim comparisons scored the twin's estimates against a different month, so they
mixed estimate error with month-to-month variation.

## Design

The twelve TimSim adults with their titrated profiles (`results/titrated_2026-10-09.json`), the
14-day learning run on seed 202 under TimSim's oref0 controller (TimSim at e64cf2e or later), and
the twin at 4cb801a with max IOB, SMB limits, insulin curve and max basal passed as a settings
file.

Ten changes, each applied to the whole profile:

| Change | Basal | ISF | Carb ratio | Target |
|---|---|---|---|---|
| basal_down | ×0.7 | | | |
| basal_up | ×1.3 | | | |
| isf_strong | | ×0.7 | | |
| isf_weak | | ×1.3 | | |
| cr_strong | | | ×0.7 | |
| cr_weak | | | ×1.3 | |
| target_down | | | | −18 mg/dL |
| target_up | | | | +18 mg/dL |
| all_strong | ×1.3 | ×0.7 | ×0.7 | |
| all_weak | ×0.7 | ×1.3 | ×1.3 | |

For each subject and change:

1. The twin's estimate: its closed-loop simulator run on the exported learning fortnight under the
   change, scored on the CGM readings over the whole fortnight.
2. The same-fortnight truth: TimSim rerun on seed 202 with the changed profile, so meals, sensor
   noise and physiology are identical and only the settings and their consequences differ.

Both are scored by one function on sensor glucose: time in range 70 to 180 mg/dL, below 70, below
54. Change is each minus the unchanged fortnight. A rerun with nothing changed is also made per
subject and must reproduce the learning run exactly. A difference there invalidates that subject.

## Analysis

Across the 120 subject-changes, for time below 70, time in range and time below 54:

- Spearman correlation between estimated and same-fortnight change.
- The slope of same-fortnight on estimated change, with a 95% interval from bootstrapping subjects.
- The median ratio of estimated to same-fortnight change, per change type.
- Sign agreement where the same-fortnight change is at least 0.5 points (below 70) or 2 points
  (in range).

The estimates are called informative on a measure when the correlation's interval excludes zero,
and calibrated when the slope's interval includes 1. Each is reported per change type as well as
pooled.
