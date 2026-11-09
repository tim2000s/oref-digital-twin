# Does the twin's estimate of a stronger setting track TimSim once glucose is allowed to return? Plan

Written 9 November 2026, before anything below was computed. Results go in `RESPONSE.md`.

## Why

`WEAK_FIX.md` reverted a rule that took the basal or ISF with the most estimated time in range.
`weak_fix_diagnosis.py` compared, for the 36 subject-conditions where that rule changed the choice,
the twin's estimated difference between the two choices (learning fortnight) with the difference
TimSim produced on evaluation. The estimate of time in range was a median +3.75 points against +0.95
realised, with a per-case correlation of −0.04. Time below 70 was +0.65 against +0.70. Extra insulin
was +1.19 U/day against +3.20.

`DECAY.md` already found the mechanism in TimSim: glucose follows an insulin difference for an hour
or two and then returns, with a time constant of about 2.4 h, where the twin keeps the shift for the
rest of the period. The simulator's `decay_tau_min` option models that return. It is off on the page
because the time constant was measured from interventional TimSim runs and cannot be read from one
person's record (`RESCUE.md`). This plan first asks whether the return accounts for the failure, then
whether it can be measured from a person's own fortnight.

## Step 1: the existing correction on the 36 cases

For each of the 36, regenerate the learning fortnight (TimSim is deterministic on seed 202), take
the replay inputs the twin builds from it, and estimate both runs' chosen settings under three arms:

| Arm | Rescue | Decay |
|---|---|---|
| Page | 10 g, new lows only | none |
| Decay | 10 g, new lows only | 144 min |
| Decay, no rescue | none | 144 min |

The page arm must reproduce the stored estimates (`twin_estimate.est_all` in both result files) for
every case; any mismatch stops the step as a fault.

For each arm, the estimated difference (fix run's choice minus comparison run's choice) is set
against the realised difference in pooled sensor outcomes on evaluation, for time in range, below 70
and below 54, and for insulin per day.

Expected direction, stated before computing: the decay shrinks the estimated gain in time in range,
since a shift that returns cuts fewer highs, and raises estimated insulin, since the loop then sees
glucose that has not fallen as far.

An arm is taken to account for the failure when both hold for time in range:

- the median estimated difference is no more than 1.5 times the median realised difference
  (+0.95 points, so at most +1.43);
- the Spearman correlation between estimated and realised difference has a 95% bootstrap interval
  (10,000 resamples of cases) above zero.

Reported beside it, without a criterion: the same figures for the other measures, and the count of
cases where estimated and realised time in range agree in sign.

The estimates come from the learning fortnight and the outcomes from three other 28-day seeds, so
seed-to-seed variation limits any correlation; the page arm's −0.04 is the comparison. The 36 cases
were selected because the twin estimated a gain under the page arm, which inflates that arm's
estimates and not the others'. Both limits are stated with the result.

## Step 2, only if an arm with the decay passes step 1: measuring the return from one record

Fit each subject's time constant from their own learning fortnight with no second run: on stretches
outside meals, regress the change in sensor glucose over 1, 2, 4, 8, 12 and 24 h on oref's summed
BGI over the same window, and fit the exponential return to the six coefficients as `DECAY.md` did.
The fit is compared with `DECAY.md`'s interventional responses for the same twelve subjects. The
criterion and the next test (the same-fortnight check, then the harm run) are written in a further
plan once step 1's result is known, since the loop's own response to glucose biases a regression on
observational data and the size of that bias is unknown.

Not in scope: changing the page, the choice rule, or the strengthening limit.
