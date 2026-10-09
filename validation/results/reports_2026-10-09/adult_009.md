# oref digital twin — report

Findings: 0 critical, 1 to watch, 4 notes.

## Your setup

- Detected: **unknown** (confidence 0.0)
- The controller could not be classified — findings only.

## Glucose

- Readings: 4032 over ~14.0 days
- Mean: 137.2 mg/dL (7.6 mmol/L), GMI 6.6%
- Time in range (70–180): 89.3%
- Time below 70: 0.3%; below 54: 0.0%
- Time above 180: 10.4%; above 250: 0.9%
- Variability (CV): 24.6%

## Findings

### Worth attention

- **Nocturnal hypoglycaemia episodes** — 1 overnight (00:00-06:00) low episode(s) below 70 mg/dL across 1 night(s). Overnight lows are the domain's repeated risk; cross-check against overnight SMBs and IOB.

### Notes

- **Meets consensus glycaemic targets** — TIR 89.3%, TBR<70 0.3%, TBR<54 0.0% — within consensus targets over this window.
- **Estimated daily insulin** — ~63.1 U/day estimated (profile basal ~25.89 U + bolus/SMB ~37.2 U/day). Rough: basal is the scheduled profile, not delivered basal, and temp basals are not integrated.
- **Overnight SMBs at high IOB, with lows following** — 79 of 347 overnight SMBs fired at high IOB (>= p75 2.8 U); 0 (0.0%) were followed by BG < 70 mg/dL within 2h. Association only — this names the pattern, it does not prove the SMB caused the low.
- **30-min IOB prediction bias -9.1 mg/dL** — Over 4027 cycles the IOB-only prediction ran 9.1 mg/dL lower than realised on average (MAE 17.5). A large systematic bias points at model calibration; it is descriptive, not a dosing instruction.


---

_This is decision-support, not medical advice, and it is advisory-only — it never changes your loop or pump. Discuss any change with your clinician and trial it deliberately._

## Settings tests (estimated)

Goal: time in range above 70% and time below range under 2%. Observed over 14.0 days: 89.3% in range, 0.3% below, 1 low episodes.

Each setting is stepped from −30% to +30% and the loop is re-run through every 5-minute cycle (4032) under each value. Basal is tested first, on fasting stretches; ISF next, on correction stretches; then carb ratio on meals; then target, the SMB limit and max IOB over the whole period. Each stage keeps the choices before it.

_Estimated, not measured: each value's glucose is your CGM shifted by the change in insulin the loop would have given, times your profile ISF, with the loop reacting to the shifted glucose at every step. It assumes your meals, activity and own treatments would have been the same, and that your profile ISF is your real sensitivity. Treat any change as a trial to test, one setting at a time._

_Your loop was detected as unknown. These tests run stock oref0, so anything your variant adds on top of it is not modelled._

Insulin curve: rapid-acting (settings).

### 1. Basal

Judged on fasting stretches (no carbs or meal-sized rise in the last 4 h, nothing above 180 mg/dL in the last 3 h): 102.2 h of readings, observed 99.2% in range and 0.8% below.

| Basal rates | Average glucose change | In range (fasting) | Below range (fasting) | Low episodes | In range (all) | Below range (all) |
|---|---|---|---|---|---|---|
| -30% | +12 mg/dL (+0.7 mmol/L) | 99.0% | 0.2% | 0 | 83.8% | 0.0% |
| -20% | +8 mg/dL (+0.4 mmol/L) | 99.1% | 0.3% | 0 | 86.0% | 0.1% |
| -10% | +4 mg/dL (+0.2 mmol/L) | 99.2% | 0.5% | 0 | 87.6% | 0.1% |
| current ← | +0 mg/dL (+0.0 mmol/L) | 99.2% | 0.8% | 1 | 89.3% | 0.3% |
| +10% | -4 mg/dL (-0.2 mmol/L) | 98.7% | 1.3% | 2 | 90.5% | 0.5% |
| +20% | -8 mg/dL (-0.4 mmol/L) | 98.1% | 1.9% | 3 | 91.2% | 0.9% |
| +30% | -12 mg/dL (-0.7 mmol/L) | 97.1% | 2.9% | 3 | 91.5% | 1.6% |

No change suggested: already meets both goals.

### 2. ISF

Judged on correction stretches (above 180 mg/dL in the last 3 h, outside meals): 20.9 h of readings, observed 98.4% in range and 0.0% below.

| ISF | Average glucose change | In range (correction) | Below range (correction) | Low episodes | In range (all) | Below range (all) |
|---|---|---|---|---|---|---|
| -30% | -13 mg/dL (-0.7 mmol/L) | 94.0% | 6.0% | 2 | 91.0% | 2.6% |
| -20% | -8 mg/dL (-0.4 mmol/L) | 97.2% | 2.8% | 1 | 91.6% | 0.9% |
| -10% | -4 mg/dL (-0.2 mmol/L) | 98.4% | 1.2% | 0 | 90.5% | 0.5% |
| current ← | +0 mg/dL (+0.0 mmol/L) | 98.4% | 0.0% | 0 | 89.3% | 0.3% |
| +10% | +3 mg/dL (+0.2 mmol/L) | 94.0% | 0.0% | 0 | 87.3% | 0.2% |
| +20% | +7 mg/dL (+0.4 mmol/L) | 92.8% | 0.0% | 0 | 86.0% | 0.1% |
| +30% | +10 mg/dL (+0.6 mmol/L) | 89.2% | 0.0% | 0 | 83.6% | 0.1% |

