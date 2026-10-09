# Mis-set profiles through TimSim, second run: plan, fixed before the run

Written 9 October 2026, before the run. Results go in `BAD_PROFILES_2.md`, judged against this
plan as written.

## What changed since the first run

The twin at 86d1a07: ISF is judged on the whole period (correction stretches only decide whether
there are the 6 hours needed), and a value giving more insulin than the current setting is only
considered when the whole period's estimate keeps time below 70 under 2% and time below 54 under
0.6%. The max IOB stage now tries the exact current value. Its goals are otherwise unchanged:
time in range above 70%, time below 70 under 2%.

The test: the first run judged harm per subject on one 28-day month against a threshold of 0.2
points, which a 0.03 U change in max IOB crossed in 21 of 96 cases. This run repeats each
evaluation on three seeds and sets the harm threshold from a null arm run alongside.

## Design

The same twelve titrated TimSim adults and the same eight mis-set starting profiles as
`BAD_PROFILES_PLAN.md`, learning run 14 days on seed 202, TimSim at e64cf2e or later.

Each subject and condition is evaluated on seeds 101, 102 and 103, 28 days each, with outcomes
pooled over the 84 days. Three arms share those seeds:

| Arm | Profile |
|---|---|
| Start | the mis-set profile |
| Twin | the twin's profile |
| Null | the mis-set profile with max IOB 0.03 U higher, a change with no clinical meaning |

## Pass rule

Unchanged, per subject on the pooled sensor glucose: time in range above 80%, time below 70 under
1.5%, time below 54 under 0.4%. Reported as subjects passing of twelve, start against twin, per
condition, with true glucose beside it.

## Harm

The null change is null minus start in pooled time below 54 (sensor); the twin change is twin
minus start. The harm threshold is the 95th percentile of the 96 null changes. A twin change above
it is an exceedance. With no effect from the twin about 5 of 96 would exceed it by chance.

Counts against the twin, any one sufficient:

1. Ten or more exceedances of 96 (P = 0.03 under no effect, binomial, p = 0.05).
2. Any twin rise larger than the largest null rise.
3. Among subjects given more insulin, exceedances at a rate whose binomial probability under
   p = 0.05 is below 0.05.
4. Fewer subjects passing with the twin's profile than with the mis-set one in any condition.

## Secondary

The direction of the twin's changes and whether each mis-set setting moved back towards its
titrated value; how many values the strengthening limit excluded; the twin's estimated change
against the realised change; the same tables on true glucose; and each of these beside the first
run.
