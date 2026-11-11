# Strengthen slowly, weaken as now: results

Run on 11 November 2026 to `PACE_PLAN.md`, as amended, on branch `pace`. Arm P is the round trip
with `--guard --pace`; S2008 ran from 14:33 to 19:09 and Hovorka from 19:09 to 21:07, with no
failed row. Every figure comes from `summarise_pace.py` (`results/pace_2026-11-11.json`). Medians
are over subject-conditions, evaluation sensor pooled over three seeds, with bootstrap 95%
intervals over subjects, in points of percentage time.

Arm P does not go forward. It meets all three tests on Hovorka and two on S2008, where it fails one
part of the harm test: in cr_weak 2 of 12 subjects met the pass rule after the reviews against 3 at
the mis-set start. Every other part of the harm test, and both tests on lows, were met on both
bodies.

## The tests

| Test | S2008 | Hovorka |
|---|---|---|
| 1. No harm criterion met | No: fewer passing in cr_weak (3 to 2) | Yes |
| 2. Lows fall with too much insulin (48 cases, change in time below 54 from start) | Yes: −0.67 (−0.91 to −0.28) | Yes: −0.74 (−1.21 to −0.65) |
| 3. No more lows than the page (P − A, time below 54, upper end under +0.05) | Yes: −0.06 (−0.17 to 0.00) | Yes: −0.34 (−0.58 to −0.24) |

## Harm counts beside the earlier arms

Against each body's null arm (S2008: 95th centile +0.349, maximum +0.413; Hovorka: +0.456 and
+0.823). The guard's counts are reported, not re-judged, as the plan says.

| Body | Arm | Exceedances of 96 | Above the null maximum | Given more insulin | Exceedances among them | Fewer passing in |
|---|---|---|---|---|---|---|
| S2008 | A (page) | 9 | 6 | 83 | 9 (P = 0.023) | cr_weak |
| S2008 | C (guard) | 5 | 2 | 79 | 5 (P = 0.36) | none |
| S2008 | P (guard and pace) | 1 | 0 | 64 | 1 (P = 0.96) | cr_weak |
| Hovorka | A | 24 | 12 | 91 | 24 (P < 0.001) | none |
| Hovorka | C | 7 | 2 | 91 | 7 (P = 0.17) | none |
| Hovorka | P | 0 | 0 | 71 | 0 (P = 1.0) | none |

No row of arm P ended with basal, ISF or carb ratio more than 20% towards more insulin, against 59
of 96 (S2008) and 51 (Hovorka) under the page. The single S2008 failure is a count of one subject
in a condition of twelve; that part of the harm test was set before any of these runs and is applied
as written.

## Paired against the page and the guard

| Body | Comparison | Below 54 | Below 70 | In range |
|---|---|---|---|---|
| S2008 | P − A | −0.06 (−0.17 to 0.00) | −0.30 (−0.61 to 0.00) | −0.58 (−1.01 to 0.00) |
| S2008 | P − C | −0.00 (−0.08 to 0.00) | −0.05 (−0.45 to 0.00) | 0.00 (−0.54 to 0.00) |
| Hovorka | P − A | −0.34 (−0.58 to −0.24) | −0.91 (−1.54 to −0.53) | −4.44 (−7.38 to −2.68) |
| Hovorka | P − C | −0.18 (−0.36 to −0.09) | −0.50 (−0.78 to −0.24) | −3.24 (−4.67 to −1.08) |

## Was the loss of time in range paid for?

Per the amendment, a loss is justified when the intervals for P − A in time in range and in time
below 70 both lie below zero, and unjustified when time in range falls and time below 70 does not.

