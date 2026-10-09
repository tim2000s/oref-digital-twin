# oref digital twin — report

Findings: 1 critical, 2 to watch, 2 notes.

## Your setup

- Detected: **unknown** (confidence 0.0)
- The controller could not be classified — findings only.

## Glucose

- Readings: 4032 over ~14.0 days
- Mean: 119.2 mg/dL (6.6 mmol/L), GMI 6.2%
- Time in range (70–180): 89.9%
- Time below 70: 3.5%; below 54: 1.4%
- Time above 180: 6.6%; above 250: 0.1%
- Variability (CV): 27.7%

## Findings

### Critical

- **Severe hypoglycaemia exposure above the 1% limit** — 1.4% of readings are below 54 mg/dL (3.0 mmol/L), above the 1.0% consensus safety limit. This is the priority to address.

### Worth attention

- **Overnight SMBs at high IOB, with lows following** — 104 of 281 overnight SMBs fired at high IOB (>= p75 3.44 U); 1 (1.0%) were followed by BG < 70 mg/dL within 2h. Association only — this names the pattern, it does not prove the SMB caused the low.
- **Nocturnal hypoglycaemia episodes** — 3 overnight (00:00-06:00) low episode(s) below 70 mg/dL across 3 night(s). Overnight lows are the domain's repeated risk; cross-check against overnight SMBs and IOB.

### Notes

- **Estimated daily insulin** — ~69.5 U/day estimated (profile basal ~26.68 U + bolus/SMB ~42.8 U/day). Rough: basal is the scheduled profile, not delivered basal, and temp basals are not integrated.
- **30-min IOB prediction bias -8.6 mg/dL** — Over 4027 cycles the IOB-only prediction ran 8.6 mg/dL lower than realised on average (MAE 17.7). A large systematic bias points at model calibration; it is descriptive, not a dosing instruction.


---

_This is decision-support, not medical advice, and it is advisory-only — it never changes your loop or pump. Discuss any change with your clinician and trial it deliberately._

## Settings tests (estimated)

Goal: time in range above 70% and time below range under 2%. Observed over 14.0 days: 89.9% in range, 3.5% below, 8 low episodes.

Each setting is stepped from −30% to +30% and the loop is re-run through every 5-minute cycle (4032) under each value. Basal is tested first, on fasting stretches; ISF next, on correction stretches; then carb ratio on meals; then target, the SMB limit and max IOB over the whole period. Each stage keeps the choices before it.

_Estimated, not measured: each value's glucose is your CGM shifted by the change in insulin the loop would have given, times your profile ISF, with the loop reacting to the shifted glucose at every step. It assumes your meals, activity and own treatments would have been the same, and that your profile ISF is your real sensitivity. Treat any change as a trial to test, one setting at a time._

_Your loop was detected as unknown. These tests run stock oref0, so anything your variant adds on top of it is not modelled._

Insulin curve: rapid-acting (settings).

### 1. Basal

Judged on fasting stretches (no carbs or meal-sized rise in the last 4 h, nothing above 180 mg/dL in the last 3 h): 117.2 h of readings, observed 94.0% in range and 6.0% below.

| Basal rates | Average glucose change | In range (fasting) | Below range (fasting) | Low episodes | In range (all) | Below range (all) |
|---|---|---|---|---|---|---|
| -30% ← | +8 mg/dL (+0.4 mmol/L) | 96.7% | 3.3% | 5 | 89.0% | 2.5% |
| -20% | +5 mg/dL (+0.3 mmol/L) | 95.4% | 4.6% | 4 | 89.0% | 3.0% |
| -10% | +3 mg/dL (+0.2 mmol/L) | 94.9% | 5.1% | 5 | 89.4% | 3.2% |
| current | +0 mg/dL (+0.0 mmol/L) | 94.0% | 6.0% | 6 | 89.9% | 3.5% |
| +10% | -2 mg/dL (-0.1 mmol/L) | 93.2% | 6.8% | 6 | 90.0% | 4.2% |
| +20% | -5 mg/dL (-0.3 mmol/L) | 92.2% | 7.8% | 9 | 90.2% | 4.8% |
| +30% | -8 mg/dL (-0.4 mmol/L) | 90.8% | 9.2% | 10 | 89.9% | 5.6% |

Trial to consider: basal rates -30%, because no value gets lows under 2%; this has the fewest.

### 2. ISF

Judged on correction stretches (above 180 mg/dL in the last 3 h, outside meals): 11.8 h of readings, observed 78.0% in range and 22.0% below.
Run with basal rates -30%.

| ISF | Average glucose change | In range (correction) | Below range (correction) | Low episodes | In range (all) | Below range (all) |
|---|---|---|---|---|---|---|
| -30% | -3 mg/dL (-0.2 mmol/L) | 73.8% | 26.2% | 3 | 89.2% | 5.1% |
| -20% | +1 mg/dL (+0.0 mmol/L) | 78.0% | 22.0% | 2 | 89.1% | 3.8% |
| -10% | +4 mg/dL (+0.2 mmol/L) | 78.0% | 22.0% | 2 | 88.9% | 3.2% |
| current | +8 mg/dL (+0.4 mmol/L) | 78.7% | 21.3% | 2 | 89.0% | 2.5% |
| +10% | +11 mg/dL (+0.6 mmol/L) | 80.1% | 19.9% | 2 | 88.8% | 2.1% |
| +20% | +14 mg/dL (+0.8 mmol/L) | 82.3% | 16.3% | 2 | 88.6% | 1.6% |
| +30% ← | +17 mg/dL (+0.9 mmol/L) | 91.5% | 5.0% | 1 | 88.5% | 0.9% |

