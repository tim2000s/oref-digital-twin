# oref digital twin — report

Findings: 0 critical, 1 to watch, 4 notes.

## Your setup

- Detected: **unknown** (confidence 0.0)
- The controller could not be classified — findings only.

## Glucose

- Readings: 4032 over ~14.0 days
- Mean: 136.5 mg/dL (7.6 mmol/L), GMI 6.6%
- Time in range (70–180): 81.6%
- Time below 70: 3.0%; below 54: 0.8%
- Time above 180: 15.4%; above 250: 1.8%
- Variability (CV): 31.3%

## Findings

### Worth attention

- **Nocturnal hypoglycaemia episodes** — 5 overnight (00:00-06:00) low episode(s) below 70 mg/dL across 5 night(s). Overnight lows are the domain's repeated risk; cross-check against overnight SMBs and IOB.

### Notes

- **Meets consensus glycaemic targets** — TIR 81.6%, TBR<70 3.0%, TBR<54 0.8% — within consensus targets over this window.
- **Estimated daily insulin** — ~85.7 U/day estimated (profile basal ~37.41 U + bolus/SMB ~48.3 U/day). Rough: basal is the scheduled profile, not delivered basal, and temp basals are not integrated.
- **Overnight SMBs at high IOB, with lows following** — 103 of 342 overnight SMBs fired at high IOB (>= p75 3.02 U); 0 (0.0%) were followed by BG < 70 mg/dL within 2h. Association only — this names the pattern, it does not prove the SMB caused the low.
- **30-min IOB prediction bias -9.6 mg/dL** — Over 4027 cycles the IOB-only prediction ran 9.6 mg/dL lower than realised on average (MAE 18.8). A large systematic bias points at model calibration; it is descriptive, not a dosing instruction.


---

_This is decision-support, not medical advice, and it is advisory-only — it never changes your loop or pump. Discuss any change with your clinician and trial it deliberately._

## Settings tests (estimated)

Goal: time in range above 70% and time below range under 2%. Observed over 14.0 days: 81.6% in range, 3.0% below, 10 low episodes.

Each setting is stepped from −30% to +30% and the loop is re-run through every 5-minute cycle (4032) under each value. Basal is tested first, on fasting stretches; ISF next, on correction stretches; then carb ratio on meals; then target, the SMB limit and max IOB over the whole period. Each stage keeps the choices before it.

_Estimated, not measured: each value's glucose is your CGM shifted by the change in insulin the loop would have given, times your profile ISF, with the loop reacting to the shifted glucose at every step. It assumes your meals, activity and own treatments would have been the same, and that your profile ISF is your real sensitivity. Treat any change as a trial to test, one setting at a time._

_Your loop was detected as unknown. These tests run stock oref0, so anything your variant adds on top of it is not modelled._

Insulin curve: rapid-acting (settings).

### 1. Basal

Judged on fasting stretches (no carbs or meal-sized rise in the last 4 h, nothing above 180 mg/dL in the last 3 h): 103.8 h of readings, observed 98.0% in range and 2.0% below.

| Basal rates | Average glucose change | In range (fasting) | Below range (fasting) | Low episodes | In range (all) | Below range (all) |
|---|---|---|---|---|---|---|
| -30% | +16 mg/dL (+0.9 mmol/L) | 99.4% | 0.5% | 0 | 76.9% | 0.8% |
| -20% | +10 mg/dL (+0.6 mmol/L) | 99.2% | 0.8% | 0 | 78.2% | 1.3% |
| -10% ← | +5 mg/dL (+0.3 mmol/L) | 98.6% | 1.4% | 3 | 80.0% | 2.1% |
| current | +0 mg/dL (+0.0 mmol/L) | 98.0% | 2.0% | 3 | 81.6% | 3.0% |
| +10% | -5 mg/dL (-0.3 mmol/L) | 96.6% | 3.4% | 4 | 82.7% | 4.2% |
| +20% | -10 mg/dL (-0.6 mmol/L) | 94.8% | 5.2% | 6 | 83.3% | 5.5% |
| +30% | -16 mg/dL (-0.9 mmol/L) | 93.3% | 6.7% | 9 | 83.2% | 7.3% |

Trial to consider: basal rates -10%, because the smallest change that meets both goals.

### 2. ISF

Judged on correction stretches (above 180 mg/dL in the last 3 h, outside meals): 19.0 h of readings, observed 45.6% in range and 8.8% below.
Run with basal rates -10%.

| ISF | Average glucose change | In range (correction) | Below range (correction) | Low episodes | In range (all) | Below range (all) |
|---|---|---|---|---|---|---|
| -30% | -11 mg/dL (-0.6 mmol/L) | 65.4% | 17.5% | 4 | 83.1% | 7.0% |
| -20% | -5 mg/dL (-0.3 mmol/L) | 56.6% | 12.3% | 3 | 83.2% | 4.4% |
| -10% | +0 mg/dL (+0.0 mmol/L) | 49.1% | 9.2% | 3 | 81.7% | 3.2% |
| current | +5 mg/dL (+0.3 mmol/L) | 39.9% | 7.9% | 2 | 80.0% | 2.1% |
| +10% | +10 mg/dL (+0.5 mmol/L) | 40.8% | 4.8% | 1 | 78.6% | 1.1% |
| +20% | +14 mg/dL (+0.8 mmol/L) | 42.5% | 3.1% | 1 | 77.6% | 0.4% |
| +30% ← | +18 mg/dL (+1.0 mmol/L) | 43.9% | 1.8% | 1 | 76.2% | 0.2% |