| Condition | S2008 in range | S2008 below 70 | S2008 verdict | Hovorka in range | Hovorka below 70 | Hovorka verdict |
|---|---|---|---|---|---|---|
| All 96 | −0.58 (−1.01 to 0.00) | −0.30 (−0.61 to 0.00) | no loss | −4.44 (−7.38 to −2.68) | −0.91 (−1.54 to −0.53) | justified |
| isf_strong | 0.00 (−0.77 to +1.47) | −0.18 (−0.58 to +0.17) | no loss | −3.42 (−5.84 to −1.14) | −0.61 (−1.39 to −0.24) | justified |
| isf_weak | −1.15 (−2.44 to +0.53) | −0.34 (−0.69 to +0.13) | no loss | −6.12 (−10.22 to −2.36) | −0.76 (−2.05 to −0.45) | justified |
| basal_high | 0.00 (−0.40 to +0.95) | −0.07 (−0.83 to +0.21) | no loss | −1.72 (−6.27 to −0.10) | −0.96 (−1.70 to −0.26) | justified |
| basal_low | −1.47 (−2.53 to +0.16) | −0.36 (−1.05 to −0.05) | no loss | −4.89 (−9.28 to −3.95) | −1.94 (−2.91 to −0.46) | justified |
| cr_strong | −0.50 (−3.10 to 0.00) | −0.31 (−0.83 to 0.00) | no loss | −7.01 (−10.45 to −1.20) | −1.02 (−2.98 to −0.42) | justified |
| cr_weak | −0.86 (−3.40 to −0.23) | −0.53 (−0.97 to −0.09) | justified | −2.89 (−9.57 to −0.77) | −0.77 (−1.83 to −0.41) | justified |
| all_strong | 0.00 (−0.60 to +0.24) | 0.00 (−0.61 to 0.00) | no loss | 0.00 (−5.97 to +1.35) | −0.80 (−1.51 to 0.00) | no loss |
| all_weak | −3.35 (−4.88 to −2.57) | −0.31 (−1.05 to −0.03) | justified | −12.85 (−16.99 to −3.59) | −1.38 (−3.57 to −0.53) | justified |

No condition on either body showed an unjustified loss. The verdict is a sign test on two
intervals and says nothing of the exchange rate: on Hovorka in all_weak, 12.8 points of range went
with 1.4 points below 70.

## Where the range went

Median time in range under each arm against the mis-set start.

| Condition | S2008 start | S2008 A | S2008 C | S2008 P | Hovorka start | Hovorka A | Hovorka C | Hovorka P |
|---|---|---|---|---|---|---|---|---|
| isf_strong | 84.3 | 82.5 | 81.9 | 81.9 | 75.5 | 73.9 | 73.9 | 69.6 |
| isf_weak | 81.6 | 80.2 | 81.4 | 80.0 | 68.7 | 70.8 | 68.0 | 64.9 |
| basal_high | 86.0 | 81.4 | 81.9 | 82.3 | 77.0 | 72.9 | 71.2 | 70.5 |
| basal_low | 80.3 | 81.2 | 80.3 | 80.3 | 66.9 | 73.9 | 70.3 | 64.3 |
| cr_strong | 83.2 | 83.6 | 83.2 | 81.7 | 73.6 | 73.5 | 69.2 | 65.3 |
| cr_weak | 81.8 | 81.9 | 82.5 | 80.3 | 72.7 | 70.8 | 65.5 | 64.3 |
| all_strong | 84.9 | 82.2 | 81.6 | 82.1 | 77.1 | 73.0 | 74.6 | 66.8 |
| all_weak | 76.1 | 80.1 | 78.7 | 76.3 | 59.6 | 72.0 | 66.3 | 58.5 |

On Hovorka arm P ended below the mis-set start in all eight conditions, including the four with
too little insulin. Of the 48 subject-conditions with too little insulin, the number ending with
any of basal, ISF or carb ratio weaker than the mis-set value was 32 under P on S2008 (A 26, C 30)
and 40 on Hovorka (A 39, C 35). The weak cases meeting the tighter aim were 20 under P on S2008
(start 18, A 20, C 22) and none under any arm on Hovorka.

Settings strengthened by each review of arm P (a row can count under more than one):

| Body | Review | Basal | ISF | Carb ratio | Target | None |
|---|---|---|---|---|---|---|
| S2008 | 1 | 3 | 8 | 25 | 0 | 60 |
| S2008 | 2 | 1 | 26 | 21 | 1 | 47 |
| S2008 | 3 | 1 | 21 | 13 | 5 | 56 |
| Hovorka | 1 | 1 | 35 | 17 | 3 | 40 |
| Hovorka | 2 | 5 | 36 | 17 | 4 | 34 |
| Hovorka | 3 | 2 | 46 | 11 | 9 | 28 |

Expected, stated in the plan: fewer rises above the null maximum than A and about as many as C (P
had fewer than both); criteria 2 and 3 met on both bodies (they were); range in the
too-little-insulin conditions at or below C's (it was, in seven of eight); no row past 20% towards
more insulin (none was).

## What follows

On lows pace did what it was built for: no case on either body rose above the null maximum, and
time below 54 was lower than under the page on both bodies and lower than under the guard on
Hovorka. It fails the plan by one subject in one
condition on S2008. The cost is time in range, small on S2008 and 3 to 13 points on Hovorka, and on
Hovorka it falls below the mis-set start even where the profile gives too little insulin. Weakening
was left at three steps a review, and in most of the too-little-insulin cases some setting ended
weaker than it started, so the fast side of the rule is acting where the profile is already weak.
Whether that is the right exchange is a choice about the aim, which these runs measure and do not
make.
