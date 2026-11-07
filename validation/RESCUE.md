# Rescue eating in the twin's simulator: TimSim results, 6 November 2026

The option described here was removed on 7 November 2026, since it was not adopted and the page
never used it. It is in commit ed51121, which reproduces the results below.

The settings tests keep the person's real food and treatments. A low in the real record was usually
treated, so a change that removes the low still carries the rescue's rise, and a change that adds a
low leaves it untreated. This note records an optional rescue model and its test against TimSim.
The plan was fixed before anything was computed; it, the fitting script and the real-data check are
kept in a private analysis repository.

## The model

`replay/oracle/request.js` accepts `rescue` in a simulate call: `{threshold, refractory_min, delay,
rise, rise_min}`. One rule (a rescue at a cycle below `threshold`, no sooner than `refractory_min`
after the last) is applied to the real glucose and to the shifted glucose. The shifted trace gains
its own rescues and loses the real trace's. Each rescue adds nothing for `delay` minutes, then
`rise` mg/dL spread over `rise_min` minutes. With `decay_tau_min` also set, the rise relaxes with
the same time constant. Where the two sets of rescue times agree the terms cancel exactly, so a
change that alters nothing still gives the baseline. It is off unless given, and the page does not
give it. Tested in `replay/tests/test_oracle_integration.py`.

The parameters came from 38 AndroidAPS users in the OpenAPS Data Commons with at least ten lows
each: nadir 10 minutes after crossing 70 mg/dL, then a rise of 68.8 mg/dL [66.0, 80.0] over
91 minutes. The threshold (70 mg/dL) and spacing (60 minutes) were set, not fitted. No TimSim data
entered the fit.

## Same-fortnight check

`same_week.py --rescue '<json>' [--decay-tau-min 144] --truth-from results/same_week_2026-10-10.json`,
all 12 subjects reproducing the stored estimates without options exactly. Results in
`results/same_week_rescue_2026-11-06.json` and `results/same_week_rescue_decay144_2026-11-06.json`.

| Arm | Below 70: slope | Below 70: Spearman | In range: slope | Below 54: Spearman |
|---|---|---|---|---|
| Neither | 0.348 [0.298, 0.403] | 0.863 [0.815, 0.912] | 0.534 [0.423, 0.674] | 0.608 [0.476, 0.778] |
| Decay 144 min | 0.971 [0.843, 1.168] | 0.858 [0.806, 0.912] | 1.164 [0.929, 1.514] | 0.604 [0.453, 0.798] |
| Rescue | 1.131 [0.969, 1.340] | 0.792 [0.744, 0.852] | 0.522 [0.420, 0.619] | 0.400 [0.124, 0.626] |
| Rescue and decay | 2.106 [1.729, 2.701] | 0.636 [0.375, 0.820] | 0.985 [0.766, 1.143] | 0.269 [−0.054, 0.567] |

The rescue model brought the size of the estimate for lows right out of sample, but its ranking of
changes by their effect on lows fell below the interval it had without options, which the plan set
as a condition. Together with the decay it overcorrects, which fits the separate finding that
TimSim's pull-back is physiological rather than rescue eating. Neither arm was adopted, and the
published page is unchanged.

## A 10 g, 15-minute rule, 7 November 2026

Added and tested on 7 November: a person below 70 mg/dL eats 10 g, again every 15 minutes while
still low, each rising by 10 × ISF ÷ carb ratio after 10 minutes and over 30. Every number is
taught practice, not fitted. Applied to both traces (as above) or to new lows only:

| Arm | Below 70: slope | Below 70: Spearman | In range: slope | Below 54: Spearman |
|---|---|---|---|---|
| Both | 1.161 [0.954, 1.406] | 0.842 [0.803, 0.892] | 0.492 [0.382, 0.587] | 0.228 [0.047, 0.437] |
| New lows only | 0.874 [0.745, 1.078] | 0.819 [0.763, 0.879] | 0.482 [0.357, 0.589] | 0.583 [0.430, 0.718] |
| Both, with decay | 2.498 [2.109, 3.073] | 0.794 [0.741, 0.851] | 0.936 [0.688, 1.104] | 0.159 [−0.132, 0.419] |
| New lows only, with decay | 1.878 [1.587, 2.244] | 0.711 [0.601, 0.825] | 0.960 [0.675, 1.137] | 0.475 [0.192, 0.665] |

Without the decay both versions passed the criterion set beforehand (slope interval includes 1,
Spearman at least 0.815), out of sample. Neither improved on the decay alone for time below 54, and
both left time in range overstated about twofold where the decay does not, so the rule was removed
again. Results in `results/same_week_rescue10g_*_2026-11-07.json`.
