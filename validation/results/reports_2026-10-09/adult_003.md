# oref digital twin — report

Findings: 0 critical, 0 to watch, 4 notes.

## Your setup

- Detected: **unknown** (confidence 0.0)
- The controller could not be classified — findings only.

## Glucose

- Readings: 4032 over ~14.0 days
- Mean: 141.0 mg/dL (7.8 mmol/L), GMI 6.7%
- Time in range (70–180): 87.9%
- Time below 70: 0.6%; below 54: 0.2%
- Time above 180: 11.4%; above 250: 1.3%
- Variability (CV): 25.0%

## Findings

### Notes

- **Meets consensus glycaemic targets** — TIR 87.9%, TBR<70 0.6%, TBR<54 0.2% — within consensus targets over this window.
- **Estimated daily insulin** — ~83.1 U/day estimated (profile basal ~33.74 U + bolus/SMB ~49.4 U/day). Rough: basal is the scheduled profile, not delivered basal, and temp basals are not integrated.
- **Overnight SMBs at high IOB, with lows following** — 88 of 304 overnight SMBs fired at high IOB (>= p75 3.42 U); 0 (0.0%) were followed by BG < 70 mg/dL within 2h. Association only — this names the pattern, it does not prove the SMB caused the low.
- **30-min IOB prediction bias -10.6 mg/dL** — Over 4027 cycles the IOB-only prediction ran 10.6 mg/dL lower than realised on average (MAE 18.9). A large systematic bias points at model calibration; it is descriptive, not a dosing instruction.


---

_This is decision-support, not medical advice, and it is advisory-only — it never changes your loop or pump. Discuss any change with your clinician and trial it deliberately._

## Settings tests (estimated)

Goal: time in range above 70% and time below range under 2%. Observed over 14.0 days: 87.9% in range, 0.6% below, 1 low episodes.

Each setting is stepped from −30% to +30% and the loop is re-run through every 5-minute cycle (4032) under each value. Basal is tested first, on fasting stretches; ISF next, on correction stretches; then carb ratio on meals; then target, the SMB limit and max IOB over the whole period. Each stage keeps the choices before it.

_Estimated, not measured: each value's glucose is your CGM shifted by the change in insulin the loop would have given, times your profile ISF, with the loop reacting to the shifted glucose at every step. It assumes your meals, activity and own treatments would have been the same, and that your profile ISF is your real sensitivity. Treat any change as a trial to test, one setting at a time._

_Your loop was detected as unknown. These tests run stock oref0, so anything your variant adds on top of it is not modelled._

Insulin curve: rapid-acting (settings).

### 1. Basal

Judged on fasting stretches (no carbs or meal-sized rise in the last 4 h, nothing above 180 mg/dL in the last 3 h): 100.1 h of readings, observed 100.0% in range and 0.0% below.

| Basal rates | Average glucose change | In range (fasting) | Below range (fasting) | Low episodes | In range (all) | Below range (all) |
|---|---|---|---|---|---|---|
| -30% | +12 mg/dL (+0.7 mmol/L) | 98.0% | 0.0% | 0 | 80.5% | 0.3% |
| -20% | +8 mg/dL (+0.5 mmol/L) | 99.0% | 0.0% | 0 | 83.0% | 0.4% |
| -10% | +4 mg/dL (+0.2 mmol/L) | 99.4% | 0.0% | 0 | 85.4% | 0.5% |
| current ← | +0 mg/dL (+0.0 mmol/L) | 100.0% | 0.0% | 0 | 87.9% | 0.6% |
| +10% | -4 mg/dL (-0.2 mmol/L) | 99.9% | 0.1% | 0 | 89.0% | 1.0% |
| +20% | -8 mg/dL (-0.5 mmol/L) | 99.8% | 0.2% | 0 | 90.4% | 1.5% |
| +30% | -13 mg/dL (-0.7 mmol/L) | 99.4% | 0.6% | 1 | 91.0% | 2.2% |

No change suggested: already meets both goals.

### 2. ISF

Judged on correction stretches (above 180 mg/dL in the last 3 h, outside meals): 23.8 h of readings, observed 88.4% in range and 3.5% below.

| ISF | Average glucose change | In range (correction) | Below range (correction) | Low episodes | In range (all) | Below range (all) |
|---|---|---|---|---|---|---|
| -30% | -15 mg/dL (-0.8 mmol/L) | 85.3% | 14.7% | 5 | 90.0% | 4.0% |
| -20% | -9 mg/dL (-0.5 mmol/L) | 84.9% | 13.0% | 4 | 89.3% | 2.8% |
| -10% | -5 mg/dL (-0.3 mmol/L) | 88.4% | 7.0% | 3 | 89.1% | 1.3% |
| current | +0 mg/dL (+0.0 mmol/L) | 88.4% | 3.5% | 1 | 87.9% | 0.6% |
| +10% ← | +4 mg/dL (+0.2 mmol/L) | 84.6% | 0.7% | 0 | 85.2% | 0.4% |
| +20% | +8 mg/dL (+0.4 mmol/L) | 80.7% | 0.0% | 0 | 83.1% | 0.2% |
| +30% | +12 mg/dL (+0.6 mmol/L) | 75.1% | 0.0% | 0 | 80.5% | 0.0% |

