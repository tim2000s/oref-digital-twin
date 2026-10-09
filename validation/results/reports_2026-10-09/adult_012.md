# oref digital twin — report

Findings: 0 critical, 1 to watch, 4 notes.

## Your setup

- Detected: **unknown** (confidence 0.0)
- The controller could not be classified — findings only.

## Glucose

- Readings: 4032 over ~14.0 days
- Mean: 130.8 mg/dL (7.3 mmol/L), GMI 6.4%
- Time in range (70–180): 92.7%
- Time below 70: 0.7%; below 54: 0.2%
- Time above 180: 6.6%; above 250: 0.5%
- Variability (CV): 23.6%

## Findings

### Worth attention

- **Nocturnal hypoglycaemia episodes** — 2 overnight (00:00-06:00) low episode(s) below 70 mg/dL across 2 night(s). Overnight lows are the domain's repeated risk; cross-check against overnight SMBs and IOB.

### Notes

- **Meets consensus glycaemic targets** — TIR 92.7%, TBR<70 0.7%, TBR<54 0.2% — within consensus targets over this window.
- **Estimated daily insulin** — ~63.2 U/day estimated (profile basal ~29.21 U + bolus/SMB ~34.0 U/day). Rough: basal is the scheduled profile, not delivered basal, and temp basals are not integrated.
- **Overnight SMBs at high IOB, with lows following** — 81 of 315 overnight SMBs fired at high IOB (>= p75 2.73 U); 0 (0.0%) were followed by BG < 70 mg/dL within 2h. Association only — this names the pattern, it does not prove the SMB caused the low.
- **30-min IOB prediction bias -12.3 mg/dL** — Over 4027 cycles the IOB-only prediction ran 12.3 mg/dL lower than realised on average (MAE 19.0). A large systematic bias points at model calibration; it is descriptive, not a dosing instruction.


---

_This is decision-support, not medical advice, and it is advisory-only — it never changes your loop or pump. Discuss any change with your clinician and trial it deliberately._

## Settings tests (estimated)

Goal: time in range above 70% and time below range under 2%. Observed over 14.0 days: 92.7% in range, 0.7% below, 3 low episodes.

Each setting is stepped from −30% to +30% and the loop is re-run through every 5-minute cycle (4032) under each value. Basal is tested first, on fasting stretches; ISF next, on correction stretches; then carb ratio on meals; then target, the SMB limit and max IOB over the whole period. Each stage keeps the choices before it.

_Estimated, not measured: each value's glucose is your CGM shifted by the change in insulin the loop would have given, times your profile ISF, with the loop reacting to the shifted glucose at every step. It assumes your meals, activity and own treatments would have been the same, and that your profile ISF is your real sensitivity. Treat any change as a trial to test, one setting at a time._

_Your loop was detected as unknown. These tests run stock oref0, so anything your variant adds on top of it is not modelled._

Insulin curve: rapid-acting (settings).

### 1. Basal

Judged on fasting stretches (no carbs or meal-sized rise in the last 4 h, nothing above 180 mg/dL in the last 3 h): 102.7 h of readings, observed 99.5% in range and 0.5% below.

| Basal rates | Average glucose change | In range (fasting) | Below range (fasting) | Low episodes | In range (all) | Below range (all) |
|---|---|---|---|---|---|---|
| -30% | +12 mg/dL (+0.7 mmol/L) | 98.5% | 0.0% | 0 | 88.3% | 0.2% |
| -20% | +8 mg/dL (+0.4 mmol/L) | 99.2% | 0.0% | 0 | 90.1% | 0.3% |
| -10% | +4 mg/dL (+0.2 mmol/L) | 99.6% | 0.1% | 0 | 91.5% | 0.4% |
| current ← | +0 mg/dL (+0.0 mmol/L) | 99.5% | 0.5% | 1 | 92.7% | 0.7% |
| +10% | -4 mg/dL (-0.2 mmol/L) | 98.6% | 1.4% | 2 | 93.4% | 1.1% |
| +20% | -8 mg/dL (-0.5 mmol/L) | 95.7% | 4.3% | 3 | 92.7% | 2.5% |
| +30% | -12 mg/dL (-0.7 mmol/L) | 93.7% | 6.3% | 10 | 92.7% | 3.4% |

No change suggested: already meets both goals.

### 2. ISF

Judged on correction stretches (above 180 mg/dL in the last 3 h, outside meals): 8.2 h of readings, observed 93.9% in range and 6.1% below.

| ISF | Average glucose change | In range (correction) | Below range (correction) | Low episodes | In range (all) | Below range (all) |
|---|---|---|---|---|---|---|
| -30% | -11 mg/dL (-0.6 mmol/L) | 86.7% | 13.3% | 1 | 92.9% | 3.2% |
| -20% | -7 mg/dL (-0.4 mmol/L) | 87.8% | 12.2% | 1 | 93.4% | 1.9% |
| -10% | -3 mg/dL (-0.2 mmol/L) | 93.9% | 6.1% | 1 | 93.3% | 1.0% |
| current | +0 mg/dL (+0.0 mmol/L) | 93.9% | 6.1% | 1 | 92.7% | 0.7% |
| +10% | +3 mg/dL (+0.2 mmol/L) | 93.9% | 6.1% | 1 | 92.0% | 0.4% |
| +20% | +5 mg/dL (+0.3 mmol/L) | 93.9% | 6.1% | 1 | 90.7% | 0.3% |
| +30% ← | +8 mg/dL (+0.4 mmol/L) | 94.9% | 5.1% | 1 | 90.0% | 0.2% |

