# oref digital twin — report

Findings: 0 critical, 2 to watch, 3 notes.

## Your setup

- Detected: **unknown** (confidence 0.0)
- The controller could not be classified — findings only.

## Glucose

- Readings: 4032 over ~14.0 days
- Mean: 128.2 mg/dL (7.1 mmol/L), GMI 6.4%
- Time in range (70–180): 93.3%
- Time below 70: 1.7%; below 54: 0.3%
- Time above 180: 5.0%; above 250: 0.4%
- Variability (CV): 24.3%

## Findings

### Worth attention

- **Overnight SMBs at high IOB, with lows following** — 62 of 255 overnight SMBs fired at high IOB (>= p75 2.94 U); 1 (1.6%) were followed by BG < 70 mg/dL within 2h. Association only — this names the pattern, it does not prove the SMB caused the low.
- **Nocturnal hypoglycaemia episodes** — 6 overnight (00:00-06:00) low episode(s) below 70 mg/dL across 6 night(s). Overnight lows are the domain's repeated risk; cross-check against overnight SMBs and IOB.

### Notes

- **Meets consensus glycaemic targets** — TIR 93.3%, TBR<70 1.7%, TBR<54 0.3% — within consensus targets over this window.
- **Estimated daily insulin** — ~74.1 U/day estimated (profile basal ~29.08 U + bolus/SMB ~45.0 U/day). Rough: basal is the scheduled profile, not delivered basal, and temp basals are not integrated.
- **30-min IOB prediction bias -14.1 mg/dL** — Over 4027 cycles the IOB-only prediction ran 14.1 mg/dL lower than realised on average (MAE 25.1). A large systematic bias points at model calibration; it is descriptive, not a dosing instruction.


---

_This is decision-support, not medical advice, and it is advisory-only — it never changes your loop or pump. Discuss any change with your clinician and trial it deliberately._

## Settings tests (estimated)

Goal: time in range above 70% and time below range under 2%. Observed over 14.0 days: 93.3% in range, 1.7% below, 5 low episodes.

Each setting is stepped from −30% to +30% and the loop is re-run through every 5-minute cycle (4032) under each value. Basal is tested first, on fasting stretches; ISF next, on correction stretches; then carb ratio on meals; then target, the SMB limit and max IOB over the whole period. Each stage keeps the choices before it.

_Estimated, not measured: each value's glucose is your CGM shifted by the change in insulin the loop would have given, times your profile ISF, with the loop reacting to the shifted glucose at every step. It assumes your meals, activity and own treatments would have been the same, and that your profile ISF is your real sensitivity. Treat any change as a trial to test, one setting at a time._

_Your loop was detected as unknown. These tests run stock oref0, so anything your variant adds on top of it is not modelled._

Insulin curve: rapid-acting (settings).

### 1. Basal

Judged on fasting stretches (no carbs or meal-sized rise in the last 4 h, nothing above 180 mg/dL in the last 3 h): 94.7 h of readings, observed 98.3% in range and 1.7% below.

| Basal rates | Average glucose change | In range (fasting) | Below range (fasting) | Low episodes | In range (all) | Below range (all) |
|---|---|---|---|---|---|---|
| -30% | +10 mg/dL (+0.6 mmol/L) | 99.6% | 0.3% | 0 | 90.9% | 0.7% |
| -20% | +7 mg/dL (+0.4 mmol/L) | 99.4% | 0.5% | 0 | 91.7% | 0.8% |
| -10% | +3 mg/dL (+0.2 mmol/L) | 98.9% | 1.1% | 0 | 92.5% | 1.4% |
| current ← | +0 mg/dL (+0.0 mmol/L) | 98.3% | 1.7% | 2 | 93.3% | 1.7% |
| +10% | -4 mg/dL (-0.2 mmol/L) | 97.4% | 2.6% | 3 | 93.3% | 2.5% |
| +20% | -7 mg/dL (-0.4 mmol/L) | 96.7% | 3.3% | 5 | 92.9% | 3.2% |
| +30% | -11 mg/dL (-0.6 mmol/L) | 95.4% | 4.6% | 5 | 92.4% | 4.1% |

No change suggested: already meets both goals.

### 2. ISF

Judged on correction stretches (above 180 mg/dL in the last 3 h, outside meals): 10.0 h of readings, observed 78.3% in range and 19.2% below.

| ISF | Average glucose change | In range (correction) | Below range (correction) | Low episodes | In range (all) | Below range (all) |
|---|---|---|---|---|---|---|
| -30% | -12 mg/dL (-0.7 mmol/L) | 61.7% | 38.3% | 3 | 90.9% | 5.8% |
| -20% | -8 mg/dL (-0.4 mmol/L) | 70.8% | 29.2% | 3 | 92.3% | 3.9% |
| -10% | -4 mg/dL (-0.2 mmol/L) | 73.3% | 24.2% | 3 | 93.1% | 2.6% |
| current | +0 mg/dL (+0.0 mmol/L) | 78.3% | 19.2% | 2 | 93.3% | 1.7% |
| +10% | +3 mg/dL (+0.2 mmol/L) | 85.0% | 11.7% | 2 | 92.7% | 1.1% |
| +20% | +7 mg/dL (+0.4 mmol/L) | 85.8% | 9.2% | 2 | 91.8% | 0.7% |
| +30% ← | +11 mg/dL (+0.6 mmol/L) | 86.7% | 5.0% | 0 | 90.8% | 0.4% |