Trial to consider: ISF +10%, because the smallest change that meets both goals.

### 3. Carb ratio

Judged on meal stretches (the 4 h after logged carbs or a meal-sized rise): 212.2 h of readings, observed 82.2% in range and 0.6% below.
Run with ISF +10%.
Logged meal boluses are scaled with the ratio, as the bolus wizard would.

| Carb ratio | Average glucose change | In range (meal) | Below range (meal) | Low episodes | In range (all) | Below range (all) |
|---|---|---|---|---|---|---|
| -30% | +2 mg/dL (+0.1 mmol/L) | 79.3% | 0.6% | 1 | 85.7% | 0.6% |
| -20% | +3 mg/dL (+0.2 mmol/L) | 79.1% | 0.6% | 1 | 85.6% | 0.5% |
| -10% | +4 mg/dL (+0.2 mmol/L) | 78.9% | 0.6% | 1 | 85.4% | 0.4% |
| current ← | +4 mg/dL (+0.2 mmol/L) | 78.6% | 0.5% | 1 | 85.2% | 0.4% |
| +10% | +4 mg/dL (+0.2 mmol/L) | 78.2% | 0.5% | 1 | 84.9% | 0.3% |
| +20% | +5 mg/dL (+0.3 mmol/L) | 78.1% | 0.5% | 1 | 84.9% | 0.3% |
| +30% | +5 mg/dL (+0.3 mmol/L) | 77.8% | 0.5% | 1 | 84.5% | 0.3% |

No change suggested: already meets both goals.

### 4. Target

Judged on the whole period: 336.0 h of readings, observed 87.9% in range and 0.6% below.
Run with ISF +10%.

| Target | Average glucose change | In range | Below range | Low episodes |
|---|---|---|---|---|
| -1.0 mmol/L (-18 mg/dL) on every target: 92 mg/dL (5.1 mmol/L) | -14 mg/dL (-0.8 mmol/L) | 91.8% | 1.9% | 7 |
| -0.5 mmol/L (-9 mg/dL) on every target: 101 mg/dL (5.6 mmol/L) | -5 mg/dL (-0.3 mmol/L) | 89.3% | 0.9% | 3 |
| 110 mg/dL (6.1 mmol/L) (current) ← | +4 mg/dL (+0.2 mmol/L) | 85.2% | 0.4% | 1 |
| +0.5 mmol/L (+9 mg/dL) on every target: 119 mg/dL (6.6 mmol/L) | +13 mg/dL (+0.7 mmol/L) | 80.2% | 0.2% | 1 |
| +1.0 mmol/L (+18 mg/dL) on every target: 128 mg/dL (7.1 mmol/L) | +22 mg/dL (+1.2 mmol/L) | 73.0% | 0.0% | 0 |

No change suggested: already meets both goals.

### 5. SMB limit

Judged on the whole period: 336.0 h of readings, observed 87.9% in range and 0.6% below.
Run with ISF +10%.

| Maximum SMB basal minutes | Average glucose change | In range | Below range | Low episodes |
|---|---|---|---|---|
| 15 min | +4 mg/dL (+0.2 mmol/L) | 85.1% | 0.3% | 1 |
| 30 min | +4 mg/dL (+0.2 mmol/L) | 85.4% | 0.4% | 1 |
| 45 min | +4 mg/dL (+0.2 mmol/L) | 85.2% | 0.4% | 1 |
| 60 min | +4 mg/dL (+0.2 mmol/L) | 85.2% | 0.4% | 1 |
| 75 min (current) ← | +4 mg/dL (+0.2 mmol/L) | 85.2% | 0.4% | 1 |
| 90 min | +4 mg/dL (+0.2 mmol/L) | 85.2% | 0.4% | 1 |

No change suggested: already meets both goals.

### 6. Max IOB

Judged on the whole period: 336.0 h of readings, observed 87.9% in range and 0.6% below.
Run with ISF +10%.

| Max IOB | Average glucose change | In range | Below range | Low episodes |
|---|---|---|---|---|
| 7.1 U | +3 mg/dL (+0.2 mmol/L) | 85.4% | 0.6% | 2 |
| 8.1 U | +3 mg/dL (+0.2 mmol/L) | 85.5% | 0.4% | 2 |
| 9.1 U | +4 mg/dL (+0.2 mmol/L) | 85.5% | 0.4% | 1 |
| 10.1 U ← | +4 mg/dL (+0.2 mmol/L) | 85.3% | 0.4% | 1 |
| 11.1 U | +4 mg/dL (+0.2 mmol/L) | 85.2% | 0.4% | 1 |
| 12.1 U | +4 mg/dL (+0.2 mmol/L) | 85.2% | 0.4% | 1 |
| 13.2 U | +4 mg/dL (+0.2 mmol/L) | 85.2% | 0.4% | 1 |

Trial to consider: max IOB 10.1 U, because the smallest change that meets both goals.

### Together

With ISF +10%, max IOB 10.1 U: estimated 85.3% in range and 0.4% below (observed 87.9% and 0.6%), average glucose +4 mg/dL (+0.2 mmol/L). That meets both goals.

Change one setting at a time and give each a few days before the next, so its effect can be seen on its own.