# Mis-set profiles through TimSim, second run: results

Judged against `BAD_PROFILES_PLAN_2.md`, committed (0bbb7cc) before the run. The twin was at
86d1a07: ISF judged on the whole period, and a change towards more insulin only considered when
the whole period's estimate keeps time below 70 under 2% and below 54 under 0.6%.

Ninety-six round trips, none failed: twelve titrated TimSim adults, eight mis-set starting
profiles, a 14-day learning run, then three arms (mis-set, twin's, and a null arm with max IOB
0.03 U higher) on seeds 101 to 103, 28 days each, pooled to 84 days per subject. The run took
42,721 s on seven workers. Tables from `summarise_bad_profiles_2.py`.

## Verdict against the plan

None of the four criteria was met, so on this test the twin is not found to cause harm.

| Criterion (any one counts against the twin) | Result |
|---|---|
| 1. Ten or more of 96 rises in time below 54 beyond the null arm's 95th percentile (+0.349 points) | 0 |
| 2. Any rise larger than the null arm's largest (+0.413) | 0; the twin's largest was +0.343 |
| 3. Exceedances among subjects given more insulin at a binomial probability under 0.05 | 0 of 14 |
| 4. Fewer subjects passing the pass rule with the twin's profile in any condition | none |

Change in pooled time below 54 (sensor), 5th, 50th and 95th percentile across the 96: null arm
−0.215, +0.004, +0.349; twin −0.814, −0.035, +0.044.

## Pass rule

Time in range above 80%, below 70 under 1.5%, below 54 under 0.4%, per subject on the pooled 84
days. Subjects passing of twelve:

| Starting profile | Sensor: mis-set → twin | True glucose: mis-set → twin | First run, sensor |
|---|---|---|---|
| ISF ×0.7 | 0 → 0 | 2 → 3 | 0 → 0 |
| ISF ×1.4 | 4 → 5 | 7 → 8 | 4 → 6 |
| Basal ×1.3 | 1 → 1 | 3 → 7 | 1 → 3 |
| Basal ×0.7 | 3 → 4 | 5 → 8 | 3 → 3 |
| Carb ratio ×0.7 | 2 → 3 | 4 → 5 | 2 → 3 |
| Carb ratio ×1.4 | 3 → 3 | 5 → 6 | 2 → 5 |
| All three too strong | 0 → 0 | 1 → 3 | 1 → 1 |
| All three too weak | 2 → 2 | 4 → 3 | 3 → 3 |

On sensor glucose 15 subject-conditions passed with the mis-set profiles and 18 with the twin's.
On true glucose, 31 and 43. The first run's figures are on one 28-day month and are not directly
comparable.

## What the twin did

The changes made the twin more conservative. It gave more insulin in 14 of 96 cases against 36 in
the first run, and six of the 14 were in the all-too-weak condition.

| Mis-set | Moved towards titrated | Away | Unchanged |
|---|---|---|---|
| ISF ×0.7 | 4 | 0 | 8 |
| ISF ×1.4 | 0 | 2 | 10 |
| Basal ×1.3 | 8 | 0 | 4 |
| Basal ×0.7 | 0 | 5 | 7 |
| Carb ratio ×0.7 | 0 | 1 | 11 |
| Carb ratio ×1.4 | 1 | 0 | 11 |
| All too strong: ISF, basal, carb ratio | 8, 8, 5 | 0, 0, 0 | 4, 4, 7 |
| All too weak: ISF, basal, carb ratio | 0, 0, 6 | 0, 2, 0 | 12, 10, 6 |

In the too-strong conditions lows fell: in all three too strong, median time below 70 from 5.16%
to 3.03% and below 54 from 1.52% to 0.91%, with time in range unchanged (84.9% to 85.0%).

In the too-weak conditions the twin mostly returned the settings unchanged. "Too weak" describes
how the settings were made, not their outcome, and most of those subjects already met the twin's
goals over the learning fortnight (ISF ×1.4: 9 of 12; basal ×0.7: 8; carb ratio ×1.4: 5; all three:
11), so leaving them alone is what the goals ask for. Where single-setting weak profiles failed the
pass rule it was mostly on lows (carb ratio ×1.4: 9 of 12 at 1.5% or more below 70), where more
insulin would be wrong. Only the all-too-weak condition was weak in outcome: median time in range
76.7%, 9 of 12 at or below 80%, with few lows, which meets the twin's 70% goal and falls short only
of the pass rule's 80%.

The twin's estimate of the fall in time below 70 was again larger than what happened, by 1.5 to
3.3 times where there was a fall (for example −2.85 estimated against −1.84 realised in all three
too strong).

## What this does and does not show

- It shows that on these twelve simulated people, with harm measured against the noise a
  meaningless change produces over 84 days, the twin's changes did not raise time below 54
  beyond that noise in any case, and lowered it in most of the too-strong conditions.
- It does not show the twin reaches the pass rule. Few subjects meet it either way. Most of the
  shortfall is lows the loop's settings did not cause; the rest is the all-too-weak condition
  sitting between 70% and 80% in range, which the twin's 70% goal does not ask it to correct.
- The safety of strengthening rests on 14 cases. That is too few to say much about the rule that
  now governs them; a test built to make the twin strengthen more often would be needed.
- The plan asked how many values the strengthening limit excluded. The run kept each subject's
  choices but not the full report where exclusions are marked, so that figure is not available.
  This is a deviation from the plan.
- TimSim's people are S2008 subjects, more alike than a real cohort, run under stock oref0.
