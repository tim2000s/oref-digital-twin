# Profile switches and temp targets in the replay, 7 November 2026

Until this change the replay rebuilt every loop cycle with the most recent Nightscout profile. Temp
targets were read but not used, and profile switches were not read. Each cycle now runs on the
Profile Switch and Temporary Target in force at its time (`replay/inputs.py`, `in_force`):

- the latest switch that has started and, if temporary, not yet run out, scaled as AndroidAPS
  scales it (basal × percentage, ISF and carb ratio ÷ percentage) and with its schedule moved later
  by its timeshift; its own profile is used where it carries one;
- the latest temp target that has started, while it runs, as oref0's own profile carries it
  (`min_bg`, `max_bg`, `target_bg` and `temptargetSet`); one of length 0 cancels the one before it;
- a settings test of the profile target leaves a running temp target alone, since the loop would.

The page also fetches the latest 20 switches and 5 temp targets from before the window, because one
set earlier can still be in force inside it. Profile values given as strings, as Nightscout's
profile editor stores them, are now read; before they were dropped.

## Check against the profile the loop used

AndroidAPS exports in the OpenAPS Data Commons log the profile oref ran with on every cycle. Their
temp targets and switches were converted to the treatments AndroidAPS uploads to Nightscout, and each
cycle's profile was rebuilt by `build_profile` as the page did before and as it does now. 637 seven-
day windows from 30 users; share of cycles whose rebuilt value matches the logged one (target within
1 mg/dL, the others within 2%), median window and 10th centile:

| Component | Before | After |
|---|---|---|
| Target, temp targets included | 82.2% (53.4%) | 98.6% (95.8%) |
| Basal and carb ratio | 87.6% (19.8%) | 96.8% (81.1%) |
| ISF | 91.8% (33.3%) | 99.8% (91.4%) |

ISF is scored on AndroidAPS 2 switches only, because every AndroidAPS 3 switch in that export
carries its basal blocks in place of its ISF blocks and no targets (48,845 records). In the 516
windows with a temp target on more than 5% of cycles, the target matched on a median 78.8% of cycles
before and 98.2% after. The "before" arm was given the latest switch's percentage, which a
Nightscout profile document does not carry, so it is if anything flattered. The script and the
converter are kept in the private analysis repository with the other real-data checks.

The TimSim validation runs carry no switches or temp targets; their estimates were rerun after the
change and reproduce the stored ones.

## Not covered

Trio and Loop overrides (a scaling of insulin needs and a correction range) are not read. Neither
is a history of Nightscout profile documents: the latest is the base when no switch is in force.
