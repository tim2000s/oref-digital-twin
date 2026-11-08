# Settings read and replayed as configured: plan for the rechecks, fixed before they ran

Written 8 November 2026, before any of the runs below. Results go in `SETTINGS_FIX.md`.

## What changed

A check of how the page reads settings files, against the AndroidAPS and Trio sources, found
faults in the settings reader and in the oref profile the replay builds. Two of them change what
the replay simulates for everyone, with or without a settings file:

- The replay set a profile field `enableSMB_uam`, which oref0 does not read. oref0 reads
  `enableUAM`, so every replay ran with unannounced-meal predictions off. It now sets `enableUAM`,
  on unless the settings say otherwise.
- `max_daily_basal` was the scheduled rate at the cycle. oref0 and AndroidAPS use the largest
  scheduled rate of the day, which bounds the temp basal through the daily safety multiplier.

The others change only what is read from a file:

- AndroidAPS's SMB switches are now kept apart, as oref0 has them, rather than collapsed into one.
- Max IOB is taken from the SMB key, then the AMA key, never from Boost's own tier cap.
- Max basal, the two basal safety multipliers and the insulin curve are read where the file has
  them, and Trio's high-glucose SMB switch is replayed.

TimSim's oref controller (`timsim/controller/oref.py`) runs with UAM on and with the daily basal as
the largest scheduled rate. Until now the twin replayed it with UAM off and the current rate, so
the earlier TimSim figures compared TimSim with a loop configured differently from it.

## Runs

1. Same fortnight in TimSim, without options:
   `same_week.py --workers 7 --out results/same_week_2026-11-08.json`. TimSim truth is recomputed
   and the learning run must reproduce itself exactly.
2. The same with the page's 10 g rule: `same_week.py --rescue '{"grams": 10, "threshold": 70,
   "refractory_min": 15, "delay": 10, "rise_min": 30, "mode": "new"}' --truth-from
   results/same_week_2026-11-08.json`, which requires the estimates without options to match run 1.
3. The twelve AndroidAPS events of the private analysis repository's `RESULTS_AAPS.md`, with and
   without the 10 g rule, now passing each SMB switch and the basal multipliers the loop logged.
4. The harm test of `BAD_PROFILES_PLAN_4.md`, unchanged in design, on the fixed twin.

The direction of any change is not predicted: UAM predictions raise or lower oref's insulin
requirement depending on the shape of the rise, and the larger daily basal only lifts a ceiling
that may not bind.

## Judgement

- Run 2 is judged by the criterion of the 10 g plan: the time-below-70 slope's interval includes 1
  and the Spearman correlation is at least 0.815. Run 1 is reported beside the earlier figures
  without a criterion.
- Run 3 is reported beside the earlier real-data figures. With twelve events from five people it
  can show a change in agreement only if it is large, and it is reported as such.
- Run 4 is judged by the harm criteria of `BAD_PROFILES_PLAN_4.md`. None met: the fixes ship with
  the limit as it is. Any one met: the limit is tightened to under 0.8% below 70 and 0.24% below 54
  and the run repeated before release.
- Run 2 failing does not hold the fixes back, since they make the replay match the loop it
  replays; it puts the README's description of the estimate's accuracy back to what run 2 shows.
