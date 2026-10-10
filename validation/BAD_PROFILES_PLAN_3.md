# Mis-set profiles through TimSim, third run: the tighter aim. Plan, fixed before the run

Written 10 October 2026, before the run. Results go in `BAD_PROFILES_3.md`.

## Question

Can the twin, aiming for time in range above 80% and time below 70 under 2% (the page's
"tighter" aim), get people there, without harm?

## Design

As `BAD_PROFILES_PLAN_2.md` in every respect except the aim: the same twelve subjects, the same
eight mis-set profiles, the same 14-day learning run on seed 202, evaluation on seeds 101 to 103,
28 days each, pooled to 84 days. The twin's strengthening limit (time below 70 under 2% and
below 54 under 0.6% for any change towards more insulin) is unchanged.

The mis-set and null arms do not depend on the twin's aim and TimSim is deterministic, so they
are taken from the second run (`results/bad_profiles_2026-10-09b.json`) rather than rerun. A
reduced case was run both ways before this plan and gave identical twin choices and outcomes.
Only the learning run, the twin and the twin's arm are run.

## Primary outcome

Subject-conditions of 96 meeting the tighter aim on pooled sensor glucose (time in range above
80% and time below 70 under 2%): with the mis-set profile, with the twin on the standard aim
(second run) and with the twin on the tighter aim.

The tighter aim is judged to work when more subject-conditions meet it with the tighter twin
than with the standard twin, and when none of the harm criteria below is met.

## Harm

As the second plan, against the second run's null arm: the 95th percentile of the null changes
in pooled time below 54 (+0.349 points) and the largest (+0.413). Counts against the tighter aim,
any one sufficient: ten or more of 96 exceedances; any rise above the null maximum; exceedances
among subjects given more insulin at a binomial probability under 0.05; fewer subjects passing
the pass rule (above 80% in range, below 70 under 1.5%, below 54 under 0.4%) than with the
mis-set profile in any condition.

## Secondary

Per condition the same tables as the second run; how often the twin gave more insulin; the
estimated against the realised change; and the time in range given up or gained against the
standard aim.