Trial to consider: ISF +30%, because no value gets lows under 2%; this has the fewest.

### 3. Carb ratio

Judged on meal stretches (the 4 h after logged carbs or a meal-sized rise): 207.1 h of readings, observed 88.2% in range and 1.1% below.
Run with basal rates -30%, ISF +30%.
Logged meal boluses are scaled with the ratio, as the bolus wizard would.

| Carb ratio | Average glucose change | In range (meal) | Below range (meal) | Low episodes | In range (all) | Below range (all) |
|---|---|---|---|---|---|---|
| -30% | +15 mg/dL (+0.9 mmol/L) | 83.1% | 0.6% | 1 | 88.6% | 1.2% |
| -20% | +16 mg/dL (+0.9 mmol/L) | 83.0% | 0.6% | 1 | 88.7% | 1.1% |
| -10% | +16 mg/dL (+0.9 mmol/L) | 82.9% | 0.6% | 1 | 88.7% | 1.0% |
| current ← | +17 mg/dL (+0.9 mmol/L) | 82.5% | 0.6% | 1 | 88.5% | 0.9% |
| +10% | +17 mg/dL (+0.9 mmol/L) | 82.3% | 0.6% | 1 | 88.6% | 0.8% |
| +20% | +18 mg/dL (+1.0 mmol/L) | 82.2% | 0.6% | 1 | 88.5% | 0.7% |
| +30% | +18 mg/dL (+1.0 mmol/L) | 81.9% | 0.6% | 1 | 88.3% | 0.7% |

No change suggested: already meets both goals.

### 4. Target

Judged on the whole period: 336.0 h of readings, observed 89.9% in range and 3.5% below.
Run with basal rates -30%, ISF +30%.

| Target | Average glucose change | In range | Below range | Low episodes |
|---|---|---|---|---|
| -1.0 mmol/L (-18 mg/dL) on every target: 92 mg/dL (5.1 mmol/L) | -1 mg/dL (-0.1 mmol/L) | 89.6% | 3.8% | 8 |
| -0.5 mmol/L (-9 mg/dL) on every target: 101 mg/dL (5.6 mmol/L) | +8 mg/dL (+0.4 mmol/L) | 89.1% | 2.3% | 6 |
| 110 mg/dL (6.1 mmol/L) (current) ← | +17 mg/dL (+0.9 mmol/L) | 88.5% | 0.9% | 4 |
| +0.5 mmol/L (+9 mg/dL) on every target: 119 mg/dL (6.6 mmol/L) | +26 mg/dL (+1.4 mmol/L) | 86.6% | 0.1% | 1 |
| +1.0 mmol/L (+18 mg/dL) on every target: 128 mg/dL (7.1 mmol/L) | +34 mg/dL (+1.9 mmol/L) | 82.8% | 0.0% | 0 |

No change suggested: already meets both goals.

### 5. SMB limit

Judged on the whole period: 336.0 h of readings, observed 89.9% in range and 3.5% below.
Run with basal rates -30%, ISF +30%.

| Maximum SMB basal minutes | Average glucose change | In range | Below range | Low episodes |
|---|---|---|---|---|
| 15 min | +18 mg/dL (+1.0 mmol/L) | 88.3% | 0.6% | 2 |
| 30 min | +17 mg/dL (+0.9 mmol/L) | 88.5% | 0.8% | 3 |
| 45 min | +17 mg/dL (+0.9 mmol/L) | 88.5% | 0.9% | 4 |
| 60 min | +16 mg/dL (+0.9 mmol/L) | 88.6% | 1.0% | 4 |
| 75 min (current) ← | +16 mg/dL (+0.9 mmol/L) | 88.6% | 1.0% | 4 |
| 90 min | +16 mg/dL (+0.9 mmol/L) | 88.6% | 1.0% | 4 |

No change suggested: already meets both goals.

### 6. Max IOB

Judged on the whole period: 336.0 h of readings, observed 89.9% in range and 3.5% below.
Run with basal rates -30%, ISF +30%.

| Max IOB | Average glucose change | In range | Below range | Low episodes |
|---|---|---|---|---|
| 5.9 U | +16 mg/dL (+0.9 mmol/L) | 87.9% | 1.4% | 6 |
| 6.7 U | +16 mg/dL (+0.9 mmol/L) | 88.2% | 1.2% | 5 |
| 7.6 U | +16 mg/dL (+0.9 mmol/L) | 88.3% | 1.2% | 5 |
| 8.4 U ← | +16 mg/dL (+0.9 mmol/L) | 88.5% | 1.0% | 4 |
| 9.3 U | +17 mg/dL (+1.0 mmol/L) | 88.8% | 0.5% | 3 |
| 10.1 U | +17 mg/dL (+1.0 mmol/L) | 88.8% | 0.5% | 3 |
| 10.9 U | +17 mg/dL (+1.0 mmol/L) | 88.8% | 0.5% | 3 |

Trial to consider: max IOB 8.4 U, because the smallest change that meets both goals.

### Together

With basal rates -30%, ISF +30%, max IOB 8.4 U: estimated 88.5% in range and 1.0% below (observed 89.9% and 3.5%), average glucose +16 mg/dL (+0.9 mmol/L). That meets both goals.

Change one setting at a time and give each a few days before the next, so its effect can be seen on its own.