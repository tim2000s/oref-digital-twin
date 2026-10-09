# oref digital twin — report

Findings: 0 critical, 2 to watch, 3 notes.

## Your setup

- Detected: **unknown** (confidence 0.0)
- The controller could not be classified — findings only.

## Glucose

- Readings: 4032 over ~14.0 days
- Mean: 127.4 mg/dL (7.1 mmol/L), GMI 6.4%
- Time in range (70–180): 85.3%
- Time below 70: 4.2%; below 54: 0.8%
- Time above 180: 10.5%; above 250: 0.1%
- Variability (CV): 30.3%

## Findings

### Worth attention

- **Time below 70 mg/dL above the 4% target** — 4.2% of readings are below 70 mg/dL (3.9 mmol/L), above the 4.0% consensus target.
- **Nocturnal hypoglycaemia episodes** — 6 overnight (00:00-06:00) low episode(s) below 70 mg/dL across 6 night(s). Overnight lows are the domain's repeated risk; cross-check against overnight SMBs and IOB.

### Notes

- **Estimated daily insulin** — ~60.8 U/day estimated (profile basal ~22.15 U + bolus/SMB ~38.6 U/day). Rough: basal is the scheduled profile, not delivered basal, and temp basals are not integrated.
- **Overnight SMBs at high IOB, with lows following** — 137 of 298 overnight SMBs fired at high IOB (>= p75 4.56 U); 0 (0.0%) were followed by BG < 70 mg/dL within 2h. Association only — this names the pattern, it does not prove the SMB caused the low.
- **30-min IOB prediction bias -11.4 mg/dL** — Over 4027 cycles the IOB-only prediction ran 11.4 mg/dL lower than realised on average (MAE 18.0). A large systematic bias points at model calibration; it is descriptive, not a dosing instruction.


---

_This is decision-support, not medical advice, and it is advisory-only — it never changes your loop or pump. Discuss any change with your clinician and trial it deliberately._

## Settings tests (estimated)

Goal: time in range above 70% and time below range under 2%. Observed over 14.0 days: 85.3% in range, 4.2% below, 16 low episodes.

Each setting is stepped from −30% to +30% and the loop is re-run through every 5-minute cycle (4032) under each value. Basal is tested first, on fasting stretches; ISF next, on correction stretches; then carb ratio on meals; then target, the SMB limit and max IOB over the whole period. Each stage keeps the choices before it.

_Estimated, not measured: each value's glucose is your CGM shifted by the change in insulin the loop would have given, times your profile ISF, with the loop reacting to the shifted glucose at every step. It assumes your meals, activity and own treatments would have been the same, and that your profile ISF is your real sensitivity. Treat any change as a trial to test, one setting at a time._

_Your loop was detected as unknown. These tests run stock oref0, so anything your variant adds on top of it is not modelled._

Insulin curve: rapid-acting (settings).

### 1. Basal

Judged on fasting stretches (no carbs or meal-sized rise in the last 4 h, nothing above 180 mg/dL in the last 3 h): 109.7 h of readings, observed 93.5% in range and 6.5% below.

| Basal rates | Average glucose change | In range (fasting) | Below range (fasting) | Low episodes | In range (all) | Below range (all) |
|---|---|---|---|---|---|---|
| -30% ← | +9 mg/dL (+0.5 mmol/L) | 97.0% | 2.2% | 2 | 82.5% | 2.0% |
| -20% | +6 mg/dL (+0.3 mmol/L) | 96.4% | 3.3% | 3 | 83.8% | 2.5% |
| -10% | +3 mg/dL (+0.2 mmol/L) | 94.8% | 5.2% | 6 | 84.8% | 3.3% |
| current | +0 mg/dL (+0.0 mmol/L) | 93.5% | 6.5% | 9 | 85.3% | 4.2% |
| +10% | -3 mg/dL (-0.2 mmol/L) | 89.9% | 10.1% | 14 | 85.2% | 5.9% |
| +20% | -6 mg/dL (-0.3 mmol/L) | 87.5% | 12.5% | 14 | 84.4% | 7.6% |
| +30% | -9 mg/dL (-0.5 mmol/L) | 85.7% | 14.3% | 17 | 84.1% | 9.0% |

Trial to consider: basal rates -30%, because no value gets lows under 2%; this has the fewest.

### 2. ISF

Judged on correction stretches (above 180 mg/dL in the last 3 h, outside meals): 26.1 h of readings, observed 73.2% in range and 5.4% below.
Run with basal rates -30%.

| ISF | Average glucose change | In range (correction) | Below range (correction) | Low episodes | In range (all) | Below range (all) |
|---|---|---|---|---|---|---|
| -30% | -4 mg/dL (-0.2 mmol/L) | 77.0% | 8.9% | 4 | 84.5% | 7.6% |
| -20% | +0 mg/dL (+0.0 mmol/L) | 75.7% | 5.4% | 3 | 85.3% | 4.8% |
| -10% | +5 mg/dL (+0.3 mmol/L) | 69.6% | 4.5% | 3 | 84.4% | 3.1% |
| current | +9 mg/dL (+0.5 mmol/L) | 54.3% | 3.5% | 1 | 82.5% | 2.0% |
| +10% | +12 mg/dL (+0.7 mmol/L) | 41.9% | 2.6% | 1 | 80.3% | 1.1% |
| +20% | +16 mg/dL (+0.9 mmol/L) | 31.9% | 2.6% | 1 | 78.0% | 0.5% |
| +30% ← | +19 mg/dL (+1.0 mmol/L) | 29.7% | 1.6% | 0 | 76.0% | 0.3% |

