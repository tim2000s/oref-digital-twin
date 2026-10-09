# oref digital twin — report

Findings: 0 critical, 1 to watch, 4 notes.

## Your setup

- Detected: **unknown** (confidence 0.0)
- The controller could not be classified — findings only.

## Glucose

- Readings: 4032 over ~14.0 days
- Mean: 143.3 mg/dL (8.0 mmol/L), GMI 6.7%
- Time in range (70–180): 81.3%
- Time below 70: 1.6%; below 54: 0.2%
- Time above 180: 17.1%; above 250: 2.0%
- Variability (CV): 30.7%

## Findings

### Worth attention

- **Nocturnal hypoglycaemia episodes** — 4 overnight (00:00-06:00) low episode(s) below 70 mg/dL across 3 night(s). Overnight lows are the domain's repeated risk; cross-check against overnight SMBs and IOB.

### Notes

- **Meets consensus glycaemic targets** — TIR 81.3%, TBR<70 1.6%, TBR<54 0.2% — within consensus targets over this window.
- **Estimated daily insulin** — ~70.0 U/day estimated (profile basal ~23.96 U + bolus/SMB ~46.0 U/day). Rough: basal is the scheduled profile, not delivered basal, and temp basals are not integrated.
- **Overnight SMBs at high IOB, with lows following** — 129 of 360 overnight SMBs fired at high IOB (>= p75 4.21 U); 0 (0.0%) were followed by BG < 70 mg/dL within 2h. Association only — this names the pattern, it does not prove the SMB caused the low.
- **30-min IOB prediction bias -9.0 mg/dL** — Over 4027 cycles the IOB-only prediction ran 9.0 mg/dL lower than realised on average (MAE 18.1). A large systematic bias points at model calibration; it is descriptive, not a dosing instruction.


---

_This is decision-support, not medical advice, and it is advisory-only — it never changes your loop or pump. Discuss any change with your clinician and trial it deliberately._

## Settings tests (estimated)

Goal: time in range above 70% and time below range under 2%. Observed over 14.0 days: 81.3% in range, 1.6% below, 8 low episodes.

Each setting is stepped from −30% to +30% and the loop is re-run through every 5-minute cycle (4032) under each value. Basal is tested first, on fasting stretches; ISF next, on correction stretches; then carb ratio on meals; then target, the SMB limit and max IOB over the whole period. Each stage keeps the choices before it.

_Estimated, not measured: each value's glucose is your CGM shifted by the change in insulin the loop would have given, times your profile ISF, with the loop reacting to the shifted glucose at every step. It assumes your meals, activity and own treatments would have been the same, and that your profile ISF is your real sensitivity. Treat any change as a trial to test, one setting at a time._

_Your loop was detected as unknown. These tests run stock oref0, so anything your variant adds on top of it is not modelled._

Insulin curve: rapid-acting (settings).

### 1. Basal

Judged on fasting stretches (no carbs or meal-sized rise in the last 4 h, nothing above 180 mg/dL in the last 3 h): 72.8 h of readings, observed 98.6% in range and 1.4% below.

| Basal rates | Average glucose change | In range (fasting) | Below range (fasting) | Low episodes | In range (all) | Below range (all) |
|---|---|---|---|---|---|---|
| -30% | +9 mg/dL (+0.5 mmol/L) | 99.7% | 0.3% | 0 | 77.9% | 0.6% |
| -20% | +6 mg/dL (+0.3 mmol/L) | 99.5% | 0.5% | 0 | 79.5% | 0.8% |
| -10% | +3 mg/dL (+0.2 mmol/L) | 99.3% | 0.7% | 0 | 80.5% | 1.1% |
| current ← | +0 mg/dL (+0.0 mmol/L) | 98.6% | 1.4% | 1 | 81.3% | 1.6% |
| +10% | -3 mg/dL (-0.2 mmol/L) | 97.8% | 2.2% | 2 | 81.7% | 2.2% |
| +20% | -6 mg/dL (-0.3 mmol/L) | 96.2% | 3.8% | 5 | 82.5% | 3.0% |
| +30% | -9 mg/dL (-0.5 mmol/L) | 94.4% | 5.6% | 7 | 82.8% | 4.0% |

No change suggested: already meets both goals.

### 2. ISF

Judged on correction stretches (above 180 mg/dL in the last 3 h, outside meals): 25.2 h of readings, observed 92.1% in range and 6.3% below.

| ISF | Average glucose change | In range (correction) | Below range (correction) | Low episodes | In range (all) | Below range (all) |
|---|---|---|---|---|---|---|
| -30% | -12 mg/dL (-0.7 mmol/L) | 77.2% | 22.5% | 7 | 81.2% | 6.4% |
| -20% | -8 mg/dL (-0.4 mmol/L) | 85.8% | 13.9% | 4 | 81.8% | 4.2% |
| -10% | -4 mg/dL (-0.2 mmol/L) | 90.7% | 8.3% | 2 | 81.2% | 2.7% |
| current | +0 mg/dL (+0.0 mmol/L) | 92.1% | 6.3% | 2 | 81.3% | 1.6% |
| +10% | +3 mg/dL (+0.2 mmol/L) | 94.7% | 2.6% | 1 | 80.6% | 1.0% |
| +20% ← | +7 mg/dL (+0.4 mmol/L) | 93.7% | 0.7% | 0 | 79.3% | 0.6% |
| +30% | +11 mg/dL (+0.6 mmol/L) | 94.4% | 0.0% | 0 | 78.2% | 0.3% |

