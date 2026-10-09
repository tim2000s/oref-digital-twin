# Mis-set profiles through TimSim: plan, fixed before the run

Written 9 October 2026, before any result existed. The results go in `BAD_PROFILES.md`, which
judges them against this plan as written. Anything decided after the results were seen is
marked as such there.

## Question

When the starting profile is wrong in either direction, do the twin's settings tests move a
person to the pass rule below, and do they ever cause harm? The 9 October round trip
(`TIMSIM_ROUNDTRIP.md`) started from titrated profiles with too many lows, so the twin almost
never recommended more insulin. This test makes it do so.

## Subjects and profiles

The twelve TimSim adults titrated on 9 October (`results/titrated_2026-10-09.json`). Each
titrated profile is mis-set eight ways, multiplying the hourly arrays:

| Condition | ISF | Basal | Carb ratio | More or less insulin than titrated |
|---|---|---|---|---|
| isf_strong | ×0.7 | | | more |
| isf_weak | ×1.4 | | | less |
| basal_high | | ×1.3 | | more |
| basal_low | | ×0.7 | | less |
| cr_strong | | | ×0.7 | more |
| cr_weak | | | ×1.4 | less |
| all_strong | ×0.7 | ×1.3 | ×0.7 | more |
| all_weak | ×1.4 | ×0.7 | ×1.4 | less |

Target, max IOB and SMB limits are left as titrated. The twin steps each setting across ±30%,
so it cannot fully undo a ×0.7 mis-set (undoing it needs ×1.43). That is a property of the tool
under test and is reported, not corrected for.

## Procedure per subject and condition

As in `timsim_roundtrip.py`: 14 days under TimSim's oref0 SMB controller (TimSim f0e5e45 or
later, issue 54 fixed) with the mis-set profile, seed 202; the twin's settings tests on those
days with its deployed goals (time in range above 70%, time below 70 under 2%); the twin's
choices applied to the mis-set profile; then 28 days on TimSim's benchmark seed 101, run once
with the mis-set profile and once with the twin's, same seed.

## Pass rule, per subject, on the evaluation month's sensor glucose

A subject passes when all three hold: time in range (70 to 180 mg/dL) above 80%, time below
70 mg/dL under 1.5%, time below 54 mg/dL under 0.4%.

For each condition the result is the number of the twelve subjects passing with the mis-set
profile and with the twin's profile. The titrated profiles of the 9 October round trip are
reported beside them as a reference for what the titration itself achieves.

## Harm check

Separately from the pass rule, every subject whose time below 54 mg/dL is higher with the
twin's profile than with the mis-set one is flagged and listed with the size of the rise. A rise
of more than 0.2 percentage points is counted as harm. The 0.2 is a threshold chosen in advance,
not a measured noise floor.

The twin's recommendations are also classed by direction (more insulin: basal up, ISF down,
carb ratio down, target down, SMB limit or max IOB up), and the harm count is reported
separately for subjects who were given more insulin.

## Secondary

The same statistics on true glucose (`bg`). The twin's estimated change against the realised
change. Whether the twin moved each mis-set setting back towards its titrated value.

## What would count against the twin

Any harm, as defined above, in a condition where the mis-set profile was too strong and the twin
was correcting it, or in any subject given more insulin. Fewer subjects passing with the twin's
profile than with the mis-set one in any condition.
