# Mis-set profiles through TimSim, fourth run: lows treated in the estimate. Plan, fixed before the run

Written 7 November 2026, before the run. Results go in `BAD_PROFILES_4.md`.

## Question

The settings tests now treat a low the changed setting causes with 10 g every 15 minutes
(`validation/RESCUE.md`). That made the estimated change in time below 70 about the right size in
TimSim, where before it was about three times too large. The limit on suggesting more insulin
(estimated time below 70 under 2% and below 54 under 0.6% over the whole period) was validated by
the third run with the old estimate, so with lows no longer overstated the same limit may let
through changes it used to stop. Is the twin, aiming for the tighter goal with lows treated, still
without harm?

## Design

As `BAD_PROFILES_PLAN_3.md` in every respect except the estimate: the same twelve subjects, the same
eight mis-set profiles, the 14-day learning run on seed 202, evaluation on seeds 101 to 103, 28 days
each, pooled to 84 days, the tighter aim and the same strengthening limit. The mis-set and null arms
are reused from `results/bad_profiles_2026-10-09b.json`, as the third run reused them; only the
learning run, the twin and the twin's arm are run. The twin is at commit fe1e4f7.

## Harm

Exactly as the third plan, against the second run's null arm: the 95th percentile of the null
changes in pooled time below 54 (+0.349 points) and the largest (+0.413). Any one counts against
releasing this change: ten or more of 96 exceedances; any rise above the null maximum; exceedances
among subjects given more insulin at a binomial probability under 0.05; fewer subjects passing the
pass rule (above 80% in range, below 70 under 1.5%, below 54 under 0.4%) than with the mis-set
profile in any condition.

## Decision

No harm criterion met: the change ships as committed. Any one met: the strengthening limit is
tightened by the ratio of the two estimators' time-below-70 slopes (0.348 / 0.874, so under 0.8%
below 70 and 0.24% below 54), which restores the effective limit the third run validated, and the
run is repeated with that limit before release.

## Secondary

Subject-conditions of 96 meeting the tighter aim, against the third run's 37; how often the twin
gave more insulin, against the third run's 38 of 96; per condition the tables of the earlier runs.
