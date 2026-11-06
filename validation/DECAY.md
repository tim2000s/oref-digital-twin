# A decaying glucose shift in the twin's simulator: TimSim results, 6 November 2026

The settings tests move glucose by each unit of extra or withheld insulin times the profile ISF
times the fraction of its action completed, and keep that shift for the rest of the period
(DESIGN.md §2.1). In TimSim the twin's estimate of the change in time below 70 was about three
times the change TimSim produced (slope 0.348, `SAME_WEEK.md`). This note records where that came
from and an optional correction. The plan was fixed before each step was computed; the plans,
scripts and the matching real-data check are kept in a private analysis repository.

## Response by horizon

The twelve titrated TimSim adults, the 14-day learning fortnight on seed 202, each run with basal at
80%, 100% and 120% on the same seed. For windows of 1 to 24 hours, the difference between runs in
the change of sensor glucose against the difference in oref's summed BGI (activity × ISF), per
subject by least squares; median over subjects with a bootstrap 95% interval:

| Horizon | 1 h | 2 h | 4 h | 8 h | 12 h | 24 h |
|---|---|---|---|---|---|---|
| Response | 0.96 [0.73, 1.09] | 0.90 [0.71, 1.06] | 0.62 [0.49, 0.78] | 0.31 [0.22, 0.42] | 0.23 [0.15, 0.31] | 0.12 [0.07, 0.19] |

Glucose follows an insulin difference as the twin's rule says for an hour or two and then returns.
An exponential pull-back with a time constant of 2.40 hours fits the six medians (squared error
0.0095). The twin's permanent shift is the source of most of the overstatement.

## The correction

`replay/oracle/request.js` accepts `decay_tau_min` in a simulate call: each dose's glucose effect
becomes its absorption convolved with an exponential relaxation of that time constant. It is off
unless given, and the page does not give it, so the published page is unchanged. Tested in
`replay/tests/test_oracle_integration.py`.

## Same-fortnight check with the correction

`same_week.py --decay-tau-min 144 --truth-from results/same_week_2026-10-10.json` re-estimated the
120 changes with a 144-minute decay and reused the stored TimSim truth. That is valid only if
nothing upstream moved, and the run checked it: for all 12 subjects the estimates without decay
reproduced the stored ones exactly. Results in `results/same_week_decay144_2026-11-06.json`.

| Measure | Slope without decay | Slope with decay | Spearman without | Spearman with |
|---|---|---|---|---|
| Time below 70 | 0.348 [0.298, 0.403] | 0.971 [0.843, 1.168] | 0.863 [0.815, 0.912] | 0.858 [0.806, 0.912] |
| Time in range | 0.534 [0.423, 0.674] | 1.164 [0.929, 1.514] | 0.532 [0.340, 0.720] | 0.590 [0.385, 0.769] |
| Time below 54 | 0.264 [0.202, 0.323] | 0.781 [0.629, 1.009] | 0.608 [0.476, 0.778] | 0.604 [0.453, 0.798] |

With the decay the size of the estimate for lows matches TimSim (slope interval includes 1) and the
ranking is unchanged. Where the same-fortnight change in time in range was large, the sign agreed
in 55 of 69 against 46 of 69.

The time constant was fitted on the same subjects and fortnight, so this confirms the mechanism
rather than validating the correction out of sample. On twelve real AndroidAPS setting changes it
left the correlation between estimated and realised change about where it was (time below 70
+0.11 to +0.02, time in range +0.66 to +0.63) and halved the largest estimates; twelve events can
show only that it does no visible harm there.
