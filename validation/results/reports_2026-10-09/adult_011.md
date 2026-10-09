# oref digital twin — report

Findings: 1 critical, 3 to watch, 4 notes.

## Your setup

- Detected: **unknown** (confidence 0.0)
- The controller could not be classified — findings only.

## Glucose

- Readings: 4032 over ~14.0 days
- Mean: 142.8 mg/dL (7.9 mmol/L), GMI 6.7%
- Time in range (70–180): 72.4%
- Time below 70: 5.6%; below 54: 3.1%
- Time above 180: 22.0%; above 250: 5.3%
- Variability (CV): 41.7%

## Findings

### Critical

- **Severe hypoglycaemia exposure above the 1% limit** — 3.1% of readings are below 54 mg/dL (3.0 mmol/L), above the 1.0% consensus safety limit. This is the priority to address.

### Worth attention

- **Time below 70 mg/dL above the 4% target** — 5.6% of readings are below 70 mg/dL (3.9 mmol/L), above the 4.0% consensus target.
- **Glucose variability above 36%** — Coefficient of variation is 41.7%, above the 36.0% consensus ceiling — high variability makes stable dosing harder and raises hypo risk.
- **Nocturnal hypoglycaemia episodes** — 5 overnight (00:00-06:00) low episode(s) below 70 mg/dL across 4 night(s). Overnight lows are the domain's repeated risk; cross-check against overnight SMBs and IOB.

### Notes

- **Time above 250 mg/dL above 5%** — 5.3% of readings are above 250 mg/dL (13.9 mmol/L).
- **Estimated daily insulin** — ~51.4 U/day estimated (profile basal ~21.09 U + bolus/SMB ~30.3 U/day). Rough: basal is the scheduled profile, not delivered basal, and temp basals are not integrated.
- **Overnight SMBs at high IOB, with lows following** — 107 of 273 overnight SMBs fired at high IOB (>= p75 2.18 U); 0 (0.0%) were followed by BG < 70 mg/dL within 2h. Association only — this names the pattern, it does not prove the SMB caused the low.
- **30-min IOB prediction bias -10.3 mg/dL** — Over 4027 cycles the IOB-only prediction ran 10.3 mg/dL lower than realised on average (MAE 18.7). A large systematic bias points at model calibration; it is descriptive, not a dosing instruction.


---

_This is decision-support, not medical advice, and it is advisory-only — it never changes your loop or pump. Discuss any change with your clinician and trial it deliberately._

## Settings tests (estimated)

Goal: time in range above 70% and time below range under 2%. Observed over 14.0 days: 72.4% in range, 5.6% below, 14 low episodes.

Each setting is stepped from −30% to +30% and the loop is re-run through every 5-minute cycle (4032) under each value. Basal is tested first, on fasting stretches; ISF next, on correction stretches; then carb ratio on meals; then target, the SMB limit and max IOB over the whole period. Each stage keeps the choices before it.

_Estimated, not measured: each value's glucose is your CGM shifted by the change in insulin the loop would have given, times your profile ISF, with the loop reacting to the shifted glucose at every step. It assumes your meals, activity and own treatments would have been the same, and that your profile ISF is your real sensitivity. Treat any change as a trial to test, one setting at a time._

_Your loop was detected as unknown. These tests run stock oref0, so anything your variant adds on top of it is not modelled._

Insulin curve: rapid-acting (settings).

### 1. Basal

Judged on fasting stretches (no carbs or meal-sized rise in the last 4 h, nothing above 180 mg/dL in the last 3 h): 89.2 h of readings, observed 97.0% in range and 3.0% below.