No change suggested: already meets both goals.

### 3. Carb ratio

Judged on meal stretches (the 4 h after logged carbs or a meal-sized rise): 212.8 h of readings, observed 83.6% in range and 0.0% below.
Logged meal boluses are scaled with the ratio, as the bolus wizard would.

| Carb ratio | Average glucose change | In range (meal) | Below range (meal) | Low episodes | In range (all) | Below range (all) |
|---|---|---|---|---|---|---|
| -30% | -2 mg/dL (-0.1 mmol/L) | 84.8% | 0.1% | 0 | 90.0% | 0.3% |
| -20% | -1 mg/dL (-0.1 mmol/L) | 84.1% | 0.1% | 0 | 89.6% | 0.3% |
| -10% | -1 mg/dL (-0.0 mmol/L) | 83.9% | 0.1% | 0 | 89.4% | 0.3% |
| current ← | +0 mg/dL (+0.0 mmol/L) | 83.6% | 0.0% | 0 | 89.3% | 0.3% |
| +10% | +0 mg/dL (+0.0 mmol/L) | 82.9% | 0.1% | 0 | 88.8% | 0.3% |
| +20% | +1 mg/dL (+0.1 mmol/L) | 82.2% | 0.1% | 0 | 88.2% | 0.3% |
| +30% | +2 mg/dL (+0.1 mmol/L) | 82.0% | 0.0% | 0 | 88.0% | 0.3% |

No change suggested: already meets both goals.

### 4. Target

Judged on the whole period: 336.0 h of readings, observed 89.3% in range and 0.3% below.

| Target | Average glucose change | In range | Below range | Low episodes |
|---|---|---|---|---|
| -1.0 mmol/L (-18 mg/dL) on every target: 92 mg/dL (5.1 mmol/L) | -18 mg/dL (-1.0 mmol/L) | 91.0% | 3.1% | 9 |
| -0.5 mmol/L (-9 mg/dL) on every target: 101 mg/dL (5.6 mmol/L) | -9 mg/dL (-0.5 mmol/L) | 91.2% | 1.0% | 4 |
| 110 mg/dL (6.1 mmol/L) (current) ← | +0 mg/dL (+0.0 mmol/L) | 89.3% | 0.3% | 1 |
| +0.5 mmol/L (+9 mg/dL) on every target: 119 mg/dL (6.6 mmol/L) | +9 mg/dL (+0.5 mmol/L) | 85.6% | 0.1% | 0 |
| +1.0 mmol/L (+18 mg/dL) on every target: 128 mg/dL (7.1 mmol/L) | +18 mg/dL (+1.0 mmol/L) | 79.7% | 0.0% | 0 |

No change suggested: already meets both goals.

### 5. SMB limit

Judged on the whole period: 336.0 h of readings, observed 89.3% in range and 0.3% below.

| Maximum SMB basal minutes | Average glucose change | In range | Below range | Low episodes |
|---|---|---|---|---|
| 15 min | +0 mg/dL (+0.0 mmol/L) | 88.8% | 0.3% | 1 |
| 30 min | -0 mg/dL (-0.0 mmol/L) | 89.0% | 0.3% | 1 |
| 45 min | +0 mg/dL (+0.0 mmol/L) | 89.3% | 0.3% | 1 |
| 60 min | +0 mg/dL (+0.0 mmol/L) | 89.3% | 0.3% | 1 |
| 75 min (current) ← | +0 mg/dL (+0.0 mmol/L) | 89.3% | 0.3% | 1 |
| 90 min | +0 mg/dL (+0.0 mmol/L) | 89.3% | 0.3% | 1 |

No change suggested: already meets both goals.

### 6. Max IOB

Judged on the whole period: 336.0 h of readings, observed 89.3% in range and 0.3% below.

| Max IOB | Average glucose change | In range | Below range | Low episodes |
|---|---|---|---|---|
| 5.4 U | -1 mg/dL (-0.1 mmol/L) | 89.6% | 0.3% | 1 |
| 6.2 U | -0 mg/dL (-0.0 mmol/L) | 89.4% | 0.3% | 1 |
| 7 U | -0 mg/dL (-0.0 mmol/L) | 89.0% | 0.3% | 1 |
| 7.8 U ← | -0 mg/dL (-0.0 mmol/L) | 89.1% | 0.3% | 1 |
| 8.5 U | -0 mg/dL (-0.0 mmol/L) | 89.1% | 0.3% | 1 |
| 9.3 U | -0 mg/dL (-0.0 mmol/L) | 89.1% | 0.3% | 1 |
| 10.1 U | -0 mg/dL (-0.0 mmol/L) | 89.1% | 0.3% | 1 |

Trial to consider: max IOB 7.8 U, because the smallest change that meets both goals.

### Together

With max IOB 7.8 U: estimated 89.1% in range and 0.3% below (observed 89.3% and 0.3%), average glucose -0 mg/dL (-0.0 mmol/L). That meets both goals.

Change one setting at a time and give each a few days before the next, so its effect can be seen on its own.