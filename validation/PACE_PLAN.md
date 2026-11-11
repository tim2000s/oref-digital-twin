# Strengthen slowly, weaken as now: plan, fixed before the rule was built or run

Written 11 November 2026. Results go in `PACE.md`.

## Why

One review of a mis-set profile does no harm beyond noise on TimSim (`BAD_PROFILES_4.md`). Three
reviews in sequence do (`GUARD_PLAN.md`): strengthening compounds over reviews, and at the end of
the three-review run of the current page (`bad_profiles_2026-11-09-stepA.json`) 56 of 96
subject-conditions had a carb ratio below ×0.8 of the mis-set value. Every rise in time below 54
above the null maximum was among them. Making the estimate the right size did not change that
(`BODY.md`): the stages still take any change the twin rates as a gain, and a single review can
strengthen every setting by up to 30% at once.

Tim's direction, 11 November 2026: the twin should not try to fix everything at once; reducing
lows and not increasing them come first, so it should strengthen slowly and weaken faster, as long
as weakening can be done safely.

## Change

An option of the settings tests, `pace`, off unless given, so the published page is unchanged.
With it, among values towards more insulin, two more are excluded, through the same exclusion the
strengthening limit and the guard use:

- any value more than one step from the current setting (basal ×1.1, ISF and carb ratio ×0.9,
  target −9 mg/dL, the next SMB limit or max IOB value up);
- every value towards more insulin once an earlier stage in the same review has chosen one, so a
  review strengthens one setting at most. The stages run in their existing order (basal, ISF,
  carb ratio, target, SMB limit, max IOB), so basal is considered first.

Values towards less insulin are not touched: a review can still weaken any setting by up to three
steps (30%, or 18 mg/dL on the target). That keeps weakening at the pace that, in every mis-set run
so far, took time below 54 down in the conditions with too much insulin. Its safety rests on what
it already rests on: a weaker value is chosen only when it meets the aim with the smallest change,
gives the most time in range with lows under 2%, or has the fewest lows. The step sizes are the
existing grid and the one-setting rule is a modelling choice, following Tim's order of basal, then
ISF, then carb ratio.

The guard of `GUARD_PLAN.md` (no further strengthening of a setting without evidence the last
step gained, and nothing past 20% towards more insulin from the reference profile) is kept and
given its history as in that test. With one step of 10% per review, the cap allows two reviews of
strengthening on one setting.

## Test

The round trip with three reviews, as `GUARD_PLAN.md`: twelve subjects, eight mis-set conditions,
tighter aim, 10 g rule, evaluation on seeds 101 to 103 for 28 days, the page's simulator (no body
model). Arm P is `--guard --pace`.

| Body | Arm A (current page) | Arm C (guard) | Arm P (guard and pace) |
|---|---|---|---|
| S2008 | `bad_profiles_2026-11-09-stepA.json` | `bad_profiles_2026-11-10-guardC.json` | new, mis-set and null arms reused from `bad_profiles_2026-10-09b.json` |
| Hovorka | `bad_profiles_2026-11-10-hovA.json` | `bad_profiles_2026-11-10-hovC.json` | new, mis-set and null arms reused from `bad_profiles_2026-11-10-hovA.json` |

## The harm criterion on rises above the null maximum, amended

The fourth harm criterion of `BAD_PROFILES_PLAN_4.md` counts against an arm at any rise in time
below 54 above the null arm's maximum. With 96 cases set against the largest of 96 null cases, an
arm whose cases are exchangeable with the null arm's has at least one such rise with probability
0.50, at least two with 0.25, and at least five with 0.030 (the chance that the top k of 192
exchangeable values all come from the arm, C(96, k)/C(192, k)). The criterion as written fails an
arm that changes nothing half the time. This was noticed after the guard's result (2 rises on each
body) had been read, so the guard is not re-judged by it here; its counts are reported beside P's.
For P, and from now on, the criterion counts against an arm at five or more rises above the null
maximum.

## Judgement

Arm P goes forward to the page wiring when, on both bodies, all of these hold:

1. No harm criterion is met, against that body's null arm (S2008: 95th percentile +0.349 points,
   maximum +0.413; Hovorka: +0.456 and +0.823): ten or more of 96 exceedances of the 95th
   percentile; five or more rises above the maximum; exceedances among subjects given more insulin
   at a binomial probability under 0.05; fewer passing the pass rule than with the mis-set profile
   in any condition.
2. Lows fall where there is too much insulin. In the 48 subject-conditions of isf_strong,
   basal_high, cr_strong and all_strong, the median change in time below 54 from the mis-set start
   (evaluation, sensor pooled over three seeds) has a bootstrap 95% interval over subjects wholly
   below zero.
3. Lows are no higher than with the current page. Over all 96, paired P minus A in time below 54
   has a bootstrap 95% interval whose upper end is below +0.05 points. The margin is a modelling
   choice: about a seventh of the null arm's 95th percentile.

Time in range is reported, not judged, since Tim has put lows first: paired P minus A and P minus
C, medians by condition against the mis-set start, and the number of the 48 with too little
insulin that meet the tighter aim. Also reported: how often each review strengthened a setting and
which, how often pace and the guard each excluded a value, and the settings each arm ends with
(the share ending with any of basal, ISF or carb ratio more than 20% towards more insulin).

Expected, stated before the run: P has fewer rises above the null maximum than A and about as many
as C; it meets criteria 2 and 3 on both bodies; in the too-little-insulin conditions its time in
range is at or below C's, since it strengthens at most one setting by 10% per review; no row ends
more than 20% towards more insulin on any setting.

## Limits

Three reviews show the first six weeks of use. A weak profile corrected one 10% step a fortnight
on one setting takes several months, and these runs do not reach that far. TimSim's absolute levels
are not trusted, so only the comparisons between arms count.

## Amendment, 11 November 2026, while arm P was running and before any result was read

Tim's reply on what safe weakening means: time above 250 mg/dL is not a criterion, provided any
loss of time in range is justified. A loss is taken as justified where it buys fewer lows. Per
condition and over all 96, paired P minus A is reported for time in range and time below 70, each
with a bootstrap 95% interval over subjects. A condition's loss of time in range is called
justified when the interval for time in range lies below zero and the interval for time below 70
also lies below zero; it is called unjustified when time in range falls with its interval below
zero and time below 70 does not. Neither verdict changes the judgement above. They say whether
the cost the plan already reports was paid for.
