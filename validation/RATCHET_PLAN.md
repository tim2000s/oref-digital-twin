# Does each review add insulin because TimSim's glucose returns? Plan, fixed before the run

Written 9 November 2026, before the script was run. Results go in `RATCHET.md`.

## Why

Over three reviews the twin kept strengthening settings (`STEP_PLAN.md`, arm B): the carb ratio was
strengthened in 40, 50 and 41 of 96 subject-conditions at reviews 1, 2 and 3, and some profiles
reached ×0.34 to ×0.54 of the mis-set values. `DECAY.md` found that in TimSim glucose follows an
insulin difference for an hour or two and then returns (time constant about 2.4 h), whereas the
twin keeps the shift. A setting made stronger would then leave much the same highs in the next
fortnight, and the twin, still expecting a lasting effect, would recommend more again. A first look
at arm B compared each review's fortnight with the next, but those used different seeds, so meals
and sensitivity differed as well as the profile. This check holds the seed fixed.

## Design

For each of the 96 rows of a three-review run and each review r (1 to 3), with p_r the profile
review r was given and p_r+1 the profile after its choices, both on review r's learning seed
(202, 203 or 204) for 14 days:

1. run TimSim with p_r (the base run) and check it reproduces the stored learning outcomes for
   review r; a mismatch is a fault and stops the summary;
2. run TimSim with p_r+1 (the next run), with the SMB limit each profile carried in the original
   run;
3. run the page's settings tests on the next run, with the rule of the run being checked (the
   re-review);
4. run the settings tests with the decay of `DECAY.md` (`decay_tau_min` 144) on both the base run
   and the next run.

A choice gives more insulin when at least one of basal, ISF, carb ratio and target moves towards
more insulin (basal up; ISF, carb ratio or target down) and none moves the other way; less insulin
mirrors it; anything else with a change is mixed.

Measured per case, next minus base on the same seed: insulin in U/day, mean sensor glucose, time in
range, below 70 and below 54, and the daily mean glucose difference for each of the 14 days. Set
against the twin's own estimate at review r (`du_per_day`, `mean_shift`, `est_all`).

Run on the current page's three-review run first (`bad_profiles_2026-11-09-stepA.json`, from main),
then on arm B (`bad_profiles_2026-11-09-stepB.json`, from the step-rule branch), seven workers.

## Judgement

Among cases where review r chose more insulin, the ratchet is attributed to the twin's lasting
shift meeting TimSim's return when both hold:

- the page re-review on the same seed chooses more insulin again in at least half;
- the realised fall in mean glucose per extra U/day, next minus base, has a median below the
  twin's estimated fall per U/day, and the bootstrap 95% interval of the difference between the
  two medians excludes zero. Cases enter this comparison only where both the realised and the
  estimated insulin difference exceed 0.2 U/day, since the ratio is unstable near zero.

If the re-review chooses more insulin again in under half, the repeated strengthening in the
three-review runs comes mainly from the change of seed between reviews. Reported either way: the
same repeat rate under the decay, counted among cases where the decayed twin chose more insulin on
the base run, with the difference from the page's and a bootstrap interval; and the daily
difference by day, as a check that the gap does not shrink over days as well as hours.

Expected, stated before the run: the page repeats more insulin in more than half; realised mean
glucose falls by about 2 mg/dL per extra U/day against about 8 estimated, as `WEAK_FIX.md`'s
diagnosis found on evaluation; the daily difference is roughly flat after day 1; the decayed twin
repeats less often than the page.

## Limits

Both runs of a case use the fortnight review r learned on, so the re-review sees data from a
profile it was never shown in the original run. Twelve subjects are not independent across the
eight conditions and three reviews, so the intervals resample subjects.
