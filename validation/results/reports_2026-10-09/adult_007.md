# oref digital twin — report

Findings: 0 critical, 1 to watch, 4 notes.

## Your setup

- Detected: **unknown** (confidence 0.0)
- The controller could not be classified — findings only.

## Glucose

- Readings: 4032 over ~14.0 days
- Mean: 149.2 mg/dL (8.3 mmol/L), GMI 6.9%
- Time in range (70–180): 83.7%
- Time below 70: 0.1%; below 54: 0.0%
- Time above 180: 16.2%; above 250: 1.5%
- Variability (CV): 23.3%

## Findings

### Worth attention

- **Nocturnal hypoglycaemia episodes** — 1 overnight (00:00-06:00) low episode(s) below 70 mg/dL across 1 night(s). Overnight lows are the domain's repeated risk; cross-check against overnight SMBs and IOB.

### Notes

- **Meets consensus glycaemic targets** — TIR 83.7%, TBR<70 0.1%, TBR<54 0.0% — within consensus targets over this window.
- **Estimated daily insulin** — ~52.4 U/day estimated (profile basal ~17.86 U + bolus/SMB ~34.5 U/day). Rough: basal is the scheduled profile, not delivered basal, and temp basals are not integrated.
- **Overnight SMBs at high IOB, with lows following** — 106 of 387 overnight SMBs fired at high IOB (>= p75 2.6 U); 0 (0.0%) were followed by BG < 70 mg/dL within 2h. Association only — this names the pattern, it does not prove the SMB caused the low.
- **30-min IOB prediction bias -11.2 mg/dL** — Over 4027 cycles the IOB-only prediction ran 11.2 mg/dL lower than realised on average (MAE 17.2). A large systematic bias points at model calibration; it is descriptive, not a dosing instruction.


---

_This is decision-support, not medical advice, and it is advisory-only — it never changes your loop or pump. Discuss any change with your clinician and trial it deliberately._

## Settings tests (estimated)

Goal: time in range above 70% and time below range under 2%. Observed over 14.0 days: 83.7% in range, 0.1% below, 0 low episodes.

Each setting is stepped from −30% to +30% and the loop is re-run through every 5-minute cycle (4032) under each value. Basal is tested first, on fasting stretches; ISF next, on correction stretches; then carb ratio on meals; then target, the SMB limit and max IOB over the whole period. Each stage keeps the choices before it.

_Estimated, not measured: each value's glucose is your CGM shifted by the change in insulin the loop would have given, times your profile ISF, with the loop reacting to the shifted glucose at every step. It assumes your meals, activity and own treatments would have been the same, and that your profile ISF is your real sensitivity. Treat any change as a trial to test, one setting at a time._

_Your loop was detected as unknown. These tests run stock oref0, so anything your variant adds on top of it is not modelled._

Insulin curve: rapid-acting (settings).

### 1. Basal

Judged on fasting stretches (no carbs or meal-sized rise in the last 4 h, nothing above 180 mg/dL in the last 3 h): 114.6 h of readings, observed 99.9% in range and 0.1% below.

| Basal rates | Average glucose change | In range (fasting) | Below range (fasting) | Low episodes | In range (all) | Below range (all) |
|---|---|---|---|---|---|---|
| -30% | +9 mg/dL (+0.5 mmol/L) | 98.8% | 0.1% | 0 | 78.6% | 0.0% |
| -20% | +6 mg/dL (+0.3 mmol/L) | 99.2% | 0.1% | 0 | 80.2% | 0.0% |
| -10% | +3 mg/dL (+0.2 mmol/L) | 99.5% | 0.1% | 0 | 81.8% | 0.1% |
| current ← | +0 mg/dL (+0.0 mmol/L) | 99.9% | 0.1% | 0 | 83.7% | 0.1% |
| +10% | -3 mg/dL (-0.2 mmol/L) | 99.9% | 0.1% | 0 | 84.7% | 0.1% |
| +20% | -6 mg/dL (-0.3 mmol/L) | 99.9% | 0.1% | 0 | 86.1% | 0.1% |
| +30% | -9 mg/dL (-0.5 mmol/L) | 99.9% | 0.1% | 0 | 87.1% | 0.1% |

No change suggested: already meets both goals.

### 2. ISF

Judged on correction stretches (above 180 mg/dL in the last 3 h, outside meals): 39.8 h of readings, observed 52.3% in range and 0.0% below.

| ISF | Average glucose change | In range (correction) | Below range (correction) | Low episodes | In range (all) | Below range (all) |
|---|---|---|---|---|---|---|
| -30% | -15 mg/dL (-0.8 mmol/L) | 89.3% | 0.0% | 0 | 91.0% | 1.1% |
| -20% ← | -10 mg/dL (-0.5 mmol/L) | 77.6% | 0.0% | 0 | 89.2% | 0.2% |
| -10% | -4 mg/dL (-0.2 mmol/L) | 63.2% | 0.0% | 0 | 86.1% | 0.1% |
| current | +0 mg/dL (+0.0 mmol/L) | 52.3% | 0.0% | 0 | 83.7% | 0.1% |
| +10% | +4 mg/dL (+0.2 mmol/L) | 44.6% | 0.0% | 0 | 80.6% | 0.0% |
| +20% | +8 mg/dL (+0.5 mmol/L) | 38.7% | 0.0% | 0 | 78.1% | 0.0% |
| +30% | +12 mg/dL (+0.7 mmol/L) | 33.1% | 0.0% | 0 | 75.0% | 0.0% |