| Basal rates | Average glucose change | In range (fasting) | Below range (fasting) | Low episodes | In range (all) | Below range (all) |
|---|---|---|---|---|---|---|
| -30% ← | +12 mg/dL (+0.7 mmol/L) | 97.9% | 1.9% | 2 | 70.8% | 3.7% |
| -20% | +8 mg/dL (+0.4 mmol/L) | 97.8% | 2.2% | 2 | 71.7% | 4.4% |
| -10% | +4 mg/dL (+0.2 mmol/L) | 97.6% | 2.4% | 2 | 72.0% | 4.9% |
| current | +0 mg/dL (+0.0 mmol/L) | 97.0% | 3.0% | 4 | 72.4% | 5.6% |
| +10% | -4 mg/dL (-0.2 mmol/L) | 95.7% | 4.3% | 6 | 72.0% | 7.0% |
| +20% | -8 mg/dL (-0.4 mmol/L) | 94.4% | 5.6% | 7 | 72.3% | 8.2% |
| +30% | -12 mg/dL (-0.7 mmol/L) | 93.0% | 7.0% | 9 | 72.3% | 9.7% |

Trial to consider: basal rates -30%, because the smallest change that meets both goals.

### 2. ISF

Judged on correction stretches (above 180 mg/dL in the last 3 h, outside meals): 27.8 h of readings, observed 53.5% in range and 24.0% below.
Run with basal rates -30%.

| ISF | Average glucose change | In range (correction) | Below range (correction) | Low episodes | In range (all) | Below range (all) |
|---|---|---|---|---|---|---|
| -30% | -6 mg/dL (-0.3 mmol/L) | 47.7% | 36.9% | 12 | 71.4% | 9.4% |
| -20% | +0 mg/dL (+0.0 mmol/L) | 52.0% | 27.9% | 9 | 71.8% | 6.9% |
| -10% | +6 mg/dL (+0.4 mmol/L) | 52.9% | 21.3% | 8 | 71.5% | 5.0% |
| current | +12 mg/dL (+0.7 mmol/L) | 56.2% | 15.6% | 5 | 70.8% | 3.7% |
| +10% | +17 mg/dL (+1.0 mmol/L) | 60.7% | 10.5% | 4 | 69.9% | 2.7% |
| +20% | +22 mg/dL (+1.2 mmol/L) | 66.1% | 3.3% | 2 | 69.8% | 1.2% |
| +30% ← | +27 mg/dL (+1.5 mmol/L) | 68.2% | 0.0% | 0 | 68.8% | 0.2% |

Trial to consider: ISF +30%, because no value reaches 70% in range; this keeps lows under 2% with the most time in range.

### 3. Carb ratio

Judged on meal stretches (the 4 h after logged carbs or a meal-sized rise): 219.1 h of readings, observed 64.8% in range and 4.3% below.
Run with basal rates -30%, ISF +30%.
Logged meal boluses are scaled with the ratio, as the bolus wizard would.

| Carb ratio | Average glucose change | In range (meal) | Below range (meal) | Low episodes | In range (all) | Below range (all) |
|---|---|---|---|---|---|---|
| -30% ← | +26 mg/dL (+1.4 mmol/L) | 57.8% | 0.5% | 2 | 69.0% | 0.4% |
| -20% | +26 mg/dL (+1.5 mmol/L) | 57.6% | 0.5% | 2 | 68.9% | 0.4% |
| -10% | +27 mg/dL (+1.5 mmol/L) | 57.6% | 0.3% | 1 | 68.9% | 0.2% |
| current | +27 mg/dL (+1.5 mmol/L) | 57.5% | 0.3% | 1 | 68.8% | 0.2% |
| +10% | +28 mg/dL (+1.5 mmol/L) | 57.2% | 0.3% | 1 | 68.6% | 0.2% |
| +20% | +28 mg/dL (+1.5 mmol/L) | 57.2% | 0.3% | 1 | 68.6% | 0.2% |
| +30% | +28 mg/dL (+1.6 mmol/L) | 56.9% | 0.3% | 1 | 68.3% | 0.2% |

Trial to consider: carb ratio -30%, because no value reaches 70% in range; this keeps lows under 2% with the most time in range.

### 4. Target