Trial to consider: ISF +20%, because the smallest change that meets both goals.

### 3. Carb ratio

Judged on meal stretches (the 4 h after logged carbs or a meal-sized rise): 238.1 h of readings, observed 74.9% in range and 1.2% below.
Run with ISF +20%.
Logged meal boluses are scaled with the ratio, as the bolus wizard would.

| Carb ratio | Average glucose change | In range (meal) | Below range (meal) | Low episodes | In range (all) | Below range (all) |
|---|---|---|---|---|---|---|
| -30% | +7 mg/dL (+0.4 mmol/L) | 72.0% | 0.7% | 2 | 79.6% | 0.7% |
| -20% | +7 mg/dL (+0.4 mmol/L) | 71.9% | 0.7% | 2 | 79.4% | 0.7% |
| -10% | +7 mg/dL (+0.4 mmol/L) | 71.6% | 0.7% | 2 | 79.3% | 0.7% |
| current ← | +7 mg/dL (+0.4 mmol/L) | 71.5% | 0.7% | 2 | 79.3% | 0.6% |
| +10% | +8 mg/dL (+0.4 mmol/L) | 71.3% | 0.7% | 2 | 79.1% | 0.6% |
| +20% | +8 mg/dL (+0.4 mmol/L) | 71.1% | 0.7% | 2 | 79.0% | 0.6% |
| +30% | +8 mg/dL (+0.5 mmol/L) | 70.9% | 0.7% | 2 | 78.9% | 0.5% |

No change suggested: already meets both goals.

### 4. Target

Judged on the whole period: 336.0 h of readings, observed 81.3% in range and 1.6% below.
Run with ISF +20%.

| Target | Average glucose change | In range | Below range | Low episodes |
|---|---|---|---|---|
| -1.0 mmol/L (-18 mg/dL) on every target: 92 mg/dL (5.1 mmol/L) | -10 mg/dL (-0.6 mmol/L) | 83.2% | 4.3% | 19 |
| -0.5 mmol/L (-9 mg/dL) on every target: 101 mg/dL (5.6 mmol/L) | -2 mg/dL (-0.1 mmol/L) | 81.8% | 1.6% | 7 |
| 110 mg/dL (6.1 mmol/L) (current) ← | +7 mg/dL (+0.4 mmol/L) | 79.3% | 0.6% | 2 |
| +0.5 mmol/L (+9 mg/dL) on every target: 119 mg/dL (6.6 mmol/L) | +16 mg/dL (+0.9 mmol/L) | 74.2% | 0.1% | 0 |
| +1.0 mmol/L (+18 mg/dL) on every target: 128 mg/dL (7.1 mmol/L) | +25 mg/dL (+1.4 mmol/L) | 67.2% | 0.0% | 0 |

No change suggested: already meets both goals.

### 5. SMB limit

Judged on the whole period: 336.0 h of readings, observed 81.3% in range and 1.6% below.
Run with ISF +20%.

| Maximum SMB basal minutes | Average glucose change | In range | Below range | Low episodes |
|---|---|---|---|---|
| 15 min | +10 mg/dL (+0.5 mmol/L) | 78.4% | 0.5% | 2 |
| 30 min | +8 mg/dL (+0.4 mmol/L) | 79.2% | 0.6% | 2 |
| 45 min | +7 mg/dL (+0.4 mmol/L) | 79.3% | 0.6% | 2 |
| 60 min | +7 mg/dL (+0.4 mmol/L) | 79.3% | 0.6% | 2 |
| 75 min (current) ← | +7 mg/dL (+0.4 mmol/L) | 79.2% | 0.6% | 2 |
| 90 min | +7 mg/dL (+0.4 mmol/L) | 79.2% | 0.6% | 2 |

No change suggested: already meets both goals.

### 6. Max IOB

Judged on the whole period: 336.0 h of readings, observed 81.3% in range and 1.6% below.
Run with ISF +20%.

| Max IOB | Average glucose change | In range | Below range | Low episodes |
|---|---|---|---|---|
| 5 U | +11 mg/dL (+0.6 mmol/L) | 76.7% | 0.3% | 1 |
| 5.8 U | +10 mg/dL (+0.5 mmol/L) | 78.1% | 0.4% | 1 |
| 6.5 U | +8 mg/dL (+0.5 mmol/L) | 78.6% | 0.5% | 2 |
| 7.2 U ← | +7 mg/dL (+0.4 mmol/L) | 79.3% | 0.6% | 2 |
| 7.9 U | +6 mg/dL (+0.4 mmol/L) | 79.6% | 0.8% | 2 |
| 8.6 U | +6 mg/dL (+0.3 mmol/L) | 79.6% | 0.8% | 2 |
| 9.3 U | +6 mg/dL (+0.3 mmol/L) | 79.7% | 0.8% | 2 |

Trial to consider: max IOB 7.2 U, because the smallest change that meets both goals.

### Together

With ISF +20%, max IOB 7.2 U: estimated 79.3% in range and 0.6% below (observed 81.3% and 1.6%), average glucose +7 mg/dL (+0.4 mmol/L). That meets both goals.

Change one setting at a time and give each a few days before the next, so its effect can be seen on its own.