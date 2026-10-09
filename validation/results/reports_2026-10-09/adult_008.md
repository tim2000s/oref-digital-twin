# oref digital twin — report

Findings: 0 critical, 2 to watch, 3 notes.

## Your setup

- Detected: **unknown** (confidence 0.0)
- The controller could not be classified — findings only.

## Glucose

- Readings: 4032 over ~14.0 days
- Mean: 129.6 mg/dL (7.2 mmol/L), GMI 6.4%
- Time in range (70–180): 86.6%
- Time below 70: 2.4%; below 54: 0.5%
- Time above 180: 11.0%; above 250: 1.7%
- Variability (CV): 31.6%

## Findings

### Worth attention

- **Overnight SMBs at high IOB, with lows following** — 96 of 273 overnight SMBs fired at high IOB (>= p75 2.44 U); 13 (13.5%) were followed by BG < 70 mg/dL within 2h. Association only — this names the pattern, it does not prove the SMB caused the low.
- **Nocturnal hypoglycaemia episodes** — 9 overnight (00:00-06:00) low episode(s) below 70 mg/dL across 9 night(s). Overnight lows are the domain's repeated risk; cross-check against overnight SMBs and IOB.

### Notes

- **Meets consensus glycaemic targets** — TIR 86.6%, TBR<70 2.4%, TBR<54 0.5% — within consensus targets over this window.
- **Estimated daily insulin** — ~60.8 U/day estimated (profile basal ~23.08 U + bolus/SMB ~37.7 U/day). Rough: basal is the scheduled profile, not delivered basal, and temp basals are not integrated.
- **30-min IOB prediction bias -9.4 mg/dL** — Over 4027 cycles the IOB-only prediction ran 9.4 mg/dL lower than realised on average (MAE 20.3). A large systematic bias points at model calibration; it is descriptive, not a dosing instruction.


---

_This is decision-support, not medical advice, and it is advisory-only — it never changes your loop or pump. Discuss any change with your clinician and trial it deliberately._

## Settings tests (estimated)

Goal: time in range above 70% and time below range under 2%. Observed over 14.0 days: 86.6% in range, 2.4% below, 8 low episodes.

Each setting is stepped from −30% to +30% and the loop is re-run through every 5-minute cycle (4032) under each value. Basal is tested first, on fasting stretches; ISF next, on correction stretches; then carb ratio on meals; then target, the SMB limit and max IOB over the whole period. Each stage keeps the choices before it.

_Estimated, not measured: each value's glucose is your CGM shifted by the change in insulin the loop would have given, times your profile ISF, with the loop reacting to the shifted glucose at every step. It assumes your meals, activity and own treatments would have been the same, and that your profile ISF is your real sensitivity. Treat any change as a trial to test, one setting at a time._

_Your loop was detected as unknown. These tests run stock oref0, so anything your variant adds on top of it is not modelled._

Insulin curve: rapid-acting (settings).

### 1. Basal

Judged on fasting stretches (no carbs or meal-sized rise in the last 4 h, nothing above 180 mg/dL in the last 3 h): 87.4 h of readings, observed 96.9% in range and 3.1% below.

| Basal rates | Average glucose change | In range (fasting) | Below range (fasting) | Low episodes | In range (all) | Below range (all) |
|---|---|---|---|---|---|---|
| -30% | +10 mg/dL (+0.6 mmol/L) | 99.1% | 0.9% | 0 | 84.8% | 0.8% |
| -20% ← | +7 mg/dL (+0.4 mmol/L) | 98.4% | 1.6% | 1 | 85.7% | 1.4% |
| -10% | +3 mg/dL (+0.2 mmol/L) | 98.0% | 2.0% | 1 | 86.4% | 1.7% |
| current | +0 mg/dL (+0.0 mmol/L) | 96.9% | 3.1% | 4 | 86.6% | 2.4% |
| +10% | -3 mg/dL (-0.2 mmol/L) | 95.5% | 4.5% | 4 | 86.4% | 3.4% |
| +20% | -7 mg/dL (-0.4 mmol/L) | 94.3% | 5.7% | 8 | 86.2% | 4.8% |
| +30% | -10 mg/dL (-0.6 mmol/L) | 92.9% | 7.1% | 8 | 85.2% | 6.4% |

Trial to consider: basal rates -20%, because the smallest change that meets both goals.

### 2. ISF

Judged on correction stretches (above 180 mg/dL in the last 3 h, outside meals): 15.2 h of readings, observed 76.4% in range and 23.6% below.
Run with basal rates -20%.

| ISF | Average glucose change | In range (correction) | Below range (correction) | Low episodes | In range (all) | Below range (all) |
|---|---|---|---|---|---|---|
| -30% | -6 mg/dL (-0.3 mmol/L) | 53.3% | 46.7% | 7 | 84.4% | 5.9% |
| -20% | -2 mg/dL (-0.1 mmol/L) | 69.2% | 30.8% | 5 | 85.3% | 3.8% |
| -10% | +3 mg/dL (+0.2 mmol/L) | 76.9% | 23.1% | 4 | 85.9% | 2.2% |
| current | +7 mg/dL (+0.4 mmol/L) | 83.0% | 17.0% | 3 | 85.7% | 1.4% |
| +10% | +11 mg/dL (+0.6 mmol/L) | 87.4% | 12.1% | 2 | 84.5% | 0.8% |
| +20% | +15 mg/dL (+0.8 mmol/L) | 94.0% | 4.9% | 1 | 83.2% | 0.4% |
| +30% ← | +18 mg/dL (+1.0 mmol/L) | 95.1% | 3.8% | 1 | 81.9% | 0.3% |

