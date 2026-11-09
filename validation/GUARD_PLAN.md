# A guard on repeated strengthening, tested on both TimSim bodies: plan, fixed before the run

Written 9 November 2026, before the guard was built or run. Results go in `GUARD.md`.

## Why

Run three times in sequence, the current page meets three of the four harm criteria of
`BAD_PROFILES_PLAN_4.md` (`results/bad_profiles_2026-11-09-stepA.json`): six rises in time below 54
above the null maximum, nine of 83 among those given more insulin (P = 0.023), and fewer passing in
cr_weak. Two subjects' carb ratio and ISF reached ×0.34 to ×0.56 of the mis-set values. The
same-fortnight check of `RATCHET_PLAN.md` (`results/ratchet_2026-11-09-stepA.json`) found that,
with the seed held fixed, the page asked for more insulin again in 48 of 91 cases where it had just
done so (53%, 95% interval 47 to 58%), and that mean glucose fell 1.3 mg/dL per extra U/day
(interval 1.0 to 2.0) against the twin's 3.5 (2.2 to 5.0). The decayed twin repeated as often
(51%, difference −1 point, interval −14 to +10), so the decay does not stop the repetition. The
twin's estimate keeps promising a gain the simulated body does not deliver, and nothing in a review
looks at what the last change did.

## Change

The settings tests take an optional history of the settings: the profile in force at the start of
a reference period, the last lasting change and the outcomes either side of it. Two rules use it,
for basal, ISF, carb ratio and target. The SMB limit and max IOB are not covered.

- Evidence. Where the last change moved a setting towards more insulin (basal up, ISF or carb ratio
  down, by more than 5%, or target down by 5 mg/dL or more), every value moving it further is
  excluded unless the readings since the change had at least 2 points more time in range than the
  readings before it and no more time below 70.
- Cap. A value is excluded when it would leave the setting more than 20% towards more insulin than
  the reference profile (basal above ×1.2, ISF or carb ratio below ×0.8 of the reference) or the
  target more than 9 mg/dL below it.

Both act through the existing exclusion of more-insulin values, so a refused value is shown as
excluded and the remaining rules choose among the others. With no history given the tests behave
as now. The 2-point margin is the one `WEAK_FIX_PLAN.md` fixed. The 20% cap and the 5% and 5 mg/dL
thresholds are modelling choices, not measurements: 20% is two steps of the grid.

The page does not pass a history yet, so the published page is unchanged by this work. Deriving
the history from Nightscout's profile records and the readings before the last switch is a
separate change, made only if this test passes.

## Test

The round trip with three reviews (`STEP_PLAN.md`'s design: twelve subjects, eight mis-set
conditions, tighter aim, evaluation on seeds 101 to 103 for 28 days). With `--guard`, review r is
given the mis-set profile as the reference, the choices of review r − 1 as the last change, and the
sensor outcomes of the learning fortnights of reviews r − 1 and r as before and after. Review 1 has
no last change, so only the cap applies.

On each body:

- S2008 (the twelve adults used so far): arm C, the guard, against arm A already run
  (`bad_profiles_2026-11-09-stepA.json`); mis-set and null arms reused from
  `bad_profiles_2026-10-09b.json`.
- Hovorka (`--cohort hovorka`, the first twelve subjects TimSim's own titration found settings
  for, its store `titrated_settings_hovorka.json`): arm A_H, the current page, with its own
  mis-set and null arms; then arm C_H, the guard, reusing A_H's mis-set and null arms.

Then the same-fortnight check of `RATCHET_PLAN.md` on A_H, to see whether the Hovorka body returns
as S2008 does.

## Judgement

The guard goes forward to the page wiring when, on both bodies:

- no harm criterion of `BAD_PROFILES_PLAN_4.md` is met by arm C, against that body's null arm
  (for S2008 the 95th percentile +0.349 points and maximum +0.413; for Hovorka whatever A_H's null
  arm gives);
- of the 48 subject-conditions with too little insulin, the number meeting the tighter aim is no
  more than 2 below arm A's on the same body.

The second is a non-inferiority margin, and its size is a modelling choice: the guard is there to
remove harm and is allowed to cost a little benefit, not more. Reported as well: arm A_H's harm
criteria (a finding about the current page on the second body), the same counts for the 48 with
too much insulin and all 96, medians per condition, each review's choices, and how often each rule
excluded a value.

Expected, stated before the run: on S2008 the guard removes most of arm A's exceedances, since
adult#008 and adult#011 reached their profiles by strengthening the same settings at successive
reviews; weak cases meeting the aim fall by a case or two. On Hovorka, whose production has no
glucose term (`TimSim docs/HOVORKA.md`), the return should be weaker and arm A_H should show less
repeated strengthening than S2008; the cap does most of the guard's work there.