Trial to consider: ISF +30%, because no value reaches 70% in range; this keeps lows under 2% with the most time in range.

### 3. Carb ratio

Judged on meal stretches (the 4 h after logged carbs or a meal-sized rise): 213.2 h of readings, observed 76.9% in range and 2.9% below.
Run with basal rates -10%, ISF +30%.
Logged meal boluses are scaled with the ratio, as the bolus wizard would.

| Carb ratio | Average glucose change | In range (meal) | Below range (meal) | Low episodes | In range (all) | Below range (all) |
|---|---|---|---|---|---|---|
| -30% ← | +17 mg/dL (+0.9 mmol/L) | 68.3% | 0.0% | 0 | 76.5% | 0.3% |
| -20% | +17 mg/dL (+1.0 mmol/L) | 68.2% | 0.0% | 0 | 76.4% | 0.2% |
| -10% | +17 mg/dL (+1.0 mmol/L) | 68.1% | 0.0% | 0 | 76.4% | 0.3% |
| current | +18 mg/dL (+1.0 mmol/L) | 67.7% | 0.0% | 0 | 76.2% | 0.2% |
| +10% | +18 mg/dL (+1.0 mmol/L) | 67.4% | 0.0% | 0 | 76.0% | 0.2% |
| +20% | +18 mg/dL (+1.0 mmol/L) | 67.3% | 0.0% | 0 | 75.9% | 0.2% |
| +30% | +19 mg/dL (+1.0 mmol/L) | 66.9% | 0.0% | 0 | 75.6% | 0.2% |

Trial to consider: carb ratio -30%, because no value reaches 70% in range; this keeps lows under 2% with the most time in range.

### 4. Target

Judged on the whole period: 336.0 h of readings, observed 81.6% in range and 3.0% below.
Run with basal rates -10%, ISF +30%, carb ratio -30%.

| Target | Average glucose change | In range | Below range | Low episodes |
|---|---|---|---|---|
| -1.0 mmol/L (-18 mg/dL) on every target: 92 mg/dL (5.1 mmol/L) | -1 mg/dL (-0.1 mmol/L) | 81.2% | 2.7% | 12 |
| -0.5 mmol/L (-9 mg/dL) on every target: 101 mg/dL (5.6 mmol/L) | +8 mg/dL (+0.4 mmol/L) | 79.5% | 0.9% | 4 |
| 110 mg/dL (6.1 mmol/L) (current) ← | +17 mg/dL (+0.9 mmol/L) | 76.5% | 0.3% | 1 |
| +0.5 mmol/L (+9 mg/dL) on every target: 119 mg/dL (6.6 mmol/L) | +26 mg/dL (+1.4 mmol/L) | 73.1% | 0.0% | 0 |
| +1.0 mmol/L (+18 mg/dL) on every target: 128 mg/dL (7.1 mmol/L) | +35 mg/dL (+1.9 mmol/L) | 67.4% | 0.0% | 0 |

No change suggested: already meets both goals.

### 5. SMB limit

Judged on the whole period: 336.0 h of readings, observed 81.6% in range and 3.0% below.
Run with basal rates -10%, ISF +30%, carb ratio -30%.

| Maximum SMB basal minutes | Average glucose change | In range | Below range | Low episodes |
|---|---|---|---|---|
| 15 min | +18 mg/dL (+1.0 mmol/L) | 76.4% | 0.2% | 1 |
| 30 min | +17 mg/dL (+1.0 mmol/L) | 76.5% | 0.3% | 1 |
| 45 min | +17 mg/dL (+0.9 mmol/L) | 76.5% | 0.3% | 1 |
| 60 min | +17 mg/dL (+0.9 mmol/L) | 76.5% | 0.3% | 1 |
| 75 min (current) ← | +17 mg/dL (+0.9 mmol/L) | 76.5% | 0.3% | 1 |
| 90 min | +17 mg/dL (+0.9 mmol/L) | 76.5% | 0.3% | 1 |

No change suggested: already meets both goals.

### 6. Max IOB

Judged on the whole period: 336.0 h of readings, observed 81.6% in range and 3.0% below.
Run with basal rates -10%, ISF +30%, carb ratio -30%.

| Max IOB | Average glucose change | In range | Below range | Low episodes |
|---|---|---|---|---|
| 7.9 U | +15 mg/dL (+0.8 mmol/L) | 76.5% | 1.1% | 4 |
| 9 U | +16 mg/dL (+0.9 mmol/L) | 76.3% | 0.8% | 3 |
| 10.1 U | +17 mg/dL (+0.9 mmol/L) | 76.3% | 0.5% | 2 |
| 11.2 U ← | +17 mg/dL (+0.9 mmol/L) | 76.5% | 0.3% | 1 |
| 12.3 U | +17 mg/dL (+0.9 mmol/L) | 76.6% | 0.3% | 1 |
| 13.5 U | +17 mg/dL (+0.9 mmol/L) | 76.6% | 0.3% | 1 |
| 14.6 U | +17 mg/dL (+0.9 mmol/L) | 76.6% | 0.3% | 1 |

Trial to consider: max IOB 11.2 U, because the smallest change that meets both goals.

### Together

With basal rates -10%, ISF +30%, carb ratio -30%, max IOB 11.2 U: estimated 76.5% in range and 0.3% below (observed 81.6% and 3.0%), average glucose +17 mg/dL (+0.9 mmol/L). That meets both goals.

Change one setting at a time and give each a few days before the next, so its effect can be seen on its own.