Trial to consider: ISF +30%, because no value gets lows under 2%; this has the fewest.

### 3. Carb ratio

Judged on meal stretches (the 4 h after logged carbs or a meal-sized rise): 231.3 h of readings, observed 91.8% in range and 1.0% below.
Run with ISF +30%.
Logged meal boluses are scaled with the ratio, as the bolus wizard would.

| Carb ratio | Average glucose change | In range (meal) | Below range (meal) | Low episodes | In range (all) | Below range (all) |
|---|---|---|---|---|---|---|
| -30% | +9 mg/dL (+0.5 mmol/L) | 87.8% | 0.5% | 3 | 91.0% | 0.7% |
| -20% | +9 mg/dL (+0.5 mmol/L) | 87.7% | 0.4% | 2 | 91.0% | 0.5% |
| -10% | +10 mg/dL (+0.6 mmol/L) | 87.5% | 0.4% | 2 | 90.9% | 0.5% |
| current ← | +11 mg/dL (+0.6 mmol/L) | 87.3% | 0.4% | 1 | 90.8% | 0.4% |
| +10% | +12 mg/dL (+0.6 mmol/L) | 86.5% | 0.3% | 1 | 90.4% | 0.3% |
| +20% | +12 mg/dL (+0.7 mmol/L) | 86.0% | 0.2% | 1 | 90.0% | 0.2% |
| +30% | +13 mg/dL (+0.7 mmol/L) | 85.5% | 0.1% | 0 | 89.6% | 0.1% |

No change suggested: already meets both goals.

### 4. Target

Judged on the whole period: 336.0 h of readings, observed 93.3% in range and 1.7% below.
Run with ISF +30%.

| Target | Average glucose change | In range | Below range | Low episodes |
|---|---|---|---|---|
| -1.0 mmol/L (-18 mg/dL) on every target: 92 mg/dL (5.1 mmol/L) | -7 mg/dL (-0.4 mmol/L) | 92.8% | 3.1% | 9 |
| -0.5 mmol/L (-9 mg/dL) on every target: 101 mg/dL (5.6 mmol/L) | +2 mg/dL (+0.1 mmol/L) | 92.8% | 1.1% | 5 |
| 110 mg/dL (6.1 mmol/L) (current) ← | +11 mg/dL (+0.6 mmol/L) | 90.8% | 0.4% | 1 |
| +0.5 mmol/L (+9 mg/dL) on every target: 119 mg/dL (6.6 mmol/L) | +20 mg/dL (+1.1 mmol/L) | 86.8% | 0.0% | 0 |
| +1.0 mmol/L (+18 mg/dL) on every target: 128 mg/dL (7.1 mmol/L) | +28 mg/dL (+1.6 mmol/L) | 81.2% | 0.0% | 0 |

No change suggested: already meets both goals.

### 5. SMB limit

Judged on the whole period: 336.0 h of readings, observed 93.3% in range and 1.7% below.
Run with ISF +30%.

| Maximum SMB basal minutes | Average glucose change | In range | Below range | Low episodes |
|---|---|---|---|---|
| 15 min | +12 mg/dL (+0.7 mmol/L) | 89.8% | 0.2% | 0 |
| 30 min | +11 mg/dL (+0.6 mmol/L) | 90.7% | 0.4% | 1 |
| 45 min | +11 mg/dL (+0.6 mmol/L) | 90.8% | 0.4% | 1 |
| 60 min | +11 mg/dL (+0.6 mmol/L) | 90.8% | 0.4% | 1 |
| 75 min (current) ← | +11 mg/dL (+0.6 mmol/L) | 90.8% | 0.4% | 1 |
| 90 min | +11 mg/dL (+0.6 mmol/L) | 90.8% | 0.4% | 1 |

No change suggested: already meets both goals.

### 6. Max IOB

Judged on the whole period: 336.0 h of readings, observed 93.3% in range and 1.7% below.
Run with ISF +30%.

| Max IOB | Average glucose change | In range | Below range | Low episodes |
|---|---|---|---|---|
| 6.1 U | +10 mg/dL (+0.6 mmol/L) | 91.1% | 0.3% | 1 |
| 7 U | +10 mg/dL (+0.6 mmol/L) | 90.9% | 0.4% | 2 |
| 7.8 U | +10 mg/dL (+0.6 mmol/L) | 91.0% | 0.4% | 2 |
| 8.7 U ← | +11 mg/dL (+0.6 mmol/L) | 90.8% | 0.4% | 1 |
| 9.6 U | +11 mg/dL (+0.6 mmol/L) | 90.9% | 0.4% | 1 |
| 10.5 U | +11 mg/dL (+0.6 mmol/L) | 90.9% | 0.4% | 1 |
| 11.3 U | +11 mg/dL (+0.6 mmol/L) | 90.9% | 0.4% | 1 |

Trial to consider: max IOB 8.7 U, because the smallest change that meets both goals.

### Together

With ISF +30%, max IOB 8.7 U: estimated 90.8% in range and 0.4% below (observed 93.3% and 1.7%), average glucose +11 mg/dL (+0.6 mmol/L). That meets both goals.

Change one setting at a time and give each a few days before the next, so its effect can be seen on its own.