Trial to consider: ISF +30%, because no value reaches 70% in range; this keeps lows under 2% with the most time in range.

### 3. Carb ratio

Judged on meal stretches (the 4 h after logged carbs or a meal-sized rise): 200.2 h of readings, observed 82.4% in range and 2.7% below.
Run with basal rates -30%, ISF +30%.
Logged meal boluses are scaled with the ratio, as the bolus wizard would.

| Carb ratio | Average glucose change | In range (meal) | Below range (meal) | Low episodes | In range (all) | Below range (all) |
|---|---|---|---|---|---|---|
| -30% | +16 mg/dL (+0.9 mmol/L) | 72.5% | 0.2% | 0 | 77.1% | 0.4% |
| -20% | +17 mg/dL (+1.0 mmol/L) | 71.6% | 0.2% | 0 | 76.6% | 0.3% |
| -10% | +18 mg/dL (+1.0 mmol/L) | 71.4% | 0.2% | 0 | 76.4% | 0.3% |
| current ← | +19 mg/dL (+1.0 mmol/L) | 70.8% | 0.2% | 0 | 76.0% | 0.3% |
| +10% | +20 mg/dL (+1.1 mmol/L) | 70.2% | 0.1% | 0 | 75.6% | 0.2% |
| +20% | +20 mg/dL (+1.1 mmol/L) | 69.7% | 0.1% | 0 | 75.4% | 0.1% |
| +30% | +21 mg/dL (+1.2 mmol/L) | 69.6% | 0.1% | 0 | 75.2% | 0.1% |

No change suggested: already meets both goals.

### 4. Target

Judged on the whole period: 336.0 h of readings, observed 85.3% in range and 4.2% below.
Run with basal rates -30%, ISF +30%.

| Target | Average glucose change | In range | Below range | Low episodes |
|---|---|---|---|---|
| -1.0 mmol/L (-18 mg/dL) on every target: 92 mg/dL (5.1 mmol/L) | +1 mg/dL (+0.1 mmol/L) | 81.2% | 4.1% | 15 |
| -0.5 mmol/L (-9 mg/dL) on every target: 101 mg/dL (5.6 mmol/L) | +10 mg/dL (+0.5 mmol/L) | 79.3% | 1.4% | 6 |
| 110 mg/dL (6.1 mmol/L) (current) ← | +19 mg/dL (+1.0 mmol/L) | 76.0% | 0.3% | 1 |
| +0.5 mmol/L (+9 mg/dL) on every target: 119 mg/dL (6.6 mmol/L) | +28 mg/dL (+1.5 mmol/L) | 72.3% | 0.0% | 0 |
| +1.0 mmol/L (+18 mg/dL) on every target: 128 mg/dL (7.1 mmol/L) | +36 mg/dL (+2.0 mmol/L) | 67.0% | 0.0% | 0 |

No change suggested: already meets both goals.

### 5. SMB limit

Judged on the whole period: 336.0 h of readings, observed 85.3% in range and 4.2% below.
Run with basal rates -30%, ISF +30%.

| Maximum SMB basal minutes | Average glucose change | In range | Below range | Low episodes |
|---|---|---|---|---|
| 15 min | +20 mg/dL (+1.1 mmol/L) | 75.5% | 0.2% | 1 |
| 30 min | +19 mg/dL (+1.1 mmol/L) | 75.8% | 0.2% | 1 |
| 45 min | +19 mg/dL (+1.0 mmol/L) | 76.0% | 0.3% | 1 |
| 60 min | +19 mg/dL (+1.0 mmol/L) | 76.0% | 0.2% | 0 |
| 75 min (current) ← | +19 mg/dL (+1.0 mmol/L) | 76.1% | 0.2% | 0 |
| 90 min | +19 mg/dL (+1.0 mmol/L) | 76.1% | 0.2% | 0 |

No change suggested: already meets both goals.

### 6. Max IOB

Judged on the whole period: 336.0 h of readings, observed 85.3% in range and 4.2% below.
Run with basal rates -30%, ISF +30%.

| Max IOB | Average glucose change | In range | Below range | Low episodes |
|---|---|---|---|---|
| 5.2 U | +23 mg/dL (+1.3 mmol/L) | 75.0% | 0.9% | 4 |
| 5.9 U | +19 mg/dL (+1.1 mmol/L) | 75.2% | 0.8% | 3 |
| 6.6 U | +18 mg/dL (+1.0 mmol/L) | 75.4% | 0.8% | 4 |
| 7.4 U ← | +19 mg/dL (+1.0 mmol/L) | 76.1% | 0.2% | 0 |
| 8.1 U | +19 mg/dL (+1.0 mmol/L) | 76.1% | 0.2% | 0 |
| 8.9 U | +19 mg/dL (+1.0 mmol/L) | 76.1% | 0.2% | 0 |
| 9.6 U | +19 mg/dL (+1.0 mmol/L) | 76.1% | 0.2% | 0 |

Trial to consider: max IOB 7.4 U, because the smallest change that meets both goals.

### Together

With basal rates -30%, ISF +30%, max IOB 7.4 U: estimated 76.1% in range and 0.2% below (observed 85.3% and 4.2%), average glucose +19 mg/dL (+1.0 mmol/L). That meets both goals.

Change one setting at a time and give each a few days before the next, so its effect can be seen on its own.