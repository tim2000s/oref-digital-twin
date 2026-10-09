# Mis-set profiles through TimSim: results, 9 October 2026

Judged against `BAD_PROFILES_PLAN.md`, which was committed (ee6bc9d) before the run. Sections
marked "added after the results" were not in the plan.

Ninety-six round trips: twelve titrated TimSim adults, eight mis-set starting profiles each, a
14-day learning run, the twin's settings tests with their deployed goals (time in range above
70%, time below 70 under 2%), then 28 days on one seed with the mis-set profile and with the
twin's. None failed. Produced by `timsim_roundtrip.py`; the tables come from
`summarise_bad_profiles.py` and `compare_noise_floor.py`.

## Verdict against the plan

The plan named two things that would count against the twin: harm (a rise in time below
54 mg/dL of more than 0.2 points with the twin's profile) in a condition where the twin was
correcting a too-strong profile or in any subject given more insulin; and fewer subjects passing
with the twin's profile than with the mis-set one.

The second did not happen. The first did: 11 of 96 subject-months crossed the harm line, seven
of them in the too-strong conditions and five in subjects given more insulin. By the plan as
written the twin fails.

The next section, added after the results, shows that the 0.2-point line sits inside the
variation a meaningless change produces. One case stands outside it.

## Pass rule

Time in range above 80%, time below 70 under 1.5% and time below 54 under 0.4%, per subject on
the evaluation month. Subjects passing, of twelve:

| Starting profile | Mis-set: sensor | Mis-set: true glucose | Twin's: sensor | Twin's: true glucose |
|---|---|---|---|---|
| Titrated (reference, 9 October round trip) | 3 | 5 | 5 | 7 |
| ISF ×0.7 | 0 | 2 | 0 | 6 |
| ISF ×1.4 | 4 | 6 | 6 | 7 |
| Basal ×1.3 | 1 | 4 | 3 | 6 |
| Basal ×0.7 | 3 | 6 | 3 | 6 |
| Carb ratio ×0.7 | 2 | 2 | 3 | 2 |
| Carb ratio ×1.4 | 2 | 4 | 5 | 7 |
| All three too strong | 1 | 1 | 1 | 2 |
| All three too weak | 3 | 4 | 3 | 4 |

The count never fell on sensor glucose and rose in five of eight conditions. No condition got more
than half the subjects through: the rule is stricter than the twin's own goals, which it was not
told about.

## Harm

Time below 54 (sensor) was higher with the twin's profile in 33 of 96 subject-months, and higher
by more than 0.2 points in 11. Three of the eleven had profiles identical to the mis-set one
except for max IOB rounded up to the next 0.1 U (by 0.01 to 0.05 U), a defect in the twin since
fixed.

### Noise floor (added after the results)

TimSim is deterministic: two runs of one profile on one seed agreed to every decimal. But raising
one subject's max IOB from 7.77 to 7.80 U moved its time below 54 from 0.93% to 1.24% over the
month. Lows are rare, and a small difference in an early dose shifts the timing of everything
after it.

To measure that, every one of the 96 mis-set profiles was rerun with max IOB 0.03 U higher
(`null_perturbation.py`) and compared with its recorded month:

| Change in one subject-month | Max IOB +0.03 U | The twin's profile |
|---|---|---|
| Time below 54, sensor: 5th, 50th, 95th percentile | −0.27, 0.00, +0.57 | −0.95, −0.06, +0.41 |
| Time below 54, sensor: rises over 0.2 | 21 of 96 | 11 of 96 |
| Time below 54, sensor: rises beyond the +0.03 U arm's 95th percentile | | 1 of 96 |
| Time below 70, sensor: 5th, 50th, 95th percentile | −0.63, +0.01, +1.00 | −2.77, −0.48, +0.53 |
| Time in range, sensor: 5th, 50th, 95th percentile | −3.11, +0.02, +3.11 | −6.19, −0.59, +3.85 |

A change of 0.03 U crossed the planned harm line nearly twice as often as the twin's changes did.
A single simulated month cannot detect harm of that size in one subject, so the planned
threshold measured noise. Repeating each month on several seeds would be needed for a
per-subject harm rule at this size.

### The case outside the noise

Subject 7 under carb ratio ×0.7. The twin left basal, carb ratio and target alone and
strengthened ISF by 20%. Over the evaluation month, time below 70 went from 0.41% to 1.86%,
below 54 from 0.01% to 0.81% (+0.79, beyond the null 95th percentile of +0.57), and rescue events
from 11 to 29, while time in range rose by 0.9 points.

The carb ratio was not what the twin acted on. Rerunning that learning fortnight (deterministic)
and printing the twin's tables showed the too-strong ratio caused no visible problem: meal
stretches ran 81.9% in range with 0.1% below, and the fortnight as a whole 84.5% and 0.1%.

The ISF stage judged on correction stretches, the readings within 3 hours of one above
180 mg/dL. They are selected for being high, and here they ran 49.3% in range over 37.5 hours.
The 70% goal cannot often be met on a slice chosen that way, so ISF −20% (78.4% on that slice)
was taken as the smallest change meeting both goals. Any subject with 6 hours or more of
correction stretches is pushed towards stronger ISF by this. The twin's own estimate for the
whole fortnight was a rise in time below 70 from 0.1% to 0.4%; the realised rise in the
evaluation month was 1.45 points, to 1.86%, with time below 54 at 0.81%.

An earlier version of this section, written before the tables were reproduced, put the change
down to the rule used when no value meets both goals. That was wrong.

## Direction of the twin's changes

Subjects given more insulin by any setting: 36 of 96 (subject-months, with the max IOB rounding
excluded).

Whether each mis-set setting moved back towards its titrated value, of twelve subjects:

| Mis-set | Towards titrated | Away | Unchanged |
|---|---|---|---|
| ISF ×0.7 | 7 | 2 | 3 |
| ISF ×1.4 | 2 | 7 | 3 |
| Basal ×1.3 | 8 | 0 | 4 |
| Basal ×0.7 | 0 | 5 | 7 |
| Carb ratio ×0.7 | 0 | 2 | 10 |
| Carb ratio ×1.4 | 3 | 1 | 8 |

The twin corrected too-strong ISF and basal in most subjects and almost never corrected
too-weak ones, which it often weakened further. With its goals at 70% and 2%, a weak profile
whose time in range is already above 70% gives it no reason to add insulin, and lows from any
other cause push it towards less.

## The twin's estimates

Median estimated change in time below 70 against the realised change, by condition: ISF ×0.7
−2.35 against −0.98; basal ×1.3 −1.90 against −0.87; carb ratio ×1.4 −1.90 against −0.60; all
three too strong −3.30 against −2.10. The benefit on lows was overstated two- to four-fold, as in
the titrated round trip. In the one case of clear harm it was understated about fivefold.

## What follows

Within TimSim the twin's changes cut lows more than they raised them and never reduced the
number of subjects meeting the pass rule, but it did not meet the plan's harm criterion and the
one clear harm came from its selection rule. Two changes to the twin follow directly, neither yet
made:

- The ISF stage should judge on the whole period, using correction stretches only to decide
  whether there is enough to judge; a time-in-range goal applied to readings selected for being
  high pushes ISF stronger whatever the person's settings.
- A time-below-54 limit on any change towards more insulin, which the twin does not have.

And two to the test: each evaluation month repeated on several seeds, so a per-subject harm rule
can be set above the noise; and the pass rule given to the twin as its goals, as a second arm.

## Defects found during the run

- The twin's max IOB stage rounded the current value to 0.1 U, so "no change" moved max IOB by up
  to 0.05 U. Fixed: the current value is now one of the values tried, exactly.
- `summarise_bad_profiles.py` at first classed that rounding as more insulin, which put the count
  of subjects given more insulin at 64 instead of 36. Fixed before any figure here was written.
