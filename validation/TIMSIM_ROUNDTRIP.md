# Round trip through TimSim, 9 October 2026

## Question

Does the profile the twin's settings tests suggest improve outcomes for a person, judged on days
the twin never saw? TimSim, a person simulator over the UVA/Padova S2008 model, supplied the
people.

## Design

Twelve TimSim adults (`adult#001` to `adult#012`), each run through four steps by
`validation/timsim_roundtrip.py`:

1. Settings titrated by TimSim's own procedure (its reference loop, 28 days, titration seed 11).
   All twelve were titrated. This is the starting profile TimSim requires of any benchmark, and
   was saved to `results/titrated_2026-10-09.json` rather than to TimSim's shared store.
2. A 14-day learning run under TimSim's oref0 SMB controller with that profile (seed 202),
   exported as Nightscout entries, devicestatus, treatments and profile.
3. The twin's settings tests on the 14 days, with max IOB, max basal, the SMB limits (75 and
   45 minutes, TimSim's settings) and the insulin curve passed as a settings file would pass them.
4. A fresh 28 days on TimSim's benchmark seed (101), run twice: once with the starting profile
   and once with the twin's. Both arms share the seed, so meals, sensor noise and sensitivity
   drift are the same in each and the difference is the profile.

Outcomes are reported on the sensor reading the loop saw (`cgm`) and, separately, on true
glucose without sensor error (`bg`). Following TimSim's convention, each arm gives the median,
mean and range across subjects. The paired difference (twin minus start) carries a bootstrap
95% interval (10,000 resamples of subjects).

### Two corrections to TimSim's oref controller made first

Checking the exported data turned up two defects in TimSim's oref0 adapter, now TimSim issue 54.
The run used the corrected behaviour through a subclass in the script, and TimSim has since been
fixed the same way.

- It pruned its insulin ledger with a 240-minute margin added to the cutoff, so every dose more
  than an hour old was dropped. On one subject over two days oref was handed a mean of 1.31 U of
  insulin on board where its own ledger held 2.60 U.
- It computed insulin on board with TimSim's own curve rather than the exponential curve
  AndroidAPS and oref0 use, which leaves 0.04 to 0.08 more of each unit on board between one and
  four hours.

With both corrected, the twin's insulin on board rebuilt from the exported treatments sat a
median 0.27 U from the figure the simulated loop used, with 74% of cycles within 0.5 U. Before
the corrections the median gap was 1.09 U. On real AndroidAPS data the same comparison gave 0.32 U.

## Results

### What the twin suggested

| Setting | Suggestions across 12 subjects |
|---|---|
| Basal | −30% for 4, −20% for 1, −10% for 1, unchanged for 6 |
| ISF | +30% (weaker) for 8, +10% and +20% for one each, −20% for 1, unchanged for 1 |
| Carb ratio | −30% (stronger) for 2, unchanged for 10 |
| Target, SMB limit, max IOB | unchanged for all 12 |

The suggestions mostly weakened the settings, and eight of twelve ISF choices sat at the edge of
the ±30% band.

### Evaluation month, sensor glucose (`cgm`)

| Measure | Start: median, mean (range) | Twin: median, mean (range) | Twin − start: median [95% CI]; mean [95% CI] | Better with twin |
|---|---|---|---|---|
| Time in range 70–180, % | 86.1, 84.4 (74.8–94.1) | 82.3, 81.7 (71.1–93.1) | −3.04 [−5.12, +0.61]; −2.61 [−4.40, −0.85] | 3/12 |
| Time below 70, % | 2.2, 2.0 (0.3–3.4) | 1.2, 1.3 (0.2–2.3) | −0.51 [−0.90, −0.12]; −0.66 [−1.09, −0.30] | 11/12 |
| Time below 54, % | 0.6, 0.6 (0.1–1.3) | 0.3, 0.3 (0.1–0.9) | −0.18 [−0.37, −0.04]; −0.25 [−0.43, −0.10] | 10/12 |
| Time above 180, % | 12.1, 13.7 (3.2–22.8) | 16.4, 17.0 (5.6–27.1) | +3.22 [−0.43, +5.99]; +3.27 [+1.31, +5.32] | 3/12 |
| Mean glucose, mg/dL | 139.1, 137.7 (123.8–150.0) | 144.1, 143.9 (124.3–157.5) | +6.17 [+0.97, +11.64]; +6.17 [+2.93, +9.57] | — |

On true glucose (`bg`) the pattern was the same: time below 70 fell by a mean 0.54 points
[−0.90, −0.21] and time in range by a mean 2.82 [−4.41, −1.26]. Rescue carbohydrate events fell
from 362 to 256 across the twelve subjects, and mean daily insulin from 59.7 to 57.0 U.

Against the goal of time in range above 70% and time below 70 under 2%, five of twelve subjects
met both with their starting profile and eleven with the twin's. All twelve were above 70% in
range to begin with, so the gain came entirely from time below range. Subject 10 ended at 2.3%
below.

### The twin's own estimates against what happened

The twin's estimates were made on the 14-day learning run; the realised changes are between the
two arms of the evaluation month. Across subjects:

| | Estimated change | Realised change | Correlation, estimated vs realised |
|---|---|---|---|
| Time below 70, points | median −1.70, mean −1.85 | median −0.51, mean −0.66 | 0.79 |
| Time in range, points | median −2.75, mean −2.89 | median −3.04, mean −2.61 | 0.55 |

The direction of the effect on lows matched for 10 of 12 subjects (the other two were within
0.5 points of zero on both sides) and its size was overstated
about threefold. The cost in time in range was estimated close to its realised size on average.

## Reading

Within this simulator the twin's suggestions did what the goal asked: fewer lows, by a margin
whose interval excludes zero on both signals, paid for with about three points of time in range
and 6 mg/dL of mean glucose. The suggestions were steered by the time-below-range goal: all
twelve subjects started above 70% in range, so every stage was choosing among values on lows
alone.

The overstatement of the benefit on lows is what the model's assumptions predict. The estimate
holds meals, rescue carbohydrate and the person's behaviour fixed, so a low avoided in the
estimate still carries the rescue that followed it, and the simulator's people respond to the
changed glucose in ways the estimate cannot see. That makes the twin's figures better at ranking
values than at predicting the size of a change, as its documentation says.

## Limits

- TimSim's people are S2008 subjects with TimSim's behaviour layers. Its own documentation records
  where they depart from real cohorts, notably too little between-person spread, and nothing
  here extends beyond that.
- The starting profiles were titrated under TimSim's reference loop and then run under oref0,
  which left half the subjects above 2% below range. The test therefore exercised the twin
  mostly on lows; a starting profile that was too weak, giving long highs, was not tested.
- Eight ISF choices sat at the +30% edge of the band, so the band, not the data, set those values.
- Twelve subjects, one learning fortnight and one evaluation month each.
- The twin replays stock oref0 0.7.1; TimSim's controller runs its own vendored copy of oref0's
  determine-basal.

## Reproducing

```
~/.venvs/boost-insilico/bin/python validation/timsim_roundtrip.py --subjects 12 --workers 7 --tag 2026-10-09
python3 validation/summarise_roundtrip.py validation/results/timsim_roundtrip_2026-10-09.json
```

The run took 3,206 s on seven workers, 636 s of it titration. Each subject's full twin report
is in `results/reports_2026-10-09/`.