Trial to consider: ISF +30%, because no value gets lows under 2%; this has the fewest.

### 3. Carb ratio

Judged on meal stretches (the 4 h after logged carbs or a meal-sized rise): 233.4 h of readings, observed 83.4% in range and 0.8% below.
Run with basal rates -20%, ISF +30%.
Logged meal boluses are scaled with the ratio, as the bolus wizard would.

| Carb ratio | Average glucose change | In range (meal) | Below range (meal) | Low episodes | In range (all) | Below range (all) |
|---|---|---|---|---|---|---|
| -30% | +18 mg/dL (+1.0 mmol/L) | 74.8% | 0.1% | 0 | 82.2% | 0.3% |
| -20% | +18 mg/dL (+1.0 mmol/L) | 74.6% | 0.1% | 0 | 82.1% | 0.3% |
| -10% | +18 mg/dL (+1.0 mmol/L) | 74.6% | 0.1% | 0 | 82.1% | 0.3% |
| current ← | +18 mg/dL (+1.0 mmol/L) | 74.3% | 0.1% | 0 | 81.9% | 0.3% |
| +10% | +18 mg/dL (+1.0 mmol/L) | 74.3% | 0.1% | 0 | 81.9% | 0.3% |
| +20% | +19 mg/dL (+1.0 mmol/L) | 74.2% | 0.1% | 0 | 81.8% | 0.3% |
| +30% | +19 mg/dL (+1.0 mmol/L) | 73.8% | 0.1% | 0 | 81.5% | 0.3% |

No change suggested: already meets both goals.

### 4. Target

Judged on the whole period: 336.0 h of readings, observed 86.6% in range and 2.4% below.
Run with basal rates -20%, ISF +30%.

| Target | Average glucose change | In range | Below range | Low episodes |
|---|---|---|---|---|
| -1.0 mmol/L (-18 mg/dL) on every target: 92 mg/dL (5.1 mmol/L) | +0 mg/dL (+0.0 mmol/L) | 87.0% | 1.8% | 6 |
| -0.5 mmol/L (-9 mg/dL) on every target: 101 mg/dL (5.6 mmol/L) | +9 mg/dL (+0.5 mmol/L) | 85.0% | 0.7% | 2 |
| 110 mg/dL (6.1 mmol/L) (current) ← | +18 mg/dL (+1.0 mmol/L) | 81.9% | 0.3% | 1 |
| +0.5 mmol/L (+9 mg/dL) on every target: 119 mg/dL (6.6 mmol/L) | +27 mg/dL (+1.5 mmol/L) | 77.8% | 0.1% | 0 |
| +1.0 mmol/L (+18 mg/dL) on every target: 128 mg/dL (7.1 mmol/L) | +36 mg/dL (+2.0 mmol/L) | 72.5% | 0.0% | 0 |

No change suggested: already meets both goals.

### 5. SMB limit

Judged on the whole period: 336.0 h of readings, observed 86.6% in range and 2.4% below.
Run with basal rates -20%, ISF +30%.

| Maximum SMB basal minutes | Average glucose change | In range | Below range | Low episodes |
|---|---|---|---|---|
| 15 min | +20 mg/dL (+1.1 mmol/L) | 80.7% | 0.3% | 1 |
| 30 min | +19 mg/dL (+1.0 mmol/L) | 81.7% | 0.3% | 1 |
| 45 min | +18 mg/dL (+1.0 mmol/L) | 81.9% | 0.3% | 1 |
| 60 min | +18 mg/dL (+1.0 mmol/L) | 82.1% | 0.3% | 1 |
| 75 min (current) ← | +18 mg/dL (+1.0 mmol/L) | 82.0% | 0.3% | 1 |
| 90 min | +18 mg/dL (+1.0 mmol/L) | 82.0% | 0.3% | 1 |

No change suggested: already meets both goals.

### 6. Max IOB

Judged on the whole period: 336.0 h of readings, observed 86.6% in range and 2.4% below.
Run with basal rates -20%, ISF +30%.

| Max IOB | Average glucose change | In range | Below range | Low episodes |
|---|---|---|---|---|
| 4.8 U | +19 mg/dL (+1.1 mmol/L) | 81.2% | 0.2% | 1 |
| 5.5 U | +19 mg/dL (+1.0 mmol/L) | 81.6% | 0.2% | 1 |
| 6.2 U | +18 mg/dL (+1.0 mmol/L) | 81.8% | 0.2% | 1 |
| 6.9 U ← | +18 mg/dL (+1.0 mmol/L) | 82.1% | 0.3% | 1 |
| 7.6 U | +18 mg/dL (+1.0 mmol/L) | 81.9% | 0.3% | 1 |
| 8.3 U | +18 mg/dL (+1.0 mmol/L) | 81.8% | 0.4% | 1 |
| 9 U | +18 mg/dL (+1.0 mmol/L) | 81.8% | 0.4% | 1 |

Trial to consider: max IOB 6.9 U, because the smallest change that meets both goals.

### Together

With basal rates -20%, ISF +30%, max IOB 6.9 U: estimated 82.1% in range and 0.3% below (observed 86.6% and 2.4%), average glucose +18 mg/dL (+1.0 mmol/L). That meets both goals.

Change one setting at a time and give each a few days before the next, so its effect can be seen on its own.