Judged on the whole period: 336.0 h of readings, observed 72.4% in range and 5.6% below.
Run with basal rates -30%, ISF +30%, carb ratio -30%.

| Target | Average glucose change | In range | Below range | Low episodes |
|---|---|---|---|---|
| -1.0 mmol/L (-18 mg/dL) on every target: 92 mg/dL (5.1 mmol/L) | +8 mg/dL (+0.4 mmol/L) | 71.1% | 3.8% | 12 |
| -0.5 mmol/L (-9 mg/dL) on every target: 101 mg/dL (5.6 mmol/L) | +17 mg/dL (+0.9 mmol/L) | 70.3% | 2.4% | 10 |
| 110 mg/dL (6.1 mmol/L) (current) ← | +26 mg/dL (+1.4 mmol/L) | 69.0% | 0.4% | 2 |
| +0.5 mmol/L (+9 mg/dL) on every target: 119 mg/dL (6.6 mmol/L) | +35 mg/dL (+1.9 mmol/L) | 64.9% | 0.2% | 1 |
| +1.0 mmol/L (+18 mg/dL) on every target: 128 mg/dL (7.1 mmol/L) | +44 mg/dL (+2.4 mmol/L) | 59.3% | 0.0% | 0 |

No change suggested: no value reaches 70% in range; this keeps lows under 2% with the most time in range.

### 5. SMB limit

Judged on the whole period: 336.0 h of readings, observed 72.4% in range and 5.6% below.
Run with basal rates -30%, ISF +30%, carb ratio -30%.

| Maximum SMB basal minutes | Average glucose change | In range | Below range | Low episodes |
|---|---|---|---|---|
| 15 min | +27 mg/dL (+1.5 mmol/L) | 68.6% | 0.4% | 2 |
| 30 min | +26 mg/dL (+1.5 mmol/L) | 68.9% | 0.4% | 1 |
| 45 min | +26 mg/dL (+1.4 mmol/L) | 69.0% | 0.4% | 2 |
| 60 min | +26 mg/dL (+1.4 mmol/L) | 69.0% | 0.4% | 2 |
| 75 min (current) ← | +26 mg/dL (+1.4 mmol/L) | 69.0% | 0.3% | 1 |
| 90 min | +26 mg/dL (+1.4 mmol/L) | 69.0% | 0.3% | 1 |

No change suggested: no value reaches 70% in range; this keeps lows under 2% with the most time in range.

### 6. Max IOB

Judged on the whole period: 336.0 h of readings, observed 72.4% in range and 5.6% below.
Run with basal rates -30%, ISF +30%, carb ratio -30%.

| Max IOB | Average glucose change | In range | Below range | Low episodes |
|---|---|---|---|---|
| 4.4 U | +30 mg/dL (+1.6 mmol/L) | 67.2% | 0.8% | 3 |
| 5.1 U | +27 mg/dL (+1.5 mmol/L) | 68.3% | 0.7% | 2 |
| 5.7 U | +26 mg/dL (+1.5 mmol/L) | 68.8% | 0.6% | 2 |
| 6.3 U | +26 mg/dL (+1.4 mmol/L) | 69.0% | 0.3% | 1 |
| 7 U ← | +26 mg/dL (+1.4 mmol/L) | 69.2% | 0.3% | 1 |
| 7.6 U | +26 mg/dL (+1.4 mmol/L) | 69.1% | 0.3% | 1 |
| 8.2 U | +26 mg/dL (+1.4 mmol/L) | 69.1% | 0.3% | 1 |

Trial to consider: max IOB 7 U, because no value reaches 70% in range; this keeps lows under 2% with the most time in range.

### Together

With basal rates -30%, ISF +30%, carb ratio -30%, max IOB 7 U: estimated 69.2% in range and 0.3% below (observed 72.4% and 5.6%), average glucose +26 mg/dL (+1.4 mmol/L). That does not meet both goals.

Change one setting at a time and give each a few days before the next, so its effect can be seen on its own.