Trial to consider: ISF -20%, because the smallest change that meets both goals.

### 3. Carb ratio

Judged on meal stretches (the 4 h after logged carbs or a meal-sized rise): 181.6 h of readings, observed 80.3% in range and 0.1% below.
Run with ISF -20%.
Logged meal boluses are scaled with the ratio, as the bolus wizard would.

| Carb ratio | Average glucose change | In range (meal) | Below range (meal) | Low episodes | In range (all) | Below range (all) |
|---|---|---|---|---|---|---|
| -30% | -13 mg/dL (-0.7 mmol/L) | 85.8% | 0.8% | 1 | 90.5% | 0.5% |
| -20% | -11 mg/dL (-0.6 mmol/L) | 85.8% | 0.5% | 1 | 90.2% | 0.4% |
| -10% | -10 mg/dL (-0.6 mmol/L) | 85.2% | 0.4% | 1 | 89.7% | 0.3% |
| current ← | -10 mg/dL (-0.5 mmol/L) | 85.1% | 0.2% | 0 | 89.2% | 0.2% |
| +10% | -9 mg/dL (-0.5 mmol/L) | 84.8% | 0.3% | 1 | 88.8% | 0.3% |
| +20% | -8 mg/dL (-0.5 mmol/L) | 84.7% | 0.2% | 0 | 88.6% | 0.2% |
| +30% | -8 mg/dL (-0.4 mmol/L) | 84.6% | 0.2% | 0 | 88.4% | 0.2% |

No change suggested: already meets both goals.

### 4. Target

Judged on the whole period: 336.0 h of readings, observed 83.7% in range and 0.1% below.
Run with ISF -20%.

| Target | Average glucose change | In range | Below range | Low episodes |
|---|---|---|---|---|
| -1.0 mmol/L (-18 mg/dL) on every target: 92 mg/dL (5.1 mmol/L) | -28 mg/dL (-1.5 mmol/L) | 92.4% | 3.1% | 9 |
| -0.5 mmol/L (-9 mg/dL) on every target: 101 mg/dL (5.6 mmol/L) | -18 mg/dL (-1.0 mmol/L) | 91.2% | 1.4% | 6 |
| 110 mg/dL (6.1 mmol/L) (current) ← | -10 mg/dL (-0.5 mmol/L) | 89.2% | 0.2% | 0 |
| +0.5 mmol/L (+9 mg/dL) on every target: 119 mg/dL (6.6 mmol/L) | -1 mg/dL (-0.0 mmol/L) | 85.0% | 0.1% | 0 |
| +1.0 mmol/L (+18 mg/dL) on every target: 128 mg/dL (7.1 mmol/L) | +8 mg/dL (+0.5 mmol/L) | 80.2% | 0.0% | 0 |

No change suggested: already meets both goals.

### 5. SMB limit

Judged on the whole period: 336.0 h of readings, observed 83.7% in range and 0.1% below.
Run with ISF -20%.

| Maximum SMB basal minutes | Average glucose change | In range | Below range | Low episodes |
|---|---|---|---|---|
| 15 min | -9 mg/dL (-0.5 mmol/L) | 88.9% | 0.2% | 1 |
| 30 min | -10 mg/dL (-0.5 mmol/L) | 89.2% | 0.2% | 0 |
| 45 min | -10 mg/dL (-0.5 mmol/L) | 89.2% | 0.2% | 0 |
| 60 min | -10 mg/dL (-0.5 mmol/L) | 89.2% | 0.2% | 0 |
| 75 min (current) ← | -10 mg/dL (-0.5 mmol/L) | 89.1% | 0.3% | 1 |
| 90 min | -10 mg/dL (-0.5 mmol/L) | 89.1% | 0.3% | 1 |

No change suggested: already meets both goals.

### 6. Max IOB

Judged on the whole period: 336.0 h of readings, observed 83.7% in range and 0.1% below.
Run with ISF -20%.

| Max IOB | Average glucose change | In range | Below range | Low episodes |
|---|---|---|---|---|
| 4.4 U | -9 mg/dL (-0.5 mmol/L) | 89.2% | 0.5% | 2 |
| 5 U | -10 mg/dL (-0.5 mmol/L) | 89.5% | 0.4% | 2 |
| 5.7 U | -10 mg/dL (-0.5 mmol/L) | 89.5% | 0.5% | 1 |
| 6.3 U (current) ← | -10 mg/dL (-0.5 mmol/L) | 89.1% | 0.3% | 1 |
| 6.9 U | -10 mg/dL (-0.5 mmol/L) | 89.3% | 0.2% | 0 |
| 7.6 U | -10 mg/dL (-0.5 mmol/L) | 89.3% | 0.3% | 0 |
| 8.2 U | -10 mg/dL (-0.5 mmol/L) | 89.3% | 0.3% | 0 |

No change suggested: already meets both goals.

### Together

With ISF -20%: estimated 89.1% in range and 0.3% below (observed 83.7% and 0.1%), average glucose -10 mg/dL (-0.5 mmol/L). That meets both goals.

Change one setting at a time and give each a few days before the next, so its effect can be seen on its own.