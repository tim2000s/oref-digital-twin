# One step towards more insulin per review, over three reviews: plan, fixed before the run

Written 9 November 2026, before the rule was built or run. Results go in `STEP.md`.

## Why

`WEAK_PROFILES.md` found that the twin leaves a too-weak ISF or basal alone because the smallest
change meeting the aim is no change. `WEAK_FIX.md` let those stages take the value with most
estimated time in range instead, and it failed: the twin overstates the gain in time in range from
more insulin by about three times, with or without the decay of `DECAY.md` (`RESPONSE.md`), so the
rule walked to the strongest value on the grid. The estimate cannot be trusted for the size of a
gain. This rule trusts it for one step at a time, and only where it predicts no more lows, and
relies on the next review, on new data, to say whether to step again. That is how a setting is
titrated by hand.

## Change

For the basal and ISF stages only: when the smallest change meeting the aim is no change, take the
value one step towards more insulin (basal ×1.1, ISF ×0.9) if all of these hold, and otherwise
keep no change:

- it meets the aim on the stage's stretches and is not excluded by the strengthening limit;
- its estimated time in range on the stage's stretches is at least 2 points above no change's (the
  margin `WEAK_FIX_PLAN.md` fixed);
- its estimated whole-period time below 70 and below 54 are no higher than no change's.

Everything else in `choose`, the other stages and the strengthening limit are unchanged.

## Test

Two arms, each the fourth mis-set run's design (`BAD_PROFILES_PLAN_4.md`: twelve subjects, eight
mis-set conditions, tighter aim, 10 g rule, evaluation on seeds 101 to 103 for 28 days each, the
mis-set and null arms reused from `results/bad_profiles_2026-10-09b.json`), with three reviews in
place of one. Review 1 learns on seed 202 with the mis-set profile; each review applies its choices
and the next learns on the next seed (203, then 204) with the result; the profile after review 3 is
evaluated. The SMB limit a review chooses is used by the next review's TimSim run and given to its
twin.

- Arm A: the current rule (main as it stands).
- Arm B: the current rule with the change above.

Arm A is the comparison, since a person using the page would run it again each fortnight;
`results/bad_profiles_2026-11-08-fix.json` (one review, current rule) is reported beside both.

## Judgement

The change ships when both hold:

- No harm criterion of `BAD_PROFILES_PLAN_4.md` is met by arm B, against the same null arm (95th
  percentile +0.349 points in pooled time below 54, maximum +0.413): ten or more of 96 exceedances;
  any rise above the null maximum; exceedances among subjects given more insulin at a binomial
  probability under 0.05; fewer passing the pass rule than with the mis-set profile in any condition.
- Of the 48 subject-conditions with too little insulin, more meet the tighter aim (above 80% in
  range, below 70 under 2%, pooled sensor) in arm B than in arm A.

Either failing, the rule is not adopted. Arm A's harm criteria are reported too: three reviews of
the current page have not been tested, and a failure there is a finding about the page as it is.
Also reported: the same counts for the 48 with too much insulin and all 96; medians per condition;
how often ISF and basal moved towards titrated in the weak conditions; each review's choices.

Expected direction, stated before the run: in the weak conditions arm B moves ISF and basal up to
three steps towards titrated and gains time in range over arm A, with somewhat more time below 70.
Little difference where the profile already gives too much insulin, since no change rarely meets
the aim there.
