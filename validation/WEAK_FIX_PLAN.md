# Strengthening a too-weak ISF or basal when it gains time in range: plan, fixed before the run

Written 8 November 2026, before the change was built or run. Results go in `WEAK_FIX.md`.

## Change

`WEAK_PROFILES.md` found that `choose` takes the smallest change meeting the aim, so where the loop
has made up a too-weak ISF or basal the answer is no change, even when a stronger value is
estimated to give more time in range. For the basal and ISF stages only, the rule becomes: among
the values that meet the aim and pass the strengthening limit, take the one with the most time in
range on the stage's stretches when it beats the smallest such change by at least 2 points;
otherwise the smallest change, as now. Ties go to the smaller change. The other stages, the
strengthening limit (estimated whole-period time below 70 under 2% and below 54 under 0.6% for any
value giving more insulin) and both fallbacks are unchanged.

The 2-point margin is a modelling choice: large enough that a stage does not move for differences
inside the estimate's noise, small against the gains the diagnostic found.

Not in scope: where the limit removes every stronger value and the fallback takes the fewest lows
(adult#011's basal). Changing that means loosening the limit, which the repository's rules do not
allow.

## Test

The fourth mis-set run's design (`BAD_PROFILES_PLAN_4.md`) on the changed twin: twelve subjects,
eight mis-set conditions, learning fortnight on seed 202, evaluation on seeds 101 to 103 for 28 days
each, the tighter aim, the 10 g rule, the mis-set and null arms reused from
`results/bad_profiles_2026-10-09b.json`. The comparison is the settings-fix run
(`results/bad_profiles_2026-11-08-fix.json`, the twin at 48e1f3b), which differs only in the rule.

## Judgement

The change ships when both hold:

- No harm criterion of `BAD_PROFILES_PLAN_4.md` is met, against the same null arm (95th percentile
  +0.349 points in pooled time below 54, maximum +0.413): ten or more of 96 exceedances; any rise
  above the null maximum; exceedances among subjects given more insulin at a binomial probability
  under 0.05; fewer passing the pass rule than with the mis-set profile in any condition.
- Of the 48 subject-conditions with too little insulin (ISF too weak, basal too low, carb ratio too
  weak, all too weak), more meet the tighter aim (above 80% in range, below 70 under 2%, pooled
  sensor) than in the comparison run.

Either failing, the rule is reverted. Reported beside the judgement: the same count for the 48
with too much insulin and for all 96; median time in range and time below 70 and 54 per condition;
how often ISF and basal moved towards their titrated values in the weak conditions, against the
comparison run; how often the twin gave more insulin.

Expected direction, stated before the run: more insulin in the weak conditions, more time in range
there and somewhat more time below 70. Little change where the profile already gives too much
insulin, since the strengthening limit binds more often there.
