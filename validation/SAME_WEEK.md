# Same-fortnight accuracy of the twin's estimates in TimSim: results

Judged against `SAME_WEEK_PLAN.md`, committed (d413856) before the run. Twelve titrated TimSim
adults, ten changes each, 120 comparisons. Each compares the twin's estimate for the learning
fortnight under a change with TimSim replaying that same fortnight (same seed, meals, sensor noise
and physiology) under the change. Replaying with nothing changed reproduced the learning run
exactly for all twelve subjects. The run took 3,510 s; tables from `summarise_same_week.py`.

## Verdict against the plan

Pooled over the 120, with 95% intervals from bootstrapping subjects:

| Measure | Spearman correlation | Same-fortnight change per point of estimated change | Informative? | Calibrated? |
|---|---|---|---|---|
| Time below 70 | +0.863 [+0.815, +0.912] | 0.348 [0.298, 0.403] | yes | no |
| Time in range | +0.532 [+0.340, +0.720] | 0.534 [0.423, 0.674] | yes | no |
| Time below 54 | +0.608 [+0.476, +0.778] | 0.264 [0.202, 0.323] | yes | no |

On every measure the estimates are informative: the correlation's interval excludes zero. They are
not calibrated: the slope's interval excludes 1 on every measure. For lows the estimates rank
changes well and are about three times too large. A twin estimate of +3 points of time below 70
corresponds to about +1 point on the same fortnight.

Where the same-fortnight change was large (0.5 points below 70, or 2 points in range), the
estimate had the right sign in 74 of 79 changes for time below 70, and in 46 of 69 for time in
range.

## By change

Median over the twelve subjects, points:

| Change | Below 70: estimated | Below 70: same fortnight | In range: estimated | In range: same fortnight |
|---|---|---|---|---|
| Basal ×0.7 | −1.05 | −0.41 | −3.93 | −2.96 |
| Basal ×1.3 | +2.58 | +0.81 | 0.00 | +2.11 |
| ISF ×0.7 (stronger) | +4.43 | +1.40 | −0.51 | +0.10 |
| ISF ×1.3 (weaker) | −1.36 | −0.93 | −2.84 | −0.79 |
| Carb ratio ×0.7 (stronger) | +0.37 | +0.15 | +0.06 | +0.87 |
| Carb ratio ×1.3 (weaker) | −0.12 | +0.02 | −0.56 | −1.48 |
| Target −1 mmol/L | +5.85 | +1.40 | −0.86 | +0.91 |
| Target +1 mmol/L | −1.70 | −0.68 | −6.46 | −3.19 |
| All three stronger | +9.14 | +2.28 | −3.53 | +2.21 |
| All three weaker | −1.93 | −1.43 | −11.66 | −4.84 |

The pattern is consistent. Changes that add insulin raise lows by about a third to a quarter of
what the twin estimates, so the twin also expects them to cost time in range when on the same
fortnight they gained it (basal ×1.3, all three stronger, target −1 mmol/L). Changes that remove
insulin are estimated closer to their size, but their cost in time in range is overstated. The
carb-ratio changes moved little either way, because TimSim's oref0 controller doses meals by SMB
rather than a wizard bolus.

## What this means

For the question the page's figures answer (this period, these settings, nothing else different)
the twin is a good guide to direction and to which change does more to lows. It is poor on size:
it puts three times too many lows on changes that add insulin, and so understates what they do
for time in range. Its selection rule leans on the size, so it is more cautious about adding
insulin than the same-fortnight replay would justify. That fits the earlier finding that it
rarely strengthened settings.

This also squares the TimSim runs with the real-data backtest. In TimSim the estimate's ranking
holds, while on real people the following week did not resemble the estimate. That is consistent
with the following week differing from the one the twin saw, and the backtest could not tell the
two apart.

## Not in the plan, and not done

A correction for the size, for example scaling the estimated shift by about a third, would follow
from the slope but has to be tested on subjects it was not fitted to before it goes near the page.
These results are for TimSim's people under stock oref0 only.