Trial to consider: ISF +30%, because no value gets lows under 2%; this has the fewest.

### 3. Carb ratio

Judged on meal stretches (the 4 h after logged carbs or a meal-sized rise): 225.2 h of readings, observed 89.6% in range and 0.6% below.
Run with ISF +30%.
Logged meal boluses are scaled with the ratio, as the bolus wizard would.

| Carb ratio | Average glucose change | In range (meal) | Below range (meal) | Low episodes | In range (all) | Below range (all) |
|---|---|---|---|---|---|---|
| -30% | +6 mg/dL (+0.3 mmol/L) | 86.7% | 0.3% | 0 | 90.6% | 0.3% |
| -20% | +7 mg/dL (+0.4 mmol/L) | 86.4% | 0.2% | 0 | 90.5% | 0.3% |
| -10% | +7 mg/dL (+0.4 mmol/L) | 86.0% | 0.2% | 0 | 90.2% | 0.3% |
| current ← | +8 mg/dL (+0.4 mmol/L) | 85.8% | 0.2% | 0 | 90.0% | 0.2% |
| +10% | +8 mg/dL (+0.5 mmol/L) | 85.3% | 0.2% | 0 | 89.6% | 0.2% |
| +20% | +9 mg/dL (+0.5 mmol/L) | 85.0% | 0.2% | 0 | 89.4% | 0.2% |
| +30% | +9 mg/dL (+0.5 mmol/L) | 84.7% | 0.2% | 0 | 89.1% | 0.2% |

No change suggested: already meets both goals.

### 4. Target

Judged on the whole period: 336.0 h of readings, observed 92.7% in range and 0.7% below.
Run with ISF +30%.

| Target | Average glucose change | In range | Below range | Low episodes |
|---|---|---|---|---|
| -1.0 mmol/L (-18 mg/dL) on every target: 92 mg/dL (5.1 mmol/L) | -10 mg/dL (-0.6 mmol/L) | 92.5% | 2.5% | 11 |
| -0.5 mmol/L (-9 mg/dL) on every target: 101 mg/dL (5.6 mmol/L) | -1 mg/dL (-0.1 mmol/L) | 92.1% | 0.8% | 3 |
| 110 mg/dL (6.1 mmol/L) (current) ← | +8 mg/dL (+0.4 mmol/L) | 90.0% | 0.2% | 1 |
| +0.5 mmol/L (+9 mg/dL) on every target: 119 mg/dL (6.6 mmol/L) | +17 mg/dL (+0.9 mmol/L) | 86.1% | 0.2% | 1 |
| +1.0 mmol/L (+18 mg/dL) on every target: 128 mg/dL (7.1 mmol/L) | +26 mg/dL (+1.4 mmol/L) | 80.5% | 0.0% | 0 |

No change suggested: already meets both goals.

### 5. SMB limit

Judged on the whole period: 336.0 h of readings, observed 92.7% in range and 0.7% below.
Run with ISF +30%.

| Maximum SMB basal minutes | Average glucose change | In range | Below range | Low episodes |
|---|---|---|---|---|
| 15 min | +8 mg/dL (+0.4 mmol/L) | 89.9% | 0.2% | 1 |
| 30 min | +8 mg/dL (+0.4 mmol/L) | 89.9% | 0.2% | 1 |
| 45 min | +8 mg/dL (+0.4 mmol/L) | 90.0% | 0.2% | 1 |
| 60 min | +8 mg/dL (+0.4 mmol/L) | 90.0% | 0.2% | 1 |
| 75 min (current) ← | +8 mg/dL (+0.4 mmol/L) | 90.0% | 0.2% | 1 |
| 90 min | +8 mg/dL (+0.4 mmol/L) | 90.0% | 0.2% | 1 |

No change suggested: already meets both goals.

### 6. Max IOB

Judged on the whole period: 336.0 h of readings, observed 92.7% in range and 0.7% below.
Run with ISF +30%.

| Max IOB | Average glucose change | In range | Below range | Low episodes |
|---|---|---|---|---|
| 6.1 U | +8 mg/dL (+0.4 mmol/L) | 90.1% | 0.3% | 1 |
| 7 U | +8 mg/dL (+0.4 mmol/L) | 90.1% | 0.2% | 1 |
| 7.9 U | +8 mg/dL (+0.4 mmol/L) | 89.9% | 0.2% | 1 |
| 8.8 U ← | +8 mg/dL (+0.4 mmol/L) | 89.8% | 0.2% | 1 |
| 9.6 U | +8 mg/dL (+0.4 mmol/L) | 89.9% | 0.2% | 1 |
| 10.5 U | +8 mg/dL (+0.4 mmol/L) | 89.9% | 0.2% | 1 |
| 11.4 U | +8 mg/dL (+0.4 mmol/L) | 89.9% | 0.2% | 1 |

Trial to consider: max IOB 8.8 U, because the smallest change that meets both goals.

### Together

With ISF +30%, max IOB 8.8 U: estimated 89.8% in range and 0.2% below (observed 92.7% and 0.7%), average glucose +8 mg/dL (+0.4 mmol/L). That meets both goals.

Change one setting at a time and give each a few days before the next, so its effect can be seen on its own.