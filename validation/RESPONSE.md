# Does the twin's estimate of a stronger setting track TimSim once glucose is allowed to return? Results

Step 1 of `RESPONSE_PLAN.md`, run on 9 November 2026 by `response_check.py` (914 s, seven workers).
Results in `results/response_check_2026-11-09.json` and the log beside it. For the 36
subject-conditions where the weak-fix run and the comparison run chose differently, both choices
were estimated on the regenerated learning fortnight under three simulator arms and the difference
set against the difference TimSim produced on evaluation. The page arm reproduced all 72 stored
estimates exactly.

No arm meets the plan's criteria, so step 2 was not run.

| Arm | Time in range: estimated, realised | Spearman [95% interval] | Below 70: estimated, realised | Below 54: estimated, realised | Insulin, U/day: estimated, realised | Mean glucose, mg/dL: estimated, realised |
|---|---|---|---|---|---|---|
| Page | +3.75, +0.95 | −0.02 [−0.35, 0.33] | +0.65, +0.70 | +0.08, +0.20 | +1.19, +3.20 | −10.3, −5.0 |
| Decay | +2.95, +0.95 | 0.17 [−0.17, 0.49] | +0.10, +0.70 | +0.02, +0.20 | +3.69, +3.20 | −6.4, −5.0 |
| Decay, no rescue | +2.40, +0.95 | 0.12 [−0.21, 0.45] | +0.90, +0.70 | +0.23, +0.20 | +3.54, +3.20 | −7.1, −5.0 |

Medians over cases. The criterion was a median estimated gain in time in range of at most +1.43
points and a Spearman interval above zero; both decay arms miss both.

The decay did what `DECAY.md` predicted for insulin and mean glucose. With glucose allowed to
return, the loop in the twin gives about as much extra insulin as it did in TimSim (+3.69 against
+3.20 U/day) and mean glucose falls by about the right amount. Without the rescue rule the sizes of
the change in time below 70 and below 54 are also close. The estimated gain in time in range stays
two and a half to three times the realised one.

For the same fall in mean glucose the twin converts more into time in range than TimSim does: about
0.46 points per mg/dL under the decay arm against 0.19 realised. The twin moves the recorded trace;
in TimSim the stronger setting also changed its shape, with more time low for the same mean. This
is an observation from medians, not a tested mechanism.

Per case nothing tracked well. Mean glucose agreed in sign in all 36 under every arm (Spearman 0.32
to 0.41), and no other measure had a Spearman interval above zero except time below 54 without the
rescue, which was negative (−0.41 [−0.68, −0.04]). Two limits apply, as the plan stated: the
estimates come from the learning fortnight and the outcomes from three other seeds, and the 36
were selected for a large estimated gain under the page arm.
